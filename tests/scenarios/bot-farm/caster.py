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
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "new-mage-playtest"))
from bot_common import FARM, PROFESSIONS, BotBase, Notes, load_bank, load_features, save_bank  # noqa: E402
from memory import MEMDIR, SharedMemory, cell_of, choose_spot  # noqa: E402
from first_trip import FirstTrip  # noqa: E402
from places import Places  # noqa: E402

import mage_bot  # noqa: E402
import items  # noqa: E402  (the shared item table)
from basics import BasicsMixin  # noqa: E402  (the shared basics: potions, threats, fleeing, selling)
from recovery import RecoveryMixin  # noqa: E402  (death recovery and stamina)
from stall import StallMixin  # noqa: E402  (stall sense)
from progress import ProgressMixin  # noqa: E402  (the progress check; feature progress_check)
from ambition import AmbitionMixin  # noqa: E402  (ambitions)
from planner import PlannerMixin  # noqa: E402  (the planner, measure only)
from bw import BetweenWorldsMixin  # noqa: E402  (Between Worlds plan)
from ground_rates import GroundRateMixin  # noqa: E402  (measured grounds)
from spellbook import SpellbookMixin  # noqa: E402  (know and fill the spellbook)
from far import FarMixin  # noqa: E402  (far service walks, routed and resumable)
from runes import RuneMixin  # noqa: E402  (runes, Mark and Recall; feature runes)
from scribe import ScribeMixin  # noqa: E402  (Inscription: scribe and sell scrolls; feature scribe)
from profit import ProfitMixin  # noqa: E402  (casters who make money: net gold per kill, cheapest kills, carving, leather, learning; feature caster_profit)
from practice import PracticeMixin  # noqa: E402  (practice from the spells the book holds)
from party import PartyMixin  # noqa: E402  (parties; feature party)
from buddy import BuddyMixin  # noqa: E402  (buddy pairs; feature buddy + party)
from pacing import PacingMixin  # noqa: E402  (pacing; features pacing, pacing_walk)
from housegoal import HouseGoalMixin  # noqa: E402  (the A1 house goal; feature house_goal)
from uo import Event  # noqa: E402


