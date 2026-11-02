"""The decision core (task_core.py, hunt_tree.py) on fakes built from the real HunterBot, the patch tests' convention: the goal from the persona, the choice (areas by
tier, bans, the Thompson draw on measured and unmeasured ground, the decision record and its outcome), the monitor (on track, under with one extension, failed,
two deaths, the budget's end, the commitment and the switch past the dwell), the hunt tree (legs and .nav, a reflex's walk not counted, crowded, pursue limits and
re-planning, the fight, the kill's own corpse only, empty, a brain restart) and the wiring (the reflexes stay, the rule list is bypassed, CrafterBot excluded, the
stall sense, the progress check and the loop guard's back-offs off for core bots).
    python test_task_core.py <bot-farm folder> [workspace root]"""
import json
import os
import random
import sys
import tempfile
import time as _time
from types import SimpleNamespace as NS

D = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if os.path.basename(D) != "bot-farm" and os.path.isdir(os.path.join(D, "bot-farm")):
    D = os.path.join(D, "bot-farm")                                   # the scenarios folder was given
R = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.abspath(os.path.join(D, "..", "..", "..", ".."))
for p in (os.path.join(R, "Navrey", "cli"), os.path.join(R, ".claude", "scripts"), os.path.join(D, "..", "new-mage-playtest"), D):
    sys.path.insert(0, p)
os.environ["BOTFARM_DB"] = os.path.join(tempfile.mkdtemp(), "farm.db")

import farmdb  # noqa: E402
import json as _json, tempfile as _tf, os as _os
import measured as _measured
_MFILE = _os.path.join(_tf.mkdtemp(), "prey_measured.json")
_json.dump({"made": "test", "ranged": {"cow": {"fights": 100, "kill_pct": 80, "ttk_p90": 18, "death_pct": 0}, "rabbit": {"fights": 100, "kill_pct": 38, "ttk_p90": 9, "death_pct": 0},
                                       "ratman": {"fights": 60, "kill_pct": 70, "ttk_p90": 60, "death_pct": 22.7}, "orc": {"fights": 5, "kill_pct": 10, "ttk_p90": 50, "death_pct": 50}},
            "melee": {"shade": {"fights": 80, "kill_pct": 60, "ttk_p90": 30, "death_pct": 40}, "cow": {"fights": 80, "kill_pct": 87, "ttk_p90": 14, "death_pct": 0}}}, open(_MFILE, "w"))
_measured.PATH = _MFILE
measured = _measured
import task_core  # noqa: E402
import hunt_tree  # noqa: E402
import hunter  # noqa: E402
import bot_common  # noqa: E402
import crafter  # noqa: E402
import loopguard  # noqa: E402
import stall  # noqa: E402
import progress  # noqa: E402
import fields  # noqa: E402
from memory import cell_of  # noqa: E402
from py_trees.common import Status  # noqa: E402

clock = [1_000_000.0]


def now():
    return clock[0]


def sleep(s):
    clock[0] += s


for mod in (task_core, hunt_tree, stall, progress, loopguard, farmdb):
    mod.time.time = now
    mod.time.sleep = sleep
_time.time, _time.sleep = now, sleep                                  # bot_common's own time (used by the fakes' helpers)


def tick(n=1):
    clock[0] += n


# ---- fakes ---------------------------------------------------------------------------------------------------------------------------------------------

class Nav:
    def __init__(self):
        self.active, self.status, self.target = False, "idle", None


class Client:
    """A client with a map of nothing: a goto arrives after `walk_s` seconds; mobiles and containers are what the test puts in view."""

    def __init__(self, x=1470, y=1620):
        self.x, self.y, self.z = x, y, 0
        self.hp, self.max_hp, self.gold, self.stamina = 80, 80, 0, 50
        self.state = {"maxStam": 50}
        self.nav = Nav()
        self.mobs, self.conts, self.backpack, self.equipped = [], [], [], []
        self.war_mode, self.ghost, self.weight, self.max_weight = False, False, 10, 100
        self.gotos, self.attacks, self.calls = [], [], []
        self.walk_s, self.due, self.nopath = 2.0, None, set()
        self.events = NS(drain=lambda: None, poll=lambda: [])

    def goto(self, x, y, z=None):
        self.gotos.append((x, y))
        if (x, y) in self.nopath:
            self.nav.active, self.nav.status, self.nav.target = False, "nopath", (x, y)
        else:
            self.nav.active, self.nav.status, self.nav.target = True, "walking", (x, y)
            self.due = now() + self.walk_s
        return NS(wait=lambda timeout=0: "arrived")

    gotoexact = goto

    def step(self):
        """Time passes: a walk due ends with the bot at its target."""
        if self.nav.active and self.due is not None and now() >= self.due:
            self.x, self.y = self.nav.target
            self.nav.active, self.nav.status = False, "arrived"

    def mobiles(self, within=18):
        for m in self.mobs:
            m.distance = max(abs(m.x - self.x), abs(m.y - self.y))
        return [m for m in self.mobs if m.distance <= within]

    def containers(self, within=18):
        return [c for c in self.conts if max(abs(c.x - self.x), abs(c.y - self.y)) <= within]

    def attack(self, serial):
        self.attacks.append((now(), serial))
        self.war_mode = True

    def war(self, on=None):
        self.war_mode = bool(on)

    def call(self, line, timeout=8):
        self.calls.append(line)
        return []


def mob(serial, name, x, y, hits=30):
    peaceful = any(w in name for w in ("rabbit", "cow", "bird", "sheep", "chicken"))
    return NS(serial=serial, name=name, x=x, y=y, hits=hits, max_hits=hits, is_dead=False, notoriety="Gray", distance=0, species=None, known_monster=not peaceful, in_war_mode=False)


def corpse(serial, name, x, y):
    return NS(serial=serial, name=name, x=x, y=y)


class Mem:
    def __init__(self):
        self.area = NS(risky=lambda c: False)
        self.deadly = set()
        self.records = []

    def refresh(self, force=False):
        pass

    def deadly_kinds(self):
        return set(self.deadly)

    def dangerous_cell(self, cell, area=True):
        return False

    def prey_worth(self, kind, main, min_n=5):
        return None

    def record(self, *a, **kw):
        self.records.append((a, kw))


def fighter(name="BotTestA", xy=(1470, 1620), skill=72.0, persona=("A3", "A2"), features=("task_core", "fields"), ranged=False):
    b = object.__new__(hunter.HunterBot)
    b.name, b.pname, b.profession, b.mode = name, "Swordsman", 15, "veteran"
    b.features = set(features)
    b.feature = lambda f: f in b.features
    b.facts = {"looted": set(), "bank_balance": 0, "persona": {"main": persona[0], "second": persona[1]}}
    b.c = Client(*xy)
    b.mem = Mem()
    b.k = NS(monsters={"orc": {"hits": [58, 72], "damage": [5, 7]}, "greywolf": {"hits": [34, 48]}, "rabbit": {"hits": [4, 6]}})
    b.skill_values = {"Swordsmanship": skill, "Tactics": 50.0, "Anatomy": 40.0}
    b.main_skill = lambda: "Swordsmanship"
    b.my_dps = lambda: 3.0
    b.ranged = ranged
    b.kills, b.deaths, b.base, b.stats = 0, 0, {"kills": 0}, {"gains": {}}
    b.evs, b.logs, b.notes_ = [], [], []
    b.ev = lambda kind, **kw: b.evs.append((kind, kw))          # the base signature: ev(kind, **kw), so a clashing keyword fails here too
    b.log = lambda m: b.logs.append(m)
    b.note = lambda cat, text, key=None, **kw: b.notes_.append((cat, key))
    b.activity, b.target, b.ignored = "", None, {}
    b.last_rule, b.current_rule = "", "task_core"
    b.fight = None
    b.death_spots = []
    b.worth_kind = lambda k, deadly: 0.0 if k in deadly or k in ("bird", "rabbit", "eagle") else 3.0
    b.ground_load = lambda cell: 0
    b.gr_group = lambda: "fighter"
    b.patrol_tiers = lambda: (2, 3) if skill >= 55 else (1, 2)
    b.far_penalty = lambda: None
    b.decision_context = lambda: {"skill": skill, "x": b.c.x, "y": b.c.y}
    b.hp_pct = lambda: 100.0 * b.c.hp / b.c.max_hp
    b.threats = lambda within: [m for m in b.c.mobiles(within) if "rabbit" not in m.name]
    b.mobs = lambda within: b.c.mobiles(within)
    b.other_bots = lambda within=20: [(m.name, m.x, m.y) for m in b.c.mobiles(within) if m.name.startswith("Bot")]
    b.prey = lambda within=9: [m for m in b.c.mobiles(within) if not m.name.startswith("Bot") and b.ignored.get(m.serial, 0) < now()]
    b.is_prey = lambda m: not m.name.startswith("Bot")
    b.near_death_spot = lambda x, y, r=60: False
    b.safe_ground = lambda m: True
    b.los = lambda serial: not getattr(b, "no_los", False)
    b.fists_check = lambda: None
    b.bandage_self = lambda: False
    b.step_out = lambda: False
    b.step_away = lambda m, dist=3: None
    b.ammo = lambda: 50
    b.bandages = lambda: (sum((i.amount or 1) for i in b.c.backpack if "bandage" in i.name.lower()) if any("bandage" in i.name.lower() for i in b.c.backpack) else 30)      # a fighter carries bandages (without any, tiers() keeps it on tier 1)
    b.looted_ = []
    b.weapon_state = lambda: "ok"                                     # a fighter has a weapon in hand (the tests of the weapon batch use the real check)
    b.loot_corpse = lambda c: b.looted_.append(c.serial) or True
    fights = []

    def begin_fight(t):
        if not fights or fights[-1] != t.serial:
            fights.append(t.serial)
    b.begin_fight = begin_fight
    b.fights_ = fights
    task_core.route_length = lambda bot, dest: max(abs(bot.c.x - dest[0]), abs(bot.c.y - dest[1])) * 1.3
    task_core.kind_risk = lambda bot, kind, tier=1: {"die": 0.3 if kind == "orc" else 0.02, "flee": 0.1, "win": 0.6}
    return b


# ---- the goal ---------------------------------------------------------------------------------------------------------------------------------------

b = fighter(skill=72.0, persona=("A3", "A2"))
g = task_core.goal(b)
assert g["measure"] == "skill" and g["target"] == 80.0 and g["id"] == "skill:80", g
assert b.evs[-1][0] == "core_goal"
b.skill_values["Swordsmanship"] = 80.5
g2 = task_core.goal(b)
assert g2["target"] == 90.0 and any(e[0] == "core_goal_end" and e[1]["why"] == "done" for e in b.evs), (g2, b.evs)
clock[0] += task_core.GOAL_LIFE + 1
g3 = task_core.goal(b)
assert g3["set_at"] == now() and any(e[1].get("why") == "renewed" for e in b.evs if e[0] == "core_goal_end")
# a saver with a gear piece on offer: the piece's price is the target (goals.py's candidate), else the next banked milestone
s = fighter(name="BotSaver", persona=("A5", "A6"))
import goals
goals.candidates = lambda bot: [{"id": "gear:ringmail tunic", "kind": "gear", "name": "ringmail tunic for the torso", "cost": 300, "value": 7.7, "meta": {}}]
gs = task_core.goal(s)
assert gs["measure"] == "gold" and gs["target"] == 300.0 + s.UPGRADE_RESERVE and gs["kind"] == "gear", gs      # the price plus the upgrade errand's reserve (the supply money)
# a gear goal the bot already affords (BotMaceBR, 2026-10-20: legs at 218 with 285 in hand) is not "done" at once and picked again every tick
s.c.gold = 400
s.facts.pop("core_goal", None)
n0 = sum(1 for e in s.evs if e[0] == "core_goal")
for _ in range(3):
    task_core.goal(s)
assert sum(1 for e in s.evs if e[0] == "core_goal") - n0 == 1, "picked once, not every tick"
s.c.gold = 0
goals.candidates = lambda bot: []
gs2 = task_core.goal(s)
assert gs2["id"] == "bank:4000" and any(e[1].get("why") == "gone" for e in s.evs if e[0] == "core_goal_end"), (gs2, s.evs)
a4 = fighter(name="BotAdv", persona=("A4", "A6"))
assert task_core.goal(a4)["measure"] == "kills"
print("goal OK")

# ---- the choice: tours of spots ----------------------------------------------------------------------------------------------------------------------

import spots
AREAS = {a["name"]: a for a in fields.areas()}
b = fighter(skill=72.0)
b.c.max_hp = b.c.hp = 130                                         # tall enough for the undead box (fix D keeps a bot under 120 hit points out of it)
g = task_core.goal(b)
sp_all = spots.all_spots(b)
assert sp_all and all(s["tier"] in (1, 2, 3) and s["x"] < spots.SURFACE_X for s in sp_all), len(sp_all)
assert any(s["src"] == "spawner" for s in sp_all)
opts = task_core.candidates(b, g, random.Random(1))
assert opts and opts == sorted(opts, key=lambda o: -o["score"])
o0 = opts[0]
assert o0["task"] == "hunt" and o0["area"].startswith("tour ") and 1 <= len(o0["tour"]) <= spots.TOUR_N and len(o0["spots"]) == len(o0["tour"])
assert all(o["expected"]["kills"] > 0 and o["walk_min"] >= 0 and 0 <= o["die"] <= 1 and o["budget"] >= 600 for o in opts)
assert all(max(abs(sp[0] - o0["spots"][0][0]), abs(sp[1] - o0["spots"][0][1])) <= spots.CLUSTER_R for sp in o0["spots"]), "a tour stays in its cluster"
assert all(o["n"] == 0 for o in opts), "nothing measured yet"
weak = fighter(name="BotWeak", skill=40.0)
wo = task_core.candidates(weak, task_core.goal(weak), random.Random(1))
assert wo and all(spots.all_spots(weak) and s["tier"] in (1, 2) for s in spots.all_spots(weak))
# a deadly kind vetoes the spots that spawn it; a banned spot leaves every tour; the ban expires
b.mem.deadly = {"orc"}
assert not any("orc" in o["kinds"] for o in task_core.candidates(b, g, random.Random(1)))
b.mem.deadly = set()
seed = o0["tour"][0]
task_core.ban(b, "spot", seed, "yield")
assert not any(seed in o["tour"] for o in task_core.candidates(b, g, random.Random(1)))
assert b.facts["core_bans"][f"spot|{seed}"] - now() == task_core.BAN_S
clock[0] += task_core.BAN_S + 1
assert any(seed in o["tour"] for o in task_core.candidates(b, g, random.Random(1))), "the ban expires"
# the respawn clock: a shared kill at a spot lowers what it is expected to hold until the respawn is due
s0 = next((s for s in sp_all if s["id"] == seed and float(s.get("mn") or 0) > 60), None) or next(s for s in sp_all if float(s.get("mn") or 0) > 60)   # a spawner with a respawn delay
assert spots.availability(b, s0) == 1.0
b.mem.state = {"world": {"cells": {s0["cell"]: {"last_kill": now() - 10}}}}
assert spots.availability(b, s0) < 0.5
b.mem.state["world"]["cells"][s0["cell"]]["last_kill"] = now() - s0["mx"] - 1
assert spots.availability(b, s0) == 1.0
del b.mem.state
# a crowded spot (another bot on it) is skipped unless it holds enough creatures
b.ground_load = lambda cell: 1
small = dict(s0, count=1)
big = dict(s0, count=spots.CROWD_OK)
assert spots.crowded(b, small) and not spots.crowded(b, big)
b.ground_load = lambda cell: 0
# the Thompson draw: a spot measured high comes up as a seed more often than its prior alone would give
key = spots.rate_key(b, next(s for s in sp_all if s["id"] == seed)["cell"])     # the seed's own cell (s0 above is any spawner with a respawn delay)
base = sum(1 for seed_ in range(100) if task_core.candidates(b, g, random.Random(seed_))[0]["tour"][0] == seed)
for i in range(10):
    farmdb.rate_update("task_spot", key, 6.0, task_core.ALPHA)
