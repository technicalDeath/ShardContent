using System.Text.Json.Serialization;
using Server;
using Server.Collections;
using Server.Engines.Spawners;
using Server.Mobiles;
using Server.Regions;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Town guards kill monsters (docs/Town-Guards-Monsters-Evidence.md), behind <c>featureFlags.townGuardsKillMonsters</c>. The owner's rulings
/// (2026-10-16): "Monsters in town should be killed by guards regardless of who attacks first", but "guards only come if a player calls them",
/// only creatures that attack on sight count, and "Shrink the guard zone. Monsters should not spawn inside one", "only where there are no vendors".
/// Stock guards act only on criminals and murderers, and a monster turns criminal only by hurting someone who had not struck it, so a player
/// who fought back got no help. Here such a creature is a guard target wherever guards work, as a murderer is, so a "guards" call kills it
/// (the engine hook <see cref="GuardedRegion.AlwaysGuardTarget"/>). The zones shrink by the configured <c>townGuards.unguardedAreas</c>,
/// registered above the towns so they stop being town at all; they take effect at server start.
/// </summary>
public static class TownGuardsService
{
    /// <summary>Above the towns' 50, so a point in an unguarded area belongs to it and to no town region.</summary>
    public const int UnguardedPriority = 51;

    private static bool _configured;
    private static bool _initialized;
    private static readonly List<Region> Unguarded = [];

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.TownGuardsKillMonsters == true;