from stock import CasterStock  # noqa: E402
from hunt import HuntMixin  # noqa: E402
from lessons import LessonMixin  # noqa: E402  (lessons from NPC trainers; feature lessons)
from castfight import CasterFightMixin  # noqa: E402  (kiting, the spell that fits, Reactive Armor, Greater Heal)
from castdungeon import CasterDungeonMixin  # noqa: E402  (a caster's hunt on a dungeon stay)
from stairhold import StairHoldMixin  # noqa: E402  (the stair hold: fight from a stair's landing, hop through it, Poison first)
from tele import TeleMixin  # noqa: E402  (teleporters: a dungeon trip's door and stairs, the stay's retreat, castdungeon's journeys)
class CasterBot(StairHoldMixin, CasterFightMixin, CasterDungeonMixin, LessonMixin, ProfitMixin, HuntMixin, CasterStock, GroundRateMixin, BetweenWorldsMixin, PlannerMixin, AmbitionMixin, ProgressMixin, StallMixin, RecoveryMixin, HouseGoalMixin, PacingMixin, BuddyMixin, PartyMixin, PracticeMixin, ScribeMixin, RuneMixin, FarMixin, SpellbookMixin, FirstTrip, TeleMixin, BasicsMixin, mage_bot.Bot):
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
        self.base = {"uptime": self.lifetime_s()}             # first_trip's "played under an hour" reads it: a caster keeps no totals.json, so every restart was
                                                              # a new character (no trip offered for an hour after each, 2026-11-08)
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
        self.walks_notice_jumps()

    def walks_notice_jumps(self):
        """Every goto / gotoexact's wait is tele.tele_wait: a jump in position (a teleporter) cancels the walk at once. The hunters get it from
        BotBase._wrap_goto, which mage_bot's Bot never ran, so a caster's walk onto a stair went on after the jump toward its old target on the new
        floor: from Despise's landing stair (5573,628) to 5503,569 and on 25 tiles into the lizardmen of 5504,597, three deaths (2026-11-09 05:29-06:46)."""
        if getattr(self.c, "_walks_notice_jumps", False):
            return
        bot = self
        for name in ("goto", "gotoexact"):
            orig = getattr(self.c, name, None)
            if orig is None:
                continue

            def make(orig):
                def walk(*a, **k):
                    w = orig(*a, **k)
                    first = getattr(w, "wait", None)
                    if first is None:
                        return w
                    return SimpleNamespace(wait=lambda timeout=300.0, poll=0.1: bot.tele_wait(first, timeout, poll), target=getattr(w, "target", None))
                return walk
            setattr(self.c, name, make(orig))
        self.c._walks_notice_jumps = True

    # ---- shared memory: what was met, how fights went, where to hunt ------------------------------------------------

    # the decision log is the hunters' one (bot_common.BotBase), borrowed as plain functions
    dlog = BotBase.dlog
    decision_record = BotBase.decision_record                     # dlog calls these (farmdb decision records; patch_caster_borrow.py)
    decision_context = BotBase.decision_context
    DECISION_EVS = BotBase.DECISION_EVS
    DECISION_OPTIONS = BotBase.DECISION_OPTIONS
    kill_worth_ok = BotBase.kill_worth_ok                         # note_kill_at calls it
    goto_near = BotBase.goto_near
    near_death_spot = BotBase.near_death_spot
    tele_side_of = BotBase.tele_side_of
    note_attacker = BotBase.note_attacker
    peaceful_person = BotBase.peaceful_person
    open_corpse = BotBase.open_corpse
    feature = BotBase.feature
    shop_at = BotBase.shop_at                                     # a vendor's buy list (ride.r_ride's horse; owner 2026-11-08: "don't forget mounts for casters")
    shop_why = BotBase.shop_why                                   # (shop_at asks them)
    wants = staticmethod(BotBase.wants)                           # (a staticmethod there: borrowed plain it took the bot as its first argument)
    SHOP_NEAR = BotBase.SHOP_NEAR                                 # (shop_at reads it)
    ground_items = BotBase.ground_items                    # bones are not containers: the corpse run looks for them here
    CRITTERS = BotBase.CRITTERS
    CRITTER_SKILL = BotBase.CRITTER_SKILL
    BIRDS = BotBase.BIRDS
    critter_skip = BotBase.critter_skip
    carve_room = BotBase.carve_room
    CORPSE_NAMES = BotBase.CORPSE_NAMES
    feathers_pay = BotBase.feathers_pay
    home = BotBase.home
    home_unsafe = BotBase.home_unsafe                             # home() asks it (patch_home_town)
    home_centre = BotBase.home_centre
    home_refuges = BotBase.home_refuges
    # where things are, by role (places.py): the mage bot's hooks point at the gazetteer instead of Britain's constants
    places_ref = Places.places_ref
    find_places = Places.find_places
    where1 = Places.where1
    patrol_spots = Places.patrol_spots
    patrol_tiers = Places.patrol_tiers                                         # patrol_spots asks it (patch_patrol_tiers.py)
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
        if self.profit_on():
            self.profit_settle()
    other_bots = BotBase.other_bots                          # (BotBase's goes through party_filter)
    taken_by_other = BotBase.taken_by_other
    CROWD = BotBase.CROWD
    crowded_here = BotBase.crowded_here                   # r_camp (borrowed) leaves a crowded camp
    mark_crowded = BotBase.mark_crowded
    ground_cap = BotBase.ground_cap

    # facts a new brain takes over from the last one (BotBase.save_facts / load_facts, facts.json in the bot's folder): a far trip, the held ground, the camp, the throttles
    PERSIST = ("ground", "anchor", "anchors_left", "crowded", "pushed_at", "spots_reached", "meat_sold_at", "gear_sold_at", "sold_at", "sell_skip_until", "soldout_until",
               "stocked_at", "bank_balance", "banked_at", "shop_at", "home", "camp_step", "home_region", "birth_town", "unsafe_homes", "rehome_walk", "corpse", "gold_alive", "far", "far_skip", "skill_gap", "killer", "killer_until", "mat_until", "mat_from", "walk_until",
               "pasture", "pasture_hold", "book_shopped", "book_try_read", "goal", "goals_done", "inc_log", "death_log", "res_at", "res_from", "died_at", "stall_off", "persona", "worth_ring", "regions_seen", "dungeon_seen", "milestones", "trips_done", "act_rates", "plan_v", "plan_explored_at", "bw", "walk_rate", "runes", "rune_blanks", "rune_stay", "rune_buy_at", "scribe", "profit_pending", "profit_hold", "leather_sold_at", "profit_field", "fields_worked", "profit_paid_at")
    PERSIST_SETS = ()
    save_facts = BotBase.save_facts
    load_facts = BotBase.load_facts

    def prey(self, within=9):
        others = self.other_bots(within + 4)
        mine = self.fight["serial"] if self.fight else None
        import townguard
        return self.focus_order(self.profit_prey(townguard.filter_prey(self, [m for m in super().prey(within) if not self.taken_by_other(m, others, mine) and not self.critter_skip(m)])))      # not another bot's fight, not a critter; not inside a guarded region (town_guards)

    FOCUS_RANGE = 10              # a targeted spell's range before AOS

    def focus_order(self, ps):
        """The prey in the order a player picks a target in a pack: the one it is already fighting while it is in spell range, then the most hurt in range,
        then the nearest. mage_bot's r_fight takes ps[0], the nearest: in a pack of lizardmen the nearest changed every tick, so the spells were spread over
        all of them and none died (33 caster fights with lizardmen in Despise, no kill, 2026-11-09 01:33-04:21)."""
        if len(ps) < 2:
            return ps
        mine = self.fight["serial"] if self.fight else None

        def key(m):
            d = int(getattr(m, "distance", 99) or 99)
            near = d <= self.FOCUS_RANGE
            pct = float(m.hp_pct) if (getattr(m, "max_hits", 0) or 0) > 0 else 100.0
            return (0 if (m.serial == mine and near) else 1, pct if near else 101.0, d)
        return sorted(ps, key=key)

    def mobs(self, within):
        return [m for m in super().mobs(within) if not self.peaceful_person(m) and not self.killer_spared(m)]

    def dangers(self, within=8):
        """Non-prey that can hurt: a kind that attacks on sight (creature_stats ai, not AI_Animal), or a creature already in war mode (an animal fighting back).
        mage_bot's dangers were every non-prey grey, so a hind or a hart turned non-prey by its flee rate sent the caster stepping away (r_avoid, 18% of the
        casters' last day, 2026-10-29): an animal only fights back."""
        import task_core
        return [m for m in super().dangers(within) if task_core.aggressive(BotBase.mkey(m)) or getattr(m, "in_war_mode", False)]      # people are not prey; the killer goes home (killer_home)

    def read_journal(self):
        import deathsrc
        out = super().read_journal()
        import talk
        for t in out:
            deathsrc.feed(self, t)
            talk.feed(self, t)
            self.note_attacker(t)
            self.book_journal(t)                              # "You do not have that spell!": that spell is marked missing
            if "More reagents are needed" in t:
                # the count was wrong (mage_bot.cast takes one off per cast; the pack is read once a minute): read it again before the next choice.
                # BotMageAdvBR cast Magic Arrow, Greater Heal and Teleport from an empty pack for a minute at 85 mana and died (2026-11-09 05:52)
                self.state_at = 0
                self.__dict__.pop("_casts_now", None)
        return out

    # goods a shop buys stay in the pack for the Butcher and the Tanner (sell_due): mage_bot's bank visit put away everything not on its list, and 54 visits in the
    # casters' logs to 2026-10-29 23:00 banked cut leather or raw meat, where no shop ever buys it
    KEEP = mage_bot.Bot.KEEP + items.GOODS_WORDS
    note_kill_at = BotBase.note_kill_at
    ANCHOR_WAIT = BotBase.ANCHOR_WAIT
    ANCHOR_RADIUS = BotBase.ANCHOR_RADIUS
    anchor_seen = BotBase.anchor_seen
    r_camp = BotBase.r_camp
    revisit_anchor = BotBase.revisit_anchor
    below_my_tier = BotBase.below_my_tier                                      # revisit_anchor asks it (patch_camp_tiers2.py)
    patrol_visit = BotBase.patrol_visit
    home_range = BotBase.home_range
    track_episode = BotBase.track_episode
    close_episode = BotBase.close_episode
    sprint = BotBase.sprint
    in_britain = BotBase.in_britain
    where = BotBase.where                                    # (talk: "where are you")
    chatter = BotBase.chatter                                # (talk: the monster warning; the greet / skill / wares lines)
    sprint_check = BotBase.sprint_check
    RUN_FLOOR, RUN_RESUME = BotBase.RUN_FLOOR, BotBase.RUN_RESUME          # run above 20% of max stamina, not only above half (BotBase.sprint_check)
    set_runmode = BotBase.set_runmode

    def go_town(self):
        if self.in_dungeon_now():
            # mage_bot "backs off" to town when no spell fits: from a dungeon that is a straight walk at a surface point, into Despise's dead-end west
            # room (BotMageBR, 2026-11-09 04:17): kite the attackers instead, else stay for the patrol and the stay's own way out
            att = self.kite_attackers()
            return self.kite_away(att) if att else False
        self.sprint()
        return super().go_town()

    def step_away(self, m, dist=3):
        if self.holding():
            return self.hold_strike(m)                              # at the stair hold: cast (or hop, hold_kite), never a step off it
        att = self.kite_attackers()
        if len(att) >= 2 or self.in_dungeon_now():
            # mage_bot's r_fight side-steps its target whenever it is adjacent: beside four lizardmen BotMageAR side-stepped for a minute, cast nothing
            # (mana 83 throughout) and died (Despise, 2026-11-09 05:29). The pack's kite moves it off all of them (toward the way out, else away, else
            # Teleport), and the next tick casts
            if self.kite_away(att or [m]):
                return True
        self.sprint()
        return super().step_away(m, dist)

    def note_journal_numbers(self, t):
        super().note_journal_numbers(t)
        g = re.search(r"Your skill in (.+?) has increased by (\d+(?:\.\d+)?)\.\s+It is now (\d+(?:\.\d+)?)", t)
        if g and self.fight:
            self.mem.record("gain", scope="prof", skill=g.group(1), action=f"fighting {self.fight['key']}", value=float(g.group(3)), m=self.fight["key"])

    MEAT_KINDS = ("cow", "bull", "deer", "hart", "hind", "sheep", "goat", "chicken", "pig", "boar", "rabbit", "bird")
    def vendor_list(self, vendor, kind):
        """BotBase.vendor_list; a buy list is kept with where it was read (r_resupply's sold-out test)."""
        out = BotBase.vendor_list(self, vendor, kind)
        if kind == "buy" and len(out) >= 2:
            self.__dict__["_last_buy_list"] = (time.time(), (int(self.c.x), int(self.c.y)), list(out))
        return out

    sell_items = BotBase.sell_items                          # the shared sale at a shop (r_sellmeat, basics.py)
    visit_bank = BotBase.visit_bank                          # the shared bank visit (goods back out, a full box, the goal's reserve)
    drop_excess = BotBase.drop_excess                        # the shared shedding when over the weight limit
    junk_in_pack = BotBase.junk_in_pack                      # r_bank reads it
    beat = BotBase.beat                                      # the status heartbeat inside a long step (visit_bank, far walks)
    bank_walk = BotBase.bank_walk                            # the bank visit's own steps and limits (BotBase)
    bank_spot = BotBase.bank_spot
    bank_spread_walk = BotBase.bank_spread_walk
    bank_box_full = BotBase.bank_box_full
    bank_clear = BotBase.bank_clear
    bank_overload_pass = BotBase.bank_overload_pass
    BANK_FULL = BotBase.BANK_FULL
    BANK_SPEECH = BotBase.BANK_SPEECH
    BOX_PRODUCT_CAP = BotBase.BOX_PRODUCT_CAP
    CLEAR_N = BotBase.CLEAR_N
    CLEAR_SHARE = BotBase.CLEAR_SHARE
    HEAVY_THINGS = BotBase.HEAVY_THINGS
    OVERLOAD_ESSENTIAL = BotBase.OVERLOAD_ESSENTIAL
    OVERLOAD_TOOLS = BotBase.OVERLOAD_TOOLS
    FORGE = BotBase.FORGE

    def r_bank(self):
        """The shared bank rule (BotBase.r_bank: rich, heavy with junk, overloaded, a purse to bank in town). Over the weight limit first the shared shedding
        (BotBase.drop_excess: bank from earshot, else the cheapest dropped): a caster cannot take a step overloaded."""
        if self.c.weight > self.c.max_weight and not self.c.ghost and time.time() - self.facts.get("unload_at", 0) >= 30:
            self.facts["unload_at"] = time.time()
            self.drop_excess()
            return True
        r = BotBase.r_bank(self)
        if str(getattr(self, "_far_last", "")).startswith("interrupted"):
            self.facts["bank_fail"] = time.time()                  # an interrupted far walk was retried every step (BotSorcBR, 2026-10-30)
        return r
    note = BotBase.note                                      # sell_items reads these
    travel = BotBase.travel
    read_menu = BotBase.read_menu                            # (scribe.py: the legacy inscription menus)
    close_menus = BotBase.close_menus
    index_of = staticmethod(BotBase.index_of)
    parse_menus = staticmethod(BotBase.parse_menus)

    def can_cast(self):
        """Reagents for at least one attack spell (mana aside: that comes back by resting)."""
        self.refresh_state()
        return self.k.best_attack(self.skill, max(self.c.mana, 40), self.regs) is not None

    def dagger(self):
        return next((i for i in self.c.equipped if any(w in i.name.lower() for w in ("dagger", "knife"))), None) or \
            next((i for i in self.c.backpack if i.name.lower() in ("dagger", "butcher knife", "skinning knife")), None)

    def r_fight(self):
        f = self.fight
        if f:
            try:
                import measured
                g = measured.give_up_s(self, f.get("key"))
            except Exception:
                g = None
            if g and time.time() - f.get("t0", time.time()) > g:
                # the kind's measured ttk_p90 for the casters, as the fighters let go (2026-10-29: BotMageAdvR chased one chicken with its fists for the whole
                # window at 7 of 49 stamina, mana untouched)
                # never reached (no blow, no spell: a chicken in a pen, a rat across a fence): it stays out of reach, so it is left for good, not 300 s
                reached = bool(f.get("reached"))
                self.facts.setdefault("ignore_until", {})[f["serial"]] = time.time() + (300 if reached else 86400)
                if not reached:
                    self.facts.setdefault("kind_unreached", {}).setdefault(f.get("key") or "?", []).append(time.time())   # profit_prey's reach share
                self.ev("give_up", prey=f.get("key"), after=round(time.time() - f.get("t0", time.time())), limit=g, reached=reached)
                self.end_fight("lost")
                return False
        if (self.fight or self.prey(9)) and self.drink_refresh():
            return True
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
        self.fight["reached"] = True
        self.c.attack(t.serial)
        time.sleep(1.4)
        return True

    def r_carve(self):
        """Just killed a farm animal: carve it with the dagger and take the meat."""
        if self.dangers(8) or time.time() - self.facts.get("last_kill_at", 0) > 30:
            return False                                  # (the weight is judged per corpse below by its real carve: BotBase.carve_room)
        carved = self.facts.setdefault("carved", set())
        corpses = [i for i in self.c.containers(within=10 if self.profit_on() else 4) if "corpse" in i.name.lower()
                   and (any(k in i.name.lower() for k in self.MEAT_KINDS) or self.profit_on() and self.profit_carve_kind(i.name))
                   and i.serial not in carved]
        blade = self.dagger()
        if not corpses or not blade:
            return False
        corpse = corpses[0]
        kind_ = items.corpse_kind(corpse.name)
        if not self.carve_room(kind_):
            return False                                  # engine weights (a hide 5 stones, leather and meat 1): the fighters skipped 203 of 302 carves on a 70% line (2026-10-29)
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
        got_cursor = False
        for attempt in range(2):                              # the server's action delay: a knife used 0.1 s after opening the corpse is refused
            time.sleep(1.1)                                    # ("You must wait to perform another action", patch_carve_delay)
            self.c.events.drain()
            self.c.use(blade.serial)
            if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is not None:
                got_cursor = True
                break
        if not got_cursor:
            self.log(f"carve: no knife cursor on {corpse.name} (the server's action delay?)")
            return True
        self.c.target(corpse.serial)
        time.sleep(1.5)
        self.c.use(corpse.serial)
        self.c.wait_for(Event.CONTAINER_CONTENTS, timeout=4)
        try:
            contents = self.c.container(corpse.serial, timeout=5)
        except Exception:
            contents = []
        value, hides = 0, 0
        if self.profit_on():
            value, hides = self.profit_take(contents)              # meat, and the hides while the weight allows; cut into leather at once
            if hides:
                self.profit_cut()
                value += items.HIDE_CUT_VALUE * hides
        else:
            for it in contents:
                if it.name.lower().startswith("raw "):
                    self.c.get_item(it.serial, it.amount if (it.amount or 0) > 1 else None)
                    time.sleep(1.0)
                    value += (it.amount or 1) * items.sale_price(it.name)
        if value:
            kind = items.corpse_kind(corpse.name)
            self.mem.record("loot", cell=cell_of(corpse.x, corpse.y), gold=value, m=kind)
            self.log(f"carved {corpse.name}: meat worth {value} gold")
            self.ev("carve", corpse=corpse.name, meat_value=value, hides=hides)
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
            best.append((meat, cx, cy, cell))
        if not best:
            return None
        best.sort(reverse=True)
        if self.profit_on():
            top = best[:6]                                    # five casters shared one pasture: the least crowded of the best (patch_pasture_harvest)
            low = min(self.caster_load(b[3]) for b in top)
            return random.choice([b for b in top if self.caster_load(b[3]) == low])[1:3]
        return random.choice(best[:4])[1:3]

    PRACTICE = ("Bless", "Arch Cure", "Arch Protection", "Greater Heal", "Magic Reflection", "Reveal")     # harmless on oneself

    def r_practice(self):
        """Between hunts a mage practises: with mana to spare and nothing hostile or huntable near, a harmless spell on itself that can still
        teach Magery (success 35-95%, nearest 60% first), at most once every 20 seconds, keeping half its mana for a fight. Casters fought seldom
        and gained Magery only in fights (+2.9 an hour); this turns walking and resting time into practice, the way UO:R mages trained, and the
        reagents it spends send it shopping when they run low."""
        top = self.c.state.get("maxMana") or 40
        if not self.feature("practice") or self.c.ghost or not self.practice_affordable() or self.c.mana < self.practice_floor(top) or time.time() - self.facts.get("practice_at", 0) < self.practice_gap() or self.dangers(10) or self.prey(9):
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

    REAGENT_ROLES = ("mage", "alchemist", "herbalist")   # SBMage and SBAlchemist sell all eight reagents, SBHerbalist five; 20 a line (ModernUO SBInfo)
    SOLD_OUT_S = 1800                                     # a sold-out seller is not asked again for vendorStock.restockMinutes (30, shard-rules.json)

    def reagent_sellers(self):
        """The reagent sellers on this side of the map, nearest first, the shop it found sold out within SOLD_OUT_S left out."""
        try:
            import gazetteer as gz
        except Exception:
            return []
        here = (int(self.c.x), int(self.c.y))
        out = []
        for role in self.REAGENT_ROLES:
            try:
                ps = gz.near(role, here[0], here[1], n=8, same_side=True)
            except Exception:
                ps = []
            for p in ps:
                q = (int(p["x"]), int(p["y"]))
                if all(max(abs(q[0] - o[0]), abs(q[1] - o[1])) > 4 for o in out):
                    out.append(q)
        now = time.time()
        sold = {k: v for k, v in (self.facts.get("regs_soldout") or {}).items() if float(v) > now}
        self.facts["regs_soldout"] = sold
        out = [q for q in out if not any(max(abs(q[0] - int(k.split(",")[0])), abs(q[1] - int(k.split(",")[1]))) <= 6 for k in sold)]
        return sorted(out, key=lambda q: max(abs(q[0] - here[0]), abs(q[1] - here[1])))

    def mage_shop_xy(self):
        """The nearest reagent seller not found sold out (reagent_sellers), else the Mages' Guild shop (places.py): eight casters each restocking 80 of
        a reagent emptied Britain's shop of all but Blood Moss, and mage_bot.r_resupply asked the empty one again every 4 s for an hour, its kit at
        "8 casts" and the dungeon shut (BotWarlockAR, Karol at 1576,1703, 2026-11-09 03:47-04:37)."""
        s = self.reagent_sellers()
        return s[0] if s else super().mage_shop_xy()

    def r_resupply(self):
        if not self.can_cast() and self.c.gold >= 60 and self.book_has_attack():
            self.facts["last_fail"] = ("reagents", "no reagents for any spell", time.time())    # go and buy them: the mage bot shops after a failed cast
        self.__dict__.pop("_last_buy_list", None)
        self.__dict__["_regs_before"] = dict(getattr(self, "regs", None) or {})
        r = super().r_resupply()
        self.reagent_soldout_check()
        return r

    def reagent_soldout_check(self):
        """After a shop visit: a reagent the plan still has under half of (its line was gone, or its 20 did not cover it) marks that seller sold out
        for SOLD_OUT_S, and the next resupply walks on to the next seller; with every seller out, r_resupply rests until the first restock. At most
        one round of the sellers, whatever the cause (a budget that stops the buy ends it the same way)."""
        got = self.__dict__.pop("_last_buy_list", None)
        if not got:
            return
        _t, xy, lines = got
        try:
            plan = self.reagent_plan()
            regs = self.regs or {}
            before = self.__dict__.pop("_regs_before", None) or {}
            offered = {}
            for line in lines:
                m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
                if m:
                    k = mage_bot.REAGENT_KEYS.get(mage_bot.norm(m.group(4).strip()))
                    if k:
                        offered[k] = offered.get(k, 0) + int(m.group(3))
            # out at this seller: its line gone, or every one on it bought; a line still stocked that the purse did not stretch to is no sell-out
            # (BotWarlockAR with 0 gold carried marked all five sellers out in two minutes, 2026-11-09 05:37-05:38)
            lacking = sorted(k for k, n in plan.items() if regs.get(k, 0) < n // 2
                             and (k not in offered or regs.get(k, 0) - before.get(k, 0) >= offered[k]))
        except Exception:
            return
        if not lacking:
            return
        until = time.time() + self.SOLD_OUT_S
        self.facts.setdefault("regs_soldout", {})[f"{xy[0]},{xy[1]}"] = until
        nxt = self.reagent_sellers()
        self.log(f"resupply: the seller at {xy[0]},{xy[1]} is out of {', '.join(lacking)}; " + (f"next {nxt[0][0]},{nxt[0][1]}" if nxt else "every seller is out: resting"))
        self.ev("regs_soldout", at=list(xy), lacking=lacking, next=list(nxt[0]) if nxt else None)
        if nxt:
            self.facts["resupply_backoff_until"] = 0
            self.facts["last_fail"] = ("reagents", "the seller was sold out", time.time())        # straight on to the next seller
        else:
            soonest = min(float(v) for v in self.facts["regs_soldout"].values())
            self.facts["resupply_backoff_until"] = soonest

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

    def lifetime_s(self):
        """Seconds since the character's first decision record: the caster's playtime for the trips' one-hour guard (a fighter's is totals.json)."""
        try:
            with open(self.decisions_path, encoding="utf-8", errors="ignore") as f:
                first = json.loads(f.readline())
            return max(0.0, time.time() - float(first.get("t") or time.time()))
        except Exception:
            return 0.0

    @property
    def skill_values(self):
        """{skill name: value} as the fighters keep it (the rating, the skill plan, basics read it): a caster's skills are mage_bot's stats["skill_gains"].
        Without it the rating rated every caster as fists at 0 Magery (rating.bot_numbers: "wolves 6.18", "eagle 2.44"), and the dungeon rung's fight test
        refused the lizardmen, so no caster was offered a trip (2026-11-08)."""
        return dict((getattr(self, "stats", None) or {}).get("skill_gains") or {})

    RATING_JOIN = 14          # tiles: an attack-on-sight monster this near the target joins the fight (hunter.HunterBot.RATING_JOIN)
    BITERS_HURT = 60.0        # hunter.HunterBot.BITERS_HURT: rated_prey (borrowed) refuses a new monster under it; "rating: zombie: AttributeError" on every sight

    def is_prey(self, m):
        if self.feature("rating"):
            import hunter
            rated = hunter.HunterBot.rated_prey(self, m)        # feature rating: the rated fight decides, spells and mana included (rating.spell_plan)
            if rated is not None:
                return rated
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
        if self.kite_before_cast(m):
            self.__dict__["_kite_window"] = None                   # (the window is this cast's only: left set, the kit counted "0 casts", 2026-11-09)
            return True                                            # no spell fits before the nearest attacker arrives: it ran (castfight.py)
        if self.buff_before_fight(m):
            return True                                            # Reactive Armor first (castfight.py)
        if self.profit_on() and not self.facts.get("dungeon_hunt") and len(self.kite_attackers()) < 2:
            # (the cheapest way is for a lone animal, not a pack or a dungeon: BotMageBR cast Poison at 3 gold a cast with ten lizardmen on it, 2026-11-09 02:40)
            r = self.profit_attack(m)                              # the cheapest way: fists, Poison and follow, the least gold per damage (profit.py)
            if r is not None:
                return r
        if self.hold_poison(m):
            return True                                            # Poison first on a dungeon stay (stairhold.py)
        self.profit_reached(m)                                     # mage_bot's attack casts at once (its r_fight saw the target in sight)
        try:
            return super().attack(m, train)
        finally:
            self.__dict__["_kite_window"] = None                   # the window is this cast's: can_cast and the kit count see every spell (castfight.py)

    def end_fight(self, outcome):
        f, self.fight = self.fight, None
        if not f:
            return
        self.kite_fight_note(f, outcome)                           # the kite's measure (castfight.py)
        if outcome == "kill":
            self.kills += 1
            self.facts.setdefault("kind_kills", {}).setdefault(f.get("key") or "?", []).append(time.time())             # profit_prey's reach share
            self.note_kill_at(self.c.x, self.c.y)
            self.profit_killed(f)                                  # what the kill cost; what it brought is measured shortly (profit_settle)
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
        if self.c.ghost and self.ghost_out():
            return True                                            # in a dungeon: out by the stairs and the exit first (tele.ghost_out): BotSorcAR's ghost walked at
                                                                   # the healer from inside Despise and stood in its corner at 5384,629 for 46 minutes (2026-11-09)
        return super().r_dead()

    r_corpse = RecoveryMixin.recovery_corpse_run                      # only with blue_self_loot or materializing on (recovery.py)
    RULES = ["r_dead", "r_corpse", "r_cure"] + [r for r in mage_bot.Bot.RULES if r != "r_dead"]       # no r_camp: camping cut casters' gains to nothing

    LESSON_READ_S = 600

    def lesson_have(self):
        """{skill: base} for the lesson gate: a caster keeps no skill table (only Magery), so the client's skill list is read here, every
        LESSON_READ_S seconds at most (skillplan.read: value, base, lock)."""
        now = time.time()
        if now - float(self.__dict__.get("_lesson_read_at", 0) or 0) >= self.LESSON_READ_S:
            self.__dict__["_lesson_read_at"] = now
            try:
                import skillplan
                self.__dict__["_lesson_bases"] = {k: v[1] for k, v in skillplan.read(self).items()}
            except Exception:
                pass
        return dict(self.__dict__.get("_lesson_bases") or {})

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
        return self.caster_heal()                                  # Greater Heal out of reach, Heal or a potion beside one (castfight.py)

    def cure_spell(self):
        """The Cure spell (basics.r_cure's hook): a poisoned caster with nothing next to it cures with mana, and keeps its potions."""
        if self.c.mana >= 6 and self.spell_ok("cure"):
            self.cast("cure", "self")
            self.notes.add("poison", "A poisoned caster cures itself first: a Heal spell does not work while poisoned, and the message does not say to cure.", key="cure:spell")
            return True
        return False

    def heal_spell(self):
        if self.caster_heal():
            return True
        if self.c.mana >= 4 and self.spell_ok("heal") and self.heal_regs():
            self.log(f"emergency heal at {self.c.hp}")
            self.cast("heal", "self")
            return True
        return False

    def fight_back(self, m):
        """No way out (basics.flee_from "trapped"): an attack spell, else fists. A slime has 15-19 hit points, a giant rat 26-39 (creature_stats.json).
        Committed for FLEE_STUCK_S, as basics.fight_back."""
        self.ev("flee_trapped", at=self.mkey(m), hp=self.c.hp)
        self.facts["fight_until"] = max(float(self.facts.get("fight_until", 0) or 0), time.time() + float(getattr(self, "FLEE_STUCK_S", 20)))
        if self.c.mana >= 4 and self.attack(m):
            return True
        self.c.attack(m.serial)
        return True

    def r_avoid(self):
        """A danger it does not take on (dangers(7)): leave it (castfight.caster_avoid), else mage_bot's (fight back when cornered)."""
        ds = self.dangers(7)
        if not ds:
            return False
        if self.caster_avoid(ds):
            return True
        return super().r_avoid()

    def r_flee(self):
        """Low health with something hostile close, in the shared order (basics.py) with the caster's spells: cure first when due; off the bodies beside
        it when two or more stand round it (castfight.kite_away); a Heal potion beside an attacker; the heal spells (castfight.caster_heal: Greater Heal
        out of reach, Heal beside them: first circle, which no blow disturbs before AOS: Spell.OnCasterHurt passes firstCircle false and Spell.Disturb
        returns for a first-circle MagerySpell); else the potion; then run, and fight when trapped. Beside seven undead at Britain's graveyard BotMageAdvBR
        "fled" for 80 s at 85 mana without one heal, because the Heal spell was tried only with nothing adjacent (2026-11-09 05:42-05:43)."""
        danger = self.dangers(10) or self.prey(3)
        if self.hp_pct() >= 40 or not danger:
            return False
        if self.cure_due() and self.potion("cure") is not None:
            return False
        adjacent = self.adjacent_attacker()
        att = self.kite_attackers(4)
        if adjacent and len(att) >= 2 and self.kite_away(att):
            return True
        if adjacent and self.drink_heal("adjacent attacker"):
            return True
        if self.heal_spell():
            return True
        if self.drink_heal("no spell"):
            return True
        self.log(f"fleeing from {danger[0].name} at hp {self.c.hp}")
        if self.flee_from(danger[0]) == "trapped":
            return self.fight_back(danger[0])
        self.end_fight("flee")
        return True

    LEAVE_GAP = 20                # s between two tries of the way out (tele_leave blocks while it walks)

    def r_explore(self):
        if not self.facts.get("dungeon_hunt") and self.in_dungeon_now():
            # no stay (its trip ended: a restart, a death, the time): the way out by the stairs. r_explore's surface field from inside Despise walked
            # BotMageAdvR from the ettin level's stair 140 tiles west into four ettins, dead in a minute (2026-11-09 05:28-05:29)
            now = time.time()
            if now - float(self.__dict__.get("_leave_at", 0) or 0) < self.LEAVE_GAP:
                return False
            self.__dict__["_leave_at"] = now
            self.activity = "out of the dungeon: no stay"
            at = [int(self.c.x), int(self.c.y)]
            ok = bool(self.tele_leave("leave", "no stay"))
            self.ev("dungeon_leave", at=at, ok=ok)
            return True
        if self.facts.get("dungeon_hunt") and not self.c.ghost:
            try:
                import gazetteer
                if gazetteer.side(int(self.c.x), int(self.c.y)) not in (None, "surface"):
                    return False                                   # the stay's patrol is r_cdungeon: profit_explore chose Britain's fields from Despise's west
            except Exception:                                      # room every tick, "not reached in 900 s" (BotMageBR, 2026-11-09 04:16)
                pass
        self.profit_hold_spot()                                    # a patrol spot that paid in the last minutes is kept (feature caster_profit)
        if self.profit_explore():
            return True                                            # a safe field that pays, worked until it stops paying (patch_safe_fields)
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
            import places
            self.cur_spot = places.scatter(getattr(self, "name", ""), *self.cur_spot,          # not the same exact point as every other bot (patch_scatter)
                                           bad=lambda x, y: self.mem.dangerous_cell(cell_of(x, y)) or (1400 <= x <= 1700 and 1550 <= y <= 1770))
        if self.cur_spot is not None and self.ground_closed(*self.cur_spot):
            self.ev("spot_closed", spot=list(self.cur_spot))
            self.cur_spot = None                              # a losing spawner's reach or the undead box: not a patrol point
            return False
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
        self.pack_upkeep()                                   # the pack seen, and an overload shed (basics.BasicsMixin)
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
            f["near_max"] = max(int(f.get("near_max", 0) or 0), sum(1 for d, _n, _k in threats if d <= 10))     # kite_fight's n: the leak by pack size
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
        self.status()

    def status(self, force=False):
        """status.json (the supervisor's liveness check reads its time): every 10 s from observe, and from BotBase.beat inside a long blocking step (a far
        walk, a bank visit), as for every brain."""
        if not force and time.time() - self.last_status < 10:
            return
        self.last_status = time.time()
        s = {
            "name": self.name, "profession": self.pname, "t": time.time(), "uptime": int(time.time() - self.started), "rule": self.last_rule, "activity": self.last_rule,
            "hp": self.c.hp, "max_hp": self.c.max_hp, "mana": self.c.mana, "stam": self.c.stamina, "pos": [self.c.x, self.c.y], "gold": self.c.gold,
            "weight": [self.c.weight, self.c.max_weight], "ghost": self.c.ghost, "kills": self.kills, "deaths": self.deaths,
            "gains": {k.split(":")[0]: v for k, v in self.stats.get("gains", {}).items()}, "skills": self.stats.get("skill_gains", {}), "tick": self.tick_no,
            "all_skills": {k: v for k, v in sorted(self.stats.get("skill_gains", {}).items()) if v > 0},
            "bank": self.facts.get("bank_balance", 0), "net_worth": self.net_worth(), "house_worth": self.house_worth(),
            "region": self.region_name(), "home": (self.home() or {}).get("name"), "features": sorted(self.features), **self.ambition_status(),
        }
        self.write_status_file(s)
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


