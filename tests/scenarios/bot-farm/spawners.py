"""The world's spawners as the server makes them: every file of the Alpha2b Spawns folder in the manifest's order (spawnerFiles, then customSpawnerFiles), and of
two definitions with the same GUID, or the same type, map and place, only the LAST counts (Alpha2bWorldGenerationCommands.CanonicalizeSpawners). Without
this a re-themed spawner (greater-britain-spawn-areas.json re-themes 76 stock ones by GUID, 2026-10-18) would be read twice: its old creatures and its new.

    for f, s in spawners.canonical(spawn_dir): ...      # f: the file name, s: the spawner record (location, map, entries, homeRange, ...)
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
MANIFEST = os.path.join(ROOT, "ShardContent", "data", "world-generation", "alpha2b", "world-generation.json")


def order(spawn_dir, manifest=MANIFEST):
    """The spawner files of spawn_dir in the order the server reads them; files the manifest does not name come last, by name (never silently dropped)."""
    names = sorted(f for f in os.listdir(spawn_dir) if f.endswith(".json"))
    try:
        m = json.load(open(manifest, encoding="utf-8-sig"))
        listed = list(m.get("spawnerFiles", [])) + list(m.get("customSpawnerFiles", []))
    except (OSError, ValueError):
        listed = []
    return [f for f in listed if f in names] + [f for f in names if f not in listed]


def canonical(spawn_dir, manifest=MANIFEST):
    """[(file, record)] of the canonical spawners, in the server's order."""
    defs = []
    for f in order(spawn_dir, manifest):
        try:
            data = json.load(open(os.path.join(spawn_dir, f), encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        for s in data if isinstance(data, list) else []:
            defs.append((f, s))
    seen_loc, seen_guid, out = set(), set(), []
    for f, s in reversed(defs):
        loc = s.get("location") or [None, None, None]
        key = (s.get("$type"), s.get("map"), *loc[:3])
        g = s.get("guid")
        if key in seen_loc or (g and g in seen_guid):
            continue
        seen_loc.add(key)
        if g:
            seen_guid.add(g)
        out.append((f, s))
    out.reverse()
    return out
