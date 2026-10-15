"""The shared body of every farm bot: a connection to its client, a journal reader, notes, a status heartbeat and the behaviors every player needs
whatever the profession (walking home as a ghost, running from a fight it is losing, banking, shopping, looting, resting).

A brain (hunter.py, crafter.py, gatherer.py) adds its own rules and lists them in RULES; the first rule that acts wins each tick, as in the new-mage
bot this grew out of. Findings go to work/botfarm/notes.jsonl, one line each tagged with the bot and its profession, so many bots' notes can be
counted together (aggregate.py). Everything the bot does goes through the commands a player has.
"""
from __future__ import annotations

import faulthandler
import json
import math
import os
import re
import sys
import time
import traceback
from collections import deque
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
FARM = os.path.join(ROOT, "work", "botfarm")
os.makedirs(FARM, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "Navrey", "cli"))
sys.path.insert(0, os.path.join(ROOT, ".claude", "scripts"))

from navrey_session import connect  # noqa: E402
from uo import Event  # noqa: E402
from memory import MEMDIR, SharedMemory, cell_of  # noqa: E402

HEALER = (1472, 1611)
TOWN = (1470, 1620)
BANKS = [(1425, 1690), (1650, 1608)]
# Places in Britain to run to. Everyone used to run to TOWN, beside the healer, and a gazer that followed a fleeing bot in killed it (and the next
# ghost to be resurrected) on the healer's doorstep: guards act only on criminals and murderers, not on an ordinary monster.
REFUGES = [(1470, 1620), (1425, 1690), (1650, 1608), (1430, 1600), (1481, 1584), (1469, 1668)]
# the Britain TownRegion's rectangles (x0, y0, x1, y1) from the server's Data/regions.json
BRITAIN = [(1416, 1498, 1740, 1777), (1500, 1408, 1546, 1498), (1385, 1538, 1416, 1777), (1416, 1777, 1740, 1837), (1385, 1777, 1416, 1907), (1093, 1538, 1385, 1907)]
MAGE_SHOP = (1485, 1553)

PROFESSIONS = {
    8: "Archer", 9: "Bard", 10: "Ranger", 11: "PureMage", 12: "Warlock", 13: "MaceFighter", 14: "Fencer", 15: "Swordsman",
    16: "Blacksmith", 17: "Carpenter", 18: "Tailor", 19: "Tinker", 20: "AnimalTamer", 21: "Fisherman", 22: "Prospector", 23: "Sorcerer",
}

# messages worth remembering as findings the first time a bot sees them (the digits are removed so "takes 5" and "takes 7" are one)
IGNORE_PREFIX = ("[GUMP]", "[CMD", "[CONTAINER]", "[PERF]", "[NAV]", "[LABEL]", "[WARN", " ", "Said (", "War mode", "Attack cleared", "Walking to", "Used ", "Targeted",
                 "Dropped", "Grabbed", "Casting", "Equipped", "Unequipped", "[TARGET]", "Target cancelled", "Damage:", "Skill ", "[BOOK]", "Entered")


def norm_msg(t: str) -> str:
    t = re.sub(r"\d+(\.\d+)?", "#", t)
    t = re.sub(r"0x[0-9A-Fa-f]+", "0x#", t)
    return t.strip()[:120]


