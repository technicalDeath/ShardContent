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
import items  # noqa: E402  (the shared item table)
from basics import BasicsMixin  # noqa: E402  (the shared basics: potions, threats, fleeing, selling)
import basics  # noqa: E402  (walkroute_mod for walk_again)
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
from runes import RuneMixin  # noqa: E402  (runes, Mark and Recall; feature runes)
from evade import EvadeMixin  # noqa: E402  (r_evade only for real threats; needs fightmodes.json)
from gotoroute import GotoRouteMixin  # noqa: E402  (goto of over 120 tiles as routed legs; feature goto_routed)
from party import PartyMixin  # noqa: E402  (parties; feature party; needs Navrey build Lean5+)
from buddy import BuddyMixin  # noqa: E402  (buddy pairs: rendezvous, staying together, bandaging; feature buddy + party)
from pacing import PacingMixin  # noqa: E402  (walk in town, pause before talking, a break at the bank; features pacing, pacing_walk)
from housegoal import HouseGoalMixin  # noqa: E402  (the A1 house goal; feature house_goal, off in the farm world)
from market import MarketMixin  # noqa: E402  (the bots' market: quantity offers / wants, secure trades; feature trade)
from uo import Event  # noqa: E402
from memory import MEMDIR, SharedMemory, cell_center, cell_of  # noqa: E402
from places import Places  # noqa: E402
from loopguard import LoopGuard  # noqa: E402
from recovery import RecoveryMixin  # noqa: E402
from stall import StallMixin  # noqa: E402
from progress import ProgressMixin  # noqa: E402  (is what it does moving its ambition? loop breakers; feature progress_check)
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
GATHER_DEATHS = 3.0             # decayed deaths of any bot in a 3x3-cell neighbourhood that close it to gatherers and crafters (memory.deaths_near)
BIRTH_TOWN = "Britain"                  # every farm bot is made in Britain (startInBritainOnly) (patch_home_town)
STEP = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0), "ne": (1, -1), "nw": (-1, -1), "se": (1, 1), "sw": (-1, 1)}     # the client's walk directions
ROUTE_DEATH_DAYS = 14   # a long walk to a new home is judged on this many days of deaths: the danger map forgets in 24 h (half-life 3 h), and the pocket at
                        # 1990-2110 x 960-1050 (slimes, rats, mongbats boxing a walker in) had 12 deaths on 10-21 and 3 by 10-30 noon, yet looked safe at 16:34
_ROUTE_DEATHS = {"at": 0.0, "cells": {}}


