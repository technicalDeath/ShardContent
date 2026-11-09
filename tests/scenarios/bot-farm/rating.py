"""A fight's rating, from the bot's own numbers and the monster's, by the engine's pre-AOS combat rules (owner, 2026-11-04: "rate monsters using criteria the
bots can rely on that takes into account the bots stats, skills, and the enemy stats, skills. The ratings can drive the decisions to engage or not, and if the
rating is determined to be too tight or loose or specific inputs, that can be adjusted"). Every tunable is in rating.json beside this file.

The engine's rules (ModernUO, Core.AOS false; UOTD and LBR off, expansion.json; read 2026-11-04):
  hit chance   (atk + 50) / (2 x (def + 50)), atk the attacker's skill for its weapon, def the defender's for its own (Wrestling for fists)      BaseWeapon.CheckHit
               a player at AccessLevel.Player: x (1 + 0.66 x max(0, 1 - atk / 100)), the shard's novice lift (NoviceCombatService, noviceCombat)
  swing        15000 / ((stamina + 100) x speed) s; a player's stamina counts at least 60 (noviceCombat); a creature fights with Fists (speed 30) and has
               its Dex for stamina (BaseCreature.StamMax)                                                                                      BaseWeapon.GetDelay
  damage       base x (1 + (Tactics - 50) / 100) x (1 + Str/500 + Anatomy/500 [+ Lumberjacking/500 with an axe]); a player's Tactics counts at least
               30; halved when a player is hit, or when the attacker is no player                                                             ScaleDamageOld
               base: the weapon's OldMin..OldMaxDamage, a creature's SetDamage
  armour       a hit lands on one piece with the piece's body share (neck .07, hands .07, arms .14, head .15, legs .22, chest .35) and loses
               AR/2..AR of it, so a player loses 0.75 x the shown armour rating on average (PlayerMobile.ArmorRating sums AR x the same shares);
               a creature's VirtualArmor takes VA x s / 2 .. VA x s with s by body share, 0.75 x 0.2245 x VA on average; a hit does at least 1  AbsorbDamage
  hit points   a creature's SetHits under 1000 is x 100 / 60 (BaseCreature.SetHits pre-AOS)
  spells       a caster's expected damage a second: casterpass.per_cast / casterpass.interval (MageAI)
  a bot mage  its best damage spell (spell_plan): (3 + circle) x 0.25 s to cast and 0.75 s to recover (MagerySpell.CastDelayBase, Spell.NextSpellDelay),
               mana 4/6/9/11/14/20/40/50 by circle, regained at RegenRates' pre-AOS rate from (Int + Meditation) / 2; casterpass's fizzle, scalar and resist
  poison       pre-AOS ticks: clamp(1 + hits x pct, min, max) every interval, 10 ticks (PoisonKinds.cs), from a landed blow half the time
               (BaseCreature.HitPoisonChance 0.5); the shop's Lesser Cure cures Lesser 75%,
               Regular 50%, Greater 15%, Deadly and Lethal 0% (LesserCurePotion _oldLevelInfo; AOS has Greater 25%)

    rate(bot, kind) -> {"engage", "cost", "ttk", "lost", "budget", "dps_out", "dps_in", "why", ...}
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "rating.json")
SHARES = (0.07, 0.07, 0.14, 0.15, 0.22, 0.35)                       # BaseArmor.ArmorScalars = the hit-location chances (BaseWeapon.AbsorbDamage)
VA_SHARE = 0.14 * 0.07 + 0.14 * 0.14 + 0.15 * 0.15 + 0.22 * 0.22 + 0.35 * 0.35     # a creature's VirtualArmor scalar by body part, weighted
FISTS = {"min": 1, "max": 8, "speed": 30, "skill": "Wrestling"}     # Fists.cs: OldMinDamage 1, OldMaxDamage 8, OldSpeed 30
POISON = {"Lesser": (4, 26, 2.5, 3.0), "Regular": (5, 26, 3.125, 3.0), "Greater": (6, 26, 6.25, 3.0), "Deadly": (7, 26, 12.5, 4.0), "Lethal": (9, 26, 25.0, 5.0)}
CURE = {"Lesser": 0.75, "Regular": 0.5, "Greater": 0.15, "Deadly": 0.0, "Lethal": 0.0}     # LesserCurePotion pre-AOS (_oldLevelInfo; 0.25 is AOS)
POISON_TICKS = 10
POISON_CHANCE = 0.5          # BaseCreature.HitPoisonChance: a landed blow of a poisoner poisons half the time (OnGaveMeleeAttack)
DEFAULTS = {
    "engage_max_cost": 0.5,       # predicted hit points lost / hit points now, at or under which the bot engages (the old assess rule's 0.5 x hp)
    "max_ttk_s": 90.0,            # a fight longer than this is no fight to start
    "scale": {"bot_dps": 1.0, "monster_melee": 1.0, "monster_spells": 1.0, "poison": 1.0, "armor": 1.0},
    "potions": {"count": True, "heal_avg": 13.0, "every_s": 10.0},   # HealPotion 6-20 pre-AOS, one every 10 s (BaseHealPotion's shared delay)
    "kinds": {},                  # per kind: {"lost": multiplier on predicted hit points lost} (from rating_check.py's calibration)
}
_cfg = {"t": None, "mtime": None, "data": None}
_tables = {}


def config():
    """rating.json merged over DEFAULTS, re-read when it changes."""
    try:
        mt = os.path.getmtime(CONFIG)
    except OSError:
        mt = None
    if _cfg["data"] is None or mt != _cfg["mtime"]:
        data = json.loads(json.dumps(DEFAULTS))
        if mt is not None:
            try:
                over = json.load(open(CONFIG, encoding="utf-8"))
                for k, v in over.items():
                    if isinstance(v, dict) and isinstance(data.get(k), dict):
                        data[k].update(v)
                    else:
                        data[k] = v
            except (OSError, ValueError):
                pass
        _cfg.update(data=data, mtime=mt)
    return _cfg["data"]


def _table(name):
    if name not in _tables:
        try:
            _tables[name] = json.load(open(os.path.join(HERE, name), encoding="utf-8"))
        except (OSError, ValueError):
            _tables[name] = {}
    return _tables[name]


def _mid(r, default=0.0):
    if not r:
        return default
    return (float(r[0]) + float(r[-1])) / 2.0


def creature(kind):
    return (_table("creature_stats.json") or {}).get(kind)


def creature_hits(entry):
    """Its hit points as the engine gives them: SetHits under 1000 x 100 / 60 (pre-AOS); one whose hit points follow its Str (no SetHits) as they are."""
    h = _mid(entry.get("hits"))
    s = _mid(entry.get("str"))
    if entry.get("hits") and not (entry.get("str") and abs(h - s) < 0.5) and h < 1000:
        return h * 100.0 / 60.0
    return h


def weapon_of(state):
    """The weapon in the bot's hands (state "equipped", OneHanded or TwoHanded), from weapon_table.json; Fists when none is known."""
    table = (_table("weapon_table.json") or {}).get("weapons") or {}
    for e in state.get("equipped") or []:
        if e.get("layer") in ("OneHanded", "TwoHanded"):
            key = "".join(ch for ch in (e.get("name") or "").lower() if ch.isalpha())
            for k in (key, key[1:] if key.startswith("a") else key):
                if k in table:
                    return dict(table[k], key=k)
    return dict(FISTS, key="fists")


