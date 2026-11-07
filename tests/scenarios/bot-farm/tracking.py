"""Tracking (feature "tracking"; owner, 2026-11-05: "NEW bot capabilities ... doing things they haven't done before"). The ranger's template holds Tracking
(skillplan.TEMPLATES) and no bot ever used it: a hunter with nothing in view walked its tour blind. The engine (Skills/Tracking/Tracking.cs):
  - "useskill tracking" opens TrackWhatGump: buttons 1-4 Animals, Monsters, Human NPCs, Players;
  - a success (CheckSkill 0-21.1) lists the closest 12 of that kind within 10 + 10 per 10 skill points (TrackWhoGump: a button i+1 and the name per
    creature), else "You see no evidence of those in the area.";
  - choosing one points the quest arrow at it (packet 0xBA, moved as it moves: TrackArrow), which the Lean14 client puts in the state file as questArrow.
r_track: on a hunt that has arrived, nothing to fight in view, at most once per TRACK_GAP: track animals or monsters (alternately), take the first listed
creature the fight rating would take (rating.rate by its kind), and walk at the arrow until the prey is in view, at most FOLLOW_S; the hunt's own rules
fight it. Events: track {kind, list, picked, range}, track_none {kind_of, why}, track_found {kind, s}.
"""
from __future__ import annotations

import re
import time

TRACK_GAP = 45             # s between tracking tries (the skill's own delay is 10 s, SkillInfo; this keeps a tour's walking first)
FOLLOW_S = 120             # s to follow an arrow before the hunt goes on without it
MIN_SKILL = 20.0           # Tracking at which the list reaches 30 tiles, past the 18 a client sees
LEG = 14                   # tiles a follow step walks toward the arrow (in view of it, then the next step re-reads it)
WHAT = {"animals": 1, "monsters": 2}
BUTTON_RE = re.compile(r"\[button (\d+)\]")