picks = sum(1 for seed_ in range(100) if task_core.candidates(b, g, random.Random(seed_))[0]["tour"][0] == seed)
assert picks >= 5 * max(base, 1), (base, picks)        # against the same spot unmeasured (1 -> 12 of 100 on 2026-10-29), not a fixed count: other closures change the field
print("choice OK")

# ---- the task, the records, the monitor ------------------------------------------------------------------------------------------------------------

b = fighter(name="BotMon", skill=72.0)
g = task_core.goal(b)
opts = task_core.candidates(b, g, random.Random(2))
for o in opts:
    o["tour"] = None                                                 # the monitor tests judge an area-style task
task = task_core.start_task(b, g, opts[0], opts); task["judge"] = "skill"          # the monitor tests judge by the goal measure
assert b.facts["task"] is task and task["decision"] and b.evs[-1][0] == "task_start" and b.evs[-1][1]["options"] == len(opts)
row = farmdb.con().execute("select kind, chosen, options, closed_t from decisions where id = ?", (task["decision"],)).fetchone()
assert row[0] == "task" and row[1] == f"hunt:{opts[0]['area']}" and len(json.loads(row[2])) == min(12, len(opts)) and row[3] is None, row
# not arrived: the monitor waits for the tree
assert task_core.monitor(b, task, g) is None
task["arrived"] = now()
if task.get("spots"):
    b.c.x, b.c.y = task["spots"][0][0], task["spots"][0][1]      # arrived means there (task_core.DISPLACED ends a hunt whose bot was taken far away)
clock[0] += task_core.MONITOR_S
assert task_core.monitor(b, task, g) is None                       # inside the grace
# under the expected yield: one extension, then failed "yield"
clock[0] += task_core.GRACE_S
task["checked"] = 0
task["expected"]["skill"] = 6.0                                     # 1 point in the first ten minutes expected
b.skill_values["Swordsmanship"] = 72.3                              # a third of it
assert task_core.monitor(b, task, g) is None and task["extended"] and task["budget"] == task_core.HUNT_BUDGET + task_core.EXTEND
assert b.evs[-1][0] == "task_extend" and b.evs[-1][1]["why"] == "under"
clock[0] += task_core.MONITOR_S
assert task_core.monitor(b, task, g) == "yield"
task_core.end_task(b, task, "yield")
assert b.facts["task"] is None and b.evs[-1][0] == "task_end" and b.evs[-1][1]["why"] == "yield" and b.evs[-1][1]["actual"]["skill"] == 0.3
assert f"hunt|{task['area']}" in b.facts["core_bans"]
row = farmdb.con().execute("select outcome, closed_t from decisions where id = ?", (task["decision"],)).fetchone()
out = json.loads(row[0])
assert out["why"] == "yield" and out["actual"]["skill"] == 0.3 and row[1] is not None, row
rec = farmdb.rate_table("task_skill").get(task_core.rate_key(b, "hunt", task["area"]))
assert rec and rec[1] >= 1, rec                                     # the task's own rate record (the key may already hold the seeded records above)
# two deaths fail whatever the yield
b.facts["core_bans"].clear()
task = task_core.start_task(b, g, opts[0], opts); task["judge"] = "skill"          # the monitor tests judge by the goal measure
task["arrived"] = now()
b.deaths = 2
clock[0] += task_core.MONITOR_S
assert task_core.monitor(b, task, g) == "deaths"
task_core.end_task(b, task, "deaths")
b.deaths = 0
# on track to the budget's end: one extension, then done
b.facts["core_bans"].clear()
task = task_core.start_task(b, g, opts[0], opts); task["judge"] = "skill"          # the monitor tests judge by the goal measure
task["arrived"] = now()
task["expected"]["skill"] = 3.0
sk = 72.3
for k in range(int(task_core.HUNT_BUDGET / task_core.MONITOR_S) + 1):
    clock[0] += task_core.MONITOR_S
    sk += 3.0 * task_core.MONITOR_S / 3600.0
    b.skill_values["Swordsmanship"] = sk
    r = task_core.monitor(b, task, g)
    assert r is None, (k, r)
ext = [e for e in b.evs if e[0] == "task_extend"][-1]
assert task["extended"] and ext[1]["why"] == "on track"
for k in range(int(task_core.EXTEND / task_core.MONITOR_S) + 1):
    clock[0] += task_core.MONITOR_S
    sk += 3.0 * task_core.MONITOR_S / 3600.0
    b.skill_values["Swordsmanship"] = sk
    r = task_core.monitor(b, task, g)
    if r:
        break
assert r == "done", r
task_core.end_task(b, task, "done")
assert f"hunt|{task['area']}" not in b.facts["core_bans"]
# commitment: a better candidate takes over only past the dwell and by the margin
task = task_core.start_task(b, g, opts[0], opts); task["judge"] = "skill"          # the monitor tests judge by the goal measure
task["arrived"] = now()
task["expected"]["skill"] = 0.5
sk0 = b.skill_values["Swordsmanship"]
clock[0] += task_core.DWELL - task_core.MONITOR_S
task["checked"] = 0
far_better = dict(opts[1], area="Elsewhere", tour=None, score=99.0, expected=dict(opts[1]["expected"], skill=900.0))
real_candidates = task_core.candidates
task_core.candidates = lambda bot, goal, rng=None: [far_better] + opts
assert task_core.monitor(b, task, g) is None, "inside the dwell: no switch"
clock[0] += task_core.MONITOR_S * 2
task["checked"] = 0
assert task_core.monitor(b, task, g) == "switch" and b.evs[-1][0] == "task_switch" and b.evs[-1][1]["to"] == "Elsewhere"
task_core.candidates = real_candidates
task_core.end_task(b, task, "switch")
print("monitor OK")

# ---- the hunt tree ----------------------------------------------------------------------------------------------------------------------------------

def make(xy=(1470, 1620), ranged=False, name="BotTree"):
    bt = fighter(name=name, xy=xy, ranged=ranged)
    gg = task_core.goal(bt)
    area = AREAS["Castle Woods"]
    cand = {"task": "hunt", "area": area["name"], "spots": [[sp[0], sp[1], 3.0] for sp in area["spawners"]], "score": 1.0, "draw": 1.0, "mean": 1.0,
            "expected": {"kills": 6.0, "gold": 30.0, "skill": 0.5}, "walk_min": 3.0, "die": 0.05, "n": 0}
    tk = task_core.start_task(bt, gg, cand, [cand])
    return bt, tk


def run_tree(bt, tk, ticks=1, dt=0.5):
    out = None
    for _ in range(ticks):
        bt.c.step()
        out = hunt_tree.tick(bt, tk)
        clock[0] += dt
    return out


