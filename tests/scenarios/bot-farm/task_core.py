"""The decision core, phase 1 (docs/Bot-Farm-Decision-Core-Plan.md, recommendation 3 of the 2026-10-19 review; feature "task_core"): a hunter holds a
GOAL, runs one TASK at a time with an expected yield and a budget, and ONE progress monitor judges the task. Bots without the feature run the old rule
list unchanged; with it, the reflexes at the top of the list (BotBase.REFLEXES) still run first and everything below them is replaced by core_tick().

THE GOAL (facts["core_goal"]): from the persona (ambition.py) and the candidates goals.py already produces:
    A3 mastery       a skill target: the working skill's next milestone (ambition.STEPS A3)   measure "skill"  (points of the main skill)
    A1 home, A2 livelihood, A5 possessions   a banked sum: the gear piece goals.py picked (its price), else the next A1 milestone   measure "gold"
    A4 adventure     the next rung: kills on the ring (ladder.py reads them)                 measure "kills"
    A6 / A7          the secondary ambition decides; with none, mastery
  Re-picked when done (the measure reached the target), when its candidate disappears (the gear piece is no longer on offer) or every GOAL_LIFE (2 h).
THE TASK (facts["task"]): phase 1 has the hunt task (hunt_tree.py) and a "wait" fallback (stand where it is, WAIT_S, when no area is open). A task carries
  its area, the expected yield per hour of work (kills, gold, skill points), the budget (HUNT_BUDGET, extended once by EXTEND), the counters at its
  start, and the tree's own state; a restarted brain resumes it from facts.
THE CHOICE (choose): every candidate area is scored as expected goal progress per minute, net of the walk (route length from walkroute.py at the bot's
  measured tiles per minute, facts["walk_rate"]) and of the risk (danger.risk per kind times a death cost of DEATH_MIN minutes, and the carried gold
  for a gold goal). Expected yields: the farm.db rate tables RATE_TABLES keyed hunt|group|band|area (rate_update at every task end); with no record
  the PRIOR from the area's spawner contents (creature_stats through knowledge.py, loot_value.json through profit.py, the memory's prey_worth where
  five fights are known). Unknown ground is tried in proportion to how little is known: a Thompson draw, Normal(mean, SPREAD x mean / sqrt(n + PRIOR_N)),
  so an unmeasured area (n = 0) draws wide and a measured one narrow; this replaces fields.py's random scatter and the planner's EXPLORE_EVERY.
  The running task keeps a commitment bonus (COMMIT) and a minimum dwell (DWELL); it is switched only when another candidate beats it by that
  margin, never inside the dwell (event task_switch).
THE MONITOR (monitor, every MONITOR_S): the task's actual yield in the goal's measure against the expected one pro rata of the work time (after
  GRACE_S): on track (actual >= ON_TRACK x expected), under (one extension of EXTEND, then failed "yield"), failed. Two deaths inside one task fail it
  whatever the yield. A failed task bans that task and area for BAN_S (an hour); the tree's own failures rest the area for less (empty 30 min,
  crowded 15 min, unreachable an hour). For task_core bots the stall sense, the loop guard's rule back-offs and the progress check's rethinks are off
  (core_active(); the loop guard's server-refusal reading stays). Events: task_start {task, area, expected, budget_min, walk_min, score, draw},
  task_end {task, area, why, expected, actual, mins, deaths}, task_switch {from, to, why}. Decision records (farmdb): kind "task", the context, every
  candidate with its scores, the chosen one; the outcome (expected, actual, why) is joined at the task's end (farmdb.decision_close).
Rule names: core_tick returns "task:<task>:<step>" as the acted rule, so the scoreboard and the episodes see what the bot did (work, travel, rest).
"""
from __future__ import annotations

import items  # noqa: E402  (the shared item table)
import math
import json
import os
import random
import time

import farmdb

HUNT_BUDGET = 20 * 60.0
EXTEND = 10 * 60.0
DWELL = 5 * 60.0
COMMIT = 0.5                    # the running task's score is raised by this share before a candidate may replace it
MONITOR_S = 60.0
GRACE_S = 420.0                 # work time before the yield is judged (finding the first prey of an area takes minutes)
ON_TRACK = 0.5
UNDER = 0.15                    # below this share of the expected yield the task is failed outright (else "under": one extension)
DEATHS_FAIL = 2
BAN_S = 3600.0
REST_S = {"empty": 1800.0, "stale": 600.0, "crowded": 900.0, "unreachable": 3600.0, "yield": BAN_S, "deaths": BAN_S, "unmet": 1800.0}
PRESSING = 2.0                  # an errand this urgent (no bandages, no arrows, overloaded) interrupts a running hunt
WAIT_S = 120.0
RESTED_SOON = 1200.0            # with nothing open, an area whose rest ends within this many seconds (stale, crowded, empty) is a candidate again; the hour bans are not
GOAL_LIFE = 2 * 3600.0
DEATH_MIN = 30.0                # a death costs this many minutes (the healer, the corpse run, the gold on the corpse) in the score
PAID_REST = 1200.0              # a "yield" task that still made PAID_KILLS kills rests the area this long, not the hour: the ground paid before
PAID_KILLS = 2
GROUND_RADIUS = 320             # the memory's hunting cells this far from home are areas of their own (the rule list's wider ground, step 1 of the A/B read)
GROUND_N = 10
GROUND_APART = 60               # a memory cell this close to a Britain area's spawner is that area, not a ground of its own
CAMP_MIN, CAMP_MAX = 0.0, 0.0    # standing at a spawner for its respawn: none. Live14-15 (2026-10-29) with a 4 s look-around: 673 stops of 4.3 s after roam legs of 8.7 s, 17% of the
                                 # archers' time, and the world file shows the creatures while walking anyway. Before that: a look-around only (the Watcher, 2026-10-29, live 13:31-15:30: a roam minute led to a fight 0.48
                                 # times, a camp minute 0.12; camping was 37% of the ground time. BaseSpawner ticks on its own timer whatever is killed, and the new creature
                                 # appears anywhere in its home range (up to 50 tiles), not where the bot stands; the old cap was 60 s)
SPAWNS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "ModernUO", "Distribution", "Data", "BritanniaRenaissance", "Alpha2b", "Spawns")
WALK_RATE = 55.0                # tiles a minute when the bot has no measured rate yet (the farm's median)
ROUTE_FACTOR = 1.3              # straight distance to route length when walkroute has no grid for the spot
PLAN_BUDGET_S = 2.0             # s of route planning a choice may spend (candidates -> route_length): past it the rest take the straight guess and are planned
                                # at later ticks. A dungeon tour plans a route to every entrance of its dungeon (3-5 s each across the map, longest when there
                                # is none), and BotArchAdvR's brain stood 2 min 35 s in walkroute.plan from candidates, at full health, while a snake killed it
                                # (2026-11-02 23:29-23:31; the dungeon rungs opened when kits began to fill). 2 s: the cadence of a walking bot's danger and
                                # potion checks (first_trip.TRIP_HOT_SLICE)
SPREAD = 0.7                    # the Thompson draw's relative spread: sd = SPREAD x mean / sqrt(n + PRIOR_N)
PRIOR_N = 1.0
ALPHA = 0.3                     # the rate tables' exponential average step
RATE_TABLES = {"kills": "task_kills", "gold": "task_gold", "skill": "task_skill"}
MEASURES = ("kills", "gold", "skill")
PACK_KINDS = ("orc", "ratman", "shade", "wraith", "spectre", "lizardman", "harpy", "skeleton", "zombie")
SPAWNER_KILLS_H = 2.0           # kills an hour one spawner of fightable kinds supplies a bot working the area (the farm: 9 kills a bot-hour over 3-6 spawners)
LOOT_SHARE = 0.33               # of loot_value.json's gold ceiling a corpse pays on average (the shard: 0.15-0.5)
CARVE_REALIZE = 1.0             # measured (the Watcher, 2026-10-29, live14 with carve_room and cutting on the corpse): goods carved in = sold + held at the gold per item the bots got
                                # (leather 4.99, meat 7.84) = 5,809 against a table carve value of 4,415 for the window's kills (1.32; capped at the whole value); 0.5 before. Of loot_value.json's carve value (regular hides as leather at 5, meat at the Butcher) a bot with a blade turns into gold (owner, 2026-10-20:
                                # "low skill hunters can get resources from corpses ... hides that can be cut into leather at 5gp ... feathers, meat")
SKILL_PER_KILL = ((70, 0.15), (80, 0.05), (1e9, 0.01))     # main-skill points a kill is worth before any record, by skill (the Mastery band above 80)
APPROACH_S = 120.0              # seconds a kill costs beyond the time to kill: finding the next one in the area, the walk up, the loot
MAX_TIER = 3                    # the surface tiers; the dungeon rungs are the tiers above (item 5, "The world beyond Britain": open question 2 answered, the rungs open)
RUNG_TIERS = {1: 4, 2: 5, 3: 6}    # rung 1: level 1 of the seven rung dungeons; rung 2: their deeper levels; rung 3: the Hot Zone (spots.py)
RUNG_HP = 90                    # M1 (the Watcher, 2026-10-21: SwordBR set out for the dungeons with 20 of 97 hit points, no gold and no stock, and died twice): health at which a rung journey may begin
WALK_HP = 60                    # and below which no far walk begins at all (the bot rests first)
RUNG_PAY = 10                   # kills on the rung below (the surface's tiers 2 and 3 for rung 1, then the rung's own tier) before the next opens: the rung below must have paid
KIT = {"heal": 10, "refresh": 2, "cure": 15, "bandages": 50, "skill": 80.0}     # the price of entry to a rung (the owner: 2026-10-20 potions, bandages and the weapon skill at 80, no party; 2026-10-21 "10 heals, 15 cures, 50 bandages": a dungeon trip must be worth it)
HEAL_NAMES = items.POTION_NAMES["heal"]          # the era shows the Heal potion as "Yellow Potion"; the simulator names it (items.py)
REFRESH_NAMES = items.POTION_NAMES["refresh"]
CURE_NAMES = items.POTION_NAMES["cure"]          # the Cure potion is the "Orange Potion"
# the live hour's learnings (2026-10-20 20:59-21:59; docs/Bot-Farm-Decision-Core-Evidence.md, "Learnings from the hour")
CALIB_TABLE = "task_calib"      # 1. measured / expected per task kind, group and measure (farm.db rate table, folded at every hunt's end)
CALIB_SEED = {"kills": 0.056, "gold": 0.005, "skill": 0.3}       # the hour: 137 kills against 2,455 expected, 491 gold against 95,975; skill not measured (a guess)
CALIB_N = 2.0                   # the seed counts as this many tasks before the bot's own measurements outweigh it
CALIB_MIN, CALIB_MAX = 0.002, 2.0
MIN_STAY_S = HUNT_BUDGET / 2      # work on a hunt before a bank or sell need (pack under 90%) may end it
DISPLACED = 120                 # tiles from every spot of an arrived hunt beyond which the bot was taken away (far.FAR: from there a walk is a far walk)
HOUSE_GOLD = 16000              # a small house deed (shard-rules.json housePricing.smallHouses): the gold goal of a bot that has reached everything else
EXPECT_CAP = {"kills": 18.0, "gold": 120.0, "skill": 3.0}      # an hour's yield no bot of the farm has reached (live hour: 8.8 kills, 18 gold a bot-hour on average): the largest priors were 37 kills and 2,400 gold
NO_PREY = ("snake",)                    # 2. no loot, and its poison killed three of the nine: fought only when it is on the bot. The horse is prey again (2026-10-29): it
                                        # carves 10 hides and 3 ribs (profit table, 74), and 150 measured fights have no death (ranged 67% kills, melee 90%)
