"""The travel planner (docs/Bot-Farm-Capability-Plan-2026-10-20.md, item 4b; signed off 2026-10-20): every task's travel step asks plan_journey() for
the cheapest safe way to its destination and gets a JOURNEY, a list of legs of four kinds, each costed in minutes plus a danger charge:

    walk      the routed waypoints (walkroute.plan with the far-walk penalty: cells where bots died, the strong spawners' circles)
    gate      walk to the nearest public moongate, step in, answer the gate's list with the town nearest the destination, walk on from that gate;
              only when it saves GATE_SAVE tiles or more
    recall    a rune this bot marked near the destination (runes.py's rune_hop criteria and rune_cast), when its Magery can cast it
    camp      a party member's blue travel fire near the destination ([CampTravel: the channel, two kindling, a 30 min cooldown); the leg is chosen
              only when a fire is on the list, which the shared tour (item 5) brings
    tele      item 5: a destination on another side of the map (a dungeon level, the surface from below) is reached through the teleporter chain
              tele.py's tele_route finds (the gazetteer's pairs and the pairs bots have seen), each hop a leg of its own between the walk legs on
              either side; the hop itself is tele_hop (walk onto the entry, check the jump), which the simulator answers by moving the bot

A leg that fails (the gate gives no list or the bot did not jump, the recall fizzles or lands blocked, no path from a gate) blocks that leg kind
for BLOCK_S and the journey is planned again from where the bot stands; the journey lives in the task's state, so a restarted brain resumes it.
Events: journey {dest, kind, minutes, walk_minutes, legs}, leg_failed {kind, why}.
"""
from __future__ import annotations

import time

GATE_SAVE = 150                 # tiles a gate or a recall must save over walking
GATE_S = 12.0                   # seconds to step in and answer the list
RECALL_S = 15.0
CAMP_S = 8.0
TELE_S = 20.0                   # seconds a teleporter hop costs beyond the walk to its entry
TELE_LAND = 40                  # tiles: on the far side and this near the landing, the hop is done
DANGER_MIN = 2.0                # minutes charged for every waypoint in a cell the memory calls dangerous
BLOCK_S = 600.0
WALK_RATE = 55.0
ROUTE_FACTOR = 1.3
HOP_NEAR, HOP_SAVE = 90, 120    # runes.py's rune_hop: a landing this near the destination, saving this much


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def rate(bot):
    try:
        return min(120.0, max(30.0, float(bot.facts.get("walk_rate") or WALK_RATE)))
    except Exception:
        return WALK_RATE


def blocked(bot, kind):
    return time.time() < (bot.facts.get("travel_blocked") or {}).get(kind, 0)


def block(bot, kind, why):
    bot.facts.setdefault("travel_blocked", {})[kind] = time.time() + BLOCK_S
    try:
        bot.ev("leg_failed", leg=kind, why=why)
        bot.log(f"travel: the {kind} leg failed ({why}): not for {int(BLOCK_S / 60)} min")
    except Exception:
        pass


def side_of(x, y):
    try:
        import gazetteer as gz
        return gz.side(int(x), int(y))
    except Exception:
        return "surface"


def walk_cost(bot, frm, to):
    """(minutes, waypoints) of the routed walk from frm to to with the danger charge, or (None, None) with no land route."""
    frm, to = (int(frm[0]), int(frm[1])), (int(to[0]), int(to[1]))
    straight = cheb(frm, to)
    if straight <= 2:
        return 0.0, [to]
    if side_of(*frm) != side_of(*to):
        return None, None                                         # another side of the map: no walk joins them (the tele leg does)
    dungeon = frm[0] >= 5120
    try:
        import walkroute
        try:
            pen = bot.far_penalty()
        except Exception:
            pen = None
        r = walkroute.get().plan(frm, to, pen, step=40)
    except Exception:
        r = None
    if r is None:
        if straight > 120 or dungeon:
            return None, None                                     # on the dungeon side the grid is the judge: no route means the stairs (inner_hops), not a straight walk
        return straight * ROUTE_FACTOR / rate(bot), [to]
    wps = [tuple(int(v) for v in p[:2]) for p in r["waypoints"]]
    if not wps or cheb(wps[-1], to) > 0:
        wps.append(to)                                            # the last waypoint is the destination itself: an errand stands at the counter
    danger = 0
    try:
        from memory import cell_of
        danger = sum(1 for p in wps if bot.mem.dangerous_cell(cell_of(p[0], p[1])))
    except Exception:
        pass
    return float(r["steps"]) / rate(bot) + DANGER_MIN * danger, wps


