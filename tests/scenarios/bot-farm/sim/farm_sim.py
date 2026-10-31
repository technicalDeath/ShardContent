"""Play the farm's unchanged brain classes against the simulated world, many simulated hours in minutes, and print the farm's own measures.

    python farm_sim.py [--bots 50] [--hours 10] [--procs 10] [--roster work/botfarm/sim/roster.json] [--seed 1] [--out work/botfarm/sim/run-<stamp>]
                       [--classes hunter,caster,...] [--smoke] [--memory-from work/botfarm/memory] [--quiet]

Every bot gets its own thread under the virtual clock (sim/clock.py) and a FakeClient (sim/fake_client.py) on one World (sim/world.py). The brains write
their usual files (run.log, status.json, decisions.jsonl, notes.jsonl, the shared memory, farm.db, the client log) under <out>/farm, never under
work/botfarm itself, so the farm's scorecard.py reads a run with BOTFARM_DIR=<out>/farm. The scoreboard (rule time shares by group as in
work/botfarm-watch/scorecard.py, kills and deaths per bot-hour, gold and skill gains per bot-hour, exceptions by brain class) is printed and written to
<out>/scoreboard.json and scoreboard.md.

--procs N splits the roster over N processes, each with its own copy of the world (the bots of different parts share the memory files and farm.db, as the
farm's do, but do not see each other); the brains' own work is the cost (about ten real seconds per bot-hour), so fifty bots for ten hours need the cores.
--smoke: one bot per brain class, a short run, exit 1 when any brain class raised in a tick or failed to construct (the release pipeline's check).
"""
from __future__ import annotations

import argparse
import collections
import faulthandler
import glob
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
BOTFARM = os.path.abspath(os.path.join(HERE, ".."))
SCENARIOS = os.path.abspath(os.path.join(BOTFARM, ".."))
ROOT = os.path.abspath(os.path.join(SCENARIOS, "..", "..", ".."))
FARM = os.path.join(ROOT, "work", "botfarm")
for p in (os.path.join(ROOT, "Navrey", "cli"), os.path.join(ROOT, ".claude", "scripts"), os.path.join(SCENARIOS, "new-mage-playtest"), BOTFARM, SCENARIOS):
    if p not in sys.path:
        sys.path.insert(0, p)

from sim.clock import VirtualClock, real_time  # noqa: E402
from sim.fake_client import FakeClient  # noqa: E402
from sim.world import World  # noqa: E402
from sim.world_data import WorldData  # noqa: E402
import sim.world_data as wd  # noqa: E402

_dump_stacks = faulthandler.dump_traceback_later

PROFESSION_CLASS = {8: "hunter", 9: "bard", 10: "hunter", 13: "hunter", 14: "hunter", 15: "hunter", 11: "caster", 12: "caster", 23: "caster",
                    16: "crafter", 17: "crafter", 18: "crafter", 19: "crafter", 20: "tamer", 21: "fisher", 22: "miner"}
CLASS_PROFESSION = {"hunter": 13, "bard": 9, "caster": 11, "crafter": 16, "tamer": 20, "fisher": 21, "miner": 22}
FIGHTERS = {"Archer", "Ranger", "MaceFighter", "Fencer", "Swordsman", "Bard"}
CASTERS = {"PureMage", "Warlock", "Sorcerer"}
CRAFT = {"Blacksmith", "Carpenter", "Tailor", "Tinker"}
GATHER = {"Fisherman", "Prospector"}
WORK_RULES = {"fighter": {"r_fight", "r_hunt", "r_loot", "r_music"}, "caster": {"r_fight", "r_hunt", "r_loot", "r_train"},
              "crafter": {"r_craft", "r_cut", "r_sell", "r_dig", "r_smelt", "r_chop"}, "gatherer": {"r_fish", "r_mine", "r_cut", "r_cook", "r_smelt", "r_sell"},
              "tamer": {"r_tame"}}
TRAVEL, REST = {"r_explore", "r_wander", "r_earn"}, {"r_rest", "r_heal", "r_idle"}
MAIN = {"Archer": "Archery", "Ranger": "Archery", "Bard": "Musicianship", "MaceFighter": "Mace Fighting", "Fencer": "Fencing", "Swordsman": "Swordsmanship",
        "PureMage": "Magery", "Warlock": "Magery", "Sorcerer": "Magery", "Blacksmith": "Blacksmithy", "Carpenter": "Carpentry", "Tailor": "Tailoring",
        "Tinker": "Tinkering", "AnimalTamer": "Animal Taming", "Fisherman": "Fishing", "Prospector": "Mining"}