HURT_AT = 34                    # 3. under a third of health with no bandage and no Heal potion: the hunt ends and the bot goes to a town refuge to rest
KILL_PRIOR = (2.0, 1.0)         # 4. a kind's kill share before its fights are known: (kills, escapes) of a made-up three fights
UNDEAD_CASTERS = ("wraith", "spectre", "shade", "lich", "liche", "lichlord")      # 6. a death to one of these closes the ground around it to this bot
DEATH_R = 60                    # tiles around an own death the bot keeps off: two deaths there in DEATH_KEEP, or one to an undead caster
DEATH_KEEP = 6 * 3600.0
RANGED_LOW_STAM = 45            # 6. a ranged bot with less maximum stamina than this leaves a losing fight RANGED_LEAVE points earlier
RANGED_LEAVE = 15
BATCH_URG = 0.5                 # 7. in town after an errand, every errand due at this urgency or more is done before the next hunt (one visit, then a long hunt)
ERRAND_UNMET_REST = 240.0        # supply errands (resupply, arm, fletch) that ended unmet rest this long (the live round 3: ArchAdvR, ArcherCR and BardAdvR sat out 30 minutes with money and no arrows)
CARRY_TIER2 = 2000              # fix D: gold carried above this goes to the bank before a hunt on tier 2 or higher ground (the bank keeps 100 in the pack). Was 120:
                                # BotFairSwordNR walked to the bank 5 times an hour and BotWarAdvR twice in 9 minutes (2026-11-02 00:00-01:00). The core fighters died
                                # 2 times in 117.4 hunting hours (0.017 an hour, 2026-11-01 13:00-01:00), so a 15-minute tour risks 0.43% of what it carries, and a
                                # 2.5-minute bank walk costs about 42 gold at about 1,000 gold an hour (the fighters' net worth an hour, night runner, median 965):
                                # banking first pays from about 9,700 carried. A fifth of that, for a death rate five times this one; r_bank's purse limit still banks
                                # a large purse
UNDEAD_BOX = (1320, 1360, 1480, 1440)    # the undead ground north of Britain (wraiths, spectres): four bots died there in the 2026-10-20 hour
UNDEAD_HP = 120                 # a bot with fewer maximum hit points than this keeps out of the box, whether or not it has died there yet
TOUR2_BONUS = 1.25              # the shared tour (item 5): a tour of tier 4 or more with a buddy at hand scores this much more, and its death risk TOUR2_DIE of the lone one's
TOUR2_DIE = 0.6
TOUR2_NEAR = 40                 # tiles: a party member or buddy candidate this near makes a tour2 candidate
PARTY_EVERY = 5.0               # seconds between the party rule's turns under the core (the rule list is bypassed; invitations and acceptances still need it)
TICK_S = {"fight": 0.4, "pursue": 0.5, "pick": 0.5, "loot": 0.5, "travel": 1.0, "roam": 1.0, "camp": 0.5, "rest": 0.5, "resupply": 0.5}
STEP_CATEGORY = {"travel": "travel", "roam": "travel", "follow": "travel", "heal": "work", "camp": "camp", "pick": "work", "pursue": "work", "fight": "work", "loot": "work", "play": "work", "rest": "rest", "wait": "rest",
                 "sell": "other", "resupply": "other", "fletch": "other", "arm": "other", "ammo": "other", "gather": "other", "bank": "other", "train": "other", "upgrade": "other", "rune_buy": "other", "mark": "other"}


def on(bot):
    """The feature on a brain class that has the core (HunterBot.TASK_CORE; CrafterBot sets it False)."""
    try:
        return bool(getattr(bot, "TASK_CORE", False)) and bool(bot.feature("task_core"))
    except Exception:
        return False


def now():
    return time.time()


# ---- the goal ------------------------------------------------------------------------------------------------------------------------------------

def measure_value(bot, measure):
    """Where the bot stands on a measure: main-skill points, gold carried and banked, kills (lifetime: the totals plus this brain's)."""
    if measure == "skill":
        try:
            return float(bot.skill_values.get(bot.main_skill(), 0.0) or 0.0)
        except Exception:
            return 0.0
    if measure == "gold":
        return float((bot.c.gold or 0) + (bot.facts.get("bank_balance", 0) or 0))
    base = getattr(bot, "base", {}) or {}
    return float((base.get("kills", 0) or 0) + (getattr(bot, "kills", 0) or 0))


