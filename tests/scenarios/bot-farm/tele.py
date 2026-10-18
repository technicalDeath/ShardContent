"""Generic teleport handling for the bot brains (generality migration step 3; replaces the SEWER_* tiles and sewer_cross).

Any teleporter, dungeon entrance or hatch is handled the same way, from data and from what the bots see:
 * a JUMP is a teleport: while a walk runs (tele_wait, used by the goto / gotoexact wrappers) the position is looked at every 0.4 s; a move of more than
   JUMP_TILES in one look is a teleporter, so the walk is cancelled AT ONCE (a walk left running re-plans toward its old target from the new side and walks
   straight back through the exit), ev "teleport" {src, dst, how, known, key} is logged and the pair is remembered in the shared memory (kind "tele");
 * SIDES: the gazetteer says which side of the map a point is on ("surface", or the name of the dungeon / town region); the pathfinder cannot plan
   between two sides, so a walk whose target is on another side first walks to a teleporter entry that leads there (gazetteer transitions, plus pairs
   bots have seen and the gazetteer lacks), steps on it, checks it jumped, and carries on from the new side. A hop that does not jump blocks that entry
   for this bot for 10 minutes and the route is planned again through the next entry; the failure is also recorded in memory;
 * ENTERING a side other than the surface needs a reason: tele_allowed(side) (a brain that wants to be there calls tele_allow(side); a bot that is on a
   side keeps it allowed for 15 minutes, which covers a corpse run or a camp revisit); LEAVING to the surface is always allowed.
Pure helpers plus the mixin TeleMixin (BotBase uses it); needs self.c (Navrey client), self.mem, self.facts, self.ev, self.log, self.mobs.
"""
import json
import os
import time
from types import SimpleNamespace

import gazetteer as gz

JUMP_TILES = 8                                          # a move this far between two looks (0.4 s; running covers 3 to 5 tiles) is a teleport
LOOK = 0.4
BLOCK_SECONDS = 600
ALLOW_SECONDS = 900
HOP_LIMIT = 4
REACH = 100                                             # on a small region an entry or landing must be within this many tiles (the Britain sewer is 85 across; the next level of its region is 130 away)
BIG_LEVEL = 90000                                       # tiles in a region's rectangles from which landings may be far from the target
MATCH_TILES = 6                                         # a seen jump within this many tiles of a known pair's entry and landing is that pair
DIRS = {(0, -1): "n", (0, 1): "s", (1, 0): "e", (-1, 0): "w", (1, -1): "ne", (-1, -1): "nw", (1, 1): "se", (-1, 1): "sw"}


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def sign(v):
    return (v > 0) - (v < 0)


MIN_PATH = 8                                            # a recorded path shorter than this (tiles, first to last waypoint) is not worth keeping
TRAIL_WINDOW = 120.0                                    # seconds of walking before a jump that make its path
WAYPOINT_GAP = 6                                        # tiles between kept waypoints (a leg short enough for the planner), or a z change of 3
WAYPOINT_CAP = 12
PATH_REACH = 40                                         # the bot must be within this many tiles of a waypoint for a path to be used
PATH_FLOOR = 6                                          # and not on another floor by more than this (when both z are known)
PATH_FAILS = 2                                          # failures since the newest success that retire a path until another bot succeeds
LEG_SECONDS = 25.0
LEG_TOTAL = 90.0                                        # the whole replay
PATHS_FILE = "exit_paths.jsonl"


def trail_waypoints(trail, now, window=TRAIL_WINDOW, gap=WAYPOINT_GAP, cap=WAYPOINT_CAP):
    """[(x, y, z)] thinned from a trail [(t, x, y, z)], oldest first: the contiguous walk (no jump) of the last `window` seconds."""
    walk = []
    for s in reversed(trail):
        if now - s[0] > window:
            break
        if walk and cheb((s[1], s[2]), (walk[-1][1], walk[-1][2])) > JUMP_TILES:
            break                                       # the position before an earlier jump: another side
        walk.append(s)
    walk.reverse()
    out = []
    for s in walk:
        z = s[3]
        d = cheb((s[1], s[2]), out[-1][:2]) if out else gap
        if not out or d >= gap or (d >= 3 and z is not None and out[-1][2] is not None and abs(z - out[-1][2]) >= 3):
            out.append((s[1], s[2], z))
    if walk and (walk[-1][1], walk[-1][2]) != out[-1][:2]:
        out.append((walk[-1][1], walk[-1][2], walk[-1][3]))
    out = out[-cap:]
    if len(out) < 2 or cheb(out[0][:2], out[-1][:2]) < MIN_PATH:
        return []
    return out


