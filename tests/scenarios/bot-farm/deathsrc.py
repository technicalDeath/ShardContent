"""What killed this bot? (patch_death_source.py; logging only, no feature flag.)

A bot that dies with no hostile on its list used to log "killed by nothing seen" (BotTamerBR 14:25 at 1616,1441: one blow of 52 after "You feel yourself resisting magical energy" and a
"Your strength has changed by -7", no monster in the tick's list). The game does tell the player: this module keeps the last damage evidence from the journal and the last hostiles in view,
and source(bot) names the most likely source at death.

feed(bot, line)  every journal line (BotBase.read_journal, CasterBot.read_journal): own damage ("Damage: <me> takes N"), swings at the bot ("Swing: X -> <me>"), "X is attacking you!",
                 "<X> hits/bites/stings/... you", and cues: a spell on the bot ("You feel yourself resisting magical energy", "Your strength has changed by -N"), poison, paralysis.
snap(bot)        once per tick: the hostiles within 14 tiles (nearest 4), kept while none is in view (the killer may have been out of view by the death tick).
source(bot)      {key, label, why, sure, dmg, cues, near}: in this order, evidence from the last 30 s -
                   1. an attacker named by a swing, "is attacking you!" or "X hits you"        (sure)
                   2. poison ticks only (small hits, a poison cue)                              label "poison"
                   3. a spell cue: the nearest spell-casting kind in the snapshot (creature_stats "casts"/"breath"), else the nearest hostile, else "an unseen caster"
                   4. the nearest hostile of the snapshot                                       (a guess)
                   5. one blow of 35% of the bot's hit points or more                           label "one blow of N, source unseen"
                   6. "nothing seen"
key is the memory's name for the kind (lower case letters, no article) or None; label is for the log line, why for the death event.
"""
from __future__ import annotations

import re
import time
from collections import deque

WINDOW = 30.0
BURST = 0.35
POISON_HIT = 0.12                                        # a hit under this share of the hit points is a tick, not a blow
_SWING = re.compile(r"^Swing: (.+?) -> (.+?)(?::\s*(?:HIT|MISS))?$")
_HITS = re.compile(r"^(?:\[SYSTEM\] )?(?:The )?(.+?) (?:hits|bites|stings|claws|strikes|slashes|bashes|scratches|burns|pummels|smashes) you\b")
CUES = (("curse", re.compile(r"Your (?:strength|dexterity|intelligence) has changed by -\d+")),
        ("spell", re.compile(r"You feel yourself resisting magical energy|You are (?:dazzled|enveloped|engulfed)")),
        ("poison", re.compile(r"You (?:have been|are) poisoned|You feel (?:very )?(?:sick|ill)", re.I)),
        ("paralysis", re.compile(r"You are frozen|paralyz", re.I)))


def key_of(name):
    """The memory's name for a kind from a monster's name: "a gargoyle" -> "gargoyle"; None for a serial, a Bot or nothing."""
    n = (name or "").strip()
    if not n or n.startswith(("0x", "Bot")):
        return None
    k = re.sub(r"[^a-z]", "", re.sub(r"^(an?|the) ", "", n.lower()))
    return k or None


def state(bot):
    return bot.__dict__.setdefault("_dsrc", {"dmg": deque(maxlen=8), "att": None, "cue": None, "snap": None, "near": deque(maxlen=8)})


_NEAR = re.compile(r"(.+?) (0x[0-9A-Fa-f]+) d=(\d+) (\w+) (\d+)%")
NEAR_HOSTILE = ("Murderer", "Criminal", "Enemy", "Attackable", "Gray", "Grey")


def near_feed(bot, text):
    """A client-log "[NEAR] on damage: ..." line: who stood within 6 tiles when the bot was hit (hostile notorieties, never a Bot)."""
    i = text.find("on damage:")
    if i < 0:
        return
    found = []
    for part in text[i + 10:].split(";"):
        m = _NEAR.search(part.strip())
        if m and m.group(4) in NEAR_HOSTILE and not m.group(1).strip().startswith("Bot"):
            found.append((int(m.group(3)), m.group(1).strip()))
    if found:
        state(bot)["near"].append((time.time(), sorted(found)[0]))


