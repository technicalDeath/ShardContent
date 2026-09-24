using System.Globalization;
using System.Text.Json.Serialization;
using Server;
using Server.Json;
using Server.Logging;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Owns the shard policy document. This is deliberately separate from ModernUO's engine settings:
/// it records the approved baseline and exposes only rules that the shard content has verified.
/// </summary>
public static class ShardRulesConfiguration
{
    public const string RelativePath = "Configuration/shard-rules.json";
    private static readonly ILogger Logger = LogFactory.GetLogger(typeof(ShardRulesConfiguration));

    public static ShardRules Settings { get; private set; } = null!;

    public static void Load()
    {
        var path = Path.Combine(Server.Core.BaseDirectory, RelativePath);
        var settings = JsonConfig.Deserialize<ShardRules>(path);

        if (settings is null)
        {
            throw new InvalidOperationException($"Shard rules configuration is missing or invalid: {path}");
        }

        var errors = Validate(settings);

        if (errors.Count > 0)
        {
            throw new InvalidOperationException(
                $"Shard rules configuration failed validation:{Environment.NewLine}- {string.Join(Environment.NewLine + "- ", errors)}"
            );
        }

        Settings = settings;
        Logger.Information(
            "Loaded shard rules schema {SchemaVersion}: {Era} / {Maps}; caps {TotalSkillCap}/{IndividualSkillCap}/{StatCap}; deferred features: {DeferredFeatures}.",
            settings.SchemaVersion,
            settings.World.Era,
            string.Join(", ", settings.World.EnabledMaps),
            settings.Character.TotalSkillCap,
            settings.Character.IndividualSkillCap,
            settings.Character.StatCap,
            string.Join(", ", settings.FeatureFlags.EnabledNames())
        );
    }

    public static IReadOnlyList<string> Validate(ShardRules rules)
    {
        var errors = new List<string>();

        if (rules.SchemaVersion != 1)
        {
            errors.Add($"schemaVersion must be 1, but was {rules.SchemaVersion}.");
        }

        if (string.IsNullOrWhiteSpace(rules.PinnedModernUoCommit) ||
            rules.PinnedModernUoCommit.Length != 40 ||
            !rules.PinnedModernUoCommit.All(Uri.IsHexDigit))
        {
            errors.Add("pinnedModernUoCommit must be a 40-character Git commit SHA.");
        }

        if (!string.Equals(rules.World.Era, "UOR", StringComparison.OrdinalIgnoreCase))
        {
            errors.Add("world.era must be UOR for the Alpha 1 baseline.");
        }

        if (rules.World.EnabledMaps.Count != 1 ||
            !string.Equals(rules.World.EnabledMaps[0], "Felucca", StringComparison.OrdinalIgnoreCase))
        {
            errors.Add("world.enabledMaps must contain only Felucca; the Lost Lands are part of that facet.");
        }

        if (rules.Character.TotalSkillCap != 700 || rules.Character.IndividualSkillCap != 100 || rules.Character.StatCap != 225)
        {
            errors.Add("character caps must be 700 total skill, 100 individual skill, and 225 stats.");
        }

        if (rules.Combat.AutomaticWeaponProcs || rules.Combat.WrestlingStun || rules.Combat.WrestlingDisarm)
        {
            errors.Add("automatic UOR weapon procs and Wrestling Stun/Disarm must remain disabled.");
        }

        if (rules.FeatureFlags.HotZones || rules.FeatureFlags.CoolZones ||
            rules.FeatureFlags.HousingGeography || rules.FeatureFlags.Expeditions || rules.FeatureFlags.Pilgrimage ||
            rules.FeatureFlags.RoadSpeed || rules.FeatureFlags.RetentionContent)
        {
            errors.Add("Alpha 3+ shard feature flags must remain disabled until their phase is approved.");
        }

        if (rules.FeatureFlags.AutomaticMurderAdjudication && !rules.FeatureFlags.SafeWorld)
        {
            errors.Add("automaticMurderAdjudication requires safeWorld.");
        }

        if (rules.FeatureFlags.TheftProtection && !rules.FeatureFlags.SafeWorld)
        {
            errors.Add("theftProtection requires safeWorld so crime protections share one law policy.");
        }

        if (rules.FeatureFlags.KnockedOut && (!rules.FeatureFlags.SafeWorld || !rules.FeatureFlags.AutomaticMurderAdjudication))
        {
            errors.Add("knockedOut requires safeWorld and automaticMurderAdjudication.");
        }

        ValidatePolygons(
            rules.TheftRegions.BankProtectionPolygons,
            "bankProtectionPolygons",
            rules.World.EnabledMaps,
            errors
        );
        ValidatePolygons(
            rules.TheftRegions.CoolDungeonPolygons,
            "coolDungeonPolygons",
            rules.World.EnabledMaps,
            errors
        );

        var alpha2Enabled = rules.FeatureFlags.SafeWorld || rules.FeatureFlags.AutomaticMurderAdjudication ||
                            rules.FeatureFlags.TheftProtection || rules.FeatureFlags.KnockedOut;
        if (alpha2Enabled && !rules.Alpha2EnablementAcknowledged)
        {
            errors.Add("alpha2EnablementAcknowledged must be true before enabling any Alpha 2 feature flag.");
        }

        return errors;
    }

