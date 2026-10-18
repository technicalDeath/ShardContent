"""Pure Mage, Warlock and Sorcerer: the new-mage playtest bot (tests/scenarios/new-mage-playtest/mage_bot.py) run as one of the farm's bots.

    python caster.py --name BotMageA --profession 11 --for 3600

The mage bot keeps its own log, knowledge and stats in a per-bot folder (work/botfarm/<name>/); its notes go to the farm's shared notes.jsonl, tagged with the
bot and profession, and a status.json heartbeat is written every ten seconds for the supervisor's dashboard.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
import time
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "new-mage-playtest"))
from bot_common import FARM, PROFESSIONS, BotBase, Notes, load_bank, load_features, save_bank  # noqa: E402
from memory import MEMDIR, SharedMemory, cell_of, choose_spot  # noqa: E402
from first_trip import FirstTrip  # noqa: E402
from places import Places  # noqa: E402

import mage_bot  # noqa: E402
from recovery import RecoveryMixin  # noqa: E402  (death recovery and stamina)
from stall import StallMixin  # noqa: E402  (stall sense)
from ambition import AmbitionMixin  # noqa: E402  (ambitions)
from planner import PlannerMixin  # noqa: E402  (the planner, measure only)
from bw import BetweenWorldsMixin  # noqa: E402  (Between Worlds plan)
from ground_rates import GroundRateMixin  # noqa: E402  (measured grounds)
from spellbook import SpellbookMixin  # noqa: E402  (know and fill the spellbook)
from far import FarMixin  # noqa: E402  (far service walks, routed and resumable)
from practice import PracticeMixin  # noqa: E402  (practice from the spells the book holds)
from party import PartyMixin  # noqa: E402  (parties; feature party)
from buddy import BuddyMixin  # noqa: E402  (buddy pairs; feature buddy + party)
from pacing import PacingMixin  # noqa: E402  (pacing; features pacing, pacing_walk)
from uo import Event  # noqa: E402


from stock import CasterStock  # noqa: E402
from hunt import HuntMixin  # noqa: E402
class CasterBot(HuntMixin, CasterStock, GroundRateMixin, BetweenWorldsMixin, PlannerMixin, AmbitionMixin, StallMixin, RecoveryMixin, PacingMixin, BuddyMixin, PartyMixin, PracticeMixin, FarMixin, SpellbookMixin, FirstTrip, mage_bot.Bot):
    RICH_GOLD = 900

    def __init__(self, name, profession):
        d = os.path.join(FARM, name)
        os.makedirs(d, exist_ok=True)
        mage_bot.OUT = d
        super().__init__(name, None)
        self.profession = profession
        self.pname = PROFESSIONS.get(profession, str(profession))
        self.notes = Notes(name, self.pname)
        self.mem = SharedMemory(self.pname, name)
        self.mem.news = SharedMemory(self.pname, name, root=MEMDIR + "-newbie")     # newbies' fresh deaths: news for all
        import area_danger                                                          # the area danger map (feature danger_map)
        self.mem.area = area_danger.AreaDanger(self.mem, skill_fn=lambda: getattr(self, "skill", 0.0),
                                               enabled=lambda: self.feature("danger_map"),
                                               on_avoid=lambda cell, why: self.ev("area_avoid", area=cell, why=why))
        self.features = load_features(name)
        self._gold_prev = self.c.gold                         # gold events count from the brain's start, its first tick included
        self.BRITAIN, self.TOWN_BOX = self.home_centre(), self.home_core()     # caster_range centres on the home town (generality step 1)
        self.spots = deque(self.patrol_spots())                                # fixed patrol points of the home (Britain's ten, or learned cells and a ring)
        self.episode = None
        self.work = 0
        if self.c.ghost:
            self.facts["ghost_since"] = time.time()          # already dead when this brain started: not a new death
        self.decisions_path = os.path.join(d, "decisions.jsonl")
        self.last_presence = 0.0
        self.fight = None
        self.cur_spot = None
        self.spot_since = 0.0
        self.dir = d
        self.facts_path = os.path.join(d, "facts.json")
        self.load_facts()                                     # what the last brain knew (a far trip, the ground, the camp)
        self.facts["bank_balance"] = load_bank(d)
        self.started = time.time()
        self.book_prep()                                      # attack options only from the spells the book holds
        self.last_status = 0.0
        self.activity = ""

    # ---- shared memory: what was met, how fights went, where to hunt ------------------------------------------------

    # the decision log is the hunters' one (bot_common.BotBase), borrowed as plain functions
    dlog = BotBase.dlog
    note_attacker = BotBase.note_attacker
    peaceful_person = BotBase.peaceful_person
    open_corpse = BotBase.open_corpse
    feature = BotBase.feature
    ground_items = BotBase.ground_items                    # bones are not containers: the corpse run looks for them here
    CRITTERS = BotBase.CRITTERS
    CRITTER_SKILL = BotBase.CRITTER_SKILL
    BIRDS = BotBase.BIRDS
    critter_skip = BotBase.critter_skip
    home = BotBase.home
    home_centre = BotBase.home_centre
    home_refuges = BotBase.home_refuges
    # where things are, by role (places.py): the mage bot's hooks point at the gazetteer instead of Britain's constants
    places_ref = Places.places_ref
    find_places = Places.find_places
    where1 = Places.where1
    patrol_spots = Places.patrol_spots
    healer_xy = Places.healer_xy
    bank_xys = Places.bank_xys
    mage_shop_xy = Places.mage_shop_xy
    town_xy = Places.town_xy
    home_core = BotBase.home_core
    home_refuges = BotBase.home_refuges
    region_name = BotBase.region_name
    ev = BotBase.ev
    GOLD_EV = BotBase.GOLD_EV
    def after_tick(self, acted):
        BotBase.after_tick(self, acted)
        self.recovery_tail()                                  # the server's death-recovery and stamina lines (recovery.py)
        self.recovery_tick()
    other_bots = BotBase.other_bots                          # (BotBase's goes through party_filter)
    taken_by_other = BotBase.taken_by_other
    CROWD = BotBase.CROWD
    crowded_here = BotBase.crowded_here                   # r_camp (borrowed) leaves a crowded camp
    mark_crowded = BotBase.mark_crowded
    ground_cap = BotBase.ground_cap

    # facts a new brain takes over from the last one (BotBase.save_facts / load_facts, facts.json in the bot's folder): a far trip, the held ground, the camp, the throttles
    PERSIST = ("ground", "anchor", "anchors_left", "crowded", "pushed_at", "spots_reached", "meat_sold_at", "gear_sold_at", "sold_at", "sell_skip_until", "soldout_until",
               "stocked_at", "bank_balance", "banked_at", "shop_at", "home", "camp_step", "home_region", "corpse", "gold_alive", "far", "far_skip", "skill_gap", "killer", "killer_until", "mat_until", "mat_from", "walk_until",
               "pasture", "pasture_hold", "book_shopped", "book_try_read", "goal", "goals_done", "inc_log", "death_log", "res_at", "res_from", "died_at", "stall_off", "persona", "worth_ring", "regions_seen", "dungeon_seen", "milestones", "trips_done", "act_rates", "plan_v", "plan_explored_at", "bw", "walk_rate")
    PERSIST_SETS = ()
    save_facts = BotBase.save_facts
    load_facts = BotBase.load_facts

    def prey(self, within=9):
        others = self.other_bots(within + 4)
        mine = self.fight["serial"] if self.fight else None
        import townguard
        return townguard.filter_prey(self, [m for m in super().prey(within) if not self.taken_by_other(m, others, mine) and not self.critter_skip(m)])      # not another bot's fight, not a critter; not inside a guarded region (town_guards)

    def mobs(self, within):
        return [m for m in super().mobs(within) if not self.peaceful_person(m) and not self.killer_spared(m)]      # people are not prey; the killer goes home (killer_home)

    def read_journal(self):
        import deathsrc
        out = super().read_journal()
        import talk
        for t in out:
            deathsrc.feed(self, t)
            talk.feed(self, t)
            self.note_attacker(t)
            self.book_journal(t)                              # "You do not have that spell!": that spell is marked missing
        return out

    note_kill_at = BotBase.note_kill_at
    ANCHOR_WAIT = BotBase.ANCHOR_WAIT
    ANCHOR_RADIUS = BotBase.ANCHOR_RADIUS
    anchor_seen = BotBase.anchor_seen
    r_camp = BotBase.r_camp
    revisit_anchor = BotBase.revisit_anchor
    patrol_visit = BotBase.patrol_visit
    home_range = BotBase.home_range
    track_episode = BotBase.track_episode
    close_episode = BotBase.close_episode
    sprint = BotBase.sprint
    in_britain = BotBase.in_britain
    where = BotBase.where                                    # (talk: "where are you")
    chatter = BotBase.chatter                                # (talk: the monster warning; the greet / skill / wares lines)
    sprint_check = BotBase.sprint_check
    set_runmode = BotBase.set_runmode

    def go_town(self):
        self.sprint()
        return super().go_town()

    def step_away(self, m, dist=3):
        self.sprint()
        return super().step_away(m, dist)

    def note_journal_numbers(self, t):
        super().note_journal_numbers(t)
        g = re.search(r"Your skill in (.+?) has increased by (\d+(?:\.\d+)?)\.\s+It is now (\d+(?:\.\d+)?)", t)
        if g and self.fight:
            self.mem.record("gain", scope="prof", skill=g.group(1), action=f"fighting {self.fight['key']}", value=float(g.group(3)), m=self.fight["key"])

    MEAT_KINDS = ("cow", "bull", "deer", "hart", "hind", "sheep", "goat", "chicken", "pig", "boar", "rabbit", "bird")
    @property
    def BUTCHER(self):
        return self.where1(("butcher",))
    vendor_list = BotBase.vendor_list

    def can_cast(self):
        """Reagents for at least one attack spell (mana aside: that comes back by resting)."""
        self.refresh_state()
        return self.k.best_attack(self.skill, max(self.c.mana, 40), self.regs) is not None

    def dagger(self):
        return next((i for i in self.c.equipped if any(w in i.name.lower() for w in ("dagger", "knife"))), None) or \
            next((i for i in self.c.backpack if i.name.lower() in ("dagger", "butcher knife", "skinning knife")), None)

    def r_fight(self):
        if self.can_cast():
            return super().r_fight()
        # the farm animals in reach, chosen directly: the mage's own prey test needs a castable spell, so with no reagents nothing was prey
        ps = sorted([m for m in self.c.mobiles(within=9) if m.notoriety == "Gray" and not m.is_dead and any(k in m.name.lower() for k in self.MEAT_KINDS)
                     and abs((m.pos[2] or 0) - self.c.z) <= 14], key=lambda m: m.distance)
        if not ps:
            return False
        t = ps[0]
        d = self.dagger()
        if d and d.serial not in {i.serial for i in self.c.equipped}:
            try:
                self.c.call(f"equip {d.serial}", timeout=6)
            except Exception:
                pass
            time.sleep(0.8)
        if not self.c.war_mode:
            self.c.war(True)
        if not (self.fight and self.fight["serial"] == t.serial):
            if self.fight:
                self.end_fight("kill" if self.target_died(self.fight) else "lost")
            self.fight = {"serial": t.serial, "key": BotBase.mkey(t), "t0": time.time(), "hp0": self.c.hp, "hpmin": self.c.hp, "kills0": self.kills,
                          "mhits": 0, "cell": cell_of(t.x, t.y), "xy": (t.x, t.y), "pct": 100, "corpses0": {c.serial for c in self.c.containers(within=14)}}
            self.dlog("choice", what=f"dagger on {BotBase.mkey(t)}", why="no reagents for any spell: meat for the Butcher, money for reagents")
        self.last_rule = "r_fight"
        if t.distance > 1:
            self.c.goto(t.x, t.y).wait(timeout=3)
            return True
        self.c.attack(t.serial)
        time.sleep(1.4)
        return True

    def r_carve(self):
        """Just killed a farm animal: carve it with the dagger and take the meat."""
        if self.dangers(8) or self.c.weight > self.c.max_weight * 0.7 or time.time() - self.facts.get("last_kill_at", 0) > 30:
            return False
        carved = self.facts.setdefault("carved", set())
        corpses = [i for i in self.c.containers(within=4) if "corpse" in i.name.lower() and any(k in i.name.lower() for k in self.MEAT_KINDS)
                   and i.serial not in carved]
        blade = self.dagger()
        if not corpses or not blade:
            return False
        corpse = corpses[0]
        carved.add(corpse.serial)
        if max(abs(self.c.x - corpse.x), abs(self.c.y - corpse.y)) > 1:
            self.c.gotoexact(corpse.x, corpse.y).wait(timeout=6)
        # open it first: a corpse someone else killed in the last minutes says "Looting this monster corpse will be a criminal act!", and
        # carving it makes the caster a criminal that other players may attack
        opened, forbidden = self.open_corpse(corpse)
        if forbidden:
            self.log(f"left {corpse.name}: someone else's kill (carving it would be a criminal act)")
            return True
        if not opened:
            carved.discard(corpse.serial)                 # "You must wait to perform another action": not opened, so not known to be ours
            time.sleep(1.0)
            return True
        self.c.events.drain()
        self.c.use(blade.serial)
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
            return True
        self.c.target(corpse.serial)
        time.sleep(1.5)
        self.c.use(corpse.serial)
        self.c.wait_for(Event.CONTAINER_CONTENTS, timeout=4)
        try:
            contents = self.c.container(corpse.serial, timeout=5)
        except Exception:
            contents = []
        value = 0
        for it in contents:
            if it.name.lower().startswith("raw "):
                self.c.get_item(it.serial, it.amount if (it.amount or 0) > 1 else None)
                time.sleep(1.0)
                value += (it.amount or 1) * next((p for w, p in (("ribs", 8), ("lamb", 4), ("bird", 4), ("chicken", 3)) if w in it.name.lower()), 3)
        if value:
            kind = re.sub(r"[^a-z]", "", re.sub(r"( corpse| remains)$", "", re.sub(r"^(an?|the) ", "", corpse.name.lower())))
            self.mem.record("loot", cell=cell_of(corpse.x, corpse.y), gold=value, m=kind)
            self.log(f"carved {corpse.name}: meat worth {value} gold")
            self.ev("carve", corpse=corpse.name, meat_value=value)
        return True

    def r_sellmeat(self):
        """Meat to the Butcher: a dozen pieces, or when heavy, or when broke with any."""
        meat = [i for i in self.c.backpack if i.name.lower().startswith("raw ")]
        if not meat or self.dangers(10) or time.time() - self.facts.get("meat_sold_at", 0) < 300:
            return False
        n = sum((i.amount or 1) for i in meat)
        if n < 12 and self.c.weight < self.c.max_weight * 0.7 and self.c.gold >= 60:
            return False
        self.facts["meat_sold_at"] = time.time()
        gold0 = self.c.gold
        far = self.far_front(self.BUTCHER, "sell", 100, n)
        if far:
            self.far_after(far, "sell")
            return True
        self.c.goto(*self.BUTCHER).wait(timeout=100)
        for v in [m for m in self.c.mobiles(within=7) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")]:
            offers = self.vendor_list(v, "sell")
            cart = []
            for line in offers:
                mm = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
                if mm and mm.group(4).strip().lower().startswith("raw ") and int(mm.group(2)) > 0:
                    cart += [mm.group(1), mm.group(3)]
            if cart:
                self.cmd("sell " + " ".join(cart), timeout=10)
                time.sleep(3)
                break
        earned = self.c.gold - gold0
        self.log(f"sold {n} pieces of meat for {earned} gold")
        self.dlog("choice", what="sell meat", why=f"{n} pieces for {earned} gold")
        return True

    DANGER_KINDS = ("orc", "ratman", "skeleton", "zombie", "lizardman", "headless", "troll", "ettin", "ogre", "gazer", "gargoyle", "shade",
                    "wraith", "spectre", "harpy", "lich", "spider", "reaper")

    def safe_pasture(self):
        """For a caster with nothing to cast: a cell around Britain with farm animals seen and none of the kinds that kill a mage with a
        dagger seen there or next door, not a fresh death cell, not the city. None if there is none."""
        self.mem.refresh()
        cells = self.mem.state["world"]["cells"]
        best = []
        for cell, c in cells.items():
            x, y = (int(v) for v in cell.split(","))
            cx, cy = x + 20, y + 20
            if max(abs(cx - 1470), abs(cy - 1620)) > 200 or (1400 <= cx <= 1700 and 1550 <= cy <= 1770):
                continue
            meat = sum(n for k, n in c["sights"].items() if any(m in k for m in self.MEAT_KINDS))
            if meat < 3:
                continue
            # the whole night's sightings count, step-up spawns included, so a pasture is where the dangerous kinds are a small share of what
            # was seen (a quarter at most), and nobody has died there or next door in the last twenty minutes
            danger = sum(n for k, n in c["sights"].items() if any(d in k for d in self.DANGER_KINDS))
            if danger > 0.25 * meat or self.mem.dangerous_cell(cell):
                continue
            best.append((meat, cx, cy))
        if not best:
            return None
        best.sort(reverse=True)
        return random.choice(best[:4])[1:]

    PRACTICE = ("Bless", "Arch Cure", "Arch Protection", "Greater Heal", "Magic Reflection", "Reveal")     # harmless on oneself

    def r_practice(self):
        """Between hunts a mage practises: with mana to spare and nothing hostile or huntable near, a harmless spell on itself that can still
        teach Magery (success 35-95%, nearest 60% first), at most once every 20 seconds, keeping half its mana for a fight. Casters fought seldom
        and gained Magery only in fights (+2.9 an hour); this turns walking and resting time into practice, the way UO:R mages trained, and the
        reagents it spends send it shopping when they run low."""
        top = self.c.state.get("maxMana") or 40
        if not self.feature("practice") or self.c.ghost or self.c.mana < self.practice_floor(top) or time.time() - self.facts.get("practice_at", 0) < self.practice_gap() or self.dangers(10) or self.prey(9):
            return False
        self.refresh_state()
        streak = self.practice_streak()
        import practice
        options = practice.options(self, reserve=(0.4 if streak else 0.5) * top)       # the spells the book holds (never "You do not have that spell!"), safe on oneself, that can still teach
        if not options:
            return False
        pick = options[0]
        name, ok = pick["name"], pick["p"]
        self.facts["practice_at"] = time.time()
        self.activity = f"practising {name}"
        self.log(f"practising {name}{' on itself' if pick['target'] else ''}: success {ok:.0%} at Magery {self.skill:.1f}, mana {self.c.mana}/{top}{' (streak)' if streak else ''}")
        self.cast(name.lower(), pick["target"])
        self.ev("practice", spell=name, success=round(ok, 2), magery=self.skill, gain=round(pick["score"], 4), streak=streak)
        self.notes.add("training", f"A mage practises Magery between hunts by casting {name} on itself; nothing in the game suggests which spells "
                                   "still teach at a given skill.", key=f"practice:{name}")
        return True

    def r_resupply(self):
        if not self.can_cast() and self.c.gold >= 60 and self.book_has_attack():
            self.facts["last_fail"] = ("reagents", "no reagents for any spell", time.time())    # go and buy them: the mage bot shops after a failed cast
        return super().r_resupply()

    def total_gains(self):
        return sum(self.stats.get("gains", {}).values())

    VETO_MIN_FIGHTS = 6
    VETO_VERMIN_HITS = 25

    def memory_veto(self, m, stats):
        """Why the pooled fight memory may NOT turn this kind into prey (the table's own estimate is hopeless), else None. Only with the feature death_loop."""
        if not self.feature("death_loop"):
            return None
        if stats["n"] < self.VETO_MIN_FIGHTS:
            return f"veto: only {stats['n']:.0f} pooled fights"
        a = self.assess(m)
        if not a.get("known"):
            return None
        mon = a.get("monster") or {}
        if "expected_damage" in a:
            if a["expected_damage"] >= self.c.hp:
                return f"veto: the table expects ~{a['expected_damage']:.0f} damage against {self.c.hp} hit points"
            mana = max(self.c.mana, getattr(self.c, "max_mana", 0) or 0, 1)
            if a["mana_needed"] > 2 * mana:
                return f"veto: the kill needs {a['mana_needed']} mana, the mage has {mana}"
        elif (mon.get("hits") or [0, 0])[1] > self.VETO_VERMIN_HITS:
            return f"veto: no spell to cast and it has {mon['hits'][1]} hit points"
        return None

    def is_prey(self, m):
        r = super().is_prey(m)
        key = BotBase.mkey(m)
        final, why = r, ""
        if key in self.mem.deadly_kinds():
            final, why = False, "memory: this kind has killed casters"
        else:
            stats, src = self.mem.fight_stats(key)
            if stats:
                if stats["death_rate"] >= 0.25 or stats["flee_rate"] >= 0.5:
                    final, why = False, f"memory ({src}): {stats['n']:.0f} fights, {stats['death_rate']:.0%} deaths, {stats['flee_rate']:.0%} fled"
                elif not r and stats["death"] < 0.5 and stats["flee_rate"] < 0.2 and stats["avg_dmgpct"] <= 0.4:
                    veto = self.memory_veto(m, stats)
                    if veto:
                        logged = self.facts.setdefault("veto_logged", {})
                        if time.time() - logged.get(key, 0) > 300:
                            logged[key] = time.time()
                            self.dlog("mem", m=key, table=r, final=False, why=veto[:120])
                    else:
                        final, why = True, f"memory ({src}): {stats['n']:.0f} fights, lost {stats['avg_dmgpct']:.0%} on average, none died"
        if final != r:
            logged = self.facts.setdefault("mem_logged", {})
            if time.time() - logged.get(key, 0) > 300:
                logged[key] = time.time()
                self.dlog("mem", m=key, table=r, final=final, why=why[:120])
        return final

    def attack(self, m, train=False):
        if not (self.fight and self.fight["serial"] == m.serial):
            if self.fight:
                self.end_fight("kill" if self.target_died(self.fight) else "lost")
            mon = self.k.monster(m)
            self.fight = {"serial": m.serial, "key": BotBase.mkey(m), "t0": time.time(), "hp0": self.c.hp, "hpmin": self.c.hp, "kills0": self.kills,
                          "mhits": (sum(mon["hits"]) / 2.0) if mon else 0, "cell": cell_of(m.x, m.y), "xy": (m.x, m.y), "pct": 100,
                          "corpses0": {c.serial for c in self.c.containers(within=14)}}
        return super().attack(m, train)

    def target_died(self, f):
        x, y = f.get("xy", (None, None))
        for c in self.c.containers(within=16):
            if "corpse" in c.name.lower() and c.serial not in f.get("corpses0", set()) and x is not None and abs(c.x - x) <= 2 and abs(c.y - y) <= 2:
                return True
        return f.get("pct", 100) <= 25

    def end_fight(self, outcome):
        f, self.fight = self.fight, None
        if not f:
            return
        if outcome == "kill":
            self.kills += 1
            self.note_kill_at(self.c.x, self.c.y)
            self.log(f"kill #{self.kills}: {f['key']}")
        ttk = time.time() - f["t0"]
        if (ttk < 0.3 or outcome == "lost" and ttk < 3) and outcome != "death":
            return
        for scope in ("world", "prof"):
            self.mem.record("fight", scope=scope, m=f["key"], grp=self.mem.grp, outcome=outcome, ttk=round(ttk, 1), dmg=max(0, f["hp0"] - f["hpmin"]), hp=self.c.max_hp, cell=f["cell"], mhits=f["mhits"],
                            skill=round(float(getattr(self, "skill", 0) or 0), 1))

    def r_dead(self):
        first = self.c.ghost and self.facts["ghost_since"] is None
        if first:
            self.facts.pop("anchor", None)
            # the killer: the fight's target, or else the nearest hostile seen in the last ticks (casters often die before a spell lands)
            threats = getattr(self, "recent_threats", [])
            killer = self.fight["key"] if self.fight else (threats[0][2] if threats else None)
            import deathsrc
            src = deathsrc.source(self)
            self.log(f"DEAD at {self.c.x},{self.c.y} (killed by {killer or src['label']}; threats near: {[t[1] for t in threats[:3]]})")
            self.ev("death", killer=killer or src["label"], at=[self.c.x, self.c.y], why=src["why"], dmg=src["dmg"], cues=src["cues"], near=src["near"], **self.vitals())
            self.facts["killer"] = {"name": str(killer or src["label"]), "t": time.time()}      # killer_home (recovery.py)
            self.facts.pop("killer_until", None)
            old = self.facts.get("corpse")
            if not (old and time.time() - old.get("t", 0) < 420):
                self.facts["corpse"] = {"xy": (self.c.x, self.c.y), "t": time.time(), "gold": 0, "tries": 0}   # the corpse run (recovery_corpse_run)
            if self.fight:
                self.end_fight("death")
            elif killer:
                for scope in ("world", "prof"):
                    self.mem.record("fight", scope=scope, m=killer, grp=self.mem.grp, outcome="death", ttk=0, dmg=self.c.max_hp, hp=self.c.max_hp, cell=cell_of(self.c.x, self.c.y),
                                     skill=round(float(getattr(self, "skill", 0) or 0), 1))
            self.mem.record("death", cell=cell_of(self.c.x, self.c.y), killers=[killer] if killer else deathsrc.killers(self, src), at=[self.c.x, self.c.y])
        if self.c.ghost and self.criminal_wait():
            self.activity = "ghost: waiting out the criminal flag (the healer refuses a criminal)"
            time.sleep(3)
            return True
        if self.c.ghost and self.feature("ghost_hint") and time.time() - self.facts.get("ghost_hint_at", 0) < 20:
            self.facts["ghost_hint_at"] = 0                    # the server said the healer cannot see this ghost: war mode, out past 4 tiles, back in
            hx, hy = self.dead_healer()
            if not self.c.war_mode:
                self.c.war(True)
            self.c.goto(hx, hy + 6).wait(timeout=12)
            self.c.goto(hx, hy).wait(timeout=12)
            return True
        return super().r_dead()

    r_corpse = RecoveryMixin.recovery_corpse_run                      # only with blue_self_loot or materializing on (recovery.py)
    RULES = ["r_dead", "r_corpse", "r_cure"] + [r for r in mage_bot.Bot.RULES if r != "r_dead"]       # no r_camp: camping cut casters' gains to nothing

    def r_cure(self):
        """Poisoned: cast Cure if there is mana, else drink the Orange potion. A Heal spell fails on a poisoned character ("You cannot heal yourself in your
        current state."), which is how three casters died in four minutes."""
        if self.c.ghost or not self.c.poisoned or time.time() - self.facts.get("cured_at", 0) < 6:
            return False
        self.facts["cured_at"] = time.time()
        if self.c.mana >= 6 and self.spell_ok("cure"):
            self.cast("cure", "self")
            self.notes.add("poison", "A poisoned caster cures itself first: a Heal spell does not work while poisoned, and the message does not say to cure.", key="cure:spell")
            return True
        pot = next((i for i in self.c.backpack if i.name == "Orange Potion"), None)
        if pot:
            self.c.use(pot.serial)
            time.sleep(1.5)
            return True
        return False

    def label_hook(self, t):
        """The NPC labels ("Ryan the minter") the casters' base drops: talk.py learns who is not a person."""
        import talk
        talk.feed(self, t)

    def dead_healer(self):
        import deathloop
        return deathloop.healer(self)

    def dead_hook(self, event, **kw):
        import deathloop
        return deathloop.hook(self, event, **kw)

    def r_heal(self):
        if self.c.poisoned:
            return False
        return super().r_heal()

    def r_flee(self):
        r = super().r_flee()
        if r:
            self.end_fight("flee")
        return r

    def r_explore(self):
        held = self.facts.get("pasture_hold")
        if not self.can_cast() and held and time.time() < held[2] and (self.cur_spot is None or time.time() - self.spot_since > 240):
            self.cur_spot, self.spot_since = (held[0] + random.randint(-10, 10), held[1] + random.randint(-10, 10)), time.time()
        elif not self.can_cast() and (self.cur_spot is None or time.time() - self.spot_since > 240):
            p = self.safe_pasture()
            if p:
                if p != self.facts.get("pasture"):
                    self.dlog("choice", what="safe pasture", why=f"no spell to cast: farm animals at {p[0]},{p[1]}, no orcs, ratmen or undead seen there")
                self.facts["pasture"] = p
                self.facts["pasture_hold"] = (p[0], p[1], time.time() + 300)
                self.cur_spot, self.spot_since = p, time.time()
        if self.feature("caster_range") and self.cur_spot is not None and self.britain_dist(*self.cur_spot) > self.hunt_leash():
            self.ev("range_drop", spot=list(self.cur_spot), from_britain=self.britain_dist(*self.cur_spot))
            self.cur_spot = None                          # chosen earlier (a pasture, a far ground): too far out for a caster
        if self.cur_spot is None or time.time() - self.spot_since > 240:
            recent = self.facts.setdefault("spots_reached", [])
            center, radius = self.home_range()
            self.cur_spot = self.range_spot() if self.feature("caster_range") else self.revisit_anchor() or choose_spot(self.mem, [tuple(s) for s in self.spots], lambda x, y: any(abs(x - dx) < 70 and abs(y - dy) < 70 for dx, dy in self.facts.get("death_spots", [])),
                                        here=(self.c.x, self.c.y), recent=recent[-4:], center=center, radius=radius)
            self.spot_since = time.time()
        x, y = self.cur_spot
        res = self.c.goto(x, y).wait(timeout=4)
        if abs(self.c.x - x) < 4 and abs(self.c.y - y) < 4 or (res and str(res).startswith(("nopath", "blocked"))):
            if abs(self.c.x - x) < 4 and abs(self.c.y - y) < 4:
                self.patrol_visit(any(self.is_prey(m) for m in self.mobs(14)))
            self.facts.setdefault("spots_reached", []).append((x, y))
            if str(res).startswith("nopath"):
                self.mem.record("blocked", kind="spot", key=cell_of(x, y), ttl=6 * 3600)   # sea or rock: no bot need try it again tonight
            self.cur_spot = None
        return True

    # ---- a home range around Britain (feature "caster_range") ------------------------------------------------------------

    BRITAIN = (1470, 1620)
    TOWN_BOX = (1400, 1550, 1700, 1770)             # the city itself
    CASTER_RANGE = 180                              # grounds are chosen within this many tiles (Chebyshev) of Britain
    CASTER_LEASH = 200                              # a spot further out than this is dropped
    CASTER_PETS = ("cat", "dog", "bird", "magpie", "crow", "raven", "sparrow", "pigeon", "nightingale", "gull")

    def britain_dist(self, x, y):
        return max(abs(x - self.BRITAIN[0]), abs(y - self.BRITAIN[1]))

    def caster_load(self, cell):
        """Other bots on this ground: present in the last five minutes, or on their way (a ground claim, 300 s), as HunterBot.ground_load."""
        now = time.time()
        c = self.mem.state["world"]["cells"].get(cell)
        bots = {b for t, b in (c["pres"] if c else ()) if now - t < 300 and b != self.name}
        for key, r in self.mem.state["world"]["res"].get("ground", {}).items():
            if key.split("#")[0] == cell and r["claim_until"] > now and r["claim_by"] != self.name:
                bots.add(r["claim_by"])
        return len(bots)

    def kind_weight(self, k, deadly):
        """What a sighted kind is worth to a caster as prey (on the fighters' scale, WORTH_UNKNOWN 6): 0 for what has killed casters, the heavy kinds
        and town pets, else 4, up to double where memory has measured Magery gains from fighting it."""
        if k in deadly or any(d in k for d in self.DANGER_KINDS) or any(p in k for p in self.CASTER_PETS):
            return 0.0
        w = self.mem.prey_worth(k, "Magery")
        return 4.0 * (1.0 + min(1.0, w["main"])) if w else 4.0

    def caster_ground(self):
        """The best hunting ground for a caster within CASTER_RANGE of Britain (the fighters' G14, sized for a caster): [score, x, y, cell] or None."""
        self.mem.refresh()
        deadly = self.mem.deadly_kinds()
        recent = self.facts.get("spots_reached", [])[-2:]
        deaths = self.facts.get("death_spots", [])
        now = time.time()
        box = self.TOWN_BOX
        scored = []
        for cell, c in list(self.mem.state["world"]["cells"].items()):
            x, y = (int(v) for v in cell.split(","))
            cx, cy = x + 20, y + 20
            if self.britain_dist(cx, cy) > self.CASTER_RANGE:
                continue
            if x < box[2] and x + 40 > box[0] and y < box[3] and y + 40 > box[1]:
                continue                                  # any part of the city
            if any(abs(cx - rx) < 20 and abs(cy - ry) < 20 for rx, ry in recent) or any(abs(cx - dx) < 50 and abs(cy - dy) < 50 for dx, dy in deaths):
                continue
            if self.mem.dangerous_cell(cell) or self.mem.camp_cell(cell) or not self.mem.usable("spot", cell):
                continue
            if self.facts.get("crowded", {}).get(cell, 0) > now or self.caster_load(cell) >= self.ground_cap(cell):
                continue
            total = sum(c["sights"].values())
            danger = sum(n for k, n in c["sights"].items() if any(d in k for d in self.DANGER_KINDS))
            if total and danger > 0.25 * total:
                continue
            prey = sum(min(n, 10) / 10.0 * self.kind_weight(k, deadly) for k, n in c["sights"].items())
            self.mem._decay_cell(c, now)
            if prey <= 0 and c["kills"] < 0.5:
                continue
            score = (prey + 3.0 * c["kills"] - 4.0 * self.mem.crowd(cell) - max(abs(cx - self.c.x), abs(cy - self.c.y)) / 40.0
                     - self.britain_dist(cx, cy) / 100.0 + self.gr_bonus(cell))                    # what the ground has paid casters of this band
            scored.append((score, cx, cy, cell))
        if not scored:
            return None
        top = max(s[0] for s in scored)               # distance only ranks: even far grounds beat the random fallback
        return random.choice([s for s in scored if s[0] >= top - 0.35 * abs(top)])

    def range_spot(self):
        """The next place to go for a caster in the range cohort: a ground (above), else a spot around Britain, never the frontier ring."""
        h = self.hunt_spot() if self.feature("caster_hunt") else None
        if h:
            score, x, y, sp, good = h
            self.dlog("choice", what="caster hunt spot", why=f"spawner {x},{y} score {score:.1f}: {','.join(good)}")
            cell = f"{x // 40 * 40},{y // 40 * 40}"
            self.mem.record("claim", kind="ground", key=f"{cell}#{self.name}", ttl=300)
            self.ev("caster_ground", ground=cell, score=round(score, 2), from_britain=self.britain_dist(x, y), from_me=max(abs(x - self.c.x), abs(y - self.c.y)),
                    fallback=False, source="spawner", fightable=good)
            return x + random.randint(-6, 6), y + random.randint(-6, 6)
        g = self.caster_ground()
        if g:
            score, x, y, cell = g
            self.dlog("choice", what="caster ground", why=f"cell {cell} score {score:.1f}, {self.britain_dist(x, y)} tiles from Britain")
            self.mem.record("claim", kind="ground", key=f"{cell}#{self.name}", ttl=300)          # the others count it (caster_load, ground_load)
            self.ev("caster_ground", ground=cell, score=round(score, 2), from_britain=self.britain_dist(x, y),
                    from_me=max(abs(x - self.c.x), abs(y - self.c.y)), fallback=False)
            return x + random.randint(-6, 6), y + random.randint(-6, 6)
        deaths = self.facts.get("death_spots", [])
        recent = self.facts.setdefault("spots_reached", [])
        spot = choose_spot(self.mem, [tuple(s) for s in self.spots], lambda x, y: any(abs(x - dx) < 70 and abs(y - dy) < 70 for dx, dy in deaths),
                           here=(self.c.x, self.c.y), recent=recent[-4:], center=self.BRITAIN, radius=self.CASTER_RANGE)
        if self.britain_dist(*spot) > self.CASTER_LEASH:
            for _ in range(8):
                ang, r = random.random() * 2 * math.pi, random.uniform(60, 150)
                spot = (int(self.BRITAIN[0] + r * math.cos(ang)), int(self.BRITAIN[1] + r * math.sin(ang)))
                if not (self.TOWN_BOX[0] <= spot[0] <= self.TOWN_BOX[2] and self.TOWN_BOX[1] <= spot[1] <= self.TOWN_BOX[3]):
                    break
        self.ev("caster_ground", ground=None, score=None, from_britain=self.britain_dist(*spot),
                from_me=max(abs(spot[0] - self.c.x), abs(spot[1] - self.c.y)), fallback=True,
                why=(getattr(self, "hunt_why", None) if self.feature("caster_hunt") else None))
        return spot

    def observe(self):
        self.activity = self.last_rule or ""
        self.sprint_check()
        self.track_episode()
        if time.time() - self.last_presence > 60 and not self.c.ghost:
            self.last_presence = time.time()
            self.mem.record("presence", cell=cell_of(self.c.x, self.c.y), rule=self.last_rule)
            if time.time() - self.facts.get("pos_ev_at", 0) > 180:
                self.facts["pos_ev_at"] = time.time()
                self.ev("caster_pos", from_britain=self.britain_dist(self.c.x, self.c.y), region=self.region_name())
        for m in self.c.mobiles(within=14):
            if m.notoriety in ("Gray", "Criminal", "Enemy", "Murderer") and m.name != "Generic Player" and not self.c.ghost:
                self.mem.sight(BotBase.mkey(m), m.x, m.y)
        threats = sorted((m.distance, m.name, BotBase.mkey(m)) for m in self.mobs(12))
        if self.facts.get("anchor") and any(self.is_prey(m) for m in self.mobs(14)):
            self.anchor_seen()
        if threats:
            self.recent_threats = threats
        f = self.fight
        if f:
            f["hpmin"] = min(f["hpmin"], self.c.hp)
            target = next((m for m in self.c.mobiles(within=16) if m.serial == f["serial"]), None)
            if target and not target.is_dead:
                f["xy"] = (target.x, target.y)
                if target.max_hits:
                    f["pct"] = target.hp_pct
            else:
                self.end_fight("kill" if self.target_died(f) else "lost")
            if self.fight is f and time.time() - f["t0"] > 90:
                self.end_fight("lost")
        super().observe()
        if time.time() - self.last_status < 10:
            return
        self.last_status = time.time()
        s = {
            "name": self.name, "profession": self.pname, "t": time.time(), "uptime": int(time.time() - self.started), "rule": self.last_rule, "activity": self.last_rule,
            "hp": self.c.hp, "max_hp": self.c.max_hp, "mana": self.c.mana, "stam": self.c.stamina, "pos": [self.c.x, self.c.y], "gold": self.c.gold,
            "weight": [self.c.weight, self.c.max_weight], "ghost": self.c.ghost, "kills": self.kills, "deaths": self.deaths,
            "gains": {k.split(":")[0]: v for k, v in self.stats.get("gains", {}).items()}, "skills": self.stats.get("skill_gains", {}), "tick": self.tick_no,
            "all_skills": {k: v for k, v in sorted(self.stats.get("skill_gains", {}).items()) if v > 0},
            "bank": self.facts.get("bank_balance", 0), "net_worth": self.c.gold + self.facts.get("bank_balance", 0),
            "region": self.region_name(), "home": (self.home() or {}).get("name"), "features": sorted(self.features), **self.ambition_status(),
        }
        with open(os.path.join(self.dir, "status.json"), "w", encoding="utf-8") as f:
            json.dump(s, f)
        save_bank(self.dir, self.facts.get("bank_balance", 0))
        self.save_facts()


_r = CasterBot.RULES
for _name, _before in (("r_carve", "r_loot"), ("r_sellmeat", "r_resupply"), ("r_practice", "r_hunt"), ("r_book", "r_practice"), ("r_far", "r_sellmeat")):
    if _name not in _r:
        _r.insert(_r.index(_before), _name)


for _name, _before in (("r_party_heal", "r_carve"), ("r_party", "r_book"), ("r_buddy", "r_party")):
    if _name not in CasterBot.RULES:
        CasterBot.RULES.insert(CasterBot.RULES.index(_before), _name)


if "r_stock" not in CasterBot.RULES:
    CasterBot.RULES.insert(CasterBot.RULES.index("r_resupply"), "r_stock")      # stock.py: reagents to 20, from the bank too


if "r_break" not in CasterBot.RULES and "r_bank" in CasterBot.RULES:
    CasterBot.RULES.insert(CasterBot.RULES.index("r_bank") + 1, "r_break")        # pacing: a break at the bank


if "r_trip" not in CasterBot.RULES:
    CasterBot.RULES.insert(CasterBot.RULES.index("r_fight") + 1, "r_trip")      # first_trip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--profession", type=int, default=11)
    ap.add_argument("--for", dest="seconds", type=float, default=3600)
    a = ap.parse_args()
    CasterBot(a.name, a.profession).run(a.seconds)


if __name__ == "__main__":
    sys.exit(main())
