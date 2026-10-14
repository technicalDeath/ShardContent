"""A decision-tree bot that plays a brand-new mage so the shard can be watched through a new player's eyes.

    & .\\ShardContent\\tests\\scenarios\\new-mage-playtest\\run_bot.ps1 -Seconds 600

How it works: every tick the bot reads the journal, refreshes what it knows, then walks RULES top to bottom; the first rule that acts ends the
tick. A rule is a small function returning True when it did something. A scenario the bot could not handle is written to the notes (a `stuck`
entry or an `EXCEPTION`), and the rule that handles it is added here the next time round, so the tree grows with every run:

  run 1  walked and found nothing to do                  -> r_explore in short hops, r_hunt
  run 2  fought a black bear in melee range and died      -> SAFE_PREY, r_avoid, r_flee
  run 2  died with no staff help: a ghost's way home      -> r_dead walks to the healer and accepts the offer
  ...    (see the dated list in docs/New-Mage-Playtest-QoL.md)

Notes (work/mage-playtest/notes.jsonl) are the raw material for the quality-of-life list. Nothing here touches the server except through the
commands a player has; the staff session is used only to rescue a run that would otherwise end (and each use is itself a note).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import deque

from navrey_session import connect
from uo import Event

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
OUT = os.path.join(ROOT, "work", "mage-playtest")
os.makedirs(OUT, exist_ok=True)

SPELLS = {
    "heal": ("cast heal", 4),
    "magic arrow": ("cast magic arrow", 4),
    "cure": ("cast cure", 6),
    "night sight": ("cast night sight", 4),
}

# What a level-one mage with 74 hit points and 39 mana can hunt near town. Anything else that is grey is a danger.
SAFE_PREY = ("rat", "cat", "magpie", "nightingale", "crow", "rabbit", "hind", "sheep", "chicken", "pig", "goat", "cow", "gull", "bird", "dog", "lizard", "toad", "frog", "squirrel", "snake")
DANGEROUS = ("bear", "wolf", "orc", "ettin", "lizardman", "troll", "mongbat", "skeleton", "zombie", "gazer", "scorpion", "spider", "ogre", "harpy")

HEALER = (1472, 1611)      # data/client/UORekindled-Britain.csv: "Healer (resurrects you)"
TOWN = (1470, 1620)        # inside the walls, near the healer

FAIL_PATTERNS = [
    ("fizzle", re.compile(r"fizzle", re.I)),
    ("reagents", re.compile(r"more reagents|reagents are needed", re.I)),
    ("mana", re.compile(r"not have enough mana|insufficient mana", re.I)),
    ("overloaded", re.compile(r"too heavy|overload|weigh", re.I)),
    ("cannot_see", re.compile(r"cannot see|can't see|line of sight", re.I)),
    ("wait", re.compile(r"must wait", re.I)),
]


class Notes:
    """The playtest's findings, one JSON line each. `key` dedupes: the same finding is recorded once."""

    def __init__(self, path):
        self.path = path
        self.seen = {}

    def add(self, category, text, key=None, **evidence):
        key = key or f"{category}:{text}"
        self.seen[key] = self.seen.get(key, 0) + 1
        if self.seen[key] > 1:
            return
        entry = {"t": time.strftime("%H:%M:%S"), "category": category, "text": text, **evidence}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"  NOTE [{category}] {text}", flush=True)