def hit_chance(atk, dfn, player):
    c = (max(0.1, atk + 50.0)) / (2.0 * max(0.1, dfn + 50.0))
    if player:
        c *= 1.0 + 0.66 * max(0.0, 1.0 - atk / 100.0)                   # noviceCombat.hitLiftStrength 0.66 (shard-rules.json)
    return min(1.0, c)


def swing_s(stam, speed, player):
    if player:
        stam = max(stam, 60.0)                                           # noviceCombat.staminaFloor 60
    return 15000.0 / ((stam + 100.0) * max(1.0, speed))


def scaled(base, tactics, strength, anatomy, player, extra=0.0):
    if player:
        tactics = max(tactics, 30.0)                                      # noviceCombat.tacticsFloor 30
    return base * (1.0 + (tactics - 50.0) / 100.0) * (1.0 + strength / 500.0 + anatomy / 500.0 + extra)


def absorbed_hit(dmg_lo, dmg_hi, ar_lo, ar_hi, steps=12):
    """E[max(1, d - a)] for d uniform in [dmg_lo, dmg_hi] and a uniform in [ar_lo, ar_hi] (a small grid; the engine truncates to integers)."""
    tot = 0.0
    for i in range(steps):
        d = dmg_lo + (dmg_hi - dmg_lo) * (i + 0.5) / steps
        for j in range(steps):
            a = ar_lo + (ar_hi - ar_lo) * (j + 0.5) / steps
            tot += max(1.0, d - a)
    return tot / (steps * steps)


