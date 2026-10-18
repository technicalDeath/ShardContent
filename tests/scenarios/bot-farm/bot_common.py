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
import random
import re
import sys
import time
import traceback
import zlib
from collections import deque
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
FARM = os.path.join(ROOT, "work", "botfarm")
os.makedirs(FARM, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "Navrey", "cli"))
sys.path.insert(0, os.path.join(ROOT, ".claude", "scripts"))

from navrey_session import connect  # noqa: E402
from tele import TeleMixin  # noqa: E402  (generic teleports; needs gazetteer.py / gazetteer.json beside it)
from far import FarMixin  # noqa: E402  (far service walks, routed and resumable; needs walkroute.py)
from evade import EvadeMixin  # noqa: E402  (r_evade only for real threats; needs fightmodes.json)
from gotoroute import GotoRouteMixin  # noqa: E402  (goto of over 120 tiles as routed legs; feature goto_routed)
from party import PartyMixin  # noqa: E402  (parties; feature party; needs Navrey build Lean5+)
from buddy import BuddyMixin  # noqa: E402  (buddy pairs: rendezvous, staying together, bandaging; feature buddy + party)
from pacing import PacingMixin  # noqa: E402  (walk in town, pause before talking, a break at the bank; features pacing, pacing_walk)
from market import MarketMixin  # noqa: E402  (the bots' market: quantity offers / wants, secure trades; feature trade)
from uo import Event  # noqa: E402
from memory import MEMDIR, SharedMemory, cell_center, cell_of  # noqa: E402
from places import Places  # noqa: E402
from loopguard import LoopGuard  # noqa: E402
from recovery import RecoveryMixin  # noqa: E402
from stall import StallMixin  # noqa: E402
from ambition import AmbitionMixin  # noqa: E402
from planner import PlannerMixin  # noqa: E402
from bw import BetweenWorldsMixin  # noqa: E402
from ground_rates import GroundRateMixin  # noqa: E402
import area_danger  # noqa: E402
import deathsrc  # noqa: E402
import goals  # noqa: E402
import deathloop  # noqa: E402
import townguard  # noqa: E402
import talk  # noqa: E402
try:
    import gazetteer as gz  # noqa: E402  (generated town, role and teleporter data: a bot's home and services, by position)
except Exception:          # the data missing: the Britain constants below stay the fallback
    gz = None

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


def load_bank(d):
    """The bank balance the banker last told this bot (bank.json), or 0 if it never asked."""
    try:
        return int(json.load(open(os.path.join(d, "bank.json"), encoding="utf-8")).get("balance", 0))
    except (OSError, ValueError, TypeError, AttributeError):
        return 0


def save_bank(d, balance):
    with open(os.path.join(d, "bank.json"), "w", encoding="utf-8") as f:
        json.dump({"balance": int(balance or 0), "t": round(time.time())}, f)


PHRASES = {
    "greet": ["Hail!", "Well met.", "Greetings, friend.", "Good day to thee."],
    "reply": ["Hail, {who}.", "Well met, {who}.", "Greetings, {who}!", "Aye, {who}?"],
    "warn": ["Beware, {m} {where}!", "Careful, {m} {where}!", "{m} {where}, run!"],
    "ghost": ["Res, please?", "Anyone near a healer? I need a res.", "Ouch. Off to the healer."],
    "skill": ["Finally, {skill} {v:.0f}!", "{skill} at {v:.0f} now.", "Ha! {skill} {v:.0f}."],
    "wares": ["{item} for trade, ask me!", "Fine {item} here, fair price!", "Anyone need {item}?"],
}
DIRS = ["east", "south-east", "south", "south-west", "west", "north-west", "north", "north-east"]
PHRASES.update(talk.phrases())                                 # town_warn, sell_call (feature talk)


