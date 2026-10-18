using System.Collections.Generic;
using System.Text.Json.Serialization;
using Server;
using Server.Commands;

namespace BritanniaRenaissance.Content;

/// <summary>Settings for <see cref="WorldSeason"/> (<c>worldSeason</c> in shard-rules.json).</summary>
public sealed class WorldSeasonRules
{
    /// <summary>Felucca's season: 0 spring, 1 summer, 2 fall, 3 winter, 4 desolation; -1 keeps the map definition's (desolation).</summary>
    [JsonPropertyName("felucca")]
    public int Felucca { get; set; } = -1;
}

/// <summary>
/// Felucca's season (owner, 2026-10-18: "change the season of the shard so that there are leaves on the trees ... I want the world to feel like
/// pre-trammel felucca"). Stock ModernUO gives Felucca the Desolation season it got when Trammel split off, so the client draws every tree bare
/// and swaps flowers for gravestones and bones; Britannia before Trammel had ordinary seasons. The map's season is what the server sends a
/// player at login and on every map change (<c>Mobile.GetSeason</c>), so setting it once the maps are loaded is enough; nothing is saved.
/// </summary>
public static class WorldSeason
{
    public static readonly string[] Names = ["spring", "summer", "fall", "winter", "desolation"];

    private static bool _configured;
    private static int _stockFelucca = -1;

    public static WorldSeasonRules Rules => ShardRulesConfiguration.Settings?.WorldSeason ?? new WorldSeasonRules();

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        EventSink.ServerStarted += Apply;
        CommandSystem.Register("SeasonStatus", AccessLevel.GameMaster, e =>
            e.Mobile.SendMessage(
                $"Felucca season: {Name(Map.Felucca?.Season ?? -1)} (configured {Rules.Felucca}, map definition {Name(_stockFelucca)})."
            ));
    }

    public static void Apply()
    {
        var felucca = Map.Felucca;
        if (felucca == null)
        {
            return;
        }

        if (_stockFelucca < 0)
        {
            _stockFelucca = felucca.Season;
        }

        felucca.Season = Resolve(Rules.Felucca, _stockFelucca);
    }

    /// <summary>The configured season, or the map definition's when it is -1.</summary>
    public static int Resolve(int configured, int stock) => configured is >= 0 and <= 4 ? configured : stock;

    public static string Name(int season) => season is >= 0 and <= 4 ? Names[season] : "unknown";

    public static void Validate(WorldSeasonRules rules, List<string> errors)
    {
        if (rules != null && rules.Felucca is < -1 or > 4)
        {
            errors.Add("worldSeason.felucca must be -1 (the map's own) or 0-4 (spring, summer, fall, winter, desolation).");
        }
    }
}
