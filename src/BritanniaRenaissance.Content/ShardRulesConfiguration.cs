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

        if (rules.FeatureFlags.CoolZones)
        {
            errors.Add("coolZones is reserved for Beta 2 after single-dungeon rotation is implemented.");
        }

        if (rules.FeatureFlags.HotZones && !rules.Alpha3EnablementAcknowledged)
        {
            errors.Add("hotZones requires alpha3EnablementAcknowledged.");
        }

        if (rules.FeatureFlags.SkillBank && !rules.Alpha3EnablementAcknowledged)
        {
            errors.Add("skillBank requires alpha3EnablementAcknowledged.");
        }

        SkillGainCurveService.Validate(rules.SkillGain, errors);
        MasteryRules.Validate(rules.Mastery, errors);
        BackpackWardVendor.Validate(rules.WardVendor, errors);
        BackpackWardCraft.Validate(rules.WardCraft, errors);
        CampingService.Validate(rules.Camping, errors);
        StarterWeightBudget.Validate(rules.StarterWeight, errors);

        if (rules.FeatureFlags.HousingGeography || rules.FeatureFlags.Expeditions || rules.FeatureFlags.Pilgrimage ||
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

        if (rules.FeatureFlags.KnockedOut && !rules.FeatureFlags.SafeWorld)
        {
            errors.Add("knockedOut requires safeWorld.");
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

        var hotRegionNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var region in rules.HotZones.PermanentOutdoorRegions)
        {
            if (string.IsNullOrWhiteSpace(region.Name) || !hotRegionNames.Add(region.Name))
            {
                errors.Add("hotZones.permanentOutdoorRegions must have unique non-empty names.");
            }

            if (region.Points.Count < 3 ||
                !rules.World.EnabledMaps.Any(map => string.Equals(map, region.Map, StringComparison.OrdinalIgnoreCase)))
            {
                errors.Add($"hotZones.permanentOutdoorRegions '{region.Name}' needs at least three points on an enabled map.");
            }
        }

        if (rules.FeatureFlags.HotZones &&
            (!hotRegionNames.Contains("FireIsland") || !hotRegionNames.Contains("BuccaneersDenIsland")))
        {
            errors.Add("hotZones requires surveyed FireIsland and BuccaneersDenIsland outdoor regions.");
        }

        foreach (var dungeon in rules.HotZones.DungeonRegions)
        {
            if (string.IsNullOrWhiteSpace(dungeon.Name) || !hotRegionNames.Add(dungeon.Name))
            {
                errors.Add("hotZones.dungeonRegions must have non-empty names, unique among all Hot Zone regions.");
            }

            if (!rules.World.EnabledMaps.Any(map => string.Equals(map, dungeon.Map, StringComparison.OrdinalIgnoreCase)))
            {
                errors.Add($"hotZones.dungeonRegions '{dungeon.Name}' must be on an enabled map.");
            }
        }

        if (rules.FeatureFlags.HythlothHotZone && !rules.FeatureFlags.HotZones)
        {
            errors.Add("hythlothHotZone requires hotZones.");
        }

        if (rules.FeatureFlags.HythlothHotZone &&
            !rules.HotZones.DungeonRegions.Any(d => string.Equals(d.Name, "Hythloth", StringComparison.OrdinalIgnoreCase)))
        {
            errors.Add("hythlothHotZone requires a Hythloth entry in hotZones.dungeonRegions.");
        }

        if (rules.FeatureFlags.HousingGeography && !hotRegionNames.Contains("BuccaneersDenIsland"))
        {
            errors.Add("housingGeography requires the surveyed BuccaneersDenIsland no-housing polygon.");
        }

        var housingNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var housingSequences = new HashSet<int>();
        foreach (var district in rules.Housing.ResidentialDistricts)
        {
            ValidateHousingRegion(district.Name, district.Map, district.Points,
                "housing.residentialDistricts", housingNames, errors);
            if (!district.Name.StartsWith("GreaterBritain", StringComparison.OrdinalIgnoreCase) ||
                district.Sequence <= 0 || !housingSequences.Add(district.Sequence) || district.SoftCapacity <= 0)
            {
                errors.Add($"housing.residentialDistricts '{district.Name}' requires a GreaterBritain name, unique positive sequence and positive soft capacity.");
            }
        }

        var orderedDistricts = rules.Housing.ResidentialDistricts.OrderBy(district => district.Sequence).ToArray();
        var closedDistrictSeen = false;
        for (var i = 0; i < orderedDistricts.Length; i++)
        {
            var district = orderedDistricts[i];
            if (district.Sequence != i + 1 || closedDistrictSeen && district.Open)
            {
                errors.Add("housing.residentialDistricts must have a contiguous sequence and open only an initial prefix.");
                break;
            }

            closedDistrictSeen |= !district.Open;
        }

        foreach (var region in rules.Housing.FireIslandResidentialRegions)
        {
            ValidateHousingRegion(region.Name, region.Map, region.Points,
                "housing.fireIslandResidentialRegions", housingNames, errors);
        }

        foreach (var region in rules.Housing.ProtectedRegions)
        {
            ValidateHousingRegion(region.Name, region.Map, region.Points,
                "housing.protectedRegions", housingNames, errors);
        }

        if (rules.FeatureFlags.HousingGeography &&
            (!rules.Housing.ResidentialDistricts.Any(district => district.Open) ||
             rules.Housing.FireIslandResidentialRegions.Count == 0 ||
             rules.Housing.ProtectedRegions.Count == 0))
        {
            errors.Add("housingGeography requires surveyed open Greater Britain, Fire Island residential, and protected regions.");
        }

        var alpha2Enabled = rules.FeatureFlags.SafeWorld || rules.FeatureFlags.AutomaticMurderAdjudication ||
                            rules.FeatureFlags.TheftProtection || rules.FeatureFlags.KnockedOut;
        if (alpha2Enabled && !rules.Alpha2EnablementAcknowledged)
        {
            errors.Add("alpha2EnablementAcknowledged must be true before enabling any Alpha 2 feature flag.");
        }

        if (rules.FeatureFlags.Alpha3StartingStats && !rules.Alpha3EnablementAcknowledged)
        {
            errors.Add("alpha3EnablementAcknowledged must be true before enabling Alpha 3 starting stats.");
        }

        if (rules.FeatureFlags.Alpha3StarterScissors && !rules.Alpha3EnablementAcknowledged)
        {
            errors.Add("alpha3EnablementAcknowledged must be true before enabling Alpha 3 starter scissors.");
        }

        if (rules.FeatureFlags.Alpha3StarterBag && !rules.Alpha3EnablementAcknowledged)
        {
            errors.Add("alpha3EnablementAcknowledged must be true before enabling the Alpha 3 starter bag.");
        }

        if (rules.FeatureFlags.Alpha3StarterGold && !rules.Alpha3EnablementAcknowledged)
        {
            errors.Add("alpha3EnablementAcknowledged must be true before enabling Alpha 3 starter gold.");
        }

        if (rules.FeatureFlags.Alpha3StarterCraftMaterials && !rules.Alpha3EnablementAcknowledged)
        {
            errors.Add("alpha3EnablementAcknowledged must be true before enabling Alpha 3 starter craft materials.");
        }

        if (rules.FeatureFlags.Alpha3StarterCombatGear && !rules.Alpha3EnablementAcknowledged)
        {
            errors.Add("alpha3EnablementAcknowledged must be true before enabling Alpha 3 starter combat gear.");
        }

        if (rules.SkillBank.CapacityTenths <= 0 || rules.SkillBank.CapacityTenths > 60000)
        {
            errors.Add("skillBank.capacityTenths must be between 1 and 60000.");
        }

        if (rules.Housing.RuralCostMultiplier is < 2m or > 5m)
        {
            errors.Add("housing.ruralCostMultiplier must be between 2.0 and 5.0.");
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

    private static void ValidateHousingRegion(
        string name, string map, IReadOnlyList<TheftPoint> points, string path,
        ISet<string> names, ICollection<string> errors
    )
    {
        if (string.IsNullOrWhiteSpace(name) || !names.Add(name) ||
            !string.Equals(map, "Felucca", StringComparison.OrdinalIgnoreCase) || points.Count < 3)
        {
            errors.Add($"{path} requires unique non-empty names and Felucca polygons with at least three points.");
        }
    }

    public static IEnumerable<string> Describe()
    {
        var rules = Settings;
        yield return $"Shard rules schema: {rules.SchemaVersion}";
        yield return $"Pinned ModernUO commit: {rules.PinnedModernUoCommit}";
        yield return $"Era/maps: {rules.World.Era} / {string.Join(", ", rules.World.EnabledMaps)}";
        yield return $"Alpha 2 enablement acknowledged: {rules.Alpha2EnablementAcknowledged}.";
        yield return $"Alpha 3 enablement acknowledged: {rules.Alpha3EnablementAcknowledged}.";
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

    [JsonPropertyName("alpha3EnablementAcknowledged")]
    public bool Alpha3EnablementAcknowledged { get; set; }

    [JsonPropertyName("theftRegions")]
    public TheftRegionRules TheftRegions { get; set; } = new();

    [JsonPropertyName("hotZones")]
    public OutdoorHotZoneRules HotZones { get; set; } = new();

    [JsonPropertyName("housing")]
    public HousingLandRules Housing { get; set; } = new();

    [JsonPropertyName("skillBank")]
    public SkillBankRules SkillBank { get; set; } = new();

    [JsonPropertyName("wardVendor")]
    public WardVendorRules WardVendor { get; set; } = new();

    [JsonPropertyName("wardCraft")]
    public WardCraftRules WardCraft { get; set; } = new();

    [JsonPropertyName("camping")]
    public CampingRules Camping { get; set; } = new();

    [JsonPropertyName("starterWeight")]
    public StarterWeightRules StarterWeight { get; set; } = new();

    [JsonPropertyName("skillGain")]
    public SkillGainRules SkillGain { get; set; } = new();

    [JsonPropertyName("mastery")]
    public MasteryRules Mastery { get; set; } = new();

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

public sealed class OutdoorHotZoneRules
{
    [JsonPropertyName("permanentOutdoorRegions")]
    public List<OutdoorHotRegionDefinition> PermanentOutdoorRegions { get; set; } = [];

    /// <summary>
    /// Stock dungeon regions that follow the ordinary Hot Zone rules as a whole (Beta 2a: Hythloth), behind
    /// <c>featureFlags.hythlothHotZone</c>. They are Hot Zones, not "Hot Dungeons": no reward premium.
    /// </summary>
    [JsonPropertyName("dungeonRegions")]
    public List<HotZoneDungeonRegion> DungeonRegions { get; set; } = [];
}

public sealed class HotZoneDungeonRegion
{
    /// <summary>The stock <c>DungeonRegion</c> name, as in Data/regions.json.</summary>
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("map")]
    public string Map { get; set; } = string.Empty;
}

public sealed class OutdoorHotRegionDefinition
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("map")]
    public string Map { get; set; } = string.Empty;

    [JsonPropertyName("points")]
    public List<TheftPoint> Points { get; set; } = [];
}