def load_features(name):
    """The A/B features this bot has: work/botfarm/features.json maps a feature to the bots that have it; the rest of a group is the control."""
    try:
        table = json.load(open(os.path.join(FARM, "features.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {f for f, bots in table.items() if not f.startswith("_") and name in bots}


def connect_retry(name, tries=20, wait=1.0):
    """connect() again and again for ~20 s: a client's state file is rewritten constantly and a read can land on a stale or half-written one (NotLiveError "state file is ... stale")."""
    last = None
    for i in range(tries):
        try:
            return connect(name)
        except Exception as e:                       # NotLiveError, a half-written JSON, a missing file while the client restarts
            last = e
            if i + 1 < tries:
                time.sleep(wait)
    raise last


class BotBase(MarketMixin, GroundRateMixin, BetweenWorldsMixin, PlannerMixin, AmbitionMixin, StallMixin, RecoveryMixin, PacingMixin, BuddyMixin, PartyMixin, TeleMixin, FarMixin, EvadeMixin, GotoRouteMixin, Places, LoopGuard):
    RULES: list = []

    def __init__(self, name: str, profession: int):
        self.name = name
        self.profession = profession
        self.pname = PROFESSIONS.get(profession, str(profession))
        self.c = connect_retry(name)
        self._wrap_goto()
        orig_call, bot = self.c.call, self

        def call(cmd, *a, **k):
            if isinstance(cmd, str) and cmd.startswith("useskill"):
                bot.skill_gate(cmd)                            # the skill delay this brain has learned (loopguard.py)
            return orig_call(cmd, *a, **k)

        self.c.call = call
        self.features = load_features(name)
        self._gold_prev = self.c.gold                         # gold events count from the brain's start, its first tick included
        self.dir = os.path.join(FARM, name)
        os.makedirs(self.dir, exist_ok=True)
        self.notes = Notes(name, self.pname)
        # "newbie" bots play only on what a new player can see: no monster table, no craft skill windows, no taming table. They learn from what
        # happens to them and share that among newbies only (their own memory folder). The gap between newbie and veteran bots of one profession
        # (deaths, gold, skill gain per hour) measures what the game does not tell its players.
        self.mode = os.environ.get("BOT_MODE", "veteran")
        self.mem = SharedMemory(self.pname, name, root=MEMDIR + ("-newbie" if self.mode == "newbie" else ""))
        self.mem.news = SharedMemory(self.pname, name, root=MEMDIR + ("" if self.mode == "newbie" else "-newbie"))    # fresh deaths: news for all
        # the area danger map (feature danger_map): off while a trip or a far walk runs, which have their own route penalty
        self.mem.area = area_danger.AreaDanger(
            self.mem, skill_fn=lambda: area_danger.combat_skill(getattr(self, "skill_values", {})),
            enabled=lambda: self.feature("danger_map") and getattr(self, "current_rule", "") not in ("r_trip", "r_far"),
            on_avoid=lambda cell, why: self.ev("area_avoid", area=cell, why=why))
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
        self.facts_path = os.path.join(self.dir, "facts.json")
        self.load_facts()
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
        self.facts["bank_balance"] = load_bank(self.dir)

    # ---- plumbing --------------------------------------------------------------------------------------------

    def log(self, msg):
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        guard = getattr(self, "guard_seen", None)
        if guard:
            guard("log", msg)

    def note(self, category, text, key=None, **ev):
        self.notes.add(category, text, key, **ev)

    def cmd(self, line, timeout=8.0):
        return [l for l in self.c.call(line, timeout=timeout) if not l.startswith("[GUMP]")]

    def hp_pct(self):
        return 100.0 * self.c.hp / max(1, self.c.max_hp)

    def chatter(self, kind, cooldown=900, **kw):
        """Say one line of the kind, if this bot has not spoken for three minutes nor said this kind within `cooldown` seconds."""
        now = time.time()
        said = self.facts.setdefault("said_at", {})
        if self.c.ghost and kind != "ghost" or now - said.get(kind, 0) < cooldown or now - self.facts.get("said_any", 0) < 180 or talk.capped(self, kind):
            return False
        line = random.choice(PHRASES[kind]).format(**kw)
        line = line[:1].upper() + line[1:]
        said[kind] = self.facts["said_any"] = now
        self.facts.setdefault("own_lines", set()).add(line.lower())
        self.c.say(line)
        talk.spoke(self, kind)
        self.dlog("say", kind=kind, text=line, to_human=False)
        return True

    def where(self):
        """Where the bot is, as a player would put it: "in town", or a direction from Britain."""
        if self.in_britain():
            return "in town"
        a = math.atan2(self.c.y - 1620, self.c.x - 1470)
        return f"{DIRS[int(round(a / (math.pi / 4))) % 8]} of Britain"

    def hear(self, t):
        """Another player spoke: answer a greeting, or our own name, once in a while (with the feature talk, talk.py answers people and the bots no longer answer each other)."""
        if talk.on(self):
            return
        m = re.match(r"\[SAY\] (\w+): (.+)", t)
        if not m or m.group(1) == self.name:
            return
        who, text = m.group(1), m.group(2)
        if self.name.lower() in text.lower() or re.search(r"\b(hail|well met|greetings|good day)\b", text, re.I):
            if any(x.name == who and x.distance <= 8 for x in self.c.mobiles(within=8)):
                self.chatter("reply", cooldown=300, who=who)

    @property
    def MEET(self):            # in front of the bank nearest home: where the market's deals are done
        return self.meet_spot()

    def trades(self):
        """Open secure-trade windows: [{local, with, mybox, mine_ok, theirbox, theirs_ok}] from the `trades` command."""
        out = []
        for l in self.c.call("trades", timeout=6):
            m = re.search(r"\[TRADE\] local (0x[0-9A-Fa-f]+) with (.+?) - my box (0x[0-9A-Fa-f]+) \(.*?(not accepted|accepted)\) - their box (0x[0-9A-Fa-f]+) \(.*?(not accepted|accepted)\)", l)
            if m:
                out.append({"local": m.group(1), "with": m.group(2), "mybox": m.group(3), "mine_ok": m.group(4) == "accepted", "theirbox": m.group(5), "theirs_ok": m.group(6) == "accepted"})
        return out

    def box_items(self, box):
        try:
            return self.c.container(box, timeout=6)
        except Exception:
            return []

    def do_deal(self, d):
        """One tick of a market deal, as seller or buyer: meet at the bank spot, the seller drops the agreed quantity on the buyer (the trade window opens), the buyer puts the
        gold in, both accept once the other box holds what was agreed; the outcome is checked by counts (market.py)."""
        return self.market_deal(d)

    def read_journal(self):
        out = []
        for e in self.c.events.poll():
            t = e.text
            # (a "[LABEL] ... corpse" line is any corpse that comes into view, other bots' kills included: kills are counted by the fight that made them)
            m = re.search(r"Your skill in (.+?) has increased by (\d+(?:\.\d+)?)\.\s+It is now (\d+(?:\.\d+)?)", t)
            if m:
                was = self.skill_values.get(m.group(1), 0.0)
                if int(float(m.group(3)) // 10) > int(was // 10) and float(m.group(3)) >= 60:
                    self.chatter("skill", cooldown=1200, skill=m.group(1), v=float(m.group(3)))
                self.stats["gains"][m.group(1)] = self.stats["gains"].get(m.group(1), 0) + 1
                self.skill_values[m.group(1)] = float(m.group(3))
                f = getattr(self, "fight", None)
                self.mem.record("gain", scope="prof", skill=m.group(1), action=self.activity or "?", value=float(m.group(3)), **({"m": f["key"]} if f else {}))
            d = re.match(r"Damage: (.+?) takes (\d+)", t)
            if d and d.group(1).startswith(self.name):
                self.stats["damage_taken"] += int(d.group(2))
                self.facts["hurt_at"] = time.time()
            deathsrc.feed(self, t)                                   # the last damage evidence, before the ignore list drops the Damage lines
            talk.feed(self, t)                                       # labels (who is an NPC) and speech (feature talk), before the ignore list drops them
            if t.startswith(IGNORE_PREFIX):
                continue
            self.journal.append(t)
            out.append(t)
            own = t.startswith(f"[SAY] {self.name}:")
            self.note_attacker(t)
            if re.match(r"\[SAY\] Bot\w+:", t) and not own:
                self.hear(t)
                continue                      # another bot talking (to a banker or vendor, or to us)
            if own and t[len(self.name) + 8:].strip().lower() in self.facts.get("own_lines", ()):
                continue                      # this bot's own chatter, not the game talking
            if own and re.match(rf"\[SAY\] {self.name}: (bank|balance|withdraw|guards|all release|\w+ (buy|sell|train)\b)", t, re.I):
                continue                      # what this bot said itself
            if own and self.activity.startswith("taming"):
                continue                      # the character coaxing the animal while it tames, not the game talking to the player
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
        return [m for m in self.c.mobiles(within=within) if m.notoriety in ("Gray", "Criminal", "Enemy", "Murderer")
                and (abs((m.pos[2] or 0) - self.c.z) <= 14 or m.distance <= 2) and m.name != "Generic Player" and not self.peaceful_person(m)
                and not self.killer_spared(m)]

    def note_attacker(self, t):
        """Remember who attacked this character: the server says "X is attacking you!" under the character's own name."""
        a = re.match(rf"\[SAY\] {re.escape(self.name)}: \*?(.+?) is attacking you!", t)
        if a:
            self.facts.setdefault("attacked_by", {})[a.group(1)] = time.time()

    def peaceful_person(self, m):
        """Another player (a bot, or a person: a human body) in grey or criminal colours is no monster: a fighter who carved someone else's fresh kill
        turns criminal, and four bots once attacked one as prey. Only one that attacked this character in the last two minutes is fought; a red
        one (a murderer) stays a danger."""
        if m.notoriety == "Murderer" or not (m.name.startswith("Bot") or m.is_human):
            return False
        return time.time() - self.facts.get("attacked_by", {}).get(m.name, 0) > 120

    def gather_danger(self, cell):
        """A gatherer must not use this cell: dangerous by the old rule, or above the area danger map ceiling (the map ranks, it does not refuse a hill; patch_gather_risk.py)."""
        try:
            return bool(self.mem.dangerous_cell(cell, area=False) or not self.mem.area_ok(cell))
        except (TypeError, AttributeError):                        # a memory without the map
            return bool(self.mem.dangerous_cell(cell))

    def gather_risk(self, cell):
        """The area danger map risk of the cell (0.0 without the map or the feature): gatherers take the least risky spot."""
        try:
            return float(self.mem.area_risk(cell))
        except (TypeError, AttributeError):
            return 0.0

    def near_death_spot(self, x, y, r=60):
        return any(abs(x - dx) < r and abs(y - dy) < r for dx, dy in self.death_spots)

    def _wrap_goto(self):
        """Every walk that ends in "nopath" gets one more try after a single step to a free neighbouring tile. From two tiles at the dig spot north
        of Britain (1456,1526 and 1457,1526) the planner could not expand at all, though the bot had walked in; a player would just take a step."""
        orig = self.c.goto
        bot = self

        def goto(x, y, z=None, near=2):
            if bot.c.ghost and getattr(bot, "current_rule", "r_dead") != "r_dead":
                # a ghost walks only to a healer (r_dead); a smelting or selling loop that missed the death stops here
                return SimpleNamespace(wait=lambda timeout=300.0, poll=0.1: "stopped: ghost")
            stub = bot.tele_cross(x, y)                  # another side of the map (a dungeon level): through a teleporter first, the planner cannot cross
            if stub is not None:
                return stub
            routed = bot.goto_routed(x, y, near)         # more than 120 tiles: routed legs (feature goto_routed); the client planner gives up around 150-200
            if routed is not None:
                return routed
            walk = orig(x, y, z)
            first_wait = walk.wait

            def wait(timeout=300.0, poll=0.1):
                end = time.time() + timeout
                res = bot.tele_wait(first_wait, timeout, poll)          # a jump of the position is a teleport: cancel the walk at once
                if str(res).startswith("nopath") and bot.step_out():
                    left = max(end - time.time(), 0.0) if bot.feature("walk_fix") else timeout       # (walk_fix: the second walk gets what is left of the caller's timeout)
                    if left >= 1.0:
                        res = bot.tele_wait(orig(x, y, z).wait, left, poll)
                        bot.log(f"after a step out, the walk to {x},{y}: {res}")
                return bot.far_arrival(res, x, y, near)

            walk.wait = wait
            return walk

        self.c.goto = goto
        orig_exact = self.c.gotoexact

        def gotoexact(x, y, z=None):
            stub = bot.tele_cross(x, y)
            if stub is not None:
                return stub
            walk = orig_exact(x, y, z)
            first_wait = walk.wait

            def wait(timeout=300.0, poll=0.1):
                return bot.tele_wait(first_wait, timeout, poll)

            walk.wait = wait
            return walk

        self.c.gotoexact = gotoexact

    def far_arrival(self, res, x, y, near=2):
        """A goto that says \"arrived\" with the bot more than `near` tiles from (x, y) stopped at the closest reachable tile: that is a failure (\"nopath: closest X,Y\")."""
        if str(res).startswith("arrived") and max(abs(self.c.x - x), abs(self.c.y - y)) > near:
            logged = self.facts.setdefault("far_logged", {})
            if time.time() - logged.get((x, y), 0) > 300:
                logged[(x, y)] = time.time()
                if len(logged) > 200:
                    logged.clear()
                self.log(f"the walk to {x},{y} ended at {self.c.x},{self.c.y}, {max(abs(self.c.x - x), abs(self.c.y - y))} tiles short (closest reachable): counted as nopath")
            return f"nopath: closest {self.c.x},{self.c.y}"
        return res

    def goto_near(self, x, y, near=2):
        """self.c.goto with the tolerance for \"arrived\": a client whose goto takes no near (a fake, an unwrapped client) gets the plain call."""
        try:
            return self.c.goto(x, y, None, near=near)
        except TypeError:
            return self.c.goto(x, y)

    def step_out(self):
        """One step in the first direction that moves the character; at most once every 20 seconds."""
        if time.time() - self.facts.get("stepped_out_at", 0) < 20:
            return False
        self.facts["stepped_out_at"] = time.time()
        x0, y0 = self.c.x, self.c.y
        started = time.time()
        for d in ("s", "e", "w", "n", "se", "sw", "ne", "nw"):
            if time.time() - started > 45:
                break
            for _ in range(2):                         # the first walk in a new direction only turns the character to face it
                try:
                    self.c.call(f"walk {d}", timeout=1.5)
                except Exception:
                    break
                time.sleep(0.5)
                if (self.c.x, self.c.y) != (x0, y0):
                    break
            if (self.c.x, self.c.y) != (x0, y0):
                self.log(f"no path from {x0},{y0}: stepped {d} to {self.c.x},{self.c.y} and tried again")
                self.mem.record("blocked", kind="tile", key=f"{x0},{y0}", ttl=3600)
                return True
        self.log(f"no path from {x0},{y0}, and no step in any direction moved the character")
        self.mem.record("blocked", kind="tile", key=f"{x0},{y0}", ttl=6 * 3600)
        wedges = [t for t in self.facts.get("wedged_at", []) if time.time() - t[0] < 600 and (t[1], t[2]) == (x0, y0)] + [(time.time(), x0, y0)]
        self.facts["wedged_at"] = wedges
        if len(wedges) >= 3 and time.time() - self.facts.get("unstick_asked", 0) > 900:
            # what a player does with Help > "I'm stuck": ask, once in a while, for a move (unstick.py)
            self.facts["unstick_asked"] = time.time()
            with open(os.path.join(FARM, "wedged.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps({"bot": self.name, "x": x0, "y": y0, "t": time.time()}) + "\n")
            self.note("stuck", f"A {self.pname} was wedged at {x0},{y0}: no step in any direction moved it, three times in ten minutes. A player would use Help > I'm stuck.",
                      key=f"wedged:{x0},{y0}")    # a hill tile the server will not let anyone leave: never stand there again
        return False

    # ---- the era's legacy menus, trees and the hatchet: crafters and archers both use them ------------------------------------------

    @staticmethod
    def parse_menus(lines):
        """Every open legacy menu in a `menus` listing as [(local, server, [(index, text)])], in listing order (the newest first)."""
        menus = []
        for l in lines:
            m = re.match(r"\[MENU\] local (0x[0-9A-Fa-f]+) server (0x[0-9A-Fa-f]+)", l)
            if m:
                menus.append((m.group(1), m.group(2), []))
                continue
            o = re.match(r"\s*\[option (\d+)\] graphic \S+ hue \S+ (.+)", l)
            if o and menus:
                menus[-1][2].append((int(o.group(1)), o.group(2).strip()))
        return menus

    def read_menu(self, wait=2.5):
        """The newest open legacy menu as (local serial, server id, [(index, text)]), or None. Only that menu's own options: a listing can hold older
        menus that were never answered, and mixing their options in sent the bot down paths that do not exist (a 55 Blacksmith "learned" 0 items)."""
        deadline = time.time() + wait
        while time.time() < deadline:
            menus = self.parse_menus(self.c.call("menus", timeout=8))
            self.status_extra = {"menus": len(menus)}
            if menus:
                if len(menus) > 1:
                    self.close_menus(menus[1:])
                return menus[0]
            time.sleep(0.4)
        return None

    def close_menus(self, menus=None):
        """Answer 0 (cancel) to open menus: every menu a path abandons stays open in the client otherwise, and they pile up (134 in one Smith's client)."""
        if menus is None:
            menus = self.parse_menus(self.c.call("menus", timeout=8))
        for local, server, _ in menus:
            try:
                self.c.call(f"menuresponse {local} {server} 0", timeout=6)
            except Exception:
                pass

    @staticmethod
    def index_of(menu, text):
        """The option number whose text is `text` in this menu (the legacy menus are filtered by skill and material, so numbers move; words do not)."""
        for i, t in menu[2]:
            if t.strip().lower() == text.strip().lower():
                return i
        return None

    TREES = [(1431, 1631, 20, 3288), (1440, 1718, 20, 3288), (1392, 1673, 30, 3280)]
    try:
        # every choppable tree around Britain, one per harvest bank (make_trees.py reads them from the map's statics): three trees were soon chopped bare
        ALL_TREES = [tuple(t) for t in json.load(open(os.path.join(HERE, "trees.json"), encoding="utf-8"))]
    except (OSError, ValueError):
        ALL_TREES = TREES

    def work_centre(self):
        """The centre work radii are measured from: Britain's old centre for a Britain-like home, else the home's centre (geo.py)."""
        import geo
        return geo.centre_of(self.home())

    def all_trees(self):
        t = self.__dict__.get("_tree_list")
        if t is None:
            import geo
            t = self._tree_list = geo.regional("trees", self.home(), self.ALL_TREES)
        return t

    def near_trees(self, n=6):
        """The nearest trees within 60 tiles that no bot has found bare lately, nearest first."""
        here = (self.c.x, self.c.y)
        out = []
        for t in sorted(self.all_trees(), key=lambda t: max(abs(t[0] - here[0]), abs(t[1] - here[1]))):
            if max(abs(t[0] - here[0]), abs(t[1] - here[1])) > 60 or len(out) >= n:
                break
            if self.facts.get(("tree", t[0], t[1]), 0) <= time.time() and self.mem.usable("tree", f"{t[0]},{t[1]}"):
                out.append(t)
        return out

    def chop_trees(self, hat):
        """Chop at one of the nearest trees that still has wood: walk beside it, hold the hatchet (an axe chops only when equipped), use it
        and target the tree; the shard repeats the chop by itself. True when a reachable tree was worked, False when no tree near could be,
        None when the hatchet would not go into the hands."""
        started = time.time()
        for tx, ty, tz, g in self.near_trees()[:3]:
            if time.time() - started > 150:
                break                                      # the supervisor restarts a brain that writes no status for 240 s
            self.status(force=True)
            self.mem.record("claim", kind="tree", key=f"{tx},{ty}", ttl=300)
            self.activity = f"chopping at {tx},{ty}"
            ok = False
            self.c.goto(tx, ty).wait(timeout=60)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)):
                if max(abs(self.c.x - tx), abs(self.c.y - ty)) <= 2:
                    ok = True
                    break
                if str(self.c.gotoexact(tx + dx, ty + dy).wait(timeout=15)).startswith("nopath") and max(abs(self.c.x - tx), abs(self.c.y - ty)) > 6:
                    break                                  # no way into that stand of trees: the next tree, not five more tries here
            ok = ok or max(abs(self.c.x - tx), abs(self.c.y - ty)) <= 2
            if not ok:
                self.facts[("tree", tx, ty)] = time.time() + 900
                continue
            if not self.wield(hat):
                self.note("chop", "The hatchet could not be wielded (the hands are full?), and an axe chops only when it is equipped.", key="nowield")
                return None
            self.c.events.drain()
            self.c.use(hat.serial)
            if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
                self.note("chop", "Double-clicking the hatchet raised no target cursor (an axe has to be in hand?).", key="nochopcursor")
                self.facts[("tree", tx, ty)] = time.time() + 300
                continue
            self.c.call(f"targettile {tx} {ty} {tz} {g}", timeout=8)
            end = time.time() + 45
            while time.time() < end:
                time.sleep(2.5)
                if self.threats(8) or self.hp_pct() < 60:
                    # BotCarpBR chopped on while a troll killed it: stop and let the flight and avoid rules have the bot
                    self.log(f"stopped chopping at {tx},{ty}: {'a hostile is near' if self.threats(8) else 'hurt'}")
                    return True
                lines = self.read_journal()
                for l in lines:
                    if re.search(r"wood|log|tree|axe|lumber|chop|enough|far", l, re.I):
                        self.note("chop", f"Chopping says: {l[:100]}", key=f"chopmsg:{l[:40]}")
                if any(re.search(r"you put .* in your|logs? in your", l, re.I) for l in lines):
                    self.mem.record("res", kind="tree", key=f"{tx},{ty}", ok=True)
                if any(re.search(r"cannot be seen|can't see", l, re.I) for l in lines):
                    # a wall or a building stands between the reachable side and the tree: that never changes, so no one tries it today
                    self.mem.record("res", kind="tree", key=f"{tx},{ty}", ok=False, reason="the tree cannot be seen from where it can be reached")
                    self.mem.record("blocked", kind="tree", key=f"{tx},{ty}", ttl=86400)
                    self.facts[("tree", tx, ty)] = time.time() + 86400
                    break
                if any(re.search(r"not enough wood|no wood|too far|broke", l, re.I) for l in lines):
                    self.mem.record("res", kind="tree", key=f"{tx},{ty}", ok=False, reason="no wood left or too far")
                    self.mem.record("blocked", kind="tree", key=f"{tx},{ty}", ttl=1500)
                    self.facts[("tree", tx, ty)] = time.time() + 1500
                    break
            return True
        return False

    def wield(self, tool):
        """Hold a tool in the hands (an axe chops only when equipped): whatever is in the hands goes back in the pack first."""
        if tool.serial in {i.serial for i in self.c.equipped}:
            return True
        for w in self.c.equipped:
            if w.layer in ("OneHanded", "TwoHanded"):
                self.c.unequip(w.serial)
                time.sleep(0.8)
        try:
            self.c.call(f"equip {tool.serial}", timeout=6)
        except Exception:
            pass
        time.sleep(0.8)
        ok = tool.serial in {i.serial for i in self.c.equipped}
        self.log(f"wield {tool.name}: {'in hand' if ok else 'refused'}")
        if ok:
            self.note("chop", "Chopping needs the hatchet in hand ('The axe must be equipped for any serious wood chopping.'); double-clicking it in the pack does nothing else.", key="axeequip")
        return ok

    def feature(self, name):
        """True when this bot is in the cohort that has `name` (work/botfarm/features.json, read when the brain starts)."""
        return name in getattr(self, "features", ()) or self.ambition_grants(name)      # a persona earns some (ambition.py)

    # ---- structured events (one line per meaningful act) and the features hot reload ------------------------------------------

    GOLD_EV = {"r_sell": "sale", "r_sellmeat": "sale", "r_sellloot": "sale", "r_sellgear": "sale", "r_market": "trade", "r_resupply": "buy", "r_upgrade": "buy", "r_restock": "buy",
               "r_retool": "buy", "r_fletch": "buy", "r_chop": "buy", "r_bank": "bank", "r_loot": "loot", "r_corpse": "loot", "r_carve": "loot",
               "r_dead": "death_loss", "r_pet": "buy", "r_tame": "buy"}

    def ev(self, kind, **kw):
        """One structured event in decisions.jsonl: what happened, where, under which rule."""
        self.dlog("ev", ev=kind, cell=cell_of(self.c.x, self.c.y), rule=getattr(self, "current_rule", None) or getattr(self, "last_rule", None), **kw)

    def after_tick(self, acted):
        """After every tick: a change of carried gold becomes an event credited to the gold-moving rule that acted last (the gold arrives a moment
        after the trade, sometimes in the next tick), and features.json is re-read when it changed."""
        if acted in self.GOLD_EV:
            self._gold_rule, self._gold_rule_at = acted, time.time()
        g = self.c.gold
        prev = getattr(self, "_gold_prev", None)
        if prev is not None and g != prev:
            rule = getattr(self, "_gold_rule", None) if time.time() - getattr(self, "_gold_rule_at", 0) < 15 else None
            kind = self.GOLD_EV.get(rule, "gold")
            if kind == "bank":
                kind = "deposit" if g < prev else "withdraw"
            if g < prev and self.c.ghost:
                kind, rule = "death_loss", acted                # the corpse keeps the gold the bot carried
            if (kind in ("sale", "loot", "withdraw") and g < prev) or (kind in ("buy", "deposit", "death_loss") and g > prev):
                kind, rule = "gold", acted                # the sign does not fit that rule: not its doing
            self.dlog("ev", ev=kind, cell=cell_of(self.c.x, self.c.y), rule=rule or acted, gold=g - prev, carried=g)
            goals.income(self, kind, g - prev)
        self._gold_prev = g
        try:
            goals.tick(self)                                  # the savings goal (feature goals): once a minute
        except Exception as e:
            self.log(f"goals: {type(e).__name__}: {e}")
        try:
            townguard.tick(self)                              # under attack inside a guarded region: "guards" (feature town_guards)
        except Exception as e:
            self.log(f"town_guards: {type(e).__name__}: {e}")
        try:
            talk.tick(self)                                   # a pending reply to a person, a monster in the city (feature talk)
        except Exception as e:
            self.log(f"talk: {type(e).__name__}: {e}")
        try:
            self.buddy_tick()                                 # the published file, errands, pair start and end (buddy.py)
        except Exception as e:
            self.log(f"buddy: {type(e).__name__}: {e}")
        try:
            if hasattr(self, "ladder_tick"):                  # tamers, fishers, miners have no FirstTrip (so no ladder)
                self.ladder_tick()                            # region_first, kills on the ring and outside, rungs 1 and 2 (ladder.py)
        except Exception as e:
            self.log(f"ladder: {type(e).__name__}: {e}")
        try:
            self.pacing_tick()                                # the walk mode in towns (pacing.py)
        except Exception as e:
            self.log(f"pacing: {type(e).__name__}: {e}")
        try:
            self.ambition_tick()                              # persona, milestones (ambition.py)
            self.plan_tick(acted)                             # the activity that moves the ambition fastest (planner.py)
            self.gr_tick(acted)                               # what this ground paid (ground_rates.py)
        except Exception as e:
            self.log(f"ambition: {type(e).__name__}: {e}")
        try:
            self.stall_tick(acted)                            # no progress for 15 min: say why and change course (stall.py)
        except Exception as e:
            self.log(f"stall: {type(e).__name__}: {e}")
        if time.time() - getattr(self, "_features_checked", 0) > 30:
            self._features_checked = time.time()
            try:
                m = os.path.getmtime(os.path.join(FARM, "features.json"))
            except OSError:
                m = 0
            if m != getattr(self, "_features_mtime", None):
                was = set(getattr(self, "features", ()))
                self._features_mtime = m
                self.features = load_features(self.name)
                if was != self.features and getattr(self, "_features_loaded", False):
                    self.log(f"features now {sorted(self.features)} (were {sorted(was)})")
                    self.dlog("features", now=sorted(self.features), were=sorted(was))
                self._features_loaded = True

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
        if self.far_front((x, y), "travel", per):                  # far: a routed walk in legs, resumed by r_far; the hops below are for near places
            return False
        for _ in range(tries):
            if max(abs(self.c.x - x), abs(self.c.y - y)) <= near:
                return True
            before = (self.c.x, self.c.y)
            res = self.goto_near(x, y, near).wait(timeout=per)
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
            "features": sorted(getattr(self, "features", ())),
            "bank": self.facts.get("bank_balance", 0), "net_worth": self.c.gold + self.facts.get("bank_balance", 0),
            "region": self.region_name(), "home": (self.home() or {}).get("name"),
            **getattr(self, "status_extra", {}), **self.ambition_status(),
        }
        with open(os.path.join(self.dir, "status.json"), "w", encoding="utf-8") as f:
            json.dump(s, f)
        with open(self.totals_path, "w", encoding="utf-8") as f:
            json.dump({"kills": s["kills"], "deaths": s["deaths"], "gains": gains, "uptime": s["uptime"]}, f)
        save_bank(self.dir, self.facts.get("bank_balance", 0))
        self.save_facts()

    # facts a new brain takes over from the last one (a restart used to drop the held ground, the camp and which gear was looted)
    PERSIST = ("ground", "anchor", "anchors_left", "crowded", "pushed_at", "spots_reached", "gear_looted", "meat_sold_at", "gear_sold_at", "sold_at",
               "sell_skip_until", "soldout_until", "stocked_at", "bank_balance", "banked_at", "fletch_wait", "wood_wait", "shop_at", "chop_fail",
               "emptied", "home", "camp_step", "home_region", "corpse", "gold_alive", "far", "skill_gap", "killer", "killer_until", "mat_until", "mat_from", "walk_until", "goal", "goals_done", "inc_log", "death_log", "res_at", "res_from", "died_at", "stall_off", "stall_earn_until", "stall_gather_until", "persona", "worth_ring", "regions_seen", "dungeon_seen", "milestones", "trips_done", "act_rates", "plan_v", "plan_explored_at", "bw", "walk_rate")
    PERSIST_SETS = ("gear_looted", "emptied")

    def save_facts(self):
        out = {}
        for k in self.PERSIST:
            if k in self.facts:
                v = self.facts[k]
                out[k] = sorted(v) if isinstance(v, set) else v[-20:] if isinstance(v, list) else v     # the brains read only the newest
        try:
            with open(self.facts_path + ".tmp", "w", encoding="utf-8") as f:
                json.dump(out, f)
            os.replace(self.facts_path + ".tmp", self.facts_path)
        except (OSError, TypeError, ValueError):
            pass

    def load_facts(self):
        try:
            d = json.load(open(self.facts_path, encoding="utf-8"))
        except (OSError, ValueError):
            return
        for k, v in d.items():
            if k in self.PERSIST:
                self.facts[k] = set(v) if k in self.PERSIST_SETS else v
        self.log(f"facts taken over from the last brain: {sorted(d)}")

    def refresh_skills(self):
        for line in self.c.call("skills", timeout=8):
            m = re.match(r"\[SKILL\]\s+(.+?)\s+(\d+\.\d)\s+\(base", line)
            if m:
                self.skill_values[m.group(1).strip()] = float(m.group(2))

    # ---- rules every profession has -----------------------------------------------------------------------------

    def r_dead(self):
        HEALER = deathloop.healer(self)                        # the nearest healer (places.py) without a fresh death beside it (feature death_loop)
        if not self.c.ghost:
            if self.facts["ghost_since"] is not None:
                self.facts["just_resurrected"] = True
                deathloop.hook(self, "resurrected")
                if self.c.war_mode:
                    self.c.war(False)
                # step clear of the healer before resting: seven resurrected bots once rested on its four tiles, and the next ghost could not get in
                if max(abs(self.c.x - HEALER[0]), abs(self.c.y - HEALER[1])) <= 4:
                    ring = [(HEALER[0] + dx, HEALER[1] + dy) for dx, dy in ((8, 0), (-8, 0), (0, 8), (0, -8), (6, 6), (-6, 6), (6, -6), (-6, -6))]
                    others = [m for m in self.c.mobiles(within=16) if m.name and m.name.startswith("Bot")]
                    spot = min(ring, key=lambda p: sum(1 for m in others if max(abs(m.x - p[0]), abs(m.y - p[1])) <= 2))
                    self.c.goto(*spot).wait(timeout=15)
            self.facts["ghost_since"] = None
            self.facts.pop("res_declined", None)
            return deathloop.hook(self, "alive")             # just back, weak, hit by nothing in view: away from where it died
        if self.facts["ghost_since"] is None:
            self.facts["ghost_since"] = time.time()
            self.deaths += 1
            self.facts["war_at_death"] = self.c.war_mode
            dx_, dy_ = self.death_xy()
            self.log(f"ghost at {self.c.x},{self.c.y}, died at {dx_},{dy_}; war mode at death = {self.c.war_mode}")
            self.death_spots.append((dx_, dy_))
            if deathloop.on(self):
                deathloop.note_death(self, dx_, dy_)
            src = deathsrc.source(self)
            self.mem.record("death", cell=cell_of(dx_, dy_), killers=[t[2] for t in getattr(self, "recent_threats", [])[:3]] or deathsrc.killers(self, src), at=[dx_, dy_],
                            skill=round(area_danger.combat_skill(getattr(self, "skill_values", {})), 1))
            on_run = time.time() - self.facts.get("corpse_run_at", 0) < 400
            # killed again while fetching the corpse: whatever killed it is still there, so this corpse is not worth a second walk
            old = self.facts.get("corpse")
            if not (old and time.time() - old.get("t", 0) < 420):         # a record the last brain wrote for this death is kept
                self.facts["corpse"] = {"xy": (dx_, dy_), "t": time.time(), "gold": self.last_gold or self.facts.get("gold_alive", 0),
                                        "tries": 1 if on_run else 0}
            if on_run:
                self.note("death", f"Going back for its corpse got the {self.pname} killed again; the killer was still there and nothing warned it.", key="corpsetrap")
            json.dump({"death_spots": self.death_spots}, open(self.know_path, "w", encoding="utf-8"))
            self.note("death", f"A {self.pname} died.", key=f"death:{self.deaths}", pos=[self.c.x, self.c.y], last=list(self.journal)[-4:])
            threats = getattr(self, "recent_threats", [])
            killer = threats[0][1] if threats else src["label"]
            self.log(f"DEAD at {self.c.x},{self.c.y} (killed by {killer}); walking to the healer")
            self.facts["killer"] = {"name": str(killer), "t": time.time()}
            self.facts.pop("killer_until", None)
            self.ev("death", killer=killer, at=[dx_, dy_], war=self.facts.get("war_at_death"), why=src["why"], dmg=src["dmg"], cues=src["cues"], near=src["near"], **self.vitals())
        self.activity = "ghost: walking to the healer"
        # a living mobile sees a dead one only if it is in war mode (Mobile.CanSee), so a ghost in peace mode is invisible to the healer: switch it on
        if not self.c.war_mode:
            self.c.war(True)
            self.note("death", "A ghost in peace mode is invisible to the healer (the game only shows a ghost to the living in war mode); nothing tells the player to switch to war mode.", key="ghostwar")
        serial = self.find_gump("Resurrection")
        if serial and deathloop.hook(self, "offer", serial=serial):        # an offer beside a fresh death: decline, another healer first
            return True
        near = self.threats(12) if serial else []
        if serial and near and self.facts.get("res_declined", 0) < 3:
            # a fresh body has few hit points: with a monster this close, CANCEL, walk away and take the offer somewhere safe (BotMaceBR, 13:33-13:36)
            n = self.facts["res_declined"] = self.facts.get("res_declined", 0) + 1
            m = min(near, key=lambda o: o.distance)
            self.c.call(f"gumpresponse 0 gump:{serial}", timeout=8)
            self.log(f"resurrection offer declined ({n}/3): {m.name} is {m.distance} tiles away; walking away first")
            self.ev("res_declined", threat=self.mkey(m), dist=m.distance, n=n)
            self.note("death", "A healer offered a resurrection with a monster a few tiles away; a resurrected character has few hit points, so a player cancels and walks clear first.", key="resdecline")
            self.c.goto(*self.flee_point(m)).wait(timeout=10)
            return True
        if serial:
            self.log(f"resurrection offer opened; ghost war mode = {self.c.war_mode} (at death: {self.facts.get('war_at_death')})")
            self.facts["offer_at"] = time.time()                 # the watcher's "resurrected" event: by the healer's offer
            self.c.call(f"gumpresponse 1 gump:{serial}", timeout=8)
            self.note("death", "The healer's offer opens as a Resurrection gump (CONTINUE / CANCEL) once the ghost stands near the healer.", key="healergump")
            time.sleep(3)
            return True
        if self.criminal_wait():
            self.activity = "ghost: waiting out the criminal flag (the healer refuses a criminal)"
            time.sleep(3)
            return True
        if self.feature("ghost_hint") and time.time() - self.facts.get("ghost_hint_at", 0) < 20:
            self.facts["ghost_hint_at"] = 0                    # the server said the healer cannot see this ghost: war mode, out past 4 tiles, back in
            if not self.c.war_mode:
                self.c.war(True)
            self.c.goto(HEALER[0], HEALER[1] + 6).wait(timeout=12)
            self.c.goto(*HEALER).wait(timeout=12)
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
            self.far_goto(HEALER, "healer", 5)                      # a ghost far from any healer walks a planned route, not a straight goto
        return True

    def r_corpse(self):
        """Back from the dead: go and fetch the belongings from the corpse before it rots (the death message says to), once, if there was something worth the walk."""
        info = self.facts.get("corpse")
        if info and info.get("await_far"):
            st = self.facts.get("far")
            if st and max(abs(st["dest"][0] - info["xy"][0]), abs(st["dest"][1] - info["xy"][1])) <= 8:
                self.r_far()                                  # drive the corpse walk here: another rule's far walk would replace it (a tamer's spot walk did)
                return True                                   # and keep the tick even when r_far declines one (it let r_explore in)
            info["await_far"] = False
            info["tries"] = 0                                 # the routed walk ended: look for the corpse now
        if not info or self.c.ghost or (info["tries"] >= 1 and not (self.bw_corpse_go() and not self.facts.get("far"))):      # a Between Worlds corpse plan retries until it is taken, while no routed walk (r_far) is carrying it there
            return False
        if time.time() > self.corpse_deadline(info):
            self.facts.pop("corpse")
            return False
        mat = self.materializing()                           # monsters cannot see the bot and worn gear comes back: go now, whatever it carried
        if not mat and (self.hp_pct() < 70 or self.threats(8)):
            return False
        if info["gold"] < 60 and not mat and not self.feature("blue_self_loot"):
            self.facts.pop("corpse")
            return False
        info["tries"] += 1
        x, y = info["xy"]
        if not self.bw_corpse_go() and not self.far_worth_corpse((x, y), info["gold"]):      # a Between Worlds corpse plan goes (bw.py)
            self.facts.pop("corpse", None)                           # 100 gold under a corpse 1,000 tiles away is not worth the walk
            return False
        if not self.bw_corpse_go() and self.mem.dangerous_cell(cell_of(x, y)):
            self.log(f"not going back to the corpse at {x},{y}: the shared memory says bots die there")
            self.facts.pop("corpse")
            return False
        self.facts["corpse_run_at"] = time.time()
        self.activity = "going back for my corpse"
        self.log(f"going back to the corpse at {x},{y} ({info['gold']} gold lost)")
        self.travel(x, y, near=1, tries=12)
        if max(abs(self.c.x - x), abs(self.c.y - y)) > 8:
            if self.facts.get("far"):
                info["await_far"] = True                     # a routed walk carries it there (driven from the top of this rule): look on arrival
                self.activity = "walking back to my corpse"
                return True
            else:
                self.log(f"the walk back to the corpse at {x},{y} stopped {max(abs(self.c.x - x), abs(self.c.y - y))} tiles short")
            return True                                       # the search below runs only at the corpse (it used to run at the healer and give up)
        corpses = [i for i in self.c.containers(within=6) if ("corpse" in i.name.lower() or "remains" in i.name.lower()) and not i.name.lower().startswith(("a ", "an "))]
        corpses.sort(key=lambda i: max(abs(i.x - x), abs(i.y - y)))          # the one lying where this bot died
        if not corpses:
            try:                                          # a corpse turned to bones is not a container in the tile data, so containers() leaves it out
                bones = [i for i in self.ground_items(8) if any(w in (i.name or "").lower() for w in ("bone", "remains", "corpse"))]
            except Exception:
                bones = []
            if not bones and info.get("serial"):
                from types import SimpleNamespace as _NS
                bones = [_NS(serial=info["serial"], name="my corpse (kept serial)", x=x, y=y)]      # bones keep the corpse's serial (the watcher)
            if bones:
                bones.sort(key=lambda i: max(abs(i.x - x), abs(i.y - y)))
                self.log(f"the corpse at {x},{y} has turned to bones ({bones[0].name}): opening them")
                corpses = bones
        if not corpses:
            self.note("death", "Going back to the death spot found no corpse: it had already rotted away, or the player never saw where it was.", key="nocorpse")
            near = sorted({(i.name or "?") for i in self.c.containers(within=8)} | {(i.name or "?") for i in self.ground_items(8)})[:10]
            self.log(f"no corpse of mine at {x},{y} (containers within 8: {near}): the run ends")
            self.facts.pop("corpse", None)              # once was enough before; a Between Worlds plan retries, so it must end here
            return True
        corpse = corpses[0]
        self.c.gotoexact(corpse.x, corpse.y).wait(timeout=8)
        self.c.events.drain()
        used_at = time.time()
        self.c.use(corpse.serial)
        if self.feature("blue_self_loot"):
            time.sleep(1.5)
            how = self.self_loot_result(used_at)
            if how:
                self.dlog("ev", ev="self_loot", how=how, secs=round(time.time() - self.facts.get("mat_from", time.time())))
            if how == "all":
                self.log("took everything back from the corpse with one double-click")
                self.facts.pop("corpse", None)
                return True                                  # worn gear went back on; r_gear puts on what did not
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
        hurt = time.time() - self.facts.get("hurt_at", 0) < 10      # hit lately by something not counted (out of view, or on a slope)
        if self.hp_pct() >= self.flee_below() or not (threats or hurt):
            return False
        if not threats:
            self.log(f"hurt (hp {self.c.hp}) by something not in view: running toward town")
            self.note("combat", f"A {self.pname} lost health to something it could not see near it (out of view, or above or below it on a slope).",
                      key="unseenhit")
        self.activity = "fleeing"
        self.on_flee()
        for item in self.c.backpack if time.time() - self.facts.get("drank", 0) > 12 else ():
            if item.name == "Yellow Potion":      # a lesser heal potion: yellow, as in the era
                self.facts["drank"] = time.time()
                self.c.use(item.serial)
                self.log("drank a yellow potion at low health")
                self.ev("consumable_used", item="yellow potion", hp=self.hp_pct())
                self.note("combat", "At low health the only way to tell the Heal potion is by its color (yellow); nothing in the pack says so.", key="potioncolor")
                time.sleep(1.5)
                return True
        if self.skill_values.get("Healing", 0) >= 30 and self.bandage_self():
            return True
        threat = threats[0] if threats else None
        if threat:
            self.log(f"fleeing from {threat.name} at hp {self.c.hp}")
            self.chatter("warn", cooldown=600, m=threat.name, where=self.where())
        self.sprint()
        self.call_guards(threat)
        self.c.goto(*self.flee_point(threat)).wait(timeout=4)
        return True

    def on_flee(self):
        pass

    def sprint(self):
        """Run whatever the stamina, for the next few seconds: a flight. The client drops to a walk by itself only when stamina is gone;
        sprint_check() puts the run mode back to auto (run only at half stamina or more) once the flight is over."""
        self.facts["sprint_at"] = time.time()
        if time.time() < self.facts.get("walk_until", 0):
            return                                                       # too tired to run (stamina_relief): walk
        if self.facts.get("runmode") != "always":
            self.set_runmode("always")

    def sprint_check(self):
        if self.facts.get("runmode") == "always" and time.time() - self.facts.get("sprint_at", 0) > 8:
            self.set_runmode("auto")

    def set_runmode(self, mode):
        try:
            self.c.call(f"runmode {mode}", timeout=3)
            self.facts["runmode"] = mode
        except Exception as e:                                          # an older client without the command: nothing to switch
            self.facts["runmode"] = mode
            self.log(f"runmode {mode}: {e}")

    def flee_below(self):
        """Health (percent) under which r_flee runs."""
        return 40

    def death_xy(self):
        """Where this character died: its own corpse if it is in view (a brain busy in a long loop notices a death late, by which time the ghost
        may have walked on), else where the ghost stands."""
        try:
            mine = [i for i in self.c.containers(within=24) if self.name.lower() in (i.name or "").lower()]
        except Exception:
            mine = []
        if mine:
            m = min(mine, key=lambda i: i.distance)
            return m.x, m.y
        return self.c.x, self.c.y

    # ---- home: the town the bot started in, from the gazetteer (generality step 1) ----------------------------------------------------------

    def home(self):
        """The bot's home town (a gazetteer region): remembered, else the town it stands in, else the nearest town; None when it cannot tell yet
        (no gazetteer, or first seen below ground)."""
        h = getattr(self, "_home", None)
        if h:
            return h
        if gz is None:
            return None
        name = self.facts.get("home_region")
        h = gz.region(name) if name else None
        if not h:
            here = gz.home_region(self.c.x, self.c.y)
            if here and here.get("kind") == "town":
                h = here
            elif self.c.x < 5120:                         # on the surface: the nearest town; below ground, wait until it is back up
                h = gz.nearest_town(self.c.x, self.c.y)[0]
        if h:
            self.facts["home_region"] = h["name"]
            self._home = h
        return h

    def home_centre(self):
        h = self.home()
        return (int(h["centre"][0]), int(h["centre"][1])) if h else TOWN

    def home_core(self):
        """(x0, y0, x1, y1) of the city itself: the home rectangle that holds its centre (Britain's region also takes in farmland to the west)."""
        h = self.home()
        if not h:
            return (1400, 1540, 1700, 1770)
        cx, cy = self.home_centre()
        rects = [tuple(r) for r in gz.town_rects(h)] or [(cx - 60, cy - 60, cx + 60, cy + 60)]
        inside = [r for r in rects if r[0] <= cx < r[2] and r[1] <= cy < r[3]]
        return inside[0] if inside else min(rects, key=lambda r: abs((r[0] + r[2]) / 2 - cx) + abs((r[1] + r[3]) / 2 - cy))

    def home_refuges(self):
        h = self.home()
        try:
            out = [tuple(p[:2]) for p in gz.refuges(h)] if h else []
        except Exception:
            out = []
        return out or REFUGES

    def region_name(self):
        """The region the bot stands in (a town, a dungeon), or "wilds"."""
        if gz is None:
            return "Britain" if self.in_britain() else "wilds"
        r = gz.home_region(self.c.x, self.c.y)
        return r["name"] if r else "wilds"

    def in_britain(self):
        """In the bot's home town (the name stays from the Britain-only days: many rules ask it)."""
        h = self.home()
        rects = gz.town_rects(h) if h else BRITAIN
        return any(x0 <= self.c.x < x1 and y0 <= self.c.y < y1 for x0, y0, x1, y1 in rects)

    def refuge_from(self, threat):
        """The town refuge farthest from the threat among the nearer ones: away from it, and not always to the healer."""
        near = sorted(self.home_refuges(), key=lambda p: abs(p[0] - self.c.x) + abs(p[1] - self.c.y))[:4]
        if threat is None:
            return near[0]
        return max(near, key=lambda p: max(abs(p[0] - threat.x), abs(p[1] - threat.y)) - 0.3 * max(abs(p[0] - self.c.x), abs(p[1] - self.c.y)))

    ANCHOR_WAIT = 480          # one respawn interval of the Britain spawners (5 to 10 minutes)
    ANCHOR_RADIUS = 12

    def kill_worth_ok(self, kind):
        return True

    def note_kill_at(self, x, y, kind=None):
        k = self.facts.setdefault("kills_at", [])
        k.append((time.time(), x, y))
        del k[:-40]
        self.facts["last_kill_at"] = time.time()
        if kind is not None and not self.kill_worth_ok(kind):
            return                                        # a chicken or a cat is no reason to camp
        a = self.facts.get("anchor")
        if a and abs(a["x"] - x) <= 20 and abs(a["y"] - y) <= 20:
            a["last"] = time.time()
            a["kills"] += 1
        else:
            self.facts["anchor"] = {"x": x, "y": y, "since": time.time(), "last": time.time(), "kills": 1}
            self.dlog("choice", what="camp", why=f"a kill at {x},{y}: staying for the respawn")

    def anchor_seen(self):
        """Worthwhile prey in sight near the camp: the spawn is still giving, stay (counted as evidence at most once a minute)."""
        a = self.facts.get("anchor")
        if a and max(abs(self.c.x - a["x"]), abs(self.c.y - a["y"])) <= self.ANCHOR_RADIUS + 8:
            now = time.time()
            if now - a.get("seen_at", 0) > 60:
                a["evidence"] = a.get("evidence", 0) + 1
                a["seen_at"] = now
            a["last"] = now

    CROWD = 1                                             # other bots a hunting spot holds before a player moves on (the owner: at most one)

    def other_bots(self, within=20):
        """[(name, x, y)] of the other bots in view: players, whose kills and spots are theirs."""
        return self.party_filter([(m.name, m.x, m.y) for m in self.c.mobiles(within=within) if m.name.startswith("Bot") and m.name != self.name])      # (not the party's members)

    def taken_by_other(self, m, others, mine=None):
        """Another bot stands within 2 tiles of this prey: its fight, not ours (no kill-stealing), unless the prey is on us or already our target."""
        if m.distance <= 1 or m.serial == mine:
            return False
        return any(max(abs(x - m.x), abs(y - m.y)) <= 2 for _, x, y in others)

    def crowded_here(self, radius=18):
        """Three other bots within radius: a crowded spot, which a player leaves for the next one. Not all of them: the bots there are ranked by
        a hash of name and cell (each sees nearly the same set, so they agree), the first three stay and the rest move on (when every one of
        four left, the spot emptied)."""
        others = [n for n, _, _ in self.other_bots(radius)]
        cell = cell_of(self.c.x, self.c.y)
        cap = self.ground_cap(cell)
        if len(others) <= cap:
            return False
        ranked = sorted(others + [self.name], key=lambda n: zlib.crc32(f"{n}@{cell}".encode()))
        return ranked.index(self.name) > cap             # cap others allowed: the first cap + 1 by the hash stay

    def ground_cap(self, cell):
        """How many other bots a ground holds: 3, one more where memory has seen plenty spawning (10+ sightings), one more for steady kills
        (3+): a cow farm with a big wildlife spawner takes 5."""
        c = self.mem.state["world"]["cells"].get(cell)
        if not c:
            return self.CROWD
        return self.CROWD                                 # the owner: at most one other bot per ground, farms included

    def mark_crowded(self, x, y, why):
        self.facts.setdefault("crowded", {})[cell_of(x, y)] = time.time() + 900
        self.facts["pushed_at"] = time.time()             # the next ground: a near one first (next_spot)
        self.dlog("choice", what="leave crowded spot", why=f"{why} at {x},{y}: {len(self.other_bots(14))} other bots within 14 tiles")

    def r_camp(self):
        """Stay near the camp for one respawn interval after the last prey: a few steps about now and then, otherwise stand (resting and
        bandaging come first when hurt). Leave when an interval passes with nothing."""
        a = self.facts.get("anchor")
        if not a:
            return False
        now = time.time()
        ev = a["kills"] + a.get("evidence", 0)
        wait = 360 if ev >= 3 else (240 if ev >= 2 else 150)
        if now - a["last"] > wait:
            left = self.facts.setdefault("anchors_left", [])
            left.append((a["x"], a["y"], now, a["kills"]))
            del left[:-6]
            self.facts.pop("anchor")
            self.dlog("choice", what="leave camp", why=f"{a['kills']} kills, {a.get('evidence', 0)} sightings at {a['x']},{a['y']} in {int(now - a['since']) // 60} min; nothing worth it for {wait // 60} min")
            return False
        if self.crowded_here():
            # a crowded camp: the kills go to whoever reaches each spawn first, the corpses are someone else's, so a player moves on
            self.facts.pop("anchor")
            self.mark_crowded(a["x"], a["y"], "camp")
            return False
        self.activity = f"camping the spawn at {a['x']},{a['y']}"
        if max(abs(self.c.x - a["x"]), abs(self.c.y - a["y"])) > self.ANCHOR_RADIUS:
            self.c.goto(a["x"], a["y"]).wait(timeout=5)
            return True
        if now - self.facts.get("camp_step", 0) > 60:
            # a player waiting for a respawn stands, bandages and looks about, with a step now and then (the owner, 2026-10-15)
            self.facts["camp_step"] = now
            self.c.goto(a["x"] + random.randint(-2, 2), a["y"] + random.randint(-2, 2)).wait(timeout=4)
        else:
            time.sleep(3.5)
        return True

    def revisit_anchor(self):
        """A camp that paid (2 kills or more), left at least six minutes ago so its spawn is back: the next patrol point, before a new place."""
        now = time.time()
        left = self.facts.get("anchors_left", [])
        ok = [a for a in left if now - a[2] > 360 and a[3] >= 2]
        if not ok:
            return None
        a = min(ok, key=lambda a: abs(a[0] - self.c.x) + abs(a[1] - self.c.y))
        left.remove(a)
        self.dlog("choice", what="revisit camp", why=f"{a[3]} kills at {a[0]},{a[1]}, left {int(now - a[2]) // 60} min ago")
        return a[0], a[1]
        self.facts["empty_visits"] = 0

    def home_range(self):
        """(center, radius): the middle of this bot's own kills in the last hour (else the best-known hunting ground near Britain), and how far
        it may roam from there: 90 tiles, 40 more for every 8 minutes without a kill, up to 320."""
        now = time.time()
        recent = [(x, y) for t, x, y in self.facts.get("kills_at", []) if now - t < 3600]
        if recent:
            xs, ys = sorted(p[0] for p in recent), sorted(p[1] for p in recent)
            center = (xs[len(xs) // 2], ys[len(ys) // 2])
        else:
            best = self.mem.hunting_cells(near=self.home_centre(), radius=150, n=1)
            center = cell_center(best[0][1]) if best else self.home_centre()
        return center, min(150, 90 + 30 * (self.facts.get("empty_visits", 0) // 3))

    def patrol_visit(self, prey_seen):
        """A patrol point reached: prey in sight keeps the range tight, three empty points in a row widen it a step."""
        self.facts["empty_visits"] = 0 if prey_seen else self.facts.get("empty_visits", 0) + 1

    def flee_point(self, threat):
        """Where to run: a town refuge when one is close, otherwise straight away from the threat. Far out (a veteran archer 300 tiles west of
        town) the walk to a town refuge planned "nopath" every tick, and the bot stood still and died fleeing."""
        if self.in_sewer():
            return self.home_refuges()[0]                 # a flight from below: the walk home leaves the level through a teleporter (tele_cross)
        dest = self.refuge_from(threat)
        if threat is None or max(abs(dest[0] - self.c.x), abs(dest[1] - self.c.y)) <= 60:
            return dest
        dx, dy = self.c.x - threat.x, self.c.y - threat.y
        n = max(abs(dx), abs(dy), 1)
        ax, ay = dx / n, dy / n
        hx, hy = self.home_centre()
        tx, ty = hx - self.c.x, hy - self.c.y
        m = max(abs(tx), abs(ty), 1)
        tx, ty = tx / m, ty / m
        vx, vy = ax + tx, ay + ty                         # away from the threat, and toward town and its guards
        if abs(vx) + abs(vy) < 0.3:
            vx, vy = -ty, tx                              # the threat stands between the bot and town: step aside first
        k = max(abs(vx), abs(vy), 1e-6)
        return self.c.x + round(12 * vx / k), self.c.y + round(12 * vy / k)

    def call_guards(self, threat):
        """A player chased into town shouts for the guards. Whether they come for a monster is exactly what is worth finding out."""
        if threat is None or not self.in_britain() or time.time() - self.facts.get("guards_at", 0) < 30:
            return
        if not townguard.guarded_at(self.c.x, self.c.y):                          # (any bot: where the shard has no guards the shout cannot work)
            return                                           # the outskirts, the wilds: no guards stand here, the bot's own flight is all there is
        self.facts["guards_at"] = time.time()
        self.c.say("guards")
        time.sleep(2.5)
        guard = any("guard" in (m.name or "").lower() for m in self.c.mobiles(within=14))
        still = any(m.serial == threat.serial and not m.is_dead for m in self.c.mobiles(within=16))
        self.log(f"called the guards on {threat.name} at {self.c.x},{self.c.y}: guard in sight {guard}, it is still here: {still}")
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
            self.ev("consumable_used", item="orange potion", hp=self.hp_pct())
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
        near = self.evade_threats()                       # red, attacked me, attacks on sight (FightMode), or an unknown kind closing in: not a crow, not a mongbat
        if not near:
            return False
        m = near[0]
        self.activity = f"walking away from {m.name}"
        self.note("danger", f"A {m.name} came within {m.distance} tiles of a working {self.pname}; a gatherer or crafter can only walk away and come back later.", key=f"evade:{self.mkey(m)}")
        self.sprint()
        self.c.goto(*self.flee_point(m)).wait(timeout=8)     # away from it, and toward town, not out into the wilds
        return True

    def bandage_self(self):
        b = self.c.find("bandage")
        if not b or self.hp_pct() > 80:
            return False
        self.c.events.drain()
        self.c.use_on(b.serial, "self")
        ev = self.c.wait_for([Event.BANDAGE_DONE, Event.BANDAGE_FAILED], timeout=12)
        self.log(f"bandage: {ev.text[:60] if ev else 'no answer'}")
        self.ev("consumable_used", item="bandage", hp=self.hp_pct(), ok=bool(ev))
        return True

    def open_corpse(self, corpse):
        """Open a corpse and say (opened, forbidden). The server says "Looting this monster corpse will be a criminal act!" (someone else's kill in
        its first minutes) or "You did not earn the right..." a moment before the contents arrive, so both are read from one stream here:
        Client.wait_for() drains the log first and never saw the warning. "You must wait to perform another action" leaves it unopened."""
        self.c.events.drain()
        self.c.use(corpse.serial)
        opened = forbidden = False
        end = time.time() + 4
        while time.time() < end and not opened:
            for e in self.c.events.poll():
                t = e.text or ""
                if "criminal act" in t or "earn the right" in t:
                    forbidden = True
                if e.kind == Event.CONTAINER_CONTENTS or t.startswith("[CONTAINER] Opened"):
                    opened = True
                if "must wait to perform" in t:
                    end = time.time() + 0.3                # the server refused the double-click: no contents will come
            time.sleep(0.05)
        return opened, forbidden

    def r_loot(self):
        if self.threats(7):
            return False                                  # hostile kinds only: on a farm the next cow is always within 7 tiles
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
        opened, forbidden = self.open_corpse(corpse)
        if not opened and not forbidden:
            # "You must wait to perform another action": the corpse did not open, so the server has not said whether taking from it is a crime.
            # Carving it anyway made BotFencerBR a criminal (another bot's fresh kill): open it again in a moment, at most three times
            tries = self.facts.setdefault("open_tries", {})
            tries[corpse.serial] = tries.get(corpse.serial, 0) + 1
            if tries[corpse.serial] < 3:
                self.facts["looted"].discard(corpse.serial)
            time.sleep(1.0)
            return True
        if forbidden:
            self.note("loot", "Opening a corpse the player did not kill says 'Looting this monster corpse will be a criminal act!'; the bot left it. A new player taking from another fighter's kill would be flagged and could be attacked by guards.", key="criminalloot")
            return True
        try:
            contents = self.c.container(corpse.serial, timeout=5)
        except Exception:
            contents = []
        if any(0x203B <= (it.graphic or 0) <= 0x204D for it in contents):
            self.log(f"{corpse.name} has hair or a beard in it: a person's corpse, left alone")
            return True
        if getattr(self, "CARVE", False) and any(k in corpse.name.lower() for k in self.CARVE_KINDS) and self.c.weight < self.c.max_weight * 0.7:
            blade = self.carving_blade()
            if blade:
                # a blade on the corpse: the meat goes into the corpse, then it is looted like the rest (G13b)
                self.c.events.drain()
                self.c.use(blade.serial)
                if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is not None:
                    self.c.target(corpse.serial)
                    time.sleep(1.5)
                    self.read_journal()
                    try:
                        contents = self.c.container(corpse.serial, timeout=5) or contents
                    except Exception:
                        pass
        if not contents:
            self.note("loot", "An empty corpse still opens by itself.", key="emptycorpse")
            return True
        worth = ("gold", "pearl", "moss", "garlic", "ginseng", "mandrake", "nightshade", "ash", "silk", "potion", "scroll", "bandage", "gem", "ruby", "sapphire",
                 "emerald", "diamond", "amber", "citrine", "tourmaline", "arrow", "bolt", "feather") + (self.MATERIALS if self.LOOT_MATERIALS else ())
        # weapons and armour to sell, while there is room for them (a fighter's living: G13); carved meat for the Butcher (G13b)
        gear = getattr(self, "LOOT_GEAR", ()) if self.c.weight < self.c.max_weight * 0.7 else ()
        worth += (("amethyst", "star sapphire") if self.feature("livelihood") else ())
        worth += gear + (("raw ",) if getattr(self, "CARVE", False) and self.c.weight < self.c.max_weight * 0.7 else ())
        meat_value = 0
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
            if any(w in it.name.lower() for w in gear):
                self.facts.setdefault("gear_looted", set()).add(it.serial)
            if it.name.lower().startswith("raw "):
                meat_value += (it.amount or 1) * next((p for w, p in (("ribs", 8), ("lamb", 4), ("bird", 4), ("chicken", 3)) if w in it.name.lower()), 3)
        self.log(f"looted {corpse.name}: {[str(x) for x in contents]}")
        if meat_value:
            self.ev("carve", corpse=corpse.name, meat_value=meat_value)
        if self.c.gold - gold0 + meat_value > 0:
            # gold, and what the carved meat will fetch at the Butcher: what a kill of this kind is worth (G12's gold term)
            self.mem.record("loot", cell=cell_of(corpse.x, corpse.y), gold=self.c.gold - gold0 + meat_value, m=re.sub(r"[^a-z]", "", re.sub(r"( corpse| remains)$", "", re.sub(r"^(an?|the) ", "", corpse.name.lower()))))
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
        # a player banks the surplus before going out again and carries 50-100: bots that carried their 500 lost it at every death
        core = self.home_core()                           # the city itself, not the farmland in the town region
        purse = self.c.gold > goals.purse_limit(self, 250) and core[0] <= self.c.x < core[2] and core[1] <= self.c.y < core[3] and time.time() - self.facts.get("banked_at", 0) > 600
        purse = purse or (self.c.gold > goals.purse_limit(self, 400) and time.time() - self.facts.get("banked_at", 0) > 600)     # a good haul: walk back and bank it
        if not (rich or heavy or overloaded or purse):
            return False
        self.activity = "banking"
        if overloaded:
            done = self.visit_bank("overloaded", extra=self.HEAVY_THINGS)
            if done:
                self.facts["bank_heavy"] = False
            return True
        if purse and not (rich or heavy):
            return self.visit_bank("purse", reserve=120) or True
        return self.visit_bank("rich" if rich else "heavy") or True

    BANK_SPEECH = 10                                      # tiles from the banker's spot at which an overloaded bot says "bank" instead of walking (the banker hears 12)

    def bank_walk(self, bank):
        """The walk to the bank before the box is opened. Feature walk_fix: an overloaded character cannot walk (stamina does not come back), but the banker answers from 12 tiles and the box is
        carried by the character: say \"bank\" from here when it is close enough; else drink a Refresh potion (Red Potion) first when stamina is nearly gone."""
        if self.feature("walk_fix") and self.c.overloaded:
            if max(abs(self.c.x - bank[0]), abs(self.c.y - bank[1])) <= self.BANK_SPEECH:
                self.log(f"overloaded ({self.c.weight}/{self.c.max_weight}): banking from here, {max(abs(self.c.x - bank[0]), abs(self.c.y - bank[1]))} tiles from the banker")
                return "arrived"
            if self.c.stamina <= 2:
                red = next((i for i in self.c.backpack if i.name == "Red Potion"), None)
                if red is not None:
                    self.log("overloaded and out of stamina: a Refresh potion before the walk to the bank")
                    self.c.use(red.serial)
                    time.sleep(1.5)
        return self.goto_near(bank[0], bank[1], 4).wait(timeout=90)

    def visit_bank(self, why, withdraw=0, reserve=200, extra=()):
        banks = self.bank_xys()
        self.log(f"bank trip ({why}): gold {self.c.gold}, weight {self.c.weight}/{self.c.max_weight}")
        res = self.far_front(banks[0], "bank", 90, self.c.gold + (self.facts.get("bank_balance", 0) if withdraw else 0))      # a withdrawal is worth what is banked
        if res:
            self.far_after(res, "bank")
            return False
        res = self.bank_walk(banks[0])
        if not str(res).startswith("arrived"):
            self.facts["bank_fail"] = time.time()
            self.note("bank", f"The way to the bank failed: {res}", key="bankpath")
            return False
        self.pacing_pause("bank")                                  # a moment in front of the banker before talking (feature pacing)
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
        reserve = goals.reserve(self, reserve, why)                      # saving for a goal: the purse stays small
        gold = [i for i in self.c.backpack if "gold" in i.name.lower()]
        if gold and self.c.gold > reserve + 50:
            self.c.drop(gold[0].serial, box, self.c.gold - reserve)
            time.sleep(1.6)
        self.c.events.drain()
        self.c.say("balance")
        time.sleep(1.5)
        for line in self.read_journal():
            mb = re.search(r"balance is ([\d,]+) gold", line)     # "1,071 gold": the banker writes thousands with a comma
            if mb:
                self.facts["bank_balance"] = int(mb.group(1).replace(",", ""))
        try:
            # the banker's line is spoken aloud, and in a crowded bank the last one heard may be another player's: count the open box instead
            self.facts["bank_balance"] = sum((i.amount or 1) for i in self.c.container(box, timeout=6) if i.name.lower().startswith("gold coin"))
        except Exception:
            pass
        if withdraw and self.facts["bank_balance"] > 0:
            take = min(withdraw, self.facts["bank_balance"])
            self.c.say(f"withdraw {take}")
            time.sleep(2.5)
            self.facts["bank_balance"] -= take
        self.facts["banked_at"] = time.time()
        return True

    def shop_at(self, xy, wanted: dict, budget=None):
        """Walk to a shop, find the vendor by trying every person there ("<name> buy"), buy what `wanted` lists ({substring: target amount}). Returns what was bought."""
        res = self.far_front(xy, "shop", 90)
        if res:
            self.far_after(res, "shop")
            self.facts["shop_list_opened"] = False
            return {}
        res = self.goto_near(xy[0], xy[1], 4).wait(timeout=self.__dict__.pop("shop_walk_s", 90) if self.feature("restock_fix") else 90)
        self.log(f"to the shop at {xy}: {res}")
        if self.feature("restock_fix") and str(res).startswith(("nopath", "blocked", "timeout")):
            self.facts.setdefault("shop_nopath", {})[tuple(xy)] = time.time() + 600       # the next restock begins at another shop of the role
        self.facts["shop_had_wanted"] = False                  # did the list offer a wanted item at all (r_restock: sold out, or nothing needed)
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
        self.facts["shop_list_opened"] = len(stock) >= 2
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
                    self.facts["shop_had_wanted"] = True
                    units = 50 if name.lower().startswith("bolt of") else 1     # a bolt cuts into 50 cloth
                    owned = sum(v for k, v in have.items() if self.wants(sub, k)) + got.get(sub, 0)
                    n = min(avail, max(0, -(-(target - owned) // units)), max(0, (gold - spent) // max(price, 1)))
                    if n > 0:
                        cart += [serial, str(n)]
                        spent += n * price
                        bought[name] = n
                        got[sub] = got.get(sub, 0) + n * units
                    break
        if not cart and self.feature("restock_fix"):
            try:
                self.log(self.shop_why(xy, stock, wanted, gold, have))
            except Exception as e:
                self.log(f"shop_why: {type(e).__name__}: {e}")
        if cart:
            self.cmd("buy " + " ".join(cart), timeout=10)
            time.sleep(3)
            self.log(f"bought {bought} for {spent} gold")
        return bought

    def shop_why(self, xy, stock, wanted, budget, have):
        """Feature restock_fix: one line saying why a visit bought nothing: the wanted lines the list held with price, stock, what the budget affords and what the pack owns; else the list itself."""
        rows = []
        for line in stock[1:]:
            m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
            if not m:
                continue
            price, avail, name = int(m.group(2)), int(m.group(3)), m.group(4).strip()
            for sub, target in wanted.items():
                if self.wants(sub, name):
                    owned = sum(v for k, v in have.items() if self.wants(sub, k))
                    rows.append(f"{name} {price}gp x{avail}: budget {budget} affords {budget // max(price, 1)}, owns {owned} of {target}")
                    break
        if rows:
            return f"shop {xy}: bought nothing - " + "; ".join(rows[:4])
        names = [re.sub(r"^.*x\d+\s+", "", l.strip()) for l in stock[1:]]
        return f"shop {xy}: bought nothing - none of {list(wanted)} is listed (the list: {', '.join(names[:8])}{'...' if len(names) > 8 else ''})"

    @staticmethod
    def wants(sub, name):
        """Does a shop line's item name match a `wanted` key? "=arrow" means exactly "arrow"; any other key is a part of the name."""
        n = name.strip().lower()
        return n == sub[1:] if sub.startswith("=") else sub in n

    def vendor_list(self, vendor, kind):
        """Ask one vendor for its buy ("buy") or sell ("sell") list and return the lines, or [] when the list that came back is not this vendor's:
        Navrey's shop/selllist return the last list received, so a vendor that does not answer in time would hand back the previous vendor's list
        (a Tinker once tried to sell Neoma's goods by serial to Constance, who paid nothing)."""
        got = False
        for attempt in range(2):
            here = next((m for m in self.c.mobiles(within=12) if m.serial == vendor.serial), vendor)
            walked = here.distance > 2
            if walked:
                self.c.goto(here.x, here.y).wait(timeout=8)       # a vendor answers only within 4 tiles in this era
            self.pacing_pause("vendor")                              # a moment in front of the vendor before talking (feature pacing)
            self.c.events.drain()
            self.c.say(f"{vendor.name.split()[0]} {kind}")
            deadline = time.time() + 4
            while time.time() < deadline and not got:
                time.sleep(0.5)
                for e in self.c.events.poll():
                    if "[SHOP]" in e.text and vendor.serial.lower() in e.text.lower():
                        got = True
            if got or not walked:
                break                                     # asked from close by and no answer: asking again changes nothing
        if not got:
            return []
        lines = self.cmd("selllist" if kind == "sell" else "shop", timeout=10)
        head = next((l for l in lines if l.startswith("[SHOP]")), "")
        return lines if vendor.serial.lower() in head.lower() else []

    def sell_items(self, xy, words):
        """Walk to a buyer, find the vendor that opens a sell list, sell every pack item whose name has one of `words`. Returns gold earned (0 if it could not sell)."""
        res = self.far_front(xy, "sell", 100, sum((i.amount or 1) for i in self.c.backpack if any(w in i.name.lower() for w in words)))
        if res:
            self.far_after(res, "sell")
            return 0
        gold0 = self.c.gold
        res = self.c.goto(*xy).wait(timeout=100)
        if not self.travel(xy[0], xy[1], near=3):
            return 0
        offers = []
        # the vendors the shared memory has seen buying any of these first: asking every person at a shop cluster took two and a half minutes
        known = {v2["name"] for v2 in self.mem.state["world"]["vendors"].values()
                 if v2.get("name") and any(p > 0 and any(w in item for w in words) for item, p in v2["buys"].items())}
        people = sorted([m for m in self.c.mobiles(within=7) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")],
                        key=lambda m: (m.name not in known, m.distance))
        for v in people:
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

    @property
    def FORGE(self):                                      # the forge of the nearest smithy (Britain's is a small forge from the decoration data, not a map static)
        return self.forge_xy()

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
        res = self.far_front((fx, fy), "forge", 120)
        if res:
            self.far_after(res, "forge")
            return None
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
        if time.time() - self.facts.get("fatigued_at", 0) < 15:
            over = max(over, self.c.weight - int(self.c.max_weight * 0.85))     # "too fatigued to move": shed down to 85% (a miner wedged at 117 of them)
            self.facts["fatigued_at"] = 0
        if over <= 0:
            return False
        self.note("weight", f"Overloaded to {self.c.weight}/{self.c.max_weight}: the character stands still; the only way out is to drop things on the ground, and nothing says which weigh most.", key="overloaded_stuck")
        # a player sheds weight the cheap way first (the watcher): smelt at a forge beside him (ingots weigh far less than ore), bank from where he
        # stands when a banker is in earshot (walk_fix), and only then drop, the least valuable first (SHED_LAST: the product goes last)
        target = self.c.weight - over
        try:
            if hasattr(self, "smelt") and hasattr(self, "ore_piles") and self.ore_piles(smeltable=True) and any("forge" in (g.name or "").lower() for g in self.ground_items(3)):
                w0 = self.c.weight
                self.smelt()
                self.dlog("ev", ev="shed", how="smelt", item="ore", qty=w0 - self.c.weight)
                if self.c.weight <= target:
                    return True
        except Exception as e:
            self.log(f"shed: smelt failed ({type(e).__name__})")
        try:
            bx, by = self.bank_xys()[0]
            tried = self.facts.get("shed_bank_at", 0)
            if max(abs(self.c.x - bx), abs(self.c.y - by)) <= 10 and self.feature("walk_fix") and time.time() - tried > 120:
                self.facts["shed_bank_at"] = time.time()           # once per 2 min: if banking has not helped by then, drop (the watcher: 105 a minute)
                self.facts["bank_heavy"] = True                # r_bank (overloaded) banks from here; nothing is thrown away
                self.dlog("ev", ev="shed", how="bank", item="bank box", qty=self.c.weight)
                return False
            if time.time() - tried < 120:
                return False                                   # the bank trip is under way: give it its 2 minutes
        except Exception:
            pass
        last = tuple(getattr(self, "SHED_LAST", ()))
        def rank(i):
            n = i.name.lower()
            return any(w in n for w in last), next((k for k, w in enumerate(self.HEAVY_THINGS) if w in n), 99), -(i.amount or 1)
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
            if not still:
                self.dlog("ev", ev="shed", how="drop", item=it.name, qty=amt)
            if self.c.weight <= min(self.c.max_weight - 5, target):
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
        elif not mx or self.c.stamina >= 0.5 * mx:
            self.facts["catching_breath"] = False
        return bool(self.facts.get("catching_breath"))

    REST_BELOW = 85                          # rest when health is under this percentage (fighters fight on lower)

    def r_rest(self):
        """Hurt or out of breath, and nothing around: stand still (a mage meditates, handled by the brain)."""
        if self.mobs(10) or (self.hp_pct() >= self.REST_BELOW and not self.tired()):
            return False
        if self.tired() and time.time() - self.facts.get("refreshed_at", 0) > 60:
            red = next((i for i in self.c.backpack if i.name == "Red Potion"), None)     # Refresh: red, as in the era
            if red:
                self.facts["refreshed_at"] = time.time()
                self.c.use(red.serial)
                self.log(f"drank a Refresh potion at stamina {self.c.stamina}")
                self.ev("consumable_used", item="red potion", hp=self.hp_pct())
                time.sleep(1.5)
                return True
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
        if typ == "ev":
            guard = getattr(self, "guard_seen", None)
            if guard:
                guard("ev", kw.get("ev", ""))

    def request_unstick(self, why, every=180):
        """Ask for a staff move (what a player does with Help > I'm stuck): a line in wedged.jsonl for unstick.py, at most every `every` seconds, and hold still (r_wedged)."""
        self.facts["wedged_hold"] = {"x": self.c.x, "y": self.c.y, "since": self.facts.get("wedged_hold", {}).get("since", time.time())}
        if time.time() - self.facts.get("unstick_asked", 0) < every:
            return False
        self.facts["unstick_asked"] = time.time()
        with open(os.path.join(FARM, "wedged.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"bot": self.name, "x": self.c.x, "y": self.c.y, "t": time.time(), "why": why}) + "\n")
        self.note("stuck", f"A {self.pname} cannot get out of {self.c.x},{self.c.y} ({why}). A player would use Help > I'm stuck.", key=f"unstick:{self.c.x},{self.c.y}")
        self.log(f"asked for a staff move at {self.c.x},{self.c.y}: {why}")
        return True

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

    CRITTERS = ("towhee", "sparrow", "swallow", "nightingale", "plover", "thrush", "tern", "warbler", "finch", "starling", "bird", "magpie", "crow",
                "raven", "pigeon", "gull", "cat", "dog", "squirrel", "rabbit", "jackrabbit", "toad", "frog", "lizard", "mouse")
    CRITTER_SKILL = 35.0
    BIRDS = ("towhee", "sparrow", "swallow", "nightingale", "plover", "thrush", "tern", "warbler", "finch", "starling", "bird", "magpie", "crow",
             "raven", "pigeon", "gull")

    def critter_skip(self, m):
        """A small critter (a bird, a cat, a squirrel...) is no prey from CRITTER_SKILL on, unless it is on top of the bot (patch_critters.py)."""
        if (m.distance or 0) <= 1:
            return False
        n = (m.name or "").lower()
        caster = (getattr(self, "pname", "") or "") in ("PureMage", "Warlock", "Sorcerer")
        kinds = self.CRITTERS if caster else self.BIRDS        # a fighter's weapon skill gains on any swing: only birds (they fly off) are not worth the chase
        if not any(re.search(r"\b" + w + r"\b", n) for w in kinds) or any(w in n for w in ("giant", "dire", "hell", "plague")):
            return False
        try:
            skill = self.working_skill() if hasattr(self, "working_skill") else 0
        except Exception:
            skill = 0
        return skill >= self.CRITTER_SKILL

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
        self.sprint_check()
        if self.c.ghost and not self.facts.get("ghost_said"):
            self.facts["ghost_said"] = self.chatter("ghost", cooldown=0)
        elif not self.c.ghost:
            self.facts["ghost_said"] = False
            if self.in_britain() and random.random() < 0.05 and any(m.name.startswith("Bot") and m.distance <= 3 for m in self.c.mobiles(within=3)):
                self.chatter("greet", cooldown=900)
        self.track_episode()
        if not self.c.ghost:
            deathsrc.snap(self)                                      # the hostiles in view, for the next death
        if time.time() - self.last_presence > 60 and not self.c.ghost:
            self.last_presence = time.time()
            self.mem.record("presence", cell=cell_of(self.c.x, self.c.y), rule=self.last_rule)
        if not self.c.ghost:
            self.last_gold = self.c.gold
            self.facts["gold_alive"] = self.c.gold                 # persisted: a brain restarted on a ghost still knows what the corpse holds
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
                if (self.c.weight > self.c.max_weight or time.time() - self.facts.get("fatigued_at", 0) < 15) and not self.c.ghost and self.drop_excess():
                    time.sleep(0.5)                # never a tick without a pause (a refused drop once spun a brain at 75% of a core)
                    continue
                acted = None
                t_rules = time.time()
                for name in self.far_rules():                  # the brain's RULES with r_far (a far walk under way) before the economy rules
                    if self.stall_skip(name):
                        continue                       # the stall sense backed it off (stall.py)
                    if self.recovery_skip(name):
                        continue                       # materializing: this rule would end it (recovery.py)
                    if self.guard_off(name):
                        continue                       # the loop guard backed this rule off (loopguard.py)
                    self.current_rule = name
                    if getattr(self, name)():
                        acted = name
                        break
                self.guard_spin(acted, time.time() - t_rules)
                self.guard_client()                            # the server's refusals in the client's own log (loopguard.py)
                self.recovery_tick()
                if acted != self.last_rule:
                    self.log(f"rule -> {acted}")
                    self.last_rule = acted
                self.after_tick(acted)
                if acted is None:
                    self.note("stuck", "No rule handled the situation.", key=f"stuck:{self.tick_no // 100}")
                    self.activity = "idle"
                    time.sleep(1)
            except Exception as e:
                self.log(f"EXCEPTION {type(e).__name__}: {e}\n{traceback.format_exc()[-400:]}")
                self.note("bot", f"{type(e).__name__}: {e}", key=f"exc:{type(e).__name__}:{str(e)[:60]}")
                time.sleep(2)
        self.status(force=True)
