using System.Text.Json.Serialization;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The numbers for death recovery (docs/Death-Recovery-Plan.md): a player corpse's time, the corpse compass, the killer going home and materializing.
/// Each part has its own feature flag.
/// </summary>
public sealed class DeathRecoveryRules
{
    /// <summary>Minutes a player's corpse lasts before it turns to bones (<c>longerPlayerCorpses</c>; stock 7). Bones then last the stock 7.</summary>
    [JsonPropertyName("playerCorpseMinutes")]
    public int PlayerCorpseMinutes { get; set; } = 10;

    /// <summary>The corpse compass stops when its owner is this close to the corpse.</summary>
    [JsonPropertyName("compassStopRange")]
    public int CompassStopRange { get; set; } = 2;

    /// <summary>Seconds a monster that killed a player leaves them alone, counted from when it first sees them alive again.</summary>
    [JsonPropertyName("killerSpareSeconds")]
    public int KillerSpareSeconds { get; set; } = 120;

    /// <summary>The longest materializing lasts.</summary>
    [JsonPropertyName("materializingMinutes")]
    public int MaterializingMinutes { get; set; } = 10;

    /// <summary>Materializing ends this long after the player first opens their own corpse.</summary>
    [JsonPropertyName("materializingAfterOpenSeconds")]
    public int MaterializingAfterOpenSeconds { get; set; } = 60;

    /// <summary>The hue other players see a materializing character in (not saved, so a restart can never leave it). 0x047E is a pale silver,
    /// chosen in the real client over 0x4001, which ClassicUO draws as a black see-through shadow (its spectral shader).</summary>
    [JsonPropertyName("materializingHue")]
    public int MaterializingHue { get; set; } = 0x047E;

    public static void Validate(DeathRecoveryRules rules, List<string> errors)
    {
        Range("deathRecovery.playerCorpseMinutes", rules.PlayerCorpseMinutes, 1, 60, errors);
        Range("deathRecovery.compassStopRange", rules.CompassStopRange, 0, 10, errors);
        Range("deathRecovery.killerSpareSeconds", rules.KillerSpareSeconds, 10, 900, errors);
        Range("deathRecovery.materializingMinutes", rules.MaterializingMinutes, 1, 30, errors);
        Range("deathRecovery.materializingAfterOpenSeconds", rules.MaterializingAfterOpenSeconds, 10, 600, errors);
        Range("deathRecovery.materializingHue", rules.MaterializingHue, 0, 0xFFFF, errors);
    }

    private static void Range(string name, int value, int min, int max, List<string> errors)
    {
        if (value < min || value > max)
        {
            errors.Add($"{name} must be between {min} and {max}.");
        }
    }
}
