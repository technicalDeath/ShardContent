"""Builds data/client/UORekindled-Britain.csv: world map markers (x,y,map,name,icon,color,zoom) for the places a new player looks for in Britain, read from the generated world data
(ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b: Spawns/Vendors.json, britain-vendor-overrides.json and Decoration/Britannia__britain.cfg), so a moved NPC changes the map on the next run.
Copy the output to ClassicUO/bin/dist/Data/Client/ (the client loads every .csv there). No blank lines: the client stops reading a file at the first one."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "ModernUO" / "Distribution" / "Data" / "BritanniaRenaissance" / "Alpha2b"
OUT = ROOT / "ShardContent" / "data" / "client" / "UORekindled-Britain.csv"

# (spawn type, label, colour, all spawners or just the first)
NPCS = [
    ("Banker", "Bank", "yellow", True),
    ("Healer", "Healer (resurrects you)", "green", True),
    ("HealerGuildmaster", "Healers' Guildmaster (teaches Healing)", "purple", False),
    ("Blacksmith", "Blacksmith (weapons, armor, tools)", "blue", True),
    ("BlacksmithGuildmaster", "Blacksmiths' Guildmaster", "purple", False),
    ("Armorer", "Armorer", "blue", False),
    ("Weaponsmith", "Weaponsmith", "blue", False),
    ("Bowyer", "Bowyer (bows, arrows)", "blue", False),
    ("Provisioner", "Provisioner (general goods)", "blue", True),
    ("Alchemist", "Alchemist (potions, reagents)", "blue", False),
    ("Mage", "Mage shop (spells, reagents)", "blue", False),
    ("MageGuildmaster", "Mages' Guildmaster", "purple", False),
    ("Tinker", "Tinker (tools)", "blue", False),
    ("TinkerGuildmaster", "Tinkers' Guildmaster", "purple", False),
    ("Miner", "Miner (shovels, pickaxes)", "blue", False),
    ("MinerGuildmaster", "Miners' Guildmaster", "purple", False),
    ("Carpenter", "Carpenter", "blue", False),
    ("Tailor", "Tailor", "blue", False),
    ("Cook", "Cook / food", "blue", False),
    ("Jeweler", "Jeweler", "blue", False),
    ("Scribe", "Scribe (scrolls, books)", "blue", False),
    ("InnKeeper", "Inn", "blue", False),
    ("WarriorGuildmaster", "Warriors' Guildmaster", "purple", False),
    ("BardGuildmaster", "Bards' Guildmaster", "purple", False),
    ("ThiefGuildmaster", "Thieves' Guildmaster", "purple", False),
    ("RangerGuildmaster", "Rangers' Guildmaster", "purple", False),
    ("FisherGuildmaster", "Fishermen's Guildmaster", "purple", False),
    ("Furnisher", "Furnisher (house decorations)", "blue", False),
]


def spawners():
    out = []
    for name in ("Vendors.json", "britain-vendor-overrides.json"):
        for sp in json.loads((DATA / "Spawns" / name).read_text(encoding="utf-8-sig")):
            for e in sp.get("entries", []):
                out.append((e["name"], sp["location"][0], sp["location"][1]))
    return out


def decorations(kind):
    lines = (DATA / "Decoration" / "Britannia__britain.cfg").read_text(encoding="utf-8-sig").splitlines()
    pts, on = [], False
    for line in lines:
        if line.startswith(kind + " "):
            on = True
        elif line.startswith("#") or not line.strip():
            on = False
        elif on:
            x, y, _ = line.split()[:3]
            pts.append((int(x), int(y)))
    return pts


def cluster(points, gap=8):
    kept = []
    for x, y in points:
        if all(abs(x - kx) > gap or abs(y - ky) > gap for kx, ky in kept):
            kept.append((x, y))
    return kept


def main():
    rows = []
    sp = spawners()
    for typ, label, colour, every in NPCS:
        hits = [(x, y) for n, x, y in sp if n.lower() == typ.lower()]
        for i, (x, y) in enumerate(hits if every else hits[:1]):
            rows.append((x, y, label, colour))
    for x, y in cluster(decorations("TrainingDummy")):
        rows.append((x, y, "Training dummies (practise fighting skills)", "red"))
    for x, y in cluster(decorations("ArcheryButte")):
        rows.append((x, y, "Archery butte (practise Archery)", "red"))
    rows.append((1336, 1997, "Moongate (to the other towns)", "white"))
    # one dot per spot: labels that share a spot are joined, the first one's colour wins
    spots = {}
    for x, y, label, colour in rows:
        entry = spots.setdefault((x, y), [[], colour])
        if label not in entry[0]:
            entry[0].append(label)
    lines = [f"{x},{y},0,{' / '.join(labels).replace(',', ';')},,{colour},3" for (x, y), (labels, colour) in spots.items()]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(lines)} markers -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
