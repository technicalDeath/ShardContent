"""The simulator's own check, without a brain: a scripted FakeClient walks, fights, loots, carves, banks, shops, mines, fishes, crafts, casts, tames, dies and is
resurrected, and every step is asserted against what the brains expect (the journal wording, the command replies, the state fields).

    python selftest.py            exit 0 when every check passes
"""
from __future__ import annotations

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BOTFARM = os.path.abspath(os.path.join(HERE, ".."))
SCENARIOS = os.path.abspath(os.path.join(BOTFARM, ".."))
ROOT = os.path.abspath(os.path.join(SCENARIOS, "..", "..", ".."))
for p in (os.path.join(ROOT, "Navrey", "cli"), BOTFARM, SCENARIOS):
    if p not in sys.path:
        sys.path.insert(0, p)

from uo import Event  # noqa: E402

from sim.clock import VirtualClock  # noqa: E402
from sim.fake_client import FakeClient  # noqa: E402
from sim.world import World, cheb  # noqa: E402
from sim.world_data import WorldData  # noqa: E402

checks = []


def ok(cond, what):
    checks.append((bool(cond), what))
    print(("ok   " if cond else "FAIL ") + what)


def run_until(clock, world, seconds):
    end = clock.now + seconds
    while clock.now < end:
        world.step(0.5)
        clock.now += 0.5


def tick(clock, world):
    """A moment passes: replies reach the log, the state and the view are rebuilt."""
    world.step(0.6)
    clock.now += 0.6


