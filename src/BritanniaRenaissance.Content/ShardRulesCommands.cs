using Server;
using Server.Mobiles;
using Server.Targeting;

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
        CommandSystem.Register("Execute", AccessLevel.Player, OnExecute);
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
    [Description("Displays Backpack Ward, theft-region, and corpse-protection state.")]
    private static void OnTheftStatus(CommandEventArgs e)
    {
        foreach (var line in TheftProtectionService.DescribeStatus(e.Mobile))
        {
            e.Mobile.SendMessage(line);
        }
    }

    [Usage("KnockedOutStatus")]
    [Description("Displays Knocked Out state and encounter-resolution permissions.")]
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

    [Usage("Execute")]
    [Description("Execute an encounter-authorized Knocked Out player.")]
    private static void OnExecute(CommandEventArgs e)
    {
        if (e.Mobile is not PlayerMobile executor)
        {
            return;
        }

        executor.Target = new ExecuteTarget(executor);
        executor.SendMessage("Select the Knocked Out player to execute.");
    }

    private sealed class ExecuteTarget(PlayerMobile executor) : Target(-1, false, TargetFlags.None)
    {
        protected override bool CanTarget(Mobile from, Mobile mobile, ref Point3D loc, ref Map map)
        {
            // Knocked Out players are intentionally untargetable for ordinary actions. The
            // explicit Execute command is the one encounter-authorized exception; Execute()
            // still performs the feature, region, criminality and recorded-attacker checks.
            if (mobile is PlayerMobile victim && KnockedOutService.IsKnockedOut(victim))
            {
                loc = mobile.Location;
                map = mobile.Map;
                return true;
            }

            return base.CanTarget(from, mobile, ref loc, ref map);
        }

        protected override void OnTarget(Mobile from, object targeted)
        {
            if (targeted is not PlayerMobile victim || !KnockedOutService.Execute(executor, victim))
            {
                from.SendMessage("That target is not eligible for encounter-authorized execution.");
                return;
            }

            from.SendMessage("The Knocked Out player has been executed.");
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
