"""Buddy pairs (A7 company / G7; Helper 2, 2026-10-17; feature "buddy", which also needs the feature "party"): two fighters of similar strength find each other, party up, hunt the same
ground, bandage each other, and split for a town errand. Mixin for BotBase and CasterBot, written into the bot-farm folder by patch_buddy.py; it sits on top of party.py (the party itself,
its invitation, loot flag, healing spells, leave rules are party.py's).

What a player does: a character that wants company looks for someone about as good, goes to where they are hunting, hunts beside them, patches them up when they are hurt and does not
make them wait for the bank trip. Here:
  PUBLISHING   every 15 s each bot with the feature writes <farm>/<name>/buddy.json: {t, pos, rule, skill, ghost, party (names), errand (since when it is on a town errand, or 0), back_at
               (when its last errand of a minute or more ended), seeking}. Nothing else is shared: no new server traffic.
  RENDEZVOUS   r_buddy, a rule just before r_party: a bot in the field with no party (or a party of one), hp >= 70 and no threat near looks at the other bots' files (every 45 s): fresh
               (under 60 s), in the field (party.FIELD), not a ghost, not on an errand, a party with room, a main skill within BAND (20) of its own, on the surface and within REACH (150)
               tiles, and not at one of its own death spots (near_death_spot). The LOWER skill walks to the higher one (ties: the larger name), to within 8 tiles, in legs of 8 s, at most
               WALK_MAX (5 min); within 12 tiles party.py's invitation takes over (the higher one invites). No party after NEAR_WAIT (3 min) near the partner: pair_fail and a 15 min rest.
  TOGETHER     in a party of two or three, the FOLLOWER (whoever came back from an errand last; else the lower skill) walks back to within 6 tiles of the nearest member when it is more than
               STAY (15) tiles from it, in the field, with no threat within 6, hp >= 60 and no errand (party.py's own follow only starts at 40 tiles). A member on an errand, a ghost or one not
               in the field is not followed (the other goes on hunting alone). A bot never waits for a partner, so there is no stall to exempt; the walk is the rule r_buddy.
  HEALING      r_buddy_heal (non-casters; casters have party_heal): a member within 8 tiles under 50% hp is bandaged (move next to it, use_on the bandage) when the bot has a bandage, hp >= 60
               and no threat within 3 (or the member is under 30% and hp >= 70); one try per 12 s per member. Event party_heal {target, spell: "bandage"}.
  ERRANDS      a bot whose rule is a town errand (bank, sell, resupply, market, craft, trip, rest in town ...) for 60 s is "on an errand" in its file; its partner stays in the party and goes on
               hunting; ev pair_split {why: "errand", partner} once per errand. When the errand is over (back_at) the bot that came back is the follower and walks to its partner again.
  EVENTS       pair_start {partners, gap, ground}, pair_end {partners, minutes, replies, why} (replies = talk replies to people while the pair lasted), pair_split {why, partner},
               pair_fail {partner, why}, pair_walk {to, dist} once per walk. party_form / party_join / party_disband / party_heal are party.py's.
"""
import json
import os
import time

import party as _party

BAND = 20                 # main skills within this are "similar"
REACH = 150               # tiles: farther partners are not worth the walk
STAY = 15                 # tiles from the partner at which the follower walks back
NEAR_PARTNER = 6          # tiles it walks back to
MEET = 8                  # tiles it walks to when joining
WALK_MAX = 300            # seconds of WALKING (8-second legs) in one joining attempt before it gives up
WALK_WALL = 900           # seconds of the clock for the whole attempt (fights and flights in between count)
TOGETHER_MAX = 600        # seconds of the clock for one walk back to the partner
FAR_ASKS = 3              # party.py asks to leave when every other member has been >200 tiles away for 5 minutes; a buddy pair says no twice (15 minutes in all)
NEAR_WAIT = 180           # seconds near the partner without a party before pair_fail
REST = 900                # seconds before it tries again after a failure
PUBLISH_EVERY = 15
SCAN_EVERY = 45
FRESH = 60
ERRAND_AFTER = 60
HEAL_BELOW = 50
HEAL_EVERY = 12
ERRAND_RULES = frozenset({"r_bank", "r_sell", "r_sellgear", "r_sellmeat", "r_resupply", "r_restock", "r_market", "r_window", "r_upgrade", "r_craft", "r_trip", "r_dead", "r_corpse",
                          "r_cure", "r_lighten", "r_gear", "r_book", "r_train", "r_earn", "r_far", "r_wedged", "r_sewer_out", "r_facility"})