def main():
    data = WorldData()
    world = World(data, seed=3, now=time.time())
    clock = VirtualClock(world.now())
    # the clock is not installed: this script drives the world by hand, and the client's waits are not used
    hero = world.add_player({"name": "SelfTest", "profession": 15, "skills": {"Swordsmanship": 80, "Tactics": 80, "Anatomy": 60, "Healing": 50, "Mining": 70, "Fishing": 70,
                                                                             "Blacksmithy": 60, "Magery": 70, "Animal Taming": 60, "Lumberjacking": 50},
                             "pos": [1470, 1620], "max_hp": 90, "max_mana": 60, "max_stam": 60, "str": 80, "dex": 60, "int": 60, "max_weight": 300,
                             "backpack": [{"name": "gold coin", "amount": 500}, {"name": "bandage", "amount": 20}, {"name": "pickaxe", "amount": 1}, {"name": "fishing pole", "amount": 1},
                                          {"name": "tongs", "amount": 1}, {"name": "iron ingot", "amount": 40}, {"name": "black pearl", "amount": 10}, {"name": "nightshade", "amount": 10}, {"name": "sulfurous ash", "amount": 10},
                                          {"name": "dagger", "amount": 1}, {"name": "hatchet", "amount": 1}],
                             "equipped": [{"name": "longsword", "layer": "OneHanded"}, {"name": "leather tunic", "layer": "Torso"}]})
    c = FakeClient(world, hero)
    ok(c.in_game and c.name == "SelfTest" and c.hp == 90 and c.gold == 500, f"state: name {c.name}, hp {c.hp}, gold {c.gold}, weight {c.weight}/{c.max_weight}")
    ok(any(i.name == "bandage" and i.amount == 20 for i in c.backpack), "backpack served through the real Client")
    ok(c.find("pickaxe") is not None and c.backpack_opened, "find() and backpack_opened")

    # ---- walking: a short walk, a long walk, a walk into the sea
    w = c.goto(1480, 1630)
    run_until(clock, world, 10)
    ok(c.nav.status == "arrived" and (c.x, c.y) == (1480, 1630), f"short walk arrived at {c.xy} in 10 s ({c.nav.status})")
    c.goto(1425, 1690)                   # the west bank
    run_until(clock, world, 60)
    ok(c.nav.status == "arrived" and max(abs(c.x - 1425), abs(c.y - 1690)) <= 1, f"walk to the bank: {c.nav.status} at {c.xy}")
    c.goto(1300, 1800)                   # the farmlands, across the river
    run_until(clock, world, 120)
    ok(c.nav.status == "arrived", f"walk across the river to the farmlands: {c.nav.status} at {c.xy}")
    c.goto(1100, 1700)                   # the sea west of Britain? (whatever it is: the planner must answer, not hang)
    run_until(clock, world, 5)
    ok(c.nav.status in ("walking", "arrived", "nopath"), f"a far walk answers ({c.nav.status})")
    c.cancel_walk()
    ok(not c.nav.active, "stop cancels the walk")

    # ---- a vendor, the bank, a shop
    c.goto(1425, 1690)
    run_until(clock, world, 120)
    banker = c.nearest(named="", notoriety="Innocent")
    ok(banker is not None and banker.is_human, f"people in view at the bank: {[m.name for m in c.mobiles(within=8, notoriety='Innocent')][:4]}")
    c.events.drain()
    c.say("bank")
    tick(clock, world)
    ev = next((e for e in c.events.poll() if e.kind == Event.CONTAINER_OPENED), None)
    ok(ev is not None and "Opened" in ev.text, f"saying bank opens the box: {ev.text if ev else None}")
    box = ev.text.split("Opened ")[1].split()[0] if ev else None
    gold = c.find("gold coin")
    c.drop(gold.serial, box, 300)
    tick(clock, world)
    ok(c.gold == 200, f"300 gold dropped into the bank box: carrying {c.gold}")
    c.say("balance")
    tick(clock, world)
    lines = [e.text for e in c.events.poll()]
    ok(any("balance is 300 gold" in l for l in lines), f"balance line: {[l for l in lines if 'balance' in l]}")
    c.say("withdraw 100")
    tick(clock, world)
    ok(c.gold == 300, f"withdraw 100: carrying {c.gold}")
    items = c.container(box)
    ok(sum(i.amount for i in items if i.name == "gold coin") == 200, f"the bank box holds {[str(i) for i in items]}")
    # the tinker: buy a pickaxe, sell the dagger
    tinker = next((v for v in world.vendors.values() if v.role == "tinker"), None)
    c.goto(tinker.x, tinker.y)
    run_until(clock, world, 120)
    c.events.drain()
    c.say(f"{tinker.name} buy")
    tick(clock, world)
    ev = [e.text for e in c.events.poll()]
    ok(any("[SHOP] vendor" in l for l in ev), f"'<name> buy' answers a shop list: {[l for l in ev if 'SHOP' in l]}")
    stock = c.call("shop")
    ok(len(stock) > 2 and "gp" in stock[1], f"shop lists {len(stock) - 1} lines: {stock[1].strip()[:60]}")
    import re
    row = next((re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", l) for l in stock if "pickaxe" in l.lower() or "tongs" in l.lower()), None)
    g0 = c.gold
    if row:
        c.call(f"buy {row.group(1)} 2")
        tick(clock, world)
        ok(c.gold == g0 - 2 * int(row.group(2)), f"bought 2 x {row.group(4).strip()} for {2 * int(row.group(2))}: gold {g0} -> {c.gold}")
    c.events.drain()
    c.say(f"{tinker.name} sell")
    tick(clock, world)
    sl = c.call("selllist")
    ok(any("gp" in l for l in sl), f"sell list: {[l.strip()[:50] for l in sl[:4]]}")

    # ---- a fight: the nearest creature within reach, attacked until dead; its corpse looted and carved
    c.goto(1320, 1800)
    run_until(clock, world, 200)
    prey = [m for m in c.mobiles(within=18) if m.notoriety == "Gray" and not m.is_dead]
    ok(prey, f"creatures in view at the farmlands: {[m.name for m in prey][:6]}")
    kills0 = hero.kills
    if prey:
        t = prey[0]
        c.goto(t.x, t.y)
        run_until(clock, world, 20)
        c.war(True)
        c.attack(t.serial)
        for _ in range(60):
            run_until(clock, world, 2)
            cur = next((m for m in c.mobiles(within=18) if m.serial == t.serial), None)      # a cow wanders off between swings: follow it (within view, not three tiles)
            if cur is None:
                break
            if cur.distance > 1:
                c.goto(cur.x, cur.y)
        ok(hero.kills == kills0 + 1, f"killed {t.name}: kills {hero.kills}, hp {c.hp}/{c.max_hp}")
        corpses = [i for i in c.containers(within=8) if i.is_corpse]
        ok(corpses and corpses[0].name.endswith(" corpse"), f"corpse in view: {[i.name for i in corpses][:2]}")
        if corpses:
            corpse = corpses[0]
            c.gotoexact(corpse.x, corpse.y)
            run_until(clock, world, 10)
            c.events.drain()
            c.use(corpse.serial)
            tick(clock, world)
            ev = [e for e in c.events.poll()]
            ok(any(e.kind == Event.CONTAINER_CONTENTS for e in ev), f"opening the corpse: {[e.text for e in ev]}")
            blade = c.find("dagger")
            c.use(blade.serial)
            tick(clock, world)
            ev = c.events.poll()
            ok(any(e.kind == Event.TARGET_REQUEST for e in ev), "a blade raises a target cursor")
            c.target(corpse.serial)
            tick(clock, world)
            ev = [e.text for e in c.events.poll()]
            contents = c.container(corpse.serial)
            ok(any("carve" in l or "skin" in l or "nothing useful" in l for l in ev), f"carving: {ev[:2]}; corpse now holds {[str(i) for i in contents]}")
            for it in contents:
                c.get_item(it.serial, it.amount if it.amount > 1 else None)
            tick(clock, world)
            ok(not c.container(corpse.serial), f"looted everything: pack has {[i.name for i in c.backpack if 'raw' in i.name or 'hides' in i.name or 'gold' in i.name]}")

    # ---- bandages
    hero.hp = 40
    c.events.drain()
    c.use(c.find("bandage").serial)
    tick(clock, world)
    ok(any(e.kind == Event.TARGET_REQUEST for e in c.events.poll()), "the bandage raises a target cursor")
    c.target_self()
    run_until(clock, world, 15)
    ev = [e for e in c.events.poll()]
    ok(any(e.kind in (Event.BANDAGE_DONE, Event.BANDAGE_FAILED) or "bandages" in e.text for e in ev) and c.hp > 40, f"bandage: {[e.text for e in ev][-2:]}; hp {c.hp}")

    # ---- mining at the hills north of Britain
    mx, my = next(((x, y) for x, y, z, g in data.mountains if x < 5000), (1455, 1520))
    c.goto(mx, my + 2)
    run_until(clock, world, 200)
    c.events.drain()
    c.use(c.find("pickaxe").serial)
    tick(clock, world)
    ok(any(e.kind == Event.TARGET_REQUEST for e in c.events.poll()), "pickaxe raises a target cursor")
    c.call(f"targettile {mx} {my} 20 0")
    run_until(clock, world, 30)
    ev = [e.text for e in c.events.poll()]
    ok(any("ore" in l for l in ev), f"mining says: {[l for l in ev if 'ore' in l or 'metal' in l][:2]}; ore in pack {hero.count('ore')}")

    # ---- fishing: the nearest water
    water = None
    for r in range(1, 120):
        for dx in range(-r, r + 1, 3):
            for dy in (-r, r):
                if data.is_water(c.x + dx, c.y + dy):
                    water = (c.x + dx, c.y + dy)
                    break
            if water:
                break
        if water:
            break
    if water:
        c.goto(water[0] - 2, water[1])
        run_until(clock, world, 300)
        c.events.drain()
        c.use(c.find("fishing pole").serial)
        tick(clock, world)
        c.events.poll()
        tiles = c.call(f"tiles {water[0]} {water[1]}")
        ok(any("0x00A8" in l for l in tiles), f"tiles on water: {tiles[1:]}")
        c.call(f"targettile {water[0]} {water[1]} -5 0")
        run_until(clock, world, 60)
        ev = [e.text for e in c.events.poll()]
        ok(any("fish" in l for l in ev), f"fishing says: {[l for l in ev if 'fish' in l or 'water' in l][:2]}; fish {hero.count('fish')}")

    # ---- crafting: tongs on ingots, the menu tree, one leaf
    c.events.drain()
    c.use(c.find("tongs").serial)
    tick(clock, world)
    c.events.poll()
    c.target(c.find("iron ingot").serial)
    tick(clock, world)
    menus = c.call("menus")
    ok(any(l.startswith("[MENU]") for l in menus), f"craft menu: {menus[:3]}")
    m = re.match(r"\[MENU\] local (\S+) server (\S+)", menus[0])
    opts = [(int(o.group(1)), o.group(2)) for o in (re.match(r"\s*\[option (\d+)\] graphic \S+ hue \S+ (.+)", l) for l in menus) if o]
    build = next((i for i, t in opts if t.startswith("Build")), None)
    c.call(f"menuresponse {m.group(1)} {m.group(2)} {build}")
    menus = c.call("menus")
    m2 = re.match(r"\[MENU\] local (\S+) server (\S+)", menus[0])
    leaf = next((l for l in menus if "(" in l), None)
    ok(leaf is not None and re.search(r"\((\d+) [^)]+\)\s*$", leaf), f"leaf menu: {leaf.strip() if leaf else menus[:2]}")
    ingots0 = hero.count("ingot")
    c.events.drain()
    c.call(f"menuresponse {m2.group(1)} {m2.group(2)} 1")
    tick(clock, world)
    ev = [e.text for e in c.events.poll()]
    ok(any("You create" in l or "failed to create" in l for l in ev) and hero.count("ingot") < ingots0, f"a craft: {ev[-1:]}; ingots {ingots0} -> {hero.count('ingot')}")

    # ---- a spell at a creature
    prey = [m for m in c.mobiles(within=12) if m.notoriety == "Gray" and not m.is_dead]
    c.events.drain()
    out = c.call("cast magic arrow")
    tick(clock, world)
    ok(any("Casting" in l for l in out) and any(e.kind == Event.TARGET_REQUEST for e in c.events.poll()), f"cast: {out[:1]}")
    mana0 = c.mana
    c.target(prey[0].serial if prey else "self")
    tick(clock, world)
    ev = [e.text for e in c.events.poll()]
    ok(c.mana < mana0 or any("fizzles" in l or "reagents" in l for l in ev), f"magic arrow: mana {mana0} -> {c.mana}; {ev[-2:]}")

    # ---- taming
    animal = next((m for m in c.mobiles(within=18) if m.notoriety == "Gray" and data.tame.get(world.creatures[m.serial].kind) if m.serial in world.creatures), None)
    if animal is None:
        kind = next(k for k in data.tame if data.creature(k))
        from sim.world import Creature
        cr = Creature(world.new_serial(), kind, data, c.x + 2, c.y)
        world.creatures[cr.serial] = cr
        world._index(cr)
        world.version += 1
        tick(clock, world)
        animal = next(m for m in c.mobiles(within=4) if m.serial == cr.serial)
    c.goto(animal.x, animal.y)
    run_until(clock, world, 10)
    hero.next_skill = 0
    c.events.drain()
    c.call("useskill animal taming")
    tick(clock, world)
    ok(any(e.kind == Event.TARGET_REQUEST for e in c.events.poll()), "useskill animal taming raises a cursor")
    hero.skills["Animal Taming"] = 100.0
    c.target(animal.serial)
    run_until(clock, world, 12)
    ev = [e.text for e in c.events.poll()]
    ok(any("accept you" in l or "fail to tame" in l or "too far" in l for l in ev), f"taming {animal.name}: {ev[-1:]}; pets {len(hero.pets)}")

    # ---- death and the healer
    hero.hp = 1
    world.hurt(hero, 5, "selftest")
    tick(clock, world)
    ok(c.ghost and c.hp == 0, f"dead: ghost {c.ghost}")
    corpses = [i for i in c.containers(within=3) if "SelfTest" in i.name]
    ok(corpses, f"own corpse: {[i.name for i in corpses]}")
    healer = next(v for v in world.vendors.values() if v.role == "healer")
    c.goto(healer.x, healer.y)
    run_until(clock, world, 400)
    c.war(True)
    g = c.call("gumps")
    ok(any("Resurrection" in l for l in g), f"the healer's offer: {g[:2]}")
    serial = next((re.match(r"\[GUMP\] local \S+ server (\S+)", l).group(1) for l in g if l.startswith("[GUMP] local")), None)
    c.call(f"gumpresponse 1 gump:{serial}")
    tick(clock, world)
    ok(not c.ghost and c.hp > 0, f"resurrected: hp {c.hp}")

    # ---- item 5: the dungeon side, teleporters, parties -----------------------------------------------------------------------------------------------------
    dsp = [sp for sp in data.spawners if sp["x"] >= 5120]
    ok(dsp and all(data.side(sp["x"], sp["y"]) in ("Despise", "Shame", "Deceit", "Covetous", "Wrong", "Destard", "Hythloth") for sp in dsp), f"dungeon spawners: {len(dsp)} in the rung dungeons")
    ok(data.walkable(5588, 630) and not data.walkable(5130, 1000), "the dungeon grid: Despise's landing walkable, rock not")
    tele = world.add_player({"name": "SelfTele", "profession": 13, "skills": {}, "pos": [1298, 1083]})
    goal = min((sp for sp in dsp if data.side(sp["x"], sp["y"]) == "Despise"), key=lambda sp: abs(sp["x"] - 5588) + abs(sp["y"] - 630))
    world.start_walk(tele, goal["x"], goal["y"])
    ok(tele.nav["status"] == "nopath", f"a walk across sides is nopath: {tele.nav['status']}")
    world.start_walk(tele, 1296, 1080, exact=True)
    run_until(clock, world, 8)
    ok(tele.x >= 5120 and data.side(tele.x, tele.y) == "Despise", f"standing on Despise's entrance moved the bot to {tele.x},{tele.y}")
    back = next(((sx, sy) for (sx, sy), t in world.teleporters.items() if t[3] == "surface" and t[2] == "Despise" and max(abs(sx - tele.x), abs(sy - tele.y)) <= 12), None)
    ok(back is not None, f"a way back beside the landing: {back}")
    import spots
    hops = spots.inner_hops("Despise", (tele.x, tele.y), (goal["x"], goal["y"]))
    ok(hops and world.route(hops[-1]["dst"][0], hops[-1]["dst"][1], goal["x"], goal["y"]) is not None,
       f"the landing is an antechamber: {len(hops or [])} inner teleporter(s) to level 1, then a route to the spawner")
    world.start_walk(tele, hops[0]["src"][0], hops[0]["src"][1], exact=True) if hops else None
    run_until(clock, world, 30)
    ok(hops and max(abs(tele.x - hops[0]["dst"][0]), abs(tele.y - hops[0]["dst"][1])) <= 2, f"the inner stair moved the bot to {tele.x},{tele.y}")
    inv = world.add_player({"name": "SelfInvitee", "profession": 13, "skills": {}, "pos": [tele.x, tele.y]})
    ci, cj = FakeClient(world, tele), FakeClient(world, inv)
    ok(ci.call("partyinfo")[0].startswith("[PARTY] not in a party"), "no party yet")
    ci.call("partyinvite")
    ci.call(f"target {inv.serial}")
    ok(inv.party_invite == tele.serial, "the invitation reached the other player")
    cj.call("partyaccept")
    info = ci.call("partyinfo")[0]
    ok("in a party" in info and "members=2" in info and "SelfInvitee" in info and f"leader={tele.serial}" in info, f"partyinfo: {info}")
    cj.call("partyloot on")
    ok("canloot=yes" in cj.call("partyinfo")[0] and world._party(tele, inv.serial), "party loot on, the two are one party")
    inv.hp = inv.max_hp // 2
    tele.add_item({"name": "Bandage", "amount": 5}, quiet=True)
    ci.call("use " + next(i["serial"] for i in tele.backpack if i["name"].lower() == "bandage"))
    ci.call(f"target {inv.serial}")
    run_until(clock, world, 12)
    ok(inv.hp > inv.max_hp // 2, f"a bandage on the party member healed it: {inv.hp}/{inv.max_hp}")
    cj.call("partyleave")
    ok(ci.call("partyinfo")[0].startswith("[PARTY] not in a party") and tele.party is None, "the party of one is gone when the other leaves")

    # ---- the watcher's eight gaps (2026-10-21) ------------------------------------------------------------------------------------------------------------
    from sim.world import Creature
    import sim.world as W
    gp = world.add_player({"name": "SelfGaps", "profession": 13, "skills": {"Swordsmanship": 80}, "pos": [1320, 1800], "max_hp": 80, "max_stam": 40})
    rab = Creature(world.new_serial(), "rabbit", data, gp.x + 1, gp.y)
    world.creatures[rab.serial] = rab
    world._index(rab)
    ok(not rab.aggressive, "a rabbit does not attack on sight")
    world.rng.seed(7)
    world.damage_creature(rab, rab.max_hp - 1, gp)
    ok(rab.fleeing == gp.serial or rab.dead, f"a rabbit under half its hit points runs: {rab.fleeing}")
    if rab.fleeing:
        run_until(clock, world, 10)
        ok(rab.serial not in world.creatures, "the rabbit got away (out of the fight, its spawner respawns it)")
    flee = 0
    for i in range(40):
        rb = Creature(world.new_serial(), "rabbit", data, gp.x + 1, gp.y)
        world.creatures[rb.serial] = rb; world._index(rb)
        world.damage_creature(rb, 1, gp)
        flee += rb.fleeing is not None
        world.creatures.pop(rb.serial, None); world._unindex(rb)
    ok(25 <= flee <= 40, f"rabbits flee on their first hit about as often as the live hour (86%): {flee} of 40")
    gp.poisoned, gp.hp = True, 80
    run_until(clock, world, 4)
    hp1 = gp.hp
    run_until(clock, world, 8)
    ok(gp.hp <= hp1 - 8, f"Lesser poison ticks 4+ every 2.25 s: {hp1} -> {gp.hp}")
    run_until(clock, world, 20)
    ok(not gp.poisoned, "the poison wears off after its ten ticks")
    gp.hp = gp.max_hp
    wr = Creature(world.new_serial(), "wraith", data, gp.x + 9, gp.y)
    world.creatures[wr.serial] = wr
    world._index(wr)
    ok(wr.casts, "a wraith casts")
    wr.target, wr.next_cast = gp.serial, 0.0
    hp0 = gp.hp
    world._step_creatures(0.5)
    ok(gp.hp < hp0 and cheb(wr.x, wr.y, gp.x, gp.y) >= 2, f"a wraith hits from {cheb(wr.x, wr.y, gp.x, gp.y)} tiles: {hp0} -> {gp.hp}")
    st0 = gp.stam
    world.hurt(gp, 10, wr)
    ok(gp.stam == max(0, st0 - 3), f"a hit takes at most 3 stamina: {st0} -> {gp.stam}")
    world.creatures.pop(wr.serial, None); world._unindex(wr)
    healer = world._vendor_near(gp, 9999, role="healer")
    names = [x["name"].lower() for x in healer.stock] if healer else []
    ok(healer and any("bandage" in n for n in names) and "yellow potion" in names, f"the simulated healer's list is the live one (shops.json): {names[:6]}")
    if healer:
        b = next(x for x in healer.stock if "bandage" in x["name"].lower())
        b["qty"] = 0
        healer.restock_at = world._now + W.RESTOCK_S
        run_until(clock, world, 120)
        ok(b["qty"] == 0, "a sold-out list stays empty between restocks")
        healer.restock_at = world._now
        run_until(clock, world, 6)
        ok(b["qty"] == b["max"], "and comes back to full at its hour")
    bk = world.add_player({"name": "SelfSpeech", "profession": 13, "skills": {}, "pos": [1425, 1688]})
    banker = world._vendor_near(bk, 12, role="bank")
    if banker:
        world.say(bk, "Going to the bank now")
        ok(bk.bank_open, "'bank' inside a sentence opens the bank box near a banker (the server's keyword)")
        bk.bank_open = False
        world.say(bk, "Going to the vault now")
        ok(not bk.bank_open, "the rephrased line opens nothing")

    import sim.world_data as wdm
    tbl = wdm.price_tables(data.vendor_buys)
    v = wdm.holdings_value([{"name": "Bandage", "amount": 40}, {"name": "Yellow Potion", "amount": 3}, {"name": "Cut Of Raw Ribs", "amount": 10}, {"name": "gold coin", "amount": 999},
                            {"name": "Mystery Thing", "amount": 5}], tbl)
    ok(v == 40 * 3 + 3 * 15 + 10 * tbl[1]["cut of raw ribs"], f"holdings: bandages and potions at the shop's price, meat at the buy-back, gold and unknowns not counted: {v}")

    bad = [w for okk, w in checks if not okk]
    print(f"\n{len(checks) - len(bad)} of {len(checks)} checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
