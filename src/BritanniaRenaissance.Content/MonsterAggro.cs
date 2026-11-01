using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Server;
using Server.Commands;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>Settings for <see cref="MonsterAggro"/> (<c>monsterAggro</c> in shard-rules.json).</summary>
public sealed class MonsterAggroRules
{
    /// <summary>Tiles taken off the range a wild creature picks a new target within; 0 keeps stock.</summary>
    [JsonPropertyName("rangeReduction")]
    public int RangeReduction { get; set; }
}

/// <summary>
/// A shorter aggro range, to make the world a little easier to explore (owner, 2026-10-19: "I want to tune down monster agro range ... if it's global,
/// reduce it by 2 tiles"). Stock has two ranges: each creature's own <c>RangePerception</c> (16 unless the creature sets another), which its periodic scan
/// (every 10 s) picks targets within, and the 10-tile reaction when an enemy moves near it (<c>AcquireOnApproachRange</c>, the same for every creature).
/// Both lose <see cref="MonsterAggroRules.RangeReduction"/> tiles for wild creatures, never below <see cref="MinimumRange"/>. A tamed or summoned creature
/// keeps its stock ranges, and a creature already fighting chases, leashes and fights back as stock. Engine hook: <c>BaseCreature.AcquireRangeFilter</c>.
/// </summary>
public static class MonsterAggro
{
    public const int MinimumRange = 2;
    public const int MaximumReduction = 8;

    private static bool _configured;

    public static MonsterAggroRules Rules => ShardRulesConfiguration.Settings?.MonsterAggro ?? new MonsterAggroRules();

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        BaseCreature.AcquireRangeFilter = (creature, range) => Range(creature, range, Rules.RangeReduction);
        CommandSystem.Register("AggroStatus", AccessLevel.GameMaster, e =>
            e.Mobile.SendMessage(
                $"Monster aggro: {Rules.RangeReduction} tiles off (a stock 16-tile scan is {Reduced(16, Rules.RangeReduction)}, the 10-tile reaction {Reduced(10, Rules.RangeReduction)})."));
    }

    public static int Range(BaseCreature creature, int range, int reduction) =>
        creature == null || creature.Controlled || creature.Summoned ? range : Reduced(range, reduction);

    public static int Reduced(int range, int reduction) => reduction <= 0 || range <= MinimumRange ? range : Math.Max(MinimumRange, range - reduction);

    public static void Validate(MonsterAggroRules rules, List<string> errors)
    {
        if (rules == null)
        {
            return;
        }

        if (rules.RangeReduction < 0 || rules.RangeReduction > MaximumReduction)
        {
            errors.Add($"monsterAggro.rangeReduction must be from 0 (stock) to {MaximumReduction} tiles.");
        }
    }
}
