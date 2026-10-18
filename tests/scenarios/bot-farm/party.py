"""Parties for the farm's bots (Operator's board item 15:40, the watcher's A7 "company"; the Helper). Mixin for BotBase and CasterBot, written into the bot-farm folder by
patch_party.py. Behind the feature "party"; it needs the Navrey commands partyinfo / partyaccept / partydecline / partyleave / partyloot (Navrey/src/ClassicUO.Client/Agent/Commands/
CommandEngine.Party.cs, in client build Lean5 or later); on a client that lacks them the first partyinfo gets no [PARTY] line, the feature stays off for this brain and nothing else changes.

What a party is here: a real UO party (server: Party.cs), at most 3. FORMING: a bot in the field with another bot of the farm within 12 tiles whose main skill is within 20 of its own, and
who is itself in the field (status.json: rule in FIELD), invites it with the party window's Add action (partyinvite, then target). The invitee accepts when the inviter
is a farm bot close by with a main skill within 20 (else declines). Who invites: the higher main skill (ties: the smaller name), or the leader of a party with room. PLAYING TOGETHER:
party members are not "other bots on this ground" (other_bots, ground_load: one ground for the party, no crowded-spot exit, no kill-steal guard between them), a member more than
40 tiles from the leader follows it (until 200), a casting member heals members under 60% (Greater Heal, else Heal, from the book) and blesses / strengthens a member before a fight; the
danger model counts a fight with the party's members at hand as a smaller pack (near minus party members within 10 tiles). LOOT: partyloot on once per membership (the server's
party loot flag; stock Corpse rules then let members loot each other's kills). DISBANDING: a member leaves when its main skill differs from the leader's by more than 30, when it is
farther than 200 tiles from every other member for 5 minutes, or when it starts a first trip (trips are not party-aware: the bot goes alone); a ghost stays in the party and rejoins
the others when resurrected, or leaves by the distance rule.
Events (decisions.jsonl): party_invite {target}, party_form {members, ground}, party_join {leader}, party_heal {target, spell}, party_buff {target, spell}, party_disband {why}.
"""
import json
import os
import re
import time

PARTY_MAX = 3
BAND_FORM = 20
BAND_KEEP = 30
RANGE_FORM = 12
INVITE_GAP = 90                   # seconds before the same bot is invited again
INFO_EVERY = 6                    # seconds a partyinfo answer is kept
STATUS_EVERY = 20
FOLLOW_FROM, FOLLOW_TO = 40, 200
FAR_LEAVE_S = 300
HEAL_BELOW = 60
BUFF_EVERY = 150
BUFFS = ("bless", "strength")
FIELD = frozenset({"r_hunt", "r_fight", "r_camp", "r_explore", "r_loot", "r_rest", "r_party", "r_heal", "r_tame", "r_practice", "r_carve", "r_avoid", "r_evade", "r_flee"})
INFO = re.compile(r"\[PARTY\]\s+(?P<state>not in a party|in a party)\s+leader=0x(?P<leader>[0-9A-Fa-f]+)\s+inviter=0x(?P<inviter>[0-9A-Fa-f]+)\s+canloot=(?P<loot>yes|no)\s+members=(?P<n>\d+)(?P<rest>.*)")
MEMBER = re.compile(r"0x([0-9A-Fa-f]+):(\S+)")
ENTRY = re.compile(r"\[entry\s+(\d+)\]\s*(.+)")
_STATUS = {}
FARM_DIR = None


def farm_dir():
    global FARM_DIR
    if FARM_DIR is None:
        from bot_common import FARM
        FARM_DIR = FARM
    return FARM_DIR


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def serial_int(s):
    try:
        return int(str(s), 16)
    except (TypeError, ValueError):
        return 0


def parse_info(lines):
    """{in_party, leader (serial int), inviter (serial int), canloot, members [(serial int, name)]} from a partyinfo reply, or None when no [PARTY] line came."""
    for l in lines or ():
        m = INFO.search(str(l))
        if m:
            return {"in_party": m.group("state") == "in a party", "leader": int(m.group("leader"), 16), "inviter": int(m.group("inviter"), 16), "canloot": m.group("loot") == "yes",
                    "members": [(int(s, 16), n) for s, n in MEMBER.findall(m.group("rest"))]}
    return None