public sealed class HousingLandRules
{
    [JsonPropertyName("ruralCostMultiplier")]
    public decimal RuralCostMultiplier { get; set; } = 2m;

    [JsonPropertyName("residentialDistricts")]
    public List<HousingDistrictDefinition> ResidentialDistricts { get; set; } = [];

    [JsonPropertyName("fireIslandResidentialRegions")]
    public List<OutdoorHotRegionDefinition> FireIslandResidentialRegions { get; set; } = [];

    [JsonPropertyName("protectedRegions")]
    public List<OutdoorHotRegionDefinition> ProtectedRegions { get; set; } = [];
}

public sealed class HousingDistrictDefinition
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("map")]
    public string Map { get; set; } = string.Empty;

    [JsonPropertyName("points")]
    public List<TheftPoint> Points { get; set; } = [];

    [JsonPropertyName("sequence")]
    public int Sequence { get; set; }

    [JsonPropertyName("softCapacity")]
    public int SoftCapacity { get; set; }

    [JsonPropertyName("open")]
    public bool Open { get; set; }
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

/// <summary>
/// The skill-gain curve below Mastery (Beta 1). Each class is a list of bands: from the band's <c>from</c> skill value
/// (inclusive) until the next band, the stock gain probability is multiplied by <c>multiplier</c>. Below 10.0 the
/// stock unconditional gain is untouched and at 90.0 Mastery takes over, so only 10.0 to 90.0 is ever consulted.
/// </summary>
public sealed class SkillGainRules
{
    [JsonPropertyName("classes")]
    public Dictionary<string, List<SkillGainBand>> Classes { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>Every UOR skill (by <c>SkillName</c>) to exactly one class.</summary>
    [JsonPropertyName("skills")]
    public Dictionary<string, string> Skills { get; set; } = new(StringComparer.OrdinalIgnoreCase);
}

public sealed class SkillGainBand
{
    [JsonPropertyName("from")]
    public double From { get; set; }

