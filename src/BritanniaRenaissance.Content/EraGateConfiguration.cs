using System.Text.Json.Serialization;
using Server;
using Server.Json;
using Server.Logging;
using Server.Maps;
using Server.Systems.FeatureFlags;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Validates the shard-owned UOR era gates after the deployment tool has applied them to ModernUO.
/// These values are intentionally explicit rather than relying on later-expansion defaults.
/// </summary>
public static class EraGateConfiguration
{
    public const string RelativePath = "Configuration/modernuo-era-gates.json";
    private static readonly ILogger Logger = LogFactory.GetLogger(typeof(EraGateConfiguration));

    public static EraGates Settings { get; private set; } = null!;

    public static void Load()
    {
        var path = Path.Combine(Core.BaseDirectory, RelativePath);
        var settings = JsonConfig.Deserialize<EraGates>(path);

        if (settings is null)
        {
            throw new InvalidOperationException($"Era gate configuration is missing or invalid: {path}");
        }

        var errors = Validate(settings);
        errors.AddRange(ValidateRuntime(settings));

        if (errors.Count > 0)
        {
            throw new InvalidOperationException(
                $"Era gate configuration failed validation:{Environment.NewLine}- {string.Join(Environment.NewLine + "- ", errors)}"
            );
        }

        Settings = settings;
        Logger.Information("Validated UOR era gates: {Gates}.", string.Join(", ", settings.Settings.Keys));
    }

    public static List<string> Validate(EraGates gates)
    {
        var errors = new List<string>();

        if (gates.SchemaVersion != 1)
        {
            errors.Add($"schemaVersion must be 1, but was {gates.SchemaVersion}.");
        }

        foreach (var key in RequiredDisabledSettings)
        {
            if (!gates.Settings.TryGetValue(key, out var value) || !string.Equals(value, "False", StringComparison.OrdinalIgnoreCase))
            {
                errors.Add($"settings.{key} must be explicitly False.");
            }
        }

        return errors;
    }

    public static List<string> ValidateRuntime(EraGates gates)
    {
        var errors = new List<string>();

        if (Core.Expansion != Expansion.UOR)
        {
            errors.Add($"ModernUO core expansion must be UOR, but was {Core.Expansion}.");
        }

        if (ExpansionInfo.CoreExpansion.MapSelectionFlags != MapSelectionFlags.Felucca)
        {
            errors.Add($"ModernUO map selection must be only Felucca, but was {ExpansionInfo.CoreExpansion.MapSelectionFlags}.");
        }

        if (ExpansionInfo.CoreExpansion.SupportedFeatures.HasFlag(FeatureFlags.ML))
        {
            errors.Add("The ML supported-feature bit must remain disabled; cosmetic Elf uses only the character-list capability.");
        }

        foreach (var key in RequiredDisabledSettings)
        {
            if (ServerConfiguration.GetSetting(key, true))
            {
                errors.Add($"ModernUO setting {key} must be False at runtime.");
            }
        }

        return errors;
    }

    /// <summary>
    /// Runs once the server has started. ModernUO's <c>ProfessionInfo</c> loads its file in a static constructor, on first
    /// use, and resolves skills by their profession names through the skill table. Touching it any earlier (the era gates
    /// load during <c>Configure</c>, before the skill table exists) would freeze a table that silently lacks every
    /// template using an aliased skill name, so this check must not run before startup completes. If the shard's
    /// profession file is not the one in use the server is stopped: a silent fallback would hand out later-era gear.
    /// </summary>
    public static void ValidatePostBootProfessions()
    {
        var errors = ValidateProfessions();

        if (errors.Count == 0)
        {
            Logger.Information("Validated shard character-creation templates: {Ids} defined; {Undefined} undefined.",
                string.Join(", ", ShardProfessions.TemplateIds), string.Join(", ", ShardProfessions.UndefinedIds));
            return;
        }

        Logger.Error(
            "Character-creation templates are wrong, so the server is stopping: {Errors}",
            string.Join(" ", errors)
        );
        Core.Kill();
    }

    /// <summary>
    /// The shard's own profession file must be the one the server loaded: exactly the approved template IDs exist and
    /// none of the later-era ones (4 to 7). Otherwise the server would grant a later-era profession's skills and gear
    /// from whichever prof.txt the client data folder holds.
    /// </summary>
    public static List<string> ValidateProfessions()
    {
        var errors = new List<string>();

        foreach (var id in ShardProfessions.TemplateIds)
        {
            if (!ProfessionInfo.GetProfession(id, out _))
            {
                errors.Add($"Profession {id} is not defined; the shard profession file ({ShardProfessions.SettingKey}) is not in use.");
            }
        }

        foreach (var id in ShardProfessions.UndefinedIds)
        {
            if (ProfessionInfo.GetProfession(id, out var profession))
            {
                errors.Add($"Profession {id} ({profession.Name}) must not be defined on this shard.");
            }
        }

        return errors;
    }

    public static IEnumerable<string> Describe()
    {
        yield return $"Runtime era gates: {string.Join(", ", RequiredDisabledSettings)} disabled";
        yield return $"Runtime expansion/maps: {Core.Expansion} / {ExpansionInfo.CoreExpansion.MapSelectionFlags}";
        yield return $"Insurance feature flag: {(FeatureFlagManager.IsEnabled("insurance") ? "ENABLED" : "disabled")}";
    }

    /// <summary>
    /// The `insurance.enable` ModernUO setting checked in <see cref="Validate"/>/<see cref="ValidateRuntime"/>
    /// only seeds the "insurance" feature flag's default the first time it is created; once persisted to
    /// `Configuration/FeatureFlags/flags.json`, that flag overrides it independently (e.g. a GM toggle via
    /// `[FF insurance true` or a leftover file from testing). <see cref="FeatureFlagManager"/> only finishes
    /// loading during the ModernUO `Initialize` boot pass, which runs after this class's own `Load()`, so this
    /// check must run separately once the server has actually started.
    /// </summary>
    public static void ValidatePostBootFeatureFlags()
    {
        if (FeatureFlagManager.IsEnabled("insurance"))
        {
            Logger.Error(
                "ModernUO feature flag 'insurance' is enabled at runtime, but the UOR era gates require " +
                "insurance to stay disabled. The insurance.enable setting only seeds this flag's first-boot " +
                "default and does not override a persisted value; disable it with '[FF insurance false' or " +
                "by editing Configuration/FeatureFlags/flags.json."
            );
        }
    }

    private static readonly string[] RequiredDisabledSettings =
    [
        "insurance.enable",
        "vetRewards.enable",
        "vetRewards.skillCapRewards",
        "questSystem.enableMLQuests",
        "taming.enableBonding",
        "taming.petsStandDownOnCommand"
    ];
}

public sealed class EraGates
{
    [JsonPropertyName("schemaVersion")]
    public int SchemaVersion { get; set; }

    [JsonPropertyName("settings")]
    public Dictionary<string, string> Settings { get; set; } = new(StringComparer.OrdinalIgnoreCase);
}