if "r_house" not in CasterBot.RULES and "r_bank" in CasterBot.RULES:
    CasterBot.RULES.insert(CasterBot.RULES.index("r_bank"), "r_house")                # the house goal: before the bank


if "r_break" not in CasterBot.RULES and "r_bank" in CasterBot.RULES:
    CasterBot.RULES.insert(CasterBot.RULES.index("r_bank") + 1, "r_break")        # pacing: a break at the bank


if "r_trip" not in CasterBot.RULES:
    CasterBot.RULES.insert(CasterBot.RULES.index("r_fight") + 1, "r_trip")      # first_trip
if "r_dungeon_out" not in CasterBot.RULES:
    CasterBot.RULES.insert(CasterBot.RULES.index("r_flee"), "r_dungeon_out")     # first_trip: a dungeon hunt's way out of a pack
if "r_stair" not in CasterBot.RULES:
    CasterBot.RULES.insert(CasterBot.RULES.index("r_dungeon_out"), "r_stair")    # stairhold: the hold's fight and hop, before every danger rule
if "r_cdungeon" not in CasterBot.RULES:
    CasterBot.RULES.insert(CasterBot.RULES.index(("r_ride" if "r_ride" in CasterBot.RULES else "r_trip")) + 1, "r_cdungeon")   # castdungeon: the stay's patrol