def pick_invite_entry(lines):
    """The index of the context menu's "Add to Party" entry, or None."""
    for l in lines or ():
        m = ENTRY.search(str(l))
        if m and "party" in m.group(2).lower() and not re.search(r"remove|leave|quit|kick", m.group(2).lower()):
            return int(m.group(1))
    return None


def status_of(name):
    """{skill (main skill value), pos, rule, ghost, age} from the farm's status.json of that bot, or None (cached 20 s)."""
    now = time.time()
    hit = _STATUS.get(name)
    if hit and now - hit[0] < STATUS_EVERY:
        return hit[1]
    out = None
    try:
        d = json.load(open(os.path.join(farm_dir(), name, "status.json"), encoding="utf-8"))
        skills = d.get("skills") or {}
        out = {"skill": max(skills.values()) if skills else 0.0, "pos": tuple(d.get("pos") or (0, 0)), "rule": d.get("rule", ""), "ghost": bool(d.get("ghost")), "age": now - d.get("t", 0)}
    except (OSError, ValueError, TypeError, AttributeError):
        out = None
    _STATUS[name] = (now, out)
    return out


class PartyMixin:
    _party_ok = None

    # ---- what the bot knows about its party -------------------------------------------------------------------------------------------------------------

    def party_names(self):
        """Names of the other members, from the last partyinfo (no round trip)."""
        p = self.facts.get("party")
        return set(p["names"]) if p else set()

    def party_skill(self):
        sv = getattr(self, "skill_values", None)
        if sv is not None and hasattr(self, "main_skill"):
            try:
                return float(sv.get(self.main_skill(), 0))
            except Exception:
                return 0.0
        return float(getattr(self, "skill", 0.0))

    def party_help(self):
        """How many party members are within 10 tiles of this bot (for the danger model's pack)."""
        names = self.party_names()
        if not names or not self.feature("party"):
            return 0
        return sum(1 for m in self.c.mobiles(within=10) if m.name in names and not getattr(m, "is_dead", False))

    def party_filter(self, bots):
        """BotBase.other_bots minus the party's members: their kills and spots are shared (no crowded-spot exit, no kill-steal guard between them)."""
        names = self.party_names() if self.feature("party") else set()
        return [o for o in bots if o[0] not in names] if names else bots

    def far_rules(self):
        rules = super().far_rules()
        if "r_party" not in rules and "r_hunt" in rules:
            rules.insert(rules.index("r_hunt"), "r_party")
        return rules

    def party_info(self, force=False):
        """The parsed partyinfo, kept INFO_EVERY seconds; None when the client has no such command (the feature then stays off for this brain)."""
        if self._party_ok is False:
            return None
        now = time.time()
        p = self.facts.get("party")
        if p and not force and now - p["t"] < (INFO_EVERY if p["info"]["in_party"] else 2):
            return p["info"]
        try:
            info = parse_info(self.c.call("partyinfo", timeout=3))
        except Exception as e:
            self.log(f"party: partyinfo failed ({type(e).__name__}: {e})")
            info = None
        if info is None:
            if self._party_ok is None:
                self._party_ok = False
                self.log("party: this client has no partyinfo command (build Lean5 or later): the party feature stays off")
            return None
        self._party_ok = True
        me_members = [(s, n) for s, n in info["members"] if n != self.name]
        self.facts["party"] = {"t": now, "info": info, "names": [n for _, n in me_members]}
        self.party_track(info)
        return info

    def party_track(self, info):
        """Events for a party forming, growing and ending; the loot flag once per membership."""
        names = sorted(n for _, n in info["members"]) if info["in_party"] else []
        prev = self.facts.get("party_seen", [])
        if names != prev:
            leader = next((n for s, n in info["members"] if s == info["leader"]), None)
            if len(names) >= 2 and len(names) > len(prev):
                if leader == self.name:
                    self.ev("party_form", members=names, ground=f"{self.c.x // 40 * 40},{self.c.y // 40 * 40}")
                elif len(prev) < 2:
                    self.ev("party_join", leader=leader)
            elif len(prev) >= 2 and len(names) < 2:
                self.ev("party_disband", why=self.facts.pop("party_leave_why", "dissolved or removed"))
            self.facts["party_seen"] = names
            if len(names) >= 2 and not info["canloot"]:
                self.party_command("partyloot on")
            if len(names) < 2:
                self.facts.pop("party_since", None)
            else:
                self.facts.setdefault("party_since", time.time())

    def party_command(self, line):
        try:
            return self.c.call(line, timeout=5)
        except Exception as e:
            self.log(f"party: {line} failed ({type(e).__name__}: {e})")
            return []

    def party_leave(self, why):
        self.facts["party_leave_why"] = why
        self.party_command("partyleave")
        self.facts.pop("party", None)
        self.facts["party_seen"] = []
        self.ev("party_disband", why=why)
        self.log(f"party: left ({why})")

    # ---- the rule ----------------------------------------------------------------------------------------------------------------------------------------

    def party_bots_near(self, within=RANGE_FORM):
        return [m for m in self.c.mobiles(within=within) if m.name.startswith("Bot") and m.name != self.name]

    def party_compat(self, name, mine=None):
        st = status_of(name)
        if st is None or st["age"] > 120:
            return None, None
        mine = self.party_skill() if mine is None else mine
        return abs(st["skill"] - mine) <= BAND_FORM, st

    def r_party(self):
        if not self.feature("party") or self.c.ghost or self._party_ok is False:
            return False
        now = time.time()
        near = self.party_bots_near()
        cached = self.facts.get("party")
        in_party = bool(cached and cached["info"]["in_party"])
        if not near and not in_party and not (cached and cached["info"]["inviter"]):
            if cached or now - self.facts.get("party_probe", 0) < 30:
                return False                                                  # nobody to party with and no party: no round trip
            self.facts["party_probe"] = now                                   # (but ask now and then: a restarted brain may be in a party it does not know of)
        info = self.party_info()
        if info is None:
            return False
        # an invitation: accept from a farm bot close by with a main skill within 20, else decline
        if info["inviter"] and not info["in_party"]:
            who = next((m for m in self.c.mobiles(within=20) if serial_int(m.serial) == info["inviter"]), None)
            ok = False
            if who is not None and who.name.startswith("Bot"):
                comp, _ = self.party_compat(who.name)
                ok = comp is not False
            self.party_command("partyaccept" if ok else "partydecline")
            self.facts.pop("party", None)
            self.log(f"party: {'accepted' if ok else 'declined'} the invitation from {who.name if who else hex(info['inviter'])}")
            return True
        if info["in_party"]:
            return self.party_member_step(info, now)
        return self.party_invite_step(near, info, now)

    def party_member_step(self, info, now):
        leader = next((n for s, n in info["members"] if s == info["leader"]), None)
        others = [n for _, n in info["members"] if n != self.name]
        # leave: skills drifted apart, a first trip begins, every other member is far away for five minutes
        lst = status_of(leader) if leader and leader != self.name else None
        if lst and abs(lst["skill"] - self.party_skill()) > BAND_KEEP:
            self.party_leave("skills drifted apart")
            return True
        if getattr(self, "current_rule", "") == "r_trip" or (getattr(self, "_trip", None) or {}).get("trip"):
            self.party_leave("first trip")
            return True
        pos = [status_of(n)["pos"] for n in others if status_of(n)]
        if pos and min(cheb((self.c.x, self.c.y), p) for p in pos) > FOLLOW_TO:
            since = self.facts.setdefault("party_far_since", now)
            if now - since > FAR_LEAVE_S:
                self.facts.pop("party_far_since", None)
                self.party_leave("far from the others")
                return True
        else:
            self.facts.pop("party_far_since", None)
        # follow the leader when it is more than 40 tiles away (not beyond 200)
        if leader and leader != self.name and lst:
            d = cheb((self.c.x, self.c.y), lst["pos"])
            if FOLLOW_FROM < d <= FOLLOW_TO and now - self.facts.get("party_follow_at", 0) > 3:
                self.facts["party_follow_at"] = now
                self.activity = f"following {leader}"
                self.goto_near(lst["pos"][0], lst["pos"][1], 8).wait(timeout=6)
                return True
        if leader == self.name and len(info["members"]) < PARTY_MAX:
            return self.party_invite_step(self.party_bots_near(), info, now)
        return False

    def party_invite_step(self, near, info, now):
        if self.facts.get("party_invite_at", 0) > now - 20:
            return False
        if getattr(self, "last_rule", "") not in FIELD and getattr(self, "last_rule", ""):
            return False
        members = len(info["members"]) if info["in_party"] else 1
        if members >= PARTY_MAX:
            return False
        mine = self.party_skill()
        invited = self.facts.setdefault("party_invited", {})
        names = {n for _, n in info["members"]}
        best = None
        higher = False
        for m in near:
            if m.name in names or invited.get(m.name, 0) > now - INVITE_GAP or getattr(m, "is_dead", False):
                continue
            comp, st = self.party_compat(m.name, mine)
            if not comp or st["ghost"] or (st["rule"] and st["rule"] not in FIELD):
                continue
            if st["skill"] > mine or (st["skill"] == mine and m.name < self.name):
                higher = True                                                  # a better candidate to lead is at hand
            if best is None or m.distance < best.distance:
                best = m
        if best is None:
            self.facts.pop("party_wait_since", None)
            return False
        if higher and not info["in_party"]:
            # the higher main skill leads: it invites, this one waits (up to 90 s: a bot that is full or busy may never ask)
            since = self.facts.setdefault("party_wait_since", now)
            if now - since < 90:
                return False
        self.facts.pop("party_wait_since", None)
        invited[best.name] = now
        self.facts["party_invite_at"] = now
        # the party window's Add button: partyinvite asks the server, which raises a target cursor; the target answers it. (The server's "Add to Party"
        # context menu entry exists only from AOS on; this shard is UOR, so the packet is the way. Live check 2026-10-15: partyinvite, 0.5 s, target.)
        self.party_command("partyinvite")
        time.sleep(0.6)
        try:
            self.c.target(best.serial)
        except Exception as e:
            self.log(f"party: targeting {best.name} failed ({type(e).__name__}: {e})")
            return True
        self.ev("party_invite", target=best.name)
        self.facts.pop("party", None)
        return True

    # ---- healing and blessing (casters) -----------------------------------------------------------------------------------------------------------------

    def party_spell(self, names):
        k = self.k
        for n in names:
            s = k.spell(n)
            if s and self.spell_ok(n) and k.reagent_ok(s, self.regs) and s["mana"] <= self.c.mana:
                return n, s
        return None, None

    def r_party_heal(self):
        if not self.feature("party") or self.c.ghost or self._party_ok is False:
            return False
        names = self.party_names()
        if not names:
            return False
        now = time.time()
        if now - self.facts.get("party_heal_at", 0) < 2.5:
            return False
        near = [m for m in self.c.mobiles(within=10) if m.name in names and not getattr(m, "is_dead", False)]
        hurt = sorted((m for m in near if m.hp_pct < HEAL_BELOW), key=lambda m: m.hp_pct)
        top = self.c.state.get("maxMana") or 40
        if hurt and self.hp_pct() >= 40:
            self.refresh_state()
            spell, s = self.party_spell(("greater heal", "heal"))
            if spell:
                m = hurt[0]
                self.facts["party_heal_at"] = now
                self.activity = f"healing {m.name}"
                ok = self.cast(spell, m.serial)
                self.ev("party_heal", target=m.name, spell=spell, hp=round(m.hp_pct), ok=bool(ok))
                return True
        # a blessing before a fight: prey in sight, a member at hand, mana to spare, once per member and spell every 150 s
        if near and self.c.mana >= 0.6 * top and self.prey(12):
            buffed = self.facts.setdefault("party_buffed", {})
            for m in sorted(near, key=lambda m: m.distance):
                for sp in BUFFS:
                    if buffed.get(f"{m.name}|{sp}", 0) > now - BUFF_EVERY:
                        continue
                    self.refresh_state()
                    spell, s = self.party_spell((sp,))
                    if spell:
                        buffed[f"{m.name}|{sp}"] = now
                        self.facts["party_heal_at"] = now
                        self.activity = f"{spell} on {m.name}"
                        ok = self.cast(spell, m.serial)
                        self.ev("party_buff", target=m.name, spell=spell, ok=bool(ok))
                        return True
        return False
