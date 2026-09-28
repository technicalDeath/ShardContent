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
        CommandSystem.Register("SkillBank", AccessLevel.Player, OnSkillBank);
        CommandSystem.Register("SkillBankStatus", AccessLevel.Administrator, OnSkillBankStatus);
        CommandSystem.Register("SkillBankRecover", AccessLevel.Administrator, OnSkillBankRecover);
        CommandSystem.Register("HotZoneStatus", AccessLevel.Administrator, OnHotZoneStatus);
        CommandSystem.Register("Welcome", AccessLevel.Player, OnWelcome);
    }

    [Usage("Welcome")]
    [Description("Explains player combat consent and the two Ward systems.")]
    private static void OnWelcome(CommandEventArgs e)
    {
        if (!TheftProtectionService.Enabled)
        {
            e.Mobile.SendMessage("Ward rules are not currently active.");
            return;
        }

        foreach (var line in StarterOnboarding.DescribeRules())
        {
            e.Mobile.SendMessage(line);
        }
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

    [Usage("SkillBank [lock|down <skill>]")]
    [Description("Displays stored skills or changes a banked skill's retention setting.")]
    private static void OnSkillBank(CommandEventArgs e)
    {
        if (e.Length > 0)
        {
            if (e.Mobile is not PlayerMobile player || e.Length != 2 ||
                !Enum.TryParse<SkillName>(e.GetString(1), true, out var skillName) ||
                !Enum.IsDefined(skillName))
            {
                e.Mobile.SendMessage("Use [SkillBank lock <skill> or [SkillBank down <skill>.");
                return;
            }

            var retention = e.GetString(0).ToLowerInvariant() switch
            {
                "lock" => BankRetention.Locked,
                "down" => BankRetention.Down,
                _ => (BankRetention?)null
            };
            e.Mobile.SendMessage(retention is null
                ? "Use lock or down for bank retention."
                : SkillBankService.SetRetention(player, (int)skillName, retention.Value));
            return;
        }

        foreach (var line in SkillBankService.Describe(e.Mobile))
        {
            e.Mobile.SendMessage(line);
        }
    }

    [Usage("SkillBankStatus [serial]")]
    [Description("Inspect a player's saved Skill Bank and active skill totals without changing them.")]
    private static void OnSkillBankStatus(CommandEventArgs e)
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

        foreach (var line in SkillBankService.DescribeForStaff(target))
        {
            e.Mobile.SendMessage(line);
        }
    }

    [Usage("SkillBankRecover <serial>")]
    [Description("Archive and reset an invalid saved Skill Bank payload without changing active skills.")]
    private static void OnSkillBankRecover(CommandEventArgs e)
    {
        if (e.Mobile.AccessLevel < AccessLevel.Administrator)
        {
            e.Mobile.SendMessage("Only authorized staff may recover Skill Bank data.");
            return;
        }

        if (e.Length != 1 || World.FindMobile((Serial)e.GetUInt32(0)) is not PlayerMobile target)
        {
            e.Mobile.SendMessage("Specify a valid player serial: [SkillBankRecover <serial>.");
            return;
        }

        e.Mobile.SendMessage(SkillBankService.RecoverInvalidPayload(
            target,
            true,
            ShardRulesConfiguration.Settings.SkillBank.CapacityTenths
        ));
    }

    [Usage("HotZoneStatus")]
    [Description("Inspect configured outdoor Hot regions and current membership.")]
    private static void OnHotZoneStatus(CommandEventArgs e)
    {
        foreach (var line in OutdoorHotZonePolicy.Describe(e.Mobile))
        {
            e.Mobile.SendMessage(line);
        }
    }
}
