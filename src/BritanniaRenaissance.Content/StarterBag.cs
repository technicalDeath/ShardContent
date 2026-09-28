using Server;
using Server.Accounting;
using Server.Engines.CharacterCreation;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Issues one ordinary stock <see cref="Bag"/> at character creation for organizing starter
/// items. Owner ruling (2026-09-28): the bag carries no starter binding or special death rule;
/// newbied items inside it are kept by <see cref="KeptItemDeathRouting"/>.
/// </summary>
public static class StarterBagIssuance
{
    private const string IssuanceTagPrefix = "BritanniaRenaissance.StarterBag.v1.";
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CharacterCreation.CharacterCreatedHandler += Issue;
    }

    public static void Issue(CharacterCreatedEventArgs args)
    {
        if (ShardRulesConfiguration.Settings?.FeatureFlags.Alpha3StarterBag != true ||
            args.Mobile is not PlayerMobile { AccessLevel: AccessLevel.Player, Backpack: not null } player ||
            player.Account is not Account account)
        {
            return;
        }

        var tag = $"{IssuanceTagPrefix}{player.Serial.Value}";
        if (account.GetTag(tag) is not null)
        {
            return;
        }

        player.Backpack.DropItem(new Bag());
        account.SetTag(tag, "issued");
    }
}
