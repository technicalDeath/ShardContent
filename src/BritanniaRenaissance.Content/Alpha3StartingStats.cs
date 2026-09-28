using Server;
using Server.Engines.CharacterCreation;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

public static class Alpha3StartingStats
{
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CharacterCreation.CharacterCreatedHandler += Apply;
    }

    public static void Apply(CharacterCreatedEventArgs args)
    {
        if (ShardRulesConfiguration.Settings?.FeatureFlags.Alpha3StartingStats != true ||
            args.Mobile is not PlayerMobile { AccessLevel: AccessLevel.Player } player)
        {
            return;
        }

        var hasProfession = ProfessionInfo.GetProfession(args.Profession, out var profession);
        var sourceStats = hasProfession ? profession.Stats : args.Stats;
        var (strength, dexterity, intelligence) = Allocate(hasProfession ? profession.Name : null, sourceStats);
        player.InitStats(strength, dexterity, intelligence);
    }

    public static (int Strength, int Dexterity, int Intelligence) Allocate(
        string? professionName,
        ReadOnlySpan<byte> sourceStats
    )
    {
        // The UOR profession file exposes these three templates. Advanced keeps the
        // player's relative choices after the server's 30-point minimum is applied.
        return professionName switch
        {
            "Warrior" => (50, 40, 30),
            "Mage" => (30, 30, 60),
            "Blacksmith" => (60, 30, 30),
            _ => AllocateFromPreferences(sourceStats)
        };
    }

    private static (int Strength, int Dexterity, int Intelligence) AllocateFromPreferences(ReadOnlySpan<byte> stats)
    {
        if (stats.Length < 3)
        {
            return (40, 40, 40);
        }

        Span<int> weights = stackalloc int[3];
        Span<int> result = stackalloc int[3];
        var totalWeight = 0;

        for (var i = 0; i < 3; i++)
        {
            weights[i] = Math.Max(0, stats[i] - 10);
            result[i] = 30;
            totalWeight += weights[i];
        }

        if (totalWeight == 0)
        {
            return (40, 40, 40);
        }

        var assigned = 0;
        for (var i = 0; i < 3; i++)
        {
            var share = 30 * weights[i] / totalWeight;
            result[i] += share;
            assigned += share;
        }

        // Distribute integer remainders in stat order for a stable result.
        while (assigned < 30)
        {
            var best = -1;
            var bestRemainder = -1;
            for (var i = 0; i < 3; i++)
            {
                var remainder = 30 * weights[i] % totalWeight;
                if (remainder > bestRemainder && result[i] < 60)
                {
                    best = i;
                    bestRemainder = remainder;
                }
            }

            result[best]++;
            assigned++;
            weights[best] = 0;
        }

        return (result[0], result[1], result[2]);
    }
}
