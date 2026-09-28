using Server;
using Server.Accounting;
using Server.Engines.CharacterCreation;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

public static class StarterGoldPolicy
{
    public const int StockStartingGold = 1000;
    public const int FirstAccountGold = 500;
    private const string EntitlementTag = "BritanniaRenaissance.StarterGold.v1";
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CharacterCreation.StartingGoldAmount = ResolveAmount;
    }

    public static int SelectAmount(
        bool enabled, bool ordinaryPlayer, bool entitlementRecorded,
        bool anotherCharacterExists, bool priorGameTime
    )
    {
        if (!enabled || !ordinaryPlayer)
        {
            return StockStartingGold;
        }

        return entitlementRecorded || anotherCharacterExists || priorGameTime ? 0 : FirstAccountGold;
    }

    private static int ResolveAmount(Mobile mobile)
    {
        var enabled = ShardRulesConfiguration.Settings?.FeatureFlags.Alpha3StarterGold == true;
        if (!enabled || mobile is not PlayerMobile { AccessLevel: AccessLevel.Player } player)
        {
            return StockStartingGold;
        }

        if (player.Account is not Account account)
        {
            return 0;
        }

        var recorded = account.GetTag(EntitlementTag) is not null;
        var amount = SelectAmount(
            true,
            true,
            recorded,
            account.Count > 1,
            account.TotalGameTime > TimeSpan.Zero
        );

        if (!recorded)
        {
            // Consume the account's one-time entitlement even when an older character or
            // deleted-character playtime proves that the account already had a start.
            account.SetTag(EntitlementTag, amount == FirstAccountGold ? "granted" : "prior-account");
        }

        return amount;
    }
}