def gates(bot):
    """[(name, (x, y))] the public moongates the gazetteer knows, on this side."""
    try:
        import gazetteer as gz
        g = gz.load() if hasattr(gz, "load") else gz
        out = []
        for p in g.near("moongate", int(bot.c.x), int(bot.c.y), n=12, same_side=True):
            out.append((p.get("name") or "gate", (int(p["x"]), int(p["y"]))))
        return out
    except Exception:
        return []


def plan_cross(bot, here, dest):
    """A journey to another side of the map: the teleporter chain (tele_route) as tele legs, each reached by a same-side journey of its own."""
    if blocked(bot, "tele"):
        return None
    try:
        hops = bot.tele_route(here, side_of(*dest), dest)
    except Exception:
        hops = None
    if not hops:
        return None
    legs, minutes, at = [], 0.0, here
    for t in hops:
        sub = plan_journey(bot, (t["src"][0], t["src"][1]), here=at)
        if sub is None:
            return None
        legs += sub["legs"]
        minutes += float(sub["minutes"])
        legs.append({"kind": "tele", "t": {k: t[k] for k in ("src", "dst", "src_side", "dst_side", "kind") if k in t}, "land": [int(t["dst"][0]), int(t["dst"][1])], "to_side": t["dst_side"]})
        minutes += TELE_S / 60.0
        at = (int(t["dst"][0]), int(t["dst"][1]))
    sub = plan_journey(bot, dest, here=at)
    if sub is None:
        return None
    legs += sub["legs"]
    minutes += float(sub["minutes"])
    return {"kind": "tele", "minutes": round(minutes, 1), "walk_minutes": None, "legs": legs, "dest": list(dest), "options": {"tele": round(minutes, 1)}, "hops": len(hops)}


def plan_inner(bot, here, dest, hops):
    """Inside one dungeon: the inner teleporters (stairs) between the walkable components, each a tele leg between walk legs."""
    legs, minutes, at = [], 0.0, here
    for t in hops:
        m, w = walk_cost(bot, at, (t["src"][0], t["src"][1]))
        if m is None:
            return None
        legs.append({"kind": "walk", "to": [int(t["src"][0]), int(t["src"][1])], "wps": [list(p) for p in w]})
        legs.append({"kind": "tele", "t": {k: t[k] for k in ("src", "dst", "src_side", "dst_side", "kind") if k in t}, "land": [int(t["dst"][0]), int(t["dst"][1])], "to_side": t["dst_side"]})
        minutes += m + TELE_S / 60.0
        at = (int(t["dst"][0]), int(t["dst"][1]))
    m, w = walk_cost(bot, at, dest)
    if m is None:
        return None
    legs.append({"kind": "walk", "to": list(dest), "wps": [list(p) for p in w]})
    minutes += m
    return {"kind": "tele", "minutes": round(minutes, 1), "walk_minutes": None, "legs": legs, "dest": list(dest), "options": {"tele": round(minutes, 1)}, "hops": len(hops)}