def track_range(skill):
    """Tiles the list reaches: 10 + 10 per 10 skill points (TrackWhoGump.DisplayTo)."""
    return 10 + int(float(skill or 0) // 10) * 10


def kind_of(name):
    """The rating's key for a listed name: lower case letters only, without the article ("a grey wolf" -> "greywolf")."""
    n = re.sub(r"^(an?|the) ", "", (name or "").strip().lower())
    return re.sub(r"[^a-z]", "", n)


def parse_list(lines):
    """[(button, name)] from a TrackWhoGump dump: each "[button N]" followed by its creature's name (Narrator's gump text, in layout order)."""
    out, pending = [], None
    for raw in lines:
        t = raw.strip()
        if t.startswith("[GUMP]"):
            t = t[6:].strip()
        m = BUTTON_RE.fullmatch(t)
        if m:
            pending = int(m.group(1))
            continue
        if pending is not None and t and not t.startswith("[") and pending >= 1:
            out.append((pending, t))
            pending = None
    return out


def _serial(s):
    try:
        return int(str(s), 16) if str(s).lower().startswith("0x") else int(s)
    except (TypeError, ValueError):
        return None


def tamed_near(bot, within=30):
    """{kind key: count} of the tame creatures in view: the bot's own pet (rangerpet's facts["pet"]) and every creature shown Innocent (a tamed one is
    blue; a wild animal is grey and a monster red, which is all BotBase.mobs() hunts). The list names creatures, never serials, holds tamed ones too,
    nearest first (TrackWhoGump's InternalSorter): BotRangerBR tracked its own timber wolf 1-4 tiles off every 90 s (16:46-16:58), and after the first
    fix a second tamed timber wolf beside it (19:18-19:23), 2026-11-06, and "found" nothing, since a pet is no prey."""
    out = {}
    try:
        near = list(bot.c.mobiles(within=within))
    except Exception:
        return out
    pet = (getattr(bot, "facts", None) or {}).get("pet") or {}
    want = _serial(pet.get("serial"))
    for m in near:
        own = want is not None and _serial(getattr(m, "serial", None)) == want
        if own or getattr(m, "notoriety", None) == "Innocent":
            k = pet.get("kind") if own and pet.get("kind") else kind_of(getattr(m, "name", ""))
            if k:
                out[k] = out.get(k, 0) + 1
    return out


def pick_listed(listed, rate, tame=None):
    """(button, name) of the first listed creature the rating would fight, skipping the nearest ones of each kind as many as are tame in view
    (tamed_near: they are the pets), or None."""
    skip = dict(tame or {})
    for button, name in listed:
        k = kind_of(name)
        if skip.get(k, 0) > 0:
            skip[k] -= 1
            continue
        r = rate(k)
        if r and r.get("engage"):                          # (rating.rate: the fight worth taking)
            return (button, name)
    return None


class TrackMixin:
    def track_rate(self, k):
        """The fight rating of a listed kind (rating.rate); a hide hunt (crafter) takes only the kinds that carry hides."""
        import rating
        return rating.rate(self, k)

    def track_animals_only(self):
        return False

    def track_on(self):
        return self.feature("tracking") and float((getattr(self, "skill_values", {}) or {}).get("Tracking", 0)) >= MIN_SKILL

    def track_arrow(self):
        """(x, y) the quest arrow points at, while it is shown and fresh, else None."""
        qa = (self.c.state or {}).get("questArrow") if hasattr(self.c, "state") else None
        if not qa or float(qa.get("ageMs", 1e9)) > 10000:
            return None
        return int(qa["x"]), int(qa["y"])

    def track_hunting(self):
        """On a hunt that has arrived (the decision core's task), or roaming without the core, and out of town."""
        t = (self.facts or {}).get("task") or {}
        if t and (t.get("task") != "hunt" or not t.get("arrived")):
            return False
        try:
            import gazetteer as gz
            if gz.in_town(int(self.c.x), int(self.c.y)):
                return False
        except Exception:
            pass
        return True

    def track_gump(self, word, timeout=4.0):
        """(serial, lines) of the open gump whose text holds word, waiting up to timeout, else (None, [])."""
        end = time.time() + timeout
        while time.time() < end:
            try:
                lines = self.c.call("gumps", timeout=5)
            except Exception:
                lines = []
            serial, block = None, []
            for line in lines:
                m = re.search(r"server (0x[0-9A-Fa-f]+)", line)
                if m:
                    if serial and any(word in l for l in block):
                        return serial, block
                    serial, block = m.group(1), []
                else:
                    block.append(line)
            if serial and any(word in l for l in block):
                return serial, block
            time.sleep(0.5)
        return None, []

    def track_deadly(self, xy, kind):
        """True (and logged, ev track_skip) when the arrow points into the reach of a spawner this bot loses to (spots.measured_danger_near, the check a
        hunting tour's spots pass) or into a cell the area danger map marks (mem.dangerous_cell): the prey is not followed there. BotRangerAR tracked a horse to 1749,1316 in the gazer and gargoyle pocket north-east
        of Britain, rated the gazer that came up "leave it", ran and was killed (2026-11-07 11:15-11:27); 7 ranger deaths there overnight."""
        why = None
        try:
            import spots
            hit = spots.measured_danger_near(self, {"x": int(xy[0]), "y": int(xy[1])})
            if hit:
                why = f"{hit[0]} spawner at {hit[1]['x']},{hit[1]['y']}"
        except Exception:
            pass
        mem = getattr(self, "mem", None)
        if why is None and mem is not None:
            try:
                from memory import cell_of
                if mem.dangerous_cell(cell_of(int(xy[0]), int(xy[1]))):
                    why = f"a dangerous cell ({cell_of(int(xy[0]), int(xy[1]))})"       # the area danger map: spawners too strong, or recent deaths
            except Exception:
                pass
        if why is None:
            return False
        self.ev("track_skip", prey=kind, at=[int(xy[0]), int(xy[1])], why=why)
        self.log(f"tracking: not following the {kind} to {int(xy[0])},{int(xy[1])}: {why}")
        return True

    def r_track(self):
        """Feature tracking: find prey out of sight with the Tracking skill and walk at it (the module doc)."""
        if not self.track_on() or self.c.ghost:
            return False
        now = time.time()
        follow = self.__dict__.get("_track_follow")
        try:
            seen = bool(self.prey(14))
        except Exception:
            seen = True
        if follow:
            if seen or now > follow["until"] or self.threats(6):
                if seen:
                    self.ev("track_found", prey=follow["kind"], s=round(now - follow["t0"]))
                self.__dict__.pop("_track_follow", None)
                return False
            xy = self.track_arrow()
            if not xy or self.track_deadly(xy, follow["kind"]):
                self.__dict__.pop("_track_follow", None)
                return False
            d = max(abs(xy[0] - self.c.x), abs(xy[1] - self.c.y))
            step = 1.0 if d <= LEG else LEG / float(d)
            tx, ty = int(round(self.c.x + (xy[0] - self.c.x) * step)), int(round(self.c.y + (xy[1] - self.c.y) * step))
            self.activity = f"tracking a {follow['kind']} ({d} tiles)"
            self.c.goto(tx, ty).wait(timeout=10)
            return True
        if seen or now < float(self.facts.get("track_next", 0) or 0) or not self.track_hunting():
            return False
        try:
            if self.hp_pct() < 60 or self.threats(10):
                return False
        except Exception:
            return False
        self.facts["track_next"] = now + TRACK_GAP
        what = "animals" if self.track_animals_only() or self.facts.get("track_last") != "animals" else "monsters"
        self.facts["track_last"] = what
        self.activity = f"tracking {what}"
        self.c.events.drain()
        self.c.call("useskill tracking", timeout=6)
        serial, _ = self.track_gump("Animals")
        if not serial:
            self.ev("track_none", kind_of=what, why="no tracking menu")
            return False
        self.c.call(f"gumpresponse {WHAT[what]} gump:{serial}", timeout=5)
        serial2, lines = self.track_gump("[button 1]", timeout=3.0)
        listed = parse_list(lines) if serial2 and serial2 != serial else []
        if not listed:
            self.ev("track_none", kind_of=what, why="none listed")
            return False
        try:
            pick = pick_listed(listed, self.track_rate, tamed_near(self, track_range((getattr(self, "skill_values", {}) or {}).get("Tracking", 0))))
        except Exception:
            pick = None
        if pick is None:
            self.c.call(f"gumpresponse 0 gump:{serial2}", timeout=5)
            self.ev("track_none", kind_of=what, why="nothing worth a fight", list=[n for _, n in listed][:8])
            return False
        self.c.call(f"gumpresponse {pick[0]} gump:{serial2}", timeout=5)
        end = time.time() + 3
        while time.time() < end and not self.track_arrow():
            time.sleep(0.3)
        xy = self.track_arrow()
        rng = track_range((getattr(self, "skill_values", {}) or {}).get("Tracking", 0))
        self.ev("track", prey=kind_of(pick[1]), list=[n for _, n in listed][:8], picked=pick[1], range=rng, arrow=list(xy) if xy else None)
        if not xy or self.track_deadly(xy, kind_of(pick[1])):
            return True
        self.log(f"tracking: {pick[1]} at {xy[0]},{xy[1]} ({max(abs(xy[0] - self.c.x), abs(xy[1] - self.c.y))} tiles; {len(listed)} {what} within {rng})")
        self.__dict__["_track_follow"] = {"kind": kind_of(pick[1]), "t0": now, "until": now + FOLLOW_S}
        return True