if "r_ride" not in CasterBot.RULES:
    CasterBot.RULES.insert(CasterBot.RULES.index("r_trip") + 1, "r_ride")      # ride.py: between outings (r_trip stays right after r_fight)
CasterBot.PERSIST = CasterBot.PERSIST + tuple(k for k in ("ride", "ride_try_at") if k not in CasterBot.PERSIST)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--profession", type=int, default=11)
    ap.add_argument("--for", dest="seconds", type=float, default=3600)
    a = ap.parse_args()
    CasterBot(a.name, a.profession).run(a.seconds)

for _name, _before in (("r_rune_mark", "r_fight"), ("r_rune_buy", "r_resupply")):
    if _name not in CasterBot.RULES:
        CasterBot.RULES.insert(CasterBot.RULES.index(_before), _name)      # runes.py: mark a rune when quiet, buy blank runes (feature runes)


if "r_scribe" not in CasterBot.RULES:
    CasterBot.RULES.insert(CasterBot.RULES.index("r_hunt"), "r_scribe")      # scribe.py: a scribing session at the Mage shop every half hour (feature scribe)


if "r_sell_leather" not in CasterBot.RULES:
    CasterBot.RULES.insert(CasterBot.RULES.index("r_sellmeat") + 1, "r_sell_leather")      # profit.py: leather to the Tanner, after the meat (r_far stays right before r_sellmeat)


if __name__ == "__main__":
    sys.exit(main())