class Notes:
    def __init__(self, bot, profession):
        self.bot = bot
        self.profession = profession
        self.seen = {}
        self.path = os.path.join(FARM, "notes.jsonl")

    def add(self, category, text, key=None, **evidence):
        key = key or f"{category}:{text[:80]}"
        self.seen[key] = self.seen.get(key, 0) + 1
        if self.seen[key] > 1:
            return
        entry = {"t": time.strftime("%H:%M:%S"), "bot": self.bot, "profession": self.profession, "category": category, "text": text, "key": key, **evidence}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class BotBase:
    RULES: list = []

    def __init__(self, name: str, profession: int):
        self.name = name
        self.profession = profession
        self.pname = PROFESSIONS.get(profession, str(profession))
        self.c = connect(name)
        self._wrap_goto()
        self.dir = os.path.join(FARM, name)
        os.makedirs(self.dir, exist_ok=True)
        self.notes = Notes(name, self.pname)
        # "newbie" bots play only on what a new player can see: no monster table, no craft skill windows, no taming table. They learn from what
        # happens to them and share that among newbies only (their own memory folder). The gap between newbie and veteran bots of one profession
        # (deaths, gold, skill gain per hour) measures what the game does not tell its players.
        self.mode = os.environ.get("BOT_MODE", "veteran")
        self.mem = SharedMemory(self.pname, name, root=MEMDIR + ("-newbie" if self.mode == "newbie" else ""))
        self.journal = deque(maxlen=300)
        self.tick_no = 0
        self.last_rule = ""
        self.kills = 0
        self.deaths = 0
        self.facts = {"looted": set(), "ghost_since": None, "bank_balance": 0, "seen_msgs": set()}
        if self.c.ghost:
            self.facts["ghost_since"] = time.time()          # already dead when this brain started: the death was counted by the brain before
        self.stats = {"gains": {}, "loot": {}, "casts": {}, "swings": 0, "damage_taken": 0, "kills_by": {}}
        self.skill_values = {}
        self.activity = ""
        self.started = time.time()
        self.log_path = os.path.join(self.dir, "run.log")
        self.know_path = os.path.join(self.dir, "knowledge.json")
        self.death_spots = []
        try:
            self.death_spots = [tuple(p) for p in json.load(open(self.know_path, encoding="utf-8")).get("death_spots", [])]
        except (OSError, ValueError):
            pass
        self.last_status = 0.0
        self.last_gold = 0
        self.episode = None
        self.work = 0                    # productive results that are not kills or gold: a catch, a craft, ore dug, a tame, a meal cooked
        self.decisions_path = os.path.join(self.dir, "decisions.jsonl")
        self.last_presence = 0.0
        self.totals_path = os.path.join(self.dir, "totals.json")
        self.base = {"kills": 0, "deaths": 0, "gains": {}, "uptime": 0}
        try:
            self.base.update(json.load(open(self.totals_path, encoding="utf-8")))
        except (OSError, ValueError):
            pass

    # ---- plumbing --------------------------------------------------------------------------------------------

    def log(self, msg):
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

    def note(self, category, text, key=None, **ev):
        self.notes.add(category, text, key, **ev)

    def cmd(self, line, timeout=8.0):
        return [l for l in self.c.call(line, timeout=timeout) if not l.startswith("[GUMP]")]

    def hp_pct(self):
        return 100.0 * self.c.hp / max(1, self.c.max_hp)

    def read_journal(self):
        out = []
        for e in self.c.events.poll():
            t = e.text
            # (a "[LABEL] ... corpse" line is any corpse that comes into view, other bots' kills included: kills are counted by the fight that made them)
            m = re.search(r"Your skill in (.+?) has increased by (\d+(?:\.\d+)?)\.\s+It is now (\d+(?:\.\d+)?)", t)
            if m:
                self.stats["gains"][m.group(1)] = self.stats["gains"].get(m.group(1), 0) + 1
                self.skill_values[m.group(1)] = float(m.group(3))
                self.mem.record("gain", scope="prof", skill=m.group(1), action=self.activity or "?", value=float(m.group(3)))
            d = re.match(r"Damage: (.+?) takes (\d+)", t)
            if d and d.group(1).startswith(self.name):
                self.stats["damage_taken"] += int(d.group(2))
            if t.startswith(IGNORE_PREFIX):
                continue
            self.journal.append(t)
            out.append(t)
            own = t.startswith(f"[SAY] {self.name}:")
            if re.match(r"\[SAY\] Bot\w+:", t) and not own:
                continue                      # another bot talking to a banker or vendor
            if own and re.match(rf"\[SAY\] {self.name}: (bank|balance|withdraw|guards|all release|\w+ (buy|sell|train)\b)", t, re.I):
                continue                      # what this bot said itself
            body = re.sub(r"^\[(SYSTEM|SAY)\]\s*", "", t)
            # the server's overhead messages to the character itself ("*You feel a bit nauseous*", "The spell fizzles.") come as speech under its own name
            tag = "system" if t.startswith("[SYSTEM]") else ("self" if own else ("npc" if t.startswith("[SAY]") else ""))
            if own:
                body = body[len(self.name) + 2:]
            if tag:
                k = norm_msg(body)
                if k not in self.facts["seen_msgs"]:
                    self.facts["seen_msgs"].add(k)
                    self.note("message", f"{tag}: {body[:140]}", key=f"msg:{k}")
        self.status()
        return out

    def find_gump(self, word):
        serial = None
        found = None
        for line in self.c.call("gumps", timeout=8):
            m = re.match(r"\[GUMP\] local \S+ server (0x[0-9A-Fa-f]+)", line)
            if m:
                serial = m.group(1)
            elif word in line and serial and not found:
                found = serial
        return found

    def mobs(self, within):
        """Hostile-looking mobiles that are on this floor: one more than ~14 up or down (a rat in the cellar under Britain) cannot be fought or fought by."""
        return [m for m in self.c.mobiles(within=within) if m.notoriety in ("Gray", "Criminal", "Enemy", "Murderer") and abs((m.pos[2] or 0) - self.c.z) <= 14 and m.name != "Generic Player"]

    def near_death_spot(self, x, y, r=60):
        return any(abs(x - dx) < r and abs(y - dy) < r for dx, dy in self.death_spots)

    def _wrap_goto(self):
        """Every walk that ends in "nopath" gets one more try after a single step to a free neighbouring tile. From two tiles at the dig spot north
        of Britain (1456,1526 and 1457,1526) the planner could not expand at all, though the bot had walked in; a player would just take a step."""
        orig = self.c.goto
        bot = self

        def goto(x, y, z=None):
            walk = orig(x, y, z)
            first_wait = walk.wait

            def wait(timeout=300.0, poll=0.1):
                res = first_wait(timeout=timeout, poll=poll)
                if str(res).startswith("nopath") and bot.step_out():
                    res = orig(x, y, z).wait(timeout=timeout, poll=poll)
                    bot.log(f"after a step out, the walk to {x},{y}: {res}")
                return res

            walk.wait = wait
            return walk

        self.c.goto = goto

    def step_out(self):
        """One step in the first direction that moves the character; at most once every 20 seconds."""
        if time.time() - self.facts.get("stepped_out_at", 0) < 20:
            return False
        self.facts["stepped_out_at"] = time.time()
        x0, y0 = self.c.x, self.c.y
        for d in ("s", "e", "w", "n", "se", "sw", "ne", "nw"):
            try:
                self.c.call(f"walk {d}", timeout=4)
            except Exception:
                continue
            time.sleep(0.7)
            if (self.c.x, self.c.y) != (x0, y0):
                self.log(f"no path from {x0},{y0}: stepped {d} to {self.c.x},{self.c.y} and tried again")
                self.mem.record("blocked", kind="tile", key=f"{x0},{y0}", ttl=3600)
                return True
        self.log(f"no path from {x0},{y0}, and no step in any direction moved the character")
        return False

    def ground_items(self, rng=8):
        """Every item near, immovable ones too (a campfire, a forge, a training dummy): the `items` command, because Client.items() leaves scenery out."""
        out = []
        for l in self.c.call(f"items {rng}", timeout=8):
            m = re.match(r"\s*(?:\[fixed\]\s+)?(0x[0-9A-Fa-f]+)\s+(.+?)\s+d=(\d+)\s+\((-?\d+),\s*(-?\d+),\s*(-?\d+)\)", l)
            if m:
                out.append(SimpleNamespace(serial=m.group(1), name=m.group(2).strip(), distance=int(m.group(3)), x=int(m.group(4)), y=int(m.group(5)), z=int(m.group(6))))
        return out

    def los(self, serial):
        """Is there a clear line of sight to this mobile? (the `los` command; a spell or arrow at something behind a wall is lost without a word)"""
        now = time.time()
        if now - getattr(self, "_los_at", 0) > 0.8:
            self._los = {}
            for l in self.c.call("los 12", timeout=6):
                m = re.match(r"\s+(YES|no)\s+(0x[0-9A-Fa-f]+)", l)
                if m:
                    self._los[m.group(2).upper()] = m.group(1) == "YES"
            self._los_at = now
        return self._los.get(serial.upper(), True)

    def travel(self, x, y, near=2, tries=8, per=60):
        """Walk to (x, y) in hops: a destination beyond the client's loaded map is reached in several goto calls."""
        for _ in range(tries):
            if max(abs(self.c.x - x), abs(self.c.y - y)) <= near:
                return True
            before = (self.c.x, self.c.y)
            res = self.c.goto(x, y).wait(timeout=per)
            if self.c.ghost or self.mobs(5):
                return False
            if (self.c.x, self.c.y) == before and str(res).startswith(("nopath", "blocked")):
                return False
        return max(abs(self.c.x - x), abs(self.c.y - y)) <= near

    def status(self, force=False):
        if not force and time.time() - self.last_status < 10:
            return
        self.last_status = time.time()
        gains = dict(self.base["gains"])
        for k, v in self.stats["gains"].items():
            gains[k] = gains.get(k, 0) + v
        s = {
            "name": self.name, "profession": self.pname, "t": time.time(), "uptime": self.base["uptime"] + int(time.time() - self.started), "rule": self.last_rule, "activity": self.activity,
            "hp": self.c.hp, "max_hp": self.c.max_hp, "mana": self.c.mana, "stam": self.c.stamina, "pos": [self.c.x, self.c.y], "gold": self.c.gold,
            "weight": [self.c.weight, self.c.max_weight], "ghost": self.c.ghost, "kills": self.base["kills"] + self.kills, "deaths": self.base["deaths"] + self.deaths, "gains": gains,
            "skills": dict(sorted(self.skill_values.items(), key=lambda kv: -kv[1])[:6]), "tick": self.tick_no,
            "all_skills": {k: v for k, v in sorted(self.skill_values.items()) if v > 0}, "mode": self.mode,
            **getattr(self, "status_extra", {}),
        }
        with open(os.path.join(self.dir, "status.json"), "w", encoding="utf-8") as f:
            json.dump(s, f)
        with open(self.totals_path, "w", encoding="utf-8") as f:
            json.dump({"kills": s["kills"], "deaths": s["deaths"], "gains": gains, "uptime": s["uptime"]}, f)

    def refresh_skills(self):
        for line in self.c.call("skills", timeout=8):
            m = re.match(r"\[SKILL\]\s+(.+?)\s+(\d+\.\d)\s+\(base", line)
            if m:
                self.skill_values[m.group(1).strip()] = float(m.group(2))

    # ---- rules every profession has -----------------------------------------------------------------------------

    def r_dead(self):
        if not self.c.ghost:
            if self.facts["ghost_since"] is not None:
                self.facts["just_resurrected"] = True
                if self.c.war_mode:
                    self.c.war(False)
                # step clear of the healer before resting: seven resurrected bots once rested on its four tiles, and the next ghost could not get in
                if max(abs(self.c.x - HEALER[0]), abs(self.c.y - HEALER[1])) <= 4:
                    ring = [(HEALER[0] + dx, HEALER[1] + dy) for dx, dy in ((8, 0), (-8, 0), (0, 8), (0, -8), (6, 6), (-6, 6), (6, -6), (-6, -6))]
                    others = [m for m in self.c.mobiles(within=16) if m.name and m.name.startswith("Bot")]
                    spot = min(ring, key=lambda p: sum(1 for m in others if max(abs(m.x - p[0]), abs(m.y - p[1])) <= 2))
                    self.c.goto(*spot).wait(timeout=15)
            self.facts["ghost_since"] = None
            return False
        if self.facts["ghost_since"] is None:
            self.facts["ghost_since"] = time.time()
            self.deaths += 1
            self.facts["war_at_death"] = self.c.war_mode
            self.log(f"ghost at {self.c.x},{self.c.y}; war mode at death = {self.c.war_mode}")
            self.death_spots.append((self.c.x, self.c.y))
            self.mem.record("death", cell=cell_of(self.c.x, self.c.y), killers=[t[2] for t in getattr(self, "recent_threats", [])[:3]])
            on_run = time.time() - self.facts.get("corpse_run_at", 0) < 400
            # killed again while fetching the corpse: whatever killed it is still there, so this corpse is not worth a second walk
            self.facts["corpse"] = {"xy": (self.c.x, self.c.y), "t": time.time(), "gold": self.last_gold, "tries": 1 if on_run else 0}
            if on_run:
                self.note("death", f"Going back for its corpse got the {self.pname} killed again; the killer was still there and nothing warned it.", key="corpsetrap")
            json.dump({"death_spots": self.death_spots}, open(self.know_path, "w", encoding="utf-8"))
            self.note("death", f"A {self.pname} died.", key=f"death:{self.deaths}", pos=[self.c.x, self.c.y], last=list(self.journal)[-4:])
            threats = getattr(self, "recent_threats", [])
            killer = threats[0][1] if threats else "nothing seen"
            self.log(f"DEAD at {self.c.x},{self.c.y} (killed by {killer}); walking to the healer")
        self.activity = "ghost: walking to the healer"
        # a living mobile sees a dead one only if it is in war mode (Mobile.CanSee), so a ghost in peace mode is invisible to the healer: switch it on
        if not self.c.war_mode:
            self.c.war(True)
            self.note("death", "A ghost in peace mode is invisible to the healer (the game only shows a ghost to the living in war mode); nothing tells the player to switch to war mode.", key="ghostwar")
        serial = self.find_gump("Resurrection")
        if serial:
            self.log(f"resurrection offer opened; ghost war mode = {self.c.war_mode} (at death: {self.facts.get('war_at_death')})")
            self.c.call(f"gumpresponse 1 gump:{serial}", timeout=8)
            self.note("death", "The healer's offer opens as a Resurrection gump (CONTINUE / CANCEL) once the ghost stands near the healer.", key="healergump")
            time.sleep(3)
            return True
        if abs(self.c.x - HEALER[0]) <= 6 and abs(self.c.y - HEALER[1]) <= 6:
            # the healer offers when a ghost walks INTO range, not while it stands there: step out and back in after a while
            since = self.facts.setdefault("near_since", time.time())
            if time.time() - since > 25:
                self.facts["near_since"] = time.time()
                self.note("death", "A ghost that stands next to the healer is never offered a resurrection; it has to walk away and come back (nothing tells the player).", key="ghostwalk")
                self.c.goto(HEALER[0], HEALER[1] + 9).wait(timeout=15)
                self.c.goto(*HEALER).wait(timeout=15)
            time.sleep(2)
        else:
            self.facts.pop("near_since", None)
            self.c.goto(*HEALER).wait(timeout=5)
        return True

    def r_corpse(self):
        """Back from the dead: go and fetch the belongings from the corpse before it rots (the death message says to), once, if there was something worth the walk."""
        info = self.facts.get("corpse")
        if not info or self.c.ghost or info["tries"] >= 1:
            return False
        if time.time() - info["t"] > 420:
            self.facts.pop("corpse")
            return False
        if self.hp_pct() < 70 or self.threats(8):
            return False
        if info["gold"] < 60:
            self.facts.pop("corpse")
            return False
        info["tries"] += 1
        x, y = info["xy"]
        if self.mem.dangerous_cell(cell_of(x, y)):
            self.log(f"not going back to the corpse at {x},{y}: the shared memory says bots die there")
            self.facts.pop("corpse")
            return False
        self.facts["corpse_run_at"] = time.time()
        self.activity = "going back for my corpse"
        self.log(f"going back to the corpse at {x},{y} ({info['gold']} gold lost)")
        self.travel(x, y, near=1, tries=12)
        corpses = [i for i in self.c.containers(within=6) if ("corpse" in i.name.lower() or "remains" in i.name.lower()) and not i.name.lower().startswith(("a ", "an "))]
        corpses.sort(key=lambda i: max(abs(i.x - x), abs(i.y - y)))          # the one lying where this bot died
        if not corpses:
            self.note("death", "Going back to the death spot found no corpse: it had already rotted away, or the player never saw where it was.", key="nocorpse")
            return True
        corpse = corpses[0]
        self.c.gotoexact(corpse.x, corpse.y).wait(timeout=8)
        self.c.events.drain()
        self.c.use(corpse.serial)
        self.c.wait_for(Event.CONTAINER_CONTENTS, timeout=4)
        try:
            contents = self.c.container(corpse.serial, timeout=5)
        except Exception:
            contents = []
        got = 0
        for it in contents:
            for attempt in range(3):
                time.sleep(1.0)
                self.c.get_item(it.serial, it.amount if (it.amount or 0) > 1 else None)
                time.sleep(0.9)
                if not any("must wait" in l.lower() for l in self.read_journal()):
                    break
            got += 1
        self.note("death", f"The bot walked back to its corpse and took {got} things: {[str(x) for x in contents][:6]}. The death message tells the player to do this soon.", key="corpserun", got=got)
        self.log(f"recovered {got} things from the corpse")
        self.facts.pop("corpse", None)
        return True

    def r_flee(self):
        """Losing a fight: drink the Heal potion (yellow), bandage, or run to town."""
        threats = self.mobs(8)
        if self.hp_pct() >= 40 or not threats:
            return False
        self.activity = "fleeing"
        self.on_flee()
        for item in self.c.backpack if time.time() - self.facts.get("drank", 0) > 12 else ():
            if item.name == "Yellow Potion":      # a lesser heal potion: yellow, as in the era
                self.facts["drank"] = time.time()
                self.c.use(item.serial)
                self.log("drank a yellow potion at low health")
                self.note("combat", "At low health the only way to tell the Heal potion is by its color (yellow); nothing in the pack says so.", key="potioncolor")
                time.sleep(1.5)
                return True
        if self.skill_values.get("Healing", 0) >= 30 and self.bandage_self():
            return True
        self.log(f"fleeing from {threats[0].name} at hp {self.c.hp}")
        self.call_guards(threats[0])
        self.c.goto(*self.flee_point(threats[0])).wait(timeout=4)
        return True

    def on_flee(self):
        pass

    def in_britain(self):
        return any(x0 <= self.c.x < x1 and y0 <= self.c.y < y1 for x0, y0, x1, y1 in BRITAIN)

    def refuge_from(self, threat):
        """The town refuge farthest from the threat among the nearer ones: away from it, and not always to the healer."""
        near = sorted(REFUGES, key=lambda p: abs(p[0] - self.c.x) + abs(p[1] - self.c.y))[:4]
        if threat is None:
            return near[0]
        return max(near, key=lambda p: max(abs(p[0] - threat.x), abs(p[1] - threat.y)) - 0.3 * max(abs(p[0] - self.c.x), abs(p[1] - self.c.y)))

    def flee_point(self, threat):
        """Where to run: a town refuge when one is close, otherwise straight away from the threat. Far out (a veteran archer 300 tiles west of
        town) the walk to a town refuge planned "nopath" every tick, and the bot stood still and died fleeing."""
        dest = self.refuge_from(threat)
        if threat is None or max(abs(dest[0] - self.c.x), abs(dest[1] - self.c.y)) <= 60:
            return dest
        dx, dy = self.c.x - threat.x, self.c.y - threat.y
        n = max(abs(dx), abs(dy), 1)
        return self.c.x + round(12 * dx / n), self.c.y + round(12 * dy / n)

    def call_guards(self, threat):
        """A player chased into town shouts for the guards. Whether they come for a monster is exactly what is worth finding out."""
        if threat is None or not self.in_britain() or time.time() - self.facts.get("guards_at", 0) < 30:
            return
        self.facts["guards_at"] = time.time()
        self.c.say("guards")
        time.sleep(2.5)
        guard = any("guard" in (m.name or "").lower() for m in self.c.mobiles(within=14))
        still = any(m.serial == threat.serial and not m.is_dead for m in self.c.mobiles(within=16))
        self.log(f"called the guards on {threat.name} at {self.c.x},{self.c.y}: guard in sight {guard}, the {threat.name} still here {still}")
        self.mem.record("res", kind="guards", key=self.mkey(threat), ok=guard)
        self.note("guards", f"Chased into Britain by {threat.name}, the bot shouted 'guards': {'a guard came' if guard else 'no guard came'}"
                            f"{'' if guard else ', and the monster kept on (guards act only on criminals and murderers)'}.", key=f"guards:{self.mkey(threat)}:{guard}")

    def r_cure(self):
        """Poisoned: cure before anything else. The Orange potion is the Cure potion (five come in the starting kit, from the shard's poison relief); a
        bandage cures only at Healing 60 or more in this era; a heal spell or a Yellow potion does not stop poison. Never drink Orange for hit points."""
        if self.c.ghost or not self.c.poisoned or time.time() - self.facts.get("cured_at", 0) < 8:
            return False
        self.facts["cured_at"] = time.time()
        self.activity = "curing poison"
        pot = next((i for i in self.c.backpack if i.name == "Orange Potion"), None)
        if pot:
            self.c.use(pot.serial)
            time.sleep(1.5)
            self.note("poison", f"Poisoned, the {self.pname} drank an Orange potion (Cure); still poisoned: {self.c.poisoned}. Nothing in the pack names it a Cure potion.", key="cure:orange")
            return True
        if self.skill_values.get("Healing", 0) >= 60 and self.c.find("bandage"):
            return self.bandage_self()
        self.note("poison", f"A poisoned {self.pname} with no Cure potion left and too little Healing can only run to a healer or wait it out.", key="cure:none")
        return False

    # ---- dressing: after a resurrection the starting gear is back in the pack, not on the body ----------------------------------------------
    WEAPONS = {"Archer": ("bow", "crossbow"), "Ranger": ("bow", "crossbow"), "Bard": ("bow", "crossbow"), "MaceFighter": ("club", "mace", "hammer", "staff"),
               "Fencer": ("kryss", "spear", "fork", "dagger"), "Swordsman": ("katana", "sword", "scimitar", "cutlass", "axe"), "Warlock": ("katana", "sword", "scimitar")}
    ARMOR = ("tunic", "leggings", "sleeves", "gloves", "gorget", "helm", "cap", "coif", "shield", "chest", "arms", "legs")
    CLOTHES = ("shirt", "pants", "shoes", "boots", "doublet", "skirt", "kilt")

    def r_gear(self):
        """Put the gear in the pack back on: a resurrected character comes back in a death robe with its weapon and armour in the backpack, and fights
        barehanded until the player notices (bots did, for hours). Checked once a minute and right after a resurrection."""
        if self.c.ghost or time.time() - self.facts.get("gear_at", 0) < 60 and not self.facts.pop("just_resurrected", False):
            return False
        self.facts["gear_at"] = time.time()
        self.c.open_backpack()
        worn = {(i.layer or "").lower() for i in self.c.equipped}
        names = [i.name.lower() for i in self.c.equipped]
        todo = []
        wanted = self.WEAPONS.get(self.pname, ())
        has_weapon = any(any(w in n for w in wanted) for n in names) if wanted else True
        if not has_weapon:
            weapon = next((i for i in self.c.backpack if any(w in i.name.lower() for w in wanted)), None)
            if weapon:
                todo.append(weapon)
        for it in self.c.backpack:
            low = it.name.lower()
            if any(a in low for a in self.ARMOR) and low not in names:
                todo.append(it)
            elif any(c in low for c in self.CLOTHES) and low not in names and not any(c in n for n in names for c in self.CLOTHES if c in low):
                todo.append(it)
        if not todo:
            return False
        if "robe" in names and any(any(a in i.name.lower() for a in self.ARMOR) for i in todo):
            robe = next((i for i in self.c.equipped if i.name.lower() == "robe"), None)
            if robe:
                self.c.unequip(robe.serial)                 # the death robe covers the chest armour's layer
                time.sleep(0.8)
        failed = self.facts.setdefault("gear_failed", {})
        todo = [it for it in todo if failed.get(it.serial, 0) < time.time()]
        if not todo:
            return False
        self.activity = "getting dressed"
        put_on = []
        for it in todo[:10]:
            try:
                self.c.call(f"equip {it.serial}", timeout=6)
            except Exception:
                pass
            time.sleep(0.8)
        self.c.open_backpack()
        still = {i.serial for i in self.c.backpack}
        for it in todo[:10]:
            if it.serial in still:
                failed[it.serial] = time.time() + 1800          # something else holds that layer: do not keep trying every minute
            else:
                put_on.append(it.name)
        if not put_on:
            return False
        self.log(f"put back on: {put_on}")
        self.note("death", "After a resurrection the starting weapon and armour are in the backpack, not worn; nothing reminds the player to put them back on, and a character that forgets fights barehanded.", key="regear", items=put_on)
        return True

    def r_evade(self):
        """For bots that do not fight for a living: a hostile within seven tiles means walk away from it, towards town, before it gets to them (waiting beside it achieves nothing)."""
        if self.c.ghost:
            return False
        near = [m for m in self.mobs(7) if not m.name.lower().startswith(("a rat", "a cat", "a dog", "a bird", "a chicken", "a rabbit"))]
        if not near:
            return False
        m = near[0]
        self.activity = f"walking away from {m.name}"
        self.note("danger", f"A {m.name} came within {m.distance} tiles of a working {self.pname}; a gatherer or crafter can only walk away and come back later.", key=f"evade:{self.mkey(m)}")
        dx = 1 if self.c.x >= m.x else -1
        dy = 1 if self.c.y >= m.y else -1
        self.c.goto(self.c.x + 10 * dx, self.c.y + 10 * dy).wait(timeout=8)
        return True

    def bandage_self(self):
        b = self.c.find("bandage")
        if not b or self.hp_pct() > 80:
            return False
        self.c.events.drain()
        self.c.use_on(b.serial, "self")
        ev = self.c.wait_for([Event.BANDAGE_DONE, Event.BANDAGE_FAILED], timeout=12)
        self.log(f"bandage: {ev.text[:60] if ev else 'no answer'}")
        return True

    def r_loot(self):
        if self.mobs(7):
            return False
        # only monster corpses ("a rat corpse"); a player's corpse ("corpse", "the remains of BotX") is someone's belongings and taking from it is a crime
        corpses = [i for i in self.c.containers(within=8) if "corpse" in i.name.lower() and i.name.lower().startswith(("a ", "an ")) and "bot" not in i.name.lower()
                   and i.serial not in self.facts["looted"]]
        if not corpses:
            return False
        corpse = corpses[0]
        self.activity = "looting"
        if max(abs(self.c.x - corpse.x), abs(self.c.y - corpse.y)) > 1:
            res = self.c.gotoexact(corpse.x, corpse.y).wait(timeout=6)
            if max(abs(self.c.x - corpse.x), abs(self.c.y - corpse.y)) > 1:
                tries = self.facts.setdefault("loot_tries", {})
                tries[corpse.serial] = tries.get(corpse.serial, 0) + 1
                if tries[corpse.serial] >= 3 or str(res).startswith("nopath"):
                    self.facts["looted"].add(corpse.serial)
                return True
        self.facts["looted"].add(corpse.serial)
        self.c.events.drain()
        self.c.use(corpse.serial)
        self.c.wait_for(Event.CONTAINER_CONTENTS, timeout=4)
        if any("criminal act" in l for l in self.read_journal()):
            self.note("loot", "Opening a corpse the player did not kill says 'Looting this monster corpse will be a criminal act!'; the bot left it. A new player taking from another fighter's kill would be flagged and could be attacked by guards.", key="criminalloot")
            return True
        try:
            contents = self.c.container(corpse.serial, timeout=5)
        except Exception:
            contents = []
        if not contents:
            self.note("loot", "An empty corpse still opens by itself.", key="emptycorpse")
            return True
        if any(0x203B <= (it.graphic or 0) <= 0x204D for it in contents):
            self.log(f"{corpse.name} has hair or a beard in it: a person's corpse, left alone")
            return True
        worth = ("gold", "pearl", "moss", "garlic", "ginseng", "mandrake", "nightshade", "ash", "silk", "potion", "scroll", "bandage", "gem", "ruby", "sapphire",
                 "emerald", "diamond", "amber", "citrine", "tourmaline", "arrow", "bolt", "feather") + (self.MATERIALS if self.LOOT_MATERIALS else ())
        gold0 = self.c.gold
        for it in contents:
            if not any(w in it.name.lower() for w in worth):
                continue
            for attempt in range(4):
                time.sleep(0.9 if attempt == 0 else 1.2)
                self.c.events.drain()
                self.c.get_item(it.serial, it.amount if (it.amount or 0) > 1 else None)
                time.sleep(1.0)
                if not any("must wait" in l.lower() for l in self.read_journal()):
                    break
            self.stats["loot"][it.name] = self.stats["loot"].get(it.name, 0) + (it.amount or 1)
        self.log(f"looted {corpse.name}: {[str(x) for x in contents]}")
        if self.c.gold > gold0:
            self.mem.record("loot", cell=cell_of(corpse.x, corpse.y), gold=self.c.gold - gold0, m=re.sub(r"[^a-z]", "", re.sub(r"( corpse| remains)$", "", re.sub(r"^(an?|the) ", "", corpse.name.lower()))))
        return True

    def junk_in_pack(self):
        keep = self.KEEP
        return [i for i in self.c.backpack if not any(w in i.name.lower() for w in keep) and i.name.lower() != "backpack"]

    RICH_GOLD = 900

    KEEP = ("book", "gold", "dagger", "candle", "bag", "scroll", "potion", "recall", "scissors", "bedroll", "kindling", "pearl", "moss", "garlic", "ginseng", "mandrake",
            "nightshade", "ash", "silk", "bandage", "gem", "ruby", "sapphire", "emerald", "diamond", "amber", "citrine", "tourmaline", "star ", "check", "arrow", "bolt",
            "ingot", "ore", "board", "log", "hide", "leather", "cloth", "feather", "shaft", "tool", "hammer", "tongs", "saw", "pickaxe", "shovel", "pole", "kit",
            "mortar", "needle", "sewing", "fish", "instrument", "lute", "drum", "harp", "tambourine", "bow", "crossbow", "mace", "club", "kryss", "katana", "sword",
            "shield", "armor", "tunic", "robe", "hat", "cap", "boots", "gloves", "sleeves", "leggings", "gorget", "helm", "pants", "shirt", "cloak", "sash", "apron",
            "skirt", "kilt", "sandals", "shoes", "fork", "knife", "axe", "staff", "spear", "halberd", "cleaver", "scimitar", "broadsword", "longsword", "hatchet")

    def r_bank(self):
        """Rich (450+ gold) or too heavy with leftovers: bank the gold above a reserve."""
        if self.threats(10) or self.hp_pct() < 60 or time.time() - self.facts.get("bank_fail", 0) < 180 or time.time() - self.facts.get("banked_at", 0) < 240:
            return False
        rich = self.c.gold >= self.RICH_GOLD
        heavy = self.c.weight > self.c.max_weight * 0.8 and bool(self.junk_in_pack())
        overloaded = self.facts.get("bank_heavy") and self.c.weight > self.c.max_weight * 0.9
        if not (rich or heavy or overloaded):
            return False
        self.activity = "banking"
        if overloaded:
            done = self.visit_bank("overloaded", extra=self.HEAVY_THINGS)
            if done:
                self.facts["bank_heavy"] = False
            return True
        return self.visit_bank("rich" if rich else "heavy") or True

    def visit_bank(self, why, withdraw=0, reserve=200, extra=()):
        banks = sorted(BANKS, key=lambda p: abs(p[0] - self.c.x) + abs(p[1] - self.c.y))
        self.log(f"bank trip ({why}): gold {self.c.gold}, weight {self.c.weight}/{self.c.max_weight}")
        res = self.c.goto(*banks[0]).wait(timeout=90)
        if not str(res).startswith("arrived"):
            self.facts["bank_fail"] = time.time()
            self.note("bank", f"The way to the bank failed: {res}", key="bankpath")
            return False
        self.c.events.drain()
        self.c.say("bank")
        ev = self.c.wait_for(Event.CONTAINER_OPENED, timeout=5)
        m = re.search(r"Opened (0x[0-9A-Fa-f]+)", ev.text) if ev else None
        if not m:
            self.facts["bank_fail"] = time.time()
            self.note("bank", "Saying 'bank' next to a banker did not open the box.", key="nobox")
            return False
        box = m.group(1)
        self.note("bank", "The bank box opens when the player says 'bank' near a banker; gold goes in by dragging it onto the box, and comes out by saying 'withdraw <amount>'.", key="howbank")
        self.c.open_backpack()
        for it in list(self.c.backpack):
            low = it.name.lower()
            if (any(w in low for w in self.KEEP) and not any(w in low for w in extra)) or low == "backpack" or "bandage" in low:
                continue
            self.c.drop(it.serial, box, it.amount if (it.amount or 1) > 1 else None)   # without an amount Navrey moves one of a stack
            time.sleep(1.4)
        gold = [i for i in self.c.backpack if "gold" in i.name.lower()]
        if gold and self.c.gold > reserve + 50:
            self.c.drop(gold[0].serial, box, self.c.gold - reserve)
            time.sleep(1.6)
        self.c.events.drain()
        self.c.say("balance")
        time.sleep(1.5)
        for line in self.read_journal():
            mb = re.search(r"balance is (\d+) gold", line)
            if mb:
                self.facts["bank_balance"] = int(mb.group(1))
        if withdraw and self.facts["bank_balance"] > 0:
            take = min(withdraw, self.facts["bank_balance"])
            self.c.say(f"withdraw {take}")
            time.sleep(2.5)
            self.facts["bank_balance"] -= take
        self.facts["banked_at"] = time.time()
        return True

    def shop_at(self, xy, wanted: dict, budget=None):
        """Walk to a shop, find the vendor by trying every person there ("<name> buy"), buy what `wanted` lists ({substring: target amount}). Returns what was bought."""
        res = self.c.goto(*xy).wait(timeout=90)
        self.log(f"to the shop at {xy}: {res}")
        stock = []
        vendor_name = ""
        # A shop often has two vendors (the Tailor and a Weaver, the Armorer and the Weaponsmith) who sell different things: ask each until one
        # stocks something wanted. Taking the first list that came back sent a carpenter home without a hatchet and a tailor without a sewing kit.
        first = ([], "")
        for v in [m for m in self.c.mobiles(within=7) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")]:
            stock = self.vendor_list(v, "buy")
            if len(stock) < 2:
                continue
            if not first[0]:
                first = (stock, v.name)
            if any(self.wants(sub, re.sub(r"^.*x\d+\s+", "", l.strip())) for sub in wanted for l in stock[1:]):
                vendor_name = v.name
                break
        else:
            stock, vendor_name = first
        if len(stock) < 2:
            self.note("shop", "Saying '<name> buy' to each person at the shop opened no list: a new player has to know the vendor-name-plus-buy words (or double-click the vendor).", key="noshop")
            return {}
        self.note("shop", f"Shop at {xy} sells: " + "; ".join(l.strip()[11:56] for l in stock[1:16]), key=f"stock:{xy}")
        try:
            shops = json.load(open(os.path.join(FARM, "shops.json"), encoding="utf-8"))
        except (OSError, ValueError):
            shops = {}
        shops[str(xy)] = [l.strip()[:80] for l in stock]
        rows = []
        for l in stock:
            mm = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", l)
            if mm:
                rows.append([mm.group(4).strip(), int(mm.group(2)), int(mm.group(3))])
        if rows:
            self.mem.record("vendor", xy=f"{xy[0]},{xy[1]}", name=vendor_name, stock=rows)
        json.dump(shops, open(os.path.join(FARM, "shops.json"), "w", encoding="utf-8"), indent=1)
        have = {}
        for it in self.c.backpack:
            have[it.name.lower()] = have.get(it.name.lower(), 0) + (it.amount or 1)
        cart, spent, bought, got = [], 0, {}, {}
        gold = self.c.gold if budget is None else min(budget, self.c.gold)
        for line in stock:
            m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
            if not m:
                continue
            serial, price, avail, name = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4).strip()
            for sub, target in wanted.items():
                if self.wants(sub, name):
                    units = 50 if name.lower().startswith("bolt of") else 1     # a bolt cuts into 50 cloth
                    owned = sum(v for k, v in have.items() if self.wants(sub, k)) + got.get(sub, 0)
                    n = min(avail, max(0, -(-(target - owned) // units)), max(0, (gold - spent) // max(price, 1)))
                    if n > 0:
                        cart += [serial, str(n)]
                        spent += n * price
                        bought[name] = n
                        got[sub] = got.get(sub, 0) + n * units
                    break
        if cart:
            self.cmd("buy " + " ".join(cart), timeout=10)
            time.sleep(3)
            self.log(f"bought {bought} for {spent} gold")
        return bought

    @staticmethod
    def wants(sub, name):
        """Does a shop line's item name match a `wanted` key? "=arrow" means exactly "arrow"; any other key is a part of the name."""
        n = name.strip().lower()
        return n == sub[1:] if sub.startswith("=") else sub in n

    def vendor_list(self, vendor, kind):
        """Ask one vendor for its buy ("buy") or sell ("sell") list and return the lines, or [] when the list that came back is not this vendor's:
        Navrey's shop/selllist return the last list received, so a vendor that does not answer in time would hand back the previous vendor's list
        (a Tinker once tried to sell Neoma's goods by serial to Constance, who paid nothing)."""
        self.c.events.drain()
        self.c.say(f"{vendor.name.split()[0]} {kind}")
        deadline = time.time() + 4
        got = False
        while time.time() < deadline and not got:
            time.sleep(0.5)
            for e in self.c.events.poll():
                if "[SHOP]" in e.text and vendor.serial.lower() in e.text.lower():
                    got = True
        if not got:
            return []
        lines = self.cmd("selllist" if kind == "sell" else "shop", timeout=10)
        head = next((l for l in lines if l.startswith("[SHOP]")), "")
        return lines if vendor.serial.lower() in head.lower() else []

    def sell_items(self, xy, words):
        """Walk to a buyer, find the vendor that opens a sell list, sell every pack item whose name has one of `words`. Returns gold earned (0 if it could not sell)."""
        gold0 = self.c.gold
        res = self.c.goto(*xy).wait(timeout=100)
        if not self.travel(xy[0], xy[1], near=3):
            return 0
        offers = []
        for v in [m for m in self.c.mobiles(within=7) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")]:
            offers = self.vendor_list(v, "sell")
            if any("gp" in l for l in offers):
                break
            offers = []
        if not offers:
            self.note("sell", "Saying '<vendor> sell' near the vendor opened no list of what the vendor buys.", key="nosell")
            return 0
        self.note("sell", "The sell list shows each item's price (" + "; ".join(l.strip()[11:60] for l in offers[:6]) + ")", key=f"selllist:{xy}")
        buys = {}
        for l in offers:
            mm = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", l)
            if mm:
                buys[mm.group(4).strip().lower()] = int(mm.group(2))
        if buys:
            self.mem.record("vendor", xy=f"{xy[0]},{xy[1]}", name="", buys=[[k, v] for k, v in buys.items()])
        cart = []
        for line in offers:
            m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
            if m and any(w in m.group(4).lower() for w in words) and int(m.group(2)) > 0:
                cart += [m.group(1), m.group(3)]
        if cart:
            self.cmd("sell " + " ".join(cart), timeout=10)
            time.sleep(3)
        earned = max(self.c.gold - gold0, 0)
        self.log(f"sold {len(cart) // 2} stacks for {earned} gold")
        return earned

    # heaviest per piece first; never ammunition (arrows weigh a tenth of a stone, and an overloaded archer used to drop its own arrows first)
    HEAVY_THINGS = ("ore", "log", "hide", "leather", "board", "fish", "raw ", "cloth", "ingot", "fletching")   # "arrow fletching": fletcher's tools, 2 stones each
    MATERIALS = ("ore", "log", "hide", "leather", "board", "ingot")
    LOOT_MATERIALS = True                                 # gatherers and crafters; fighters set it False

    FORGE = (1424, 1558)                                  # the Britain smithy's small forge: an item from the decoration data, not a map static

    def ore_piles(self, smeltable=False):
        """Ore in the pack; with smeltable, without piles that gave nothing at the forge lately (a single small ore, or a colour this Mining cannot smelt)."""
        bad = self.facts.setdefault("unsmeltable", {})
        return [i for i in self.c.backpack if re.search(r"\bore\b", i.name.lower()) and not (smeltable and bad.get(i.serial, 0) > time.time())]

    def ingots(self):
        return sum((i.amount or 1) for i in self.c.backpack if "ingot" in i.name.lower())

    def smelt(self):
        """Carry the ore to the Britain forge and smelt every pile: double-click the ore, target the forge (Mining 25-75 for iron; a failure burns half
        the pile away). Returns (ore, ingots made, piles burned), or None when the forge could not be reached."""
        piles = self.ore_piles(smeltable=True)
        ore = sum((i.amount or 1) for i in piles)
        fx, fy = self.FORGE
        self.activity = "smelting ore at the forge"
        if max(abs(self.c.x - fx), abs(self.c.y - fy)) > 2:
            self.c.goto(fx, fy).wait(timeout=120)
            for dx, dy in ((-1, -1), (0, -1), (-1, 0), (1, -1), (-1, 1), (1, 0), (0, 1)):
                if max(abs(self.c.x - fx), abs(self.c.y - fy)) <= 1:
                    break
                self.c.gotoexact(fx + dx, fy + dy).wait(timeout=20)
        forges = [g for g in self.ground_items(4) if re.search(r"\bforge$", g.name.lower())]
        forge = min(forges, key=lambda g: (g.x, g.y) != (fx, fy), default=None)
        if forge is None or max(abs(self.c.x - forge.x), abs(self.c.y - forge.y)) > 2:
            self.note("smelt", f"Could not get within two steps of the forge (at {self.c.x},{self.c.y}; forge seen: {bool(forge)}).", key="noforge")
            return None
        before = self.ingots()
        said = []
        for p in piles:
            self.c.events.drain()
            self.c.use(p.serial)
            if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
                said += self.read_journal()
                self.log(f"no target cursor from {p.name} x{p.amount} ({p.serial}); journal: {said[-2:]}")
                continue
            self.c.target(forge.serial)
            end = time.time() + 5
            got = []
            while time.time() < end and not got:            # wait for the server's answer (or the pile to go), not a fixed beat
                time.sleep(0.7)
                got = [l for l in self.read_journal() if re.search(r"smelt|burn away|ore|too far|no idea|metal|cannot|can't", l, re.I)]
                if not any(i.serial == p.serial for i in self.c.backpack):
                    break
            said += got
            if not got:
                self.log(f"no answer to smelting {p.name} x{p.amount} at forge {forge.serial} ({forge.name}, {forge.x},{forge.y}); I am at {self.c.x},{self.c.y}")
        self.c.open_backpack()
        time.sleep(1)
        made = self.ingots() - before
        burned = sum(1 for l in said if "burn away" in l.lower())       # success also says "removing the impurities"
        left = {i.serial: (i.amount or 1) for i in self.ore_piles()}
        for p in piles:
            if left.get(p.serial) == (p.amount or 1):
                self.facts["unsmeltable"][p.serial] = time.time() + 1800   # unchanged after a try: do not walk back to the forge for it
        self.mem.record("res", kind="smelt", key=f"{fx},{fy}", ok=made > 0, ingots=made, burned=burned)
        self.work += made > 0
        self.log(f"smelted {ore} ore into {made} ingots ({burned} piles burned down); lines: {said[-3:]}")
        self.note("smelt", f"Smelting ore at the Britain forge: {ore} ore gave {made} ingots, {burned} piles lost half to impurities.", key=f"smeltresult:{self.pname}")
        if made <= 0 and not burned:
            self.note("smelt", f"Smelting gave nothing and said: {said[-2:]}", key="smeltnothing")
        return ore, made, burned

    def cancel_repeat(self):
        """Any step ends the shard's gather/craft repeat loop (docs/Harvest-AutoRepeat-Evidence.md); step to a free tile and back."""
        for d in ("s", "n", "e", "w"):
            self.c.walk(d)
            time.sleep(0.5)
            break

    def drop_excess(self):
        """Over the weight limit a character cannot walk at all. Drop the biggest stacks of heavy material on the ground until it can move again."""
        self.c.open_backpack()
        over = self.c.weight - self.c.max_weight
        if over <= 0:
            return False
        self.note("weight", f"Overloaded to {self.c.weight}/{self.c.max_weight}: the character stands still; the only way out is to drop things on the ground, and nothing says which weigh most.", key="overloaded_stuck")
        def rank(i):
            n = i.name.lower()
            return next((k for k, w in enumerate(self.HEAVY_THINGS) if w in n), 99), -(i.amount or 1)
        if time.time() < self.facts.get("drop_refused_until", 0):
            return False                                  # dropping was refused a moment ago: let r_bank walk to the bank box instead
        stacks = sorted((i for i in self.c.backpack if any(w in i.name.lower() for w in self.HEAVY_THINGS) and "bandage" not in i.name.lower()), key=rank)
        if not stacks:
            # overloaded by something that is not material (gear, ammunition): nothing here to drop, so the rules (the bank trip) take the tick
            self.facts["drop_refused_until"] = time.time() + 600
            self.facts["bank_heavy"] = True
            return False
        left = 0
        for it in stacks[:3]:
            amt = it.amount or 1
            self.c.call(f"dropground {it.serial} {amt}", timeout=8)
            time.sleep(1.5)
            still = any(i.serial == it.serial for i in self.c.backpack)
            left += still
            self.log(f"{'tried to drop' if still else 'dropped'} {amt} {it.name} to get under the weight limit")
            if self.c.weight <= self.c.max_weight - 5:
                break
        if stacks and left == len(stacks[:3]):
            self.facts["drop_refused_until"] = time.time() + 600
            self.facts["bank_heavy"] = True
            self.note("weight", "An overloaded character cannot drop anything: the server puts each item straight back (\"You are overloaded\") and says nothing else. The only way out is to stagger to a bank or a vendor.",
                      key="cantdrop")
            return False
        return True

    def tired(self):
        """Out of breath: running costs stamina (StaminaSystem: a point every few steps, more below a third, and no running at all at 0) and the
        frontier walks are long, so bots arrived everywhere at stamina 1 and crawled. A player stops to get their breath back."""
        mx = self.c.state.get("maxStam") or 0
        if mx and self.c.stamina < 0.2 * mx:
            self.facts["catching_breath"] = True
        elif not mx or self.c.stamina >= 0.7 * mx:
            self.facts["catching_breath"] = False
        return bool(self.facts.get("catching_breath"))

    def r_rest(self):
        """Hurt or out of breath, and nothing around: stand still (a mage meditates, handled by the brain)."""
        if self.mobs(10) or (self.hp_pct() >= 85 and not self.tired()):
            return False
        if self.tired():
            self.activity = f"catching breath (stamina {self.c.stamina})"
            if not self.facts.get("tired_noted"):
                self.facts["tired_noted"] = True
                self.note("stamina", f"Running across the map leaves a {self.pname} at stamina {self.c.stamina}: it can hardly move until it stops to rest, and nothing but the stamina bar says why.", key="tired")
            time.sleep(4)
            return True
        self.activity = "resting"
        if self.bandage_self():
            return True
        time.sleep(3)
        return True

    # ---- main loop --------------------------------------------------------------------------------------------

    # ---- the decision log: every stretch of one rule, and what it earned ----------------------------------------------

    def total_gains(self):
        return sum(self.stats["gains"].values())

    def dlog(self, typ, **kw):
        """One line in this bot's decisions.jsonl (episodes of a rule, and the moments the shared memory changed a decision); evaluate.py reads them all."""
        try:
            with open(self.decisions_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"type": typ, "t": round(time.time()), "bot": self.name, "prof": self.pname, "mode": getattr(self, "mode", "veteran"), **kw}, ensure_ascii=False, separators=(",", ":")) + "\n")
        except OSError:
            pass

    def track_episode(self):
        """Close the current stretch of one rule when the rule changes (or after two minutes) and log what it yielded: gold, kills, skill gains, hit points, deaths, distance."""
        rule = self.last_rule or "-"
        now = time.time()
        ep = self.episode
        if ep and (rule != ep["rule"] or now - ep["t0"] > 120):
            self.close_episode(now)
            ep = None
        if ep is None:
            self.episode = {"rule": rule, "act": self.activity, "t0": now, "gold0": self.c.gold, "kills0": self.kills, "gains0": self.total_gains(), "hp0": self.c.hp, "work0": self.work,
                            "deaths0": self.deaths, "x0": self.c.x, "y0": self.c.y}

    def close_episode(self, now=None):
        ep, self.episode = self.episode, None
        if not ep:
            return
        now = now or time.time()
        dur = now - ep["t0"]
        if dur < 1.5:
            return
        self.dlog("ep", rule=ep["rule"], act=(ep["act"] or "")[:40], dur=round(dur, 1), gold=self.c.gold - ep["gold0"], kills=self.kills - ep["kills0"], gains=self.total_gains() - ep["gains0"],
                  hp=self.c.hp - ep["hp0"], died=self.deaths - ep["deaths0"], work=self.work - ep.get("work0", self.work), moved=round(math.hypot(self.c.x - ep["x0"], self.c.y - ep["y0"])))

    HARMLESS = ("rat", "cat", "dog", "bird", "chicken", "rabbit", "sheep", "cow", "pig", "goat", "hind", "deer", "crow", "magpie", "sparrow", "swallow",
                "nightingale", "plover", "thrush", "tern", "warbler", "squirrel", "toad", "frog", "lizard", "gull", "raven", "finch", "towhee", "starling")

    def threats(self, within):
        """Hostiles that can hurt a working character: mobs() without the town animals (a rat beside the forge is no reason to stop working; the
        Fisherman once stood idle for twenty minutes because two rats were near)."""
        out = []
        for m in self.mobs(within):
            n = m.name.lower()
            if n.startswith(("a ", "an ")) and any(re.search(r"\b" + re.escape(w) + r"\b", n) for w in self.HARMLESS) and not any(w in n for w in ("giant", "dire", "plague", "rat man", "ratman")):
                continue
            out.append(m)
        return out

    @staticmethod
    def mkey(m):
        """The memory's name for a kind of monster: its body species when the client knows it ("orc" for a personally named orc), else its name without the article."""
        return re.sub(r"[^a-z]", "", (m.species or re.sub(r"^(an?|the) ", "", m.name.lower())).lower())

    def observe(self):
        self.track_episode()
        if time.time() - self.last_presence > 60 and not self.c.ghost:
            self.last_presence = time.time()
            self.mem.record("presence", cell=cell_of(self.c.x, self.c.y), rule=self.last_rule)
        if not self.c.ghost:
            self.last_gold = self.c.gold
            for m in self.c.mobiles(within=14):
                if m.notoriety in ("Gray", "Criminal", "Enemy", "Murderer") and m.name != "Generic Player":
                    self.mem.sight(self.mkey(m), m.x, m.y)
        self.status()
        if self.c.overloaded:
            self.note("weight", f"A {self.pname} became overloaded ({self.c.weight}/{self.c.max_weight} stones) and can no longer walk normally.", key="overload")
        if self.tick_no % 40 == 0:
            self.log(f"tick {self.tick_no} hp {self.c.hp}/{self.c.max_hp} mana {self.c.mana} at ({self.c.x},{self.c.y}) gold {self.c.gold} weight {self.c.weight}/{self.c.max_weight} kills {self.kills} deaths {self.deaths}")

    def run(self, seconds):
        end = time.time() + seconds
        self.log(f"start: {self.pname}")
        try:
            self.c.open_backpack()            # a client that has just logged in knows nothing of the pack until it is opened
        except Exception:
            pass
        pause = os.path.join(self.dir, "pause")
        hang_file = open(os.path.join(self.dir, "hang.txt"), "w")
        while time.time() < end:
            faulthandler.dump_traceback_later(150, repeat=False, file=hang_file)      # a tick that takes over 150 s leaves its stack in hang.txt
            if os.path.exists(pause):              # `touch work/botfarm/<name>/pause` hands the character to a human or a test script
                self.activity = "paused"
                self.status()
                time.sleep(2)
                continue
            self.tick_no += 1
            try:
                self.read_journal()
                self.observe()
                if self.c.weight > self.c.max_weight and not self.c.ghost and self.drop_excess():
                    time.sleep(0.5)                # never a tick without a pause (a refused drop once spun a brain at 75% of a core)
                    continue
                acted = None
                for name in self.RULES:
                    if getattr(self, name)():
                        acted = name
                        break
                if acted != self.last_rule:
                    self.log(f"rule -> {acted}")
                    self.last_rule = acted
                if acted is None:
                    self.note("stuck", "No rule handled the situation.", key=f"stuck:{self.tick_no // 100}")
                    self.activity = "idle"
                    time.sleep(1)
            except Exception as e:
                self.log(f"EXCEPTION {type(e).__name__}: {e}\n{traceback.format_exc()[-400:]}")
                self.note("bot", f"{type(e).__name__}: {e}", key=f"exc:{type(e).__name__}:{str(e)[:60]}")
                time.sleep(2)
        self.status(force=True)