def feed(bot, t):
    st, now, name = state(bot), time.time(), bot.name
    m = re.match(r"Damage: (.+?) takes (\d+)", t)
    if m:
        if m.group(1).startswith(name):
            st["dmg"].append((now, int(m.group(2))))
        return
    m = _SWING.match(t)
    if m:
        if m.group(2).startswith(name) and not m.group(1).startswith(name):
            st["att"] = (now, m.group(1).strip(), "swing")
            st.setdefault("hit_by", {})[m.group(1).strip()] = now
        return
    m = re.match(rf"\[SAY\] {re.escape(name)}: \*?(.+?) is attacking you!", t)
    if m:
        st["att"] = (now, m.group(1).strip(), "is attacking you")
        st.setdefault("hit_by", {})[m.group(1).strip()] = now
        return
    if not t.startswith("[SAY]"):
        m = _HITS.match(t)
        if m:
            st["att"] = (now, m.group(1).strip(), "hits you")
            st.setdefault("hit_by", {})[m.group(1).strip()] = now
    for kind, pat in CUES:
        if pat.search(t):
            st["cue"] = (now, kind, t[:80])


def snap(bot):
    """The hostiles in view (nearest 4: distance, name, kind key), remembered while any is."""
    try:
        ms = bot.mobs(14)
        if ms:
            near = sorted(((m.distance, m.name, key_of(m.name) or bot.mkey(m)) for m in ms), key=lambda s: s[0])[:4]
            state(bot)["snap"] = (time.time(), near)
    except Exception:
        pass


def _casts(key):
    try:
        import danger
        c = danger.stats().get(key or "")
        return bool(c and (c.get("casts") or c.get("breath")))
    except Exception:
        return False


def source(bot):
    st, now = state(bot), time.time()
    dmg = [(int(now - t), a) for t, a in st["dmg"] if now - t <= WINDOW]
    cue = st["cue"] if st["cue"] and now - st["cue"][0] <= WINDOW else None
    cues = [f"{cue[1]}: {cue[2]}"] if cue else []
    snapshot = st["snap"][1] if st["snap"] and now - st["snap"][0] <= WINDOW else []
    near = [[d, n] for d, n, k in snapshot]
    try:
        hp = max(1, bot.c.max_hp)
    except Exception:
        hp = 70

    def out(key, label, why, sure):
        return {"key": key, "label": label, "why": why, "sure": sure, "dmg": dmg[-4:], "cues": cues, "near": near}

    att = st["att"]
    if att and now - att[0] <= WINDOW:
        return out(key_of(att[1]), att[1], f"{att[2]} {int(now - att[0])} s before", True)
    small = bool(dmg) and all(a <= POISON_HIT * hp for _, a in dmg)
    if cue and cue[1] == "poison" and small:
        return out(None, "poison", "poison ticks, no attacker", True)
    seen = [(t, d, n) for t, (d, n) in st.get("near", ()) if now - t <= WINDOW]
    if seen:
        t, d, n = min(seen, key=lambda s: (s[1], -s[0]))       # the nearest, the latest among equals
        return out(key_of(n), f"{n} (beside it when hit)", f"the client's damage line: {n} {d} tiles away {int(now - t)} s before", d <= 2)
    if cue and cue[1] in ("spell", "curse", "paralysis"):
        casters = [s for s in snapshot if _casts(s[2])]
        if casters:
            d, n, k = casters[0]
            return out(k, f"{n} (a spell)", f"{cue[1]} cue; the nearest caster in view, {d} tiles", True)
        if snapshot:
            d, n, k = snapshot[0]
            return out(k, f"{n} (a spell?)", f"{cue[1]} cue; the nearest hostile in view, {d} tiles", False)
        return out(None, "an unseen caster", f"{cue[1]} cue, nobody in view", False)
    if snapshot:
        d, n, k = snapshot[0]
        return out(k, f"{n} (nearest in view)", f"nearest hostile {d} tiles away, no damage line names it", False)
    big = max([a for _, a in dmg] or [0])
    if big >= BURST * hp:
        return out(None, f"one blow of {big}, source unseen", f"{big} damage in one hit ({big * 100 // hp}% of the hit points)", False)
    return out(None, "nothing seen", "no damage source in the journal or in view", False)


def killers(bot, src=None):
    """The death record's killers list for a bot that had no hostile on its list: the named kind, if any."""
    src = src or source(bot)
    return [src["key"]] if src["key"] else []