class Bot:
    def __init__(self, name, admin):
        self.name = name
        self.c = connect(name)
        self.admin = connect(admin) if admin else None
        self.notes = Notes(os.path.join(OUT, "notes.jsonl"))
        self.journal = deque(maxlen=400)
        self.tick_no = 0
        self.last_rule = ""
        self.kills = 0
        self.deaths = 0
        self.facts = {"seen": {}, "looted": set(), "potion_effects": {}, "ghost_since": None}
        self.log_path = os.path.join(OUT, "run.log")
        self.knowledge_path = os.path.join(OUT, "knowledge.json")
        try:
            with open(self.knowledge_path, encoding="utf-8") as f:
                self.facts["death_spots"] = [tuple(p) for p in json.load(f).get("death_spots", [])]
        except (OSError, ValueError):
            self.facts["death_spots"] = []
        self.spots = deque([(1380, 1560), (1300, 1520), (1260, 1495), (1450, 1450), (1600, 1500), (1650, 1700), (1450, 1850)])

    # ---- plumbing --------------------------------------------------------------------------------------------

    def log(self, msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def read_journal(self):
        out = []
        for e in self.c.events.poll():
            t = e.text
            if t.startswith("[LABEL]") and t.rstrip().endswith("corpse"):
                self.kills += 1
                self.log(f"kill #{self.kills}: {t.split(": ",1)[-1]}")
            if t.startswith(("[GUMP]", "[CMD", "[CONTAINER]", "[PERF]", "[NAV]", "[LABEL]", "[WARN", " ")):
                continue
            self.journal.append(t)
            out.append(t)
            for tag, pat in FAIL_PATTERNS:
                if pat.search(t):
                    self.facts["last_fail"] = (tag, t, time.time())
                    self.notes.add("message", f"Game message seen: {t[:100]}", key=f"msg:{t[:60]}")
        return out

    def cmd(self, line, timeout=8.0):
        return [l for l in self.c.call(line, timeout=timeout) if not l.startswith("[GUMP]")]

    def find_gump(self, word):
        """The server serial of the open gump whose text mentions `word`, or None. (`gumps` lists every open gump, the Welcome guide included.)"""
        serial = None
        found = None
        for line in self.c.call("gumps", timeout=8):
            m = re.match(r"\[GUMP\] local \S+ server (0x[0-9A-Fa-f]+)", line)
            if m:
                serial = m.group(1)
            elif word in line and serial and not found:
                found = serial
        return found

    def hp_pct(self):
        return 100.0 * self.c.hp / max(1, self.c.max_hp)

    def mobs(self, within):
        """Hostile-looking mobiles. An orc with a personal name ("Dilug") only shows as Criminal-colored, so notoriety is what counts."""
        return [m for m in self.c.mobiles(within=within) if m.notoriety in ("Gray", "Criminal", "Enemy", "Murderer")]

    @staticmethod
    def is_prey(m):
        n = m.name.lower()
        # animals are called "a rat"; a monster with a personal name ("Dilug", an orc) is never prey
        if not n.startswith(("a ", "an ")):
            return False
        return m.notoriety == "Gray" and any(w in n for w in SAFE_PREY) and not any(w in n for w in DANGEROUS)

    def prey(self, within=9):
        return [m for m in self.mobs(within) if self.is_prey(m)]

    def dangers(self, within=8):
        return [m for m in self.mobs(within) if not self.is_prey(m)]

    # ---- rules, in priority order -----------------------------------------------------------------------------

    def r_dead(self):
        """A ghost: the way a new player gets home is to walk to a healer and accept the offer."""
        if not self.c.ghost:
            self.facts["ghost_since"] = None
            return False
        if self.facts["ghost_since"] is None:
            self.facts["ghost_since"] = time.time()
            self.deaths += 1
            self.facts.setdefault("death_spots", []).append((self.c.x, self.c.y))
            with open(self.knowledge_path, "w", encoding="utf-8") as f:
                json.dump({"death_spots": self.facts["death_spots"]}, f)
            self.notes.add("death", "The character died.", key=f"death{self.deaths}", pos=[self.c.x, self.c.y], last=list(self.journal)[-4:])
            self.log("DEAD at %d,%d; walking to the healer as a ghost" % (self.c.x, self.c.y))
        waited = time.time() - self.facts["ghost_since"]
        serial = self.find_gump("Resurrection")
        if serial:
            self.log("the healer's offer is open; accepting")
            self.notes.add("death", "A healer's resurrection offer opens as a gump when the ghost walks up to the healer; it offers CONTINUE and CANCEL.", key="healergump")
            self.c.call(f"gumpresponse 1 gump:{serial}", timeout=8)
            time.sleep(3)
            return True
        near = abs(self.c.x - HEALER[0]) <= 6 and abs(self.c.y - HEALER[1]) <= 6
        if near:
            if not self.facts.get("waiting_noted"):
                self.facts["waiting_noted"] = True
                self.log("near the healer, waiting for the offer")
            time.sleep(2)
        elif waited < 240:
            res = self.c.goto(*HEALER).wait(timeout=5)
            if res and res.startswith("nopath"):
                self.notes.add("death", "A ghost's route to the healer failed: no path.", key="ghostnopath")
            return True
        if self.c.ghost and waited > 240 and self.admin:
            self.notes.add("tooling", "The ghost could not get resurrected by a healer in 4 minutes; a staff resurrect ended the run's stall.", key="staffres")
            self.admin.say("[go %d %d" % (self.c.x, self.c.y))
            time.sleep(1.5)
            from staff_command import staff_target
            staff_target(self.admin, "[resurrect", self.c.state["charID"])
            time.sleep(2)
        return True

    def r_flee(self):
        """Low health with something hostile close: heal, drink or run, in that order."""
        danger = self.dangers(10) or self.prey(3)
        if self.hp_pct() >= 40 or not danger:
            return False
        if self.c.mana >= 4:
            self.log(f"emergency heal at {self.c.hp}")
            self.cast("heal", "self")
            return True
        if self.drink_unknown_potion():
            return True
        self.log(f"fleeing from {danger[0].name} at hp {self.c.hp}")
        self.notes.add("combat", "At low health a new mage with no mana and no known healing potion can only run; nothing says which colored potion heals.", key="nopotionknowledge")
        self.go_town()
        return True

    def r_avoid(self):
        """A grey that is not on the safe list within seven tiles: leave, quietly."""
        ds = self.dangers(7)
        if not ds:
            return False
        d = ds[0]
        if d.distance <= 8 and self.c.mana >= 4 and self.hp_pct() > 40:
            # it caught up (a new mage cannot outrun anything): fight back rather than be hit in the back
            if not self.c.war_mode:
                self.c.war(True)
            self.log(f"cornered by {d.name}; magic arrow at {d.distance} tiles, hp {self.c.hp} mana {self.c.mana}")
            self.notes.add("combat", f"A {d.name} that follows a new mage into Britain is not stopped by the town: the mage must fight it with its starting mana.", key="followed", name=d.name)
            self.cast("magic arrow", d.serial)
            return True
        self.log(f"avoiding {d.name} ({d.notoriety}) {d.distance} tiles away")
        self.notes.add("danger", f"Hostile {d.name!r} within {d.distance} tiles of a new mage in town: nothing warns the player or deals with it.", key=f"danger:{d.name}", dist=d.distance)
        self.step_away(d, 7)
        return True

    def r_heal(self):
        want = 55 if not self.mobs(9) else 45
        if self.hp_pct() >= want or self.c.mana < 4:
            return False
        self.cast("heal", "self")
        return True

    def r_fight(self):
        ps = self.prey(9)
        fail = self.facts.get("last_fail")
        if fail and fail[0] == "reagents" and time.time() - fail[2] < 60:
            return False  # no reagents: spells fizzle for free, so go and buy some
        if not ps:
            return False
        t = ps[0]
        if not self.c.war_mode:
            self.c.war(True)
        if self.c.mana < 4:
            self.notes.add("combat", "A new mage runs out of mana after about nine spells and has no quick way to recover it (no Meditation).", key="oom")
            self.log("out of mana: backing off to rest")
            self.go_town()
            return True
        if t.distance <= 1:
            self.step_away(t)
            return True
        self.log(f"magic arrow at {t.name} ({t.distance} tiles) mana {self.c.mana}")
        self.cast("magic arrow", t.serial)
        return True

    def r_loot(self):
        for it in list(self.c.containers(within=2)) + list(self.c.items(within=2)):
            if "corpse" in it.name.lower() and it.serial not in self.facts["looted"]:
                self.facts["looted"].add(it.serial)
                try:
                    contents = self.c.container(it.serial, timeout=4)
                except Exception:
                    contents = []
                self.log(f"corpse {it.name}: {[str(x) for x in contents]}")
                if not contents:
                    self.notes.add("loot", "An empty corpse still opens by itself; nothing says it was worthless before it opens.", key="emptycorpse")
                return True
        return False

    def r_hunt(self):
        spots = self.facts.get("death_spots", [])
        ps = [m for m in self.prey(16) if m.distance > 8 and not any(abs(m.x - dx) < 70 and abs(m.y - dy) < 70 for dx, dy in spots)]
        if not ps or self.c.mana < 12 or self.hp_pct() < 70:
            return False
        t = ps[0]
        self.log(f"approach {t.name} ({t.distance} tiles)")
        self.c.goto(t.x, t.y).wait(timeout=4)
        return True

    def r_rest(self):
        """Safe, but hurt or out of mana: stand still, heal what can be healed."""
        if self.mobs(10):
            return False
        mana_max = self.c.state.get("maxMana", 39)
        if self.c.mana >= mana_max * 0.85 and self.hp_pct() >= 85:
            return False
        if self.c.war_mode:
            self.c.war(False)
        if self.c.hp < self.c.max_hp - 15 and self.c.mana >= 4:
            self.cast("heal", "self")
            return True
        if self.c.mana < mana_max * 0.7 and time.time() > self.facts.get("med_until", 0):
            # the only quick way to get mana back is the Meditation skill; a new player is not told so, the bot tries it as a curious player would
            self.cmd("useskill meditation")
            time.sleep(1.5)
            for line in self.read_journal():
                if "medit" in line.lower() or "concentrat" in line.lower() or "trance" in line.lower():
                    self.notes.add("meditation", f"Using Meditation answered: {line[:90]}", key=f"med:{line[:40]}")
            self.facts["med_until"] = time.time() + 12
            return True
        if not self.facts.get("rest_noted"):
            self.facts["rest_noted"] = True
            self.log(f"resting: mana {self.c.mana}/{mana_max}, hp {self.c.hp}/{self.c.max_hp}")
        time.sleep(3)
        return True

    def reagent_counts(self):
        """Reagents the bot can see: everything named like a reagent in the backpack and in the bags in it."""
        names = ("black pearl", "blood moss", "bloodmoss", "garlic", "ginseng", "mandrake", "nightshade", "sulfurous", "spider")
        counts = {}
        for it in self.c.backpack:
            low = it.name.lower()
            if any(n in low for n in names):
                counts[it.name] = counts.get(it.name, 0) + (it.amount or 1)
            elif it.name.lower() in ("bag", "backpack", "pouch"):
                try:
                    for sub in self.c.container(it.serial, timeout=3):
                        if any(n in sub.name.lower() for n in names):
                            counts[sub.name] = counts.get(sub.name, 0) + (sub.amount or 1)
                except Exception:
                    pass
        return counts

    def r_resupply(self):
        """Out of reagents (or once after the first hunt): walk to the mage shop, open the vendor's list and buy what casting uses."""
        fail = self.facts.get("last_fail")
        out_of_regs = bool(fail and fail[0] == "reagents" and time.time() - fail[2] < 60)
        if not out_of_regs and (self.facts.get("shopped") or self.kills < 3):
            return False
        if self.mobs(10) or self.hp_pct() < 60:
            return False
        self.facts["shopped"] = True
        if out_of_regs:
            self.facts["last_fail"] = None
            self.notes.add("shop", "Casting stopped with 'More reagents are needed for this spell.'; the starting reagents do not last one hunt.", key="oor")
        self.log(f"resupply: reagents {self.reagent_counts()}; gold {self.c.gold}")
        res = self.c.goto(1485, 1553).wait(timeout=90)
        self.log(f"walk to the mage shop: {res}, now at {self.c.x},{self.c.y}")
        stock = []
        for vendor in [m for m in self.c.mobiles(within=6) if m.notoriety == "Innocent" and m.name]:
            self.log(f"vendor candidate: {vendor.name} at {vendor.distance} tiles")
            self.c.events.drain()
            self.c.say(f"{vendor.name.split()[0]} buy")
            time.sleep(2.5)
            stock = self.cmd("shop", timeout=10)
            if len(stock) >= 2:
                break
        self.log(f"shop listing: {len(stock)} lines; first: {stock[:3]}")
        if len(stock) < 2:
            self.notes.add("shop", "Saying '<name> buy' to each person at the Mage shop opened no shop list: a new player has to know the vendor-name-plus-buy trick (or double-click the vendor).", key="noshop")
            return True
        self.notes.add("shop", "The mage shop sells: " + "; ".join(l.strip()[11:60] for l in stock[1:]), key="shopstock")
        cart = []
        spent_plan = 0
        for line in stock:
            m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
            if not m:
                continue
            serial, price, avail, name = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4).strip()
            if any(w in name.lower() for w in ("pearl", "moss", "garlic", "ginseng", "mandrake", "nightshade", "sulfur", "spider")):
                budget = self.c.gold if self.c.gold < 200 else self.c.gold // 3
                want = min(avail, 30, max(0, (budget - spent_plan) // max(price, 1) // 4))
                if want > 0:
                    cart += [serial, str(want)]
                    spent_plan += want * price
                    self.log(f"  buying {want} {name} at {price}gp")
        if cart:
            self.cmd("buy " + " ".join(cart), timeout=10)
            time.sleep(3)
            self.notes.add("shop", f"Bought reagents; gold {self.c.gold}; reagents now {self.reagent_counts()}", key="bought")
        return True
    def r_train(self):
        """Once after shopping: ask the Mages' Guildmaster (the other person at the Mage shop) what he can teach."""
        if self.facts.get("trained") or not self.facts.get("shopped") or self.mobs(10) or self.hp_pct() < 60:
            return False
        self.facts["trained"] = True
        res = self.c.goto(1485, 1553).wait(timeout=90)
        masters = [m for m in self.c.mobiles(within=8) if m.notoriety == "Innocent" and ("mage" in m.name.lower() or True)]
        self.log(f"at the mage guild: {res}; people near: {[m.name for m in masters][:6]}")
        for m in masters[:3]:
            self.c.events.drain()
            self.c.say(f"{m.name.split()[0]} train")
            time.sleep(2.5)
            lines = [l for l in self.read_journal() if l.strip()]
            gumps = [l for l in self.c.call("gumps", timeout=8) if not l.startswith("[GUMP]")]
            self.log(f"asked {m.name} to train: journal {lines[-3:]}")
            if any("train" in g.lower() or "teach" in g.lower() for g in gumps + lines):
                self.notes.add("training", f"Asking {m.name} to 'train' answered: {(lines or gumps)[-1][:110]}", key=f"train:{m.name}")
        return True

    def r_explore(self):
        # a place that has killed the mage once is not walked to again (the tree learns the map)
        for _ in range(len(self.spots)):
            x, y = self.spots[0]
            if any(abs(x - dx) < 70 and abs(y - dy) < 70 for dx, dy in self.facts.get("death_spots", [])):
                self.log(f"skipping {x},{y}: it killed the mage before")
                self.spots.rotate(-1)
            else:
                break
        x, y = self.spots[0]
        res = self.c.goto(x, y).wait(timeout=4)
        if abs(self.c.x - x) < 4 and abs(self.c.y - y) < 4:
            self.log(f"reached {x},{y}")
            self.spots.rotate(-1)
        elif res and res.startswith(("nopath", "blocked")):
            self.log(f"no way to {x},{y}: {res[:60]}")
            self.spots.rotate(-1)
        return True

    RULES = ["r_dead", "r_flee", "r_avoid", "r_heal", "r_fight", "r_loot", "r_resupply", "r_train", "r_hunt", "r_rest", "r_explore"]

    # ---- actions ----------------------------------------------------------------------------------------------

    def cast(self, spell, target):
        command, _ = SPELLS[spell]
        self.c.events.drain()
        self.cmd(command)
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=3.0) is None:
            self.notes.add("cast", f"Casting {spell} raised no target cursor.", key=f"nocursor:{spell}")
            return False
        if target == "self":
            self.c.target_self()
        else:
            self.c.target(target)
        time.sleep(2.0)
        self.read_journal()
        return True

    def drink_unknown_potion(self):
        """Starter potions are three unnamed colors: try one, see what it does, remember."""
        tried = self.facts["potion_effects"]
        for item in self.c.backpack:
            if "potion" in item.name.lower() and item.name not in tried:
                before = self.c.hp
                self.c.use(item.serial)
                time.sleep(2)
                tried[item.name] = self.c.hp - before
                self.notes.add("potions", f"Drinking {item.name!r} at low health changed hit points by {tried[item.name]:+d}; colors give no hint what they do.", key=f"pot:{item.name}")
                return True
        for item in self.c.backpack:
            if "potion" in item.name.lower() and tried.get(item.name, 0) > 0:
                self.c.use(item.serial)
                time.sleep(1.5)
                return True
        return False

    def step_away(self, m, dist=3):
        dx = self.c.x - m.x
        dy = self.c.y - m.y
        self.c.goto(self.c.x + (dist if dx >= 0 else -dist), self.c.y + (dist if dy >= 0 else -dist)).wait(timeout=3)

    def go_town(self):
        return self.c.goto(*TOWN).wait(timeout=4)

    # ---- main loop --------------------------------------------------------------------------------------------

    def observe(self):
        if self.tick_no % 15 == 0:
            self.log(f"tick {self.tick_no} hp {self.c.hp}/{self.c.max_hp} mana {self.c.mana} stam {self.c.stamina} at ({self.c.x},{self.c.y}) weight {self.c.weight}/{self.c.max_weight} kills {self.kills} deaths {self.deaths}")
        for m in self.c.mobiles(within=14):
            if m.name not in self.facts["seen"] and m.notoriety != "Innocent":
                self.facts["seen"][m.name] = (m.x, m.y, m.notoriety)
                kind = "prey" if self.is_prey(m) else "DANGER"
                self.log(f"first sight of {m.name!r} ({m.notoriety}, {kind}) at {m.x},{m.y}")
        if self.c.overloaded:
            self.notes.add("weight", "The new mage is overloaded and cannot move at full pace.", key="overload")

    def run(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            self.tick_no += 1
            try:
                self.read_journal()
                self.observe()
                acted = None
                for name in self.RULES:
                    if getattr(self, name)():
                        acted = name
                        break
                if acted != self.last_rule:
                    self.log(f"rule -> {acted}")
                    self.last_rule = acted
                if acted is None:
                    self.notes.add("stuck", "No rule handled the situation.", key=f"stuck:{self.tick_no // 50}")
                    time.sleep(1)
            except Exception as e:
                self.log(f"EXCEPTION {type(e).__name__}: {e}")
                self.notes.add("bot", f"Exception in tick: {type(e).__name__}: {e}", key=f"exc:{type(e).__name__}:{e}")
                time.sleep(1)
        self.log(f"done: ticks {self.tick_no}, kills {self.kills}, deaths {self.deaths}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="MageP")
    ap.add_argument("--admin", default="admin")
    ap.add_argument("--for", dest="seconds", type=float, default=600)
    args = ap.parse_args()
    Bot(args.name, args.admin).run(args.seconds)


if __name__ == "__main__":
    sys.exit(main())
