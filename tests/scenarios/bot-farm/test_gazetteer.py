"""Tests for the gazetteer (gazetteer.py + gazetteer.json from make_gazetteer.py): python test_gazetteer.py

The coordinates typed below are ORACLES: the hand-typed Britain constants the brains used (bot_common.py HEALER, BANKS, BRITAIN, MAGE_SHOP; crafter.py
station / shop / sell_to; hunter.py FACILITIES) and the facts the world data states. The gazetteer must give every one of them back from data alone.
"""
import ast
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gazetteer as gz
import make_gazetteer as mk

# ---- oracles (from the brains' hand-typed constants) ---------------------------------------------------------------------------------------------
HEALER = (1472, 1611)
BANKS = [(1425, 1690), (1650, 1608)]
BRITAIN = {(1416, 1498, 1740, 1777), (1500, 1408, 1546, 1498), (1385, 1538, 1416, 1777), (1416, 1777, 1740, 1837), (1385, 1777, 1416, 1907),
           (1093, 1538, 1385, 1907)}
MAGE_SHOP = (1485, 1553)
SMITH_STATION, SMITH_SHOP, SMITH_SELL = (1423, 1557), (1427, 1652), (1418, 1550)
TAILOR_SHOP, CARPENTER_SHOP = (1467, 1688), (1430, 1599)
DUMMIES, BUTTE = [(1589, 1554), (1528, 1431)], (1468, 1579)
TOWN = (1470, 1620)


def d(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])
def xy(p): return (p["x"], p["y"])


