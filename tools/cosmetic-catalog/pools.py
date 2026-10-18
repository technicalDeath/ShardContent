"""Suggested reward pools: validate and build.

Source: ShardContent/docs/cosmetic-rewards/pools/<pool>.json, one file per pool:

  {"pool": "wanted-curator-deceit", "system": "wanted-curator", "notes": "...",
   "entries": [{"id": "CR-DNG-004", "tier": "easy", "why": "one short line"}]}

  python pools.py validate            -> structure + rule checks (exit 1 on errors)
  python pools.py build               -> Reward-Pools.md and reward-pools.json (needs the built cosmetic-rewards.json)

Rules checked (from the Hot-Zones plan: Nemesis 6.1, Wanted 20.6A, Shipwreck, Expedition 15.12A):
  * every id exists in the catalog and is not retired
  * an id belongs to at most one pool (no design is reused between systems, towns or dungeons)
  * nemesis-species-trophies: one entry per species (field "species"), at least 30 species
  * wanted-curator-<dungeon>: field "tier" in easy|medium|hard|boss; every tier present; 5-8 entries
  * shipwreck-decor: field "rarity" in uncommon|scarce|rare|extremely-rare; 8-12 entries; every rarity present
  * expedition-<town>: field "role" core|rare; 6-8 entries; 2-4 core; at least 4 rare
  * pilgrimage-shrine-tokens: field "shrine"
  * no id may also be a gold-sink decoration (gold-sink/picks.json): those are for sale only
  * art-only systems may use any other pool name; they only get the generic checks
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import catalog  # noqa: E402

DOCS = catalog.DOCS
POOLS = os.path.join(DOCS, "pools")
CATALOG_JSON = os.path.join(DOCS, "cosmetic-rewards.json")


def load_pools():
    out = []
    if not os.path.isdir(POOLS):
        return out
    for name in sorted(os.listdir(POOLS)):
        if name.endswith(".json"):
            with open(os.path.join(POOLS, name), encoding="utf-8") as f:
                data = json.load(f)
            data["_file"] = name
            out.append(data)
    return out


def live_ids():
    ids = {}
    for e in catalog.load_all():
        if e.get("id") and not e.get("retired"):
            ids[e["id"]] = e
    return ids


def validate():
    errors, warnings = [], []
    ids = live_ids()
    owner = {}
    pools = load_pools()
    names = set()
    for p in pools:
        n = p.get("pool")
        where = p["_file"]
        if not n or n + ".json" != p["_file"]:
            errors.append("%s: pool name must equal the file name" % where)
            continue
        if n in names:
            errors.append("%s: duplicate pool" % where)
        names.add(n)
        entries = p.get("entries", [])
        if not entries:
            errors.append("%s: no entries" % n)
            continue
        for en in entries:
            rid = en.get("id")
            if rid not in ids:
                errors.append("%s: %s is not a live catalog id" % (n, rid))
                continue
            if rid in owner and owner[rid] != n:
                errors.append("%s: %s is already in pool %s" % (n, rid, owner[rid]))
            owner[rid] = n
        if len({en["id"] for en in entries}) != len(entries):
            errors.append("%s: the same id is listed twice" % n)

        if n == "nemesis-species-trophies":
            sp = [en.get("species") for en in entries]
            if None in sp or len(set(sp)) != len(sp):
                errors.append("%s: every entry needs a unique 'species'" % n)
            if len(set(sp)) < 30:
                errors.append("%s: only %d species (need >= 30)" % (n, len(set(sp))))
        elif n.startswith("wanted-curator-"):
            tiers = {"easy", "medium", "hard", "boss"}
            got = {en.get("tier") for en in entries}
            if not got <= tiers:
                errors.append("%s: tier must be one of %s" % (n, sorted(tiers)))
            if got != tiers:
                errors.append("%s: missing tiers %s" % (n, sorted(tiers - got)))
            if not (5 <= len(entries) <= 8):
                errors.append("%s: %d entries (want 5-8)" % (n, len(entries)))
        elif n == "shipwreck-decor":
            tiers = {"uncommon", "scarce", "rare", "extremely-rare"}
            got = {en.get("rarity") for en in entries}
            if not got <= tiers or got != tiers:
                errors.append("%s: rarity must cover exactly %s (got %s)" % (n, sorted(tiers), sorted(got)))
            if not (8 <= len(entries) <= 12):
                errors.append("%s: %d entries (want 8-12)" % (n, len(entries)))
        elif n.startswith("expedition-"):
            roles = [en.get("role") for en in entries]
            if any(r not in ("core", "rare") for r in roles):
                errors.append("%s: role must be core or rare" % n)
            if not (6 <= len(entries) <= 8):
                errors.append("%s: %d designs (want 6-8)" % (n, len(entries)))
            if not (2 <= roles.count("core") <= 4):
                errors.append("%s: %d core designs (want 2-4)" % (n, roles.count("core")))
            if roles.count("rare") < 4:
                errors.append("%s: %d rare designs (want >= 4)" % (n, roles.count("rare")))
        elif n == "pilgrimage-shrine-tokens":
            if any(not en.get("shrine") for en in entries):
                errors.append("%s: every entry needs a 'shrine'" % n)
        # soft checks
        for en in entries:
            e = ids.get(en.get("id"))
            if e and e["era"]["grade"] == "C":
                warnings.append("%s: %s is era grade C (needs an audit before use)" % (n, en["id"]))
    # the gold-sink decorations (Design Proposal 3) are for sale only: no reward pool may hand one out
    sink = os.path.join(DOCS, "gold-sink", "picks.json")
    if os.path.exists(sink):
        with open(sink, encoding="utf-8") as f:
            picked = {rid for tiers in json.load(f)["picks"].values() for rids in tiers.values() for rid in rids}
        for rid in sorted(picked & set(owner)):
            errors.append("%s is a gold-sink decoration and cannot also be in pool %s" % (rid, owner[rid]))
    print("pools: %d, ids used: %d of %d" % (len(pools), len(owner), len(ids)))
    for m in errors:
        print("  ERROR  " + m)
    for m in warnings:
        print("  warn   " + m)
    return 1 if errors else 0


def build():
    if validate():
        raise SystemExit("fix pool errors first")
    ids = live_ids()
    pools = load_pools()
    owner = {en["id"]: p["pool"] for p in pools for en in p["entries"]}
    unallocated = [i for i in ids if i not in owner]
    lines = []
    out = lines.append
    out("# Suggested Reward Pools")
    out("")
    out("*Generated by `ShardContent/tools/cosmetic-catalog/pools.py build` from `pools/*.json`. **A proposal, not a ruling**: nothing here is approved or built. "
        "Each pool follows the rules of the system in the Hot-Zones plan it is meant for; any id sits in at most one pool.*")
    out("")
    out("| Pool | System | Entries |")
    out("| --- | --- | ---: |")
    for p in pools:
        out("| [%s](#%s) | %s | %d |" % (p["pool"], p["pool"], p.get("system", ""), len(p["entries"])))
    out("| *unallocated (general stock)* | any | %d |" % len(unallocated))
    out("")
    for p in pools:
        out('<a id="%s"></a>' % p["pool"])
        out("## %s" % p["pool"])
        out("")
        if p.get("notes"):
            out(p["notes"])
            out("")
        keys = []
        for en in p["entries"]:
            for k in en:
                if k not in ("id", "why") and k not in keys:
                    keys.append(k)
        out("| Id | Picture | Name | %s | Tier | Why |" % " | ".join(keys) if keys else "| Id | Picture | Name | Tier | Why |")
        out("| --- | --- | --- | %s--- | --- |" % ("--- | " * len(keys)))
        for en in p["entries"]:
            e = ids[en["id"]]
            out("| `%s` | <img src=\"images/%s/%s.png\" height=\"56\"> | %s | %s%s | %s |" % (
                e["id"], e["category"], e["id"], e["name"], "".join("%s | " % en.get(k, "") for k in keys), e["tier"],
                en.get("why", "")))
        out("")
    out("## Unallocated")
    out("")
    out("Rewards not in any pool (%d) stay available as general stock for any system that wants them. Their ids are in `cosmetic-rewards.json`." % len(unallocated))
    out("")
    with open(os.path.join(DOCS, "Reward-Pools.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    doc = {"schema": "uo-rekindled-reward-pools/1", "pools": [{k: v for k, v in p.items() if k != "_file"} for p in pools],
           "unallocated": unallocated}
    with open(os.path.join(DOCS, "reward-pools.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("built Reward-Pools.md and reward-pools.json")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "validate":
        sys.exit(validate())
    if cmd == "build":
        build()
    else:
        print(__doc__)