    private static void ValidatePolygons(
        IEnumerable<TheftPolygonDefinition> polygons,
        string name,
        IReadOnlyCollection<string> enabledMaps,
        ICollection<string> errors
    )
    {
        var index = 0;
        foreach (var polygon in polygons)
        {
            if (string.IsNullOrWhiteSpace(polygon.Map) || polygon.Points.Count < 3)
            {
                errors.Add($"theftRegions.{name}[{index}] must specify a map and at least three points.");
            }
            else if (!enabledMaps.Any(map => string.Equals(map, polygon.Map, StringComparison.OrdinalIgnoreCase)))
            {
                errors.Add(
                    $"theftRegions.{name}[{index}] references map '{polygon.Map}', which is not enabled by world.enabledMaps."
                );
            }

            index++;
        }
    }

    public static IEnumerable<string> Describe()
    {
        var rules = Settings;
        yield return $"Shard rules schema: {rules.SchemaVersion}";
        yield return $"Pinned ModernUO commit: {rules.PinnedModernUoCommit}";
        yield return $"Era/maps: {rules.World.Era} / {string.Join(", ", rules.World.EnabledMaps)}";
        yield return $"Alpha 2 enablement acknowledged: {rules.Alpha2EnablementAcknowledged}.";
        yield return string.Format(
            CultureInfo.InvariantCulture,
            "Character caps: {0} skill total, {1} per skill, {2} stats",
            rules.Character.TotalSkillCap,
            rules.Character.IndividualSkillCap,
            rules.Character.StatCap
        );
        yield return "Combat specials: automatic weapon procs, Wrestling Stun, and Wrestling Disarm disabled";
        yield return $"Configured feature flags enabled: {string.Join(", ", rules.FeatureFlags.EnabledNames())}";
    }
}

public sealed class ShardRules
{
    [JsonPropertyName("schemaVersion")]
    public int SchemaVersion { get; set; }

    [JsonPropertyName("pinnedModernUoCommit")]
    public string PinnedModernUoCommit { get; set; } = string.Empty;

    [JsonPropertyName("world")]
    public WorldRules World { get; set; } = new();

    [JsonPropertyName("character")]
    public CharacterRules Character { get; set; } = new();

    [JsonPropertyName("combat")]
    public CombatRules Combat { get; set; } = new();

    [JsonPropertyName("alpha2EnablementAcknowledged")]
    public bool Alpha2EnablementAcknowledged { get; set; }

    [JsonPropertyName("theftRegions")]
    public TheftRegionRules TheftRegions { get; set; } = new();

