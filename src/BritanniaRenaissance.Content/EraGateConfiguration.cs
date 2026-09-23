using System.Text.Json.Serialization;
using Server;
using Server.Json;
using Server.Logging;
using Server.Maps;

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

        foreach (var key in RequiredDisabledSettings)
        {
            if (ServerConfiguration.GetSetting(key, true))
            {
                errors.Add($"ModernUO setting {key} must be False at runtime.");
            }
        }

        return errors;
    }

    public static IEnumerable<string> Describe()
    {
        yield return $"Runtime era gates: {string.Join(", ", RequiredDisabledSettings)} disabled";
        yield return $"Runtime expansion/maps: {Core.Expansion} / {ExpansionInfo.CoreExpansion.MapSelectionFlags}";
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