    [JsonPropertyName("multiplier")]
    public double Multiplier { get; set; }
}

public sealed class SkillBankRules
{
    [JsonPropertyName("capacityTenths")]
    public int CapacityTenths { get; set; } = 3000;
}

/// <summary>
/// What Tinker vendors charge for a Backpack Ward, how many each shelf holds, and what they pay for an unused one (see
/// <see cref="BackpackWardVendor"/>). A stock of zero takes the Ward off sale; a buy-back price of zero stops the buy-back.
/// </summary>
public sealed class WardVendorRules
{
    [JsonPropertyName("price")]
    public int Price { get; set; } = 2000;

    [JsonPropertyName("stockPerVendor")]
    public int StockPerVendor { get; set; } = 20;

    [JsonPropertyName("buyBackPrice")]
    public int BuyBackPrice { get; set; } = 110;
}

/// <summary>
/// The Tinkering recipe for a Backpack Ward (see <see cref="BackpackWardCraft"/>): the skill range it is made across and
/// the iron ingots it costs. <c>enabled</c> false leaves the recipe out of the Tinkering menu.
/// </summary>
public sealed class WardCraftRules
{
    [JsonPropertyName("enabled")]
    public bool Enabled { get; set; } = true;

    [JsonPropertyName("minSkill")]
    public double MinSkill { get; set; } = 45.0;