PROF_NAME = {8: "Archer", 9: "Bard", 10: "Ranger", 11: "PureMage", 12: "Warlock", 13: "MaceFighter", 14: "Fencer", 15: "Swordsman", 16: "Blacksmith", 17: "Carpenter",
             18: "Tailor", 19: "Tinker", 20: "AnimalTamer", 21: "Fisherman", 22: "Prospector", 23: "Sorcerer"}


def group(prof):
    return ("fighter" if prof in FIGHTERS else "caster" if prof in CASTERS else "crafter" if prof in CRAFT else "gatherer" if prof in GATHER
            else "tamer" if prof == "AnimalTamer" else "other")


REFLEXES = ("r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_avoid", "r_sewer_out", "r_heal")
CORE_STEPS = {"travel": "travel", "roam": "travel", "follow": "travel", "camp": "camp", "pick": "work", "pursue": "work", "fight": "work", "loot": "work", "play": "work", "heal": "work",
              "rest": "rest", "wait": "rest"}


def rule_cat(g, rule):
    rule = rule or "-"
    if rule.startswith("task:"):                                  # the decision core's steps (task_core.py): task:<task>:<step>
        return CORE_STEPS.get(rule.split(":")[-1], "other")
    return ("camp" if rule == "r_camp" else "work" if rule in WORK_RULES.get(g, set()) else "travel" if rule in TRAVEL else "rest" if rule in REST
            else "dead" if rule == "r_dead" else "other")


# ---- redirecting the brains' files to the run folder ---------------------------------------------------------------------------------------------------------

class _PathProxy:
    def __init__(self, real, farm_watch):
        self._real, self._watch = real, farm_watch

    def __getattr__(self, k):
        return getattr(self._real, k)

    def join(self, *a):
        if any("botfarm-watch" in str(x) for x in a):
            return self._real.join(self._watch, a[-1])
        return self._real.join(*a)


class _OsProxy:
    def __init__(self, farm_watch):
        self.path = _PathProxy(os.path, farm_watch)

    def __getattr__(self, k):
        return getattr(os, k)


def prepare(out_farm, memory_from=None, with_features=(), without_features=(), names=()):
    """The run folder: the farm's features.json (cohorts) and shops.json, its geo cache, optionally a copy of a memory folder. Done once per run.
    --with-feature / --without-feature put every bot of the run's roster into, or out of, a feature in the run's own copy of features.json."""
    os.makedirs(os.path.join(out_farm, "memory"), exist_ok=True)
    os.makedirs(os.path.join(out_farm, "watch"), exist_ok=True)
    os.makedirs(os.path.join(out_farm, "work", "navrey-sessions"), exist_ok=True)
    for f in ("features.json", "shops.json"):
        src = os.path.join(FARM, f)
        if os.path.exists(src) and not os.path.exists(os.path.join(out_farm, f)):
            shutil.copy(src, os.path.join(out_farm, f))
    if with_features or without_features:
        fp = os.path.join(out_farm, "features.json")
        try:
            table = json.load(open(fp, encoding="utf-8"))
        except (OSError, ValueError):
            table = {}
        for f in with_features:
            table[f] = sorted(set(table.get(f) or []) | set(names))
        for f in without_features:
            table[f] = sorted(set(table.get(f) or []) - set(names))
        json.dump(table, open(fp, "w", encoding="utf-8"), indent=1)
    if os.path.isdir(os.path.join(FARM, "geo")) and not os.path.isdir(os.path.join(out_farm, "geo")):
        shutil.copytree(os.path.join(FARM, "geo"), os.path.join(out_farm, "geo"))
    if memory_from and os.path.isdir(memory_from):
        for f in glob.glob(os.path.join(memory_from, "*.jsonl")):
            if not os.path.exists(os.path.join(out_farm, "memory", os.path.basename(f))):
                shutil.copy(f, os.path.join(out_farm, "memory", os.path.basename(f)))