class NS_:
    def __init__(self, d):
        self.name = (d or {}).get("name")


def bot_numbers(bot):
    st = bot.c.state or {}
    sk = getattr(bot, "skill_values", {}) or {}
    w = weapon_of(st)
    return {"str": float(st.get("str") or 50), "dex": float(st.get("dex") or 50), "stam": float(st.get("stamina") or st.get("dex") or 50),
            "hp": float(getattr(bot.c, "hp", None) or st.get("hits") or 50), "max_hp": float(st.get("maxHits") or 50),
            "ar": float(st.get("physicalResistance") or 0), "weapon": w, "skill": float(sk.get(w["skill"], 0.0) or 0.0),
            "tactics": float(sk.get("Tactics", 0.0) or 0.0), "anatomy": float(sk.get("Anatomy", 0.0) or 0.0),
            "lumber": float(sk.get("Lumberjacking", 0.0) or 0.0), "resist": float(sk.get("Resisting Spells", 0.0) or 0.0),
            "magery": float(sk.get("Magery", 0.0) or 0.0), "evalint": float(sk.get("Evaluating Intelligence", 0.0) or 0.0),
            "meditation": float(sk.get("Meditation", 0.0) or 0.0), "int": float(st.get("int") or 50), "mana": float(st.get("mana") or st.get("int") or 50),
            "book": any("spellbook" in (i.name or "").lower() for i in list(getattr(bot.c, "backpack", None) or []) + [NS_(e) for e in st.get("equipped") or []]),
            "heals": sum((i.amount or 1) for i in (getattr(bot.c, "backpack", None) or []) if "yellow" in (i.name or "").lower() or "heal potion" in (i.name or "").lower()),
            "cures": sum((i.amount or 1) for i in (getattr(bot.c, "backpack", None) or []) if "orange" in (i.name or "").lower() or "cure potion" in (i.name or "").lower()),
            "kite": bool(_call(bot, "kite_on", False)), "run_s": float(_call(bot, "run_s", 0.2) or 0.2),
            "casts": _call(bot, "casts_now", None)}


def _call(bot, name, default):
    """bot.name() when the bot has it, else default (a test stub, a bot class without it)."""
    try:
        fn = getattr(bot, name, None)
        return fn() if callable(fn) else default
    except Exception:
        return default


CAST_RECOVERY = 0.75             # s between spells pre-AOS (Spell.NextSpellDelay; GetCastRecovery's AOS formula is off)
MANA = (4, 6, 9, 11, 14, 20, 40, 50)                                     # MagerySpell._manaTable by circle
BOT_SPELLS = (("magic arrow", 4, 7, 0, 0.75), ("harm", 1, 15, 1, 0.75), ("fireball", 10, 16, 2, 0.75), ("lightning", 12, 20, 3, 0.75),
              ("energy bolt", 24, 41, 5, 0.75), ("explosion", 23, 44, 5, 0.75), ("flamestrike", 27, 48, 6, 0.6))      # casterpass.SPELLS' damage spells


def cast_delay(c):
    """Seconds a cast holds the caster still, c the 0-based circle: 0.5 + 0.25 x circle before AOS (MagerySpell.GetCastDelay; Spell.BlocksMovement while
    casting). The recovery after it (CAST_RECOVERY) does not hold it: it may run."""
    return 0.5 + 0.25 * c