def goal_candidates(bot):
    """[{id, kind, measure, target, name}] in the persona's order: the main ambition's, then the secondary's, mastery last."""
    import ambition
    try:
        p = bot.persona()
    except Exception:
        p = {"main": "A3", "second": "A2"}
    out = []
    for a in (p.get("main"), p.get("second"), "A3"):
        if a == "A3":
            v = measure_value(bot, "skill")
            nxt = next((s for s in ambition.STEPS["A3"] if v < s), None)
            if nxt is not None:
                out.append({"id": f"skill:{nxt}", "kind": "skill", "measure": "skill", "target": float(nxt), "name": f"{bot.main_skill()} to {nxt}"})
        elif a in ("A1", "A2", "A5"):
            gear = None
            try:
                import goals
                cands = [c for c in goals.candidates(bot) if c["kind"] == "gear"]
                if cands:
                    gear = max(cands, key=lambda c: (c["value"], -c["cost"]))
            except Exception:
                gear = None
            if gear:
                # the price plus the reserve the upgrade errand keeps (UPGRADE_RESERVE): at the price alone the goal was "done" every tick while the errand could not
                # buy it (BotMaceBR, 2026-10-20: 285 gold against legs at 218, the goal re-picked every 3 s, no purchase)
                target = float(gear["cost"]) + float(getattr(bot, "UPGRADE_RESERVE", 250) or 0)
                out.append({"id": gear["id"], "kind": "gear", "measure": "gold", "target": target, "name": gear["name"], "meta": gear.get("meta", {})})
            v = measure_value(bot, "gold")
            nxt = next((s for s in ambition.STEPS["A1"] if v < s), None)
            if nxt is not None:
                out.append({"id": f"bank:{nxt}", "kind": "bank", "measure": "gold", "target": float(nxt), "name": f"{nxt} gold banked and carried"})
        elif a == "A4":
            v = measure_value(bot, "kills")
            rung = int(v // 25) + 1
            out.append({"id": f"rung:{rung}", "kind": "rung", "measure": "kills", "target": float(rung * 25), "name": f"rung {rung}: {rung * 25} kills"})
    seen, uniq = set(), []
    for c in out:
        if c["id"] not in seen:
            seen.add(c["id"])
            uniq.append(c)
    met = [c for c in uniq if measure_value(bot, c["measure"]) >= c["target"]]
    return [c for c in uniq if c not in met] or uniq            # a goal already reached is not picked again (it would be "done" at once, every tick)


def goal(bot):
    """The active goal, picked or re-picked as the module docstring says."""
    g = bot.facts.get("core_goal")
    t = now()
    cands = goal_candidates(bot)
    if g:
        done = measure_value(bot, g["measure"]) >= g["target"]
        gone = bool(cands) and not g.get("fallback") and not any(c["id"] == g["id"] for c in cands)      # a fallback is never among them: it stays
        # (a fallback counted "gone" at once and was set again every tick: BotFairSwordNR "goal 64000 gold banked and carried" once a second, 1,441 lines
        # and 248 loop-guard firings in 15 min, 2026-11-02 23:59-00:14)
        old = t - g.get("set_at", t) > GOAL_LIFE
        if done or gone or old:
            why = "done" if done else "gone" if gone else "renewed"
            bot.ev("core_goal_end", goal=g["name"], why=why, value=round(measure_value(bot, g["measure"]), 1), target=g["target"])
            g = None
    if not g:
        c = cands[0] if cands else {"id": "skill:100", "kind": "skill", "measure": "skill", "target": 100.0, "name": "mastery", "fallback": True}
        if measure_value(bot, c["measure"]) >= c["target"]:
            # everything reached (the skill at 100, past the last gold step, no gear to buy): the next small house's price in gold (housePricing.smallHouses
            # 16,000) beyond what it has. The mastery fallback was met the moment it was set and re-picked every tick: BotFairSwordNR wrote it 21,267 times
            # (Swordsmanship 100, 29,848 gold banked, 2026-11-01)
            v = measure_value(bot, "gold")
            nxt = (int(v // HOUSE_GOLD) + 1) * HOUSE_GOLD
            c = {"id": f"bank:{nxt}", "kind": "bank", "measure": "gold", "target": float(nxt), "name": f"{nxt} gold banked and carried", "fallback": True}
        g = dict(c, set_at=t, start=round(measure_value(bot, c["measure"]), 1))
        bot.facts["core_goal"] = g
        bot.ev("core_goal", goal=g["name"], measure=g["measure"], target=g["target"], start=g["start"])
        bot.log(f"core: goal {g['name']} ({g['measure']} {g['start']} -> {g['target']})")
    return g


# ---- the expected yield of an area ----------------------------------------------------------------------------------------------------------------

def band(bot):
    try:
        return int(float(bot.skill_values.get(bot.main_skill(), 0) or 0) // 10 * 10)
    except Exception:
        return 0


def group(bot):
    try:
        return bot.gr_group()
    except Exception:
        return "fighter"


def rate_key(bot, task, area):
    return f"{task}|{group(bot)}|{band(bot)}|{area}"


def rates(force=False):
    """{measure: {key: [avg, n, t]}} from farm.db (best-effort; empty tables when the database is unreachable)."""
    out = {}
    for m, tbl in RATE_TABLES.items():
        try:
            out[m] = farmdb.rate_table(tbl)
        except Exception:
            out[m] = {}
    return out


def record_rates(bot, task, area, hours, actual):
    """A task ended: its kills, gold and skill points per hour of work go into the rate tables."""
    if hours <= 0.02:
        return
    key = rate_key(bot, task, area)
    for m in MEASURES:
        try:
            farmdb.rate_update(RATE_TABLES[m], key, float(actual.get(m, 0.0)) / hours, ALPHA)
        except Exception as e:
            bot.log(f"core: rate write failed ({type(e).__name__}: {e})")
            return


def kill_seconds(bot, kind):
    """Seconds a kill of this kind takes this bot: the monster table's hit points over the bot's damage a second."""
    mon = None
    try:
        mon = bot.k.monsters.get(kind)
    except Exception:
        mon = None
    hits = (sum(mon["hits"]) / 2.0) if mon and mon.get("hits") else 40.0
    try:
        dps = max(0.5, float(bot.my_dps()))
    except Exception:
        dps = 2.5
    return hits / dps


def gold_per_kill(bot, kind):
    """What a kill of this kind pays, less the arrows it costs a bow user (2026-10-21: ArchAdvR spent 188 gold of arrows on 12 kills)."""
    return gold_per_kill_raw(bot, kind) - arrow_cost(bot, kind)


def gold_per_kill_raw(bot, kind):
    """The profit table's value of a kill (coins x LOOT_SHARE, plus the carve at CARVE_REALIZE with a blade), else the memory's recorded loot. The record came
    first before 2026-10-29, but it holds coins and meat only (mem.record "loot"): leather, hides and feathers, most of an animal's worth, were left out, so tours
    of harts and cows scored a few gold an hour while carving was realised at 1.32 of the table's value (live14)."""
    try:
        import profit
        e = profit.table().get(kind)
        if e is not None:
            carve = 0.0
            try:
                if bot.carving_blade() is not None:
                    carve = float(e.get("carve") or 0) * CARVE_REALIZE                      # hides cut into leather, meat for the Butcher: the sell errand turns them into gold
            except Exception:
                pass
            return float(e.get("gold") or 0) * LOOT_SHARE + carve
    except Exception:
        pass
    try:
        w = bot.mem.prey_worth(kind, bot.main_skill())
        if w and w.get("gold") is not None and w["n"] >= 5:
            return float(w["gold"])
    except Exception:
        pass
    return 5.0


def skill_per_kill(bot, kind):
    try:
        w = bot.mem.prey_worth(kind, bot.main_skill())
        if w and w["n"] >= 5:
            return float(w["main"]) * float(w["min_per_kill"]) * 0.1      # gain events a minute x minutes a kill x 0.1 point each
    except Exception:
        pass
    s = band(bot)
    return next(v for edge, v in SKILL_PER_KILL if s < edge)


def kit(bot):
    """(ok, detail): the price of entry to a dungeon rung, as the bot's pack and skill stand now."""
    try:
        heal = sum((i.amount or 1) for i in bot.c.backpack if (i.name or "").lower() in HEAL_NAMES)
        refresh = sum((i.amount or 1) for i in bot.c.backpack if (i.name or "").lower() in REFRESH_NAMES)
        cure = sum((i.amount or 1) for i in bot.c.backpack if (i.name or "").lower() in CURE_NAMES)
    except Exception:
        heal, refresh, cure = 0, 0, 0
    try:
        bandages = int(bot.bandages())
    except Exception:
        bandages = 0
    try:
        skill = float(bot.skill_values.get(bot.main_skill(), 0) or 0)
    except Exception:
        skill = 0.0
    ok = heal >= KIT["heal"] and refresh >= KIT["refresh"] and cure >= KIT["cure"] and bandages >= KIT["bandages"] and skill >= KIT["skill"]
    return ok, f"{heal} heal, {refresh} refresh, {cure} cure, {bandages} bandages, {skill:.0f} skill"


def rung_ready(bot):
    """The kit is carried (kit()) AND health is at least RUNG_HP: the check made when the rungs' tiers are offered, when a rung task starts, and at the gate."""
    try:
        return kit(bot)[0] and bot.hp_pct() >= RUNG_HP
    except Exception:
        return False


def rung(bot):
    """The highest dungeon rung open to this bot (facts["rung"]: 0 none, 1 level 1, 2 deeper, 3 the Hot Zone), persisted across restarts."""
    try:
        return int(bot.facts.get("rung", 0) or 0)
    except Exception:
        return 0


def rung_update(bot):
    """The next rung opens once the rung below has paid (RUNG_PAY kills recorded on its tier, facts["rung_kills"]) and the kit is carried; event rung {from, to, why}."""
    r = rung(bot)
    if r >= max(RUNG_TIERS):
        return r
    ok, detail = kit(bot)
    if not ok:
        return r
    rk = bot.facts.get("rung_kills") or {}
    below = (2, 3) if r == 0 else (MAX_TIER + r,)               # rung 1's "rung below" is the surface's upper ground (tiers 2 and 3: a fighter at 80 hunts both); then the rung's own tier
    paid = sum(float(rk.get(str(t), 0) or 0) for t in below)
    if paid >= RUNG_PAY:
        bot.facts["rung"] = r + 1
        bot.__dict__.pop("_spots", None)                           # the spot list is cached ten minutes: the new rung's spots come in at once
        bot.ev("rung", **{"from": r, "to": r + 1, "why": f"{int(paid)} kills on tier {' and '.join(str(t) for t in below)}; kit {detail}"})
        try:
            import think
            think.say(bot, "I'm ready for the dungeons now" if r == 0 else "Ready to go deeper", urgent=True)
        except Exception:
            pass
        bot.log(f"core: rung {r + 1} open (tier {RUNG_TIERS[r + 1]}): {int(paid)} kills on tier {' and '.join(str(t) for t in below)}, kit {detail}")
    return rung(bot)


CAUTIOUS_S = 1800.0             # a failed restock keeps a bot without bandages cautious this long (or until it has bandages again)


def cautious(bot):
    """No bandages and the last restock bought nothing within CAUTIOUS_S: hunt the lowest tier, retreat earlier, rest to full (hunt_tree reads task["cautious"])."""
    return no_heal(bot)                                          # no bandage and no Heal potion: tier 1 only, whether or not a restock was tried (BotMaceBR died five times in tier-3 ground with none)


def record_tier_kills(bot, tier, kills):
    if not kills or kills <= 0:
        return
    rk = bot.facts.setdefault("rung_kills", {})
    rk[str(int(tier or 1))] = float(rk.get(str(int(tier or 1)), 0) or 0) + float(kills)


def calib(bot, task, measure):
    """The measured / expected ratio of a task kind's yield in a measure (CALIB_TABLE), shrunk toward CALIB_SEED (learning 1: the hour's hunts expected 18x the kills)."""
    seed = CALIB_SEED.get(measure, 1.0)
    try:
        r = farmdb.rate_table(CALIB_TABLE).get(f"{task}|{group(bot)}|{measure}")
    except Exception:
        r = None
    if not r:
        return seed
    n = float(r[1])
    v = (n * float(r[0]) + CALIB_N * seed) / (n + CALIB_N)
    return min(CALIB_MAX, max(CALIB_MIN, v))


def record_calib(bot, task, expected, actual, hours):
    """A task's measured / expected ratio per measure into CALIB_TABLE (only measures it was expected to yield, after five minutes of work)."""
    if hours < 5 / 60.0:
        return
    for m in MEASURES:
        exp = float(expected.get(m, 0.0) or 0.0) * hours
        if exp <= 0.05:
            continue
        ratio = max(0.0, float(actual.get(m, 0.0) or 0.0)) / exp
        raw = ratio * calib(bot, task, m)                           # the expectation was already calibrated: the ratio to the uncalibrated one is what is stored
        try:
            farmdb.rate_update(CALIB_TABLE, f"{task}|{group(bot)}|{m}", min(CALIB_MAX, max(0.0, raw)), ALPHA)
        except Exception:
            return


ESCAPE_N, ESCAPE_SHARE = 8, 0.5    # at least this many known fights and a kill share under this (an escape rate of 50% or more, with a prior of two kills to one escape): the kind is no prey
                                   # unless it attacked first (rabbits 82 of 95 escaped, rats 44 of 54, the 2026-10-21 farm hour)


def escapes(bot, kind):
    """True when a kind has escaped most of its known fights: not worth a chase whatever its loot or skill gain says. False for a kind with a measured record
    (measured.entry): its expected value is kill_pct x the loot, escapes priced in, and refusing it here counted them twice (melee hinds kill 87% of fights and
    were turned away as escapers, 2026-10-29)."""
    try:
        import measured
        if measured.entry(bot, kind) is not None:
            return False
    except Exception:
        pass
    try:
        st, _src = bot.mem.fight_stats(kind, min_n=ESCAPE_N)
    except Exception:
        st = None
    if not st:
        return False
    return kill_share(bot, kind) < ESCAPE_SHARE


def kill_share(bot, kind):
    """The share of fights against a kind that end in its death, not its escape (learning 4: rabbits escaped 48 of 64, rats 4 of 4), with a small prior."""
    try:
        st, _src = bot.mem.fight_stats(kind, min_n=1)
    except Exception:
        st = None
    k0, l0 = KILL_PRIOR
    if not st:
        return k0 / (k0 + l0)
    kills, lost = float(st.get("kill", 0) or 0), float(st.get("lost", 0) or 0) + float(st.get("flee", 0) or 0)
    return (kills + k0) / (kills + lost + k0 + l0)


def no_heal(bot):
    """No bandage and no Heal potion in the pack."""
    try:
        if int(bot.bandages()) > 0:
            return False
    except Exception:
        return False
    try:
        return not any((i.name or "").lower() in HEAL_NAMES for i in bot.c.backpack)
    except Exception:
        return True


def hurt_bare(bot):
    """Learning 3: under HURT_AT percent of health with nothing to heal with."""
    try:
        return bot.hp_pct() < HURT_AT and no_heal(bot)
    except Exception:
        return False


def judge_target(bot, m):
    """Learning 5 (orcs 7 of 7 and giant rats 6 of 6 engaged and then fled from): before the first blow, the danger model's say on this target with the hostiles
    standing around it, and its worth with its escape rate. True when it may be fought."""
    import danger
    try:
        kind = bot.mkey(m)
    except Exception:
        return True
    if m.distance <= 1:
        return True                                                  # it is on the bot: the fight is happening whatever is decided
    if kind in NO_PREY:
        return False
    if pull_crowd(bot, m):
        return False                                                 # another attacker would join: pull only one at a time (see pull_crowd)
    try:
        near = sum(1 for o in bot.c.mobiles(within=18) if o.serial != m.serial and max(abs(o.x - m.x), abs(o.y - m.y)) <= 6 and not (o.name or "").startswith("Bot")
                   and getattr(o, "notoriety", "") not in ("Innocent", "Invulnerable") and bot.is_prey(o) and aggressive(bot.mkey(o)))     # only kinds that join a fight:
                   # an AI_Animal only fights back (creature_stats ai), so a hind in a herd of goats is no pack (melee judged_out 0.07 a look, 2026-10-29)
    except Exception:
        near = 0
    try:
        skill = float(bot.skill_values.get(bot.main_skill(), 0) or 0)
        r = danger.risk(bot.mem, kind, skill, near)
    except Exception:
        return True
    return danger.acceptable(r, "prey")


PULL_CLEAR = 14     # tiles: BaseCreature.DefaultRangePerception 16 less the shard's monsterAggro.rangeReduction 2 (MonsterAggro.cs hooks BaseAI.AcquireFocusMob, the scan
                    # every ReacquireDelay 10 s); a fight lasts longer than 10 s (prey_measured ttk_p50 7-24 s), so an attacker within 14 tiles of the fight is likely to join
_CS = {}


def aggressive(kind):
    """A kind that attacks on sight: its AI is not AI_Animal (creature_stats.json, from the engine's constructors; an animal only fights back)."""
    if not _CS:
        try:
            import json as _j
            _CS.update(_j.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "creature_stats.json"), encoding="utf-8")))
        except Exception:
            _CS["_none"] = {}
    return (_CS.get(kind) or {}).get("ai", "AI_Melee") != "AI_Animal"


def pull_crowd(bot, m):
    """The owner (2026-10-29): "The key is to only pull or engage one at a time" (55% of 131 archer deaths had 2+ hostiles within 8 tiles). True when another
    attack-on-sight creature stands within PULL_CLEAR tiles of the target: the pull would bring two. Logged as pull_refused."""
    # monsters notice the shooter, not the target: measure from where the bot will stand to fire (its weapon's reach short of the target, on the line from the
    # target toward the bot; a melee bot stands next to it)
    try:
        import hunt_tree as _ht
        reach = _ht.weapon_reach(bot) if getattr(bot, "ranged", False) else 1
    except Exception:
        reach = 1
    d = max(abs(bot.c.x - m.x), abs(bot.c.y - m.y)) or 1
    k = min(1.0, reach / d)
    fx, fy = m.x + (bot.c.x - m.x) * k, m.y + (bot.c.y - m.y) * k
    try:
        others = [o for o in bot.c.mobiles(within=30) if o.serial != m.serial and not (o.name or "").startswith("Bot")
                  and getattr(o, "notoriety", "") not in ("Innocent", "Invulnerable") and max(abs(o.x - fx), abs(o.y - fy)) <= PULL_CLEAR
                  and aggressive(bot.mkey(o))]
    except Exception:
        return False
    if others:
        key = m.serial
        seen = bot.__dict__.setdefault("_pull_refused", {})
        if now() - seen.get(key, 0) > 120:
            seen[key] = now()
            try:
                bot.ev("pull_refused", prey=bot.mkey(m), others=[bot.mkey(o) for o in others][:4], n=len(others))
            except Exception:
                pass
        return True
    return False


def own_death_spots(bot):
    """[(x, y, killer, t)] of this bot's own deaths in DEATH_KEEP (facts["own_deaths"], noted at each death by note_deaths)."""
    t = now()
    return [d for d in (bot.facts.get("own_deaths") or []) if t - float(d[3]) < DEATH_KEEP]


def note_deaths(bot):
    """A new death of this bot: where and to what, for the ground it keeps off (learning 6)."""
    d = float(getattr(bot, "deaths", 0) or 0)
    seen = bot.__dict__.get("_deaths_seen")
    bot.__dict__["_deaths_seen"] = d
    if seen is None or d <= seen:
        return
    try:
        x, y = bot.death_xy()
    except Exception:
        x, y = int(bot.c.x), int(bot.c.y)
    killer = str((bot.facts.get("killer") or {}).get("name") or "")
    lst = [list(v) for v in own_death_spots(bot)] + [[int(x), int(y), killer, now()]]
    bot.facts["own_deaths"] = lst[-12:]
    bot.__dict__.pop("_spots", None)


PROVISIONED_FLOORS = {"arrows": 20, "bandages": 8, "heal": 1, "refresh": 1, "cure": 1}      # a kit item under its floor: event provisioned_low (potions: none left)


def provisioned(bot):
    try:
        return bool(bot.feature("provisioned"))
    except Exception:
        return False


def kit_block(bot):
    """{arrows, bandages, heal, refresh, cure, weapon} carried now, for status.json and the provisioned_low events."""
    def n(names):
        return sum((i.amount or 1) for i in bot.c.backpack if (i.name or "").lower() in names)
    try:
        cur, item = bot.weapon_now()
        weapon = (item.name if item is not None else None)
    except Exception:
        weapon = None
    try:
        state = bot.weapon_state()
    except Exception:
        state = None
    return {"arrows": int(bot.ammo()), "bandages": int(bot.bandages()), "heal": n(HEAL_NAMES), "refresh": n(REFRESH_NAMES), "cure": n(CURE_NAMES), "weapon": weapon, "weapon_state": state}


def provisioned_watch(bot):
    """Every tick: the kit block into status.json; in a provisioned bot also the event provisioned_low {item, have} when a kit item that was above its floor falls under it
    (once every 10 minutes per item), so the Watcher knows when to top up."""
    try:
        k = kit_block(bot)
        st = getattr(bot, "status_extra", None)
        if not isinstance(st, dict):
            st = bot.status_extra = {}
        st["kit"] = k
        if not provisioned(bot):
            return
        seen = bot.facts.setdefault("kit_seen", {})
        last = bot.__dict__.setdefault("_kit_low_at", {})
        for item, floor in PROVISIONED_FLOORS.items():
            have = k.get(item, 0)
            if have >= floor:
                seen[item] = True
            elif seen.get(item) and now() - last.get(item, 0) > 600:
                last[item] = now()
                bot.ev("provisioned_low", item=item, have=have, floor=floor, kit=k)
    except Exception:
        pass


CORPSE_RUN_CAP = 375            # tiles from home beyond which a corpse run is refused: the farthest ground a bot works (spots.REACH_WIDE), so a death on its own ground
                                # is gone back for. Was 200 ("the Watcher's choice", no source) against tours out to 320: five deaths on 2026-11-01/02 at 234-371 tiles
                                # left the whole kit on the corpse (BotWarAdvR: bow, 50 bandages and every potion; 32,278 banked bought them again). The killer and
                                # repeat-death refusals below still hold, and Between Worlds hides a returning player until it acts
DEATH_ROBE_HUE = 2301           # UOContent Items/Clothing/OuterTorso.cs DeathRobe: Hue 2301, LootType Newbied, one per resurrection: not for sale
ARROW_GOLD = 2.0                # an arrow's price, for the cost of a kill
ARROW_DEFAULT = 2.0             # arrows a kill costs when this bot has not measured the kind (the Watcher's measure: 1.6-2.3 on tier-1 prey)


NOVICE_LIFT = 0.66              # data/configuration/shard-rules.json noviceCombat.hitLiftStrength (NoviceCombatService.LiftedChance: chance x (1 + strength x (1 - skill/100)), capped at 1)
MISS_ODDS = 0.05                # shots with no damage before a target is let go: the smallest N with (1 - p)^N under this (the Watcher's rule, the owner 2026-10-21: numbers from the engine)
_WRESTLE = {"t": None}


def hit_chance(bot, kind):
    """Chance that one shot of this bot hits this kind: the engine's pre-AOS BaseWeapon.CheckHit, (attack skill + 50) / ((defender wrestling + 50) * 2), capped at 1, then the novice lift
    (NoviceCombatService.LiftedChance). The kind's wrestling is the middle of its creature_stats.json range; unknown kinds give None."""
    if _WRESTLE["t"] is None:
        try:
            _WRESTLE["t"] = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "creature_stats.json"), encoding="utf-8"))
        except Exception:
            _WRESTLE["t"] = {}
    e = _WRESTLE["t"].get(kind)
    if not e or not e.get("wrestling"):
        return None
    w = sum(e["wrestling"]) / len(e["wrestling"])
    try:
        skill = float(bot.skill_values.get(bot.main_skill(), 0) or 0)
    except Exception:
        skill = 0.0
    p = min(1.0, (skill + 50.0) / ((w + 50.0) * 2.0))
    if p < 1.0 and skill < 100.0:
        p = min(1.0, p * (1.0 + NOVICE_LIFT * (1.0 - skill / 100.0)))
    return p