def redirect(out_farm):
    """Point every module that writes under work/botfarm (or work/botfarm-watch) at the run folder, and the brains' connect() at the FakeClient."""
    os.environ["BOTFARM_DB"] = os.path.join(out_farm, "memory", "farm.db")
    import bot_common
    import caster
    import memory
    import loopguard
    import ground_rates
    import planner
    import geo
    import stall
    import farmdb
    import mage_bot
    bot_common.FARM = caster.FARM = out_farm
    memory.MEMDIR = bot_common.MEMDIR = caster.MEMDIR = os.path.join(out_farm, "memory")
    loopguard.QUEUE_PATH = os.path.join(out_farm, "watch", "queue.jsonl")
    loopguard.ROOT = out_farm                                # its cuolog path becomes <out_farm>/work/navrey-sessions/<bot>/cuolog, which the FakeClient writes
    ground_rates.PATH = os.path.join(out_farm, "memory", "ground_rates.json")
    planner.SHARED = os.path.join(out_farm, "memory", "activity_rates.json")
    geo.GEO_DIR = os.path.join(out_farm, "geo")
    stall.os = _OsProxy(os.path.join(out_farm, "watch"))
    _connect = sqlite3.connect
    farmdb.sqlite3 = type("sqlite3", (), {"connect": staticmethod(lambda p, **k: _connect(p, check_same_thread=False, **k)), "OperationalError": sqlite3.OperationalError,
                                          "DatabaseError": sqlite3.DatabaseError, "Error": sqlite3.Error})()
    mage_bot.print = lambda *a, **k: None                    # the mage bot echoes its log to stdout
    bot_common.faulthandler.dump_traceback_later = lambda *a, **k: None
    bot_common.faulthandler.cancel_dump_traceback_later = lambda *a, **k: None
    return bot_common, caster, mage_bot


def load_roster(a):
    roster = []
    if a.roster and os.path.exists(a.roster):
        roster = json.load(open(a.roster, encoding="utf-8"))
    if a.smoke:
        picked = []
        for cls, prof in CLASS_PROFESSION.items():
            if a.classes and cls not in a.classes:
                continue
            rec = next((r for r in roster if PROFESSION_CLASS.get(r["profession"]) == cls), None)
            rec = dict(rec) if rec else {"name": f"Sim{cls.title()}", "profession": prof, "skills": {}}
            rec["name"] = f"Sim{cls.title()}"
            picked.append(rec)
        roster = picked
    elif a.classes:
        roster = [r for r in roster if PROFESSION_CLASS.get(r["profession"]) in a.classes]
    if not roster:
        roster = [{"name": f"Sim{cls.title()}", "profession": prof, "skills": {}} for cls, prof in CLASS_PROFESSION.items()]
    roster = roster[: a.bots]
    if a.procs > 1 and a.part is not None:
        roster = [r for i, r in enumerate(roster) if i % a.procs == a.part]
    return roster


