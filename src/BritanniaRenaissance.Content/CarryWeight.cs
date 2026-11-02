using System;
using System.Buffers;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Server;
using Server.Commands;
using Server.Items;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>Settings for <see cref="CarryWeight"/> (<c>carryWeight</c> in shard-rules.json). The defaults are the stock UO:R values.</summary>
public sealed class CarryWeightRules
{
    /// <summary>Stones every player carries before Strength counts; stock (before Mondain's Legacy) is 40.</summary>
    [JsonPropertyName("base")]
    public int Base { get; set; } = CarryWeight.StockBase;

    /// <summary>Stones each point of Strength adds; stock is 3.5.</summary>
    [JsonPropertyName("perStrength")]
    public double PerStrength { get; set; } = CarryWeight.StockPerStrength;

    /// <summary>The most a player's own worn backpack holds, in stones; 0 keeps the stock 400.</summary>
    [JsonPropertyName("playerBackpackMaxWeight")]
    public int PlayerBackpackMaxWeight { get; set; }
}

/// <summary>
/// The shard's carry limit (owner, 2026-11-01: base 100 so new characters are not overweight so soon). A player's limit is
/// <see cref="CarryWeightRules.Base"/> + <see cref="CarryWeightRules.PerStrength"/> x Str, rounded down as stock does, and a player's
/// own worn backpack holds <see cref="CarryWeightRules.PlayerBackpackMaxWeight"/> so strong characters are not stopped by the pack first.
/// Bags, pack animals and the bank keep their stock limits, and the overload penalty (<c>stamina.*</c> settings) is unchanged. The
/// starter weight budget stays measured against the stock limit (<see cref="StarterWeightBudget"/>), so starting kits are what they
/// were and the extra room is all headroom. Engine hooks: <c>PlayerMobile.MaxWeightAdjust</c>, <c>Backpack.PlayerMaxWeightAdjust</c>.
/// The era's status packet (version 3) carries no carry limit, so a client works out the stock one itself; at login the server sends
/// extended command 0xB3 with the base and the stones per Strength in tenths (and again when the client asks with 0xB3), and the
/// shard's client uses them for the status bar.
/// </summary>
public static class CarryWeight
{
    public const int StockBase = 40;
    public const double StockPerStrength = 3.5;
    public const int StockPlayerBackpack = 400;
    public const int Command = 0xB3;

    private static bool _configured;

    public static CarryWeightRules Rules => ShardRulesConfiguration.Settings?.CarryWeight ?? new CarryWeightRules();

    public static unsafe void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        PlayerMobile.MaxWeightAdjust = (player, _) => Limit(Rules, player.Str);
        Backpack.PlayerMaxWeightAdjust = (_, stock) => BackpackLimit(Rules, stock);
        EventSink.Connected += OnConnected;
        IncomingExtendedCommandPackets.RegisterExtended(Command, true, &OnRequest);
        CommandSystem.Register("CarryWeightStatus", AccessLevel.GameMaster, e =>
        {
            var rules = Rules;
            e.Mobile.SendMessage(
                $"Carry weight: {rules.Base} + {rules.PerStrength} x Str (stock {StockBase} + {StockPerStrength} x Str); worn backpack holds {BackpackLimit(rules, StockPlayerBackpack)} (stock {StockPlayerBackpack})."
            );

            if (e.Mobile is PlayerMobile pm)
            {
                e.Mobile.SendMessage($"You: Str {pm.Str}, limit {pm.MaxWeight} (stock {pm.StockMaxWeight}), load {Mobile.BodyWeight + pm.TotalWeight}.");
            }
        });
    }

    /// <summary>0xBF, the length, the command, the base (two bytes), then the stones per Strength in tenths (two bytes).</summary>
    public static byte[] Packet(CarryWeightRules rules)
    {
        var tenths = PerStrengthTenths(rules);
        return [0xBF, 0, 9, Command >> 8, Command & 0xFF, (byte)(rules.Base >> 8), (byte)rules.Base, (byte)(tenths >> 8), (byte)tenths];
    }

    public static int PerStrengthTenths(CarryWeightRules rules) => (int)Math.Round(rules.PerStrength * 10.0);

    /// <summary>The client asks once its game scene is up, in case the login copy came too early; the answer is the same.</summary>
    private static void OnRequest(NetState state, SpanReader reader) => OnConnected(state.Mobile);

    private static void OnConnected(Mobile mobile)
    {
        if (mobile is PlayerMobile { NetState: { } state })
        {
            state.Send(Packet(Rules));
        }
    }

    /// <summary>A player's carry limit at this Strength.</summary>
    /// <remarks>Whole-number tenths, as the client sums it: 3.3 x 10 in floating point is 32.99..., which would round a stone away.</remarks>
    public static int Limit(CarryWeightRules rules, int str) => rules.Base + PerStrengthTenths(rules) * str / 10;

    /// <summary>The most a player's worn backpack holds: the configured value, or the stock one when it is 0.</summary>
    public static int BackpackLimit(CarryWeightRules rules, int stock) =>
        rules.PlayerBackpackMaxWeight > 0 ? rules.PlayerBackpackMaxWeight : stock;

    public static void Validate(CarryWeightRules rules, List<string> errors)
    {
        if (rules == null)
        {
            return;
        }

        if (rules.Base is < 0 or > 400)
        {
            errors.Add($"carryWeight.base must be between 0 and 400 stones, but was {rules.Base}.");
        }

        // the client is told the value in tenths, so a finer one would show a different limit from the one the server keeps
        if (rules.PerStrength is < 0.0 or > 10.0 || double.IsNaN(rules.PerStrength) || Math.Abs(rules.PerStrength * 10.0 - PerStrengthTenths(rules)) > 1e-9)
        {
            errors.Add($"carryWeight.perStrength must be between 0 and 10 in steps of 0.1, but was {rules.PerStrength}.");
        }

        if (rules.PlayerBackpackMaxWeight != 0 && rules.PlayerBackpackMaxWeight is < StockPlayerBackpack or > 1600)
        {
            errors.Add($"carryWeight.playerBackpackMaxWeight must be 0 (stock) or from {StockPlayerBackpack} to 1600 stones, but was {rules.PlayerBackpackMaxWeight}.");
        }
    }
}
