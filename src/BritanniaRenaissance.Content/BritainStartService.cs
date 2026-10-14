using Server;
using Server.Engines.CharacterCreation;

namespace BritanniaRenaissance.Content;

/// <summary>
/// New characters start in Britain only (docs/Britain-Start-Evidence.md), behind <c>featureFlags.startInBritainOnly</c>. World generation keeps every shopkeeper, banker, healer, trainer and
/// guildmaster in Britain, yet the stock list offers nine starting towns, so a character that began in another town started with none of them near. The stock list is built once and is both
/// sent to the client and indexed when the character is made, so the narrowing goes through the one hook (<see cref="CharacterCreation.StartingCitiesFilter"/>) and the two always agree.
/// </summary>
public static class BritainStartService
{
    public const string Town = "Britain";

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.StartInBritainOnly == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CharacterCreation.StartingCitiesFilter = Filter;
    }

    private static CityInfo[] Filter(CityInfo[] all) => Enabled ? Only(all, Town) : all;

    /// <summary>The list reduced to the named town, or the list as it was when it has no such town (a world that cannot start anyone is worse than one that offers too many towns).</summary>
    public static CityInfo[] Only(CityInfo[] all, string town)
    {
        foreach (var city in all)
        {
            if (string.Equals(city.City, town, System.StringComparison.OrdinalIgnoreCase))
            {
                return [city];
            }
        }

        return all;
    }
}