def kite_factor(me, kind, e, t_cast):
    """A caster that kites (me["kite"]): casts, then runs while it recovers and as long again as it must, so that a melee monster slower than its run
    never reaches it. (factor, holds): the kill takes factor x as long (the extra running), and holds is True when the monster cannot close at all.
    A monster that steps no slower than the run (a lizardman against a caster on foot) cannot be kited: (1.0, False). One that never moves: (1.0, True).
    Per cycle the monster covers (cast + recovery + x) / its step, the caster (recovery + x) / its run: x = (cast/step + rec/step - rec/run) / (1/run - 1/step)."""
    if not me.get("kite"):
        return 1.0, False
    try:
        import casterpass
        step = casterpass.move_s(kind, e)
    except Exception:
        return 1.0, False
    if step is None:
        return 1.0, True
    run = float(me.get("run_s") or 0.2)
    if step <= run:
        return 1.0, False
    c = max(0.0, t_cast - CAST_RECOVERY)
    r = CAST_RECOVERY
    x = max(0.0, (c / step + r / step - r / run) / (1.0 / run - 1.0 / step))
    return (c + r + x) / (c + r), True


def kite_leak(sc, kind, e):
    """The share of a kited monster's blows that still land, by its chase step (casterpass.move_s): rating.json kite_leak_by_step, measured per speed class
    from the casters' kite_fight events; kite_leak for a step not measured."""
    by = sc.get("kite_leak_by_step") or {}
    try:
        import casterpass
        step = casterpass.move_s(kind, e)
    except Exception:
        step = None
    if step is not None:
        for k, v in by.items():
            if abs(float(k) - float(step)) < 1e-6:
                return float(v)
    return float(sc.get("kite_leak", 0.0))


def mana_regen(me):
    """Mana a second pre-AOS (RegenRates.Mobile_ManaRegenRate): one point every 7 - 239p/2400 + 19p^2/48000 s, p = (Int + Meditation) / 2; armour adds to it."""
    p = (me.get("int", 50.0) + me.get("meditation", 0.0)) * 0.5
    sec = 7.0 if p <= 0 else (7.0 - 239.0 * p / 2400.0 + 19.0 * p * p / 48000.0) if p <= 100 else 1.0 if p < 120 else 0.75
    return 1.0 / max(0.25, sec)


def spell_plan(me, e, hits):
    """(seconds to kill, the spell, damage a cast, seconds a cast) for the bot's best damage spell against this creature, mana included: full speed while
    the pool lasts, then as fast as its regeneration pays for it. None when it casts nothing that hurts. A cast: (3 + circle) x 0.25 s plus CAST_RECOVERY;
    it fizzles unless (Magery - 10 x circle) / 40 succeeds; damage x casterpass.scalar(EvalInt, Magery, its Resist), x the resisted factor at
    casterpass.resist_chance."""
    if me.get("magery", 0.0) < 20 or not me.get("book") or me.get("casts") == 0:
        return None                                                      # casts 0: no reagents for any attack spell (BotSorcBR after a death, 04:10)
    try:
        import casterpass
    except Exception:
        return None
    rs = _mid(e.get("resist"))
    sc = max(0.0, casterpass.scalar(me.get("evalint", 0.0), me["magery"], rs))
    regen = mana_regen(me)
    pool = max(0.0, me.get("mana", 0.0))
    best = None
    for name, lo, hi, c, rf in BOT_SPELLS:
        ok = casterpass.success(me["magery"], c)
        if ok <= 0:
            continue
        pr = casterpass.resist_chance(rs, me["magery"], c)
        dmg = ok * (lo + hi) / 2.0 * sc * (1 - pr + pr * rf)
        if dmg <= 0:
            continue
        t_cast = cast_delay(c) + CAST_RECOVERY
        cost = MANA[c]
        dps, need = dmg / t_cast, cost / t_cast
        if need <= regen:
            ttk = hits / dps
        else:
            t1 = pool / (need - regen)                           # until the pool is gone
            if dps * t1 >= hits:
                ttk = hits / dps
            else:
                ttk = t1 + (hits - dps * t1) / (regen / cost * dmg)
        if best is None or ttk < best[0]:
            best = (ttk, name, dmg, t_cast, cost * hits / dmg)
    return best