class Sim:
    def __init__(self, a):
        self.a = a
        self.out = a.out
        self.out_farm = os.path.join(self.out, "farm")
        self.part = a.part
        self.tag = f"-{a.part}" if a.part is not None else ""
        # the cohorts are edited by the parent of a --procs run only (run_parts): five parts editing the file at once raced, and a part that read a
        # half-written file wrote back only its own ten names (the 2026-10-20 travel-planner run: twenty bots without the core)
        if a.part is None:
            prepare(self.out_farm, a.memory_from, a.with_feature, a.without_feature, [r["name"] for r in load_roster(a)])
        else:
            prepare(self.out_farm, a.memory_from)
        self.bot_common, self.caster, self.mage_bot = redirect(self.out_farm)
        self.data = WorldData(radius=a.radius)
        self.price_tables = wd.price_tables(self.data.vendor_buys)
        self.world = World(self.data, seed=a.seed + (a.part or 0), now=real_time(), walk_tps=a.walk_tps, run_tps=a.run_tps)
        self.clock = VirtualClock(self.world.now())
        self.start = self.clock.now
        self.bots = {}
        self.players = {}
        self.crashes = []
        self.rows = []
        self.last_metrics = self.start
        self.last_print = real_time()
        self.t0 = real_time()
        self.metrics_path = os.path.join(self.out_farm, f"metrics{self.tag}.jsonl")
        self.roster = load_roster(a)
        clients = {}
        bc = self.bot_common

        def fake_connect(name, *args, **kw):
            return clients[name]

        bc.connect_retry = fake_connect
        self.mage_bot.connect_retry = fake_connect
        for rec in self.roster:
            p = self.world.add_player(rec)
            self.players[rec["name"]] = p
            d = os.path.join(self.out_farm, "work", "navrey-sessions", rec["name"])
            os.makedirs(d, exist_ok=True)
            p.cuolog = open(os.path.join(d, "cuolog"), "a", encoding="utf-8", buffering=1 << 16)
            clients[rec["name"]] = FakeClient(self.world, p)
        self._throttle_status()

    def _throttle_status(self):
        """The brains write status.json, facts.json, totals.json and bank.json every 10 s; once a minute is plenty for a simulation of fifty."""
        import hunter
        import crafter
        import tamer
        import fisher
        import miner
        for cls in (self.bot_common.BotBase, self.caster.CasterBot, hunter.HunterBot, hunter.BardBot, crafter.CrafterBot, tamer.TamerBot, fisher.FisherBot, miner.MinerBot):
            if "status" in vars(cls):
                orig = vars(cls)["status"]

                def status(self_, force=False, _orig=orig):
                    if not force and time.time() - self_.last_status < 60:
                        return
                    return _orig(self_, force=True)

                cls.status = status

    # ---- the bots ----------------------------------------------------------------------------------------------------------------------------------

    def brain_class(self, rec):
        kind = PROFESSION_CLASS.get(rec["profession"], "hunter")
        if kind in ("hunter", "bard"):
            import hunter
            return hunter.BardBot if rec["profession"] == 9 else hunter.HunterBot
        if kind == "caster":
            return self.caster.CasterBot
        if kind == "crafter":
            import crafter
            return crafter.CrafterBot
        if kind == "tamer":
            import tamer
            return tamer.TamerBot
        if kind == "fisher":
            import fisher
            return fisher.FisherBot
        import miner
        if "broke_plan" in self.bot_common.load_features(rec["name"]):
            from broke_gather import BrokeMinerBot
            return BrokeMinerBot
        return miner.MinerBot

    def bot_body(self, rec, seconds):
        name = rec["name"]
        os.environ["BOT_MODE"] = rec.get("mode", "veteran")
        cls = None
        try:
            cls = self.brain_class(rec)
            bot = cls(name, rec["profession"])
            self.bots[name] = bot
            if hasattr(bot, "refresh_skills"):
                bot.refresh_skills()
            if hasattr(bot, "cfg") and hasattr(bot, "skill_values"):
                bot.skill = bot.skill_values.get(bot.cfg["skill"], 0.0)
            bot.run(seconds)
        except Exception as e:
            self.crashes.append({"bot": name, "class": cls.__name__ if cls else "?", "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:],
                                 "sim_t": round(self.clock.now - self.start)})

    # ---- the run -----------------------------------------------------------------------------------------------------------------------------------

    def advance(self, dt):
        self.world.step(dt)
        now = self.clock.now + dt
        if now - self.last_metrics >= 60:
            self.last_metrics = now
            self.write_metrics(now)
        if real_time() - self.last_print >= self.a.progress_every:
            self.last_print = real_time()
            self.progress()

    def write_metrics(self, now):
        with open(self.metrics_path, "a", encoding="utf-8") as f:
            for name, p in self.players.items():
                bot = self.bots.get(name)
                if bot is None:
                    continue
                gains = sum((getattr(bot, "stats", {}).get("gains") or {}).values()) if hasattr(bot, "stats") else 0
                skills = {k: v for k, v in sorted(p.skills.items()) if v > 0}
                row = {"t": int(now), "bot": name, "prof": getattr(bot, "pname", None) or PROF_NAME.get(p.profession), "hp": p.hp, "gold": p.gold(), "kills": p.kills,
                       "deaths": p.deaths, "gains": gains, "skills": dict(sorted(skills.items(), key=lambda kv: -kv[1])[:6]), "all_skills": skills,
                       "rule": getattr(bot, "last_rule", None), "pos": [p.x, p.y], "bank": self.world._bank_gold(p), "weight": p.weight(), "ghost": p.ghost,
                       "holdings": wd.holdings_value(list(p.backpack) + list(p.bank) + list(p.equipped), self.price_tables),
                       "pack": wd.holdings_by_item(list(p.backpack) + list(p.bank) + list(p.equipped), self.price_tables)}
                self.rows.append(row)
                f.write(json.dumps(row) + "\n")

    def snapshot(self):
        st = self.world.stats
        return {"part": self.part, "sim_h": round((self.clock.now - self.start) / 3600, 3), "real_s": round(real_time() - self.t0, 1), "world": dict(st),
                "exceptions": dict(self.exception_count()), "crashes": len(self.crashes), "switches": self.clock.switches, "bots": len(self.roster)}

    def progress(self):
        snap = self.snapshot()
        json.dump(snap, open(os.path.join(self.out, f"progress{self.tag}.json"), "w"))
        if not self.a.quiet:
            print(progress_line(snap), flush=True)

    def exception_count(self):
        out = collections.Counter()
        for name, bot in self.bots.items():
            p = os.path.join(self.out_farm, name, "run.log")
            try:
                n = sum(1 for l in open(p, encoding="utf-8", errors="replace") if "EXCEPTION" in l)
            except OSError:
                n = 0
            if n:
                out[type(bot).__name__] += n
        return out

    def run(self):
        a = self.a
        seconds = a.hours * 3600
        self.clock.install()
        if a.stacks:
            _dump_stacks(a.stacks, repeat=True, file=open(os.path.join(self.out, f"stacks{self.tag}.txt"), "w"))
        try:
            for i, rec in enumerate(self.roster):
                self.clock.spawn(lambda rec=rec: self.bot_body(rec, seconds), rec["name"], start_in=i * 0.37)
            self.clock.run(self.start + seconds + 1, on_advance=self.advance)
        finally:
            self.clock.uninstall()
        self.progress()
        for p in self.players.values():
            try:
                p.cuolog.close()
            except Exception:
                pass
        prof_of = {n: (getattr(b, "pname", None) or PROF_NAME.get(self.players[n].profession)) for n, b in self.bots.items()}
        part = {"part": self.part, "bots": len(self.roster), "sim_hours": a.hours, "real_seconds": round(real_time() - self.t0, 1), "world": dict(self.world.stats),
                "crashes": self.crashes, "exceptions": dict(self.exception_count()), "events": [[round(t - self.start), k, b, str(d)] for t, k, b, d in self.world.events],
                "prof_of": prof_of, "walked": {n: round(p.walked) for n, p in self.players.items()}}
        json.dump(part, open(os.path.join(self.out, f"part{self.tag}.json"), "w"))
        return part