def miss_limit(bot, kind):
    """(N, p): shots with no damage after which a target is let go, the smallest N with (1 - p)^N < MISS_ODDS; (None, None) for a kind without data."""
    p = hit_chance(bot, kind)
    if p is None:
        return None, None
    if p >= 1.0:
        return 1, p
    n = 1
    while (1.0 - p) ** n >= MISS_ODDS and n < 40:
        n += 1
    return n, p


CORPSE_REPEAT_R = 60            # tiles: an earlier death of this bot this near the corpse, within CORPSE_REPEAT_S, makes the ground one it does not walk back into
CORPSE_REPEAT_S = 3600.0


def killer_kind(name):
    """A recorded killer's kind: "a bone mage (beside it when hit)" -> "bonemage". The death cause's note in brackets made it "bonemagebesideitwhenhit",
    which no measured kind matches (BotArchAdvR, 2026-11-02 01:24)."""
    import re
    n = re.sub(r"\s*\(.*\)\s*$", "", str(name or "").lower())
    return norm_kind(re.sub(r"^(an?|the)\s+", "", n.strip()))


def corpse_refusal(bot, x, y):
    """(why, dist, killer) when a corpse run to (x, y) is refused, else None. A provisioned bot makes none (its kit is replaced and the corpse holds nothing worth the risk); every
    core bot refuses a corpse beyond CORPSE_RUN_CAP from home, a killer whose measured death_pct is at the group's cut-off, a killer that has killed this bot before, and ground where
    this bot died within the last hour."""
    try:
        killer = killer_kind((bot.facts.get("killer") or {}).get("name"))
    except Exception:
        killer = ""
    try:
        hx, hy = bot.home_centre()
        dist = max(abs(int(x) - int(hx)), abs(int(y) - int(hy)))
    except Exception:
        dist = 0
    if provisioned(bot):
        return "provisioned", dist, killer
    if dist > CORPSE_RUN_CAP:
        return "beyond the corpse-run cap", dist, killer
    try:
        import measured
        if killer and measured.deadly(bot, killer):
            return "killer's measured death rate", dist, killer
    except Exception:
        pass
    deaths = sorted(own_death_spots(bot), key=lambda d: float(d[3]))
    earlier = deaths[:-1]                                         # the last one is this death
    if killer and any(killer in killer_kind(d[2]) or killer_kind(d[2]) in killer for d in earlier if killer_kind(d[2])):
        return "that killer has killed it before", dist, killer
    t = now()
    if any(t - float(d[3]) < CORPSE_REPEAT_S and max(abs(d[0] - x), abs(d[1] - y)) <= CORPSE_REPEAT_R for d in earlier):
        return "it died near here within the hour", dist, killer
    return None


def avoided(bot, kinds):
    """True when any of the spot's kinds is on this bot's own learned-avoid list (hunter.avoid_types, normalised names)."""
    try:
        av = getattr(bot, "avoid_types", None) or ()
        if av and hasattr(bot, "avoids"):
            return any(bot.avoids(norm_kind(k), ground=True) or bot.avoids(k, ground=True) for k in kinds)   # a measured animal is judged by its expected value, not the list (2026-10-29)
        return bool(av) and any(norm_kind(k) in av or k in av for k in kinds)
    except Exception:
        return False


def arrow_cost(bot, kind):
    """Gold of arrows a kill of this kind costs a bow user: the arrows this bot has measured on the kind (arrows_used), else ARROW_DEFAULT, at ARROW_GOLD each; 0 for others."""
    try:
        if not bot.bow_kind():
            return 0.0
        n, tot = (bot.facts.get("arrow_use") or {}).get(kind, (0, 0.0))
        return ARROW_GOLD * (tot / n if n >= 3 else ARROW_DEFAULT)
    except Exception:
        return 0.0


