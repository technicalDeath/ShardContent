"""Which tiles near Britain are already built or decorated, so light scenery keeps clear of them (owner, 2026-10-18:
"the light deco should not encroach on points of interest that are already decorated").

Three sources:
  * map statics that are man-made (walls, roofs, doors, windows, floors, fences, furniture, signs, graves, crops ...):
    every static that is not nature (trees, leaves, grass, ferns, flowers, rocks, boulders, reeds, mushrooms, water);
  * server items the world generation places (Decoration/*.cfg: teleporters, signs, furniture, lamp posts ...);
  * named regions that are places in their own right (Britain Graveyard, the crop fields, the moongate).
Roads and bridges (cobblestones, pavers, planks) come back separately: scenery stays off them only.
Also returns the farm tiles (crop fields and fences, hay, furrows, crops, farm buildings' surroundings are found by the
caller as built tiles near them), so farm scenery can sit beside them on purpose.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "world-decorating"))
import uo_world  # noqa: E402

NATURE = re.compile(r"tree|leaves|grass|fern|bush|weed|flower|rock|boulder|cattail|reed|lily|mushroom|vine|moss|stump|"
                    r"fallen log|sapling|plant|shrub|cactus|water|foliage|campion|poppies|snowdrop|orfluer|hedge|"
                    r"spider ?web|bramble|rushes|thorn|stalagmite|o'hii|blade|juniper|cedar|cypress|willow|palm|pine|lilies|seaweed|kelp|sand|dirt|mud")
FARM = re.compile(r"fence|hay|furrow|wheat|corn|cotton|flax|cabbage|carrot|turnip|onion|lettuce|pumpkin|trough|haystack|"
                  r"scarecrow|crop|garden|fodder|straw|barn|stable|gate")
PLACE_REGIONS = re.compile(r"graveyard|field|moongate", re.I)
PATH = re.compile(r"^(cobblestones|stone pavers|wooden bridge|wooden plank|dirt path)$")


def tiles_of(census):
    x0, y0, x1, y1 = census["rect"]
    region = uo_world.Region(x0, y0, x1, y1)
    tiles = uo_world.tiles
    built, farm, path = set(), set(), set()
    for (x, y), sts in region.stat.items():
        for tid, _ in sts:
            if tid >= len(tiles):
                continue
            t = tiles[tid]
            n = t.name.lower()
            if t.flags & uo_world.FOLI or NATURE.search(n):
                continue
            if PATH.search(n):  # a road or bridge: scenery stays off it, but it is not a place to keep away from
                path.add((x, y))
                continue
            built.add((x, y))
            if FARM.search(n):
                farm.add((x, y))
    for cls, name, x, y, _ in uo_world.load_decoration((x0, y0, x1, y1)):
        built.add((x, y))
        if FARM.search((name or "") + " " + cls.lower()):
            farm.add((x, y))
    regions = []
    for r in census["towns"] + census["otherRegions"]:
        if r["name"] and PLACE_REGIONS.search(r["name"]):
            regions.append({"name": r["name"], "rects": r["rects"]})
            for a, b, c, d in r["rects"]:
                for x in range(a, c):
                    for y in range(b, d):
                        built.add((x, y))
                        if "field" in r["name"].lower():
                            farm.add((x, y))
    return region, built, farm, path, regions