    [JsonPropertyName("maxSkill")]
    public double MaxSkill { get; set; } = 95.0;

    [JsonPropertyName("ingots")]
    public int Ingots { get; set; } = 20;
}

/// <summary>
/// The numbers behind Rekindled camping (see <see cref="CampingService"/>). Everyone lights Kindling at a chance of at
/// least <c>skillFloor</c> percent (the floor affects lighting only), and a fire burns for <c>litBaseSeconds</c> plus
/// <c>litPerSkillSeconds</c> per point of the lighter's real Camping skill (the last <c>dimShare</c> of it dim), then
/// smoulders as embers for <c>emberBaseSeconds</c> plus <c>emberPerSkillSeconds</c> per point. Kindling used within a tile feeds a fire; a fire fed less than
/// <c>feedCooldownSeconds</c> ago is not fed again.
/// </summary>
public sealed class CampingRules
{
    [JsonPropertyName("skillFloor")]
    public double SkillFloor { get; set; } = 50.0;

    [JsonPropertyName("litBaseSeconds")]
    public double LitBaseSeconds { get; set; } = 100.0;

    [JsonPropertyName("litPerSkillSeconds")]
    public double LitPerSkillSeconds { get; set; } = 2.0;

    [JsonPropertyName("dimShare")]
    public double DimShare { get; set; } = 1.0 / 3.0;

    [JsonPropertyName("emberBaseSeconds")]
    public double EmberBaseSeconds { get; set; } = 60.0;

    [JsonPropertyName("emberPerSkillSeconds")]
    public double EmberPerSkillSeconds { get; set; } = 1.2;

    [JsonPropertyName("feedCooldownSeconds")]
    public double FeedCooldownSeconds { get; set; } = 5.0;