def plan_journey(bot, dest, here=None):
    """The cheapest journey to dest: {"kind", "minutes", "walk_minutes", "legs": [...]} or None with no way at all. `here` plans from another point (the landing
    of a teleporter, for the legs after it)."""
    here = (int(here[0]), int(here[1])) if here is not None else (int(bot.c.x), int(bot.c.y))
    dest = (int(dest[0]), int(dest[1]))
    if side_of(*here) != side_of(*dest):
        return plan_cross(bot, here, dest)
    if here[0] >= 5120 and not blocked(bot, "tele"):
        try:
            import spots
            hops = spots.inner_hops(side_of(*here), here, dest)
        except Exception:
            hops = None
        if hops:
            return plan_inner(bot, here, dest, hops)
    options = []
    wmin, wps = walk_cost(bot, here, dest)
    if wmin is not None:
        options.append({"kind": "walk", "minutes": wmin, "legs": [{"kind": "walk", "to": list(dest), "wps": [list(p) for p in wps]}]})
    straight = cheb(here, dest)
    if straight >= GATE_SAVE and not blocked(bot, "gate"):
        gs = gates(bot)
        if gs:
            g1 = min(gs, key=lambda g: cheb(here, g[1]))
            g2 = min(gs, key=lambda g: cheb(g[1], dest))
            if g1[1] != g2[1] and straight - (cheb(here, g1[1]) + cheb(g2[1], dest)) >= GATE_SAVE:
                m1, w1 = walk_cost(bot, here, g1[1])
                m2, w2 = walk_cost(bot, g2[1], dest)
                if m1 is not None and m2 is not None:
                    options.append({"kind": "gate", "minutes": m1 + GATE_S / 60.0 + m2,
                                    "legs": [{"kind": "walk", "to": list(g1[1]), "wps": [list(p) for p in w1]}, {"kind": "gate", "at": list(g1[1]), "to_name": g2[0], "land": list(g2[1])},
                                             {"kind": "walk", "to": list(dest), "wps": [list(p) for p in w2]}]})
    if not blocked(bot, "recall"):
        try:
            runes = bot.rune_known() if bot.rune_on() and bot.rune_able() else {}
        except Exception:
            runes = {}
        best = None
        for s, r in runes.items():
            land = (int(r["x"]), int(r["y"]))
            if cheb(land, dest) <= HOP_NEAR and straight - cheb(land, dest) >= HOP_SAVE and (best is None or cheb(land, dest) < cheb(best[1], dest)):
                best = (s, land, r.get("label", "rune"))
        if best:
            m2, w2 = walk_cost(bot, best[1], dest)
            if m2 is not None:
                options.append({"kind": "recall", "minutes": RECALL_S / 60.0 + m2,
                                "legs": [{"kind": "recall", "rune": best[0], "land": list(best[1]), "label": best[2]}, {"kind": "walk", "to": list(dest), "wps": [list(p) for p in w2]}]})
    if not blocked(bot, "camp"):
        try:
            fires = bot.camp_fires() if hasattr(bot, "camp_fires") else []
        except Exception:
            fires = []
        near = [f for f in fires if cheb((f["x"], f["y"]), dest) <= HOP_NEAR and straight - cheb((f["x"], f["y"]), dest) >= HOP_SAVE]
        if near and time.time() - bot.facts.get("camp_travel_at", 0) > 1800:
            f = min(near, key=lambda f: cheb((f["x"], f["y"]), dest))
            m2, w2 = walk_cost(bot, (f["x"], f["y"]), dest)
            if m2 is not None:
                options.append({"kind": "camp", "minutes": CAMP_S / 60.0 + m2,
                                "legs": [{"kind": "camp", "fire": f, "land": [f["x"], f["y"]]}, {"kind": "walk", "to": list(dest), "wps": [list(p) for p in w2]}]})
    if not options:
        return None
    best = min(options, key=lambda o: o["minutes"])
    best["walk_minutes"] = round(wmin, 1) if wmin is not None else None
    best["minutes"] = round(best["minutes"], 1)
    best["dest"] = list(dest)
    best["options"] = {o["kind"]: round(o["minutes"], 1) for o in options}
    return best