def progress_line(snap):
    st = snap["world"]
    return (f"sim {snap['sim_h']:5.2f} h | real {snap['real_s']:6.0f} s | bots {snap['bots']} | kills {st['kills']} deaths {st['deaths']} crafts {st['crafts']} gathers {st['gathers']} "
            f"sales {st['sales']} buys {st['buys']} casts {st['casts']} tames {st['tames']} | exceptions {sum(snap['exceptions'].values())} crashes {snap['crashes']}")


# ---- the scoreboard --------------------------------------------------------------------------------------------------------------------------------------

WARMUP_H = 0.0


def scoreboard(out, parts, rows, hours_asked):
    """The farm's measures over the run, the first WARMUP_H hours (--warmup) left out: a run that starts on fresh spawns is loot-rich for its first quarter hour."""
    if rows and WARMUP_H > 0:
        t_from = min(r["t"] for r in rows) + WARMUP_H * 3600.0
        rows = [r for r in rows if r["t"] >= t_from]
        for part in parts:
            part["events"] = [e for e in part.get("events", []) if e[0] >= WARMUP_H * 3600.0]       # a part's events carry seconds from the run's start
        hours_asked = max(0.0, hours_asked - WARMUP_H)
    use = collections.defaultdict(collections.Counter)
    botmins = collections.Counter()
    first, last, prev, speeds = {}, {}, {}, []
    for r in rows:
        g = group(r.get("prof"))
        use[g][rule_cat(g, r.get("rule"))] += 1
        botmins[g] += 1
        first.setdefault(r["bot"], r)
        last[r["bot"]] = r
        p = prev.get(r["bot"])
        if p and 30 <= r["t"] - p["t"] <= 90:
            d = max(abs(r["pos"][0] - p["pos"][0]), abs(r["pos"][1] - p["pos"][1]))
            if d > 0:
                speeds.append(d / (r["t"] - p["t"]) * 60)
        prev[r["bot"]] = r
    hours = {g: n / 60 for g, n in botmins.items()}
    ev = collections.defaultdict(collections.Counter)
    prof_of, crashes, exceptions, world = {}, [], collections.Counter(), collections.Counter()
    real = 0.0
    for part in parts:
        prof_of.update(part.get("prof_of", {}))
        crashes += part.get("crashes", [])
        exceptions.update(part.get("exceptions", {}))
        world.update(part.get("world", {}))
        real = max(real, part.get("real_seconds", 0))
    for part in parts:
        for t, kind, bot, detail in part.get("events", []):
            ev[group(prof_of.get(bot))][kind] += 1
    board = {"bots": sum(p.get("bots", 0) for p in parts), "sim_hours": round(hours_asked, 2), "real_seconds": round(real, 1), "procs": len(parts),
             "bot_hours": {g: round(h, 2) for g, h in hours.items()}, "world": dict(world), "crashes": crashes, "exceptions": dict(exceptions), "groups": {}, "warmup_h": WARMUP_H}
    fights = fight_outcomes(os.path.join(out, "farm"), prof_of, min(r["t"] for r in rows) if rows else 0)
    flips = rule_flips(os.path.join(out, "farm"), prof_of)
    if speeds:
        speeds.sort()
        board["walk_tiles_per_min"] = {"median": round(speeds[len(speeds) // 2], 1), "p90": round(speeds[int(len(speeds) * 0.9)], 1), "rows": len(speeds)}
    for g in sorted(hours):
        n = sum(use[g].values()) or 1
        h = max(hours[g], 1e-6)
        bots = [b for b in last if group(last[b].get("prof")) == g]
        gold = sum((last[b]["gold"] + last[b].get("bank", 0)) - (first[b]["gold"] + first[b].get("bank", 0)) for b in bots)
        main_gain = 0.0
        for b in bots:
            ms = MAIN.get(last[b].get("prof"))
            if ms:
                main_gain += last[b]["all_skills"].get(ms, 0) - first[b]["all_skills"].get(ms, 0)
        fo = fights.get(g, collections.Counter())
        fl = flips.get(g, {})
        board["groups"][g] = {"bots": len(bots), "bot_hours": round(h, 2), "time": {k: round(100 * v / n, 1) for k, v in use[g].most_common()},
                              "kills_per_h": round(ev[g]["kill"] / h, 2), "deaths_per_h": round(ev[g]["death"] / h, 3), "gold_per_h": round(gold / h, 1),
                              "wealth_per_h": round(sum((last[b]["gold"] + last[b].get("bank", 0) + last[b].get("holdings", 0)) - (first[b]["gold"] + first[b].get("bank", 0) + first[b].get("holdings", 0)) for b in bots) / h, 1),
                              "main_skill_per_h": round(main_gain / h, 3), "gains_per_h": round(ev[g]["gain"] / h, 2), "sales": ev[g]["sale"], "buys": ev[g]["buy"],
                              "crafts": ev[g]["craft"], "gathers": ev[g]["gather"], "tames": ev[g]["tame"],
                              "fights": dict(fo), "lost_pct": round(100.0 * fo["lost"] / max(1, fo["kill"] + fo["lost"]), 1),
                              "rule_changes_per_h": round(fl.get("changes", 0) / h, 1), "rule_flips_per_h": round(fl.get("flips", 0) / h, 2),
                              "list_rules_acted": sorted(fl.get("list_rules", ()))}
    json.dump(board, open(os.path.join(out, "scoreboard.json"), "w", encoding="utf-8"), indent=1)
    lines = [f"# Simulator scoreboard: {board['bots']} bots, {board['sim_hours']} simulated hours in {board['real_seconds']} s real ({board['procs']} process{'es' if board['procs'] != 1 else ''})", "",
             "| Group | Bots | Bot-h | Work | Travel | Rest | Dead | Other | Kills/bot-h | Deaths/bot-h | Gold/bot-h | Main skill/bot-h | Gains/bot-h | Sales | Buys | Crafts | Gathers | Tames | Lost fights | Rule flips/bot-h |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for g, v in board["groups"].items():
        t = v["time"]
        lines.append(f"| {g} | {v['bots']} | {v['bot_hours']} | {t.get('work', 0)}% | {t.get('travel', 0)}% | {t.get('rest', 0)}% | {t.get('dead', 0)}% | {round(t.get('other', 0) + t.get('camp', 0), 1)}% | "
                     f"{v['kills_per_h']} | {v['deaths_per_h']} | {v['gold_per_h']:+} | {v['main_skill_per_h']:+} | {v['gains_per_h']} | {v['sales']} | {v['buys']} | {v['crafts']} | {v['gathers']} | {v['tames']} | "
                     f"{v['lost_pct']}% of {v['fights'].get('kill', 0) + v['fights'].get('lost', 0)} | {v['rule_flips_per_h']} |")
    lines += ["", f"World: {json.dumps(board['world'])}", f"Walking (tiles per minute between rows, rows that moved): {board.get('walk_tiles_per_min')}",
              "Rule-list rules acted (below the reflexes), by group: " + "; ".join(f"{g}: {', '.join(v['list_rules_acted']) or 'none'}" for g, v in board["groups"].items()),
              f"Exceptions by brain class: {json.dumps(board['exceptions'])}", f"Crashes: {len(crashes)}"]
    for c in crashes:
        lines.append(f"- {c['bot']} ({c['class']}) at sim {c['sim_t']} s: {c['error']}")
    text = "\n".join(lines) + "\n"
    open(os.path.join(out, "scoreboard.md"), "w", encoding="utf-8").write(text)
    return board, text


def fight_outcomes(out_farm, prof_of, since=0):
    """{group: Counter(outcome)} from the run's shared memory fight records (world.jsonl) since `since` (the run's own window: the seeded memory carries the farm's history)."""
    out = collections.defaultdict(collections.Counter)
    for folder in ("memory", "memory-newbie"):                      # newbie-mode bots write their fights to memory-newbie (15 of the 50 bots: the watcher's 2026-10-21 catch)
        try:
            for line in open(os.path.join(out_farm, folder, "world.jsonl"), encoding="utf-8", errors="replace"):
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if ev.get("k") == "fight" and ev.get("outcome") and ev.get("t", 0) >= since - 1:
                    out[group(prof_of.get(ev.get("bot")))][ev["outcome"]] += 1
        except OSError:
            pass
    return out


def rule_flips(out_farm, prof_of):
    """{group: {changes, flips, list_rules}} from the bots' run.log "rule -> X" lines: every change, the A -> B -> A flips between rule-list rules, and which
    rule-list rules below the reflexes acted at all (the decision core bypasses them: none for a task_core bot)."""
    out = collections.defaultdict(lambda: {"changes": 0, "flips": 0, "list_rules": set()})
    for name, prof in prof_of.items():
        g = group(prof)
        seq = []
        try:
            for line in open(os.path.join(out_farm, name, "run.log"), encoding="utf-8", errors="replace"):
                i = line.find("rule -> ")
                if i >= 0:
                    seq.append(line[i + 8:].strip())
        except OSError:
            continue
        d = out[g]
        d["changes"] += len(seq)
        for k, r in enumerate(seq):
            if r.startswith("r_") and r not in REFLEXES:
                d["list_rules"].add(r)
            if k >= 2 and r == seq[k - 2] and r != seq[k - 1] and r.startswith("r_") and seq[k - 1].startswith("r_"):
                d["flips"] += 1
    return out


def run_parts(a):
    """The parent of a --procs run: start the parts, print their combined progress, merge their metrics and parts into one scoreboard."""
    prepare(os.path.join(a.out, "farm"), a.memory_from, a.with_feature, a.without_feature, [r["name"] for r in load_roster(argparse.Namespace(**dict(vars(a), part=None)))])
    procs = []
    for i in range(a.procs):
        argv = [sys.executable, os.path.abspath(__file__), "--part", str(i), "--procs", str(a.procs), "--out", a.out, "--quiet", "--bots", str(a.bots), "--hours", str(a.hours),
                "--roster", a.roster, "--seed", str(a.seed), "--radius", str(a.radius), "--walk-tps", str(a.walk_tps), "--run-tps", str(a.run_tps),
                "--progress-every", str(a.progress_every), "--warmup", str(a.warmup)]
        if a.classes:
            argv += ["--classes", ",".join(a.classes)]
        if a.smoke:
            argv.append("--smoke")
        for f in a.with_feature:
            argv += ["--with-feature", f]
        for f in a.without_feature:
            argv += ["--without-feature", f]
        procs.append(subprocess.Popen(argv, stdout=open(os.path.join(a.out, f"part-{i}.out"), "w"), stderr=subprocess.STDOUT))
    last = 0.0
    while any(p.poll() is None for p in procs):
        time.sleep(1.0)
        if real_time() - last >= a.progress_every and not a.quiet:
            last = real_time()
            snaps = []
            for i in range(a.procs):
                try:
                    snaps.append(json.load(open(os.path.join(a.out, f"progress-{i}.json"))))
                except (OSError, ValueError):
                    pass
            if snaps:
                tot = {"sim_h": min(s["sim_h"] for s in snaps), "real_s": max(s["real_s"] for s in snaps), "bots": sum(s["bots"] for s in snaps), "world": collections.Counter(),
                       "exceptions": collections.Counter(), "crashes": sum(s["crashes"] for s in snaps)}
                for s in snaps:
                    tot["world"].update(s["world"])
                    tot["exceptions"].update(s["exceptions"])
                print(progress_line(tot) + f" | {len(snaps)}/{a.procs} parts reporting", flush=True)
    parts, rows = [], []
    for i in range(a.procs):
        try:
            parts.append(json.load(open(os.path.join(a.out, f"part-{i}.json"))))
        except (OSError, ValueError):
            print(f"part {i} left no result (see part-{i}.out)")
    with open(os.path.join(a.out, "farm", "metrics.jsonl"), "w", encoding="utf-8") as out:
        for i in range(a.procs):
            try:
                for line in open(os.path.join(a.out, "farm", f"metrics-{i}.jsonl"), encoding="utf-8"):
                    out.write(line)
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        pass
            except OSError:
                pass
    rows.sort(key=lambda r: r["t"])
    return scoreboard(a.out, parts, rows, a.hours)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bots", type=int, default=50)
    ap.add_argument("--hours", type=float, default=10.0)
    ap.add_argument("--procs", type=int, default=1, help="processes to split the roster over (each with its own world)")
    ap.add_argument("--part", type=int, default=None, help=argparse.SUPPRESS)
    ap.add_argument("--roster", default=os.path.join(FARM, "sim", "roster.json"))
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None)
    ap.add_argument("--classes", default="", help="comma list of brain classes to run: hunter,bard,caster,crafter,tamer,fisher,miner")
    ap.add_argument("--smoke", action="store_true", help="one bot per brain class; exit 1 on any exception or crash")
    ap.add_argument("--memory-from", default=None, help="a memory folder whose jsonl files seed the run's shared memory (default: empty)")
    ap.add_argument("--warmup", type=float, default=0.0, help="hours at the start left out of the scoreboard (the world settles from fresh spawns); the run lasts --hours")
    ap.add_argument("--with-feature", action="append", default=[], help="every bot of the run gets this feature (in the run's copy of features.json)")
    ap.add_argument("--without-feature", action="append", default=[], help="every bot of the run loses this feature")
    ap.add_argument("--radius", type=int, default=900)
    ap.add_argument("--walk-tps", type=float, default=2.6, help="walking speed, tiles per second")
    ap.add_argument("--run-tps", type=float, default=4.6, help="running speed, tiles per second")
    ap.add_argument("--progress-every", type=float, default=20.0, help="real seconds between progress lines")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--stacks", type=float, default=0, help="dump every thread's stack to <out>/stacks.txt every N real seconds")
    a = ap.parse_args(argv)
    global WARMUP_H
    WARMUP_H = float(getattr(a, "warmup", 0.0) or 0.0)
    a.classes = [c.strip() for c in a.classes.split(",") if c.strip()]
    if a.out is None:
        a.out = os.path.join(FARM, "sim", ("smoke-" if a.smoke else "run-") + time.strftime("%Y%m%d-%H%M%S"))
    a.out = os.path.abspath(a.out)
    os.makedirs(a.out, exist_ok=True)
    if a.procs > 1 and a.part is None:
        board, text = run_parts(a)
    else:
        sim = Sim(a)
        if not a.quiet:
            print(f"{len(sim.roster)} bots, {a.hours} h, world: {len(sim.data.spawners)} spawners, {len(sim.world.creatures)} creatures, {len(sim.world.vendors)} vendors; out {a.out}", flush=True)
        part = sim.run()
        if a.part is not None:
            return 0
        board, text = scoreboard(a.out, [part], sim.rows, a.hours)
    if not a.quiet:
        print(text)
    bad = sum(board["exceptions"].values()) + len(board["crashes"])
    if a.smoke and bad:
        print(f"SMOKE FAILED: {len(board['crashes'])} crash(es), {sum(board['exceptions'].values())} exception line(s) in the brains' tick loops")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