    [JsonPropertyName("starterKindling")]
    public int StarterKindling { get; set; } = 5;
}

/// <summary>
/// The weight budget for new characters' starting supplies (see <see cref="StarterWeightBudget"/>). A character whose load is
/// above <c>maxLoadPercent</c> of its carry limit has its bulk supply stacks scaled down together to fit, each keeping at
/// least <c>minimumUnits</c>. <c>enabled</c> false leaves the supplies at the quantities the Phase H rulings listed.
/// </summary>
public sealed class StarterWeightRules
{
    [JsonPropertyName("enabled")]
    public bool Enabled { get; set; } = true;

    [JsonPropertyName("maxLoadPercent")]
    public int MaxLoadPercent { get; set; } = 85;

    [JsonPropertyName("minimumUnits")]
    public int MinimumUnits { get; set; } = 10;
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

    [JsonPropertyName("alpha3StartingStats")]
    public bool Alpha3StartingStats { get; set; }

    [JsonPropertyName("alpha3StarterScissors")]
    public bool Alpha3StarterScissors { get; set; }

    [JsonPropertyName("alpha3StarterBag")]
    public bool Alpha3StarterBag { get; set; }

    [JsonPropertyName("alpha3StarterGold")]
    public bool Alpha3StarterGold { get; set; }

    [JsonPropertyName("alpha3StarterCraftMaterials")]
    public bool Alpha3StarterCraftMaterials { get; set; }

    [JsonPropertyName("alpha3StarterCombatGear")]
    public bool Alpha3StarterCombatGear { get; set; }

    [JsonPropertyName("skillBank")]
    public bool SkillBank { get; set; }

    [JsonPropertyName("petRestrictions")]
    public bool PetRestrictions { get; set; }

    [JsonPropertyName("skillGainCurve")]
    public bool SkillGainCurve { get; set; }

    [JsonPropertyName("hythlothHotZone")]
    public bool HythlothHotZone { get; set; }

    [JsonPropertyName("harvestAutoRepeat")]
    public bool HarvestAutoRepeat { get; set; }

    [JsonPropertyName("actionAutoRepeat")]
    public bool ActionAutoRepeat { get; set; }

    [JsonPropertyName("campingStarterKit")]
    public bool CampingStarterKit { get; set; }

    [JsonPropertyName("campingFires")]
    public bool CampingFires { get; set; }

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
        if (Alpha3StartingStats) yield return nameof(Alpha3StartingStats);
        if (Alpha3StarterScissors) yield return nameof(Alpha3StarterScissors);
        if (Alpha3StarterBag) yield return nameof(Alpha3StarterBag);
        if (Alpha3StarterGold) yield return nameof(Alpha3StarterGold);
        if (Alpha3StarterCraftMaterials) yield return nameof(Alpha3StarterCraftMaterials);
        if (Alpha3StarterCombatGear) yield return nameof(Alpha3StarterCombatGear);
        if (SkillBank) yield return nameof(SkillBank);
        if (PetRestrictions) yield return nameof(PetRestrictions);
        if (SkillGainCurve) yield return nameof(SkillGainCurve);
        if (HythlothHotZone) yield return nameof(HythlothHotZone);
        if (HarvestAutoRepeat) yield return nameof(HarvestAutoRepeat);
        if (ActionAutoRepeat) yield return nameof(ActionAutoRepeat);
        if (CampingStarterKit) yield return nameof(CampingStarterKit);
        if (CampingFires) yield return nameof(CampingFires);
        if (Expeditions) yield return nameof(Expeditions);
        if (Pilgrimage) yield return nameof(Pilgrimage);
        if (RoadSpeed) yield return nameof(RoadSpeed);
        if (RetentionContent) yield return nameof(RetentionContent);
        if (!SafeWorld && !AutomaticMurderAdjudication && !TheftProtection && !KnockedOut && !HotZones && !CoolZones && !HousingGeography && !Alpha3StartingStats && !Alpha3StarterScissors && !Alpha3StarterBag && !Alpha3StarterGold && !Alpha3StarterCraftMaterials && !Alpha3StarterCombatGear && !SkillBank && !PetRestrictions && !SkillGainCurve && !HythlothHotZone && !HarvestAutoRepeat && !ActionAutoRepeat && !CampingStarterKit && !CampingFires && !Expeditions && !Pilgrimage && !RoadSpeed && !RetentionContent)
        {
            yield return "none";
        }
    }
}