# ---- the non-walk legs, one tick at a time -------------------------------------------------------------------------------------------------------------

def gate_choice(lines, want):
    """(serial, ("radio" | "button", index)) for the town `want` in the moongate's window among the open windows Navrey's "gumps" printed, or
    (serial, None) when the gate's window lacks it, or (None, None) with no gate window. Navrey prints a control on one line and its label on the
    next ("[radio 1]" then "Britain"), and other windows may be open too: a gate's list once went unread because "Between Worlds" was listed last
    and its serial was taken, with a "[radio" and the name looked for on one line (BotFisherAR, 2026-10-31)."""
    blocks, cur = [], None
    for line in lines:
        if line.startswith("[GUMP] local") and "server" in line:
            cur = {"serial": line.split("server")[1].split()[0], "rows": []}
            blocks.append(cur)
        elif cur is not None:
            row = line.strip()
            if row.startswith("[GUMP]"):
                row = row[6:].strip()                         # (a row printed with the window's tag in front)
            cur["rows"].append(row)
    gate = next((b for b in blocks if any("destination" in r.lower() for r in b["rows"]) or any(r.lower().startswith("[radio") for r in b["rows"])), None)
    if gate is None:
        return None, None
    want = want.lower().strip()
    last = None
    for r in gate["rows"]:
        low = r.lower()
        if low.startswith("[radio") or low.startswith("[button"):
            try:
                last = ("radio" if low.startswith("[radio") else "button", int(low.split()[1].rstrip("]")))
            except (ValueError, IndexError):
                last = None
            rest = low.split("]", 1)[1].strip() if "]" in low else ""
            if want and rest == want:
                return gate["serial"], last                   # (a control and its label on one line, as older builds printed it)
        elif want and low == want and last is not None:
            return gate["serial"], last
    return gate["serial"], None


def gate_step(bot, leg, st):
    """At the gate: step in, answer the list with the destination town, check the jump. Returns "done", "running" or a failure reason."""
    here = (int(bot.c.x), int(bot.c.y))
    at = tuple(leg["at"])
    if cheb(here, tuple(leg["land"])) <= 12:
        if st.get("gate_sent") and not st.get("gate_done"):
            st["gate_done"] = True
            bot.ev("gate_used", to=leg.get("to_name"), land=leg["land"])
            bot.log(f"travel: through the moongate to {leg.get('to_name')} ({here[0]},{here[1]})")
        return "done"
    if cheb(here, at) > 1:
        if not st.get("gate_goto") or time.time() - st["gate_goto"] > 8:
            st["gate_goto"] = time.time()
            try:
                bot.c.gotoexact(at[0], at[1])
            except Exception:
                bot.c.goto(at[0], at[1])
        if st.get("gate_t0") and time.time() - st["gate_t0"] > 60:
            return "no path onto the gate"
        st.setdefault("gate_t0", time.time())
        return "running"
    lines = []
    try:
        lines = bot.c.call("gumps", timeout=8)
    except Exception:
        lines = []
    serial, idx = gate_choice(lines, leg.get("to_name") or "")
    if serial is None:
        st["gate_waits"] = st.get("gate_waits", 0) + 1
        if st["gate_waits"] > 6:
            return "the gate gave no list"
        time.sleep(1.0)
        return "running"
    if idx is not None and idx[0] == "radio":
        st["gate_radio"] = True
    idx = idx[1] if idx is not None else None
    before = here
    try:
        if idx is not None and st.get("gate_radio"):
            bot.c.call(f"gumpresponse 1 {idx} gump:{serial}", timeout=8)          # Navrey: the OK button with the town's radio id selected
            st["gate_sent"] = True
        elif idx is not None:
            bot.c.call(f"gumpresponse {idx} gump:{serial}", timeout=8)
        else:
            bot.c.call(f"gumpresponse 0 gump:{serial}", timeout=8)
            return f"the list has no {leg.get('to_name')}"
    except Exception as e:
        return f"gumpresponse: {type(e).__name__}"
    time.sleep(2.0)
    after = (int(bot.c.x), int(bot.c.y))
    if cheb(before, after) > 20:
        try:
            bot.tele_jumped(before, after, how="moongate")
        except Exception:
            pass
        bot.ev("gate_used", to=leg.get("to_name"), land=leg["land"])
        bot.log(f"travel: through the moongate to {leg.get('to_name')} ({after[0]},{after[1]})")
        return "done"
    st["gate_waits"] = st.get("gate_waits", 0) + 1
    return "running" if st["gate_waits"] <= 6 else "did not jump"


