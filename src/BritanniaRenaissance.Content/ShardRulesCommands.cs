using Server;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>Staff diagnostics for the loaded shard policy document.</summary>
public static class ShardRulesCommands
{
    public static void Register()
    {
        CommandSystem.Register("ShardRulesStatus", AccessLevel.Administrator, OnStatus);
        CommandSystem.Register("Intent", AccessLevel.Player, OnIntent);
        CommandSystem.Register("IntentStatus", AccessLevel.Player, OnIntentStatus);
        CommandSystem.Register("MurderStatus", AccessLevel.Administrator, OnMurderStatus);
        CommandSystem.Register("TheftStatus", AccessLevel.Administrator, OnTheftStatus);
        CommandSystem.Register("MasteryStatus", AccessLevel.Player, OnMasteryStatus);
    }

    [Usage("Intent")]
    [Description("Toggle voluntary PvP Intent for new opponents.")]
    private static void OnIntent(CommandEventArgs e)
    {
        if (e.Mobile is PlayerMobile player)
        {
            PvpIntentService.ToggleIntent(player);
        }
    }

    [Usage("IntentStatus")]
    [Description("Displays the safe-world PvP Intent status.")]
    private static void OnIntentStatus(CommandEventArgs e)
    {
        foreach (var line in PvpIntentService.DescribeStatus(e.Mobile))
        {
            e.Mobile.SendMessage(line);
        }
    }

    [Usage("MurderStatus")]
    [Description("Displays the automatic murder adjudication policy and ledger state.")]
    private static void OnMurderStatus(CommandEventArgs e)
    {
        foreach (var line in MurderAdjudicationService.DescribeStatus(e.Mobile))
        {
            e.Mobile.SendMessage(line);
        }
    }

    [Usage("TheftStatus")]
    [Description("Displays Backpack Ward protection state and deferred theft restrictions.")]
    private static void OnTheftStatus(CommandEventArgs e)
    {
        foreach (var line in TheftProtectionService.DescribeStatus(e.Mobile))
        {
            e.Mobile.SendMessage(line);
        }
    }

    [Usage("ShardRulesStatus")]
    [Description("Displays the validated Britannia Renaissance shard policy baseline.")]
    private static void OnStatus(CommandEventArgs e)
    {
        foreach (var line in ShardRulesConfiguration.Describe())
        {
            e.Mobile.SendMessage(line);
        }

        foreach (var line in EraGateConfiguration.Describe())
        {
            e.Mobile.SendMessage(line);
        }
    }

    [Usage("MasteryStatus")]
    [Description("Displays the server-controlled Mastery schedule and your pending increments.")]
    private static void OnMasteryStatus(CommandEventArgs e)
    {
        foreach (var line in MasteryProgression.DescribeStatus(e.Mobile))
        {
            e.Mobile.SendMessage(line);
        }
    }
}