def drop_robes_tick(bot):
    """Every 5 minutes, when nothing hostile is near: death robes (hue 2301, newbied) in the pack are dropped (they were held for hours: the sell errand that drops them never ran)."""
    try:
        if now() - bot.__dict__.get("_robe_tick", 0) < 300 or bot.threats(8):
            return
        bot.__dict__["_robe_tick"] = now()
        import errands
        errands.drop_death_robes(bot)
        errands.drop_unsellable(bot)                  # spined leather and hides: no vendor buys them (items.no_buyer)
    except Exception:
        pass


def box_bot(bot):
    """True for a bot the undead box is closed to (fewer than UNDEAD_HP maximum hit points)."""
    try:
        return int(bot.c.max_hp) < UNDEAD_HP
    except Exception:
        return False


def in_box(bot, x, y, pad=0):
    """True when (x, y) lies in the undead box (grown by pad tiles) and this bot may not go there. Used by the roam points, the prey picked and pursued, the walks and the flight."""
    return (UNDEAD_BOX[0] - pad <= x <= UNDEAD_BOX[2] + pad and UNDEAD_BOX[1] - pad <= y <= UNDEAD_BOX[3] + pad) and box_bot(bot)


def box_exit(bot, x, y):
    """The nearest point just outside the box from (x, y), when (x, y) is inside it (for a bot it is closed to); else (x, y) itself."""
    if not in_box(bot, x, y):
        return x, y
    opts = [(x - UNDEAD_BOX[0], (UNDEAD_BOX[0] - 8, y)), (UNDEAD_BOX[2] - x, (UNDEAD_BOX[2] + 8, y)),
            (y - UNDEAD_BOX[1], (x, UNDEAD_BOX[1] - 8)), (UNDEAD_BOX[3] - y, (x, UNDEAD_BOX[3] + 8))]
    return min(opts)[1]


def box_watch(bot, acted=None):
    """Events box_entered {task, rule, xy, max_hp} when a bot the box is closed to steps into it, box_left when it comes out (so a read shows how it got there)."""
    try:
        inside = in_box(bot, int(bot.c.x), int(bot.c.y))
    except Exception:
        return
    was = bot.__dict__.get("_in_box", False)
    if inside == was:
        return
    bot.__dict__["_in_box"] = inside
    task = bot.facts.get("task") or {}
    try:
        bot.ev("box_entered" if inside else "box_left", task=task.get("task"), step=task.get("step"),
               xy=[int(bot.c.x), int(bot.c.y)], max_hp=int(bot.c.max_hp), ghost=bool(bot.c.ghost), walking_to=str(task.get("area") or "")[:40])
    except Exception:
        pass


def death_ground(bot, x, y):
    """Ground this bot keeps off: the undead box north of Britain for a bot under UNDEAD_HP hit points, two of its own deaths within DEATH_R, or one to an undead caster
    (the wraiths north of Britain killed four)."""
    try:
        if in_box(bot, x, y):
            return True
    except Exception:
        pass
    near = [d for d in own_death_spots(bot) if max(abs(d[0] - x), abs(d[1] - y)) <= DEATH_R]
    return len(near) >= 2 or any(any(u in norm_kind(d[2]) for u in UNDEAD_CASTERS) for d in near)


def norm_kind(s):
    return "".join(ch for ch in str(s).lower() if ch.isalpha())


def kind_risk(bot, kind, tier=1):
    """{die, flee, win} for a kind at this bot's skill (danger.py): a pack of two or more companions for the pack kinds on tier-2+ ground (the live A/B's
    deaths were tier-3 packs scored as one companion), one companion for a pack kind on tier 1, none otherwise."""
    import danger
    try:
        skill = float(bot.skill_values.get(bot.main_skill(), 0) or 0)
        near = (2 if tier >= 2 else 1) if any(p in kind for p in PACK_KINDS) else 0
        return danger.risk(bot.mem, kind, skill, near)
    except Exception:
        return {"die": 0.15, "flee": 0.2, "win": 0.65}


_AGGR = {"t": None}


