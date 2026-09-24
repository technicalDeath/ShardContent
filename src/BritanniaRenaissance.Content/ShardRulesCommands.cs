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
        CommandSystem.Register("MurderMigrationAudit", AccessLevel.Administrator, OnMurderMigrationAudit);
        CommandSystem.Register("TheftStatus", AccessLevel.Administrator, OnTheftStatus);
        CommandSystem.Register("KnockedOutStatus", AccessLevel.Administrator, OnKnockedOutStatus);
        CommandSystem.Register("KnockedOutRecover", AccessLevel.Administrator, OnKnockedOutRecover);
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

    [Usage("MurderMigrationAudit")]
    [Description("Audits legacy and custom murder state without changing it.")]
    private static void OnMurderMigrationAudit(CommandEventArgs e)
    {
        foreach (var line in MurderAdjudicationService.DescribeMigrationAudit())
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

    [Usage("KnockedOutStatus")]
    [Description("Displays Knocked Out state and deferred resolution restrictions.")]
    private static void OnKnockedOutStatus(CommandEventArgs e)
    {
        foreach (var line in KnockedOutService.DescribeStatus(e.Mobile))
        {
            e.Mobile.SendMessage(line);
        }
    }

    [Usage("KnockedOutRecover [serial]")]
    [Description("Recovers a player from the Knocked Out state.")]
    private static void OnKnockedOutRecover(CommandEventArgs e)
    {
        PlayerMobile? target = e.Mobile as PlayerMobile;

        if (e.Length > 0)
        {
            target = World.FindMobile((Serial)e.GetUInt32(0)) as PlayerMobile;
        }

        if (target is null)
        {
            e.Mobile.SendMessage("Specify a player serial or use this command while possessing a player body.");
            return;
        }

        e.Mobile.SendMessage(
            KnockedOutService.Recover(target)
                ? $"Recovered {target.Name} from Knocked Out."
                : $"{target.Name} is not currently Knocked Out."
        );
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