def recall_step(bot, leg, st):
    here = (int(bot.c.x), int(bot.c.y))
    if cheb(here, tuple(leg["land"])) <= 20:
        return "done"
    way = bot.rune_way("recall")
    if way is None:
        return "no way to cast"
    ok, why = bot.rune_cast("recall", way, leg["rune"])
    if ok:
        r = bot.rune_known().get(leg["rune"])
        if r is not None:
            r["used"] = r.get("used", 0) + 1
            r["last"] = time.time()
        bot.ev("rune_recall", label=leg.get("label"), to=leg["land"], saved=None, way=way[0], chance=round(way[1], 2), journey=True)
        return "done"
    return why or "fizzled"


def tele_step(bot, leg, st):
    """At the teleporter's entry (the walk leg before brought the bot there): tele_hop onto it, check the side changed. Returns "done" or a failure reason."""
    here = (int(bot.c.x), int(bot.c.y))
    if leg.get("to_side") not in (None, "surface"):
        try:
            import task_core
            if not task_core.rung_ready(bot):            # M1: at the gate the stock or the health is gone: turn back and restock, do not go in
                bot.ev("rung_turned_back", kit=task_core.kit(bot)[1], hp=round(bot.hp_pct()))
                return f"not ready for the dungeon ({task_core.kit(bot)[1]}, {round(bot.hp_pct())}% health)"
        except Exception:
            pass
    src = tuple(int(v) for v in leg["t"]["src"][:2])
    near = min(TELE_LAND, max(1, cheb(src, tuple(leg["land"])) // 2))      # a stair teleporter may land a few tiles from its entry: "done" means nearer the landing than the entry
    if side_of(*here) == leg["to_side"] and cheb(here, tuple(leg["land"])) <= near:
        if not st.get("tele_done"):
            st["tele_done"] = True
            bot.ev("tele_used", to_side=leg["to_side"], land=leg["land"])
            bot.log(f"travel: through the teleporter to {leg['to_side']} ({here[0]},{here[1]})")
        return "done"
    if st.get("tele_tried"):
        return "did not jump"
    st["tele_tried"] = True
    try:
        bot.tele_allow(leg["to_side"])
    except Exception:
        pass
    try:
        ok = bot.tele_hop(leg["t"])
    except Exception as e:
        return f"tele_hop: {type(e).__name__}"
    if ok or side_of(int(bot.c.x), int(bot.c.y)) == leg["to_side"]:
        st["tele_done"] = True
        bot.ev("tele_used", to_side=leg["to_side"], land=leg["land"])
        bot.log(f"travel: through the teleporter to {leg['to_side']} ({int(bot.c.x)},{int(bot.c.y)})")
        return "done"
    return "did not jump"


def camp_step(bot, leg, st):
    here = (int(bot.c.x), int(bot.c.y))
    if cheb(here, tuple(leg["land"])) <= 20:
        return "done"
    fn = getattr(bot, "camp_travel_to", None)
    if fn is None:
        return "no camp travel"
    try:
        ok = fn(leg["fire"])
    except Exception as e:
        return f"camp travel: {type(e).__name__}"
    bot.facts["camp_travel_at"] = time.time()
    return "done" if ok else "refused"


STEPS = {"gate": gate_step, "recall": recall_step, "camp": camp_step, "tele": tele_step}