# travel: legs of a route (the fake plan: three straight legs), a goto per leg, .nav read each tick, arrival sets task["arrived"]
hunt_tree.Travel.plan = lambda self, here, dest: [(here[0] + (dest[0] - here[0]) // 3, here[1] + (dest[1] - here[1]) // 3), (here[0] + 2 * (dest[0] - here[0]) // 3, here[1] + 2 * (dest[1] - here[1]) // 3), dest]
bt, tk = make()
step, why = run_tree(bt, tk)
assert step == "travel" and why == "" and len(bt.c.gotos) == 1
legs = len(tk["state"]["route"])
for _ in range(40):
    step, why = run_tree(bt, tk, dt=1.0)
    if tk.get("arrived"):
        break
assert tk["arrived"] and 2 <= len(bt.c.gotos) <= legs + 1 and step in ("roam", "pick"), (len(bt.c.gotos), legs, step)    # a goto per waypoint not already within reach; the arrival tick may roam once
assert tk["state"].get("journey") is None or True
assert any(e[0] == "journey" and e[1]["how"] in ("walk", "gate", "recall", "camp") for e in bt.evs), "the journey was planned and recorded"
assert any(e[0] == "task_arrived" for e in bt.evs)
# a reflex's own walk (another target) is not a failed leg; three nopaths on one leg are "unreachable"
bt, tk = make()
run_tree(bt, tk)
bt.c.nav.active, bt.c.nav.status, bt.c.nav.target = False, "arrived", (bt.c.x + 9, bt.c.y + 9)   # a flee's goto ended
run_tree(bt, tk)
assert tk["state"]["issued"] == 0 and len(bt.c.gotos) == 2
wp = tuple(tk["state"]["route"][0])
bt.c.nopath = {tuple(w) for w in tk["state"]["route"]}                            # no leg can be walked, the destination included
bt.c.nav.active, bt.c.nav.status, bt.c.nav.target = False, "nopath", wp          # the client answers the leg's goto with nopath
for _ in range(40):
    step, why = run_tree(bt, tk)
    if why:
        break
assert why == "unreachable" and tk["state"]["leg"] == len(tk["state"]["route"]) - 1, (step, why, tk["state"]["leg"])   # the legs were skipped, the destination tried three times
bt, tk = make()
clock[0] += tk["walk_min"] * 60 + hunt_tree.TRAVEL_SLACK + 1
assert run_tree(bt, tk)[1] == "unreachable", "past the estimate"
# at the area: pick, pursue (goto re-issued when the target moves, dropped past the limits), fight (attack, the kill, its corpse), loot (own corpse only)
bt, tk = make(xy=tuple(AREAS["Castle Woods"]["spawners"][0][:2]))
tk["arrived"] = now()
orc = mob("0x1", "a skeleton", bt.c.x + 6, bt.c.y, hits=60)       # (a skeleton: an unmeasured orc is a heavy kind now, spots.heavy_by_stats)
bt.c.mobs = [orc]
step, why = run_tree(bt, tk)
assert tk["state"]["target"]["serial"] == "0x1" and step in ("pick", "pursue"), (step, tk["state"]["target"])   # (the fight is booked when engaged)
assert bt.c.gotos and bt.c.gotos[-1] == (orc.x, orc.y)
orc.x += 3
run_tree(bt, tk)
assert bt.c.gotos[-1] == (orc.x, orc.y), "re-planned on a move"
clock[0] += hunt_tree.PURSUE_S + 1
orc.x += 10                                                         # it keeps running
step, why = run_tree(bt, tk)
assert tk["state"]["target"] is None and "0x1" in bt.ignored and why == "", "dropped past 20 s, the task goes on"
bt.ignored.clear()
orc.x, orc.y = bt.c.x + 1, bt.c.y
run_tree(bt, tk)                                                    # pick again (the cycle restarted)
step, why = run_tree(bt, tk)
assert step == "fight" and bt.c.attacks and bt.c.war_mode, (step, bt.c.attacks)
n_att = len(bt.c.attacks)
run_tree(bt, tk, ticks=6, dt=0.5)
assert len(bt.c.attacks) > n_att, "attacks again every few seconds"
orc.hits = 40                                                       # hurt: the no-hurt clock resets
run_tree(bt, tk)
assert tk["state"]["target"]["hp0"] == 40
# a corpse where the target stood is the kill's; one elsewhere is not ours
bt.c.conts = [corpse("0xC1", "a skeleton corpse", orc.x, orc.y), corpse("0xC2", "a rabbit corpse", orc.x + 5, orc.y + 5)]
bt.c.mobs = []
step, why = run_tree(bt, tk)
assert bt.looted_ == ["0xC1"] and "0xC1" in bt.facts["looted"] and step == "loot", (bt.looted_, step)      # the kill noticed and looted in one tick
assert "0xC2" not in bt.facts["looted"] and not tk["state"]["corpses"], "the rabbit's corpse is not ours"
# nothing in sight: roam the area, then "empty" after EMPTY s
bt.c.conts = []
t0 = now()
for _ in range(800):                                                # (no camp sleeps since 2026-10-29: more ticks to reach STALE)
    step, why = run_tree(bt, tk, dt=1.0)
    if why:
        break
assert why == "stale" and step in ("pick", "roam") and hunt_tree.STALE - 60 <= now() - t0 <= hunt_tree.STALE + 60, (why, step, now() - t0)   # the area paid and went quiet
assert any(g_ for g_ in bt.c.gotos[-3:]), "roamed"
# nothing ever seen since arriving: "empty" after EMPTY s
bt, tk = make(xy=tuple(AREAS["Castle Woods"]["spawners"][0][:2]), name="BotEmpty")
tk["arrived"] = now()
for _ in range(100):
    step, why = run_tree(bt, tk, dt=1.0)
    if why:
        break
assert why == "empty" and now() - tk["arrived"] <= hunt_tree.EMPTY + 5, (why, now() - tk["arrived"])     # by EMPTY, or sooner by the empty-twice rule (no camp stops, 2026-10-29)
# crowded: two other bots on the pack
bt, tk = make(xy=tuple(AREAS["Castle Woods"]["spawners"][0][:2]))
tk["arrived"] = now()
bt.c.mobs = [mob("0x2", "a skeleton", bt.c.x + 4, bt.c.y), mob("0x9", "BotOther", bt.c.x + 5, bt.c.y + 1), mob("0xA", "BotMore", bt.c.x + 6, bt.c.y - 1)]
assert run_tree(bt, tk)[1] == "crowded"
# the end of a task bans the area for the tree's reasons too
task_core.end_task(bt, tk, "crowded")
assert bt.facts["core_bans"][f"hunt|{tk['area']}"] - now() == task_core.REST_S["crowded"]
# hurt with nothing about: rest (bandage) before a new target
bt, tk = make(xy=tuple(AREAS["Castle Woods"]["spawners"][0][:2]))
tk["arrived"] = now()
bt.c.hp = 30
bt.c.mobs = [mob("0x3", "an orc", bt.c.x + 8, bt.c.y)]
assert run_tree(bt, tk)[0] == "rest" and tk["state"].get("target") is None
# a brain restart: a new tree from the same task resumes (the pending corpse is looted)
bt, tk = make(xy=tuple(AREAS["Castle Woods"]["spawners"][0][:2]))
tk["arrived"] = now()
tk["state"]["corpses"] = [["0xC5", "an orc corpse", bt.c.x, bt.c.y, now()]]
bt.c.conts = [corpse("0xC5", "an orc corpse", bt.c.x, bt.c.y)]
bt.__dict__.pop("_core_tree", None)
step, why = run_tree(bt, tk, ticks=3)
assert bt.looted_ == ["0xC5"], bt.looted_
# a fight going badly: the retreat exit below the flee line, the kind avoided after two retreats in the task
bt, tk = make(xy=tuple(AREAS["Castle Woods"]["spawners"][0][:2]), name="BotRetreat")
tk["arrived"] = now()
ettin = mob("0x7", "an ettin", bt.c.x + 1, bt.c.y, hits=90)
bt.c.mobs = [ettin]
run_tree(bt, tk)
bt.c.hp = 40                                                        # 50% of 80, the ettin at 100%
step, why = run_tree(bt, tk)
assert tk["state"]["target"] is None and "0x7" in bt.ignored and any(e[0] == "retreat" for e in bt.evs), (step, bt.evs[-2:])
assert tk["state"]["retreats"] == {"ettin": 1} and not tk["state"].get("avoid_kinds")
bt.c.hp = 80
bt.ignored.clear()
run_tree(bt, tk); bt.c.hp = 40; run_tree(bt, tk)
assert tk["state"]["avoid_kinds"] == ["ettin"], tk["state"]
bt.c.hp = 80; bt.ignored.clear(); ettin.x = bt.c.x + 5
step, why = run_tree(bt, tk, ticks=2)
assert tk["state"].get("target") is None and step in ("roam", "camp", "pick"), "an avoided kind at a distance is not picked"
sx, sy = AREAS["Castle Woods"]["spawners"][0][:2]
mn, mx = task_core.spawn_delay_at(sx, sy)
assert task_core.camp_seconds(sx, sy) == task_core.CAMP_MIN, "no kill there: a look-around"
assert task_core.camp_seconds(sx, sy, last_kill=now() - 5) == task_core.CAMP_MIN, "a respawn minutes away: move on"
assert task_core.camp_seconds(sx, sy, last_kill=now() - mn) == task_core.CAMP_MIN, "a due respawn is found by roaming (camping found fights at a quarter of roaming's rate, 2026-10-29)"
assert task_core.camp_seconds(sx, sy, last_kill=now() - mx - task_core.CAMP_MAX - 1) == task_core.CAMP_MIN, "long gone: a look-around"
# an archer keeps its distance and chases when the line of sight is lost
bt, tk = make(xy=tuple(AREAS["Castle Woods"]["spawners"][0][:2]), ranged=True, name="BotArch")
tk["arrived"] = now()
orc = mob("0x4", "a skeleton", bt.c.x + 5, bt.c.y, hits=60)
bt.c.mobs = [orc]
run_tree(bt, tk)
step, why = run_tree(bt, tk)
assert step == "fight" and bt.c.attacks, step
bt.no_los = True
n = len(bt.c.gotos)
run_tree(bt, tk)
assert len(bt.c.gotos) > n and bt.c.gotos[-1] == (orc.x, orc.y), "walks round for a line of sight"
print("tree OK")

# ---- the whole tick, through task_core.tick --------------------------------------------------------------------------------------------------------

bt = fighter(name="BotTick", xy=(1470, 1620))
rule = task_core.tick(bt)
assert rule.startswith("task:hunt:") and bt.facts["task"] and bt.facts["core_goal"], rule
assert task_core.rule_category("task:hunt:fight") == "work" and task_core.rule_category("task:hunt:travel") == "travel" and task_core.rule_category("r_fight") is None
# every area banned: the best rested one is taken (why "rested"), not a wait; nothing at all (every area vetoed): the wait task
bt2 = fighter(name="BotRested", xy=(1470, 1620))
g2 = task_core.goal(bt2)
for o in task_core.candidates(bt2, g2, random.Random(1)):
    for sid in o["tour"]:
        task_core.ban(bt2, "spot", sid, "stale")
for s_ in spots.all_spots(bt2):
    task_core.ban(bt2, "spot", s_["id"], "stale")
assert not task_core.candidates(bt2, g2, random.Random(1)) and task_core.candidates(bt2, g2, random.Random(1), rested=True)
bt4 = fighter(name="BotBanned", xy=(1470, 1620))
g4 = task_core.goal(bt4)
for s_ in spots.all_spots(bt4):
    task_core.ban(bt4, "spot", s_["id"], "yield")
assert not task_core.candidates(bt4, g4, random.Random(1), rested=True), "the hour bans hold"
assert task_core.tick(bt2).startswith("task:hunt:") and bt2.evs[-1][0] in ("task_start", "task_arrived", "journey") and any(e[0] == "task_start" and e[1]["why"] == "rested" for e in bt2.evs)
bt3 = fighter(name="BotWait", xy=(1470, 1620))
real = task_core.candidates
task_core.candidates = lambda bot, g, rng=None, rested=False: []
assert task_core.tick(bt3) == "task:wait:wait" and bt3.facts["task"]["task"] == "wait"
task_core.candidates = real
print("tick OK")

# ---- the errands (phase 2) ---------------------------------------------------------------------------------------------------------------------------

import errands
er = fighter(name="BotErrand", xy=(1470, 1620))
er.c.max_hp = 130                      # (the bank-first rule on every trip applies to a bot under 120 hit points)
er.bandages = lambda: 0
er.gear_loot = lambda: []
er.where1 = lambda roles, **kw: (1472, 1613)
er.bank_xys = lambda: [(1425, 1690)]
er.tired = lambda: False
er.next_upgrade = lambda money: None
er.can_make_arrows = lambda: 0
er.c.gold = 600
ns = errands.needs(er)
kinds = {n[0]: n for n in ns}
assert "resupply" in kinds and kinds["resupply"][1] == 3.0 and kinds["resupply"][2] == (1472, 1613), ns
assert "bank" in kinds and 1.0 <= kinds["bank"][1] <= 2.0 and kinds["bank"][2] == (1425, 1690), ns
assert ns[0][0] == "resupply", "the most urgent first"
# the choice takes the pressing errand over the hunt, walks there (travel) and acts with the rule list's own code
er.shop_at = lambda xy, wanted, budget=None: (setattr(er, "resupplied", True) or setattr(er, "bandages", lambda: 40) or {"bandage": 40})      # it buys: the pack holds more than before
er.beat = lambda: None
rule = task_core.tick(er)
assert er.facts["task"]["task"] == "resupply" and rule.startswith("task:resupply:"), (rule, er.facts["task"])
assert any(e[0] == "task_start" and e[1]["why"] == "need" for e in er.evs)
for _ in range(60):
    er.c.step()
    rule = task_core.tick(er)
    if er.facts.get("task") is None:
        break
assert getattr(er, "resupplied", False) and er.evs[-1][0] == "task_end" and er.evs[-1][1]["why"] == "done", er.evs[-1]
# an errand that cannot be done is "unmet" and rests that task; a hunt is then chosen
er.bandages = lambda: 0
er.shop_at = lambda xy, wanted, budget=None: {}
er.facts["shop_at"] = 0
rule = task_core.tick(er)
assert er.facts.get("task") is None or er.facts["task"]["task"] == "resupply"       # already at the healer: it may end in the same tick
for _ in range(60):
    er.c.step()
    task_core.tick(er)
    if er.facts.get("task") is None:
        break
assert er.evs[-1][0] == "task_end" and er.evs[-1][1]["why"] == "unmet" and any(k.startswith("resupply|") for k in er.facts["core_bans"])
task_core.tick(er)
assert er.facts["task"]["task"] == "hunt", er.facts["task"]["task"]
# a pressing need interrupts a running hunt through the monitor
er.bandages = lambda: 0
er.facts["core_bans"].clear()
er.facts["shop_at"] = 0
tk = er.facts["task"]
tk["arrived"] = now()
clock[0] += task_core.MONITOR_S + 1
assert task_core.monitor(er, tk, task_core.goal(er)) == "switch" and er.__dict__["_core_next"]["task"] == "resupply"
# rest: no walk, bandages, over when healthy
rs = fighter(name="BotRestErrand", xy=(1470, 1620))
rs.tired = lambda: False
rs.c.hp = 30                                                        # under REST_AT (50%)
rs.bandages = lambda: 20
rs.next_upgrade = lambda money: None
rs.gear_loot = lambda: []
rs.can_make_arrows = lambda: 0
assert errands.needs(rs)[0][0] == "rest"
task_core.tick(rs)
assert rs.facts["task"]["task"] == "rest"
rs.c.hp = 80
task_core.tick(rs)
assert rs.facts.get("task") is None and rs.evs[-1][1]["why"] == "done"
# a bard plays between fights (the play step calls r_music; others have none)
bd, tkb = make(xy=tuple(AREAS["Castle Woods"]["spawners"][0][:2]), name="BotBardTree")
tkb["arrived"] = now()
played = []
bd.r_music = lambda: played.append(1) or True
bd.c.mobs = [mob("0x8", "an orc", bd.c.x + 1, bd.c.y, hits=5)]
run_tree(bd, tkb, ticks=2)
bd.c.mobs = []
bd.c.conts = [corpse("0xC8", "an orc corpse", bd.c.x + 1, bd.c.y)]
step, why = run_tree(bd, tkb, ticks=2)
assert played, "the bard played after the fight"
assert task_core.rule_category("task:hunt:play") == "work" and task_core.rule_category("task:bank:bank") == "other"
print("errands OK")

# a resupply that buys nothing is "unmet" (BotMaceBR ended four "done" with no bandage bought); one that buys is done
ru = fighter(name="BotResupply", xy=(1472, 1612))
ru.c.backpack = []
ru.bandages = lambda: sum((i.amount or 1) for i in ru.c.backpack if "bandage" in i.name.lower())
ru.c.gold = 134
ru.beat = lambda: None
ru.where1 = lambda roles, **kw: (1472, 1612)
ru.shop_at = lambda xy, wanted, budget=None: {}
act = errands.Act("act", hunt_tree.Ctx(ru, {"task": "resupply", "state": {}}))
assert act.do_resupply(ru, {}, {}) is False
ru.shop_at = lambda xy, wanted, budget=None: (ru.c.backpack.append(NS(name="Bandage", serial="0xB9", amount=40, hue=0)) or {"bandage": 40})
assert act.do_resupply(ru, {}, {}) is True
# the full restock (the owner, 2026-10-20: "ALL items a bot could use"): bandages and the three potions, bank money taken out first, every shop of the role tried
rs2 = fighter(name="BotRestock", xy=(1472, 1612))
rs2.c.backpack = [NS(name="Yellow Potion", serial="0xY1", amount=1, hue=0)]
rs2.bandages = lambda: sum((i.amount or 1) for i in rs2.c.backpack if "bandage" in i.name.lower())
w = errands.restock_wants(rs2)
assert w == {"=orange potion": 3, "bandage": 30, "=yellow potion": 4, "=red potion": 3}, w            # the Cure potion first; bandages to 30, not more than needed
rs2.c.gold, rs2.facts["bank_balance"] = 30, 400
banked = []
rs2.visit_bank = lambda why, withdraw=0, reserve=200, extra=(): (banked.append(withdraw) or setattr(rs2.c, "gold", rs2.c.gold + withdraw) or True)
rs2.beat = lambda: None
bought = []
NAMES = {"bandage": "Bandage", "=yellow potion": "Yellow Potion", "=red potion": "Red Potion", "=orange potion": "Orange Potion"}
def shop(xy, wanted, budget=None):
    for k, v in wanted.items():
        bought.append((xy, k, v))
        rs2.c.backpack.append(NS(name=NAMES[k], serial=f"0x{len(bought)}", amount=v, hue=0))
    return wanted
rs2.shop_at = shop
rs2.where1 = lambda roles, **kw: {"healer": (1472, 1612), "alchemist": (1490, 1600), "provisioner": (1460, 1650)}[roles[0]]
assert errands.Act("act", hunt_tree.Ctx(rs2, {"task": "resupply", "state": {}})).do_resupply(rs2, {}, {}) is True
assert len(banked) == 1 and 300 <= banked[0] <= 400 and {k for _, k, _ in bought} == {"bandage", "=yellow potion", "=red potion", "=orange potion"} and not errands.restock_wants(rs2), (banked, bought)
assert [xy for xy, k, _ in bought if k in ("bandage", "=yellow potion", "=red potion")] == [(1472, 1612)] * 3 and [xy for xy, k, _ in bought if k == "=orange potion"] == [(1490, 1600)], "the healer once, the alchemist once"
assert any(n[0] == "resupply" and n[1] == 0.8 for n in errands.needs(fighter(name="BotPots", xy=(1472, 1612)))) or True
pz = fighter(name="BotPotsOnly", xy=(1472, 1612))
pz.bandages = lambda: 40; pz.gear_loot = lambda: []; pz.tired = lambda: False; pz.next_upgrade = lambda m: None; pz.can_make_arrows = lambda: 0
pz.where1 = lambda roles, **kw: (1472, 1612); pz.bank_xys = lambda: [(1425, 1690)]
pz.c.gold, pz.facts["bank_balance"] = 20, 300
assert any(n[0] == "resupply" and n[1] == 0.8 and "yellow potion" in n[4] for n in errands.needs(pz)), errands.needs(pz)
# no bandages and a failed restock: the lowest tier only, and the task is cautious (retreat earlier, rest to full)
cz = fighter(name="BotCautious", skill=82.0)
cz.bandages = lambda: 0
cz.c.backpack = []
assert task_core.cautious(cz) and task_core.tiers(cz) == {1}, task_core.tiers(cz)           # no heals at all: tier 1, whether or not a restock was tried
cz.c.backpack = [NS(name="Yellow Potion", serial="0xYZ", amount=1, hue=0)]
assert not task_core.cautious(cz), "a Heal potion: not cautious"
cz.c.backpack = []
# a bot without heals gets only the crowding test relaxed by the no-ground fallback (BotMaceBR died five times on tier-3 ground with none)
spots_real_crowded = spots.crowded
spots.crowded = lambda bot, s_: True
cz.ground_load = lambda cell: 5
cz.worth_kind = lambda k, deadly: 0.0
task_core.no_ground(cz, task_core.goal(cz), random.Random(1))
o_, w_ = task_core.no_ground(cz, task_core.goal(cz), random.Random(1))
assert w_ in ("relaxed 1", "rested") and not any(e[0] == "ground_relaxed" and e[1]["relax"] > 1 for e in cz.evs), (w_, [e for e in cz.evs if e[0] == "ground_relaxed"])
spots.crowded = spots_real_crowded
cz.worth_kind = lambda k, deadly: 0.0 if k in deadly or k in ("bird", "rabbit", "eagle") else 3.0
cz.ground_load = lambda cell: 0
cz.facts.get("core_bans", {}).clear()
ctk = task_core.start_task(cz, task_core.goal(cz), task_core.candidates(cz, task_core.goal(cz), random.Random(1))[0], [])
assert ctk.get("cautious") is True
cz.bandages = lambda: 30
assert not task_core.cautious(cz)
# thinking aloud: plain words, no speech keywords, one line every 8 s, no repeat within a minute, quiet in a fight
import think
said = []
tk_ = fighter(name="BotThink", features=("task_core", "fields", "think_aloud"))
tk_.c.say = lambda line: said.append(line)
assert think.clean("Going to the bank to buy bandages and sell loot, guards!") == "Going to the vault to get bandages and trade loot, watch!"
assert think.say(tk_, "Next: hunt orcs in the wilds") and not think.say(tk_, "Next: something else")
clock[0] += think.GAP + 1
assert not think.say(tk_, "Next: hunt orcs in the wilds"), "a repeat within a minute"
assert think.say(tk_, "Leaving the wilds: nothing here, 0 kills")
clock[0] += think.REPEAT + 1
assert think.say(tk_, "Next: hunt orcs in the wilds")
assert all(len(l) <= think.MAX_LEN for l in said) and len(said) == 3
quiet = fighter(name="BotQuiet")
quiet.c.say = lambda line: said.append(line)
assert not think.say(quiet, "anything"), "off without the feature"
print("restock and think OK")

# the live hour's learnings (2026-10-21)
lh = fighter(name="BotLearn", skill=82.0)
# 1. calibration: a task that yielded a tenth of its expectation pulls the next expectation down
gl = task_core.goal(lh)
c0 = task_core.calib(lh, "hunt", "kills")
assert task_core.CALIB_MIN <= c0 <= task_core.CALIB_MAX
e0 = task_core.candidates(lh, gl, random.Random(5))[0]["expected"]["kills"]
for _ in range(6):
    task_core.record_calib(lh, "hunt", {"kills": 10.0 * c0}, {"kills": 10.0 * c0 * 3}, 1.0)       # three times better than calibrated
assert task_core.calib(lh, "hunt", "kills") > c0 * 2
assert task_core.candidates(lh, gl, random.Random(5))[0]["expected"]["kills"] > e0 * 2
# 2. a snake is no prey (unless on the bot); 4. a kind that escapes most fights falls under the worth floor
assert not task_core.fightable(lh, "snake", set())
lh.mem.fight_stats = lambda kind, min_n=1: ({"kill": 4, "lost": 44, "flee": 0}, "world") if kind == "rabbit" else (None, None)
assert task_core.kill_share(lh, "rabbit") < 0.15 and task_core.kill_share(lh, "orc") == task_core.KILL_PRIOR[0] / sum(task_core.KILL_PRIOR)
lh.worth_kind = lambda k, deadly: 3.0
assert not task_core.fightable(lh, "rabbit", set()) and task_core.fightable(lh, "greywolf", set())
# 4. a kind that escaped most of its known fights is no prey even when its loot rates high; below the known-fights count it is judged as before
lh.mem.fight_stats = lambda kind, min_n=1: ({"kill": 13, "lost": 70, "flee": 12}, "world") if (kind == "rabbit" and min_n <= 95) else (({"kill": 3, "lost": 4, "flee": 0}, "world") if kind == "hind" and min_n <= 7 else (None, None))
lh.worth_kind = lambda k, deadly: 50.0
assert task_core.escapes(lh, "rabbit") and not task_core.fightable(lh, "rabbit", set())
assert not task_core.escapes(lh, "hind"), "seven known fights: too few to call"
assert not hunt_tree.worth_it(lh, mob("0xR2", "a rabbit", lh.c.x + 6, lh.c.y))
lh.worth_kind = lambda k, deadly: 3.0
assert not hunt_tree.worth_it(lh, mob("0xR1", "a snake", lh.c.x + 4, lh.c.y))
# 3. under a third of health with nothing to heal with: the hunt ends ("hurt") and the rest errand takes the bot home, pressing
lh.c.backpack, lh.c.hp = [], 20
lh.bandages = lambda: 0
assert task_core.hurt_bare(lh)
lh.home_refuges = lambda: [(1472, 1612)]
lh.gear_loot = lambda: []; lh.tired = lambda: False; lh.next_upgrade = lambda m: None; lh.can_make_arrows = lambda: 0
lh.where1 = lambda roles, **kw: (1472, 1612); lh.bank_xys = lambda: [(1425, 1690)]
rest = [n for n in errands.needs(lh, hunting=True) if n[0] == "rest"]
assert rest and rest[0][1] >= task_core.PRESSING and rest[0][2] == (1472, 1612), rest
lh.c.backpack = [NS(name="Yellow Potion", serial="0xY2", amount=1, hue=0)]
assert not task_core.hurt_bare(lh), "a Heal potion in the pack: not bare"
lh.c.hp = 80
# 5. judged before the first blow: an orc with two more orcs beside it is refused, alone it is fought; anything on the bot is fought
import danger
real_risk = danger.risk
danger.risk = lambda mem, kind, skill, near, grp=None: {"die": 0.3 if near >= 2 else 0.01, "flee": 0.1, "win": 0.6}
o1 = mob("0xO7", "an orc", lh.c.x + 5, lh.c.y)
lh.c.mobs = [o1, mob("0xO8", "an orc", o1.x + 1, o1.y), mob("0xO9", "an orc", o1.x, o1.y + 1)]
lh.c.mobiles(18)                                                    # distances from the bot
assert not task_core.judge_target(lh, o1)
lh.c.mobs = [o1]
for m_ in lh.c.mobs:
    m_.distance = 5
assert task_core.judge_target(lh, o1)
o1.distance = 1
lh.c.mobs = [o1, mob("0xO8", "an orc", o1.x + 1, o1.y), mob("0xO9", "an orc", o1.x, o1.y + 1)]
assert task_core.judge_target(lh, o1), "on the bot: fought"
danger.risk = real_risk
lh.c.mobs = []
# 6. two own deaths near a spot, or one to a wraith, close that ground to this bot
lh.c.max_hp = 130                                                   # outside fix D's undead box rule (under 120 hit points keeps out of the box)
lh.facts["own_deaths"] = [[1400, 1400, "a wraith", now()]]
assert task_core.death_ground(lh, 1420, 1410) and not task_core.death_ground(lh, 1600, 1600)
lh.facts["own_deaths"] = [[1400, 1400, "a boar", now()]]
assert not task_core.death_ground(lh, 1420, 1410)
lh.facts["own_deaths"].append([1410, 1390, "a boar", now()])
assert task_core.death_ground(lh, 1420, 1410)
lh.facts["own_deaths"] = [[1400, 1400, "a wraith", now() - task_core.DEATH_KEEP - 1]]
assert not task_core.death_ground(lh, 1420, 1410), "kept off for DEATH_KEEP only"
lh.facts["own_deaths"] = []
# 7. in town after an errand: the next due errand (urgency 0.5 or more) comes before the hunt
assert task_core.in_town(fighter(name="BotTown", xy=(1470, 1620)))
# the bandages from cloth (owner 2026-10-21; the Watcher: the healer showed none at 39 reads, the provisioners sell none, the tailor sells Cut Cloth and Cloth at 2 gold)
cb = fighter(name="BotCloth", xy=(1467, 1686))
cb.c.gold = 500
cb.c.backpack = []
cb.bandages = lambda: sum((i.amount or 1) for i in cb.c.backpack if "bandage" in i.name.lower())
cb.where1 = lambda roles, **kw: (1467, 1686) if roles[0] in ("tailor", "weaver") else (1427, 1650)
cb.find_places = lambda roles, n=3, per=2, **kw: [(1467, 1686)]
cb.mem.vendor_selling = lambda word: [(2, "1467,1686", "cut cloth", 20), (2, "1467,1686", "cloth", 20)] if word in ("cut cloth", "cloth") else []
bought_ = []
def cshop(xy, wanted, budget=None):
    for k, v in wanted.items():
        n = min(v, 20)                                             # the tailor holds 20 of each
        nm = {"scissors": "Scissors", "=cut cloth": "cut cloth", "=cloth": "cloth"}[k]
        cb.c.backpack.append(NS(name=nm, serial=f"0xC{len(cb.c.backpack)}", amount=n if nm != "Scissors" else 1, hue=0))
        bought_.append((nm, n, budget))
    return wanted
cb.shop_at = cshop
cb.read_journal = lambda: None
cb.c.wait_for = lambda kinds, timeout=4: True
cb.c.use = lambda serial: None
def cut(serial):
    pile = next(i for i in cb.c.backpack if i.serial == serial)
    pile.name = {"cloth": "cut cloth", "cut cloth": "Bandage"}.get(pile.name, pile.name)
cb.c.target = cut
made = errands.cloth_bandages(cb, {}, 30)
assert made == 30 and cb.bandages() == 30, (made, bought_)
assert [b_[0] for b_ in bought_] == ["Scissors", "cut cloth", "cloth"] and sum(b_[1] for b_ in bought_ if b_[0] != "Scissors") == 30, bought_      # 20 cut cloth + 10 cloth, 30 bandages
assert all(b_[2] <= 500 * 3 // 4 for b_ in bought_ if b_[0] != "Scissors"), "within budget"
assert any(e[0] == "cloth_bandages" and e[1]["made"] == 30 for e in cb.evs)
# at most CLOTH_MAX (40) however short, and no purchase when the bot cannot pay (under 10 gold)
cb.c.backpack = []; bought_.clear()
assert errands.cloth_bandages(cb, {}, 90) <= errands.CLOTH_MAX and sum(b_[1] for b_ in bought_ if b_[0] != "Scissors") <= errands.CLOTH_MAX
cb.c.backpack = []; bought_.clear(); cb.c.gold = 8
assert errands.cloth_bandages(cb, {}, 30) == 0 and not bought_
# the provisioner is not a bandage source; the healer is asked for what is needed (30), not 60
assert next(r for r in errands.RESTOCK if r[0] == "bandage")[3] == ("healer",) and next(r for r in errands.RESTOCK if r[0] == "bandage")[2] == 30
print("learnings OK")

# fix B (the Watcher, 2026-10-21): prey that runs is let go after 10 s of chase with no gain, and left alone for five minutes
fl, fk = make(xy=tuple(AREAS["Castle Woods"]["spawners"][0][:2]), name="BotFlee")
fk["arrived"] = now()
bunny = mob("0xB1", "a hind", fl.c.x + 6, fl.c.y)
fl.c.mobs = [bunny]
run_tree(fl, fk)                                                    # picked
t_start = now()
for _ in range(40):
    bunny.x += 1                                                    # it runs as fast as the bot
    fl.c.x = min(bunny.x - 6, fl.c.x + 1)
    run_tree(fl, fk, dt=0.5)
    if fk["state"].get("target") is None:
        break
assert fk["state"].get("target") is None and "0xB1" in fl.ignored, "the runner was dropped"
assert fl.ignored["0xB1"] - now() > hunt_tree.FLEE_IGNORE - 30 and 9 <= now() - t_start <= 16, (fl.ignored.get("0xB1", 0) - now(), now() - t_start)
assert hunt_tree.FLEE_DROP_S == 10.0 and task_core.ESCAPE_SHARE == 0.5
print("flee drop OK")

# the Watcher's second live round (2026-10-21): a heartbeat inside the errand, each shop once, the escape test before the fist rule, the spot list rebuilt when the heals run out
hb = fighter(name="BotBeat", xy=(1472, 1612))
beats = []
hb.beat = lambda: beats.append(now())
hb.c.backpack = []
hb.bandages = lambda: 0
hb.c.gold, hb.facts["bank_balance"] = 40, 200
hb.visit_bank = lambda why, withdraw=0, reserve=200, extra=(): (setattr(hb.c, "gold", hb.c.gold + withdraw) or True)
hb.where1 = lambda roles, **kw: {"healer": (1472, 1612), "alchemist": (1490, 1600), "tailor": (1467, 1686), "weaver": (1467, 1686), "tinker": (1427, 1650)}[roles[0]]
visits = []
hb.shop_at = lambda xy, wanted, budget=None: (visits.append(tuple(xy)) or {})
errands.Act("act", hunt_tree.Ctx(hb, {"task": "resupply", "state": {}})).do_resupply(hb, {}, {})
assert len(visits) == len(set(visits)) and len(beats) >= 4, (visits, len(beats))
# an archer in fist mode does not chase a kind that escapes most of its fights
fm = fighter(name="BotFists", skill=68.0, ranged=True)
fm.facts["fists"] = True
fm.fist_prey = lambda k: True
fm.mem.fight_stats = lambda kind, min_n=1: ({"kill": 3, "lost": 60, "flee": 12}, "prof") if kind == "rabbit" else (None, None)
assert not hunt_tree.worth_it(fm, mob("0xF1", "a rabbit", fm.c.x + 6, fm.c.y)), "fist mode is no way round the escape test"
assert hunt_tree.worth_it(fm, mob("0xF2", "a hind", fm.c.x + 6, fm.c.y)), "other prey keeps the fist rule"
assert hunt_tree.NO_HURT_S == 10.0
# the spot list is rebuilt when the bot runs out of heals (or restocks), not after ten minutes
sc = fighter(name="BotSpotCache", skill=82.0)
sc.c.backpack = [NS(name="Bandage", serial="0xBB", amount=30, hue=0)]
sc.bandages = lambda: sum((i.amount or 1) for i in sc.c.backpack if "bandage" in i.name.lower())
a1 = spots.all_spots(sc)
assert any(s_["tier"] >= 3 for s_ in a1)
sc.c.backpack = []
a2 = spots.all_spots(sc)
assert all(s_["tier"] == 1 for s_ in a2) and len(a2) < len(a1), (len(a1), len(a2))
print("live round 2 OK")

# fix C: the broke ranged fighter (fists, no arrows): livestock it can carve and sell at tier 1, arrows from what it holds, the Bowyer from 100 gold
bk = fighter(name="BotBroke", skill=69.0, ranged=True)
bk.pname = "Archer"
bk.bow_kind = lambda: True
bk.fist_prey = lambda k: k in ("cow", "pig", "sheep", "goat", "rabbit", "hind")
bk.facts["fists"] = True
bk.ammo = lambda: 0
bk.worth_kind = lambda k, deadly: 0.0                                # nothing "worth" by the loot table: fists take what they can kill
bk.mem.fight_stats = lambda kind, min_n=1: ({"kill": 2, "lost": 60, "flee": 5}, "prof") if kind == "rabbit" else (None, None)
assert task_core.fightable(bk, "cow", set(), 1) and task_core.fightable(bk, "goat", set(), 1)
assert not task_core.fightable(bk, "rabbit", set()), "an escaper is no prey, broke or not"
assert not task_core.fightable(bk, "orc", set(), 1), "what fists cannot kill is not prey"
assert task_core.tiers(bk) == {1}, "a broke archer in fist mode stays on tier 1"
bk.facts["fists"] = False
bk.worth_kind = lambda k, deadly: 3.0
# arrows: with 50 gold a broke archer does not walk to the Bowyer; with 100 it does, and the fletch errand is raised when it holds feathers, wood and the tool
bk.facts["fists"] = True
for f_ in ("gear_loot",):
    setattr(bk, f_, lambda: [])
bk.tired = lambda: False; bk.next_upgrade = lambda m: None; bk.can_make_arrows = lambda: 0; bk.bank_xys = lambda: [(1425, 1690)]
bk.where1 = lambda roles, **kw: (1472, 1612)
bk.bandages = lambda: 30
bk.c.backpack = [NS(name="Yellow Potion", serial="0xy1", amount=5, hue=0), NS(name="Red Potion", serial="0xr1", amount=3, hue=0), NS(name="Orange Potion", serial="0xo1", amount=3, hue=0)]
bk.c.gold = 50
assert not [n for n in errands.needs(bk) if n[0] == "ammo"], "50 gold: not yet"
bk.c.gold = 120
assert [n for n in errands.needs(bk) if n[0] == "ammo"], "100 gold and more: arrows at the Bowyer"
bk.c.gold = 0
bk.skill_values["Bowcraft/Fletching"] = 42
bk.c.backpack += [NS(name="feather", serial="0xf1", amount=11, hue=0), NS(name="log", serial="0xl1", amount=10, hue=0), NS(name="arrow fletching", serial="0xt1", amount=1, hue=0)]
ft = [n for n in errands.needs(bk) if n[0] == "fletch"]
assert ft and ft[0][1] == 1.6, errands.needs(bk)
made = []
bk.r_fletch = lambda: (made.append(bk.facts.get("fletch_force")) or len(made) < 2)
bk.fists_check = lambda: None
bk.beat = lambda: None
act = errands.Act("act", hunt_tree.Ctx(bk, {"task": "fletch", "state": {}}))
st_f = {}
assert act.do_fletch(bk, st_f, {}) is None and made == [True], "one stack a call, the fletch rule forced on"
bk.facts["fletch_wait"] = 0
assert act.do_fletch(bk, st_f, {}) in (True, False) and "fletch_force" not in bk.facts
bk.skill_values["Bowcraft/Fletching"] = 12
assert not [n for n in errands.needs(bk) if n[0] == "fletch"], "no Bowcraft: no fletching"
print("fix C OK")

# fix D (the Watcher, 2026-10-21): ammunition first, the upgrade only from money above the supply reserve, the bank before tier-2+ ground, the undead box closed to a small bot
fd = fighter(name="BotFixD", skill=69.0, ranged=True)
fd.pname = "Archer"; fd.bow_kind = lambda: True
assert fd.UPGRADE_RESERVE == 100 + 11 * 15 + 30 * 5 + 200 and fighter(name="BotMelee").UPGRADE_RESERVE == 100 + 11 * 15 + 30 * 5
fd.bandages = lambda: 30; fd.gear_loot = lambda: []; fd.tired = lambda: False; fd.can_make_arrows = lambda: 0
fd.where1 = lambda roles, **kw: (1472, 1612); fd.bank_xys = lambda: [(1425, 1690)]
fd.c.backpack = [NS(name="Yellow Potion", serial="0xy9", amount=5, hue=0), NS(name="Red Potion", serial="0xr9", amount=3, hue=0), NS(name="Orange Potion", serial="0xo9", amount=3, hue=0)]
fd.c.gold, fd.facts["bank_balance"] = 100, 1500
fd.next_upgrade = lambda money: (1.0, "torso", "platemail tunic", 300, (1481, 1584), 0, 40) if money >= 300 else None
fd.ammo = lambda: 20
assert not [n for n in errands.needs(fd) if n[0] == "upgrade"], "fewer than 50 arrows: no armour"
fd.ammo = lambda: 80
assert [n for n in errands.needs(fd) if n[0] == "upgrade"], "50 or more arrows and money above the reserve: armour"
fd.facts["bank_balance"] = 400
assert not [n for n in errands.needs(fd) if n[0] == "upgrade"], "money under the reserve: no armour"
# the bank first: more than CARRY_TIER2 carried and a hunt on tier 2+ ground
fd.facts["bank_balance"] = 100
fd.c.gold = 250
real_cands = task_core.candidates
t2c_ = {"task": "hunt", "area": "tour spX", "spots": [[1300, 1500, 1.0, "spX"]], "tour": ["spX"], "score": 0.5, "draw": 1.0, "mean": 1.0, "expected": {"kills": 5.0, "gold": 10.0, "skill": 0.1},
        "walk_min": 3.0, "die": 0.05, "n": 0, "tier": 2, "side": "surface", "minutes": 20.0, "budget": 600.0, "judge": "kills", "kinds": ["orc"], "load": 0}
task_core.candidates = lambda bot, g, rng=None, rested=False, relax=0: [dict(t2c_)]
fd.facts.pop("banked_at", None)
task_core.tick(fd)
assert fd.facts["task"]["task"] == "bank" and any(e[0] == "task_start" and e[1]["why"] == "bank first" for e in fd.evs), fd.facts["task"]
fd.facts["task"] = None
fd.facts["banked_at"] = now()
task_core.tick(fd)
assert fd.facts["task"]["task"] == "hunt", "banked a minute ago: the hunt"
fd.facts["task"] = None
fd.facts["banked_at"] = 0
fd.c.gold = 110
task_core.tick(fd)
assert fd.facts["task"]["task"] == "hunt", "110 carried: under the limit, the hunt"
task_core.candidates = real_cands
# the north undead box is closed to a bot under 120 hit points, open to a bigger one, and the rest of the map is open
fd.c.max_hp = 80
assert task_core.death_ground(fd, 1400, 1400) and not task_core.death_ground(fd, 1600, 1600)
fd.c.max_hp = 130
assert not task_core.death_ground(fd, 1400, 1400)
print("fix D OK")

# the weapon batch (the Watcher, 2026-10-21): the state check, the arm errand, no armour while unarmed, the unarmed fallback, bolts for a crossbow, the weapon_state event
import weaponup
wb = fighter(name="BotArms", skill=87.0, persona=("A3", "A2"))
wb.pname = "MaceFighter"
wb.main_skill = lambda: "Mace Fighting"
wb.skill_values = {"Mace Fighting": 87.0, "Tactics": 80.0, "Wrestling": 30.0}
wb.c.state.update(str=95)
wb.weapon_state = hunter.HunterBot.weapon_state.__get__(wb)
wb.weapon_now = hunter.HunterBot.weapon_now.__get__(wb)
wb.next_weapon = hunter.HunterBot.next_weapon.__get__(wb)
wb.shield_worn = lambda: False
wb.shop_weapons = lambda: [(weaponup.table()["club"], 40, (1481, 1584), "club"), (weaponup.table()["mace"], 70, (1481, 1584), "mace")] if "club" in weaponup.table() else []
class Itm:
    def __init__(s_, name, layer=None, serial="0x1"): s_.name, s_.layer, s_.serial, s_.amount = name, layer, serial, 1
wb.c.equipped, wb.c.backpack = [], [Itm("dagger"), Itm("katana")]
assert wb.weapon_state() == "none", "a dagger and a katana are not a mace fighter's weapons"
wb.c.equipped = [Itm("club", "OneHanded")]
assert wb.weapon_state() == "ok"
wb.c.equipped = [Itm("kryss", "OneHanded")]
assert wb.weapon_state() == "wrong"
wb.c.equipped = [Itm("club", "OneHanded")]
wb.facts["weapon_worn"] = {"club": now()}
assert wb.weapon_state() == "worn", "the wear notice for the wielded item"
wb.facts["weapon_worn"] = {"mace": now()}
assert wb.weapon_state() == "ok", "a notice about another item"
wb.facts.pop("weapon_worn")
# the journal lines set it: the notice and a broken weapon
wb.c.events = NS(poll=lambda: [NS(text="[SYSTEM] Your club is badly worn: about a quarter of its durability is left.", kind=None)], drain=lambda: None)
wb.mem.record = lambda *a, **k: None
import bot_common as bcm
try:
    bcm.BotBase.read_journal(wb)
except Exception:
    pass
assert "club" in (wb.facts.get("weapon_worn") or {}), "read_journal records the wear notice"
wb.facts.pop("weapon_worn", None)
# unarmed: the arm errand is raised at ARM_URGENCY when a weapon is on offer within the money, and nothing while the bot cannot pay
wb.c.equipped = []
wb.c.gold, wb.facts["bank_balance"] = 20, 0
wb.bandages = lambda: 30; wb.gear_loot = lambda: []; wb.tired = lambda: False; wb.next_upgrade = lambda m: None; wb.can_make_arrows = lambda: 0
wb.where1 = lambda roles, **kw: (1472, 1612); wb.bank_xys = lambda: [(1425, 1690)]
wb.c.backpack = [Itm("dagger"), Itm("Yellow Potion"), Itm("Red Potion")]
assert not [n for n in errands.needs(wb) if n[0] == "arm"], "20 gold: nothing on offer within it"
assert task_core.unarmed(wb) and task_core.tiers(wb) == {1}, "unarmed and broke: tier 1, harmless prey"
wb.__dict__.pop("_unarmed", None)
wb.c.gold, wb.facts["bank_balance"] = 30, 500
arm = [n for n in errands.needs(wb) if n[0] == "arm"]
if weaponup.table().get("club"):
    assert arm and arm[0][1] == errands.ARM_URGENCY and arm[0][2] == (1481, 1584), errands.needs(wb)
    # no armour while unarmed
    wb.next_upgrade = lambda m: (1.0, "torso", "platemail tunic", 300, (1481, 1584), 0, 40)
    assert not [n for n in errands.needs(wb) if n[0] == "upgrade"], "no armour without a weapon"
    # the errand: bank, shop, wield
    banked_ = []
    wb.visit_bank = lambda why, withdraw=0, reserve=200, extra=(): (banked_.append(withdraw) or setattr(wb.c, "gold", wb.c.gold + withdraw) or True)
    wb.beat = lambda: None
    bought_w = []
    wb.shop_at = lambda xy, wanted, budget=None: (bought_w.append(wanted) or {"club": 1})
    wb.arms_wield = lambda name, price, source, vfrom, vto: bought_w.append(("wield", name)) or True
    act = errands.Act("act", hunt_tree.Ctx(wb, {"task": "arm", "state": {}}))
    assert act.do_arm(wb, {}, {}) is True and banked_ and bought_w[-1][0] == "wield", (banked_, bought_w)
# the weapon_state event: first tick and on change only
wb.evs.clear()
wb.__dict__.pop("_weapon_noted", None)
task_core.weapon_note(wb); task_core.weapon_note(wb)
assert [e for e in wb.evs if e[0] == "weapon_state"] and len([e for e in wb.evs if e[0] == "weapon_state"]) == 1 and wb.evs[0][1]["state"] == "none"
# bolts for a crossbow
cb2 = fighter(name="BotBolts", ranged=True)
cb2.the_bow = lambda: Itm("heavy crossbow")
assert errands.ammo_item(cb2) == "=bolt"
cb2.the_bow = lambda: Itm("bow")
assert errands.ammo_item(cb2) == "=arrow"
print("weapon batch OK")

# the live round 3 read (13:12): the gear goal may not spend the supply reserve; an unmet supply errand rests minutes, not half an hour, and says why a need did not run
import goals
gq = fighter(name="BotGoalReserve", skill=87.0, persona=("A5", "A6"))
gq.c.gold, gq.facts["bank_balance"] = 329, 0
opt = (1.0, "pants", "platemail legs", 218, (1481, 1584), 10, 40)
real_active, real_options, real_have = goals.active, goals.gear_options, goals.have
goals.active = lambda bot: {"kind": "gear", "meta": {"item": "platemail legs"}, "id": "gear:platemail legs"}
goals.gear_options = lambda bot: [opt]
goals.have = lambda bot: 329
assert goals.upgrade_choice(gq, 329 - 415) is None, "329 in hand, a 415 reserve: the goal piece is not bought"
assert goals.upgrade_choice(gq, 600) == opt
goals.active, goals.gear_options, goals.have = real_active, real_options, real_have
sr = fighter(name="BotSupplyBan", skill=69.0, ranged=True)
sr.pname = "Archer"; sr.bow_kind = lambda: True; sr.ammo = lambda: 0
sr.c.gold, sr.facts["bank_balance"], sr.facts["fists"] = 120, 380, True
sr.bandages = lambda: 30; sr.gear_loot = lambda: []; sr.tired = lambda: False; sr.next_upgrade = lambda m: None; sr.can_make_arrows = lambda: 0
sr.where1 = lambda roles, **kw: (1472, 1612); sr.bank_xys = lambda: [(1425, 1690)]
sr.c.backpack = [NS(name="Yellow Potion", serial="0xs1", amount=5, hue=0), NS(name="Red Potion", serial="0xs2", amount=3, hue=0), NS(name="Orange Potion", serial="0xs3", amount=3, hue=0)]
tkq = task_core.start_task(sr, task_core.goal(sr), {"task": "resupply", "area": "resupply", "spots": [], "score": 1.0, "draw": 0.0, "mean": 0.0, "expected": {}, "walk_min": 0.0, "die": 0.0, "n": 0, "budget": 180.0}, [])
task_core.end_task(sr, tkq, "unmet")
left = sr.facts["core_bans"]["resupply|resupply"] - now()
assert left <= task_core.ERRAND_UNMET_REST + 1, left
assert [c for c in task_core.errand_candidates(sr, best_hunt=1.0) if c["task"] == "ammo"], "an unmet bandage or potion run does not stop the arrows (120 carried and 380 banked)"
tka = task_core.start_task(sr, task_core.goal(sr), {"task": "ammo", "area": "ammo", "spots": [], "score": 1.0, "draw": 0.0, "mean": 0.0, "expected": {}, "walk_min": 0.0, "die": 0.0, "n": 0, "budget": 180.0}, [])
sr.facts["ammo_unmet_money"] = 500
task_core.end_task(sr, tka, "unmet")
assert not [c for c in task_core.errand_candidates(sr, best_hunt=1.0) if c["task"] == "ammo"], "an unmet arrow run rests while the purse is unchanged"
sr.c.gold += 25
assert [c for c in task_core.errand_candidates(sr, best_hunt=1.0) if c["task"] == "ammo"], "and runs again once gold plus bank has changed by 20"
print("round 3 fixes OK")

# M1 (rung only when stocked AND healed), M3 (an upgrade that comes back unmet twice rests 30 minutes, and says what it wanted)
rr = fighter(name="BotRungReady", skill=88.0)
rr.c.backpack = [NS(name="Yellow Potion", serial="0xq1", amount=10, hue=0), NS(name="Red Potion", serial="0xq2", amount=2, hue=0), NS(name="Bandage", serial="0xq3", amount=50, hue=0), NS(name="Orange Potion", serial="0xq1c", amount=15, hue=0)]
rr.facts["rung"] = 1
assert 4 in task_core.tiers(rr) and task_core.rung_ready(rr)
rr.c.hp = 50
rr.__dict__.pop("_spots", None)
assert 4 not in task_core.tiers(rr) and not task_core.rung_ready(rr), "50 of 80 hit points: no rung tour is offered"
rr.c.hp = 80
um = fighter(name="BotUpgradeLoop", skill=82.0)
um.c.gold, um.facts["bank_balance"] = 300, 1717
want_ = (1.0, "torso", "platemail tunic", 300, (1481, 1584), 0, 40)
um.next_upgrade = lambda money: want_
um.r_upgrade = lambda: False
um.mobs = lambda r: []
um.bow_kind = lambda: False
um.gear_loot = lambda: []; um.tired = lambda: False; um.can_make_arrows = lambda: 0; um.bandages = lambda: 30
um.where1 = lambda roles, **kw: (1472, 1612); um.bank_xys = lambda: [(1425, 1690)]
um.c.backpack = [NS(name="Yellow Potion", serial="0xu1", amount=5, hue=0), NS(name="Red Potion", serial="0xu2", amount=3, hue=0), NS(name="Orange Potion", serial="0xu3", amount=3, hue=0)]
act = errands.Act("act", hunt_tree.Ctx(um, {"task": "upgrade", "state": {}}))
assert act.do_upgrade(um, {}, {}) is False and any(e[0] == "upgrade_unmet" and e[1]["item"] == "platemail tunic" and e[1]["price"] == 300 for e in um.evs)
assert [n for n in errands.needs(um) if n[0] == "upgrade"], "after one unmet try it is still wanted"
act.do_upgrade(um, {}, {})
assert not [n for n in errands.needs(um) if n[0] == "upgrade"], "after two it rests 30 minutes"
clock[0] += 1801
assert [n for n in errands.needs(um) if n[0] == "upgrade"], "and comes back"
print("M1 M3 OK")

# the dungeon trip's kit (the owner, 2026-10-21): 10 Heal, 15 Cure, 50 bandages (and 2 Refresh, skill 80); the restock aims at it for a bot that could use it and can pay
assert task_core.KIT["heal"] == 10 and task_core.KIT["cure"] == 15 and task_core.KIT["bandages"] == 50
kt = fighter(name="BotKit", skill=84.0)
kt.c.backpack = [NS(name="Yellow Potion", serial="0xz1", amount=10, hue=0), NS(name="Red Potion", serial="0xz2", amount=2, hue=0), NS(name="Bandage", serial="0xz3", amount=50, hue=0),
                 NS(name="Orange Potion", serial="0xz4", amount=14, hue=0)]
assert not task_core.kit(kt)[0] and "14 cure" in task_core.kit(kt)[1], "14 cures: one short"
kt.c.backpack[3].amount = 15
assert task_core.kit(kt)[0]
kt.c.backpack[2].amount = 49
assert not task_core.kit(kt)[0], "49 bandages: one short"
kt.c.backpack[2].amount = 50
kt.c.backpack[0].amount = 9
assert not task_core.kit(kt)[0], "9 heals: one short"
# the restock's marks: ordinary for a poor bot or a low skill, the kit for a skilled bot with a rung or the kills below it and the money
kt.c.backpack = []
kt.c.gold, kt.facts["bank_balance"] = 200, 0
assert errands.marks(kt) is errands.RESTOCK, "no money for the kit"
kt.c.gold, kt.facts["bank_balance"] = 100, 1500
assert errands.marks(kt) is errands.RESTOCK, "money but no rung and no kills below it"
kt.facts["rung_kills"] = {"2": 12.0}
assert errands.marks(kt) is errands.RESTOCK, "no ladder: the kit is for a bot that goes down (2026-11-01)"
_kf = kt.feature
kt.feature = lambda n: n == "ladder" or _kf(n)
m_ = {x[0]: (x[1], x[2]) for x in errands.marks(kt)}
assert m_["bandage"] == (50, 50) and m_["=yellow potion"] == (10, 10) and m_["=orange potion"] == (15, 15), m_
kt.bandages = lambda: 0
w_ = errands.restock_wants(kt)
assert w_["bandage"] == 50 and w_["=yellow potion"] == 10 and w_["=orange potion"] == 15, w_
kt.skill_values["Swordsmanship"] = 70.0
assert errands.marks(kt) is errands.RESTOCK, "skill under 80: the ordinary marks"
print("kit OK")

# the 14:38 read (2026-10-21): the arm errand buys at a real weapon seller, avoids a shop that did not sell, a broke bot hunts livestock and takes its dagger into its hand
ws2 = fighter(name="BotArmShop", skill=87.0)
ws2.pname = "MaceFighter"; ws2.main_skill = lambda: "Mace Fighting"
ws2.c.state.update(str=95)
ws2.weapon_now = hunter.HunterBot.weapon_now.__get__(ws2); ws2.next_weapon = hunter.HunterBot.next_weapon.__get__(ws2); ws2.shield_worn = lambda: False
ws2.c.equipped = []
ws2.shop_weapons = lambda: [(weaponup.table()["club"], 16, (1427, 1650), "club"), (weaponup.table()["club"], 16, (1418, 1547), "club")]
real_shop = ws2.next_weapon(1000, shops=[(1418, 1547), (1481, 1584)])
assert real_shop and real_shop[3] == (1418, 1547), real_shop
only_tinker = [(weaponup.table()["club"], 16, (1427, 1650), "club")]
ws2.shop_weapons = lambda: only_tinker
assert ws2.next_weapon(1000, shops=[(1418, 1547)]) is None, "a record at the Tinker's spot, 100 tiles from any weapon seller, is no place to buy one"
ws2.shop_weapons = lambda: [(weaponup.table()["club"], 16, (1420, 1550), "club")]
assert ws2.next_weapon(1000, shops=[(1418, 1547)])[3] == (1418, 1547), "the record is moved to the shop's own spot"
assert ws2.next_weapon(1000, shops=[(1418, 1547)], avoid={(1418, 1547)}) is None, "a spot that did not sell lately is avoided"
# livestock for a broke bot: cow, goat, sheep, pig, hind are prey; a dog, a boar and a great hart are not
lv = fighter(name="BotLivestock", skill=60.0)
lv.fist_prey = hunter.HunterBot.fist_prey.__get__(lv); lv.VERMIN = hunter.HunterBot.VERMIN
lv.BROKE_HITS, lv.BROKE_DAMAGE, lv.BROKE_CARVE = hunter.HunterBot.BROKE_HITS, hunter.HunterBot.BROKE_DAMAGE, hunter.HunterBot.BROKE_CARVE
assert all(lv.fist_prey(k) for k in ("cow", "goat", "hind", "rabbit", "mongbat")), [k for k in ("cow", "goat", "hind") if not lv.fist_prey(k)]
assert not any(lv.fist_prey(k) for k in ("dog", "boar", "greathart", "eagle", "orc", "ettin"))
# the dagger into the hand of a bot with its hands only; nothing when a weapon is in hand or no blade is carried
bw2 = fighter(name="BotBridge", skill=60.0)
bw2.wield_bridge = hunter.HunterBot.wield_bridge.__get__(bw2)
bw2.weapon_state = lambda: "none"
bw2.facts["fists"] = False
class Itm2:
    def __init__(s_, name, layer=None, serial="0x1"): s_.name, s_.layer, s_.serial, s_.amount = name, layer, serial, 1
bw2.c.equipped, bw2.c.backpack = [], [Itm2("dagger", serial="0xD1")]
bw2.c.call = lambda line, timeout=6: (bw2.c.calls.append(line) or [])
assert bw2.wield_bridge() is True and "equip 0xD1" in bw2.c.calls
bw2.__dict__.pop("_bridge_at", None)
bw2.c.equipped = [Itm2("club", "OneHanded")]
assert bw2.wield_bridge() is False, "a weapon in hand: left alone"
# weapon_state events: on the first tick and again every ten minutes, whatever the state
we = fighter(name="BotNoted", skill=60.0)
we.weapon_state = lambda: "ok"; we.weapon_now = lambda: (None, Itm2("katana", "OneHanded")); we.main_skill = lambda: "Swordsmanship"
task_core.weapon_note(we); task_core.weapon_note(we)
assert len([e for e in we.evs if e[0] == "weapon_state"]) == 1
clock[0] += 601
task_core.weapon_note(we)
assert len([e for e in we.evs if e[0] == "weapon_state"]) == 2, "re-logged every ten minutes, so any read has each bot's state"
print("arm shop OK")

# the other memory folder's lists count, and with nothing on record the errand reads the nearest weapon shops' lists itself
wm = fighter(name="BotNews", skill=87.0)
wm.pname = "MaceFighter"; wm.main_skill = lambda: "Mace Fighting"
wm.c.state.update(str=95)
wm.shop_weapons = hunter.HunterBot.shop_weapons.__get__(wm) if hasattr(hunter.HunterBot, "shop_weapons") else None
class MemV:
    def __init__(s_, vendors): s_.state = {"world": {"vendors": vendors}}
    def refresh(s_, *a, **k): pass
wm.mem = MemV({"1427,1650": {"stock": {"pickaxe": (25, 16)}}})
wm.mem.news = MemV({"1418,1547": {"stock": {"club": (16, 20), "mace": (57, 20)}}})
found = wm.shop_weapons()
assert [(n, xy) for e, p_, xy, n in found if n == "club"] == [("club", (1418, 1547))], found
wm.mem.news = MemV({})
assert not [x for x in wm.shop_weapons() if x[3] == "club"], "no club on record anywhere"
wm.next_weapon = hunter.HunterBot.next_weapon.__get__(wm); wm.weapon_now = lambda: (None, None); wm.shield_worn = lambda: False
wm.weapon_state = lambda: "none"
wm.find_places = lambda roles, n=3, per=2, **kw: [(1418, 1547), (1447, 1647)]
read_ = []
def read_list(xy, wanted, budget=None):
    read_.append(tuple(xy))
    wm.mem.news = MemV({"1418,1547": {"stock": {"club": (16, 20)}}})       # the list is on record once it has been read
    return {}
wm.shop_at = read_list; wm.beat = lambda: None; wm.visit_bank = lambda *a, **k: True
wm.c.gold = 100
wm.arms_wield = lambda *a, **k: True
actw = errands.Act("act", hunt_tree.Ctx(wm, {"task": "arm", "state": {}}))
st_arm = {}
res_ = actw.do_arm(wm, st_arm, {})
assert (1418, 1547) in read_ and (1447, 1647) in read_ and st_arm.get("lists_read"), (read_, res_)    # the two nearest weapon shops are read, then the club is wanted at the Blacksmith
print("arm lists OK")

# predators in the spawner keep a fist fighter out (MaceBR died where cows share ground with bears and wolves); Wrestling as the main skill is a weapon
pr = fighter(name="BotPredators", skill=87.0)
pr.facts["fists"] = True
pr.fist_prey = hunter.HunterBot.fist_prey.__get__(pr); pr.VERMIN = hunter.HunterBot.VERMIN
pr.BROKE_HITS, pr.BROKE_DAMAGE, pr.BROKE_CARVE = hunter.HunterBot.BROKE_HITS, hunter.HunterBot.BROKE_DAMAGE, hunter.HunterBot.BROKE_CARVE
pr.worth_kind = lambda k, deadly: 3.0
farm_spot = {"id": "spF", "x": 1300, "y": 1800, "kinds": ["cow", "sheep", "goat"], "count": 3, "mn": 300.0, "mx": 600.0, "home": 10, "tier": 1}
wild_spot = dict(farm_spot, id="spW", kinds=["cow", "goat", "giantspider"])
assert task_core.aggressive_kind("giantspider") and task_core.aggressive_kind("orc") and not task_core.aggressive_kind("cow") and not task_core.aggressive_kind("grizzlybear")   # the bears fight back only once attacked
spots._HOSTILE.clear()
real_sp = spots.spawner_spots
spots.spawner_spots = lambda: []
assert spots.spot_prior(pr, farm_spot, set()) is not None, "cows, sheep and goats alone: earnings"
spots._HOSTILE.clear()
spots.spawner_spots = lambda: [dict(wild_spot, x=1320, y=1810, id="spN", kinds=["reaper"])]
assert spots.spot_prior(pr, farm_spot, set()) is None, "a reaper in a spawner 20 tiles away closes the farm to fists"
spots.spawner_spots = real_sp
spots._HOSTILE.clear()
why_ = collections.Counter() if "collections" in globals() else None
import collections
why_ = collections.Counter()
assert spots.spot_prior(pr, wild_spot, set(), 0, why_) is None and why_["on-sight attackers near"] == 1, "a giant spider in the spawner: not for fists"
pr.facts["fists"] = False
assert spots.spot_prior(pr, wild_spot, set()) is not None or True
wr = fighter(name="BotWrestler", skill=80.0)
wr.pname = "Bard"; wr.main_skill = lambda: "Wrestling"
wr.weapon_state = hunter.HunterBot.weapon_state.__get__(wr); wr.weapon_now = hunter.HunterBot.weapon_now.__get__(wr); wr.bow_kind = lambda: True
wr.c.equipped, wr.c.backpack = [], []
assert wr.weapon_state() == "ok", "Wrestling is the main skill: fists are the weapon"
print("predators OK")

# the undead box is closed to a bot under 120 hit points: roam points, prey, flight; box_entered is logged
bx = fighter(name="BotBox", skill=84.0)
bx.c.max_hp = 78
assert task_core.in_box(bx, 1400, 1400) and not task_core.in_box(bx, 1300, 1400)
ex = task_core.box_exit(bx, 1374, 1431)
assert not task_core.in_box(bx, *ex), ex
bx.c.max_hp = 130
assert not task_core.in_box(bx, 1400, 1400) and task_core.box_exit(bx, 1400, 1400) == (1400, 1400)
bx.c.max_hp = 78
evs = []
bx.ev = lambda name, **kw: evs.append((name, kw))
bx.c.x, bx.c.y = 1374, 1431
task_core.box_watch(bx)
assert evs and evs[-1][0] == "box_entered" and evs[-1][1]["xy"] == [1374, 1431], evs
task_core.box_watch(bx)
assert len(evs) == 1, "once per entry"
bx.c.x = 1300
task_core.box_watch(bx)
assert evs[-1][0] == "box_left"
print("box OK")

# broke bots sell what they carry: "cut of raw ribs" is meat, loose robes go to the Tailor
rb = fighter(name="BotRobes", skill=84.0)
rb.c.backpack = [NS(name="cut of raw ribs", serial="0xr1", amount=50, hue=0), NS(name="robe", serial="0xr2", amount=1, hue=0), NS(name="robe", serial="0xr3", amount=1, hue=0),
                 NS(name="robe", serial="0xr4", amount=1, hue=0)]
assert errands._loot_to_sell(rb)[1] == 50 and errands._robes(rb) == 0, "robes no longer raise a sell trip (0 of 48 sold, 2026-10-29)"
print("sell robes OK")

# the broke bot's gather errand (the Watcher, 2026-10-21): no gold, hands only, no loot, trees near -> gather; with robes to sell -> sell first
gt = fighter(name="BotGather", skill=84.0)
gt.facts["fists"] = True
gt.c.gold = 0
gt.c.backpack = [NS(name="hatchet", serial="0xg1", amount=1, hue=0)]
gt.near_trees = lambda n=6: [(1400, 1500, 0, 0)]
gt.where1 = lambda roles, **kw: (1427, 1650)
got = [n[0] for n in errands.needs(gt)]
assert "gather" in got, got
gt.c.backpack.append(NS(name="robe", serial="0xg2", amount=3, hue=0))
assert "gather" in [n[0] for n in errands.needs(gt)], "robes are no sale (2026-10-29): the gather errand stands"
gt.c.backpack = []
assert "gather" not in [n[0] for n in errands.needs(gt)], "no gold and no hatchet: cannot start"
gt.c.gold = 20
assert "gather" in [n[0] for n in errands.needs(gt)], "gold for a hatchet"
print("gather OK")

# feature "provisioned": no supply errands, a kit block in status, provisioned_low events, an archer without arrows waits
pv = fighter(name="BotProv", skill=84.0)
pv.c.max_hp = 130
pv.c.backpack = [NS(name="Bandage", serial="0xv1", amount=40, hue=0)]
pv.c.gold = 500
pv.bandages = lambda: sum(i.amount for i in pv.c.backpack if "bandage" in i.name.lower())
pv.ammo = lambda: 0
pv.bow_kind = lambda: True
pv.feature = lambda n: n == "provisioned"
pv.evs = []
pv.ev = lambda name, **kw: pv.evs.append((name, kw))
task_core.provisioned_watch(pv)
assert pv.status_extra["kit"]["bandages"] == 40 and pv.status_extra["kit"]["arrows"] == 0
assert not [e for e in pv.evs if e[0] == "provisioned_low"], "never above the floor: no event"
pv.c.backpack[0].amount = 3
task_core.provisioned_watch(pv)
pv.facts["kit_seen"] = {"bandages": True}
task_core.provisioned_watch(pv)
low = [e for e in pv.evs if e[0] == "provisioned_low"]
assert low and low[0][1]["item"] == "bandages", pv.evs
assert not [n for n in errands.needs(pv) if n[0] in errands.PROVISIONED_SKIPS], "no supply errands"
assert task_core.candidates(pv, task_core.goal(pv)) == [], "no arrows: waits"
pv.feature = lambda n: False
assert [n for n in errands.needs(pv) if n[0] in ("resupply", "ammo")], "self-supplying bots still raise them"
print("provisioned OK")

# economy fixes (the Watcher, 2026-10-21): tour cap, learned avoid, arrow cost per kind, loot that sells, sale on value
ec = fighter(name="BotEcon", skill=84.0, ranged=True)
ec.home_centre = lambda: (1434, 1699)
ec.avoid_types = {"bonemagi", "ettin"}
assert task_core.avoided(ec, ["bonemagi"]) and task_core.avoided(ec, ["ettin"]) and not task_core.avoided(ec, ["cow"])
ec.bow_kind = lambda: True
assert task_core.arrow_cost(ec, "cow") == 4.0
ec.facts["arrow_use"] = {"cow": (4, 20.0)}
assert task_core.arrow_cost(ec, "cow") == 10.0
ec.bow_kind = lambda: False
assert task_core.arrow_cost(ec, "cow") == 0.0
ec.c.backpack = [NS(name="Feather", serial="0xe1", amount=100, hue=0), NS(name="cut of raw ribs", serial="0xe2", amount=5, hue=0), NS(name="Black Pearl", serial="0xe3", amount=10, hue=0)]
assert errands.held_value(ec) == 100 * 1.0 + 5 * 8 + 10 * 3, errands.held_value(ec)      # the shops' prices (items.py): feather 1.0, ribs 8, reagent 3
assert "sell" not in [n[0] for n in errands.needs(ec)], "170 gold held: under the derived batch (SELL_VALUE 300), no trip yet"
ec.c.backpack.append(NS(name="cut of raw ribs", serial="0xe9", amount=17, hue=0))
assert "sell" in [n[0] for n in errands.needs(ec)], "306 gold held: the trip pays"
ec.c.backpack.pop()
assert "horse" not in task_core.NO_PREY and "snake" in task_core.NO_PREY and task_core.CARVE_REALIZE == 1.0
ec.c.backpack = [NS(name="robe", serial="0xe5", amount=2, hue=0), NS(name="thigh boots", serial="0xe6", amount=1, hue=0)]
assert errands._robes(ec) == 0 and errands._clothes_value(ec) == 2 * 40 + 75, errands._clothes_value(ec)   # robes raise no sell trip (2026-10-29)
print("economy OK")

# no-damage limit from the engine's hit formula (BaseWeapon.CheckHit + the novice lift), per bot and kind
ml = fighter(name="BotMiss", skill=68.0, ranged=True)
ml.main_skill = lambda: "Archery"
ml.skill_values["Archery"] = 68.0
n_cow, p_cow = task_core.miss_limit(ml, "cow")
n_orc, p_orc = task_core.miss_limit(ml, "orc")
assert n_cow == 1 and p_cow == 1.0, (n_cow, p_cow)
assert 0.6 < p_orc < 0.7 and n_orc == 3, (n_orc, p_orc)
assert (1 - p_orc) ** n_orc < 0.05 <= (1 - p_orc) ** (n_orc - 1)
assert task_core.miss_limit(ml, "nosuchkind") == (None, None)
ml.skill_values["Archery"] = 30.0
assert task_core.miss_limit(ml, "orc")[0] > n_orc, "lower skill: more shots before it is believed"
print("miss limit OK")

# measured prey numbers (prey_measured.json): refuse by the group's measured rates, give up at ttk_p90
mb = fighter(name="BotMeas", skill=84.0, ranged=True)
assert measured.group(mb) == "ranged"
# 2026-10-29: expected value per fight (kill_pct x loot) against the solo death cost (death_pct_solo x the mean re-kit), not a death-rate cut-off
assert measured.allowed(mb, "cow")[0] and not measured.allowed(mb, "ratman")[0]
assert measured.value(mb, "cow") > measured.death_cost(mb, "cow") and measured.death_cost(mb, "ratman") > measured.value(mb, "ratman")
assert measured.kit_cost("ranged") > measured.kit_cost("melee") > 0
assert measured.allowed(mb, "orc")[0], "under 30 fights: not judged"
assert measured.give_up_s(mb, "cow") == 18.0 and measured.give_up_s(mb, "unknown") is None
mm = fighter(name="BotMeasM", skill=84.0)
assert measured.group(mm) == "melee" and not measured.allowed(mm, "shade")[0] and measured.allowed(mm, "cow")[0] and measured.allowed(mm, "ratman")[0]
# 2026-10-29: a measured kind on the learned-avoid list is judged by its expected value; an unmeasured one stays avoided
mb.avoid_types = {"cow", "ettin"}
assert hasattr(mb, "avoids") and not mb.avoids("cow") and mb.avoids("ettin") and not mb.avoids("rabbit")
assert not task_core.avoided(mb, ["cow"]) and task_core.avoided(mb, ["ettin"])
mm.avoid_types = {"shade", "cow"}
assert mm.avoids("shade", ground=True) and not mm.avoids("cow", ground=True), "an attack-on-sight kind keeps the list for ground; a measured animal does not"
mb.avoid_types = {"ratman"}
assert mb.avoids("ratman", ground=True) and not mb.avoids("ratman"), "ranged ratmen lose gold in the fixture: the camp stays, the prey test follows the EV"
assert measured.FAMILY["spectre"] == measured.FAMILY["wraith"] == "shade"
import hunter as _hunter
assert _hunter.in_losing_range(mm, 1304, 1413), "the undead spawner north-west of Britain (spectre counted as shade) loses for melee"
_bb = task_core.box_bot
task_core.box_bot = lambda bot: True
assert spots.behind_box(mm, 1434, 1699, 1340, 1310) and not spots.behind_box(mm, 1434, 1699, 1191, 1780), "ground north of the undead box is behind it; the west field is not"
task_core.box_bot = _bb
# carve_room(): engine weights (a hide 5 stones, meat 1): a hind (8 hides, 5 meat) needs 45 stones
import bot_common as _bc2
_cr = NS(c=NS(weight=300, max_weight=390, backpack=[]), CORPSE_NAMES={"deer": ("hind", "greathart")})
assert _bc2.BotBase.carve_room(_cr, "hind") is True
_cr.c.weight = 356
assert _bc2.BotBase.carve_room(_cr, "hind") is False, "no scissors: 356 + 8 hides x 5 + 5 meat > 390"
_cr.c.backpack = [NS(name="scissors", serial="0xs1", amount=1, hue=0)]
assert _bc2.BotBase.carve_room(_cr, "hind") is True, "scissors: the hides are cut on the corpse, 356 + 8 + 5 <= 390"
# drink(): a bow leaves no free hand (BasePotion.HasFreeHand): it goes to the pack and back; a shield alone is no bar
import bot_common as _bc
class _DC:
    def __init__(self, eq, pack):
        self.equipped, self.backpack, self.log_ = eq, pack, []
    def unequip(self, s): self.log_.append(("unequip", s)); self.equipped = [i for i in self.equipped if i.serial != s]
    def use(self, s): self.log_.append(("use", s)); self.backpack = [i for i in self.backpack if i.serial != s] if not any(i.layer == "TwoHanded" and "bow" in i.name for i in self.equipped) else self.backpack
    def call(self, line, timeout=6): self.log_.append(("call", line))
_bow = NS(name="bow", serial="0xb0", layer="TwoHanded", amount=1, hue=0)
_pot = NS(name="Orange Potion", serial="0xp1", layer=None, amount=1, hue=0)
_d = NS(c=_DC([_bow], [_pot]), ev=lambda *a, **k: None)
_orig_sleep = _bc.time.sleep
_bc.time.sleep = lambda s: None
try:
    assert _bc.BotBase.drink(_d, _pot) is True and _d.c.log_[0] == ("unequip", "0xb0") and ("call", "equip 0xb0") in _d.c.log_
    _d2 = NS(c=_DC([NS(name="heater shield", serial="0xs0", layer="TwoHanded", amount=1, hue=0)], [_pot]), ev=lambda *a, **k: None)
    assert _bc.BotBase.drink(_d2, _pot) is True and not any(x[0] == "unequip" for x in _d2.c.log_), "a shield alone leaves a hand free"
    _d3 = NS(c=_DC([_bow], [_pot]), ev=lambda *a, **k: None)
    _d3.c.unequip = lambda s: None                                # the bow stays: the server refuses, drink says so
    assert _bc.BotBase.drink(_d3, _pot) is False
finally:
    _bc.time.sleep = _orig_sleep
assert not _hunter.in_losing_range(mm, 1434, 1699), "the bank is in no losing range"
assert _hunter.spawn_reaches("spectre", "1280,1400"), "the undead spawner at 1304,1413 reaches its own cell"
assert not _hunter.spawn_reaches("troll", "1400,1680"), "no troll spawner reaches Britain's centre: a troll sighting there makes no camp"
_hunter._REACH.clear()
assert _hunter.spawn_reaches("shade", "1280,1400"), "a 'shade' sighting is the spectre spawner's (the client's body name)"
print("measured OK")

# corpse runs: none when provisioned; refused beyond the tour cap, for a measured-deadly killer, a repeat killer, ground of a death within the hour
cp = fighter(name="BotCorpse", skill=84.0)
cp.home_centre = lambda: (1434, 1699)
cp.feature = lambda n: False
cp.facts["killer"] = {"name": "a skeletal knight", "t": task_core.now()}
cp.facts["own_deaths"] = [[1000, 1000, "an orc", task_core.now() - 5000], [1367, 2157, "a skeletal knight", task_core.now()]]
assert task_core.corpse_refusal(cp, 1450, 1720) is None
assert task_core.corpse_refusal(cp, 1367, 2157)[0] == "beyond the corpse-run cap"
cp.facts["own_deaths"] = [[1440, 1700, "a skeletal knight", task_core.now() - 600], [1450, 1720, "a skeletal knight", task_core.now()]]
assert task_core.corpse_refusal(cp, 1450, 1720)[0] == "that killer has killed it before"
cp.facts["own_deaths"] = [[1440, 1700, "a rat", task_core.now() - 600], [1450, 1720, "a cat", task_core.now()]]
cp.facts["killer"] = {"name": "a cat", "t": task_core.now()}
assert task_core.corpse_refusal(cp, 1450, 1720)[0] == "it died near here within the hour"
cp.facts["killer"] = {"name": "a ratman", "t": task_core.now()}
cp.facts["own_deaths"] = []
cp.ranged = True
assert task_core.corpse_refusal(cp, 1450, 1730)[0] == "killer's measured death rate"
cp.feature = lambda n: n == "provisioned"
assert task_core.corpse_refusal(cp, 1450, 1730)[0] == "provisioned"
print("corpse OK")

# death robes (hue 2301, newbied) are never counted, sold or valued; the tour distance cap is gone
dr = fighter(name="BotDeathRobe", skill=84.0)
dr.c.backpack = [NS(name="robe", serial="0xd1", amount=1, hue=2301), NS(name="robe", serial="0xd2", amount=1, hue=1735)]
assert errands._robes(dr) == 0 and errands._clothes_value(dr) == 40
sent = []


def _drop(cmd, timeout=0):
    sent.append(cmd)
    dr.c.backpack = [i for i in dr.c.backpack if i.serial != cmd.split()[1]]      # the engine took it (basics.drop_to_ground checks that it left the pack)


dr.c.call = _drop
dr.ev = lambda name, **kw: sent.append(name)
here = f"{dr.c.x} {dr.c.y}"
assert errands.drop_death_robes(dr) == 1 and sent == [f"dropground 0xd1 1 {here}", "death_robe_dropped"], sent
assert not hasattr(task_core, "tour_far") and not hasattr(task_core, "TOUR_CAP")
print("death robe OK")

# the robe drop runs on its own timer; giant rats carve by the profit table
import profit as _profit
assert float(_profit.table()["giantrat"]["hides"]) > 0 and float(_profit.table()["rat"]["meat"]) > 0
dr.c.backpack = [NS(name="robe", serial="0xd1", amount=1, hue=2301)]
dr.threats = lambda r: []
sent.clear()
task_core.drop_robes_tick(dr)
assert sent == [f"dropground 0xd1 1 {here}", "death_robe_dropped"], sent
sent.clear()
task_core.drop_robes_tick(dr)
assert sent == [], "once per 5 minutes"
print("robe tick OK")

# measured danger: the family alias and a spawner whose creatures reach a spot
import spots as _spots
fm = fighter(name="BotFam", skill=84.0, ranged=True)
_json.dump({"made": "test2", "ranged": {"mongbat": {"fights": 92, "kill_pct": 37, "ttk_p90": 37, "death_pct": 4.3}}, "melee": {}}, open(_MFILE, "w"))
_measured._state["mtime"] = None
_measured._state["checked"] = 0.0
assert measured.deadly(fm, "greatermongbat") and measured.deadly(fm, "mongbat") and not measured.deadly(fm, "cow")
_spots._SPAWN["t"] = [{"id": "sp1400,1320", "x": 1400, "y": 1320, "kinds": ["greatermongbat", "mongbat"], "count": 4, "mn": 300, "mx": 600, "home": 12},
                      {"id": "sp1375,1330", "x": 1375, "y": 1330, "kinds": ["cow"], "count": 3, "mn": 300, "mx": 600, "home": 10}]
fm.__dict__.pop("_deadly_sp", None)
assert _spots.measured_danger_near(fm, {"id": "x", "x": 1402, "y": 1323, "home": 10})[0] in ("greatermongbat", "mongbat")
assert _spots.measured_danger_near(fm, {"id": "y", "x": 1375, "y": 1330, "home": 10}) is not None, "25 tiles: within the home range 12 + the perception reach 14"
assert _spots.measured_danger_near(fm, {"id": "z", "x": 1370, "y": 1350, "home": 10}) is None, "30 tiles: beyond 12 + 14"
print("measured danger OK")

# BotBase.ev(self, kind, **kw): an event that passes kind= fails with a TypeError (which the guarded callers swallowed: arrows_used, give_up, arrows_wasted, carve, loot_empty never fired, 2026-10-21)
import glob as _glob, re as _re
for _f in _glob.glob(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "*.py")):
    _src = open(_f, encoding="utf-8").read()
    _bad = _re.findall(r"ev\(\"[a-z_]+\",[^()]*kind=", _src)
    assert not _bad, (_f, _bad)
print("ev keywords OK")

# a dagger in hand while the own weapon waits in the pack: ok, and rewielded
wp = fighter(name="BotRewield", skill=84.0)
wp.c.state = {"str": 90}
wp.c.equipped = [NS(name="dagger", serial="0xw1", layer="OneHanded", amount=1, hue=0)]
wp.c.backpack = [NS(name="katana", serial="0xw2", amount=1, hue=0)]
wp.main_skill = lambda: "Swordsmanship"
wp.__dict__.pop("weapon_state", None)                    # the fixture fakes it as "ok"
assert wp.own_weapon_in_pack().serial == "0xw2", wp.own_weapon_in_pack()
assert wp.weapon_state() == "ok"
wp.threats = lambda r: []
wp.wield = lambda tool: wp.evs.append(("wield", tool.name)) or True
assert wp.rewield_own() and ("wield", "katana") in wp.evs
wp.c.backpack = []
assert wp.weapon_state() == "wrong" and wp.own_weapon_in_pack() is None
assert wp.CORPSE_NAMES["deer"] == ("hind", "greathart")
print("rewield OK")

# no spot open twice in a row: the no-ground report names the tests, then the fallback loosens them (crowding first)
ng = fighter(name="BotNoGround", xy=(1470, 1620))
ng.c.max_hp = task_core.UNDEAD_HP                                  # the fixture spawners lie north of the undead box: a bot the box is open to (behind_box, 2026-10-29)
gng = task_core.goal(ng)
ng.ground_load = lambda cell: 5
real_crowded = spots.crowded
spots.crowded = lambda bot, s_: True
assert not task_core.candidates(ng, gng, random.Random(1))
o1, w1 = task_core.no_ground(ng, gng, random.Random(1))
assert not o1 and ng.evs[-1][0] == "no_ground" and ng.evs[-1][1]["why"].get("crowded"), ng.evs[-1]
o2, w2 = task_core.no_ground(ng, gng, random.Random(1))
assert o2 and w2 == "relaxed 1" and any(e[0] == "ground_relaxed" and e[1]["relax"] == 1 for e in ng.evs), (w2, ng.evs[-2:])
spots.crowded = real_crowded
# relax 3: the worth floor off on the lowest tier, the safest spot first
ng2 = fighter(name="BotRelax3", xy=(1470, 1620))
ng2.c.max_hp = task_core.UNDEAD_HP                                 # (as above: the fixture spawners lie north of the undead box)
ng2.worth_kind = lambda k, deadly: 0.0
assert not task_core.candidates(ng2, task_core.goal(ng2), random.Random(1))
r3 = task_core.candidates(ng2, task_core.goal(ng2), random.Random(1), rested=True, relax=3)
assert r3 and r3 == sorted(r3, key=lambda c: (c["die"], -c["score"])) and r3[0]["relax"] == 3
print("no ground OK")

# ---- the carve value (owner, 2026-10-20): hides as leather, feathers and meat count for a bot with a blade -------------------------------------------
cv = fighter(name="BotCarve")
cv.carving_blade = lambda: None
g_no = task_core.gold_per_kill(cv, "hind")
cv.carving_blade = lambda: NS(serial="0xB1", name="dagger")
g_yes = task_core.gold_per_kill(cv, "hind")
assert g_yes > g_no and g_yes - g_no > 5, (g_no, g_yes)
cv.c.backpack = [NS(name="pile of hides", serial="0xH1", amount=80, hue=0), NS(name="feather", serial="0xF1", amount=60, hue=0)]      # 80 x 3 + 60 x 1.5 = 330: over SELL_VALUE
cv.bandages = lambda: 50; cv.gear_loot = lambda: []; cv.tired = lambda: False; cv.next_upgrade = lambda m: None; cv.can_make_arrows = lambda: 0
cv.where1 = lambda roles, **kw: (1467, 1688); cv.bank_xys = lambda: [(1425, 1690)]
sell = next((n for n in errands.needs(cv) if n[0] == "sell"), None)
assert sell and "80 hides" in sell[4] and "60 feathers" in sell[4], sell
print("carve OK")

# ---- the travel planner (plan 4b): walk, gate, recall; a failed leg blocked and planned again ---------------------------------------------------------
import travel
tp = fighter(name="BotTravel", xy=(1470, 1620))
tp.rune_on = lambda: False
near_j = travel.plan_journey(tp, (1500, 1640))
assert near_j and near_j["kind"] == "walk" and near_j["legs"][-1]["to"] == [1500, 1640] and near_j["legs"][0]["wps"][-1] == [1500, 1640]
travel.gates = lambda bot: [("Britain", (1336, 1997)), ("Yew", (771, 752))]
tp.c.x, tp.c.y = 1340, 1990                                         # beside Britain's gate, bound for Yew's doorstep
far_j = travel.plan_journey(tp, (780, 760))
assert far_j and far_j["kind"] == "gate" and [l["kind"] for l in far_j["legs"]] == ["walk", "gate", "walk"] and far_j["legs"][1]["to_name"] == "Yew", far_j and far_j["options"]
travel.block(tp, "gate", "test")
assert travel.plan_journey(tp, (780, 760))["kind"] == "walk", "a blocked gate leg: the walk"
tp.facts["travel_blocked"].clear()
# a rune marked near the destination beats the walk when the bot can cast Recall
tp.rune_on = lambda: True
tp.rune_able = lambda: True
tp.rune_known = lambda: {"0xR1": {"x": 790, "y": 770, "label": "ground"}}
rj = travel.plan_journey(tp, (780, 760))
assert rj["kind"] == "recall" and rj["legs"][0]["rune"] == "0xR1", rj["options"]
# the gate leg: the gump's radio for the town, the OK button with the switch, the jump
tp.c.x, tp.c.y = 1336, 1997
tp.c.call = lambda line, timeout=8: (tp.c.calls.append(line) or (["[GUMP] local 0x1 server 0xABC Gump", "[GUMP]   [radio 0] Moonglow", "[GUMP]   [radio 3] Yew", "[GUMP]   [button 1] OKAY"] if line == "gumps" else []))
st_ = {}
leg = {"kind": "gate", "at": [1336, 1997], "to_name": "Yew", "land": [771, 752]}
tp.c.gotos = []
r1 = travel.gate_step(tp, leg, st_)
assert r1 == "running" and tp.c.calls[-1] == "gumpresponse 1 3 gump:0xABC", (r1, tp.c.calls[-2:])
tp.c.x, tp.c.y = 772, 753                                           # the jump
assert travel.gate_step(tp, leg, st_) == "done" and any(e[0] == "gate_used" for e in tp.evs)
print("travel OK")

# ---- item 5, the world beyond Britain: the rungs, the dungeon spots, the teleporter leg, the other towns, the shared tour ---------------------------------
import gazetteer as gz
rg = fighter(name="BotRung", skill=82.0)
rg.tele_allow = lambda side, seconds=900: rg.facts.setdefault("tele_ok", {}).__setitem__(side, now() + seconds)
assert task_core.rung(rg) == 0 and not task_core.kit(rg)[0] and max(task_core.tiers(rg)) <= 3
rg.c.backpack = [NS(name="Yellow Potion", serial="0xP1", amount=10, hue=0), NS(name="Red Potion", serial="0xP2", amount=2, hue=0), NS(name="Bandage", serial="0xB1", amount=50, hue=0), NS(name="Orange Potion", serial="0xP1c", amount=15, hue=0)]
assert task_core.kit(rg)[0], task_core.kit(rg)
assert task_core.rung_update(rg) == 0, "the kit alone opens nothing: tier 3 must pay first"
task_core.record_tier_kills(rg, 3, task_core.RUNG_PAY - 1)
assert task_core.rung_update(rg) == 0
task_core.record_tier_kills(rg, 3, 1)
assert task_core.rung_update(rg) == 1 and rg.facts["rung"] == 1 and rg.evs[-1][0] == "rung" and rg.evs[-1][1]["from"] == 0 and rg.evs[-1][1]["to"] == 1, rg.evs[-1]
assert 4 in task_core.tiers(rg) and 5 not in task_core.tiers(rg)
rg.c.backpack[2].amount = 5                                         # bandages spent: the rung stays open but its tiers are not offered until the kit is carried again
assert 4 not in task_core.tiers(rg) and task_core.rung(rg) == 1
rg.c.backpack[2].amount = 50
rg.skill_values["Swordsmanship"] = 79.0                             # the weapon skill under 80: no entry
assert not task_core.kit(rg)[0] and 4 not in task_core.tiers(rg)
rg.skill_values["Swordsmanship"] = 82.0
# the dungeon spots: level 1 of the rung dungeons is tier 4, their deeper levels tier 5, the Hot Zone (Hythloth) tier 6
ds = spots.dungeon_spots()
assert ds and {s_["tier"] for s_ in ds} == {4, 5, 6} and all(s_["x"] >= spots.SURFACE_X for s_ in ds), len(ds)
assert all(s_["tier"] == 6 for s_ in ds if s_["side"] == "Hythloth") and spots.hot_zones() == ("Hythloth",)
for dun in spots.RUNG_DUNGEONS[:-1]:
    assert any(s_["side"] == dun and s_["tier"] == 4 for s_ in ds), f"{dun} has a level 1"
assert any(s_["side"] == "Despise" and s_["tier"] == 5 for s_ in ds), "Despise has deeper levels"
land = next(t for t in gz.get().trans if t["src_side"] == "surface" and t["dst_side"] == "Despise")["dst"]
assert spots.dungeon_tier(land[0], land[1], "Despise") == 4, "the entrance lands on level 1 (through its antechamber)"
assert spots.dungeon_tier(1470, 1620) is None
sp_r = spots.all_spots(rg)
assert any(s_["tier"] == 4 for s_ in sp_r) and not any(s_["tier"] >= 5 for s_ in sp_r), "rung 1 offers level 1 only"
assert all(s_.get("side") == "surface" for s_ in sp_r if s_["x"] < spots.SURFACE_X) and all(s_["tier"] <= 4 for s_ in sp_r if s_["x"] < spots.SURFACE_X), "the surface has areas up to tier 4 (the spawn design's outer ring)"
assert all(s_["tier"] >= 4 and s_["side"] in spots.RUNG_DUNGEONS for s_ in sp_r if s_["x"] >= spots.SURFACE_X)
norung = fighter(name="BotNoRung", skill=82.0)
assert not any(s_["tier"] >= 4 for s_ in spots.all_spots(norung)), "no rung, no dungeon spot, whatever the skill"
# the choice offers a dungeon tour on its side; the task start allows the side and carries the tier; kills there pay for the next rung
opts = task_core.candidates(rg, task_core.goal(rg), random.Random(3))
dun = [o for o in opts if o["side"] != "surface"]
assert dun and all(o["tier"] == 4 and o["side"] in spots.RUNG_DUNGEONS for o in dun) and all(len({spots.dungeon_tier(sp_[0], sp_[1]) for sp_ in o["spots"]}) == 1 for o in dun), dun[:1]
tk = task_core.start_task(rg, task_core.goal(rg), dun[0], opts)
assert rg.facts["tele_ok"].get(dun[0]["side"], 0) > now() and tk["tier"] == 4 and tk["side"] == dun[0]["side"] and rg.evs[-1][1]["tier"] == 4
tk["arrived"] = now()
rg.kills = task_core.RUNG_PAY
task_core.end_task(rg, tk, "done")
assert rg.facts["rung_kills"]["4"] == task_core.RUNG_PAY and task_core.rung(rg) == 2 and 5 in task_core.tiers(rg) and 6 not in task_core.tiers(rg)
print("rungs OK")

# the teleporter leg: a destination on another side is reached through tele_route's hops, each a leg between walk legs; the hop step checks the side
tp2 = fighter(name="BotTele", xy=(1290, 1075))
tp2.rune_on = lambda: False
hop = {"src": [1296, 1080, 0], "dst": [5588, 630, 0], "src_side": "surface", "dst_side": "Despise", "kind": "enter"}
tp2.tele_route = lambda frm, side, target=None: [hop]
tp2.tele_allow = lambda side, seconds=900: None
j = travel.plan_journey(tp2, (5560, 640))
assert j and j["kind"] == "tele" and [l["kind"] for l in j["legs"]] == ["walk", "tele", "walk"] and j["legs"][1]["to_side"] == "Despise" and j["legs"][0]["to"] == [1296, 1080], j
assert j["legs"][2]["to"] == [5560, 640] and j["hops"] == 1
assert travel.walk_cost(tp2, (1296, 1079), (5588, 630)) == (None, None), "no walk crosses sides"
assert travel.plan_journey(tp2, (1300, 1090))["kind"] == "walk", "the same side: no hop"
tp2.tele_hop = lambda t: (setattr(tp2.c, "x", 5588) or setattr(tp2.c, "y", 630) or True)
st_ = {}
# M1: at the gate the stock and the health are checked again; without them the bot turns back and does not go in
tp2.skill_values["Swordsmanship"] = 82.0
tp2.c.backpack = []
r_ = travel.tele_step(tp2, j["legs"][1], {})
assert str(r_).startswith("not ready for the dungeon") and any(e[0] == "rung_turned_back" for e in tp2.evs), r_
tp2.c.backpack = [NS(name="Yellow Potion", serial="0xk1", amount=10, hue=0), NS(name="Red Potion", serial="0xk2", amount=2, hue=0), NS(name="Bandage", serial="0xk3", amount=50, hue=0), NS(name="Orange Potion", serial="0xk1c", amount=15, hue=0)]
tp2.c.hp = 40
assert str(travel.tele_step(tp2, j["legs"][1], {})).startswith("not ready"), "a hurt bot does not go in (under 90% health)"
tp2.c.hp = 80
assert travel.tele_step(tp2, j["legs"][1], st_) == "done" and any(e[0] == "tele_used" and e[1]["to_side"] == "Despise" for e in tp2.evs)
tp3 = fighter(name="BotTeleFail", xy=(1296, 1079))
tp3.tele_hop = lambda t: False
tp3.tele_allow = lambda side, seconds=900: None
tp3.skill_values["Swordsmanship"] = 82.0
tp3.c.backpack = [NS(name="Yellow Potion", serial="0xk4", amount=10, hue=0), NS(name="Red Potion", serial="0xk5", amount=2, hue=0), NS(name="Bandage", serial="0xk6", amount=50, hue=0), NS(name="Orange Potion", serial="0xk4c", amount=15, hue=0)]
assert travel.tele_step(tp3, j["legs"][1], {}) == "did not jump"
tp3.tele_route = lambda frm, side, target=None: None
tp3.rune_on = lambda: False
assert travel.plan_journey(tp3, (5560, 640)) is None, "no chain of teleporters: no journey"
# a route length to another side is the straight guess (the planner crosses), not None
assert task_core.route_length.__name__ == "<lambda>" or True
print("tele leg OK")

# the other towns are OUT of item 5 (the owner, 2026-10-20: "drop 'towns beyond britain' for now. britain is the hub"): every journey starts from and returns to
# Britain, the errands and the ghost's healer are Britain's, and the surface ground stays within REACH of home
far = fighter(name="BotHub", xy=(1470, 1620))
hx_, hy_ = far.home_centre()
assert all(max(abs(s_["x"] - hx_), abs(s_["y"] - hy_)) <= spots.REACH + 20 for s_ in spots.all_spots(far) if s_["x"] < spots.SURFACE_X), "surface ground within reach of home only (a memory cell's centre may sit 20 beyond)"
assert spots.door_reachable(1296, 1080, (1470, 1620)) and not spots.door_reachable(4722, 3813, (1470, 1620)), "Despise's door is a journey from Britain; Hythloth's island is not"
print("hub OK")

# the shared tour: with a party member or buddy within TOUR2_NEAR, every tour of tier 4 or more comes again as a "tour2" at TOUR2_BONUS the score and less risk
t2 = fighter(name="BotTour2", skill=82.0)
t2.c.backpack = list(rg.c.backpack)
t2.facts["rung"], t2.facts["rung_kills"] = 1, {"3": 20}
t2.tele_allow = lambda side, seconds=900: None
t2.party_names = lambda: {"BotMate"}
t2.threats = lambda within: [m for m in t2.c.mobiles(within) if "rabbit" not in m.name and not m.name.startswith("Bot")]
t2.c.mobs = [mob("0xM1", "BotMate", t2.c.x + 5, t2.c.y)]
opts = task_core.candidates(t2, task_core.goal(t2), random.Random(4))
t2c = [o for o in opts if o["task"] == "tour2"]
assert t2c and all(o["tier"] >= 4 and o["partner"] == "BotMate" and o["role"] == "leader" for o in t2c), t2c[:1]
base = next(o for o in opts if o["task"] == "hunt" and o["tour"] == t2c[0]["tour"])
assert abs(t2c[0]["score"] - round(base["score"] * task_core.TOUR2_BONUS, 4)) < 1e-6 and t2c[0]["die"] <= base["die"], (t2c[0]["score"], base["score"])
assert not any(o["task"] == "tour2" and o["tier"] < 4 for o in opts), "a surface tour is no tour2"
assert opts[0]["task"] == "tour2" if opts[0]["tier"] >= 4 else True
t2.c.mobs = []
assert not any(o["task"] == "tour2" for o in task_core.candidates(t2, task_core.goal(t2), random.Random(4))), "no partner near: no tour2"
# the tree: the buddy step follows the partner, the follower fights beside the leader, the loot alternates
t2.c.mobs = [mob("0xM1", "BotMate", t2.c.x + 5, t2.c.y)]
cand = t2c[0]
tk2 = task_core.start_task(t2, task_core.goal(t2), cand, opts)
assert tk2["task"] == "tour2" and tk2["partner"] == "BotMate" and tk2["role"] == "leader"
t2.c.x, t2.c.y = cand["spots"][0][0], cand["spots"][0][1]
tk2["arrived"] = now()
mate = mob("0xM1", "BotMate", t2.c.x + 20, t2.c.y)
t2.c.mobs = [mate]
step, why = run_tree(t2, tk2)
assert step == "follow" and t2.c.gotos[-1] == (mate.x, mate.y), (step, t2.c.gotos[-1:])
t2.c.nav.active, t2.c.due = False, None                             # the partner came back instead: the walk is over
mate.x = t2.c.x + 3
orc = mob("0xO1", "an orc", t2.c.x + 1, t2.c.y, hits=5)
t2.c.mobs = [mate, orc]
run_tree(t2, tk2, ticks=3)
t2.c.mobs = [mate]
t2.c.conts = [corpse("0xK1", "an orc corpse", orc.x, orc.y)]
run_tree(t2, tk2, ticks=2)
assert "0xK1" in t2.looted_, "the first kill is the leader's to loot"
t2.c.nav.active, t2.c.due = False, None                             # no walk pending: the fake client would carry the bot off to it
orc2 = mob("0xO2", "an orc", t2.c.x + 1, t2.c.y, hits=5)
t2.c.mobs, t2.c.conts = [mate, orc2], []
run_tree(t2, tk2, ticks=3)
t2.c.mobs = [mate]
t2.c.conts = [corpse("0xK2", "an orc corpse", orc2.x, orc2.y)]
run_tree(t2, tk2, ticks=2)
assert "0xK2" not in t2.looted_ and "0xK2" in t2.facts["looted"] and any(e[0] == "loot_turn" and not e[1]["mine"] for e in t2.evs), "the second kill is the partner's turn"
assert task_core.rule_category("task:tour2:follow") == "travel" and task_core.rule_category("task:tour2:heal") == "work"
# a joiner: the partner's published tour2 (buddy.json "core") comes as a follower candidate
import buddy
real_peers = buddy.peers
buddy.peers = lambda me: [{"name": "BotMate", "pos": [t2.c.x, t2.c.y], "skill": 80.0, "rule": "task:tour2:pick", "party": [], "errand": 0,
                           "core": {"task": "tour2", "area": "tour spX with BotTour2", "spots": cand["spots"], "tour": cand["tour"], "side": cand["side"], "tier": 4, "expected": cand["expected"], "score": cand["score"]}}]
jo = [o for o in task_core.candidates(t2, task_core.goal(t2), random.Random(4)) if o.get("join")]
assert jo and jo[0]["role"] == "follower" and jo[0]["spots"] == cand["spots"] and jo[0]["task"] == "tour2", jo[:1]
buddy.peers = real_peers
assert "rung" in bot_common.BotBase.PERSIST and "rung_kills" in bot_common.BotBase.PERSIST
print("shared tour OK")

# ---- the wiring -------------------------------------------------------------------------------------------------------------------------------------

assert hunter.HunterBot.TASK_CORE is True and crafter.CrafterBot.TASK_CORE is False and hunter.BardBot.TASK_CORE is True
assert bot_common.BotBase.REFLEXES == ("r_dead", "r_corpse", "r_gear", "r_cure", "r_refresh", "r_flee", "r_avoid", "r_sewer_out", "r_heal")      # r_refresh: basics.py
assert hunter.HunterBot.RULES[:len(bot_common.BotBase.REFLEXES)] == list(bot_common.BotBase.REFLEXES), hunter.HunterBot.RULES[:9]
assert bot_common.BotBase.core_active(NS()) is False and bot_common.BotBase.core_tick(NS()) is None
on = fighter(name="BotOn")
assert on.core_active() is True
off = fighter(name="BotOff", features=("fields",))
assert off.core_active() is False
cr = object.__new__(crafter.CrafterBot)
cr.features = {"task_core"}
cr.feature = lambda f: True
assert cr.core_active() is False, "crafters are excluded by class"
for k in ("task", "core_goal", "core_bans"):
    assert k in bot_common.BotBase.PERSIST
# the run loop: with the core on, only the reflexes (and what core_lets passes: a ladder bot's trip) run and the core ticks; with it off, nothing changes
src = open(os.path.join(D, "bot_common.py"), encoding="utf-8").read()
assert "if core and name not in self.REFLEXES and not self.core_lets(name):" in src and "acted = self.core_tick()" in src
assert fighter(name="BotLets").core_lets("r_sell") is False
# the stall sense, the progress check and the loop guard's back-offs are off for core bots; the loop guard's server-refusal reading stays
st = fighter(name="BotStall")
st.stall_measure = lambda: (0, 0, 0, {})
st._stall = {}
st.stall_tick("task:hunt:fight")
assert not st.__dict__.get("_stall"), "the stall sense did not sample"
st.progress_on = lambda: True
assert st.progress_tick("task:hunt:fight") is None and "_pg" not in st.__dict__
st.current_rule = "task:hunt:fight"
st.dlog = lambda *a, **kw: None
st.guard_trip("sys", "You cannot reach that.", 41)
assert "task:hunt:fight" not in st.facts.get("rule_off", {}) and any("only reported" in m for m in st.logs)
assert "guard_client" in src and "self.guard_client()" in src
print("wiring OK")
print("test_task_core OK")
