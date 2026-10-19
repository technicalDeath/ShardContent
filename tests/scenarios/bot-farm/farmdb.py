"""The farm's transactional store (watcher, 2026-10-18, owner's "Store + decision records"): one SQLite database in WAL mode that every bot
process shares, at work/botfarm/memory/farm.db (BOTFARM_DB overrides it, for tests).

Why: the shared rate tables (memory/ground_rates.json, memory/activity_rates.json) were whole JSON files that 50 processes read, changed and
rewrote with no lock, so two bots writing at once lost an update (and a failed os.replace was silently ignored; a stray .tmp was left behind).
And a decision was logged only as a sentence ("hunting ground: cell 1320,1840 score 58.7"), without what the bot knew, what else it weighed or
what came of it, which is the data any learning needs.

Two tables:
  rates      (tbl, key) -> avg, n, t        an exponential average per key, updated atomically: rate_update(), rate_table()
  decisions  one row per choice: t, bot, prof, kind, chosen, context (JSON: what the bot knew), options (JSON: what it weighed),
             outcome (JSON: gold, kills, gains, died, work, secs summed over the episodes that followed), closed_t
             decision_open() at the choice, decision_add() from each episode after it, closed when the next choice of the same kind comes or
             after DECISION_TTL. Read them with DuckDB or sqlite3 (work/botfarm-watch/q.py).
Every call is best-effort: a database problem is logged by the caller at most, never raised into a brain.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "..", "..", "..", "..", "work", "botfarm", "memory", "farm.db")
DECISION_TTL = 1800.0
OUTCOME_KEYS = ("secs", "gold", "kills", "gains", "died", "work", "hp")

_con = {"pid": None, "path": None, "c": None}


def path():
    return os.path.abspath(os.environ.get("BOTFARM_DB") or DEFAULT)


def con():
    """This process's connection (a new one after a fork, or when BOTFARM_DB changed)."""
    p = path()
    if _con["c"] is None or _con["pid"] != os.getpid() or _con["path"] != p:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        c = sqlite3.connect(p, timeout=15, isolation_level=None)
        c.execute("pragma journal_mode=wal")
        c.execute("pragma synchronous=normal")
        c.execute("pragma busy_timeout=15000")
        c.execute("create table if not exists rates (tbl text not null, key text not null, avg real not null, n integer not null, t integer not null, primary key (tbl, key))")
        c.execute("create table if not exists decisions (id integer primary key, t real not null, bot text not null, prof text, kind text not null, chosen text,"
                  " context text, options text, outcome text, closed_t real)")
        c.execute("create index if not exists decisions_open on decisions (bot, closed_t)")
        _con.update(pid=os.getpid(), path=p, c=c)
    return _con["c"]


# ---- rates -----------------------------------------------------------------------------------------------------------------------------------------

def rate_update(tbl, key, value, alpha):
    """Fold value into the exponential average for (tbl, key), atomically; returns [avg, n, t]. The first value is taken as is."""
    c = con()
    now = int(time.time())
    c.execute("begin immediate")
    try:
        row = c.execute("select avg, n from rates where tbl = ? and key = ?", (tbl, key)).fetchone()
        if row:
            avg, n = round(row[0] + alpha * (value - row[0]), 2), row[1] + 1
            c.execute("update rates set avg = ?, n = ?, t = ? where tbl = ? and key = ?", (avg, n, now, tbl, key))
        else:
            avg, n = round(value, 2), 1
            c.execute("insert into rates (tbl, key, avg, n, t) values (?, ?, ?, ?, ?)", (tbl, key, avg, n, now))
        c.execute("commit")
    except Exception:
        c.execute("rollback")
        raise
    return [avg, n, now]


def rate_table(tbl, import_json=None):
    """{key: [avg, n, t]} for a table. On first use, import_json (the old JSON file) seeds an empty table, so nothing measured so far is lost."""
    c = con()
    if import_json and not c.execute("select 1 from rates where tbl = ? limit 1", (tbl,)).fetchone():
        try:
            old = json.load(open(import_json, encoding="utf-8"))
        except (OSError, ValueError):
            old = {}
        if old:
            c.execute("begin immediate")
            try:
                if not c.execute("select 1 from rates where tbl = ? limit 1", (tbl,)).fetchone():
                    c.executemany("insert or ignore into rates (tbl, key, avg, n, t) values (?, ?, ?, ?, ?)",
                                  [(tbl, k, float(v[0]), int(v[1]), int(v[2]) if len(v) > 2 else 0) for k, v in old.items() if isinstance(v, list) and len(v) >= 2])
                c.execute("commit")
            except Exception:
                c.execute("rollback")
                raise
    return {k: [a, n, t] for k, a, n, t in c.execute("select key, avg, n, t from rates where tbl = ?", (tbl,))}


def export_json(tbl, json_path):
    """Write the table to its old JSON file too (best-effort), for the readers that still open the file. The database is the source of truth."""
    try:
        d = rate_table(tbl)
        tmp = json_path + f".{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=0)
        os.replace(tmp, json_path)
    except OSError:
        try:
            os.remove(json_path + f".{os.getpid()}.tmp")
        except OSError:
            pass


# ---- decisions -------------------------------------------------------------------------------------------------------------------------------------

def decision_open(bot, prof, kind, chosen, context=None, options=None, now=None):
    """A choice was made: close this bot's open choice of the same kind (and any too old), then open this one. Returns its id."""
    c = con()
    now = now or time.time()
    c.execute("begin immediate")
    try:
        c.execute("update decisions set closed_t = ? where bot = ? and closed_t is null and (kind = ? or t < ?)", (now, bot, kind, now - DECISION_TTL))
        cur = c.execute("insert into decisions (t, bot, prof, kind, chosen, context, options, outcome) values (?, ?, ?, ?, ?, ?, ?, ?)",
                        (now, bot, prof, kind, None if chosen is None else str(chosen)[:200], json.dumps(context or {}, separators=(",", ":"), default=str),
                         json.dumps(options, separators=(",", ":"), default=str) if options is not None else None, json.dumps({k: 0 for k in OUTCOME_KEYS})))
        c.execute("commit")
    except Exception:
        c.execute("rollback")
        raise
    return cur.lastrowid


def decision_add(bot, delta, now=None):
    """An episode ended: add what it yielded to every open choice of this bot (a choice is credited with what followed it until it closes)."""
    c = con()
    now = now or time.time()
    c.execute("begin immediate")
    try:
        c.execute("update decisions set closed_t = ? where bot = ? and closed_t is null and t < ?", (now, bot, now - DECISION_TTL))
        for rid, out in c.execute("select id, outcome from decisions where bot = ? and closed_t is null", (bot,)).fetchall():
            o = json.loads(out or "{}")
            for k in OUTCOME_KEYS:
                o[k] = round((o.get(k) or 0) + (delta.get(k) or 0), 2)
            c.execute("update decisions set outcome = ? where id = ?", (json.dumps(o, separators=(",", ":")), rid))
        c.execute("commit")
    except Exception:
        c.execute("rollback")
        raise