    [JsonPropertyName("featureFlags")]
    public DeferredFeatureFlags FeatureFlags { get; set; } = new();
}

public sealed class WorldRules
{
    [JsonPropertyName("era")]
    public string Era { get; set; } = string.Empty;

    [JsonPropertyName("enabledMaps")]
    public List<string> EnabledMaps { get; set; } = [];
}

public sealed class CharacterRules
{
    [JsonPropertyName("totalSkillCap")]
    public int TotalSkillCap { get; set; }

    [JsonPropertyName("individualSkillCap")]
    public int IndividualSkillCap { get; set; }

    [JsonPropertyName("statCap")]
    public int StatCap { get; set; }
}

public sealed class CombatRules
{
    [JsonPropertyName("automaticWeaponProcs")]
    public bool AutomaticWeaponProcs { get; set; }

    [JsonPropertyName("wrestlingStun")]
    public bool WrestlingStun { get; set; }

    [JsonPropertyName("wrestlingDisarm")]
    public bool WrestlingDisarm { get; set; }
}

public sealed class TheftRegionRules
{
    [JsonPropertyName("bankProtectionPolygons")]
    public List<TheftPolygonDefinition> BankProtectionPolygons { get; set; } = [];

    [JsonPropertyName("coolDungeonPolygons")]
    public List<TheftPolygonDefinition> CoolDungeonPolygons { get; set; } = [];
}

public sealed class TheftPolygonDefinition
{
    [JsonPropertyName("map")]
    public string Map { get; set; } = string.Empty;

    [JsonPropertyName("points")]
    public List<TheftPoint> Points { get; set; } = [];
}

public sealed class TheftPoint
{
    [JsonPropertyName("x")]
    public int X { get; set; }

    [JsonPropertyName("y")]
    public int Y { get; set; }
}

public sealed class DeferredFeatureFlags
{
    [JsonPropertyName("safeWorld")]
    public bool SafeWorld { get; set; }

    [JsonPropertyName("automaticMurderAdjudication")]
    public bool AutomaticMurderAdjudication { get; set; }

    [JsonPropertyName("theftProtection")]
    public bool TheftProtection { get; set; }

    [JsonPropertyName("knockedOut")]
    public bool KnockedOut { get; set; }

    [JsonPropertyName("hotZones")]
    public bool HotZones { get; set; }

    [JsonPropertyName("coolZones")]
    public bool CoolZones { get; set; }

    [JsonPropertyName("housingGeography")]
    public bool HousingGeography { get; set; }

    [JsonPropertyName("expeditions")]
    public bool Expeditions { get; set; }

    [JsonPropertyName("pilgrimage")]
    public bool Pilgrimage { get; set; }

    [JsonPropertyName("roadSpeed")]
    public bool RoadSpeed { get; set; }

    [JsonPropertyName("retentionContent")]
    public bool RetentionContent { get; set; }

    public IEnumerable<string> EnabledNames()
    {
        if (SafeWorld) yield return nameof(SafeWorld);
        if (AutomaticMurderAdjudication) yield return nameof(AutomaticMurderAdjudication);
        if (TheftProtection) yield return nameof(TheftProtection);
        if (KnockedOut) yield return nameof(KnockedOut);
        if (HotZones) yield return nameof(HotZones);
        if (CoolZones) yield return nameof(CoolZones);
        if (HousingGeography) yield return nameof(HousingGeography);
        if (Expeditions) yield return nameof(Expeditions);
        if (Pilgrimage) yield return nameof(Pilgrimage);
        if (RoadSpeed) yield return nameof(RoadSpeed);
        if (RetentionContent) yield return nameof(RetentionContent);
        if (!SafeWorld && !AutomaticMurderAdjudication && !TheftProtection && !KnockedOut && !HotZones && !CoolZones && !HousingGeography && !Expeditions && !Pilgrimage && !RoadSpeed && !RetentionContent)
        {
            yield return "none";
        }
    }
}