def route_deaths():
    """{cell: [skill or None, ...]} of the bots' deaths in the last ROUTE_DEATH_DAYS, from both memory folders' world.jsonl; read every 30 min."""
    now = time.time()
    if now - _ROUTE_DEATHS["at"] < 1800:
        return _ROUTE_DEATHS["cells"]
    import memory
    cells = {}
    for root in (memory.MEMDIR, memory.MEMDIR + "-newbie"):
        try:
            with open(os.path.join(root, "world.jsonl"), encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if '"death"' not in line:
                        continue
                    try:
                        e = json.loads(line)
                    except ValueError:
                        continue
                    if e.get("k") == "death" and now - e.get("t", 0) <= ROUTE_DEATH_DAYS * 86400 and e.get("cell") and not str(e.get("bot", "")).startswith("Sim"):
                        cells.setdefault(e["cell"], []).append(e.get("skill"))
        except OSError:
            continue
    _ROUTE_DEATHS.update(at=now, cells=cells)
    return cells
HOME_DEATHS = 2                         # this many of its own deaths ...
HOME_WINDOW = 7200                      # ... in this many seconds ...
HOME_REACH = 300                        # ... within this many tiles of the home's centre: the home is unsafe for this bot
UNSAFE_FOR = 6 * 3600                   # an unsafe home is not taken again for this long
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




HOME_BASICS = ("bank", "healer")      # what every home town must hold (a bank for the gold, a healer for the ghost)
_ROLES = {}


def town_roles(name):
    """The gazetteer roles of the places in a region (cached)."""
    if not _ROLES:
        try:
            for p in gz.get().places:
                reg = p.get("region")
                if reg:
                    _ROLES.setdefault(reg, set()).update(p.get("roles") or [])
        except Exception:
            return set()
    return _ROLES.get(name, set())


def town_holds(name, needs):
    return all(r in town_roles(name) for r in needs)


def town_with(needs, x, y):
    """The nearest surface town (gazetteer region) holding a place for every role in `needs`, or None."""
    try:
        towns = [t for t in gz.towns() if t["centre"][0] < 5120]
        have = {}
        for p in gz.get().places:
            reg = p.get("region")
            if reg:
                have.setdefault(reg, set()).update(p.get("roles") or [])
        ok = [t for t in towns if all(r in have.get(t["name"], ()) for r in needs)]
        return min(ok, key=lambda t: max(abs(t["centre"][0] - x), abs(t["centre"][1] - y))) if ok else None
    except Exception:
        return None

_TELE = None


def teleporter_tiles():
    """[(x, y)]: the surface tiles a step onto sends a walker elsewhere, from the generated gazetteer's transitions (teleporters and their kin)."""
    global _TELE
    if _TELE is None:
        out = []
        try:
            for t in gz.get().trans or []:
                src = t.get("src") or []
                if len(src) >= 2 and (t.get("src_side") or "surface") == "surface" and int(src[0]) < 5120:
                    out.append((int(src[0]), int(src[1])))
        except Exception:
            out = []
        _TELE = sorted(set(out))
    return _TELE

class BotBase(MarketMixin, GroundRateMixin, BetweenWorldsMixin, PlannerMixin, AmbitionMixin, ProgressMixin, StallMixin, RecoveryMixin, HouseGoalMixin, PacingMixin, BuddyMixin, PartyMixin, TeleMixin, RuneMixin, FarMixin, EvadeMixin, GotoRouteMixin, Places, LoopGuard, BasicsMixin):
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
        if self.mode == "newbie" and self.feature("one_market"):
            self.mem.share_market(self.mem.news)          # one economy: a newbie trades with veterans, and learns apart (memory.share_market)
        # the area danger map (feature danger_map): off while a trip or a far walk runs, which have their own route penalty
        self.mem.area = area_danger.AreaDanger(
            self.mem, skill_fn=lambda: area_danger.combat_skill(getattr(self, "skill_values", {})),
            enabled=lambda: self.feature("danger_map") and getattr(self, "current_rule", "") not in ("r_trip", "r_far"),
            on_avoid=lambda cell, why: self.ev("area_avoid", area=cell, why=why),
            worn_fn=lambda: self.worn_profile() if self.feature("gather_armor") else None)    # an armoured gatherer's own armour in the risk (wear.py)
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
        """A trade box's items, named without the hue tail (basics.box_contents): the client lists a hued piece as 'plate helm (hue 0x0972
        "Metals #17")', so the settle counts found 0 of the bronze plate helm BotSmithAR had put in and the first coloured trade failed (2026-11-02 18:20)."""
        try:
            return self.box_contents(box, timeout=6)
        except Exception:
            return []

    def do_deal(self, d):
        """One tick of a market deal, as seller or buyer: meet at the bank spot, the seller drops the agreed quantity on the buyer (the trade window opens), the buyer puts the
        gold in, both accept once the other box holds what was agreed; the outcome is checked by counts (market.py). With the feature trade_tree the deal runs as a
        py_trees behaviour tree (trade_tree.py, patch_trade_tree): resumable, fails once, merges gold and goods piles, fetches the price from the bank, sees a partner give up."""
        if self.feature("trade_tree"):
            import trade_tree
            return trade_tree.tick(self, d)
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
            mw = re.search(r"Your (.+?) is badly worn", t)
            if mw:
                self.facts.setdefault("weapon_worn", {})[mw.group(1).strip().lower()] = time.time()      # the shard's wear notice (a quarter of the durability left)
            elif re.search(r"\byour .+ (broke|breaks|is destroyed|has been destroyed|was destroyed)\b", t, re.I):
                self.facts["weapon_broke_at"] = time.time()
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
            if self.mem.deaths_near(cell) >= GATHER_DEATHS:
                return True                               # several deaths of any bot around it lately, whatever the fighters kill there (memory.deaths_near)
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
        """Within r of a place this bot died in the last DEATH_HALF_LIFE (memory.py: 4 h, "a place that killed bots stays suspect for hours"). A death spot was
        kept for good before (the Watcher, 2026-10-29): archers carried 6-12 of them, 80-tile boxes that turned away 0.14 of their 0.17 prey a look; ground that
        stays deadly is closed by the measured losing-spawner rule instead (hunter.in_losing_range). A spot with no recorded time is an old one: it lapses."""
        import memory
        times = self.facts.get("death_spot_t") or {}
        now_ = time.time()
        return any(abs(x - dx) < r and abs(y - dy) < r for dx, dy in self.death_spots if now_ - float(times.get(f"{dx},{dy}", 0)) < memory.DEATH_HALF_LIFE)

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
            walk = bot.goto_avoiding("goto", orig, x, y, z)
            first_wait = walk.wait

            def wait(timeout=300.0, poll=0.1):
                end = time.time() + timeout
                if getattr(bot, "packy_leading", None) and bot.packy_leading(x, y):
                    # a pack horse along: at its pace, stopping for it (packy.py, feature packy_lead)
                    res = bot.packy_lead(lambda t: bot.tele_wait(first_wait, t, poll),
                                         lambda: (lambda w: (lambda t: bot.tele_wait(w.wait, t, poll)))(bot.goto_avoiding("goto", orig, x, y, z)), timeout)
                else:
                    res = bot.tele_wait(first_wait, timeout, poll)          # a jump of the position is a teleport: cancel the walk at once
                if str(res).startswith("nopath") and bot.step_out():
                    left = max(end - time.time(), 0.0) if bot.feature("walk_fix") else timeout       # (walk_fix: the second walk gets what is left of the caller's timeout)
                    if left >= 1.0:
                        res = bot.tele_wait(orig(x, y, z).wait, left, poll)
                        bot.log(f"after a step out, the walk to {x},{y}: {res}")
                if bot.feature("walk_again"):
                    res = bot.walk_again(res, x, y, z, near, orig, end, poll)
                return bot.far_arrival(res, x, y, near)

            walk.wait = wait
            return walk

        self.c.goto = goto
        orig_exact = self.c.gotoexact

        def gotoexact(x, y, z=None):
            stub = bot.tele_cross(x, y)
            if stub is not None:
                return stub
            walk = bot.goto_avoiding("gotoexact", orig_exact, x, y, z)
            first_wait = walk.wait

            def wait(timeout=300.0, poll=0.1):
                return bot.tele_wait(first_wait, timeout, poll)

            walk.wait = wait
            return walk

        self.c.gotoexact = gotoexact

    TELE_AVOID_NEAR = 40       # teleporter tiles within this many tiles of the bot or the walk's end go on the walk's avoid list
    TELE_AVOID_AT = 2          # ... unless the walk ends this close to one: then it is the teleporter the walk is for

    def goto_avoiding(self, kind, orig, x, y, z=None):
        """The client walk to (x, y), told to keep off the known teleporter tiles near the way (Navrey's goto avoid:<x>,<y>,<r>): the walk map knows no
        teleporters, and a leg over one sends the walker elsewhere (BotFisherAR to Buccaneer's Den, 2026-10-31). A walk that ends at a teleporter is
        not stopped from using it."""
        try:
            tiles = teleporter_tiles()
        except Exception:
            tiles = []
        av = []
        for tx, ty in tiles:
            if max(abs(tx - x), abs(ty - y)) <= self.TELE_AVOID_AT:
                return orig(x, y, z)                       # the walk is for this teleporter
            if min(max(abs(tx - x), abs(ty - y)), max(abs(tx - self.c.x), abs(ty - self.c.y))) <= self.TELE_AVOID_NEAR:
                av.append((tx, ty))
        send = getattr(getattr(self.c, "commands", None), "send", None)
        if not av or send is None:
            return orig(x, y, z)
        from uo.client import Walk
        send(f"{kind} {x} {y}" + ("" if z is None else f" {z}") + "".join(f" avoid:{tx},{ty},1" for tx, ty in av[:12]))
        return Walk(self.c, (x, y))

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

    WALK_AGAIN_LEG = 25        # seconds one leg of the walk grid's route may take (far.LEG_TIMEOUT)
    WALK_AGAIN_MIN = 10        # tiles: a nearer stop still trades (a vendor's buy and sell replies count within 10, IncomingVendorPackets; a banker hears 12)

    def walk_again(self, res, x, y, z, near, orig, end, poll=0.1):
        """Feature walk_again: a walk that stopped at the closest reachable tile more than `near` short of (x, y) is walked again once from where it
        stopped, then along the walk grid's route (walkroute), as a player who finds the way blocked looks again and then takes the street. The client
        plans only through the doors it has seen, and walks a partial route to its end without planning again: BotTinkBR's walks from the weaponsmith's
        walled yard (1427,1652, z 10) to the bank at 1425,1690 stopped at 1430,1664, the yard's way out being the doors west of it, and the bank trip did
        nothing (2026-11-05); the walk grid's route leaves by 1432,1666 and 1421,1671 and goes in by the east door at 1438,1692."""
        def short():
            return max(abs(self.c.x - x), abs(self.c.y - y))

        if not (str(res).startswith("arrived") and short() > max(near, self.WALK_AGAIN_MIN)) or end - time.time() < 3.0:
            return res
        stop, how = (self.c.x, self.c.y), "again"
        res = str(self.tele_wait(self.goto_avoiding("goto", orig, x, y, z).wait, end - time.time(), poll))
        if not (res.startswith("arrived") and short() <= near) and res != "teleported" and end - time.time() >= 3.0:
            how = "route"
            try:
                r = basics.walkroute_mod().get().plan((self.c.x, self.c.y), (x, y))
            except Exception:
                r = None
            for wp in (r or {}).get("waypoints", [])[1:]:
                left = end - time.time()
                if left < 1.0:
                    break
                res = str(self.tele_wait(self.goto_avoiding("goto", orig, int(wp[0]), int(wp[1]), None).wait, min(self.WALK_AGAIN_LEG, left), poll))
                if res == "teleported" or res.startswith(("stopped", "failed", "timeout")):
                    break
            if r is None:
                how = "no route"
        self.ev("walk_again", to=[x, y], stop=list(stop), how=how, result=res[:40], short=short())
        if short() <= near and res.startswith("arrived"):
            self.log(f"the walk to {x},{y} stopped {max(abs(stop[0] - x), abs(stop[1] - y))} tiles short at {stop[0]},{stop[1]}; walked {how}: arrived")
        return res

    def goto_near(self, x, y, near=2):
        """self.c.goto with the tolerance for \"arrived\": a client whose goto takes no near (a fake, an unwrapped client) gets the plain call."""
        try:
            return self.c.goto(x, y, None, near=near)
        except TypeError:
            return self.c.goto(x, y)

    def tele_entries_near(self, x, y, r=2):
        """{(x, y)} of teleporter entries within r tiles (the gazetteer's transitions, both ways)."""
        try:
            import gazetteer
            return {(int(t["src"][0]), int(t["src"][1])) for t in gazetteer.get().trans if abs(int(t["src"][0]) - x) <= r and abs(int(t["src"][1]) - y) <= r}
        except Exception:
            return set()

    def step_out(self):
        """One step in the first direction that moves the character; at most once every 20 seconds."""
        if time.time() - self.facts.get("stepped_out_at", 0) < 20:
            return False
        self.facts["stepped_out_at"] = time.time()
        x0, y0 = self.c.x, self.c.y
        started = time.time()
        # a living mobile's tile takes a player only at full stamina (Mobile.CheckShove: Stam == StamMax, and it costs 10): short of that, a step onto
        # one never moves. Two miners spent 20-45 s here boxed in by a slime, rats and a mongbat, lost their health, and their tiles went into memory
        # as stuck ground for 6 h (2026-10-30). Those steps are skipped, and a box of bodies is no stuck tile.
        try:
            mx = int((self.c.state or {}).get("maxStam") or 0)
            full = mx <= 0 or int(self.c.stamina or 0) >= mx or bool(self.c.ghost)       # a ghost passes any mobile (Mobile.CheckShove: not Alive)
            bodies = {(m.x, m.y) for m in self.c.mobiles(within=1) if not getattr(m, "ghost", False)}
        except Exception:
            full, bodies = True, set()
        dirs = [d for d in ("s", "e", "w", "n", "se", "sw", "ne", "nw") if full or (x0 + STEP[d][0], y0 + STEP[d][1]) not in bodies]
        doors = self.tele_entries_near(x0, y0)
        if doors:
            # never onto a teleporter's entry: a step out from a dungeon door's arrival tile (Despise's 1296,1080, itself an entry, teleporters.json) went
            # south onto 1296,1081 and back into the dungeon, four jumps in 40 s and a trip ended "stranded" (BotWarAdvR, 2026-11-04 14:32). The steps
            # away from the entries come first
            dirs = sorted([d for d in dirs if (x0 + STEP[d][0], y0 + STEP[d][1]) not in doors],
                          key=lambda d: -min(max(abs(x0 + STEP[d][0] - ex), abs(y0 + STEP[d][1] - ey)) for ex, ey in doors))
        if not dirs:
            self.log(f"no path from {x0},{y0}: boxed in by {len(bodies)} mobiles at stamina {self.c.stamina}/{mx} (a step onto one needs full stamina)")
            self.facts["boxed_at"] = time.time()          # no step open at all: r_flee fights at once, as after "no step in any direction" (BotFencerBR, boxed
                                                          # in by 8 at 2030,996, fought only from 9 hit points after three more flights, 2026-11-03 01:20)
            return False
        for d in dirs:
            if time.time() - started > 45 or (bodies and self.hp_pct() < self.flee_below()):
                break                                  # losing health with bodies around: r_flee and the fight-back get the tick
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
        self.log(f"no path from {x0},{y0}, and no step in any direction moved the character" + (f" ({len(bodies)} mobiles beside it)" if bodies else ""))
        if bodies:
            self.facts["boxed_at"] = time.time()          # every direction tried and none moved it, with bodies about: r_flee fights at once (fight_committed)
        if not bodies and not self.c.ghost:
            # overloaded: "You are too fatigued to move" is seen only when the journal is read (recovery.py sets fatigued_at), and a far walk's three legs of
            # step-outs read none: BotMinerAR stood 4 minutes at 1177,1491 with a load of ore (2026-11-01 18:42-18:46). Shed here, then the walk goes on
            try:
                self.read_journal()
            except Exception:
                pass
            if (self.c.weight > self.c.max_weight or time.time() - self.facts.get("fatigued_at", 0) < 15) and self.drop_excess():
                self.log(f"no path from {x0},{y0}: overloaded, weight shed to {self.c.weight}/{self.c.max_weight}")
                return True
        if bodies:
            return False                                  # the bodies may be what held it: the ground is not to blame
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
            self.harvest_peace()
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

    def harvest_peace(self):
        """Out of war mode before a harvest: the shard's gather repeat stops in war mode (HarvestRepeatService.CheckCancel, StopReason.WarMode), so a
        fighter that chopped in war mode got one swing a visit, 10 logs or none (all five archers, Lumberjacking 45, 2026-11-01). A real player
        leaves war mode to gather; the fight rules put it back on when a fight starts."""
        if self.c.war_mode:
            self.c.war(False)
            time.sleep(0.5)

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
            self.progress_flow(kind, g - prev, rule or acted)        # the progress check's buy and sale ledger (progress.py)
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
            import skillplan
            skillplan.tick(self)                              # the profession's 700-point plan: skill locks (skillplan.py, feature skill_plan)
        except Exception as e:
            self.log(f"skill plan: {type(e).__name__}: {e}")
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
        try:
            self.progress_tick(acted)                         # is it moving its ambition? stalled, losing or looping: rethink (progress.py)
        except Exception as e:
            self.log(f"progress: {type(e).__name__}: {e}")
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

    def travel(self, x, y, near=2, tries=8, per=60):
        """Walk to (x, y) in hops: a destination beyond the client's loaded map is reached in several goto calls."""
        if self.far_front((x, y), "travel", per):                  # far: a routed walk in legs, resumed by r_far; the hops below are for near places
            return False
        for _ in range(tries):
            if max(abs(self.c.x - x), abs(self.c.y - y)) <= near:
                return True
            before = (self.c.x, self.c.y)
            res = self.goto_near(x, y, near).wait(timeout=per)
            if self.c.ghost:
                return False
            th = self.threats(5)
            if th:
                self.ev("travel_abort", x=x, y=y, by=th[0].name)
                return False                                           # a threat, not a town cat: mobs(5) gave up on any grey animal in Britain's streets, and half the
                                                                       # meat sales never asked the Butcher (MaceCR 14:33, 2026-10-29: at his door, then off to the Tailor)
            if (self.c.x, self.c.y) == before and str(res).startswith(("nopath", "blocked")):
                return False
        return max(abs(self.c.x - x), abs(self.c.y - y)) <= near

    def beat(self):
        """A heartbeat inside a long blocking step (a shop walk, an errand): the status file's time is what the supervisor reads, and a brain that writes none for 240 s is
        killed (BotMaceBR twice, 2026-10-21: one resupply errand of four minutes). Rate-limited to one write a 15 s."""
        if time.time() - self.__dict__.get("_beat_at", 0) < 15:
            return
        self.__dict__["_beat_at"] = time.time()
        try:
            self.status(force=True)
        except Exception:
            pass

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
            "bank": self.facts.get("bank_balance", 0), "net_worth": self.net_worth(), "house_worth": self.house_worth(),
            "region": self.region_name(), "home": (self.home() or {}).get("name"),
            **getattr(self, "status_extra", {}), **self.ambition_status(),
        }
        self.write_status_file(s)
        with open(self.totals_path, "w", encoding="utf-8") as f:
            json.dump({"kills": s["kills"], "deaths": s["deaths"], "gains": gains, "uptime": s["uptime"]}, f)
        save_bank(self.dir, self.facts.get("bank_balance", 0))
        self.save_facts()

    # facts a new brain takes over from the last one (a restart used to drop the held ground, the camp and which gear was looted)
    PERSIST = ("colour_buy", "death_spot_t", "shop_sold", "shop_fail", "ground", "anchor", "anchors_left", "crowded", "pushed_at", "spots_reached", "gear_looted", "meat_sold_at", "gear_sold_at", "sold_at",
               "sell_skip_until", "soldout_until", "stocked_at", "bank_balance", "banked_at", "fletch_wait", "wood_wait", "shop_at", "chop_fail",
               "emptied", "home", "camp_step", "home_region", "birth_town", "unsafe_homes", "rehome_walk", "field", "fields_rested", "roam_rested", "unsafe_count", "stand_fails", "owned_serials", "lost_pets", "fists", "corpse", "gold_alive", "far", "skill_gap", "killer", "killer_until", "mat_until", "mat_from", "walk_until", "goal", "goals_done", "inc_log", "death_log", "res_at", "res_from", "died_at", "stall_off", "stall_earn_until", "stall_gather_until", "persona", "worth_ring", "regions_seen", "dungeon_seen", "milestones", "trips_done", "act_rates", "plan_v", "plan_explored_at", "bw", "walk_rate", "runes", "rune_blanks", "rune_stay", "rune_buy_at", "deals", "deals_over", "task", "core_goal", "core_bans", "rung", "rung_kills", "ride", "ride_try_at", "arrow_use", "tamer_arms_at", "shield_at", "kit_short_until", "ammo_bad_shop")
    PERSIST_SETS = ("gear_looted", "emptied")

    # the decision core (task_core.py, feature task_core): the reflexes stay first and unchanged; a brain class with the core (HunterBot) replaces every rule
    # below them by core_tick() while core_active() says so. BotBase itself has no core.
    REFLEXES = ("r_dead", "r_corpse", "r_gear", "r_cure", "r_refresh", "r_dungeon_out", "r_flee", "r_avoid", "r_sewer_out", "r_heal")      # r_refresh: the shared Refresh rule (basics.py); r_dungeon_out: a dungeon hunt's way out of a pack (first_trip.py)

    # rules below the reflexes that still run under the decision core: each has its own limits (r_music every 22 s at 60%+ health, r_fletch under 200
    # arrows, r_wood under 120 arrows and every so often, r_shield once a half-hour); under the core they never ran, so the bards never played and the
    # archers never fletched (no event in 4 hours, 2026-11-01)
    CORE_SKILL_RULES = ("r_music", "r_instrument", "r_fletch", "r_wood", "r_shield")      # (r_instrument: a bard's worn-out instrument replaced; both bards had none, 2026-11-01)

    def core_lets(self, name):
        """A rule below the reflexes that still runs under the decision core: first_trip's trip_core_lets (the ladder's trips), else none."""
        if name in self.CORE_SKILL_RULES and hasattr(self, name):
            return True                                   # skill rules with their own limits: the core had suppressed them (no music, fletching or shield, 2026-11-01)
        f = getattr(self, "trip_core_lets", None)
        try:
            return bool(f and f(name))
        except Exception:
            return False

    def core_active(self):
        return False

    def core_tick(self):
        return None

    def save_facts(self):
        out = {}
        for k in self.PERSIST:
            if k in self.facts:
                v = self.facts[k]
                cap = (getattr(self, "PERSIST_CAPS", None) or {}).get(k, 20)
                out[k] = sorted(v) if isinstance(v, set) else v[-cap:] if isinstance(v, list) else v     # the brains read only the newest (a brain may keep more of a list)
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
            self.facts.setdefault("death_spot_t", {})[f"{dx_},{dy_}"] = time.time()
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
            # deathsrc's sure source first: BotTailorBR was "killed by a great hart" 8 tiles off while the damage line named a wraith beside it (2026-11-01 19:06),
            # so it learned to avoid nothing
            killer = src["label"] if src.get("sure") and src.get("key") else (threats[0][1] if threats else src["label"])
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
            if self.ghost_out():                                    # in a dungeon: out by the stairs and the exit first (tele.ghost_out)
                return True
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
        x, y = info["xy"]
        try:
            import task_core
            ref = task_core.corpse_refusal(self, x, y) if self.core_active() else None
        except Exception:
            ref = None
        if ref:
            self.ev("corpse_run_skipped" if ref[0] == "provisioned" else "corpse_run_refused", why=ref[0], dist=ref[1], killer=ref[2], xy=[x, y])
            self.log(f"not going back to the corpse at {x},{y}: {ref[0]} ({ref[1]} tiles from home, killer {ref[2] or '?'})")
            self.facts.pop("corpse", None)
            return False
        info["tries"] += 1
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
        if got and hasattr(self, "bw_looted") and self.facts.get("bw"):
            self.bw_looted("item by item")                                 # the Between Worlds record: the corpse was taken (bw.py)
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
        if hasattr(self, "sewer_flee") and self.sewer_flee():                            # in the sewers: out first, potions only if there is no way out (feature sewer_stay)
            return True
        if self.cure_due() and self.potion("cure") is not None:
            return False                                  # r_cure first: a Heal potion is refused while poisoned (basics.py)
        if self.drink_heal("low health"):                 # the shared rule: never while poisoned, one every 10 s (BaseHealPotion.Delay)
            self.log(f"drank a Heal potion at low health (hp {self.c.hp})")
            self.note("combat", "At low health the only way to tell the Heal potion is by its color (yellow); nothing in the pack says so.", key="potioncolor")
            time.sleep(1.5)
            return True
        adjacent = [m for m in threats if (getattr(m, "distance", 9) or 9) <= 2]
        if self.skill_values.get("Healing", 0) >= 30 and not adjacent and self.bandage_self():
            return True                                   # (not with an attacker in reach: each hit makes a bandage slip, Bandage.cs. BotFenceAdvR bandaged four
                                                          # times beside a ratman pack, every one slipping, 36 to 1 hit points in 52 s, and died, 2026-11-02 04:49)
        threat = threats[0] if threats else None
        if threat and self.fight_committed(threat):
            return self.fight_back(threat)                # boxed in a moment ago: keep swinging, no new flight (fight_committed)
        if threat and self.prey_beside(threats, threat):
            # the one attacker beside it is prey by the bot's own assessment and costs less to kill than the hit points left: kill it, as a player
            # does a snake. Fleeing from it while it hits and re-poisons ruins every bandage and Cure: BotFairSwordNR fled 90 s from a snake, a giant
            # rat and a slime (all "prey"), drank 11 Cure potions, slipped 5 bandages and died with war mode off (2026-11-02 22:53-22:54)
            self.log(f"{threat.name} beside me is prey ({self.__dict__.get('_prey_taken', '?')} to kill it, hp {self.c.hp}): fighting it")
            self.facts["fight_until"] = time.time() + self.FLEE_STUCK_S
            return self.fight_back(threat)
        if threat and (getattr(threat, "distance", 9) or 9) <= 2 and time.time() - float(self.facts.get("boxed_at", 0) or 0) < self.FLEE_STUCK_S:
            # the step-out tried every direction and none moved the character, an attacker beside it: no flight can work, so the fight starts now,
            # not after three more flights. BotSwordBR, stuck on 1587,1867 with a giant spider re-poisoning it (10 Cure potions in 150 s), fought
            # only from 11 hit points and died 9 s later (2026-11-02 22:26-22:27)
            self.log(f"boxed in beside {threat.name}: fighting back at hp {self.c.hp}")
            self.facts["fight_until"] = time.time() + self.FLEE_STUCK_S
            self.facts.pop("boxed_at", None)
            return self.fight_back(threat)
        if threat and self.flee_stuck(threat):
            # three flights in FLEE_STUCK_S that left it on the same tile, an attacker beside it: boxed in, so it fights. A flight that failed
            # without "trapped" (a short walk, no step open) ran on until death: BotTamerAR stood on 1479,1356 for 70 s "fleeing" from a mongbat and
            # Zilge with 5 mobiles beside it (2026-11-02 14:56-14:57), as it had on 1432,1364 at 09:53
            self.log(f"fleeing from {threat.name} has not moved me in {self.FLEE_STUCK_S} s: fighting back at hp {self.c.hp}")
            self.facts["fight_until"] = time.time() + self.FLEE_STUCK_S
            return self.fight_back(threat)
        if threat:
            self.log(f"fleeing from {threat.name} at hp {self.c.hp}")
            self.chatter("warn", cooldown=600, m=threat.name, where=self.where())
        self.call_guards(threat)
        if self.flee_from(threat, first=self.flee_point(threat)) == "trapped" and threat is not None:
            return self.fight_back(threat)                # no way out (basics.py): fight it
        return True

    def on_flee(self):
        pass

    FLEE_STUCK_N = 3          # flights from the same tile ...
    FLEE_STUCK_S = 20         # ... within this many seconds, an attacker within 2 tiles: boxed in (r_flee fights back)

    def prey_beside(self, threats, threat):
        """True when threat is the only attacker within 2 tiles, stands beside the bot, and the bot's own assessment (assess: the table corrected by
        memory) says fight, with the damage taken to kill it no more than 0.6 of the hit points left: the r_avoid rule's own line for a hopeless
        fight (hunter, taken > 0.6 x hp). A newbie has no table: its taken is the shared memory's average share of hit points lost against the
        kind, times its maximum; a kind never met has no estimate and is not fought this way. Never for a pack or a kind rated danger."""
        if not hasattr(self, "assess") or (getattr(threat, "distance", 9) or 9) > 1:
            return False
        if sum(1 for m in threats if (getattr(m, "distance", 9) or 9) <= 2) != 1:
            return False
        try:
            a = self.assess(threat) or {}
        except Exception:
            return False
        if not a.get("fight"):
            return False
        taken = a.get("taken")
        if taken is None:
            try:
                stats, _src = self.mem.fight_stats(self.mkey(threat))
                taken = float(stats["avg_dmgpct"]) * float(self.c.max_hp or 0) if stats else None
            except Exception:
                taken = None
        if taken is None:
            return False
        self.__dict__["_prey_taken"] = round(float(taken))
        return float(taken) <= 0.6 * float(self.c.hp or 0)

    def fight_committed(self, threat):
        """True for FLEE_STUCK_S s after flee_stuck found the bot boxed in, while the attacker is still beside it: the fight goes on with no new
        flight. Each flight dropped the fight for a walk that went nowhere, and the bot swung once every 3 s: BotHealAdvR, a troll on it near
        Despise, "fleeing ... fighting back ... fleeing" from 34 to 9 hit points in 45 s (2026-11-02 21:43-21:44). An attacker that stepped away
        ends it (a flight may work again)."""
        return time.time() < float(self.facts.get("fight_until", 0) or 0) and (getattr(threat, "distance", 9) or 9) <= 2

    def flee_stuck(self, threat):
        """True when the last FLEE_STUCK_N flights all started on the same tile within FLEE_STUCK_S s and the threat is beside the bot."""
        now = time.time()
        st = self.facts.get("flee_stuck")
        here = [self.c.x, self.c.y]
        if not st or now - st["t0"] > self.FLEE_STUCK_S or max(abs(here[0] - st["xy"][0]), abs(here[1] - st["xy"][1])) > 1:
            self.facts["flee_stuck"] = {"xy": here, "t0": now, "n": 1}
            return False
        st["n"] += 1
        if st["n"] >= self.FLEE_STUCK_N and (getattr(threat, "distance", 9) or 9) <= 2:
            self.facts.pop("flee_stuck", None)
            return True
        return False

    def sprint(self):
        """Run whatever the stamina, for the next few seconds: a flight. The client drops to a walk by itself only when stamina is gone;
        sprint_check() puts the run mode back to auto (run only at half stamina or more) once the flight is over."""
        self.facts["sprint_at"] = time.time()
        if time.time() < self.facts.get("walk_until", 0):
            return                                                       # too tired to run (stamina_relief): walk
        if getattr(self, "mount_tired", lambda: False)():
            return                                                       # the horse cannot run (ride.py): its running steps are blocked, a walk is not
        if self.facts.get("runmode") != "always":
            self.set_runmode("always")

    RUN_FLOOR = 0.2      # run while stamina is at least this share of its max. Running costs 1 stamina in 16 steps (PlayerMobile.StepsMax 16), plus 1 a step
                         # below 10% (stamina.additionalLossWhenBelow 0.1), and is refused only at 0 (stamina.cannotRunWhenFatigued): twice that line keeps a
                         # flight's margin (18 tiles is about 1 stamina, a hit at most 3 under stamina relief). The client's own "auto" walks below half,
                         # which held carpenters and rangers to 0.35-0.38 s a tile against 0.14-0.18 for the rest (2026-10-30)
    RUN_RESUME = 0.3     # ... and starts again above this, so a bot near the line does not switch each tick

    def sprint_check(self):
        now = time.time()
        mode = self.facts.get("runmode")
        if getattr(self, "mount_tired", lambda: False)():
            if mode != "never":
                self.set_runmode("never")                                # a tired horse walks (ride.py); the client's "auto" goes by the rider's stamina
            return
        if mode == "never" and getattr(self, "mount_rested", lambda: False)():
            self.set_runmode("auto")                                     # the horse has had its walk: running again
        if mode == "never":
            return                                                       # walking on purpose (pacing in town, a recovery walk)
        if mode == "always" and now - self.facts.get("sprint_at", 0) <= 8:
            return                                                       # a flight runs whatever the stamina
        try:
            mx = int((self.c.state or {}).get("maxStam") or 0)
            st = int(self.c.stamina or 0)
        except Exception:
            mx = st = 0
        if not mx or now < self.facts.get("walk_until", 0):
            want = "auto"
        elif mode == "always":
            want = "always" if st >= self.RUN_FLOOR * mx else "auto"
        else:
            want = "always" if st >= self.RUN_RESUME * mx else "auto"
        if want != mode:
            self.set_runmode(want)

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
        hub = None
        try:                                              # Britain is the hub (owner, 2026-10-21): a core fighter's home is never anywhere else (MaceBR's home became Trinsic and it hunted among spiders and skeletal knights)
            if gz is not None and getattr(self, "core_active", lambda: False)() and not (getattr(self, "HOME_DANGER_MOVES", False) or getattr(self, "GATHER_ROAMS", False)):
                hub = gz.region(BIRTH_TOWN)
        except Exception:
            hub = None
        if hub:
            cur = getattr(self, "_home", None) or gz.region(self.facts.get("home_region") or "")
            if (cur and cur.get("name") != hub["name"]) or (self.facts.get("home_region") not in (None, hub["name"])):
                if time.time() - self.__dict__.get("_home_refused_at", 0) > 600:
                    self.__dict__["_home_refused_at"] = time.time()
                    try:
                        self.ev("home_move_refused", wanted=(cur or {}).get("name") or self.facts.get("home_region"), kept=hub["name"])
                    except Exception:
                        pass
            self.facts["home_region"] = hub["name"]
            self.facts.setdefault("birth_town", hub["name"])
            self._home = hub
            return hub
        h = getattr(self, "_home", None)
        if h:
            return h
        if gz is None:
            return None
        name = self.facts.get("home_region")
        if "birth_town" not in self.facts and name:
            self.facts["birth_town"] = BIRTH_TOWN if name != BIRTH_TOWN and gz.region(BIRTH_TOWN) else name
        h = gz.region(name) if name else None
        birth = gz.region(self.facts.get("birth_town") or BIRTH_TOWN)
        if h and birth and h["name"] != birth["name"] and not town_holds(h["name"], HOME_BASICS) and town_holds(birth["name"], HOME_BASICS):
            self.log(f"home: {h['name']} has no bank or healer; home is {birth['name']} again")
            self.facts["rehome_walk"] = True
            h = birth                                     # a home kept from before the rule above (BotTailorBR: Yew)
        needs = getattr(self, "HOME_NEEDS", ())                       # (a brain that borrows home(), the caster, has no class attribute of its own)
        if not h and needs and self.c.x < 5120:
            h = town_with(needs, self.c.x, self.c.y)
            if h and max(abs(h["centre"][0] - self.c.x), abs(h["centre"][1] - self.c.y)) > 120:
                self.facts["rehome_walk"] = True                   # go there first (r_far's far travel walk: by moongate when the planner finds one cheaper);
                                                                    # the fisher thrown to Vesper took Britain as home and set off for a Britain shore on foot           # a trade that needs a buyer lives where the buyer is (see HOME_NEEDS)
        if not h:
            here = gz.home_region(self.c.x, self.c.y)
            if here and here.get("kind") == "town" and self.home_unsafe(here["name"]) and gz.region(self.facts.get("birth_town") or BIRTH_TOWN):
                here = gz.region(self.facts.get("birth_town") or BIRTH_TOWN)      # not a town it left for its deaths (patch_home_town)
            if here and here.get("kind") == "town":
                h = here
            elif self.c.x < 5120:                         # on the surface: the nearest town; below ground, wait until it is back up
                h = gz.nearest_town(self.c.x, self.c.y)[0]
        if h:
            self.facts["home_region"] = h["name"]
            self.facts.setdefault("birth_town", h["name"])          # a new bot: born where it first stands
            self._home = h
        return h

    HOME_NEEDS = ()            # gazetteer roles a bot's trade needs in its home town (a fisher: the fisherman who buys the catch, a bank). A bot with no home
                               # yet takes the nearest town that has them all, not the one it stands in: BotFisherAR, thrown to Vesper with no fish buyer
                               # nearer than Britain's, walked 1,449 tiles of wilds to sell and died twice in two hours (2026-10-31). () = the town it stands in

    HOME_DANGER_MOVES = False                             # crafters, miners and fishers move house when their home keeps killing them (patch_home_town)

    ROAM_AFTER = 1260                                     # no free gathering spot near home this long: work moves to another town (patch_gather_roam). An emptied ore bank
                                                          # refills 10-20 min after (Mining.cs MinRespawn/MaxRespawn): at 600 s the miners left Britain just before its banks came back
    ROAM_REST = 7200                                      # a town left for want of spots is not taken again for this long
    ROAM_MIN = 6                                          # a town needs this many spots of the kind
    ROAM_RISK = 0.25                                      # a town whose spots average more danger than this (the area map, this bot's skill) is left out (patch_roam_safe)
    ROAM_SAMPLE = 12                                      # spots sampled per town for that
    ROAM_HEAVY = 0.7                                      # over this share of its weight limit the move waits: sell, smelt or bank first

    ROAM_WINDOW = 3600.0       # the no-free-spot time gather_roam counts decays with this time constant (s)

    def gather_roam(self, kind, free):
        """Every spot of this kind ("mountains", "shores") near home taken, blocked or worked out for ROAM_AFTER s: the work moves to the mainland town with
        the most spots for the walk. free: a spot was found now (the clock stops). True when the home moved (patch_gather_roam)."""
        now = time.time()
        since = self.__dict__.setdefault("_roam_since", {})       # the brain's own clock, not facts: the 8.7 days the farm was off counted as "no free spot" and both
        self.facts.pop("roam_since", None)                         # miners left for Cove a minute after the 2026-10-30 start, and died on the way
        # seconds with no free spot over about the last hour (decaying, time constant ROAM_WINDOW), not one unbroken stretch: Britain's dock has 5-6 fish
        # banks, each full again within 20 min of its first catch, so a free one came up every few minutes, the old clock never reached ROAM_AFTER and the
        # fisher stood idle about half of every hour (2026-10-31)
        acc = self.__dict__.setdefault("_roam_idle", {})
        last, total = acc.get(kind, (now, 0.0))
        dt = min(max(0.0, now - last), 120.0)
        total = total * math.exp(-dt / self.ROAM_WINDOW) + (0.0 if free else dt)
        acc[kind] = (now, total)
        if free:
            since.pop(kind, None)
            return False
        since.setdefault(kind, now)
        if total < self.ROAM_AFTER or gz is None or not getattr(self, "GATHER_ROAMS", False):     # miners and fishers only (patch_step3_fixes)
            return False
        w, mw = getattr(self.c, "weight", 0) or 0, getattr(self.c, "max_weight", 0) or 0
        if mw and w > mw * self.ROAM_HEAVY:
            return False                                  # not across the wilds with a full pack: sell, smelt or bank first (patch_roam_safe)
        since.pop(kind, None)
        acc.pop(kind, None)
        h = self.home()
        old = h["name"] if h else None
        rested = {k: t for k, t in (self.facts.get("roam_rested") or {}).items() if t > now}
        if old:
            rested[old] = now + self.ROAM_REST
        self.facts["roam_rested"] = rested
        import geo
        cands = []
        for t in gz.towns():
            if t["name"] == old or t["name"] in rested or self.home_unsafe(t["name"]) or t["centre"][0] >= gz.SURFACE_X:
                continue
            try:
                spots = geo.regional(kind, t, [], 300)
                if kind == "shores":
                    import fishspot
                    spots = [s for s in spots if fishspot.has_stand(s)]
                spots = self.roam_spots(kind, t, spots)
            except Exception:
                continue
            if len(spots) < self.ROAM_MIN:
                continue
            d = max(abs(t["centre"][0] - self.c.x), abs(t["centre"][1] - self.c.y))
            try:
                from memory import cell_of
                step = max(1, len(spots) // self.ROAM_SAMPLE)
                sample = spots[::step][:self.ROAM_SAMPLE]
                risk = sum(self.gather_risk(cell_of(s[0], s[1])) for s in sample) / max(1, len(sample))
            except Exception:
                risk = 0.0
            if risk > self.ROAM_RISK:
                continue                                  # a town it would not survive (patch_roam_safe)
            cands.append((len(spots) / (1.0 + d / 500.0) * (1.0 - risk), t, len(spots), d))
        best = None
        try:
            import walkroute
            walk = walkroute.get()
        except Exception:
            walk = None
        refused = []
        for c in sorted(cands, key=lambda c: -c[0])[:4]:
            if walk is None:
                best = c
                break
            try:
                pen = self.far_penalty() if hasattr(self, "far_penalty") else None
                r = walk.plan((self.c.x, self.c.y), (int(c[1]["centre"][0]), int(c[1]["centre"][1])), pen)
            except Exception:
                r = None
            if r is None:
                continue                                  # an island town has no land route from here
            bad = self.route_danger(r)
            if bad:
                refused.append(f"{c[1]['name']} ({bad})")
                continue
            best = c
            break
        if not best:
            self.log(f"gather: no free {kind} spot near {old}, and no other town to go to" + (f": the way to {', '.join(refused)}" if refused else ""))
            return False
        _, t, n, d = best
        why = f"no free {kind} spot near {old} for {int(total) // 60} min of the last hour or so; {t['name']} has {n}, {d} tiles away"
        self.facts["home_region"] = t["name"]
        self._home = t
        for k in ("_mountain_list", "_shore_list"):
            self.__dict__.pop(k, None)
        self.facts.pop("home", None)
        self.facts["rehome_walk"] = True
        self.log(f"gather: {why}: moving work to {t['name']}")
        try:
            self.ev("rehome", **{"from": old, "to": t["name"], "why": why})
            self.dlog("choice", what="move work", why=why)
        except Exception:
            pass
        return True

    def roam_spots(self, kind, town, spots):
        """The spots of `kind` a move to `town` would give this brain (a brain that works a smaller radius narrows them: miner.py)."""
        return spots

    def route_danger(self, r, passable=None):
        """'' when a gatherer may walk the planned route (walkroute.plan's dict), else the first cell it must not use (gather_danger: the area danger map at
        this bot's skill). Every miner move from Britain crossed one (Gargoyles at 1806,1273, Ogres at 2498,767) and cost two deaths a move, 10-19 to 10-30.
        passable(cell): a cell it may cross whatever the deaths (first_trip.trip_cell_passable: a running trip past ground that shows no caster)."""
        from memory import cell_of
        if getattr(self, "mem", None) is None:
            return ""                                     # no memory, no map: nothing to judge by
        seen = set()
        for x, y in (r.get("path") or [])[::8]:
            cell = cell_of(int(x), int(y))
            if cell in seen:
                continue
            seen.add(cell)
            if gz is not None and gz.in_town(int(x), int(y)):
                continue                                  # a guarded town is no killing ground: 1440,1600 beside Britain's healer holds 17 deaths (ghosts
                                                          # come back there) and refused every walk out of Britain (2026-10-30). Before gather_danger too: its
                                                          # decayed deaths around a cell (c29fd46) closed 1440,1640 and refused every trip out of Britain at its
                                                          # first step (BotHealAdvR, "the route crosses 1440,1640", 2026-11-02 09:21)
            if passable is not None and passable(cell):
                continue
            if self.gather_danger(cell):
                return f"crosses {cell}"
            n = self.cell_deaths(cell)
            if n >= HOME_DEATHS:
                return f"crosses {cell}, where {n} bots no stronger died in {ROUTE_DEATH_DAYS} days"
        return ""

    def cell_deaths(self, cell):
        """Deaths in the cell over ROUTE_DEATH_DAYS by bots no stronger than this one (within the danger map's SKILL_MARGIN). Also a gatherer's spot test:
        BotSmithBR was boxed in and killed by skeletons at the dig spot 1359,1453, in a cell with 11 such deaths, which the 24-hour map had forgotten."""
        import area_danger
        mine = area_danger.combat_skill(getattr(self, "skill_values", {}))
        return sum(1 for sk in route_deaths().get(cell, ()) if sk is None or sk <= mine + area_danger.SKILL_MARGIN)

    def home_unsafe(self, name):
        return self.facts.get("unsafe_homes", {}).get(name, 0) > time.time()

    def home_danger(self):
        """An unsafe home (HOME_DEATHS of its own deaths in HOME_WINDOW s within HOME_REACH tiles of it): the home moves to the birth town, else to the
        nearest other town not left lately, and a walk there is queued. True when it moved."""
        if not self.HOME_DANGER_MOVES or gz is None or time.time() - self.facts.get("home_checked", 0) < 60:
            return False
        self.facts["home_checked"] = time.time()
        h = self.home()
        if not h:
            return False
        cx, cy = self.home_centre()
        now = time.time()
        near = [d for d in self.facts.get("death_log", []) if now - d[0] <= HOME_WINDOW and max(abs(d[1] - cx), abs(d[2] - cy)) <= HOME_REACH]
        if len(near) < HOME_DEATHS:
            return False
        old = h["name"]
        unsafe = {k: t for k, t in self.facts.get("unsafe_homes", {}).items() if t > now}
        times = self.facts.setdefault("unsafe_count", {})
        times[old] = times.get(old, 0) + 1
        unsafe[old] = now + UNSAFE_FOR * min(32, 2 ** (times[old] - 1))     # each time it kills again, twice as long: the miners went back to Cove and to Minoc every
                                                                            # 6 h, and each time it cost two deaths (5 moves to Cove, 4 to Minoc, 10-19 to 10-21)
        self.facts["unsafe_homes"] = unsafe
        birth = gz.region(self.facts.get("birth_town") or BIRTH_TOWN)
        # a home has a bank, a healer and what the trade needs: on this shard only Britain has any of them, and BotTailorBR, moved to Yew for two
        # deaths near Britain, walked or gated back to Britain's shop, bank and healer again and again and died on the way seven times (2026-11-01)
        needs = HOME_BASICS + tuple(getattr(self, "HOME_NEEDS", ()) or ())
        towns = [t for t in gz.towns() if t["name"] != old and t["name"] not in unsafe and t["centre"][0] < gz.SURFACE_X and town_holds(t["name"], needs)]
        towns.sort(key=lambda t: (not (birth and t["name"] == birth["name"]), max(abs(t["centre"][0] - self.c.x), abs(t["centre"][1] - self.c.y))))
        new, refused = None, []
        for t in towns[:4]:
            # the way there must be ground this bot may walk: BotSmithBR moved from Britain to Cove after two deaths there and died to a gargoyle on the
            # 680-tile walk (1997,1337, 2026-10-30); a home with no safe way to it is worse than the home it has
            try:
                import walkroute
                r = walkroute.get().plan((self.c.x, self.c.y), (int(t["centre"][0]), int(t["centre"][1])), self.far_penalty() if hasattr(self, "far_penalty") else None)
            except Exception:
                r = None
            bad = "no land route" if r is None else self.route_danger(r)
            if bad:
                refused.append(f"{t['name']} ({bad})")
                continue
            new = t
            break
        if not new:
            unsafe.pop(old, None)
            self.facts["unsafe_homes"] = unsafe
            self.log(f"home: {len(near)} deaths near {old}, but no other town has a safe way to it ({', '.join(refused) or 'none listed'}): staying")
            self.facts["home_checked"] = time.time() + 1740          # the next look in 30 min, not every minute (four route plans a look)
            return False
        why = f"{len(near)} deaths in the last {HOME_WINDOW // 3600} h within {HOME_REACH} tiles of {old}"
        self.facts["home_region"] = new["name"]
        self._home = new
        self.facts.pop("home", None)                      # the crafter's flee spot, taken from the old home
        self.facts["rehome_walk"] = True
        self.log(f"home: {why}; moving home to {new['name']} (not {old} again for {int(unsafe[old] - now) // 3600} h)")
        try:
            self.ev("rehome", **{"from": old, "to": new["name"], "why": why})
            self.dlog("choice", what="move home", why=f"{why}: {new['name']}")
        except Exception:
            pass
        return True

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
        if self.below_my_tier(a["x"], a["y"]):
            self.facts.pop("anchor")
            self.dlog("choice", what="leave camp", why=f"{a['x']},{a['y']} is ground for weaker players (area tier below mine)")
            return False                                  # patch_camp_tiers2.py
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

    def below_my_tier(self, x, y):
        """(x, y) lies in a Britain hunting area of a lower tier than this bot patrols (patch_camp_tiers2.py)."""
        fn = getattr(self, "patrol_tiers", None)
        if fn is None:
            return False
        try:
            floor = min(fn())
            if floor <= 1:
                return False
            from places import area_tier_at
            t = area_tier_at(x, y)
            return t is not None and t < floor
        except Exception:
            return False

    def revisit_anchor(self):
        """A camp that paid (2 kills or more), left at least six minutes ago so its spawn is back: the next patrol point, before a new place."""
        now = time.time()
        left = self.facts.get("anchors_left", [])
        ok = [a for a in left if now - a[2] > 360 and a[3] >= 2 and not self.below_my_tier(a[0], a[1])]
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
        try:
            import task_core
            dest = task_core.box_exit(self, int(dest[0]), int(dest[1]))      # never flee into the undead box (a bot under 120 hit points)
        except Exception:
            pass
        if threat is None:
            return dest
        near_refuge = max(abs(dest[0] - self.c.x), abs(dest[1] - self.c.y)) <= 60
        try:
            # away from every danger in view, not the one threat only, never into a caster lair, home breaking ties (detour.escape_leg): the straight
            # line from one threat can run into the next camp (2026-11-03, owner: "all bots utilize the new detour logic")
            import detour
            import walkroute
            ths = self.walk_threats()
            if all((th.x, th.y) != (int(threat.x), int(threat.y)) for th in ths):
                ths.append(detour.Threat(int(threat.x), int(threat.y), self.kind_casts(self.mkey(threat)), getattr(threat, "name", "") or "",
                                         detour.poisons(self.mkey(threat))))
            here = (int(self.c.x), int(self.c.y))
            forbid = self.detour_forbid(here, self.caster_lair_home())
            if near_refuge:
                to = (int(dest[0]), int(dest[1]))
                if not detour.needs_detour(here, to, ths):
                    return dest
                # a refuge near, but the straight way to it runs into a threat: a leg toward it round them, else out of reach. BotMineAdvR's flights
                # from an ogre and giant rats by its dig spot at 1176,1404 ran straight for the Britain refuge, into the camp at 1240-1280,1360-1400,
                # where 8 mobiles boxed it in (2026-11-03 20:14-20:16)
                leg = detour.plan_leg(here, to, ths, walkroute.get().leg_clear, forbidden=forbid)
                if leg is None:
                    leg = detour.escape_leg(here, ths, walkroute.get().leg_clear, prefer=to, forbidden=forbid)
            else:
                leg = detour.escape_leg(here, ths, walkroute.get().leg_clear, prefer=tuple(self.home_centre()), forbidden=forbid)
            if leg is not None:
                self.detour_note(here, leg)
                try:
                    import task_core
                    return task_core.box_exit(self, int(leg.to[0]), int(leg.to[1]))
                except Exception:
                    return leg.to
        except Exception:
            pass
        if near_refuge:
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
        fx, fy = self.c.x + round(12 * vx / k), self.c.y + round(12 * vy / k)
        try:
            import task_core
            fx, fy = task_core.box_exit(self, int(fx), int(fy))
        except Exception:
            pass
        return fx, fy

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

    # ---- dressing: after a resurrection the starting gear is back in the pack, not on the body ----------------------------------------------
    WEAPONS = {"Archer": ("bow", "crossbow"), "Ranger": ("bow", "crossbow"), "Bard": ("bow", "crossbow"), "MaceFighter": ("club", "mace", "hammer", "staff"),
               "Fencer": ("kryss", "spear", "fork", "dagger"), "Swordsman": ("katana", "sword", "scimitar", "cutlass", "axe"), "Warlock": ("katana", "sword", "scimitar")}
    ARMOR = ("tunic", "leggings", "sleeves", "gloves", "gorget", "helm", "cap", "coif", "shield", "chest", "arms", "legs")
    CLOTHES = ("shirt", "pants", "shoes", "boots", "doublet", "skirt", "kilt")
    # the layer a piece takes, by the word in its name (the client's layer names, lower case): a layer already worn is dressed, whatever the piece's name
    LAYER_OF = {"tunic": "innertorso", "chest": "innertorso", "leggings": "pants", "legs": "pants", "pants": "pants", "skirt": "pants", "kilt": "pants", "sleeves": "arms",
                "arms": "arms", "gloves": "gloves", "gorget": "neck", "helm": "helmet", "cap": "helmet", "coif": "helmet", "shield": "twohanded", "shirt": "shirt",
                "doublet": "shirt", "shoes": "shoes", "boots": "shoes"}

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
            layer = next((l for w, l in self.LAYER_OF.items() if w in low), None)
            if layer and layer in worn:
                continue                                   # that layer is dressed (leather leggings over long pants swapped every minute; sim run 2026-10-19)
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
        self.on_evade(m)
        self.sprint()
        self.c.goto(*self.flee_point(m)).wait(timeout=8)     # away from it, and toward town, not out into the wilds
        return True

    def on_evade(self, m):
        """A trade's work spot near the monster just walked away from is left for a while (MinerBot); by default nothing."""

    @staticmethod
    def bandage_seconds(dex):
        """How long a bandage on oneself takes, pre-AOS: 9.4 + 0.6 x (120 - Dex) / 10 seconds (UOContent Items/Skill Items/Misc/Bandage.cs, BandageContext.BeginHeal)."""
        return 9.4 + 0.6 * (120 - max(0, min(120, int(dex or 0)))) / 10.0

    def bandage_useless(self):
        """True while poisoned without Healing and Anatomy 60: a bandage on a poisoned patient only tries to cure, and below 60/60 it fails outright, no
        cure and no heal (Bandage.cs BandageContext.EndHeal: checkSkills = healing >= 60.0 && anatomy >= 60.0). BotFairSwordVR (Healing 55.9) put six on
        while poisoned crossing the pass (2026-11-04 01:05-01:07), each one also blocking a useful bandage for its 9-12 s."""
        try:
            if not getattr(self.c, "poisoned", False):
                return False
            sv = getattr(self, "skill_values", {}) or {}
            return not (float(sv.get("Healing", 0) or 0) >= 60.0 and float(sv.get("Anatomy", 0) or 0) >= 60.0)
        except Exception:
            return False

    def bandage_start(self, why=""):
        """Put a bandage on oneself and go on at once: walking or running does not stop a bandage on oneself (BandageContext checks only the range to
        the patient, and one is always in range of oneself; a hit makes the fingers slip, which only lessens the heal). bandage_self waits for the
        answer and the brain stands still that long, 12.6 s at Dex 66: BotWarAdvR and BotHealAdvR bandaged that way beside a gargoyle and a gazer,
        lost 30 and 41 hit points standing, and died (2026-11-03 14:35, 14:38). Shares bandage_at with bandage_self, so neither cancels the other's
        bandage. True when one was put on."""
        try:
            b = self.c.find("bandage")
        except Exception:
            return False
        if not b or self.bandage_useless():
            return False                                    # (poisoned below 60/60: the Cure potion's business)
        secs = self.bandage_seconds((self.c.state or {}).get("dex"))
        if time.time() - self.facts.get("bandage_at", 0) < secs + 1:
            return False                                    # one is on
        self.facts["bandage_at"] = time.time()
        try:
            self.c.use_on(b.serial, "self")
        except Exception:
            return False
        self.ev("consumable_used", item="bandage", hp=self.hp_pct(), ok=None, why=why or "moving")
        return True

    def bandage_self(self):
        """Bandage oneself and wait for the server's answer in the journal for the engine's bandage time plus 1 s. A new bandage while one is on cancels the first
        (BandageContext.BeginHeal stops the old context), so it never starts another inside that time (the Watcher, 2026-10-29: the old wait listened for
        BANDAGE_DONE events the farm's client never sends, gave up at 12 s, and 93 of 105 bandages were 'no answer', each one restarting the clock)."""
        b = self.c.find("bandage")
        if not b or self.hp_pct() > 80 or self.bandage_useless():
            return False                                    # (bandage_useless: poisoned below 60/60, it neither cures nor heals)
        secs = self.bandage_seconds((self.c.state or {}).get("dex"))
        if time.time() - self.facts.get("bandage_at", 0) < secs + 1:
            time.sleep(1.0)
            return True                                    # one is on: let it finish
        self.facts["bandage_at"] = time.time()
        self.read_journal()
        before = self.c.hp
        self.c.use_on(b.serial, "self")
        deadline = time.time() + secs + 1                 # the bandage's own time (Dex), and a second for its answer: it ends at the answer (owner, 2026-11-03)
        text = ""
        while time.time() < deadline:
            time.sleep(1.0)
            for l in self.read_journal():
                if re.search(r"bandage|heal|must wait|not damaged|fingers slip", l, re.I):
                    text = l
            if re.search(r"barely help|finish applying|you heal|cannot|not damaged|interrupt|stop|must wait|slip", text, re.I) and "begin" not in text.lower():
                break
        ok = bool(re.search(r"barely help|finish applying|you heal", text, re.I))
        self.log(f"bandage ({secs:.1f} s): {text[:70] or 'no answer'} -> {before} to {self.c.hp}")
        self.ev("consumable_used", item="bandage", hp=self.hp_pct(), ok=ok, gained=int(self.c.hp or 0) - int(before or 0))
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
        return self.loot_corpse(corpse)

    LOOT_NEVER = ()                                       # (the Watcher first said robes, boots, cloaks sell nowhere; the shared vendor lists show they do: 40, 75, 35)
    CORPSE_NAMES = {"deer": ("hind", "greathart"), "hare": ("rabbit",)}              # corpse name -> the profit table's keys (creature_stats 'name' is the living creature's: a hind's corpse reads "deer")
    LOOT_CLOTHES = ("robe", "cloak", "boots", "hat", "sash", "empty bottle")      # light things that sell: looted while the pack is under 70% of its weight

    def loot_corpse(self, corpse):
        """Standing at a corpse: open it, carve it when a blade is carried and the kind carves, take what is worth taking (r_loot's second half; the
        hunt tree (hunt_tree.py) loots the bot's own kills through this)."""
        self.facts["looted"].add(corpse.serial)
        opened, forbidden = self.open_corpse(corpse)
        kind_key = items.corpse_kind(corpse.name)
        if not opened:
            try:                                              # why a loot step took nothing (the Watcher, 2026-10-21)
                self.ev("loot_empty", prey=kind_key, opened=bool(opened), forbidden=bool(forbidden))
            except Exception:
                pass
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
        carves = False
        if getattr(self, "CARVE", False):
            try:                                              # a kind carves when the profit table (the engine's loot data) has meat or hides for it, not only the old name list
                import profit
                for k_ in (kind_key,) + self.CORPSE_NAMES.get(kind_key, ()):          # a corpse reads "deer" or "hare", the table's keys are hind/greathart and rabbit
                    e_ = profit.table().get(k_)
                    if e_ and (float(e_.get("meat") or 0) > 0 or float(e_.get("hides") or 0) > 0):
                        carves = True
            except Exception:
                carves = False
            carves = carves or any(k in corpse.name.lower() for k in self.CARVE_KINDS)
        why_not = None
        last_line = ""
        room = self.carve_room(kind_key)
        if not getattr(self, "CARVE", False) or not carves:
            why_not = "not_carvable"
        elif not room:
            why_not = "heavy"
        else:
            blade = self.carving_blade()
            if not blade:
                why_not = "no_blade"
            else:
                # a blade on the corpse: the meat goes into the corpse, then it is looted like the rest (G13b). The corpse was opened a moment ago: the shard's action delay answers
                # "You must wait to perform another action" to a use too soon after (no cursor), so wait for the delay and try again, up to three times.
                got_cursor = False
                attempt = 0
                for attempt in range(3):
                    time.sleep(1.1 + 0.6 * attempt)
                    self.c.events.drain()
                    self.c.use(blade.serial)
                    if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is not None:
                        got_cursor = True
                        break
                    lines = self.read_journal()
                    last_line = (lines[-1] if lines else "")[:80]
                    if not any("must wait" in l.lower() for l in lines):
                        break
                if got_cursor:
                    self.c.target(corpse.serial)
                    time.sleep(1.5)
                    self.read_journal()
                    try:
                        contents = self.c.container(corpse.serial, timeout=5) or contents
                    except Exception:
                        pass
                    try:
                        self.ev("carve", prey=kind_key, meat=sum((it.amount or 1) for it in contents if "raw " in it.name.lower()),
                                hides=sum((it.amount or 1) for it in contents if "hide" in it.name.lower()), tries=attempt + 1, blade=(blade.name or "")[:20])
                    except Exception:
                        pass
                else:
                    why_not = "no_cursor"
        if why_not:
            try:
                self.ev("carve_skipped", prey=kind_key, why=why_not, line=(last_line if why_not == "no_cursor" else ""))
            except Exception:
                pass
        scissors = next((i for i in self.c.backpack if "scissors" in (i.name or "").lower()), None)
        if getattr(self, "CARVE", False) and (self.core_active() or self.CUTS_HIDES) and scissors is not None and not self.threats(8):
            cut = 0
            for pile in [i for i in contents if "hide" in (i.name or "").lower()][:3]:
                # the owner (2026-10-29): hides are cut on the corpse and the leather picked up: the engine allows it before AOS (Hides.Scissor checks the
                # backpack only under Core.AOS) and drops the leather in the same container (Item.ScissorHelper); a hide weighs 5 stones, its leather 1
                self.c.events.drain()
                self.c.use(scissors.serial)
                if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
                    break
                self.c.target(pile.serial)
                time.sleep(1.2)
                self.read_journal()
                cut += 1
            if cut:
                try:
                    contents = self.c.container(corpse.serial, timeout=5) or contents
                except Exception:
                    pass
                self.ev("cut_on_corpse", prey=kind_key, piles=cut, leather=sum((it.amount or 1) for it in contents if (it.name or "").lower().endswith("leather")))
        if not contents:
            self.note("loot", "An empty corpse still opens by itself.", key="emptycorpse")
            try:
                self.ev("loot_empty", prey=kind_key, opened=True, forbidden=False, contents=0)
            except Exception:
                pass
            return True
        worth = ("gold", "pearl", "moss", "garlic", "ginseng", "mandrake", "nightshade", "ash", "silk", "potion", "scroll", "bandage", "gem", "ruby", "sapphire",
                 "emerald", "diamond", "amber", "citrine", "tourmaline", "arrow", "bolt", "feather") + (self.MATERIALS if self.LOOT_MATERIALS else ())
        # weapons and armour to sell, while there is room for them (a fighter's living: G13); carved meat for the Butcher (G13b)
        gear = getattr(self, "LOOT_GEAR", ()) if self.c.weight < self.c.max_weight * 0.7 else ()
        worth += (("amethyst", "star sapphire") if self.feature("livelihood") else ())
        worth += (self.LOOT_CLOTHES if self.c.weight < self.c.max_weight * 0.7 else ())
        hide_hunt = getattr(self, "_hide_only", False)                          # a tailor hunting its own leather (crafter.hide_hunting): the leather, not the meat
        worth += gear + (("raw ",) if getattr(self, "CARVE", False) and room and not hide_hunt else ())
        if getattr(self, "CARVE", False) and (self.core_active() or hide_hunt) and room:
            worth += ("hide", "cut up leather")                                 # a core bot's sell errand cuts hides into leather for the Tanner (owner, 2026-10-20); the rule list's r_lighten drops them
        meat_value = 0
        gold0 = self.c.gold
        for it in contents:
            if not any(w in it.name.lower() for w in worth) or any(w in it.name.lower() for w in self.LOOT_NEVER):
                continue
            amount = it.amount if (it.amount or 0) > 1 else None
            if items.is_goods(it.name):
                # goods (leather, hides, meat, feathers) only as many as fit under the limit, less the shed's margin (basics.OVERLOAD_MARGIN): the whole
                # stack took BotFencerBR to 442 of 390, and pack_upkeep put 57 cut leather on the ground (2026-11-03 22:31). A player takes what he can carry
                room = self.c.max_weight - getattr(self, "OVERLOAD_MARGIN", 5) - self.c.weight
                fit = int(room // max(items.unit_weight(it.name), 0.01))
                if fit <= 0:
                    continue
                if (it.amount or 1) > fit:
                    amount = fit
            for attempt in range(4):
                time.sleep(0.9 if attempt == 0 else 1.2)
                self.c.events.drain()
                self.c.get_item(it.serial, amount)
                time.sleep(1.0)
                if not any("must wait" in l.lower() for l in self.read_journal()):
                    break
            self.stats["loot"][it.name] = self.stats["loot"].get(it.name, 0) + (it.amount or 1)
            if any(w in it.name.lower() for w in gear):
                self.facts.setdefault("gear_looted", set()).add(it.serial)
            if items.is_meat(it.name):
                meat_value += (it.amount or 1) * items.sale_price(it.name)
        self.log(f"looted {corpse.name}: {[str(x) for x in contents]}")
        if getattr(self, "CARVE", False) and (self.core_active() or self.CUTS_HIDES) and any("hide" in (i.name or "").lower() for i in self.c.backpack)                 and any("scissors" in (i.name or "").lower() for i in self.c.backpack) and not self.threats(8):
            try:
                import errands
                errands.cut_hides(self, {"scissors_tried": True})        # a hide weighs 5 stones, its leather 1 (Hides.cs, Leathers.cs): cut at once, not at the Tanner
            except Exception:
                pass
        if meat_value:
            self.ev("carve", corpse=corpse.name, meat_value=meat_value)
        if self.c.gold - gold0 + meat_value > 0:
            # gold, and what the carved meat will fetch at the Butcher: what a kill of this kind is worth (G12's gold term)
            self.mem.record("loot", cell=cell_of(corpse.x, corpse.y), gold=self.c.gold - gold0 + meat_value, m=items.corpse_kind(corpse.name))
        return True

    def carve_room(self, kind_key):
        """Room in the pack for a carve of this kind: the weight now, plus its hides at 5 stones and its meat at 1 (Hides.cs DefaultWeight 5.0, CookableFood 1.0; the
        profit table's counts), within the most the character can carry. The old line was 70% of the limit, worn armour included: 203 of 302 melee carves were
        skipped as "heavy" in two hours (the Watcher, 2026-10-29), most with hides that are cut into 1-stone leather straight after."""
        try:
            import profit
            e = profit.table().get(kind_key) or {}
            for k_ in self.CORPSE_NAMES.get(kind_key, ()):
                e = e or profit.table().get(k_) or {}
            per_hide = items.unit_weight("leather") if any("scissors" in (i.name or "").lower() for i in self.c.backpack) else items.unit_weight("hides")      # cut on the corpse: leather
            need = per_hide * float(e.get("hides") or 0) + items.unit_weight("raw ribs") * float(e.get("meat") or 0)
        except Exception:
            need = 20.0
        return self.c.weight + need <= self.c.max_weight

    def junk_in_pack(self):
        keep = self.KEEP
        return [i for i in self.c.backpack if not any(w in i.name.lower() for w in keep) and i.name.lower() != "backpack"]

    RICH_GOLD = 900

    CUTS_HIDES = False         # a brain outside the core that cuts hides into leather on the corpse as the core fighters do (TamerBot, feature tamer_carve)
    KEEP = ("book", "gold", "dagger", "candle", "bag", "scroll", "potion", "recall", "scissors", "bedroll", "kindling", "pearl", "moss", "garlic", "ginseng", "mandrake",
            "nightshade", "ash", "silk", "bandage", "gem", "ruby", "sapphire", "emerald", "diamond", "amber", "citrine", "tourmaline", "star ", "check", "arrow", "bolt",
            "ingot", "ore", "board", "log", "hide", "leather", "cloth", "feather", "shaft", "tool", "hammer", "tongs", "saw", "pickaxe", "shovel", "pole", "kit",
            "mortar", "needle", "sewing", "fish", "instrument", "lute", "drum", "harp", "tambourine", "bow", "crossbow", "mace", "club", "kryss", "katana", "sword",
            "shield", "armor", "tunic", "robe", "hat", "cap", "boots", "gloves", "sleeves", "leggings", "gorget", "helm", "pants", "shirt", "cloak", "sash", "apron",
            "skirt", "kilt", "sandals", "shoes", "fork", "knife", "axe", "staff", "spear", "halberd", "cleaver", "scimitar", "broadsword", "longsword", "hatchet") + items.GOODS_WORDS          # goods a shop buys are never banked (items.py)

    def r_bank(self):
        """Rich (450+ gold) or too heavy with leftovers: bank the gold above a reserve."""
        if self.threats(10) or self.hp_pct() < 60 or time.time() - self.facts.get("bank_fail", 0) < 180 or time.time() - self.facts.get("banked_at", 0) < 240:
            return False
        rich = self.c.gold >= self.RICH_GOLD
        made = hasattr(self, "is_product") and any(self.is_product(i.name) for i in self.c.backpack)
        unsold = made and (time.time() < self.facts.get("sell_skip_until", 0) or not self.products())      # selling paused, or every piece struck as unsold
        unsold = unsold or time.time() - self.facts.get("craft_heavy_at", 0) < 300      # r_craft refused the weight (pieces from an older menu are no "product")
        # (a crafter heavy with what no shop bought: r_sell waits out sell_skip_until and r_craft refuses a heavy pack, so only a bank visit, whose heavy
        # pass banks the unsold products, breaks it; BotCarpAR stood 18 min with 40 game boards and 20 backgammon boards at 354/390, 2026-10-30)
        heavy = self.c.weight > self.c.max_weight * 0.8 and (bool(self.junk_in_pack()) or unsold)
        overloaded = self.facts.get("bank_heavy") and self.c.weight > self.c.max_weight * 0.9
        if heavy and not overloaded and time.time() - self.facts.get("bank_full_at", 0) < 1800:
            # the box is full: a heavy-pack visit only takes products out to sell, and the pack comes back heavier. The shops first (r_sell); BotCarpBR banked
            # "heavy" four times in 12 minutes against a full box before it sold (2026-11-01 21:16-21:28)
            heavy = False
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
                red = self.potion("refresh")
                if red is not None:
                    self.log("overloaded and out of stamina: a Refresh potion before the walk to the bank")
                    self.drink(red)
                    time.sleep(1.5)
        if self.feature("bank_spread"):
            return self.bank_spread_walk(bank)
        return self.goto_near(bank[0], bank[1], 4).wait(timeout=90)

    def bank_spot(self, bank):
        """A spot of this bot's own around the banker: a ring of radius 2-5 picked by the bot's name (feature bank_spread)."""
        h = sum(ord(ch) * (i + 3) for i, ch in enumerate(self.name))
        ang = ((h * 47) % 360) * 3.14159265 / 180.0
        r = 2 + (h % 4)
        return int(round(bank[0] + r * math.cos(ang))), int(round(bank[1] + r * math.sin(ang)))

    def bank_spread_walk(self, bank):
        spot = self.bank_spot(bank)
        res = self.goto_near(spot[0], spot[1], 1).wait(timeout=90)
        if not str(res).startswith("arrived"):
            time.sleep(random.uniform(3.0, 5.0))                  # bodies in the way: let them move rather than retry at once
            res = self.goto_near(spot[0], spot[1], 1).wait(timeout=60)
        d = max(abs(self.c.x - bank[0]), abs(self.c.y - bank[1]))
        if not str(res).startswith("arrived") and d <= self.BANK_SPEECH:
            res = "arrived (speaking from here)"                      # the banker hears from here
        self.ev("bank_spot", spot=list(spot), result=str(res)[:40], from_banker=d)
        return res

    OVERLOAD_ESSENTIAL = ("gold", "book", "bandage", "potion", "backpack", "bag", "pearl", "moss", "garlic", "ginseng", "mandrake", "nightshade",
                          "ash", "silk", "arrow", "bolt")
    OVERLOAD_TOOLS = ("tongs", "hammer", "saw", "tool kit", "tinker", "scissors", "pickaxe", "shovel", "hatchet", "axe", "sewing kit", "dovetail",
                      "mortar", "pen", "skillet", "fishing pole", "dagger", "knife", "lockpick", "instrument", "lute", "harp", "drum", "tambourine")

    BANK_FULL = "container cannot hold more items"

    def bank_box_full(self):
        """True when the server just refused a deposit because the bank box is full. A pre-AOS bank box holds 125 items, counting what is
        inside bags, and a crafter whose goods nobody buys fills it: on 2026-10-18 two crafters stood overloaded for over an hour while every
        deposit came back "That container cannot hold more items." (45 times). Remembered for 30 minutes (facts bank_full_at)."""
        if any(self.BANK_FULL in l.lower() for l in self.read_journal()):
            if time.time() - self.facts.get("bank_full_at", 0) > 1800:
                self.log("the bank box is full (125 items): nothing more goes in until something comes out")
                self.note("bank", "A bank box holds 125 items; a full one refuses every deposit with \"That container cannot hold more items.\" A crafter whose goods no shop buys fills it and then cannot shed weight by banking.", key="bankfull")
            self.facts["bank_full_at"] = time.time()
            return True
        return time.time() - self.facts.get("bank_full_at", 0) < 1800

    CLEAR_N = 12                                          # stacks a full bank box is cleared of per visit (patch_bank_clear)
    CLEAR_SHARE = 0.8                                     # sellable stacks come out into the pack only up to this share of the weight limit

    def toss_old_pieces(self):
        """The box is full and a crafter is still too heavy to craft: pieces it made under an older menu whose names hold its material word but are not
        the material ("game board", "backgammon board" for a carpenter) and that no shop is recorded buying go on the ground. BotCarpAdvR carried 56 of
        them (only barkeepers and innkeepers buy them, 1 gold each, SBBarkeeper/SBInnKeeper) and banked one piece a visit for an hour (2026-10-30)."""
        words = (self.cfg["mat"],) + tuple(self.cfg.get("mat_alt", ()))
        tossed = 0
        for it in list(self.c.backpack):
            low = (it.name or "").lower()
            if not any(w in low for w in words) or self.is_material(low):
                continue
            held = self.held_per_stone() if hasattr(self, "held_per_stone") else 0.0
            if any(p > 0 and p / items.unit_weight(low) >= held for p, xy, item in self.mem.vendor_buying(low) if item == low):
                continue                                                  # a shop pays for it, at least what the material is worth a stone: sold, not thrown away
                                                                          # (a board game: 1 gold for 5 stones, against a carpenter's boards at 2 a stone)
            if not self.drop_to_ground(it):
                continue
            tossed += 1
            if self.c.weight <= self.c.max_weight * self.CLEAR_SHARE:
                break
        if tossed:
            self.log(f"bank box full and still heavy: threw out {tossed} old pieces no shop buys, weight now {self.c.weight}/{self.c.max_weight}")
            self.ev("shed", how="toss_old_pieces", item="old pieces", qty=tossed)
        return tossed

    def bank_clear(self, box):
        """The bank box is full: throw out what no shop buys (biggest stacks first), then take out what a shop buys for the next selling trip.
        Returns (tossed, taken) (patch_bank_clear)."""
        try:
            items = list(self.c.container(box, timeout=6))
        except Exception:
            return 0, 0

        def price(it):
            n = (it.name or "").lower()
            try:
                return max([p for p, xy, item in self.mem.vendor_buying(n) if item == n] or [0])
            except Exception:
                return 0
        cand = [i for i in items if (i.name or "") and not any(w in (i.name or "").lower() for w in self.OVERLOAD_ESSENTIAL)]
        worthless = sorted([i for i in cand if price(i) <= 0], key=lambda i: -(i.amount or 1))
        sellable = sorted([i for i in cand if price(i) > 0], key=lambda i: -(price(i) * (i.amount or 1)))
        tossed = taken = 0
        for it in worthless[:self.CLEAR_N]:
            if not self.drop_to_ground(it, box=box):
                continue
            tossed += 1
        for it in sellable:
            if tossed + taken >= self.CLEAR_N or self.c.weight >= self.c.max_weight * self.CLEAR_SHARE:
                break
            self.c.get_item(it.serial, it.amount if (it.amount or 1) > 1 else None)
            time.sleep(1.2)
            taken += 1
        self.log(f"bank box full: threw out {tossed} stacks nobody buys, took out {taken} to sell (box had {len(items)} items)")
        self.ev("bank_cleared", tossed=tossed, taken=taken, items=len(items))
        if tossed or taken:
            self.facts["bank_full_at"] = 0                # room again: the next deposit tries (a refusal marks it full again)
        return tossed, taken

    BOX_PRODUCT_CAP = 100       # box items past which a product a shop buys is not banked: a bank box holds 125 (Container.GlobalMaxItems), and 25 stay
                                # for materials and valuables; BotSmithBR filled all 125 with sellable pieces and then could neither bank nor craft

    def bank_overload_pass(self, box, share=0.85):
        """Overloaded after the usual deposit: everything but the essentials and one of each tool goes in, heaviest stacks first, to 85% of the limit.
        Heaviest by stones, not by count, and a crafter's own material last: "biggest stack" by count put BotSmithAR's 244 iron ingots (24 stones) in the
        box first on heavy visits, and it then bought ingots at the shop with 244 of its own banked (2026-11-01)."""
        before = self.c.weight
        kept_tools = set()
        moved = 0
        own = getattr(self, "own_material", None)
        try:
            kept_colour = self.colour_kept() if hasattr(self, "colour_kept") else set()     # a smith's coloured pieces on offer (colours.py) stay with it
        except Exception:
            kept_colour = set()

        def order(i):
            mine = bool(own and own(i))
            return (mine, -(i.amount or 1) * items.unit_weight(i.name))
        try:
            in_box = len(list(self.c.container(box, timeout=6)))
        except Exception:
            in_box = 0

        def sells(i):
            n = (i.name or "").lower()
            try:
                return any(p > 0 for p, xy, item in self.mem.vendor_buying(n) if item == n)
            except Exception:
                return False
        for it in sorted(list(self.c.backpack), key=order):
            if self.c.weight <= self.c.max_weight * share:
                break
            low = (it.name or "").lower()
            if not low or any(w in low for w in self.OVERLOAD_ESSENTIAL) or str(it.serial) in kept_colour:
                continue
            tool = next((w for w in self.OVERLOAD_TOOLS if w in low), None)
            if tool and tool not in kept_tools:
                kept_tools.add(tool)
                continue                                                # one of each tool stays: the bot can still work
            if in_box + moved >= self.BOX_PRODUCT_CAP and not (own and own(it)) and sells(it):
                continue                                                # a shop buys it: the selling trip, not the box (BOX_PRODUCT_CAP)
            self.c.drop(it.serial, box, it.amount if (it.amount or 1) > 1 else None)
            time.sleep(1.4)
            if self.bank_box_full():
                break                                                   # the box is full (125 items): drop_excess sheds the cheapest instead
            moved += 1
        self.log(f"overloaded: banked {moved} more stacks (products and spares), weight {before} -> {self.c.weight}/{self.c.max_weight}")
        self.ev("shed", how="bank_products", item="products", qty=max(0, before - self.c.weight), stacks=moved)

    def visit_bank(self, why, withdraw=0, reserve=200, extra=()):
        self.beat()
        self.__dict__["_bank_why"] = why                     # (basics.bank_products_out: a heavy visit only puts in)
        banks = self.bank_xys()
        self.log(f"bank trip ({why}): gold {self.c.gold}, weight {self.c.weight}/{self.c.max_weight}")
        res = self.far_front(banks[0], "bank", 90, True if withdraw else self.c.gold)      # a withdrawal for a purchase always goes (far.far_worth)
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
        deed = self.house_state().get("deed_serial") if hasattr(self, "house_state") else None     # a house deed is named just "deed": KEEP cannot hold it (SorcAR banked a 16,000-gold one, 2026-10-30)
        try:
            on_offer = self.colour_kept() if hasattr(self, "colour_kept") else set()
        except Exception:
            on_offer = set()                                    # a smith's coloured pieces on offer stay in the pack, as in bank_overload_pass: BotSmithAR banked
                                                                # the bronze plate helm BotFencerBR had booked, and the deal failed "seller holds 0" (2026-11-02 18:26)
        spare_bank = self.facts.get("spare_bank") or []
        for it in list(self.c.backpack):
            low = it.name.lower()
            if str(it.serial) in on_offer:
                continue
            if str(it.serial) in spare_bank:
                self.c.drop(it.serial, box, None)                 # spare armour no shop took (hunter.gear_unsold): KEEP names helms and gorgets, so it goes in by serial
                time.sleep(1.4)
                spare_bank.remove(str(it.serial))
                continue
            if (any(w in low for w in self.KEEP) and not any(w in low for w in extra)) or low == "backpack" or "bandage" in low or it.serial == deed:
                continue
            self.c.drop(it.serial, box, it.amount if (it.amount or 1) > 1 else None)   # without an amount Navrey moves one of a stack
            time.sleep(1.4)
        if why == "overloaded" and self.c.weight > self.c.max_weight * 0.85:
            self.bank_overload_pass(box)                                  # still too heavy to walk: the products and spares go in too (patch_overload_bank.py)
        elif why == "heavy" and hasattr(self, "products") and self.c.weight > self.c.max_weight * 0.7:
            self.bank_overload_pass(box, 0.7)                             # a crafter's heavy visit: what nobody bought goes in (patch_craft_weight.py)
        if self.bank_box_full():
            self.bank_clear(box)                                          # a full box takes nothing, gold included: make room (patch_bank_clear)
            if hasattr(self, "toss_old_pieces") and hasattr(self, "is_material") and self.c.weight > self.c.max_weight * self.CLEAR_SHARE:
                self.toss_old_pieces()                                    # (crafters only)
        elif why != "overloaded":
            self.bank_goods_out(box)                                      # goods banked before come back out for the shops (basics.py)
        if hasattr(self, "house_deed_from_bank"):
            self.house_deed_from_bank(box)                                # a house deed an earlier visit banked comes back for placing (housegoal.py)
        reserve = goals.reserve(self, reserve, why)                      # saving for a goal: the purse stays small
        if reserve and hasattr(self, "material_reserve"):
            reserve = max(reserve, self.material_reserve())               # a crafter short of material keeps what it will spend on it (crafter.py)
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
        errand = getattr(self, "armor_errand", None)
        if errand is not None and why not in ("upgrade", "overloaded"):
            try:
                errand()                                           # in town anyway: the armour a working player buys on the bank trip (wear.py)
            except Exception as e:
                self.log(f"armour errand failed ({type(e).__name__}: {e})")
        return True

    SHOP_NEAR = 8          # a vendor list is filed under the shop only when the bot stands this close to it (goto_near asks 4; vendors stray a few tiles)

    def shop_at(self, xy, wanted: dict, budget=None):
        """Walk to a shop, find the vendor by trying every person there ("<name> buy"), buy what `wanted` lists ({substring: target amount}). Returns what was bought."""
        self.beat()
        res = self.far_front(xy, "shop", 90)
        if res:
            self.far_after(res, "shop")
            self.facts["shop_list_opened"] = False
            return {}
        res = self.goto_near(xy[0], xy[1], 4).wait(timeout=self.__dict__.pop("shop_walk_s", 90) if self.feature("restock_fix") else 90)
        self.beat()
        self.log(f"to the shop at {xy}: {res}")
        if self.feature("restock_fix") and str(res).startswith(("nopath", "blocked", "timeout")):
            self.facts.setdefault("shop_nopath", {})[tuple(xy)] = time.time() + 600       # the next restock begins at another shop of the role
        self.facts["shop_had_wanted"] = False                  # did the list offer a wanted item at all (r_restock: sold out, or nothing needed)
        if max(abs(self.c.x - xy[0]), abs(self.c.y - xy[1])) > self.SHOP_NEAR:
            # the walk ended short: whoever stands here is not this shop's vendor. Asking them read an armourer's list for the Tailor's shop, and the restock
            # marked cloth sold out at the Tailor in the shared memory (BotTailorBR, 11 times in 13 minutes, walks ending 38-97 tiles short, 2026-11-02 02:01)
            self.facts["shop_list_opened"] = False
            self.facts.setdefault("shop_nopath", {})[tuple(xy)] = time.time() + 600
            return {}
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
        at_shop = max(abs(self.c.x - xy[0]), abs(self.c.y - xy[1])) <= self.SHOP_NEAR
        if rows and at_shop:                                # a walk that ended short asked whoever stood there: their list is not this shop's
            self.mem.record("vendor", xy=f"{xy[0]},{xy[1]}", name=vendor_name, stock=rows)
        json.dump(shops, open(os.path.join(FARM, "shops.json"), "w", encoding="utf-8"), indent=1)
        have = {}
        for it in self.c.backpack:
            if "ingot" in (it.name or "").lower() and getattr(it, "hue", 0):
                continue                                  # the client calls every ingot "iron ingot": a coloured one is not iron owned. BotTinkBR, 1,029
                                                          # coloured and 4 of iron, "owned" 1,033 against 50 and bought none (2026-11-02 04:28)
            have[it.name.lower()] = have.get(it.name.lower(), 0) + (it.amount or 1)
        cart, spent, bought, got = [], 0, {}, {}
        gold = self.c.gold if budget is None else min(budget, self.c.gold)

        def _price(line):
            mm = re.search(r"\s(\d+)gp\s", line)
            return int(mm.group(1)) if mm else 1 << 30
        # the cheapest line first, as a player buys: a vendor resells what players sold it (ModernUO BaseVendor's buy pack) at a higher price beside its
        # own stock, and the list order put the Tanner's resale leather first: BotTailAdvR paid 9-21 a piece (990 gold for 105) against 6 on the
        # shelf (2026-11-02 10:07-10:14)
        for line in sorted(stock, key=_price):
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
        if not self.facts["shop_had_wanted"] and at_shop:
            # no list at this shop offered anything wanted: off this shop in the shared memory (the "sold out" mark, memory.py), else a stale record sends
            # every bot back - one list mis-filed at 1467,1686 (Neoma the Tinker's, 40 tiles away) sent BotMinerAR there for a pickaxe every 5 min (2026-10-31)
            self.mem.record("vendor", xy=f"{xy[0]},{xy[1]}", name="", stock=[[sub.lstrip("="), 0, 0] for sub in wanted])
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
        if sub in ("board", "log"):
            # the whole name: a carpenter restocking "board" bought 10 Backgammon Boards and 3 Checker Boards at the Carpenter (2026-10-30), the start
            # of the 50 board games that stalled BotCarpAR (crafter.matname has the same rule)
            return n in (sub, sub + "s")
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
                vz = (tuple(getattr(here, "pos", None) or ()) + (None, None, None))[2]
                self.c.goto(here.x, here.y, vz).wait(timeout=8)   # a vendor answers only within 4 tiles in this era, and on its own floor (the Mage shop's upper
                                                                  # floor at z 70 heard nothing from Merill at z 30: live, 2026-10-18)
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
        self.__dict__["_sell_unreached"] = False               # True when it returns 0 because the walk never got there (errands' sell: not a refusal)
        res = self.far_front(xy, "sell", 100, sum((i.amount or 1) for i in self.c.backpack if any(w in i.name.lower() for w in words)))
        if res:
            self.far_after(res, "sell")
            self.__dict__["_sell_unreached"] = True
            return 0
        gold0 = self.c.gold
        res = self.c.goto(*xy).wait(timeout=100)
        if not self.travel(xy[0], xy[1], near=3):
            self.__dict__["_sell_unreached"] = True
            return 0
        offers = []
        # the vendors the shared memory has seen buying any of these first: asking every person at a shop cluster took two and a half minutes
        known = {v2["name"] for v2 in self.mem.state["world"]["vendors"].values()
                 if v2.get("name") and any(p > 0 and any(w in item for w in words) for item, p in v2["buys"].items())}
        people = sorted([m for m in self.c.mobiles(within=7) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")],
                        key=lambda m: (m.name not in known, m.distance))
        fallback, fallback_v, seller = [], None, None
        for v in people:
            offers = self.vendor_list(v, "sell")
            if any("gp" in l for l in offers):
                if any(re.search(r"(\d+)gp\s+x\d+\s+(.+)", l) and any(w in re.search(r"(\d+)gp\s+x\d+\s+(.+)", l).group(2).lower() for w in words)
                       and int(re.search(r"(\d+)gp", l).group(1)) > 0 for l in offers):
                    seller = v
                    break                                          # this vendor pays for something wanted (Noella at the tailor's paid nothing for a robe, Chantal 40)
                if not fallback:
                    fallback, fallback_v = offers, v
            offers = []
        else:
            offers, seller = fallback, fallback_v
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
            self.sell_cart(cart, seller)
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
            if self.bank_box_full():
                raise LookupError("bank box full")                    # banking cannot help: go straight to dropping the cheapest
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
            # the least gold a stone first (items.py: a shop's price over the piece's weight; material no shop buys 0), then the old material order. By the
            # material order alone an archer a few stones over dropped 48 cut leather, 5 gold a stone, before its meat (2026-10-30)
            # coloured metal goes before the iron: the client names it after the graphic ("iron ore", "iron ingot"), but no shop buys it (S\blacksmith buys
            # IronIngot only) and the bots' market takes plain ingots only. About one dig in five is coloured at 100 Mining (Mining.cs veins; BotMinerBR
            # 271 of 1,240 digs, 2026-10-31)
            price = -1 if getattr(i, "hue", 0) and re.search(r"\b(ore|ingots?)\b", n) else items.sale_price(n) / items.unit_weight(n)
            return any(w in n for w in last), price, next((k for k, w in enumerate(self.HEAVY_THINGS) if w in n), 99), -(i.amount or 1)
        if time.time() < self.facts.get("drop_refused_until", 0):
            return False                                  # dropping was refused a moment ago: let r_bank walk to the bank box instead
        stacks = sorted((i for i in self.c.backpack if any(w in i.name.lower() for w in self.HEAVY_THINGS) and "bandage" not in i.name.lower()), key=rank)
        if not stacks and self.bank_box_full():
            # nothing heavy but products, and the bank is full: a player tosses what no shop buys, the least worth first (one of each tool stays)
            buys = {}
            try:
                for v in self.mem.state["world"]["vendors"].values():
                    for item, price in v.get("buys", {}).items():
                        buys[item] = max(buys.get(item, 0), price)
            except Exception:
                pass
            def worth(i):                                          # what a known shop pays per piece (0: nobody buys it), biggest pile first
                low = (i.name or "").lower()
                if getattr(i, "hue", 0) and re.search(r"\b(ore|ingots?)\b", low):
                    # coloured metal: the client names it after the graphic ("iron ore", "iron ingot"), but no shop buys it (SBBlacksmith buys IronIngot
                    # only) and the bots' market takes plain ingots only, so it goes before the iron. About one dig in five is coloured at 100 Mining
                    # (Mining.cs veins; BotMinerBR 271 of 1,240 digs, 2026-10-31)
                    return -1, -(i.amount or 1)
                return buys.get(low, 0), -(i.amount or 1)
            kept_tools = set()
            junk = []
            for i in self.c.backpack:
                low = (i.name or "").lower()
                if not low or any(w in low for w in self.OVERLOAD_ESSENTIAL):
                    continue
                tool = next((w for w in self.OVERLOAD_TOOLS if w in low), None)
                if tool and tool not in kept_tools:
                    kept_tools.add(tool)
                    continue
                junk.append(i)
            stacks = sorted(junk, key=worth)
        if not stacks:
            # overloaded by something that is not material (gear, ammunition): nothing here to drop, so the rules (the bank trip) take the tick
            self.facts["drop_refused_until"] = time.time() + 600
            self.facts["bank_heavy"] = True
            return False
        left = 0
        need = max(1.0, float(over))                      # stones to shed: only that much of a stack goes, not the whole stack
        for it in stacks[:3]:
            if need <= 0:
                break
            amt = min(int(it.amount or 1), int(math.ceil(need / items.unit_weight(it.name)))) if items.is_goods(it.name) else (it.amount or 1)
            need -= amt * items.unit_weight(it.name)
            still = not self.drop_to_ground(it, amt)
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
            red = self.potion("refresh")     # Refresh: red, as in the era (items.POTION_NAMES)
            if red:
                self.facts["refreshed_at"] = time.time()
                ok = self.drink(red)
                self.log(f"drank a Refresh potion at stamina {self.c.stamina}")
                self.ev("consumable_used", item="red potion", hp=self.hp_pct(), ok=ok)
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
        if typ == "choice" or (typ == "ev" and kw.get("ev") in self.DECISION_EVS):
            self.decision_record(typ, kw)

    # Choices worth learning from (farmdb decisions): the event and the field that names what was chosen. A "choice" line is one too.
    DECISION_EVS = {"plan": "to", "caster_ground": "ground", "tame_spot": "spot", "bw_plan": "choice", "pair_start": "partners", "trip_start": "dest",
                    "sewer_enter": None, "goal_set": "goal", "deal_booked": "item", "far_service": "role", "stall": "action"}
    DECISION_OPTIONS = ("rates", "score", "value", "kinds", "dist", "eta_min", "corpse_dist", "cost", "price", "qty", "steps")

    def decision_context(self):
        """What the bot knew when it chose: a small, stable set of numbers the outcome can later be explained by."""
        ctx = {"mode": getattr(self, "mode", "veteran")}
        try:
            c = self.c
            ctx.update(hp=c.hp, max_hp=c.max_hp, gold=c.gold, weight=c.weight, max_weight=c.max_weight, x=c.x, y=c.y, cell=f"{c.x // 40 * 40},{c.y // 40 * 40}")
        except Exception:
            pass
        f = getattr(self, "facts", {}) or {}
        ctx["bank"] = f.get("bank_balance")
        died = f.get("died_at")
        ctx["mins_since_death"] = round((time.time() - died) / 60, 1) if died else None
        p = f.get("persona")
        if isinstance(p, dict):
            ctx["persona"] = p.get("main")
        try:
            ctx["skill"] = round(float(self.working_skill()), 1)
        except Exception:
            pass
        ctx["rule"] = getattr(self, "current_rule", None) or getattr(self, "last_rule", None)
        return ctx

    def decision_record(self, typ, kw):
        """Open a decision row in the farm's database (best-effort; never breaks the tick). The episodes that follow fill in its outcome."""
        try:
            import farmdb
            if typ == "choice":
                kind, chosen = "choice:" + str(kw.get("what", "?"))[:40], kw.get("why")
            else:
                ev = kw.get("ev")
                if ev == "far_service" and kw.get("decided") != "go":
                    return
                kind, field = ev, self.DECISION_EVS.get(ev)
                chosen = kw.get(field) if field else ev
            opts = {k: kw[k] for k in self.DECISION_OPTIONS if k in kw} or None
            farmdb.decision_open(self.name, getattr(self, "pname", None), kind, chosen, self.decision_context(), opts)
        except Exception as e:
            if time.time() - getattr(self, "_decision_err_at", 0) > 600:
                self._decision_err_at = time.time()
                try:
                    self.log(f"decisions: database write failed ({type(e).__name__}: {e})")
                except Exception:
                    pass

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
        out = dict(gold=self.c.gold - ep["gold0"], kills=self.kills - ep["kills0"], gains=self.total_gains() - ep["gains0"],
                   hp=self.c.hp - ep["hp0"], died=self.deaths - ep["deaths0"], work=self.work - ep.get("work0", self.work))
        self.dlog("ep", rule=ep["rule"], act=(ep["act"] or "")[:40], dur=round(dur, 1), **out, moved=round(math.hypot(self.c.x - ep["x0"], self.c.y - ep["y0"])))
        try:
            import farmdb
            farmdb.decision_add(self.name, dict(out, secs=round(dur, 1)), now)      # what this stretch yielded goes to the choices that led to it
        except Exception:
            pass

    CRITTERS = ("towhee", "sparrow", "swallow", "nightingale", "plover", "thrush", "tern", "warbler", "finch", "starling", "bird", "magpie", "crow",
                "raven", "pigeon", "gull", "cat", "dog", "squirrel", "rabbit", "jackrabbit", "toad", "frog", "lizard", "mouse")
    CRITTER_SKILL = 35.0
    BIRDS = ("towhee", "sparrow", "swallow", "nightingale", "plover", "thrush", "tern", "warbler", "finch", "starling", "bird", "magpie", "crow",
             "raven", "pigeon", "gull")

    def feathers_pay(self, k):
        """A kind whose carve gives feathers (the engine's Feathers, profit.table) and whose measured fight pays for this bot's group (measured.net > 0): birds are
        prey again (the Watcher, 2026-10-29: melee kill 83% of 443 bird fights in a median 1.4 s with no death; 25 feathers at 1 gold and the meat, 28 gold a carve)."""
        try:
            import profit
            import measured
            if not (profit.table().get(k) or {}).get("feathers"):
                return False
            n = measured.net(self, k)
            return n is not None and n > 0
        except Exception:
            return False

    def critter_skip(self, m):
        """A small critter (a bird, a cat, a squirrel...) is no prey from CRITTER_SKILL on, unless it is on top of the bot (patch_critters.py), or a feathered kind
        that pays (feathers_pay)."""
        if (m.distance or 0) <= 1:
            return False
        key = re.sub(r"[^a-z]", "", (getattr(m, "species", None) or re.sub(r"^(an?|the) ", "", (m.name or "").lower())).lower())    # as mkey (HunterBot's): casters have none
        if self.feathers_pay(key):
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

    def observe(self):
        self.pack_upkeep()                                   # the pack seen, and an overload shed (basics.BasicsMixin)
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

    LEAVE_GRACE = 120.0     # s a brain may run past its time while unsafe_to_leave: a fight's length (the longest the bots rated on 2026-11-02 was a skeletal
                            # knight, ~78 s to kill) or a flight to safety. Every brain of a supervisor run ends at the same moment (start_brain --for the
                            # time left), and the next run starts them about a minute later: BotTamerAR's brain stopped at 03:14:34 with a greater mongbat
                            # on it, the next started at 03:15:47, and it died at 8 hit points (2026-11-03). The next supervisor starts no second brain
                            # while this one runs (farm_launch.is_brain)

    def unsafe_to_leave(self):
        """A brain at its time does not stop in the middle of danger: a hostile within notice range, health under the flee line, or a fight on."""
        try:
            return bool(self.threats(14)) or self.hp_pct() < self.flee_below() or bool(getattr(self, "fight", None))
        except Exception:
            return False

    def run(self, seconds):
        end = time.time() + seconds
        self.log(f"start: {self.pname}")
        try:
            self.c.open_backpack()            # a client that has just logged in knows nothing of the pack until it is opened
        except Exception:
            pass
        pause = os.path.join(self.dir, "pause")
        hang = os.path.join(self.dir, "hang.txt")
        try:
            if os.path.getsize(hang) > 0:
                os.replace(hang, os.path.join(self.dir, "hang.prev.txt"))     # the last brain's stack, kept: the "w" below used to wipe it at every restart
        except OSError:
            pass
        hang_file = open(hang, "w")
        while time.time() < end or (time.time() < end + self.LEAVE_GRACE and self.unsafe_to_leave()):
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
                core = self.core_active()                      # the decision core (task_core.py): only the reflexes, then the core's own tick
                for name in self.far_rules():                  # the brain's RULES with r_far (a far walk under way) before the economy rules
                    if core and name not in self.REFLEXES and not self.core_lets(name):
                        continue
                    if self.stall_skip(name):
                        continue                       # the stall sense backed it off (stall.py)
                    if self.recovery_skip(name):
                        continue                       # materializing: this rule would end it (recovery.py)
                    if self.guard_off(name):
                        continue                       # the loop guard backed this rule off (loopguard.py)
                    if getattr(self, "trip_skip", None) and self.trip_skip(name):
                        continue                       # a trip running past monsters: no rule that stands still (first_trip.trip_skip, feature trip_run)
                    self.current_rule = name
                    if getattr(self, name)():
                        acted = name
                        break
                if acted is None and core:
                    self.current_rule = "task_core"
                    acted = self.core_tick()
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