class TeleMixin:
    _in_tele = False
    _tele_jump = None                                   # (time, src, dst) of the last jump seen

    # ---- sides -----------------------------------------------------------------------------------------------------------------------------------

    def tele_side(self):
        return gz.side(self.c.x, self.c.y)

    def tele_side_of(self, x, y):
        return gz.side(x, y)

    def off_surface(self):
        return self.tele_side() != "surface"

    def in_sewer(self):                                 # BotBase default: any level below the surface; HunterBot narrows it to its own level
        return self.off_surface()

    def surface_target(self):                           # a point on the surface to leave toward (the side is all that matters)
        return (self.c.x, self.c.y) if not self.off_surface() else (0, 0)

    # ---- permission to enter a side ------------------------------------------------------------------------------------------------------------

    def tele_allow(self, side, seconds=ALLOW_SECONDS):
        self.facts.setdefault("tele_ok", {})[side] = time.time() + seconds

    def tele_allowed(self, side):
        if side == "surface":
            return True
        return self.facts.get("tele_ok", {}).get(side, 0) > time.time()

    # ---- the teleporters we know -------------------------------------------------------------------------------------------------------------

    def tele_pairs(self):
        """The gazetteer's teleporters plus pairs bots have seen that it lacks (shared memory kind "tele", key "sx,sy>dx,dy")."""
        base = list(gz.get().trans)
        known = {(t["src"][0], t["src"][1], t["dst"][0], t["dst"][1]) for t in base}
        try:
            self.mem.refresh()
            seen = self.mem.state["world"]["res"].get("tele", {})
            by = self.mem.state["world"]["res"].get("tele_by", {})
        except Exception:
            seen, by = {}, {}
        for key, r in list(seen.items()):
            try:
                s, d = key.split(">")
                sx, sy = (int(v) for v in s.split(","))
                dx, dy = (int(v) for v in d.split(","))
            except ValueError:
                continue
            if r.get("ok", 0) <= 0 or (sx, sy, dx, dy) in known:
                continue
            if r.get("ok", 0) <= r.get("fail", 0) or sum(1 for k in by if k.startswith(key + "#")) < 2:
                continue                                # a pair only one bot has seen (or that failed as often as it worked) is not a teleporter yet
            ss, ds = gz.side(sx, sy), gz.side(dx, dy)
            if ss != ds:
                base.append(dict(src=[sx, sy, 0], dst=[dx, dy, 0], kind="learned", src_side=ss, dst_side=ds, src_region=None, dst_region=None,
                                 derived=False, learned=True))
        return base

    def tele_blocked(self, t):
        key = f"{t['src'][0]},{t['src'][1]}"
        if self.facts.get("tele_bad", {}).get(key, 0) > time.time():
            return True
        try:
            return not self.mem.usable("tele_entry", key)
        except Exception:
            return False

    def tele_reach(self, side):
        """How far from the target a landing may be: a region named "Misc Dungeons" holds many unrelated levels (the Britain sewer and caves 150 tiles
        away share its name), so on a small region the landing must be near the target; on a big dungeon any entry of the region will do (None)."""
        r = gz.get().region(side)
        if not r or gz._area(r["rects"]) >= BIG_LEVEL:
            return None
        return REACH

    def tele_route(self, frm, to_side, target=None):
        """The teleporters to step on, in order, to get from `frm` (x, y) to the side `to_side`: [] when already there, None when no chain of the
        entries not blocked reaches it. The nearest entry at each hop, gazetteer entries before learned ones. On a small region (see tele_reach) an
        entry must be within REACH tiles of the bot, and with a `target` (x, y) the last hop must land within REACH tiles of it: another level of
        the same region does not count."""
        a = gz.side(frm[0], frm[1])
        if a == to_side:
            return []
        reach = self.tele_reach(to_side) if target else None
        g = {}
        for t in self.tele_pairs():
            if t["src_side"] != t["dst_side"] and not self.tele_blocked(t):
                if reach is not None and t["dst_side"] == to_side and cheb(t["dst"], target) > reach:
                    continue
                g.setdefault(t["src_side"], {}).setdefault(t["dst_side"], []).append(t)
        dead = set()                                    # side-to-side edges with no entry near the position (another level of a small region)
        for _ in range(6):
            prev, queue = {a: None}, [a]
            for cur in queue:
                for nxt in g.get(cur, {}):
                    if nxt not in prev and (cur, nxt) not in dead:
                        prev[nxt] = cur
                        queue.append(nxt)
            if to_side not in prev:
                return None
            path, cur = [], to_side
            while cur != a:
                path.append(cur)
                cur = prev[cur]
            path.append(a)
            path.reverse()
            pos, hops, ok = (frm[0], frm[1]), [], True
            for s1, s2 in zip(path, path[1:]):
                cands = g[s1][s2]
                r = self.tele_reach(s1)
                if r is not None:                       # on a small region the entry must be one the bot can walk to: on its own level
                    cands = [t for t in cands if cheb(t["src"], pos) <= r]
                if not cands:
                    dead.add((s1, s2))
                    ok = False
                    break
                t = min(cands, key=lambda t: (bool(t.get("learned")), cheb(t["src"], pos)))
                hops.append(t)
                pos = (t["dst"][0], t["dst"][1])
            if ok:
                return hops
        return None

    # ---- seeing a jump -------------------------------------------------------------------------------------------------------------------------

    def tele_match(self, before, after):
        """The known teleporter a seen jump was (entry within MATCH_TILES of `before`, landing within MATCH_TILES of `after`), else None."""
        best = None
        for t in self.tele_pairs():
            if cheb(t["src"], before) <= MATCH_TILES and cheb(t["dst"], after) <= MATCH_TILES:
                d = cheb(t["src"], before)
                if best is None or d < best[0]:
                    best = (d, t)
        return best[1] if best else None

    def staff_moved_recently(self, within=120):
        """True when unstick.py / drop_test.py moved this character by a staff command in the last `within` seconds (they touch <bot dir>/staff_moved)."""
        try:
            return time.time() - os.path.getmtime(os.path.join(self.dir, "staff_moved")) < within
        except (OSError, AttributeError):
            return False

    def tele_jumped(self, before, after, how="walk", entry=None):
        """The bot was teleported: stop the walk now, log it, remember the pair, allow the side it is on, close the dungeon warning gump.
        A jump within two minutes of a staff move is that move, not a teleporter: nothing is remembered."""
        self._tele_jump = (time.time(), tuple(before), tuple(after))
        try:
            self.c.cancel_walk()
        except Exception:
            pass
        time.sleep(0.4)
        if self.staff_moved_recently():
            self.ev("staff_move", src=list(before), dst=list(after), how=how)
            self._trail = []
            return
        hint = getattr(self, "_hop_entry", None) if self._in_tele else None
        if entry is None and hint is not None and cheb(hint["src"], before) <= 8 and gz.side(after[0], after[1]) == hint["dst_side"]:
            entry = hint                                    # walking to a known entry: that is the one it was (two hatches are 2 tiles apart)
        m = entry or self.tele_match(before, after)
        key = f"{m['src'][0]},{m['src'][1]}>{m['dst'][0]},{m['dst'][1]}" if m else f"{before[0]},{before[1]}>{after[0]},{after[1]}"
        self.ev("teleport", src=list(before), dst=list(after), how=how, known=bool(m and not m.get("learned")), key=key)
        self.exit_path_record(key, before)
        try:
            self.mem.record("res", kind="tele", key=key, ok=True)
            self.mem.record("res", kind="tele_by", key=f"{key}#{self.name}", ok=True)         # who saw it: a learned pair needs two bots
        except Exception:
            pass
        side = gz.side(after[0], after[1])
        if side != "surface":
            self.tele_allow(side)
            try:
                self.c.call("gumpresponse 0", timeout=4)       # "Warning: monsters may attack you on sight down here in the dungeons!"
            except Exception:
                pass

    def tele_wait(self, first_wait, timeout=300.0, poll=0.1):
        """A walk's wait that notices a teleport: looks every 0.4 s and, on a jump, cancels the walk at once and returns "teleported"."""
        end = time.time() + timeout
        prev = (self.c.x, self.c.y)
        target = getattr(getattr(first_wait, "__self__", None), "target", None)     # the Walk's (x, y)
        while True:
            left = end - time.time()
            res = first_wait(timeout=LOOK if left > LOOK else max(left, 0.05), poll=poll)
            cur = (self.c.x, self.c.y)
            if cheb(cur, prev) > JUMP_TILES:
                self.tele_jumped(prev, cur, "walk")
                return "teleported"
            prev = cur
            self.tele_trail_note()
            if str(res) != "timeout":
                return res
            nav = getattr(self.c, "nav", None)
            if target is not None and nav is not None and not nav.active and nav.target is not None and tuple(nav.target[:2]) == tuple(target[:2]):
                # the walk ended before a slice looked (Walk.wait's start-up wait used the whole slice): its status is the answer
                return nav.status
            if left <= LOOK:
                return "timeout"

    # ---- crossing -----------------------------------------------------------------------------------------------------------------------------

    def tele_step_dir(self, tx, ty):
        """One plain step toward an adjacent tile (the planner will not always step onto a teleporter tile; a direct step does)."""
        sx, sy = sign(tx - self.c.x), sign(ty - self.c.y)
        if sx and sy and cheb((self.c.x, self.c.y), (tx, ty)) == 1:
            # a diagonal step can be refused at a corner: stand straight beside the entry first, then step on (BotFairSwordNR 14:17, hatch 1491,1642)
            for nx, ny in ((tx - sx, ty), (tx, ty - sy)):
                self.c.gotoexact(nx, ny).wait(timeout=6)
                if (self.c.x, self.c.y) == (nx, ny) or (self._tele_jump and self._tele_jump[0] >= self._hop_t0):
                    break
        d = DIRS.get((sign(tx - self.c.x), sign(ty - self.c.y)))
        if not d or cheb((self.c.x, self.c.y), (tx, ty)) > 1:
            return
        for _ in range(2):                              # the first walk in a new direction only turns the character
            try:
                self.c.call(f"walk {d}", timeout=2)
            except Exception:
                pass
            time.sleep(0.7)
            if cheb((self.c.x, self.c.y), (tx, ty)) > 1 or (self._tele_jump and self._tele_jump[0] >= self._hop_t0):
                break

    def tele_landing_near(self, t):
        """(x, y) of a teleporter landing on this entry's side within 2 tiles of the entry (the reverse pair's arrival tile), or None."""
        best = None
        pairs = self.tele_pairs()
        entries = {(q["src"][0], q["src"][1]) for q in pairs}       # a landing that is itself an entry (Britain's two hatches) would teleport the bot
        for p in pairs:
            if (p["dst"][0], p["dst"][1]) in entries:
                continue
            if p["dst_side"] == t["src_side"] and cheb(p["dst"], t["src"]) <= 2 and (p["dst"][0], p["dst"][1]) != (t["src"][0], t["src"][1]):
                d = cheb(p["dst"], t["src"])
                if best is None or d < best[0]:
                    best = (d, (p["dst"][0], p["dst"][1]))
        return best[1] if best else None

    def tele_landing_z(self, t, land):
        """The z of the landing tile `land` from the transition table, or None."""
        for p in self.tele_pairs():
            if (p["dst"][0], p["dst"][1]) == tuple(land[:2]) and len(p["dst"]) > 2 and p["dst"][2]:
                return p["dst"][2]
        return None

    def tele_goto(self, x, y, z=None, exact=False):
        """goto / gotoexact with the floor named when it is known; a client whose goto takes no z gets the plain call."""
        fn = self.c.gotoexact if exact else self.c.goto
        if z is not None:
            try:
                return fn(x, y, z)
            except TypeError:
                pass
        return fn(x, y)

    # ---- learned exit paths (patch_exit_path_v2.py) -------------------------------------------------------------------------------------------------

    def tele_trail_note(self):
        """One sample (t, x, y, z) of where the bot is, at each look of tele_wait; the newest 300 are kept."""
        tr = self.__dict__.setdefault("_trail", [])
        x, y = self.c.x, self.c.y
        if tr and tr[-1][1] == x and tr[-1][2] == y:
            return
        try:
            z = self.c.z
        except Exception:
            z = None
        tr.append((time.time(), x, y, z))
        del tr[:-300]

    def exit_paths_file(self):
        try:
            return os.path.join(os.path.dirname(self.mem.paths["world"]), PATHS_FILE)
        except Exception:
            return None

    def exit_path_append(self, rec):
        path = self.exit_paths_file()
        if not path:
            return
        rec = dict(rec, t=time.time(), bot=self.name)
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        except OSError:
            pass

    def exit_path_record(self, key, before):
        """At a jump: keep the walk that led to the teleporter as waypoints (see the module doc), then forget the trail."""
        trail, self._trail = self.__dict__.get("_trail", []), []
        wps = trail_waypoints(trail, time.time())
        if wps:
            self.exit_path_append({"key": key, "wp": [list(w) for w in wps]})
            self.log(f"exit path for {key}: {len(wps)} waypoints from {wps[0][0]},{wps[0][1]}")

    def exit_path_read(self):
        """[records] of the paths file, parsed again only when the file changed."""
        path = self.exit_paths_file()
        try:
            st = os.stat(path)
        except (OSError, TypeError):
            return []
        c = self.__dict__.get("_paths_cache")
        if c and c[0] == (st.st_mtime_ns, st.st_size):
            return c[1]
        recs = []
        try:
            for line in open(path, encoding="utf-8"):
                try:
                    r = json.loads(line)
                    if isinstance(r, dict) and r.get("key"):
                        recs.append(r)
                except ValueError:
                    continue
        except OSError:
            pass
        self._paths_cache = ((st.st_mtime_ns, st.st_size), recs)
        return recs

    def exit_path_pick(self, key):
        """(waypoints, index of the one to start from) for this teleporter key, or None: two different bots recorded a path, fewer than PATH_FAILS failures since the newest one,
        and a waypoint of the newest path that fits is near the bot."""
        recs = self.exit_path_read()
        oks = [r for r in recs if r["key"] == key and r.get("wp")]
        if len({r["bot"] for r in oks}) < 2:
            return None
        newest = max(r["t"] for r in oks)
        if sum(1 for r in recs if r["key"] == key and "fail" in r and r.get("after") and r["t"] > newest) >= PATH_FAILS:
            return None
        here = (self.c.x, self.c.y)
        try:
            hz = self.c.z
        except Exception:
            hz = None
        best = None
        for r in sorted(oks, key=lambda r: -r["t"]):
            for i, w in enumerate(r["wp"]):
                d = cheb(here, w[:2])
                if d > PATH_REACH or (hz is not None and w[2] is not None and abs(w[2] - hz) > PATH_FLOOR):
                    continue
                if best is None or d < best[0]:
                    best = (d, r, i)
            if best:
                break                                   # the newest path with a fitting waypoint
        return (best[1]["wp"], best[1]["t"], best[2]) if best else None

    START_MAX = 4                                         # start points tried for one hop (patch_exit_path_v3)
    LEG_FIRST = 12.0                                      # the first leg: a wall shows at once
    START_WINDOW = 120.0                                  # no new start after this many seconds of replay
    NEAR_PATH = 3.5                                       # a recorded walk that passed this close to the bot's tile is preferred

    @staticmethod
    def seg_dist(p, a, b):
        """Distance from point p to the segment a-b (x, y pairs)."""
        ax, ay, bx, by = a[0], a[1], b[0], b[1]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
        return ((p[0] - (ax + t * dx)) ** 2 + (p[1] - (ay + t * dy)) ** 2) ** 0.5

    def exit_path_candidates(self, key, limit=None):
        """[(waypoints, stamp, start index)]: up to START_MAX start points from every recorded path for the key (two bots must have recorded one; fewer than PATH_FAILS "after" failures since the newest)."""
        recs = self.exit_path_read()
        oks = [r for r in recs if r["key"] == key and r.get("wp")]
        if len({r["bot"] for r in oks}) < 2:
            return []
        newest = max(r["t"] for r in oks)
        if sum(1 for r in recs if r["key"] == key and "fail" in r and r.get("after") and r["t"] > newest) >= PATH_FAILS:
            return []
        here = (self.c.x, self.c.y)
        try:
            hz = self.c.z
        except Exception:
            hz = None
        cands = []
        for r in oks:
            wp = r["wp"]
            passes = any(self.seg_dist(here, wp[i][:2], wp[i + 1][:2]) <= self.NEAR_PATH for i in range(len(wp) - 1))
            for i, w in enumerate(wp):
                d = cheb(here, w[:2])
                if d > PATH_REACH or (hz is not None and w[2] is not None and abs(w[2] - hz) > PATH_FLOOR):
                    continue
                cands.append((0 if passes else 1, d, -r["t"], r["t"], i, wp))
        cands.sort(key=lambda c: c[:3])
        out, taken = [], []
        for _, d, _, t, i, wp in cands:
            if any(cheb(wp[i][:2], q) <= 3 for q in taken):
                continue
            taken.append(wp[i][:2])
            out.append((wp, t, i))
            if len(out) >= (limit or self.START_MAX):
                break
        return out

    RING = ((0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1))
    STEP_RANGE = 14                                       # tiles from the waypoint within which a leg is finished by single steps
    STEP_SECONDS = 18.0

    def tele_step_leg(self, x, y, seen, max_steps=14):
        """Finish a leg the planner could not: single steps (`walk <dir>`) toward (x, y), the straight direction first, then 45 and 90 degrees to either side, a tile tried at most twice.
        True when the bot ends within 3 tiles of it (or a jump was seen)."""
        end = time.time() + self.STEP_SECONDS
        tried = {}
        for _ in range(max_steps):
            if seen():
                return True
            here = (self.c.x, self.c.y)
            if cheb(here, (x, y)) <= 2 or time.time() > end:
                break
            vec = (sign(x - here[0]), sign(y - here[1]))
            k = self.RING.index(vec)
            moved = False
            for off in (0, 1, -1, 2, -2):
                dx, dy = self.RING[(k + off) % 8]
                tile = (here[0] + dx, here[1] + dy)
                if tried.get(tile, 0) >= 2:
                    continue
                tried[tile] = tried.get(tile, 0) + 1
                for _turn in range(2):                         # the first walk in a new direction only turns the character
                    try:
                        self.c.call(f"walk {DIRS[(dx, dy)]}", timeout=2)
                    except Exception:
                        break
                    time.sleep(0.6)
                    if (self.c.x, self.c.y) != here or seen():
                        break
                if (self.c.x, self.c.y) != here or seen():
                    moved = True
                    break
            if not moved:
                break
        return seen() or cheb((self.c.x, self.c.y), (x, y)) <= 3

    def tele_follow_from(self, wps, start, seen):
        """Walk the waypoints from `start`. Returns (failed leg or None, got going). The first leg gets one short try: not within 3 tiles of it, the start is given up (got going False, nothing counts
        against the path). After a leg has succeeded, a waypoint that cannot be reached is skipped (two in a row at most); a third miss, the time cap or the end with a miss fails the replay."""
        end = time.time() + LEG_TOTAL
        progressed, misses, first_bad = False, 0, None
        for i in range(start, len(wps)):
            x, y, z = wps[i]
            if seen():
                return None, progressed
            if time.time() > end:
                return (first_bad if first_bad is not None else i), progressed
            for exact in ((False,) if i == start else (False, True)):
                self.tele_goto(x, y, z, exact=exact).wait(timeout=self.LEG_FIRST if i == start else LEG_SECONDS)
                if seen() or cheb((self.c.x, self.c.y), (x, y)) <= 2:
                    break
            if not seen() and 3 < cheb((self.c.x, self.c.y), (x, y)) <= self.STEP_RANGE:
                self.tele_step_leg(x, y, seen, max_steps=6 if i == start else 14)        # the planner could not finish it: single steps (stairs the planner cannot join)
            if seen():
                return None, True
            if cheb((self.c.x, self.c.y), (x, y)) <= 3:
                progressed, misses = True, 0
                continue
            if not progressed:
                return i, False
            first_bad = i if first_bad is None else first_bad
            misses += 1
            if misses > 2:
                return first_bad, True
        return (first_bad, True) if misses else (None, progressed)

    def tele_follow(self, wps, start, seen):
        """Walk the waypoints from `start`, each leg a goto naming the floor, then a gotoexact; returns the index of the leg that failed, or None when all were walked (or a jump was seen)."""
        end = time.time() + LEG_TOTAL
        for i in range(start, len(wps)):
            x, y, z = wps[i]
            if time.time() > end:
                return i
            for exact in (False, True):
                if seen():
                    return None
                self.tele_goto(x, y, z, exact=exact).wait(timeout=LEG_SECONDS)
                if seen() or cheb((self.c.x, self.c.y), (x, y)) <= 2:
                    break
            if not seen() and cheb((self.c.x, self.c.y), (x, y)) > 3:
                return i
        return None

    def tele_hop(self, t):
        """Walk to a teleporter's entry on this side and step on it; True when the bot jumped. A failure blocks that entry for this bot for 10 minutes."""
        sx, sy = t["src"][0], t["src"][1]
        before = (self.c.x, self.c.y)
        t0 = self._hop_t0 = time.time()
        self._hop_entry = t
        seen = lambda: bool(self._tele_jump and self._tele_jump[0] >= t0)
        self._in_tele = True
        try:
            if before == (sx, sy):
                self.c.goto(sx - 4, sy + 1).wait(timeout=10)                 # standing on the entry (just came out of it): step off, then on
            if not seen() and getattr(self, "feature", lambda n: False)("exit_path"):
                key = f"{sx},{sy}>{t['dst'][0]},{t['dst'][1]}"
                started = time.time()
                tried, counted = set(), False
                while not seen() and time.time() - started <= self.START_WINDOW:
                    cand = next(((w, s_, i_) for w, s_, i_ in self.exit_path_candidates(key, limit=8) if (s_, i_) not in tried), None)       # from where the bot stands now
                    if cand is None:
                        break
                    wps, stamp, i0 = cand
                    tried.add((stamp, i0))
                    self.log(f"exit path to {sx},{sy}: from waypoint {i0} of {len(wps)} ({wps[i0][0]},{wps[i0][1]}) at {self.c.x},{self.c.y}")
                    bad, going = self.tele_follow_from(wps, i0, seen)
                    if bad is None:
                        break
                    if going:
                        if not counted:
                            counted = True
                            self.exit_path_append({"key": key, "fail": bad, "after": True})
                        self.log(f"exit path to {sx},{sy}: leg {bad} ({wps[bad][0]},{wps[bad][1]}) failed after the replay got going, at {self.c.x},{self.c.y}; trying another start")
                        continue
                    self.log(f"exit path to {sx},{sy}: waypoint {bad} ({wps[bad][0]},{wps[bad][1]}) cannot be reached from {self.c.x},{self.c.y}; the next start")
            land = self.tele_landing_near(t)
            if land and not seen():
                # the landing of the reverse teleporter beside this entry: standable and reachable (players arrive there); walking at a raised entry
                # instead led into a pocket of the floor below it (BotMaceCR, 6048,1484). It is planned ONTO ITS OWN FLOOR (z of the transition table): a goto
                # without z plans to the surface nearest the bot's own z, and a stacked column (six surfaces at 6032,1499) then ends at the closest tile
                lz = self.tele_landing_z(t, land)
                for _ in range(3):
                    d0 = cheb((self.c.x, self.c.y), land)
                    self.tele_goto(land[0], land[1], lz).wait(timeout=45)
                    d1 = cheb((self.c.x, self.c.y), land)
                    if seen() or d1 <= 1 or d1 >= d0:
                        break                                        # arrived, jumped, or no closer: stop repeating
                if not seen():
                    self.tele_goto(land[0], land[1], lz, exact=True).wait(timeout=15)
            if not seen() and cheb((self.c.x, self.c.y), (sx, sy)) > 1:
                self.c.goto(sx, sy).wait(timeout=45)                         # may step on it already; a jump is noticed and the walk cancelled
            if not seen() and self.mobs(4) and self.hp_pct() < 60:
                return False
            if not seen():
                self.c.gotoexact(sx, sy).wait(timeout=15)
            if not seen() and cheb((self.c.x, self.c.y), (sx, sy)) > 1:
                # the entry itself can be out of the planner's reach (the sewer exit is raised, z 42 beside a landing at 31): stand on its nearest
                # walkable neighbour, then step on (BotMaceCR stopped 17 tiles short of 6031,1499 and the hop failed)
                near = sorted(((sx + dx, sy + dy) for dx, dy in DIRS), key=lambda p: cheb(p, (self.c.x, self.c.y)))
                for nx, ny in near[:4]:
                    if seen() or cheb((self.c.x, self.c.y), (sx, sy)) <= 1:
                        break
                    self.c.gotoexact(nx, ny).wait(timeout=15)
            if not seen():
                time.sleep(1.0)                                              # the walk is over: a moment for the server's move to arrive
            if not seen() and cheb((self.c.x, self.c.y), (sx, sy)) <= 1 and gz.side(self.c.x, self.c.y) == t["src_side"]:
                self.tele_step_dir(sx, sy)
        finally:
            self._in_tele = False
        jumped = seen() or gz.side(self.c.x, self.c.y) != t["src_side"]
        if jumped and not seen():
            self._in_tele = True
            try:
                self.tele_jumped(before, (self.c.x, self.c.y), "hop", entry=t)
            finally:
                self._in_tele = False
        if not jumped:
            self.facts.setdefault("tele_bad", {})[f"{sx},{sy}"] = time.time() + BLOCK_SECONDS
            try:
                self.mem.record("res", kind="tele", key=f"{sx},{sy}>{t['dst'][0]},{t['dst'][1]}", ok=False, reason="no jump")
            except Exception:
                pass
            self.log(f"teleport: stepping on {sx},{sy} did not move the bot (at {self.c.x},{self.c.y})")
        return jumped

    def tele_to_side(self, to_side, limit=150, target=None):
        """Cross to a side of the map: plan the teleporter chain, hop through it (planning again after each hop and each failure). True on arrival."""
        t0 = time.time()
        hops = 0
        while time.time() - t0 < limit and hops < HOP_LIMIT + 3:
            if self.tele_side() == to_side:
                return True
            if self.c.ghost and to_side != "surface":
                return False
            route = self.tele_route((self.c.x, self.c.y), to_side, target)
            if not route:
                return False
            hops += 1
            self.tele_hop(route[0])
        return self.tele_side() == to_side

    def tele_cross(self, tx, ty):
        """For the goto wrappers: a walk whose target is on another side first crosses. None = carry on with the real walk; else a stand-in walk that
        says why it cannot."""
        if self._in_tele:
            return None
        to_side = gz.side(tx, ty)
        if self.tele_side() == to_side:
            return None
        if not self.tele_allowed(to_side):
            return None                                                      # no reason to go there: the planner will answer nopath as it always did
        if self.tele_route((self.c.x, self.c.y), to_side, (tx, ty)) is None:
            return None
        if self.tele_to_side(to_side, target=(tx, ty)):
            return None
        return SimpleNamespace(wait=lambda timeout=300.0, poll=0.1: "nopath: teleport")

    def tele_enter(self, target, tag="tele"):
        """Go to the side `target` (x, y) is on, now, because the brain wants to be there; True when the bot is on it."""
        side = gz.side(target[0], target[1])
        if self.tele_side() == side:
            return True
        if self.c.ghost:
            return False
        self.tele_allow(side)
        ok = self.tele_to_side(side, limit=100, target=target)
        if not ok:
            self.log(f"{tag}: could not cross from {self.c.x},{self.c.y} to {side}")
        return ok

    def tele_leave(self, tag="tele", why="walk"):
        """Back to the surface by the entry the route finds; True when the bot is out. Every attempt starts with this bot's blocks cleared: the callers back
        off between attempts, and a retry that finds both entries blocked from the last pass would fail without trying."""
        if not self.off_surface():
            return True
        self.facts.pop("tele_bad", None)
        ok = self.tele_to_side("surface", limit=150)
        if not ok:
            self.log(f"{tag}: no way out from {self.c.x},{self.c.y} (why {why})")
        return ok