def rate(bot, kind, numbers=None):
    """The fight with one monster of this kind, rated (see the module note); None for a kind the creature table does not know."""
    e = creature(kind)
    if not e:
        return None
    cfg = config()
    sc = cfg.get("scale") or {}
    me = numbers or bot_numbers(bot)
    w = me["weapon"]
    # the bot's blows on it
    m_def = _mid(e.get("wrestling"))
    p_out = hit_chance(me["skill"], m_def, True)
    axe = "axe" in w.get("key", "")
    lo = scaled(float(w["min"]), me["tactics"], me["str"], me["anatomy"], True, (me["lumber"] / 500.0) if axe else 0.0)
    hi = scaled(float(w["max"]), me["tactics"], me["str"], me["anatomy"], True, (me["lumber"] / 500.0) if axe else 0.0)
    va = float(e.get("armor") or 0) * VA_SHARE
    per_hit_out = absorbed_hit(lo, hi, va / 2.0, va)
    dps_out = p_out * per_hit_out / swing_s(me["stam"], float(w["speed"]), True) * float(sc.get("bot_dps", 1.0))
    hits = creature_hits(e)
    ttk = hits / dps_out if dps_out > 0 else float("inf")
    how = f"{w.get('key', 'fists')}"
    plan = spell_plan(me, e, hits)
    cdps = max(1e-9, float(sc.get("caster_dps", sc.get("bot_dps", 1.0))))     # spells have their own measured scale: no misses and no chase (rating.json)
    kite_holds = False
    mana_kill = None
    if plan and plan[0] / cdps < ttk:
        mana_kill = plan[4]                                             # the mana one kill takes (rate_pack shares the pool)
        ttk = plan[0] / cdps                                            # a mage: its best spell, mana included (spell_plan)
        kf, kite_holds = kite_factor(me, kind, e, plan[3])
        ttk *= kf                                                       # the extra running of a kite (kite_factor)
        dps_out = hits / ttk
        how = f"{plan[1]} ({plan[2]:.1f} a cast every {plan[3]:.2f}s" + (f", kiting x{kf:.2f})" if kite_holds else ")")
    # its blows on the bot
    p_in = hit_chance(_mid(e.get("wrestling")), me["skill"], False)
    dmg = e.get("damage") or [0, 0]
    m_tac, m_str = _mid(e.get("tactics")), _mid(e.get("str"))
    lo_in = scaled(float(dmg[0]), m_tac, m_str, 0.0, False) / 2.0                  # halved: a player is hit
    hi_in = scaled(float(dmg[-1]), m_tac, m_str, 0.0, False) / 2.0
    ar = me["ar"] * float(sc.get("armor", 1.0))
    per_hit_in = absorbed_hit(lo_in, hi_in, ar / 2.0, ar)
    melee_in = p_in * per_hit_in / swing_s(_mid(e.get("dex"), 50.0), 30.0, False) * float(sc.get("monster_melee", 1.0))
    if kite_holds:
        melee_in *= kite_leak(sc, kind, e)                              # kited: its blows land only when the kite fails (a wall, a corner): measured, rating.json
    spells_in = 0.0
    if e.get("casts"):
        try:
            import casterpass
            dmg_c, _top = casterpass.per_cast(e, me["resist"], (me["str"], me["dex"], 50.0))
            spells_in = dmg_c / casterpass.interval(e) * float(sc.get("monster_spells", 1.0))
        except Exception:
            spells_in = 0.0
    dps_in = melee_in + spells_in
    lost = dps_in * ttk if ttk != float("inf") else float("inf")
    # poison: what its ticks take when the bot's cures do not clear it
    pz = e.get("poison")
    if pz in POISON and lost != float("inf"):
        mn, mx, pct, every = POISON[pz]
        tick = max(mn, min(mx, 1 + me["hp"] * pct / 100.0))
        fail = 1.0 - (CURE.get(pz, 0.0) if me["cures"] > 0 else 0.0)
        swings = ttk / swing_s(_mid(e.get("dex"), 50.0), 30.0, False)
        poisoned = 1.0 - (1.0 - POISON_CHANCE * p_in) ** max(0.0, swings)       # a landed blow poisons with HitPoisonChance 0.5 (BaseCreature)
        lost += tick * POISON_TICKS * fail * poisoned * float(sc.get("poison", 1.0))
    kmul = float(((cfg.get("kinds") or {}).get(kind) or {}).get("lost", 1.0))
    lost *= kmul
    budget = me["hp"]
    pot = cfg.get("potions") or {}
    if pot.get("count") and me["heals"] > 0 and ttk != float("inf"):
        budget += min(me["heals"], ttk / float(pot.get("every_s", 10.0))) * float(pot.get("heal_avg", 13.0))
    cost = lost / budget if budget > 0 else float("inf")
    engage = cost <= float(cfg.get("engage_max_cost", 0.5)) and ttk <= float(cfg.get("max_ttk_s", 90.0))
    why = (f"rating {cost:.2f} (lose ~{lost:.0f} of {budget:.0f}; {ttk:.0f}s to kill with {how}; "
           f"it hits {p_in:.0%} x {per_hit_in:.1f}" + (f" + spells {spells_in:.1f}/s" if spells_in else "") + (f" + {pz} poison" if pz in POISON else "") + ")")
    return {"engage": engage, "cost": round(cost, 3), "ttk": round(ttk, 1), "lost": round(lost, 1), "budget": round(budget, 1), "dps_out": round(dps_out, 2),
            "dps_in": round(dps_in, 2), "p_out": round(p_out, 3), "p_in": round(p_in, 3), "hits": round(hits, 1), "how": how, "why": why,
            "mana": round(mana_kill, 1) if mana_kill is not None else None}