# ---- the module is pure -----------------------------------------------------------------------------------------------------------------------------
tree = ast.parse(open(os.path.join(HERE, "gazetteer.py"), encoding="utf-8").read())
imports = {n.names[0].name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)} | \
          {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
assert imports <= {"json", "math", "os"}, imports                                    # no Navrey, no bot state
src = open(os.path.join(HERE, "gazetteer.py"), encoding="utf-8").read()
assert "1470" not in src and "1620" not in src                                       # no Britain coordinate literal in the module

# ---- regions ----------------------------------------------------------------------------------------------------------------------------------------
b = gz.home_region(*TOWN)
assert b["name"] == "Britain" and b["kind"] == "town", b
assert {tuple(r) for r in gz.town_rects("Britain")} == BRITAIN, gz.town_rects("Britain")      # the TownRegion's own rectangles, equal to BRITAIN
assert b["centre"][:2] == [1495, 1629], b["centre"]
assert gz.in_town(*TOWN) and gz.in_town(1120, 1790) and not gz.in_town(1470, 1300) and not gz.in_town(700, 1100)
assert gz.home_region(1470, 1300) is None and gz.home_region(100, 100) is None
for name, pos in (("Trinsic", (1927, 2779)), ("Vesper", (2882, 788)), ("Yew", (535, 992)), ("Minoc", (2526, 583)), ("Skara Brae", (632, 2233))):
    r = gz.home_region(*pos)
    assert r and r["name"] == name and gz.in_town(*pos), (name, r and r["name"])
assert gz.home_region(2970, 800)["name"] == "Vesper" or gz.home_region(2970, 800) is None
town, dist = gz.nearest_town(1470, 1300)
assert town["name"] == "Britain" and 100 < dist < 220, (town["name"], dist)
assert gz.nearest_town(*TOWN)[1] == 0
assert gz.nearest_town(1927, 2779)[0]["name"] == "Trinsic"
assert all(r["kind"] != "town" or not mk.FARM.search(r["name"]) for r in gz.towns())      # the wheat and cotton fields are not towns
assert gz.home_region(5501, 570)["name"] == "Despise" and gz.home_region(5501, 570)["kind"] == "dungeon"

# ---- Britain's services come out of the data -------------------------------------------------------------------------------------------------------
bank = gz.near("bank", *TOWN, n=4, region="Britain")
assert {xy(p) for p in bank} >= set(BANKS), bank
assert d(xy(gz.near("healer", *TOWN)[0]), HEALER) <= 3
assert d(xy(gz.near("mage", *MAGE_SHOP)[0]), MAGE_SHOP) <= 5
assert d(xy(gz.near("forge", *SMITH_STATION)[0]), SMITH_STATION) <= 3 and d(xy(gz.near("anvil", *SMITH_STATION)[0]), SMITH_STATION) <= 3
assert d(xy(gz.near("smith", *SMITH_SELL)[0]), SMITH_SELL) <= 4                         # the blacksmith the crafters sell to
assert d(xy(gz.near("tinker", *SMITH_SHOP)[0]), SMITH_SHOP) <= 4                        # the ingot shop
assert d(xy(gz.near("tailor", *TAILOR_SHOP)[0]), TAILOR_SHOP) <= 4
assert d(xy(gz.near("carpenter", *CARPENTER_SHOP)[0]), CARPENTER_SHOP) <= 4
for pos in DUMMIES:
    assert d(xy(gz.near("dummy", *pos)[0]), pos) <= 1
assert d(xy(gz.near("butte", *BUTTE)[0]), BUTTE) <= 1
assert gz.near("bowyer", *TOWN)[0]["region"] == "Britain" and gz.near("banker", *TOWN)[0]["role"] == "bank"          # raw type names answer too
assert gz.near(("bank", "healer"), *TOWN, n=3)[0]["dist"] <= gz.near("bank", *TOWN)[0]["dist"]
svc = gz.services("Britain")
for role in ("bank", "healer", "smith", "tailor", "carpenter", "butcher", "bowyer", "mage", "provisioner", "forge", "anvil", "loom", "guard"):
    assert svc.get(role), (role, svc)
assert gz.has_role("Britain", "healer") and not gz.has_role("Britain", "no_such_role")
refs = gz.refuges("Britain")
assert 3 <= len(refs) <= 6 and all(gz.in_town(*p) for p in refs) and all(d(a, c) >= 12 for i, a in enumerate(refs) for c in refs[:i])
assert d(refs[0], HEALER) <= 3 and any(d(p, BANKS[0]) <= 3 for p in refs)

# ---- the drop test's need: other towns, and what they lack -----------------------------------------------------------------------------------------
for name, pos in (("Trinsic", (1927, 2779)), ("Vesper", (2882, 788)), ("Skara Brae", (632, 2233)), ("Yew", (535, 992))):
    s = gz.services(name)
    assert not s.get("bank") and not s.get("healer") and not s.get("smith"), (name, s)         # only Britain has them on this shard
    assert not gz.has_role(name, "bank")
    nb = gz.near("bank", *pos)[0]
    assert nb["region"] == "Britain" and nb["dist"] > 200                                      # the nearest town that has one
    assert gz.refuges(name), name                                                              # a town without services still has a refuge: its centre
    assert gz.refuges(name)[0] == tuple(gz.region(name)["centre"][:2]) or d(gz.refuges(name)[0], gz.region(name)["centre"]) < 3
trin = gz.region("Trinsic")
assert trin["centre"][:2] == [1867, 2780] or d(trin["centre"], (1867, 2780)) < 5
assert gz.near("moongate", 1927, 2779)[0]["x"] == 1828 and gz.near("moongate", 2882, 788)[0]["name"] in ("Minoc", "Britain", "Yew", "Trinsic")
assert gz.near("moongate", 2882, 788)[0]["x"] == 2701                                          # Vesper's nearest gate is Minoc's

# ---- moongates -------------------------------------------------------------------------------------------------------------------------------------
gates = gz.near("moongate", *TOWN, n=20)
assert len(gates) == 9, len(gates)
assert (1336, 1997) in {xy(g) for g in gates} and {g["name"] for g in gates} >= {"Britain", "Trinsic", "Yew", "Minoc", "Skara Brae", "Jhelom", "Moonglow"}
assert xy(gz.near("moongate", *TOWN)[0]) == (1336, 1997)                                       # Britain's gate is outside the walls

# ---- teleporters: the sewer hatch pair, both ways -------------------------------------------------------------------------------------------------
hatch = gz.transitions(1491, 1641, 3)
pairs = {(tuple(t["src"][:2]), tuple(t["dst"][:3])) for t in hatch}
assert ((1491, 1640), (6032, 1499, 31)) in pairs and ((1491, 1642), (6032, 1501, 31)) in pairs, pairs
assert all(t["kind"] == "enter" and t["dst_side"] == gz.side(6032, 1499) for t in hatch)
out = gz.transitions(6031, 1500, 3)
assert {(tuple(t["src"][:3]), tuple(t["dst"][:3])) for t in out} >= {((6031, 1499, 42), (1491, 1640, 24)), ((6031, 1501, 42), (1491, 1642, 24))}
assert all(t["kind"] == "exit" for t in out)
assert gz.side(1470, 1620) == "surface" and gz.side(6045, 1470) == gz.side(6032, 1499) != "surface"
r = gz.route(TOWN, (6045, 1470))                                                                # from Britain to a spot in the sewer: the hatch
assert len(r) == 1 and tuple(r[0]["src"][:2]) in {(1491, 1640), (1491, 1642)} and r[0]["dst"][0] == 6032
r = gz.route((6045, 1470), TOWN)                                                                # from the sewer to Britain: the exit
assert len(r) == 1 and tuple(r[0]["src"][:2]) in {(6031, 1499), (6031, 1501)} and tuple(r[0]["dst"][:2]) in {(1491, 1640), (1491, 1642)}
assert gz.route(TOWN, (1500, 1600)) == [] and gz.route((6045, 1470), (6050, 1480)) == []       # same side: the planner can walk it
r = gz.route((1491, 1641), (6045, 1470)); assert tuple(r[0]["src"][:2]) in {(1491, 1640), (1491, 1642)}
# a chain: from the sewer into Despise and back goes through the surface
rr = gz.route((6045, 1470), (5501, 570))
assert rr is None or (len(rr) >= 2 and rr[0]["kind"] == "exit"), rr
assert gz.route((6045, 1470), (1470, 1620))[0]["dst_region"] == "Britain"

# ---- dungeon entrances ----------------------------------------------------------------------------------------------------------------------------------
ent = gz.near("dungeon_entrance", *TOWN, n=60)
names = {p["name"] for p in ent}
for want in ("Despise", "Covetous", "Shame", "Destard", "Deceit", "Wrong", "Misc Dungeons"):
    assert want in names, (want, sorted(names))
assert any(p["name"] == "Misc Dungeons" and p["region"] == "Britain" for p in ent)             # the Britain sewer hatch
dec = next(p for p in ent if p["name"] == "Deceit")
assert d(xy(dec), (4111, 431)) <= 3, dec
sh = next(p for p in ent if p["name"] == "Shame")
assert d(xy(sh), (513, 1560)) <= 3 and sh["landing"][0] > 5120

# ---- near(): filters ------------------------------------------------------------------------------------------------------------------------------------
assert gz.near("bank", *TOWN, max_dist=5) == []
assert all(p["dist"] <= 200 for p in gz.near("mage", *TOWN, n=5, max_dist=200))
sew = gz.near("dungeon_entrance", 6045, 1470, n=3, same_side=True)
assert all(p["side"] == gz.side(6045, 1470) for p in sew)
assert gz.near("no_such_role", *TOWN) == []

# ---- regenerable and deterministic ----------------------------------------------------------------------------------------------------------------------
import json
fresh = mk.dump(mk.build(os.path.join(mk.ROOT, "ModernUO", "Distribution", "Data"), os.path.join(mk.ROOT, "UOData"),
                         os.path.join(mk.ROOT, "ModernUO", "Projects", "UOContent", "Items", "Misc", "PublicMoongate.cs")))
assert fresh == open(gz.DEFAULT_PATH, encoding="utf-8").read(), "gazetteer.json is stale or hand-edited: run make_gazetteer.py"
assert mk.dump(json.loads(fresh)) == fresh
print("test_gazetteer OK:", len(gz.get().places), "places,", len(gz.get().regions), "regions,", len(gz.get().trans), "teleporters")