FIELD = _party.FIELD | {"r_buddy", "r_buddy_heal"}      # a bot walking to its partner is still in the field
_party.FIELD = FIELD                                       # (party.py reads its own FIELD when it invites: the walker must not look like someone on an errand)
_PEERS = {"t": 0.0, "rows": []}


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def farm_dir():
    return _party.farm_dir()


def read_peer(name):
    """The parsed buddy.json of one bot, or None."""
    try:
        d = json.load(open(os.path.join(farm_dir(), name, "buddy.json"), encoding="utf-8"))
        d["pos"] = tuple(d.get("pos") or (0, 0))
        return d
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def peers(me):
    """Every other bot's fresh buddy.json (cached 10 s)."""
    now = time.time()
    if now - _PEERS["t"] < 10:
        return [p for p in _PEERS["rows"] if p.get("name") != me]
    rows = []
    try:
        for n in os.listdir(farm_dir()):
            if n.startswith("Bot"):
                d = read_peer(n)
                if d and now - d.get("t", 0) < FRESH:
                    d["name"] = n
                    rows.append(d)
    except OSError:
        pass
    _PEERS.update(t=now, rows=rows)
    return [p for p in rows if p["name"] != me]


class BuddyMixin:
    # ---- the file other bots read -------------------------------------------------------------------------------------------------------------------

    def buddy_on(self):
        return self.feature("buddy") and self.feature("party")

    def buddy_party(self):
        """Names of the other party members: the last REAL membership (party_seen), which a pending invitation does not clear."""
        try:
            return sorted(n for n in (self.facts.get("party_seen") or ()) if n != self.name)
        except Exception:
            return []

    def party_bots_near(self, within=_party.RANGE_FORM):
        """Feature buddy: only bots that publish a fresh buddy.json (the features buddy and party) are partners; the rest never accept."""
        near = super().party_bots_near(within)
        if not self.buddy_on():
            return near
        ok = {p["name"] for p in peers(self.name)}
        return [m for m in near if m.name in ok]

    def buddy_tick(self):
        """After every tick: errand bookkeeping, the published file, the pair's start and end events."""
        if not self.buddy_on():
            return
        b = self.__dict__.setdefault("_buddy", {})
        now = time.time()
        rule = getattr(self, "current_rule", "") or ""
        if rule in ERRAND_RULES and not self.c.ghost:
            b.setdefault("errand_at", now)
        elif rule and rule not in ERRAND_RULES:
            since = b.pop("errand_at", None)
            if since and now - since >= ERRAND_AFTER:
                b["back_at"] = now
        self.buddy_pair_events(b, now)
        if now - b.get("published", 0) < PUBLISH_EVERY:
            return
        b["published"] = now
        errand = b.get("errand_at")
        doc = {"t": now, "pos": [int(self.c.x), int(self.c.y)], "rule": rule, "skill": round(self.party_skill(), 1), "ghost": bool(self.c.ghost),
               "party": self.buddy_party(), "errand": errand if errand and now - errand >= ERRAND_AFTER else 0, "back_at": b.get("back_at", 0),
               "seeking": not self.buddy_party()}
        path = os.path.join(farm_dir(), self.name, "buddy.json")
        try:
            with open(path + ".tmp", "w", encoding="utf-8") as f:
                json.dump(doc, f)
            os.replace(path + ".tmp", path)
        except OSError:
            pass

    def buddy_pair_events(self, b, now):
        names = self.buddy_party()
        prev = b.get("pair")
        if names and not prev:
            peer = read_peer(names[0])
            gap = round(abs(peer["skill"] - self.party_skill()), 1) if peer else None
            b["pair"] = {"since": now, "names": names, "replies": self.buddy_replies()}
            self.ev("pair_start", partners=names, gap=gap, ground=f"{self.c.x // 40 * 40},{self.c.y // 40 * 40}")
        elif prev and not names:
            self.ev("pair_end", partners=prev["names"], minutes=round((now - prev["since"]) / 60, 1), replies=max(0, self.buddy_replies() - prev["replies"]),
                    why=self.facts.get("party_leave_why", "dissolved or removed"))
            b.pop("pair", None)
        elif prev and names != prev["names"]:
            prev["names"] = names

    def party_leave(self, why):
        """Feature buddy: \"far from the others\" (an errand of over 5 minutes) is refused twice, so a pair survives one of 15 minutes; any other reason leaves at once."""
        if why == "far from the others" and self.buddy_on():
            b = self.__dict__.setdefault("_buddy", {})
            b["far_refused"] = b.get("far_refused", 0) + 1
            if b["far_refused"] < FAR_ASKS:
                self.log("buddy: staying in the party although far from the others")
                return
        self.__dict__.setdefault("_buddy", {}).pop("far_refused", None)
        return super().party_leave(why)

    def buddy_replies(self):
        """How many talk replies to people this bot has made (talk.py keeps the last hour's times)."""
        try:
            import talk
            return len(talk._st(self)["replied"])
        except Exception:
            return 0

    # ---- the rules ----------------------------------------------------------------------------------------------------------------------------------

    def far_rules(self):
        rules = super().far_rules()
        for name in ("r_buddy_heal", "r_buddy"):
            if name not in rules:
                at = rules.index("r_party") if "r_party" in rules else rules.index("r_hunt") if "r_hunt" in rules else len(rules)
                rules.insert(at, name)
        return rules

    def buddy_threat(self, within):
        try:
            return bool(self.mobs(within))
        except Exception:
            return False

    def buddy_follower(self, peer):
        """Who walks to whom: the one that came back from an errand last; else the lower skill; else the larger name."""
        mine, theirs = self.__dict__.get("_buddy", {}).get("back_at", 0), peer.get("back_at", 0)
        if mine != theirs:
            return mine > theirs
        sk = self.party_skill()
        if sk != peer["skill"]:
            return sk < peer["skill"]
        return self.name > peer["name"]

    def r_buddy(self):
        if not self.buddy_on() or self.c.ghost or getattr(self, "_party_ok", None) is False:
            return False
        now = time.time()
        b = self.__dict__.setdefault("_buddy", {})
        if now < b.get("rest_until", 0) or self.hp_pct() < 60 or self.buddy_threat(6):
            return False
        names = self.buddy_party()
        if names:
            return self.buddy_together(b, names, now)
        return self.buddy_seek(b, now)

    def buddy_together(self, b, names, now):
        b.pop("seek", None)
        rows = {p["name"]: p for p in peers(self.name) if p["name"] in names}
        if not rows:
            return False
        here = (self.c.x, self.c.y)
        peer = min(rows.values(), key=lambda p: cheb(here, p["pos"]))
        if peer.get("ghost") or peer.get("errand") or peer.get("rule") not in FIELD:
            if peer.get("errand") and not b.get("split_for") == peer.get("errand"):
                b["split_for"] = peer["errand"]
                self.ev("pair_split", why="errand", partner=peer["name"])
                self.log(f"buddy: {peer['name']} is on an errand; hunting alone meanwhile")
            return False
        d = cheb(here, peer["pos"])
        if d <= _party.FOLLOW_TO:
            b.pop("far_refused", None)                                   # not far from the others after all
        if d <= STAY or not self.buddy_follower(peer) or getattr(self, "last_rule", "") not in FIELD and getattr(self, "last_rule", ""):
            b.pop("walk_since", None)
            return False
        since = b.setdefault("walk_since", now)
        if now - since > TOGETHER_MAX:
            b.pop("walk_since", None)
            b["rest_until"] = now + 120
            self.log(f"buddy: could not get back to {peer['name']} in {TOGETHER_MAX // 60} min")
            return False
        self.activity = f"back to {peer['name']}"
        self.goto_near(peer["pos"][0], peer["pos"][1], NEAR_PARTNER).wait(timeout=8)
        return True

    def buddy_candidates(self):
        here = (self.c.x, self.c.y)
        mine = self.party_skill()
        out = []
        for p in peers(self.name):
            if p.get("ghost") or p.get("errand") or p.get("rule") not in FIELD or len(p.get("party") or ()) >= _party.PARTY_MAX - 1:
                continue
            if abs(p["skill"] - mine) > BAND:
                continue
            d = cheb(here, p["pos"])
            if d > REACH:
                continue
            try:
                if self.tele_side_of(*p["pos"]) != self.tele_side_of(*here):
                    continue                                            # not on the same level (the sewers, a dungeon)
                if self.near_death_spot(p["pos"][0], p["pos"][1], 40):
                    continue
            except Exception:
                pass
            out.append((d, p))
        return [p for d, p in sorted(out, key=lambda t: t[0])]

    def buddy_seek(self, b, now):
        if getattr(self, "last_rule", "") not in FIELD and getattr(self, "last_rule", ""):
            return False
        seek = b.get("seek")
        if seek is None:
            if now - b.get("scanned", 0) < SCAN_EVERY:
                return False
            b["scanned"] = now
            for p in self.buddy_candidates():
                if self.buddy_follower(p):
                    b["seek"] = seek = {"to": p["name"], "since": now, "near_since": None}
                    self.ev("pair_walk", to=p["name"], dist=cheb((self.c.x, self.c.y), p["pos"]))
                    self.log(f"buddy: going to {p['name']} (skill {p['skill']}, {cheb((self.c.x, self.c.y), p['pos'])} tiles)")
                    break
            if seek is None:
                return False
        peer = read_peer(seek["to"])
        if not peer or now - peer.get("t", 0) > FRESH * 2 or peer.get("ghost") or peer.get("errand") or peer.get("rule") not in FIELD:
            b.pop("seek", None)
            return False
        d = cheb((self.c.x, self.c.y), peer["pos"])
        if now - seek["since"] > WALK_WALL:
            return self.buddy_fail(b, seek, "no party formed", now)
        if d <= _party.RANGE_FORM:
            seek["near_since"] = seek["near_since"] or now
            if now - seek["near_since"] > NEAR_WAIT:
                return self.buddy_fail(b, seek, "not invited", now)
            if d > MEET:
                self.activity = f"joining {seek['to']}"
                self.goto_near(peer["pos"][0], peer["pos"][1], MEET - 2).wait(timeout=6)
                return True
            return False                                                # close enough: party.py's invitation takes it from here
        seek["near_since"] = None
        if seek.get("walked", 0) > WALK_MAX:
            return self.buddy_fail(b, seek, "too far to reach", now)
        self.activity = f"going to {seek['to']}"
        self.goto_near(peer["pos"][0], peer["pos"][1], MEET).wait(timeout=8)
        seek["walked"] = seek.get("walked", 0) + 8
        return True

    def buddy_fail(self, b, seek, why, now):
        b.pop("seek", None)
        b["rest_until"] = now + REST
        self.ev("pair_fail", partner=seek["to"], why=why)
        self.log(f"buddy: gave up on {seek['to']} ({why})")
        return False

    def r_buddy_heal(self):
        """Fighters bandage a hurt party member (casters have party_heal)."""
        if not self.buddy_on() or self.c.ghost or any(c.__name__ == "CasterBot" for c in type(self).__mro__):
            return False
        names = self.party_names()
        if not names:
            return False
        now = time.time()
        if self.hp_pct() < 60:
            return False
        hurt = sorted((m for m in self.c.mobiles(within=8) if m.name in names and not getattr(m, "is_dead", False) and m.hp_pct < HEAL_BELOW), key=lambda m: m.hp_pct)
        if not hurt:
            return False
        m = hurt[0]
        threat = self.buddy_threat(3)
        if threat and not (m.hp_pct < 30 and self.hp_pct() >= 70):
            return False
        done = self.facts.setdefault("buddy_healed", {})
        if now - done.get(m.name, 0) < HEAL_EVERY:
            return False
        band = self.c.find("bandage")
        if not band:
            return False
        done[m.name] = now
        self.activity = f"bandaging {m.name}"
        if m.distance > 1:
            self.goto_near(m.x, m.y, 1).wait(timeout=5)
        ok = self.c.use_on(band.serial, m.serial)
        self.ev("party_heal", target=m.name, spell="bandage", hp=round(m.hp_pct), ok=bool(ok))
        return True