def aggressive_kind(kind):
    """True for a creature that attacks a player on sight (fightmodes.json: Closest, Weakest, Strongest or Evil; "Aggressor" animals fight back only once attacked); unknown kinds count as aggressive."""
    if _AGGR["t"] is None:
        try:
            _AGGR["t"] = {k: (v or {}).get("mode") for k, v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fightmodes.json"), encoding="utf-8")).items()}
        except Exception:
            _AGGR["t"] = {}
    mode = _AGGR["t"].get(kind)
    return mode in (None, "None", "Closest", "Weakest", "Strongest", "Evil")


def hands_only(bot):
    return bool(bot.facts.get("fists")) or unarmed(bot)


def unarmed(bot):
    """A melee fighter with no weapon of its skill in hand or pack (and no money for one, or the arm errand would have it away): it fights like fix C's broke archer, with what
    its hands can kill, on tier 1. Cached 20 s."""
    hit = bot.__dict__.get("_unarmed")
    if hit and now() - hit[0] < 20:
        return hit[1]
    try:
        v = (not bot.bow_kind()) and bot.weapon_state() in ("none", "wrong")
    except Exception:
        v = False
    bot.__dict__["_unarmed"] = (now(), v)
    return v


def weapon_note(bot):
    """Event weapon_state {state, wielded, skill, why} on the first tick and whenever the state or the wielded weapon changes (the before and after of the weapon batch)."""
    try:
        state = bot.weapon_state()
        cur, item = bot.weapon_now()
        wielded = (item.name if item is not None else None)
    except Exception:
        return
    key = (state, wielded)
    if bot.__dict__.get("_weapon_noted") == key and now() - bot.__dict__.get("_weapon_noted_at", 0) < 600:
        return
    bot.__dict__["_weapon_noted"] = key
    bot.__dict__["_weapon_noted_at"] = now()
    why = {"ok": "a weapon of its skill", "none": "nothing of its skill wielded or carried", "wrong": "a weapon of another skill",
           "worn": "the wielded weapon is badly worn (the shard's notice)"}.get(state, state)
    try:
        bot.ev("weapon_state", state=state, wielded=wielded, skill=bot.main_skill(), why=why, gold=int(bot.c.gold or 0), bank=int(bot.facts.get("bank_balance", 0) or 0))
    except Exception:
        pass


def fightable(bot, kind, deadly, tier=1):
    """A kind this bot would hunt here: no NO_PREY kind, worth something once its escapes are counted (hunter.worth_kind x kill_share) and acceptable to the danger model.
    A bot in fist mode (an archer with no arrows and no money) takes what its hands can kill and that does not run, at tier 1 (fix C): livestock it can carve and sell."""
    if kind in NO_PREY or escapes(bot, kind):
        return False
    try:
        import measured
        measured.announce(bot)
        if not measured.allowed(bot, kind)[0]:
            return False                                          # the measured kill and death rates of the bot's group (prey_measured.json)
    except Exception:
        pass
    if bot.facts.get("fists") or unarmed(bot):
        import danger
        try:
            return bool(bot.fist_prey(kind)) and kind not in deadly and danger.acceptable(kind_risk(bot, kind, tier), "prey")
        except Exception:
            return False
    try:
        import measured
        n_ = measured.net(bot, kind)
    except Exception:
        n_ = None
    if n_ is not None:
        if n_ <= 0:
            return False                                        # a measured kind: its expected gold a fight against its solo death cost (measured.py), as prey() and worth_it() judge it,
    else:                                                       # not the old worth floor (no carving in it): the floor turned melee spots away 51 times in live12 (2026-10-29)
        try:
            if bot.worth_kind(kind, deadly) * kill_share(bot, kind) / (KILL_PRIOR[0] / sum(KILL_PRIOR)) <= getattr(bot, "WORTH_FLOOR", 1.5):
                return False                                    # nothing, an unmeasured kind the loot table rates at the floor (birds), or one that mostly escapes (rabbits): no ground
        except Exception:
            return False
    import danger
    return danger.acceptable(kind_risk(bot, kind, tier), "prey")


def prior(bot, area, deadly):
    """{kills, gold, skill, die, kinds} an hour of work on this area, from its spawner contents (before any record)."""
    spawners = area.get("spawners", [])
    tier = int(area.get("tier") or 1)
    kinds = sorted({k for sp in spawners for k in sp[3] if fightable(bot, k, deadly, tier)})
    if not kinds:
        return None
    supply = SPAWNER_KILLS_H * sum(1 for sp in spawners if any(k in kinds for k in sp[3]))
    ttk = sum(kill_seconds(bot, k) for k in kinds) / len(kinds)
    demand = 3600.0 / (ttk + APPROACH_S)
    kills_h = max(0.5, min(supply, demand))
    gold = sum(gold_per_kill(bot, k) for k in kinds) / len(kinds)
    skill = sum(skill_per_kill(bot, k) for k in kinds) / len(kinds)
    die = sum(kind_risk(bot, k, tier)["die"] for k in kinds) / len(kinds)
    return {"kills": kills_h, "gold": gold * kills_h, "skill": skill * kills_h, "die": die, "kinds": kinds}


_DELAYS = {"t": None}


def spawn_delays():
    """{(x, y): (min_s, max_s)} of the canonical spawners (spawners.py), read once; {} when the folder is not there."""
    if _DELAYS["t"] is None:
        out = {}
        try:
            import spawners as sp
            for _f, s in sp.canonical(os.path.abspath(SPAWNS)):
                loc = s.get("location") or [0, 0, 0]
                try:
                    mn = float(str(s.get("minDelay") or "00:05:00").split(":")[-2]) * 60 + float(str(s.get("minDelay") or "0:05:00").split(":")[-1])
                    mx = float(str(s.get("maxDelay") or "00:10:00").split(":")[-2]) * 60 + float(str(s.get("maxDelay") or "0:10:00").split(":")[-1])
                except (ValueError, IndexError):
                    mn, mx = 300.0, 600.0
                out[(int(loc[0]), int(loc[1]))] = (mn, mx)
        except Exception:
            out = {}
        _DELAYS["t"] = out
    return _DELAYS["t"]


def spawn_delay_at(x, y):
    """(min_s, max_s) of the nearest canonical spawner within 15 tiles, else (300, 600)."""
    best = None
    for (sx, sy), (mn, mx) in spawn_delays().items():
        d = max(abs(sx - x), abs(sy - y))
        if d <= 15 and (best is None or d < best[0]):
            best = (d, mn, mx)
    return (best[1], best[2]) if best else (300.0, 600.0)


def camp_seconds(x, y, last_kill=None, t=None):
    """How long to stand at a spawner with nothing in sight: a look-around (CAMP_MIN) when nothing was killed there lately, or, once a respawn is due (the last
    kill there plus the spawner's minimum delay), until its longest delay has passed (CAMP_MAX at most). A player waits for a respawn that is coming, not for
    one that is minutes away (the first steps-1-and-2 run stood three minutes at spawners with five to ten minute delays and killed a third less)."""
    t = t or now()
    mn, mx = spawn_delay_at(x, y)
    if not last_kill or t - last_kill > mx + CAMP_MAX:
        return CAMP_MIN
    due = last_kill + mn
    if t < due - CAMP_MIN:
        return CAMP_MIN                                          # not due yet: look around and move on, come back
    return max(CAMP_MIN, min(CAMP_MAX, last_kill + mx - t + CAMP_MIN))


def ground_areas(bot, ts):
    """The memory's best hunting cells as areas of their own (name "ground <cell>", one spawner: the cell's centre and the kinds sighted there), away from the
    Britain areas' spawners: the rule list's r_explore ground, which the first live A/B showed the core lacked (12% of its time with no open area)."""
    import fields
    from memory import cell_center
    out = []
    try:
        home = bot.home_centre()
        cells = bot.mem.hunting_cells(near=home, radius=GROUND_RADIUS, n=GROUND_N)
    except Exception:
        return out
    taken = [(sp[0], sp[1]) for a in fields.areas() for sp in a.get("spawners", [])]
    try:
        import places
        tier_at = places.area_tier_at
    except Exception:
        tier_at = None
    for score, cell in cells:
        if score <= 0:
            continue
        cx, cy = cell_center(cell)
        if any(max(abs(cx - x), abs(cy - y)) <= GROUND_APART for x, y in taken):
            continue
        try:
            if bot.spot_in_city(cx, cy):
                continue
        except Exception:
            pass
        c = bot.mem.state["world"]["cells"].get(cell) or {}
        kinds = sorted(k for k, n in (c.get("sights") or {}).items() if n >= 1)
        if not kinds:
            continue
        tier = (tier_at(cx, cy) if tier_at else None) or 1
        if tier not in ts:
            continue
        out.append({"name": f"ground {cell}", "tier": tier, "spawners": [[int(cx), int(cy), 20, kinds]], "ground": True})
    return out


def walk_rate(bot):
    try:
        return min(120.0, max(30.0, float(bot.facts.get("walk_rate") or WALK_RATE)))
    except Exception:
        return WALK_RATE


def route_length(bot, dest):
    """Tiles of the route from the bot to dest (walkroute.plan with the far-walk penalty, cached per 40-tile cell and destination), else the straight
    distance times ROUTE_FACTOR; None when walkroute says there is no land route."""
    here = (int(bot.c.x), int(bot.c.y))
    cell = (here[0] // 40, here[1] // 40, int(dest[0]), int(dest[1]))
    cache = bot.__dict__.setdefault("_core_routes", {})
    hit = cache.get(cell)
    if hit and now() - hit[0] < 600:
        return hit[1]
    straight = max(abs(here[0] - dest[0]), abs(here[1] - dest[1]))
    length = straight * ROUTE_FACTOR
    if time.time() - float(bot.__dict__.get("_plan_t0", time.time()) or time.time()) > PLAN_BUDGET_S:
        return length                                              # the choice's planning budget is spent: the straight guess, not cached (planned at a later tick)
    try:
        import walkroute
        try:
            pen = bot.far_penalty()
        except Exception:
            pen = None
        r = walkroute.get().plan(here, (int(dest[0]), int(dest[1])), pen)
        if r is None:
            same = True
            try:
                import gazetteer as gz
                same = gz.side(here[0], here[1]) == gz.side(int(dest[0]), int(dest[1]))
            except Exception:
                pass
            length = None if (straight > 60 and same) else length                # another side of the map: a teleporter joins them (travel.py); the straight guess stands
        else:
            length = float(r["steps"])
    except Exception:
        pass
    if len(cache) > 400:
        cache.clear()
    cache[cell] = (now(), length)
    return length


def draw(mean, n, rng):
    """One Thompson draw of a rate whose record holds n observations (0: the prior alone)."""
    sd = SPREAD * max(mean, 0.05) / math.sqrt(n + PRIOR_N)
    return max(0.0, rng.gauss(mean, sd))


def tiers(bot):
    """The tiers this bot hunts: the surface tiers (the fields' tiers by weapon skill and the patrol tiers by combat skill, up to MAX_TIER) and, for a bot whose
    rung is open AND who carries the kit now (the price of entry is paid every time), the rungs' tiers up to its rung."""
    out = set()
    for fn in ("field_tiers", "patrol_tiers"):
        try:
            out |= set(getattr(bot, fn)())
        except Exception:
            pass
    out = {t for t in out if t <= MAX_TIER} or {1}
    if cautious(bot) or bot.facts.get("fists") or unarmed(bot):
        return {min(out)}                                      # no bandages and the restock failed: the lowest ground only, until the pack is stocked again
    r = rung_update(bot)
    if r and rung_ready(bot) and bot.feature("dungeon_tours"):
        # (feature dungeon_tours, 2026-11-03: off for every bot until the journeys are fixed. With kits filling the rungs opened, and in some 30
        # dungeon tours no bot reached a door: Covetous's door at 2384,837 cannot be walked to, and the tele journeys through the Britain moongate
        # cross the undead ground south of Britain. Three died on the way: BotFairSwordNR 22:54, BotFencerBR 01:20, BotRangerAR 01:59 to a
        # skeletal knight beside a bone mage and a spectre at 1359,1929. The rung bookkeeping, kills and kit, goes on.)
        out |= {RUNG_TIERS[k] for k in range(1, r + 1)}
    return out


def bans(bot):
    b = bot.facts.setdefault("core_bans", {})
    t = now()
    for k in [k for k, until in b.items() if until <= t]:
        del b[k]
    return b


def ban(bot, task, area, why, secs=None):
    bans(bot)[f"{task}|{area}"] = now() + (secs if secs is not None else REST_S.get(why, BAN_S))


def candidates(bot, g, rng=None, rested=False, relax=0):
    """The hunt candidates for the goal g: tours of spots (spots.tours), the banned spots left out (rested=True: only the hour bans hold; relax: spots.RELAX_MAX). Best first."""
    import spots
    rng = rng or random
    bot.__dict__["_plan_t0"] = time.time()                       # route_length's planning budget for this choice (PLAN_BUDGET_S)
    b = bans(bot)
    if rested:
        b = {k: until for k, until in b.items() if until - now() > RESTED_SOON}
    banned = {k.split("|", 1)[1] for k in b if k.startswith("spot|")}
    try:
        if provisioned(bot) and bot.bow_kind() and bot.ammo() == 0:
            bot.__dict__["_spot_why"] = {"no arrows: top-up": 1}  # the no-ground report names it (it read as an empty reason, 2026-10-29)
            return []                                              # a provisioned archer out of arrows waits near town for the top-up (no fists, no shop)
    except Exception:
        pass
    out = spots.tours(bot, g, rng, banned, relax)
    out += tour2_candidates(bot, out)
    out.sort(key=lambda c: -c["score"])
    return out


def partner_near(bot):
    """(name, x, y) of a party member, else a buddy candidate (buddy.py), within TOUR2_NEAR tiles; None without one."""
    try:
        names = set(bot.party_names()) if hasattr(bot, "party_names") else set()
        if not names and hasattr(bot, "buddy_on") and bot.buddy_on():
            names = {p["name"] for p in bot.buddy_candidates()}
        if not names:
            return None
        for o in bot.other_bots(TOUR2_NEAR):
            if o[0] in names:
                return o
    except Exception:
        return None
    return None


def tour2_candidates(bot, tours):
    """The shared tour (item 5): with a partner near, every tour of tier TIER_RUNG1 or more comes again as a "tour2" (one pulls, one heals, the loot by turns:
    hunt_tree.Buddy) at TOUR2_BONUS the score and TOUR2_DIE the risk; a partner already on a tour2 (its published task, buddy.json "core") is joined."""
    import spots
    p = partner_near(bot)
    if not p:
        return []
    out = []
    for c in tours:
        if (c.get("tier") or 1) >= spots.TIER_RUNG1:
            out.append(dict(c, task="tour2", partner=p[0], role="leader", score=round(c["score"] * TOUR2_BONUS, 4), die=round(c["die"] * TOUR2_DIE, 3), area=f"{c['area']} with {p[0]}"))
    try:
        import buddy
        best = max((c["score"] for c in tours), default=0.01)
        for peer in buddy.peers(bot.name):
            core = peer.get("core") or {}
            if peer["name"] == p[0] and core.get("task") == "tour2" and core.get("spots"):
                c = {"expected": {}, "walk_min": 0.0, "die": 0.0, "n": 0, "draw": 0.0, "mean": 0.0, "minutes": HUNT_BUDGET / 60.0, "budget": HUNT_BUDGET}
                c.update(core)
                c.update(task="tour2", partner=p[0], role="follower", join=True, score=round(max(best, float(core.get("score") or 0)) * TOUR2_BONUS * 1.1, 4))
                out.append(c)
    except Exception:
        pass
    return out


# ---- the task --------------------------------------------------------------------------------------------------------------------------------------

def counters(bot):
    return {"kills": measure_value(bot, "kills"), "gold": measure_value(bot, "gold"), "skill": measure_value(bot, "skill"),
            "deaths": float(getattr(bot, "deaths", 0) or 0)}


def actual(bot, task):
    c0, c1 = task["start"], counters(bot)
    return {m: round(c1[m] - c0[m], 2) for m in MEASURES}


def work_hours(task):
    """Hours since the task's work began (arrival at the area), the budget's clock."""
    t0 = task.get("arrived")
    return max(0.0, (now() - t0) / 3600.0) if t0 else 0.0


def start_task(bot, g, cand, options, why="chosen"):
    t = now()
    task = {"task": cand["task"], "area": cand.get("area"), "spots": cand.get("spots", []), "t0": t, "arrived": None,
            "budget": cand.get("budget") or (HUNT_BUDGET if cand["task"] == "hunt" else WAIT_S),
            "extended": False, "expected": cand.get("expected", {}), "walk_min": cand.get("walk_min", 0.0), "score": cand.get("score", 0.0), "start": counters(bot),
            "goal": g["id"], "measure": g["measure"], "judge": cand.get("judge") or g["measure"], "checked": t, "state": {}, "decision": None, "tour": cand.get("tour"),
            "tier": cand.get("tier"), "side": cand.get("side", "surface"), "partner": cand.get("partner"), "role": cand.get("role")}
    if task["side"] and task["side"] != "surface":
        try:
            bot.tele_allow(task["side"], seconds=task["budget"] + 1800.0)          # the reason to be on that side (tele.py): the goto wrappers may cross to it
        except Exception:
            pass
    if task["task"] in ("hunt", "tour2") and cautious(bot):
        task["cautious"] = True
    try:
        task["decision"] = farmdb.decision_open(bot.name, getattr(bot, "pname", None), "task", f"{task['task']}:{task['area']}", dict(bot.decision_context(), goal=g["name"], measure=g["measure"]),
                                                [{k: c[k] for k in ("task", "area", "score", "draw", "mean", "walk_min", "die", "n")} for c in options[:12]])
    except Exception as e:
        bot.log(f"core: decision record failed ({type(e).__name__}: {e})")
    bot.facts["task"] = task
    bot.__dict__.pop("_core_tree", None)
    bot.ev("task_start", task=task["task"], area=task["area"], expected=task["expected"], budget_min=round(task["budget"] / 60), walk_min=task["walk_min"], score=task["score"],
           draw=cand.get("draw"), why=why, goal=g["name"], judge=task["judge"], options=len(options), tier=task.get("tier"), side=task.get("side"), partner=task.get("partner"),
           earning=("fists" if bot.facts.get("fists") else "unarmed" if unarmed(bot) else None), kinds=(cand.get("kinds") or [])[:6])
    try:
        import think
        think.task_start(bot, task, cand)
    except Exception:
        pass
    others = ", ".join(f"{c['area']} {c['score']:.3f}" for c in options[:4] if c is not cand)
    bot.log(f"core: task {task['task']} {task['area'] or ''} for {g['name']} (score {task['score']:.3f}, {task['walk_min']} min walk, expected {task['expected']}; others: {others or 'none'})")
    return task


def end_task(bot, task, why):
    t = now()
    act = actual(bot, task)
    hours = work_hours(task)
    mins = round((t - task["t0"]) / 60, 1)
    deaths = counters(bot)["deaths"] - task["start"]["deaths"]
    if task["task"] in ("hunt", "tour2") and task.get("arrived"):
        record_rates(bot, "hunt", task["area"], hours, act)
        # tour_rank: the estimate is an hour of the whole tour, walk included (spots.tours: minutes = walk + legs + fights), so the calibration compares the
        # actual with it over the same hours; over the work hours alone the ratio read 0.89 for archers making a third of their estimate (2026-11-01)
        record_calib(bot, "hunt", task.get("expected") or {}, act, hours + (float(task.get("walk_min") or 0.0) / 60.0 if bot.feature("tour_rank") else 0.0))
        record_tier_kills(bot, task.get("tier") or 1, act.get("kills", 0))        # the rung below pays for the next (rung_update)
        rung_update(bot)
    supply = task["task"] in ("resupply", "ammo", "arm", "fletch", "gather")
    if supply and why != "done":
        # the reason a supply errand did not finish, for the Watcher's trace (the 2026-10-21 round: BardAdvR and ArcherCR sat out an hour with gold and no arrows: the ban was "unreachable"'s 3600 s)
        try:
            bot.ev("errand_unmet", task=task["task"], why=why, step=(task.get("state") or {}).get("step"), reason=bot.facts.pop("errand_reason", None), xy=[int(bot.c.x), int(bot.c.y)],
                   gold=int(bot.c.gold or 0), bank=int(bot.facts.get("bank_balance", 0) or 0), dest=(task.get("spots") or [None])[0])
        except Exception:
            pass
        if task["task"] == "ammo":
            n = bot.facts.setdefault("ammo_unmets", {})
            n[why] = n.get(why, 0) + 1
            if n[why] >= 2 and task.get("spots"):                      # twice in a row for the same reason: the next Bowyer, not this one again
                sp = task["spots"][0]
                bot.facts.setdefault("ammo_bad_shop", {})[f"{sp[0]},{sp[1]}"] = time.time() + 1800
                n.clear()
                bot.ev("ammo_route_changed", shop=[sp[0], sp[1]], why=why)
    if why in REST_S or (supply and why != "done"):
        paid = why == "yield" and act.get("kills", 0) >= PAID_KILLS
        short = ERRAND_UNMET_REST if supply else None          # a supply errand that found nothing to buy, or could not get there, is tried again in minutes (240 s at most), not half an hour or an hour
        for sid in task.get("tour") or [task["area"]]:
            ban(bot, "spot" if task.get("tour") else task["task"], sid, why, PAID_REST if paid else short)
    if task.get("tour"):
        import spots
        tk = (task.get("state") or {}).get("tour_kills") or {}
        for k, visited in enumerate(task.get("spots") or []):
            if str(k) in (task.get("state") or {}).get("visited_set", {}) or k in ((task.get("state") or {}).get("visited") or []):
                spots.record_visit(bot, spots.cell_of(visited[0], visited[1]), tk.get(str(k), 0))
    if why == "unreachable" and task.get("spots") and task["task"] in ("hunt", "tour2"):
        try:
            from memory import cell_of as _cell
            here = (bot.c.x, bot.c.y)
            near = min(task["spots"], key=lambda s: max(abs(here[0] - s[0]), abs(here[1] - s[1])))
            bot.mem.record("blocked", kind="spot", key=_cell(near[0], near[1]), ttl=6 * 3600)        # every bot's choice skips it for six hours
        except Exception:
            pass
    if task["task"] in ("hunt", "tour2"):
        try:                                                      # per tour: minutes walking to it, minutes on its ground, kills, spawners (the Watcher/owner, 2026-10-21: where does the hour go)
            arr = task.get("arrived")
            st_ = task.get("state") or {}
            bot.ev("tour_stats", area=task["area"], walk_min=round(((arr or t) - task["t0"]) / 60, 1), ground_min=round(((t - arr) / 60) if arr else 0.0, 1), kills=act.get("kills", 0),
                   spawners=len(task.get("spots") or []), visited=len(st_.get("visited") or []), why=why, tier=task.get("tier"))
        except Exception:
            pass
    bot.ev("task_end", task=task["task"], area=task["area"], why=why, expected=task["expected"], actual=act, mins=mins, work_min=round(hours * 60, 1), deaths=deaths,
           tier=task.get("tier"), side=task.get("side"))
    bot.log(f"core: task {task['task']} {task['area'] or ''} ended ({why}) after {mins} min: actual {act}, expected {task['expected']}, deaths {int(deaths)}")
    try:
        import think
        think.task_end(bot, task, why, act)
    except Exception:
        pass
    if task.get("decision"):
        try:
            farmdb.decision_close(task["decision"], {"why": why, "expected": task["expected"], "actual": act, "mins": mins, "deaths": deaths}, t)
        except Exception:
            pass
    bot.facts["task"] = None
    bot.__dict__.pop("_core_tree", None)


def judge_measure(measure, expected, budget=HUNT_BUDGET):
    """The measure a hunt task is judged and scored by: the goal's, unless its expected yield in one budget is under one unit (a fighter above 80 gains its
    skill by Mastery's daily allowance, not by any one task): then the task's kills, the thing hunting yields."""
    if measure == "kills" or float(expected.get(measure, 0.0) or 0.0) * budget / 3600.0 >= 1.0:
        return measure
    return "kills"


def expected_so_far(task):
    m = task.get("judge") or task["measure"]
    return float(task["expected"].get(m, 0.0)) * work_hours(task)


def monitor(bot, task, g, rng=None):
    """Once a minute: on track, under (one extension), failed; two deaths fail. Returns the why that ended the task, else None."""
    t = now()
    if t - task.get("checked", 0) < MONITOR_S:
        return None
    task["checked"] = t
    deaths = counters(bot)["deaths"] - task["start"]["deaths"]
    if deaths >= DEATHS_FAIL:
        return "deaths"
    if task["task"] not in ("hunt", "tour2"):
        return "done" if t - task["t0"] >= task["budget"] else None
    press = pressing_need(bot)
    if press is not None and press["task"] in ("bank", "sell") and t - (task.get("arrived") or t) < MIN_STAY_S:
        try:
            heavy = bot.c.weight >= bot.c.max_weight * 0.9
        except Exception:
            heavy = True
        if not heavy:
            # a purse or a part-full pack waits for the hunt's first MIN_STAY_S of work: 9 of 17 switches in 20:35-21:05 went to the bank or a shop after tours
            # of 7-9 minutes with packs 53-64% full, while tours that ran their course made 0.52 kills a minute against 0.27 for those cut short (2026-11-01)
            press = None
    if press is not None:
        bot.__dict__["_core_next"] = press
        bot.ev("task_switch", **{"from": task["area"], "to": press["task"], "why": press["detail"]})
        try:
            import think
            think.switch(bot, {"resupply": "restocking", "sell": "trading loot", "bank": "to the vault", "rest": "resting"}.get(press["task"], press["task"]),
                         "the pack needs it" if press["task"] != "rest" else "too hurt")
        except Exception:
            pass
        bot.log(f"core: {press['task']} first ({press['detail']}): the hunt at {task['area']} ends")
        return "switch"
    if not task.get("arrived"):
        return None                                                  # the tree judges the walk (unreachable)
    sp = task.get("spots") or []
    if sp and min(max(abs(bot.c.x - s[0]), abs(bot.c.y - s[1])) for s in sp) > DISPLACED:
        # an errand took the bot back to town after it arrived, and the roam's short walks cannot cover a far walk: BotArchAdvR stood 11 minutes at the
        # Bowyer, 190-211 tiles from its tour's spots, its roam asking for a route 21 times a minute (2026-11-01 19:27-19:42). The task ends (no ban) and
        # the next one travels properly
        bot.log(f"core: {task['area']} is {min(max(abs(bot.c.x - s[0]), abs(bot.c.y - s[1])) for s in sp)} tiles off after arriving: the hunt ends, travel again")
        return "displaced"
    worked = t - task["arrived"]
    judge = task.get("judge") or task["measure"]
    exp, act = expected_so_far(task), actual(bot, task)[judge]
    verdict = "on track"
    if worked >= GRACE_S and exp > 0:
        ratio = act / exp
        verdict = "on track" if ratio >= ON_TRACK else "under" if ratio >= UNDER else "failed"
    if verdict == "failed" or (verdict == "under" and task.get("extended")):
        return "yield"
    if verdict == "under" and not task.get("extended"):
        task["extended"] = True
        task["budget"] += EXTEND
        bot.ev("task_extend", task=task["task"], area=task["area"], why="under", actual=round(act, 2), expected=round(exp, 2))
        bot.log(f"core: {task['area']}: under the expected yield ({act:.2f} of {exp:.2f} {task['measure']}): one extension of {int(EXTEND / 60)} min")
    if worked >= task["budget"]:
        if verdict == "on track" and not task.get("extended"):
            task["extended"] = True
            task["budget"] += EXTEND
            bot.ev("task_extend", task=task["task"], area=task["area"], why="on track", actual=round(act, 2), expected=round(exp, 2))
            bot.log(f"core: {task['area']}: on track at the budget's end: one extension of {int(EXTEND / 60)} min")
            return None
        return "done"
    # a better task? only past the dwell, and only by the commitment margin: the running task is scored on the better of what it has actually yielded and
    # what was expected of it (the expectation halved once the grace has passed), so a slow first ten minutes do not throw a sound choice away
    if worked >= DWELL:
        rate_h = max(act / max(work_hours(task), 1e-6), float(task["expected"].get(judge, 0.0)) * (0.5 if worked >= GRACE_S else 1.0))
        running = rate_h / 60.0 * (1.0 + COMMIT) + 1e-6
        opts = [c for c in candidates(bot, g, rng) if c["area"] != task["area"]]
        sr = bool(bot.feature("switch_rate"))                      # a candidate's yield over the walk plus the budget (score_for)
        best = max(opts, key=lambda c: score_for(c, judge, sr)) if opts else None
        if best and score_for(best, judge, sr) > running * 1.5 + 0.01:
            bot.ev("task_switch", **{"from": task["area"], "to": best["area"], "why": f"{score_for(best, judge, sr):.3f} against {running:.3f} {judge} a minute here",
                                     "switch_rate": sr})
            bot.log(f"core: switching from {task['area']} ({running:.3f} {judge} a minute) to {best['area']} ({score_for(best, judge, sr):.3f})")
            bot.__dict__["_core_next"] = best
            return "switch"
    return None


def score_for(cand, measure, budget_time=False):
    """A candidate's expected progress a minute on a given measure (the running task's judge), for the switch comparison. With budget_time
    (feature switch_rate): the budget's yield over the walk plus the budget it is worked for. Without, over the tour's own loop (cand["minutes"],
    8 minutes at least), which overrates a tour shorter than the budget by budget/minutes: switch targets claimed 0.40-0.54 kills a minute
    against an expectation capped at 0.30, and the 8 traced switches delivered 0.21, less than the tours left (2026-11-02)."""
    exp = float((cand.get("expected") or {}).get(measure, 0.0) or 0.0) * HUNT_BUDGET / 3600.0
    if budget_time:
        return exp / max(float(cand.get("walk_min", 0.0) or 0.0) + HUNT_BUDGET / 60.0, 1.0)
    return exp / max(float(cand.get("minutes") or (cand.get("walk_min", 0.0) + HUNT_BUDGET / 60.0)), 1.0)


def errand_candidates(bot, hunting=False, best_hunt=0.0):
    """The errands the bot's state raises now (errands.needs), as candidates scored urgency x the best hunt's score (an urgency of 1 is as good as the best hunt)."""
    import errands
    b = bans(bot)
    out = []
    for task, urg, dest, budget, detail in errands.needs(bot, hunting):
        if task == "ammo" and any(k.startswith("ammo|") for k in b):
            last = bot.facts.get("ammo_unmet_money")
            money_now = int(bot.c.gold or 0) + int(bot.facts.get("bank_balance", 0) or 0)
            if last is not None and abs(money_now - int(last)) >= errands.AMMO_MONEY_STEP:
                for k in [k for k in b if k.startswith("ammo|")]:
                    del b[k]                                      # the purse changed: the arrows are tried again at once
        if any(k.startswith(task + "|") for k in b):
            seen = bot.__dict__.setdefault("_skipped_log", {})
            if now() - seen.get(task, 0) > 300:                   # why a raised need did not run: the ban (event errand_skipped), for the Watcher's trace
                seen[task] = now()
                left = max([until - now() for k, until in b.items() if k.startswith(task + "|")] or [0])
                bot.ev("errand_skipped", task=task, why="banned after an unmet run", secs_left=round(left), urgency=urg, detail=str(detail)[:80])
            continue
        walk = 0.0
        if dest is not None:
            length = route_length(bot, (int(dest[0]), int(dest[1])))
            if length is None:
                continue
            walk = length / walk_rate(bot)
        out.append({"task": task, "area": detail if task in ("camp", "loot") else task, "spots": [[int(dest[0]), int(dest[1]), 0]] if dest is not None else [],
                    "score": round(urg * max(best_hunt, 0.01), 4), "urgency": urg, "draw": 0.0, "mean": 0.0, "expected": {}, "walk_min": round(walk, 1), "die": 0.0, "n": 0,
                    "budget": float(budget), "detail": detail})
    return out


def pressing_need(bot):
    """The most urgent errand at PRESSING or above while a hunt runs, else None."""
    try:
        opts = [c for c in errand_candidates(bot, hunting=True) if c["urgency"] >= PRESSING]
    except Exception:
        return None
    return max(opts, key=lambda c: c["urgency"]) if opts else None


def wait_candidate():
    return {"task": "wait", "area": None, "spots": [], "score": 0.0, "draw": 0.0, "mean": 0.0, "expected": {}, "walk_min": 0.0, "die": 0.0, "n": 0}


# ---- the tick ---------------------------------------------------------------------------------------------------------------------------------------

NO_GROUND_RELAX = 2             # choices in a row with no spot open before the fallback loosens the tests (BotMaceBR waited 20 min, 2026-10-20)


def no_ground(bot, g, rng):
    """No spot open: report which test refused the spots (event no_ground {why: {test: spots}, n}); from the NO_GROUND_RELAX-th choice in a row, loosen the tests one
    step at a time (spots.RELAX_MAX) until a tour comes back. Returns (candidates, why)."""
    import spots
    n = bot.__dict__["_no_ground_n"] = bot.__dict__.get("_no_ground_n", 0) + 1
    why = dict(bot.__dict__.get("_spot_why") or {})
    bot.ev("no_ground", why=why, n=n)
    bot.log(f"core: no spot open ({n} in a row): refused by {why or 'nothing (no spot in reach)'}")
    try:
        import think
        top = max(why, key=why.get) if why else None
        think.say(bot, f"No ground open{', ' + {'crowded': 'too crowded', 'risky cell': 'too risky', 'danger model': 'too dangerous', 'worth floor': 'nothing worth it', 'banned': 'all rested', 'deadly kind': 'too deadly'}.get(top, top) if top else ''}, waiting")
    except Exception:
        pass
    if n < NO_GROUND_RELAX:
        return [], "rested"
    limit = 1 if no_heal(bot) else spots.RELAX_MAX                 # a bot without heals gets its crowding test relaxed and nothing more: no tier, no danger, no worth floor
    for relax in range(1, limit + 1):
        opts = candidates(bot, g, rng, rested=True, relax=relax)
        if opts:
            bot.ev("ground_relaxed", relax=relax, area=opts[0]["area"], tier=opts[0].get("tier"), die=opts[0].get("die"))
            bot.log(f"core: relaxed the spot tests to level {relax} ({['', 'crowding off', 'area risk off', 'worth floor off, the safest lowest-tier spot'][relax]}): {opts[0]['area']}")
            return opts, f"relaxed {relax}"
    return [], "rested"


def bank_candidate(bot, hunt):
    """A bank errand as a candidate (the nearest bank), for the bank-first rule; None when no bank is known."""
    try:
        x, y = bot.bank_xys()[0]
    except Exception:
        return None
    length = route_length(bot, (int(x), int(y)))
    if length is None:
        return None
    return {"task": "bank", "area": "bank", "spots": [[int(x), int(y), 0]], "score": hunt.get("score", 0.0), "urgency": 1.0, "draw": 0.0, "mean": 0.0, "expected": {},
            "walk_min": round(length / walk_rate(bot), 1), "die": 0.0, "n": 0, "budget": 120.0, "detail": f"{int(bot.c.gold)} gold carried to tier {hunt.get('tier')} ground"}


def party_tick(bot):
    """The party rule's turn (party.py r_party: invitations, acceptances, the loot flag) every PARTY_EVERY s for a bot with the feature: the core bypasses the rule list."""
    try:
        if not bot.feature("party") or not hasattr(bot, "r_party"):
            return
    except Exception:
        return
    if now() - bot.__dict__.get("_core_party_at", 0) < PARTY_EVERY:
        return
    bot.__dict__["_core_party_at"] = now()
    try:
        bot.r_party()
    except Exception as e:
        bot.log(f"core: party: {type(e).__name__}: {e}")


def in_town(bot):
    try:
        if bot.spot_in_city(int(bot.c.x), int(bot.c.y)):
            return True
        hx, hy = bot.home_centre()
        return max(abs(bot.c.x - hx), abs(bot.c.y - hy)) <= 90
    except Exception:
        return False


def tick(bot):
    """One brain tick under the core: the goal, the running task's monitor and tree, or a new choice. Returns the acted rule name (task:<task>:<step>)."""
    g = goal(bot)
    party_tick(bot)
    note_deaths(bot)
    weapon_note(bot)
    drop_robes_tick(bot)
    box_watch(bot)
    provisioned_watch(bot)
    try:
        if not bot.rewield_own():
            bot.wield_bridge()
    except Exception:
        pass
    task = bot.facts.get("task")
    rng = bot.__dict__.setdefault("_core_rng", random.Random(f"{bot.name}|{int(now() // 3600)}"))
    if task:
        why = monitor(bot, task, g, rng)
        if why:
            bot.__dict__["_last_errand"] = task["task"] not in ("hunt", "tour2", "wait")
            end_task(bot, task, why)
            task = None
    if not task:
        nxt = bot.__dict__.pop("_core_next", None)
        opts = candidates(bot, g, rng)
        why = "switch" if nxt else "chosen"
        if not opts:
            opts = candidates(bot, g, rng, rested=True)              # every spot resting: the ones whose rest ends soon
            why = "rested"
        if not opts:
            opts, why = no_ground(bot, g, rng)
        best_hunt = opts[0]["score"] if opts else 0.0
        try:
            errs = errand_candidates(bot, hunting=False, best_hunt=best_hunt)
        except Exception as e:
            bot.log(f"core: errands: {type(e).__name__}: {e}")
            errs = []
        if nxt and nxt["task"] != "hunt":
            cand = nxt
        else:
            cand = nxt if nxt and any(c["area"] == nxt["area"] for c in opts) else (opts[0] if opts else None)
            batching = bot.__dict__.get("_last_errand") and in_town(bot)            # learning 7: in town after an errand, the rest of the errands due, then a long hunt
            if errs and (cand is None or errs[0]["urgency"] >= (BATCH_URG if batching else 1.0)):
                cand = errs[0]
                why = "need" if not batching else "same visit"
        opts = errs + opts
        if cand is None:
            cand = wait_candidate()
            if not bot.__dict__.get("_core_waited"):
                bot.log("core: no hunt area is open (bans, danger, crowding): waiting a while")
            bot.__dict__["_core_waited"] = True
        else:
            bot.__dict__["_core_waited"] = False
            if cand.get("task") in ("hunt", "tour2"):
                bot.__dict__["_no_ground_n"] = 0
        if cand and cand.get("task") in ("hunt", "tour2") and ((cand.get("tier") or 1) >= 2 or box_bot(bot)) and int(bot.c.gold or 0) > CARRY_TIER2 and now() - bot.facts.get("banked_at", 0) > 300:
            bank = bank_candidate(bot, cand)                      # fix D: carrying more than CARRY_TIER2 to tier-2+ ground: the bank first, keeping 100
            if bank is not None:
                bot.log(f"core: {int(bot.c.gold)} gold carried to tier {cand.get('tier')} ground: the bank first")
                cand, why = bank, "bank first"
        task = start_task(bot, g, cand, opts, why=why)
        if cand.get("relax"):
            task["relax"] = cand["relax"]
    if task["task"] == "wait":
        bot.activity = "waiting for an open hunting area"
        time.sleep(3.0)
        return "task:wait:wait"
    if task.get("side") and task["side"] != "surface":
        try:
            bot.tele_allow(task["side"])                            # kept allowed while the task runs (a corpse run, a walk back from the healer)
        except Exception:
            pass
    if task["task"] in ("hunt", "tour2"):
        import hunt_tree
        step, failed = hunt_tree.tick(bot, task)
    else:
        import errands
        step, failed = errands.tick(bot, task)
    if failed:
        bot.__dict__["_last_errand"] = task["task"] not in ("hunt", "tour2", "wait")
        end_task(bot, task, failed)
    time.sleep(TICK_S.get(step, 0.7))                  # never a tick without a pause; the rule list paused 1.4-4 s a tick, the core about 1 s
    return f"task:{task['task']}:{step}"


def rule_category(rule):
    """The scoreboard's class of a core rule name ("task:hunt:fight" -> work), or None for a rule-list rule."""
    if not rule or not str(rule).startswith("task:"):
        return None
    step = str(rule).split(":")[-1]
    return STEP_CATEGORY.get(step, "other")