def rate_pack(bot, kinds, numbers=None):
    """The fight with several monsters at once (the target and every attack-on-sight one that will join it), rated: the bot kills them one at a time,
    quickest first, and each one's blows and spells keep coming until it dies; poison counts once per poisoner. None when no kind is known. A spectre,
    a skeletal knight and a bone mage rate 0.19, 0.06 and 0.22 one by one for a fencer at 100 skill in platemail, and together they killed BotFencerBR
    and BotMaceCR at the Skara Brae graveyard (2026-11-04 16:35, 16:56): one at a time is the wrong question."""
    me = numbers or bot_numbers(bot)
    one = [(k, rate(bot, k, me)) for k in kinds]
    one = [(k, r) for k, r in one if r]
    if not one:
        return None
    cfg = config()
    one.sort(key=lambda kr: kr[1]["ttk"])
    t = lost = 0.0
    full = pool = max(0.0, float(me.get("mana", 0.0) or 0.0))
    regen = mana_regen(me)
    for k, r in one:
        need = float(r.get("mana") or 0.0)
        wait = 0.0
        if need > 0:
            # one pool for the whole pack: each kill was rated from a full pool, so the mana the earlier kills spent is waited for again at the regeneration
            # rate (beyond what that kill's own rating already waited). A pack of 10 lizardmen rated 190 s and 0.42 "fight" for BotMageBR with 90 mana and
            # 44 a kill, and boxed it in (Despise, 2026-11-09 04:17)
            wait = max(0.0, (max(0.0, need - pool) - max(0.0, need - full)) / max(regen, 1e-6))
            pool = min(full, max(0.0, pool + regen * (r["ttk"] + wait) - need))
        t += r["ttk"] + wait
        melee_and_spells = r["dps_in"]
        lost += melee_and_spells * t                                   # it hits until it dies, at the sum of the kill times so far
    pois = sum(max(0.0, r["lost"] - r["dps_in"] * r["ttk"]) for _k, r in one)       # each poisoner's poison, once (rate's own term)
    lost += pois
    budget = me["hp"]
    pot = cfg.get("potions") or {}
    if pot.get("count") and me["heals"] > 0:
        budget += min(me["heals"], t / float(pot.get("every_s", 10.0))) * float(pot.get("heal_avg", 13.0))
    cost = lost / budget if budget > 0 else float("inf")
    engage = cost <= float(cfg.get("engage_max_cost", 0.5)) and t <= float(cfg.get("max_ttk_s", 90.0)) * max(1, len(one))
    return {"engage": engage, "cost": round(cost, 3), "ttk": round(t, 1), "lost": round(lost, 1), "budget": round(budget, 1), "n": len(one),
            "why": f"pack of {len(one)} ({', '.join(k for k, _ in one)}): rating {cost:.2f} (lose ~{lost:.0f} of {budget:.0f} in {t:.0f}s)"}
