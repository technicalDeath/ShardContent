"""The shared body of every farm bot: a connection to its client, a journal reader, notes, a status heartbeat and the behaviors every player needs
whatever the profession (walking home as a ghost, running from a fight it is losing, banking, shopping, looting, resting).

A brain (hunter.py, crafter.py, gatherer.py) adds its own rules and lists them in RULES; the first rule that acts wins each tick, as in the new-mage
bot this grew out of. Findings go to work/botfarm/notes.jsonl, one line each tagged with the bot and its profession, so many bots' notes can be
counted together (aggregate.py). Everything the bot does goes through the commands a player has.
"""
from __future__ import annotations

import faulthandler
import json
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
from memory import SharedMemory, cell_of  # noqa: E402

HEALER = (1472, 1611)
TOWN = (1470, 1620)
BANKS = [(1425, 1690), (1650, 1608)]
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
        self.dir = os.path.join(FARM, name)
        os.makedirs(self.dir, exist_ok=True)
        self.notes = Notes(name, self.pname)
        self.mem = SharedMemory(self.pname, name)
        self.journal = deque(maxlen=300)
        self.tick_no = 0
        self.last_rule = ""
        self.kills = 0
        self.deaths = 0
        self.facts = {"looted": set(), "ghost_since": None, "bank_balance": 0, "seen_msgs": set()}
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
            if t.startswith("[LABEL]") and t.rstrip().endswith("corpse"):
                self.kills += 1
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
            if re.match(r"\[SAY\] Bot\w+:", t):
                continue                      # another bot talking to a banker or vendor
            body = re.sub(r"^\[(SYSTEM|SAY)\]\s*", "", t)
            tag = "system" if t.startswith("[SYSTEM]") else ("npc" if t.startswith("[SAY]") and not t.startswith(f"[SAY] {self.name}") else "")
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
            self.facts["ghost_since"] = None
            return False
        if self.facts["ghost_since"] is None:
            self.facts["ghost_since"] = time.time()
            self.deaths += 1
            self.facts["war_at_death"] = self.c.war_mode
            self.log(f"ghost at {self.c.x},{self.c.y}; war mode at death = {self.c.war_mode}")
            self.death_spots.append((self.c.x, self.c.y))
            self.mem.record("death", cell=cell_of(self.c.x, self.c.y), killers=[t[2] for t in getattr(self, "recent_threats", [])[:3]])
            self.facts["corpse"] = {"xy": (self.c.x, self.c.y), "t": time.time(), "gold": self.last_gold, "tries": 0}
            json.dump({"death_spots": self.death_spots}, open(self.know_path, "w", encoding="utf-8"))
            self.note("death", f"A {self.pname} died.", key=f"death:{self.deaths}", pos=[self.c.x, self.c.y], last=list(self.journal)[-4:])
            self.log(f"DEAD at {self.c.x},{self.c.y}; walking to the healer")
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
        if self.hp_pct() < 70 or self.mobs(8):
            return False
        if info["gold"] < 60:
            self.facts.pop("corpse")
            return False
        info["tries"] += 1
        self.activity = "going back for my corpse"
        x, y = info["xy"]
        self.log(f"going back to the corpse at {x},{y} ({info['gold']} gold lost)")
        self.travel(x, y, near=1, tries=12)
        corpses = [i for i in self.c.containers(within=6) if "corpse" in i.name.lower()]
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
        for item in self.c.backpack:
            if item.name == "Yellow Potion":      # a lesser heal potion: yellow, as in the era
                self.c.use(item.serial)
                self.log("drank a yellow potion at low health")
                self.note("combat", "At low health the only way to tell the Heal potion is by its color (yellow); nothing in the pack says so.", key="potioncolor")
                time.sleep(1.5)
                return True
        if self.skill_values.get("Healing", 0) >= 30 and self.bandage_self():
            return True
        self.log(f"fleeing from {threats[0].name} at hp {self.c.hp}")
        self.c.goto(*TOWN).wait(timeout=4)
        return True

    def on_flee(self):
        pass

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
        corpses = [i for i in self.c.containers(within=8) if "corpse" in i.name.lower() and i.serial not in self.facts["looted"]]
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
        worth = ("gold", "pearl", "moss", "garlic", "ginseng", "mandrake", "nightshade", "ash", "silk", "potion", "scroll", "bandage", "gem", "ruby", "sapphire",
                 "emerald", "diamond", "amber", "citrine", "tourmaline", "arrow", "bolt", "hide", "leather", "feather", "ingot", "ore", "board", "log")
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
        if self.mobs(10) or self.hp_pct() < 60 or time.time() - self.facts.get("bank_fail", 0) < 180 or time.time() - self.facts.get("banked_at", 0) < 240:
            return False
        rich = self.c.gold >= self.RICH_GOLD
        heavy = self.c.weight > self.c.max_weight * 0.8 and bool(self.junk_in_pack())
        if not (rich or heavy):
            return False
        self.activity = "banking"
        return self.visit_bank("rich" if rich else "heavy") or True

    def visit_bank(self, why, withdraw=0, reserve=200):
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
            if any(w in low for w in self.KEEP) or low == "backpack":
                continue
            self.c.drop(it.serial, box)
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
        for v in [m for m in self.c.mobiles(within=7) if m.notoriety == "Innocent" and m.name]:
            self.c.events.drain()
            self.c.say(f"{v.name.split()[0]} buy")
            time.sleep(2.5)
            stock = self.cmd("shop", timeout=10)
            if len(stock) >= 2:
                vendor_name = v.name
                break
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
        cart, spent, bought = [], 0, {}
        gold = self.c.gold if budget is None else min(budget, self.c.gold)
        for line in stock:
            m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
            if not m:
                continue
            serial, price, avail, name = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4).strip()
            for sub, target in wanted.items():
                if sub in name.lower():
                    owned = sum(v for k, v in have.items() if sub in k)
                    n = min(avail, max(0, target - owned), max(0, (gold - spent) // max(price, 1)))
                    if n > 0:
                        cart += [serial, str(n)]
                        spent += n * price
                        bought[name] = n
                    break
        if cart:
            self.cmd("buy " + " ".join(cart), timeout=10)
            time.sleep(3)
            self.log(f"bought {bought} for {spent} gold")
        return bought

    def sell_items(self, xy, words):
        """Walk to a buyer, find the vendor that opens a sell list, sell every pack item whose name has one of `words`. Returns gold earned (0 if it could not sell)."""
        gold0 = self.c.gold
        res = self.c.goto(*xy).wait(timeout=100)
        if not self.travel(xy[0], xy[1], near=3):
            return 0
        offers = []
        for v in [m for m in self.c.mobiles(within=7) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")]:
            self.c.events.drain()
            self.c.say(f"{v.name.split()[0]} sell")
            time.sleep(2.5)
            offers = self.cmd("selllist", timeout=10)
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

    HEAVY_THINGS = ("ore", "ingot", "board", "log", "fish", "raw ", "hide", "leather", "cloth", "arrow", "bolt", "feather", "shaft")

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
        stacks = sorted((i for i in self.c.backpack if any(w in i.name.lower() for w in self.HEAVY_THINGS) and "bandage" not in i.name.lower()), key=lambda i: -(i.amount or 1))
        for it in stacks[:3]:
            amt = it.amount or 1
            self.c.call(f"dropground {it.serial} {max(amt // 2, 1)}", timeout=8)
            self.log(f"dropped {max(amt // 2, 1)} of {it.name} to get under the weight limit")
            time.sleep(1.5)
            if self.c.weight <= self.c.max_weight - 5:
                break
        return True

    def r_rest(self):
        """Hurt and nothing around: stand still (a mage meditates, handled by the brain)."""
        if self.mobs(10) or self.hp_pct() >= 85:
            return False
        self.activity = "resting"
        if self.bandage_self():
            return True
        time.sleep(3)
        return True

    # ---- main loop --------------------------------------------------------------------------------------------

    @staticmethod
    def mkey(m):
        """The memory's name for a kind of monster: its body species when the client knows it ("orc" for a personally named orc), else its name without the article."""
        return re.sub(r"[^a-z]", "", (m.species or re.sub(r"^(an?|the) ", "", m.name.lower())).lower())

    def observe(self):
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