    public static TownGuardRules Rules => ShardRulesConfiguration.Settings?.TownGuards ?? new TownGuardRules();

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        GuardedRegion.AlwaysGuardTarget = IsTarget;
        BaseSpawner.MobileSpawnPositionAllowed = SpawnAllowed;
    }

    /// <summary>
    /// The owner's "Monsters should not spawn inside one" (2026-10-16), and his yes (2026-10-17) to the spawners outside a zone whose range reaches
    /// into it: a spot where guards work is refused to a creature that would be a guard target there, so the spawner draws another.
    /// </summary>
    public static bool SpawnAllowed(BaseSpawner spawner, Mobile m, Map map, Point3D spot) =>
        m is not BaseCreature creature ||
        !ShouldTarget(
            Enabled,
            true,
            creature.Controlled || creature.Summoned || creature.ControlMaster is not null,
            creature.IsInvulnerable || creature.Blessed,
            creature is BaseVendor || creature.InitialInnocent,
            creature.FightMode,
            GuardsWorkAt(spot, map)
        );

    // after the regions and the world have loaded
    public static void Initialize()
    {
        if (_initialized || !Enabled)
        {
            return;
        }

        _initialized = true;
        RegisterUnguardedAreas(Rules);
    }

    /// <summary>The rule, free of the game: a live wild creature that attacks on sight, not a pet, summons or townsperson, where guards work.</summary>
    public static bool ShouldTarget(
        bool enabled, bool alive, bool controlledOrSummoned, bool invulnerable, bool townsperson, FightMode mode, bool guardsWorkWhereItStands
    ) =>
        enabled && alive && !controlledOrSummoned && !invulnerable && !townsperson && AttacksOnSight(mode) && guardsWorkWhereItStands;

    /// <summary>Closest, Strongest and Weakest pick a target unprovoked; None never fights and Aggressor (every town animal, vendor, hireling and
    /// escort) and Evil fight only someone who struck them, or a murderer.</summary>
    public static bool AttacksOnSight(FightMode mode) => mode is FightMode.Closest or FightMode.Strongest or FightMode.Weakest;

    public static bool IsTarget(Mobile m, GuardedRegion region) =>
        m is BaseCreature creature &&
        ShouldTarget(
            Enabled,
            creature.Alive && !creature.Deleted,
            creature.Controlled || creature.Summoned || creature.ControlMaster is not null,
            creature.IsInvulnerable || creature.Blessed,
            creature is BaseVendor || creature.InitialInnocent,
            creature.FightMode,
            GuardsWorkAt(creature)
        );

    // the region at its feet, so an unguarded area that overrides the town counts even before the mobile's region is refreshed
    private static bool GuardsWorkAt(Mobile m) => GuardsWorkAt(m.Location, m.Map);

    private static bool GuardsWorkAt(Point3D p, Map map) =>
        map is not null && map != Map.Internal && Region.Find(p, map)?.GetRegion<GuardedRegion>() is { } guarded && !guarded.IsDisabled();

    public static void RegisterUnguardedAreas(TownGuardRules rules)
    {
        foreach (var area in rules.UnguardedAreas)
        {
            var map = Map.Parse(area.Map);

            if (map is null)
            {
                continue;
            }

            var rects = area.Rectangles
                .Select(r => new Rectangle3D(new Point3D(r.X1, r.Y1, Region.MinZ), new Point3D(r.X2, r.Y2, Region.MaxZ)))
                .ToArray();

            var region = new NoHousingRegion(area.Name, map, UnguardedPriority, rects);
            region.Register();
            Unguarded.Add(region);

            // whoever stands there keeps the town as its region until it next moves
            foreach (var r in area.Rectangles)
            {
                using var standing = PooledRefList<Mobile>.Create();

                foreach (var m in map.GetMobilesInBounds(new Rectangle2D(r.X1, r.Y1, r.X2 - r.X1, r.Y2 - r.Y1)))
                {
                    standing.Add(m);
                }

                foreach (var m in standing)
                {
                    m.UpdateRegion();
                }
            }
        }
    }

    public static IEnumerable<string> DescribeStatus(Mobile from)
    {
        var rules = Rules;
        yield return $"Town guards kill monsters: {(Enabled ? "on" : "off")} (featureFlags.townGuardsKillMonsters).";
        yield return "Guards come only when someone calls them; the call kills every such monster within its range in the town.";

        if (Unguarded.Count == 0)
        {
            yield return Enabled
                ? "No unguarded areas are registered (they register at server start)."
                : "Unguarded areas: none while the flag is off; configured: " + string.Join(", ", rules.UnguardedAreas.Select(a => a.Name)) + ".";
        }
        else
        {
            foreach (var region in Unguarded)
            {
                yield return $"Unguarded area '{region.Name}' on {region.Map}: {region.Area.Length} rectangle(s).";
            }
        }

        if (from.Map is { } map)
        {
            var here = Region.Find(from.Location, map);
            var guarded = here?.GetRegion<GuardedRegion>();
            yield return guarded is null
                ? $"Here ({here?.Name ?? "no region"}): not guarded."
                : $"Here ({guarded.Name ?? here?.Name}): guarded{(guarded.IsDisabled() ? ", but its guards are disabled" : "")}.";
        }
    }

    public static void Validate(TownGuardRules rules, List<string> errors)
    {
        var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var area in rules.UnguardedAreas)
        {
            if (string.IsNullOrWhiteSpace(area.Name) || !names.Add(area.Name))
            {
                errors.Add("townGuards.unguardedAreas must have unique non-empty names.");
            }

            if (!string.Equals(area.Map, "Felucca", StringComparison.OrdinalIgnoreCase))
            {
                errors.Add($"townGuards.unguardedAreas '{area.Name}' must be on Felucca.");
            }

            if (area.Rectangles.Count == 0 || area.Rectangles.Any(r => r.X2 <= r.X1 || r.Y2 <= r.Y1))
            {
                errors.Add($"townGuards.unguardedAreas '{area.Name}' needs at least one rectangle with x2 > x1 and y2 > y1.");
            }
        }
    }
}

public sealed class TownGuardRules
{
    /// <summary>Parts of the towns' regions that are not guarded: vendor-free ground where monsters spawn.</summary>
    [JsonPropertyName("unguardedAreas")]
    public List<UnguardedArea> UnguardedAreas { get; set; } = [];
}

public sealed class UnguardedArea
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("map")]
    public string Map { get; set; } = "Felucca";

    /// <summary>The ends are not included, as in Data/regions.json.</summary>
    [JsonPropertyName("rectangles")]
    public List<UnguardedRectangle> Rectangles { get; set; } = [];
}

public sealed class UnguardedRectangle
{
    [JsonPropertyName("x1")]
    public int X1 { get; set; }

    [JsonPropertyName("y1")]
    public int Y1 { get; set; }

    [JsonPropertyName("x2")]
    public int X2 { get; set; }

    [JsonPropertyName("y2")]
    public int Y2 { get; set; }

    public bool Contains(int x, int y) => x >= X1 && x < X2 && y >= Y1 && y < Y2;
}
