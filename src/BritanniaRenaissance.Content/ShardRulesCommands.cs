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
        CommandSystem.Register("Mastery", AccessLevel.Player, OnMastery);
        CommandSystem.Register("SkillBank", AccessLevel.Player, OnSkillBank);
        CommandSystem.Register("SkillBankStatus", AccessLevel.Administrator, OnSkillBankStatus);
        CommandSystem.Register("SkillBankRecover", AccessLevel.Administrator, OnSkillBankRecover);
        CommandSystem.Register("GrantFaintMemories", AccessLevel.Administrator, OnGrantFaintMemories);
        CommandSystem.Register("HotZoneStatus", AccessLevel.Administrator, OnHotZoneStatus);
        CommandSystem.Register("Welcome", AccessLevel.Player, OnWelcome);
        CommandSystem.Register("HarvestRepeatStatus", AccessLevel.Administrator, OnHarvestRepeatStatus);
        CommandSystem.Register("CampStatus", AccessLevel.Administrator, OnCampStatus);
        CommandSystem.Register("ActionRepeatStatus", AccessLevel.Administrator, OnActionRepeatStatus);
        CommandSystem.Register("BuffIconStatus", AccessLevel.Administrator, OnBuffIconStatus);
    }

    [Usage("BuffIconStatus")]
    [Description("Shows whether the buff bar is on, what the table lists, and the shard-added icons you have right now.")]
    private static void OnBuffIconStatus(CommandEventArgs e)
    {
        foreach (var line in BuffIconService.DescribeStatus(e.Mobile))
        {
            e.Mobile.SendMessage(line);
        }
    }

    [Usage("ActionRepeatStatus")]
    [Description("Shows whether taming, lockpicking, spinning, the loom and cooking auto-repeat, and the loops in flight.")]
    private static void OnActionRepeatStatus(CommandEventArgs e)
    {
        foreach (var line in ActionRepeatService.DescribeStatus())
        {
            e.Mobile.SendMessage(line);
        }
    }

    [Usage("CampStatus")]
    [Description("Shows the camping flags and numbers, and the campfires near you with their state and timing.")]
    private static void OnCampStatus(CommandEventArgs e)
    {
        foreach (var line in CampingService.DescribeStatus(e.Mobile))
        {
            e.Mobile.SendMessage(line);
        }

        foreach (var line in CampTravelService.DescribeSettings(e.Mobile))
        {
            e.Mobile.SendMessage(line);
        }
    }

    [Usage("HarvestRepeatStatus")]
    [Description("Shows whether mining, lumberjacking and fishing auto-repeat, and the loops in flight.")]
    private static void OnHarvestRepeatStatus(CommandEventArgs e)
    {
        foreach (var line in HarvestRepeatService.DescribeStatus(e.Mobile))
        {
            e.Mobile.SendMessage(line);
        }
    }

    [Usage("Welcome")]
    [Description("Opens the guide to the shard's rules: fighting, Hot Zones, the Wards, camp travel and the commands.")]
    private static void OnWelcome(CommandEventArgs e)
    {
        if (e.Mobile is PlayerMobile player)
        {
            WelcomeGuide.Open(player);
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
    [Description("Opens a window showing whether your Criminal Intent is on, with a button to change it. Staff see the policy diagnostics.")]
    private static void OnIntentStatus(CommandEventArgs e)
    {
        if (e.Mobile is PlayerMobile { AccessLevel: AccessLevel.Player } player)
        {
            StatusWindows.OpenIntent(player);
            return;
        }

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

    [Usage("TheftStatus [serial]")]
    [Description("Displays Backpack Ward, theft-region, and corpse-protection state, for you or the player with that serial.")]
    private static void OnTheftStatus(CommandEventArgs e)
    {
        var subject = e.Length > 0 ? World.FindMobile((Serial)e.GetUInt32(0)) : e.Mobile;

        if (subject is null)
        {
            e.Mobile.SendMessage("No mobile has that serial.");
            return;
        }

        foreach (var line in TheftProtectionService.DescribeStatus(subject))
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
    [Description("Execute a Knocked Out player you fought: stand next to them for five seconds. Also in the menu you get by clicking them.")]
    private static void OnExecute(CommandEventArgs e)
    {
        if (e.Mobile is not PlayerMobile executor)
        {
            return;
        }

        executor.Target = new ExecuteTarget(executor);
        executor.SendMessage("Select the Knocked Out player to execute. You must stand next to them.");
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
            if (targeted is not PlayerMobile victim)
            {
                from.SendMessage("Select a Knocked Out player.");
                return;
            }

            // Every check is made now, and a refusal is told at once; the countdown only starts when they all pass.
            KnockedOutService.BeginExecution(executor, victim);
        }
    }

    [Usage("ShardRulesStatus")]
    [Description("Displays the validated UO Rekindled shard policy baseline.")]
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

    [Usage("Mastery [serial]")]
    [Description("Opens a window with your Mastery cycle and each Mastery skill's allowance; staff may name a player.")]
    private static void OnMastery(CommandEventArgs e)
    {
        var subject = e.Mobile;

        if (e.Length > 0 && e.Mobile.AccessLevel >= AccessLevel.Administrator)
        {
            subject = World.FindMobile((Serial)e.GetUInt32(0));

            if (subject is null)
            {
                e.Mobile.SendMessage("No mobile has that serial.");
                return;
            }
        }

        MasteryGump.Open(e.Mobile, subject);
    }

    [Usage("SkillBank [lock|down <skill>]")]
    [Description("Opens your Skill Bank window; the window's buttons set a banked skill to Locked or Down.")]
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
            if (retention is null)
            {
                e.Mobile.SendMessage("Use lock or down for bank retention.");
                return;
            }

            var message = SkillBankService.SetRetention(player, (int)skillName, retention.Value);
            var done = message.EndsWith($"set to {retention}.", StringComparison.Ordinal);
            SkillBankGump.Open(
                player,
                0,
                done ? SkillBankGump.DescribeChange(player.Skills[(int)skillName].Info.Name, retention.Value) : message,
                done ? BannerKind.Done : BannerKind.Danger
            );
            return;
        }

        if (e.Mobile is PlayerMobile self)
        {
            SkillBankGump.Open(self);
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

    [Usage("GrantFaintMemories <serial>")]
    [Description("Gives a player character the standard Faint Memories pool if it has none. Never grants twice.")]
    private static void OnGrantFaintMemories(CommandEventArgs e)
    {
        if (e.Length < 1 || World.FindMobile((Serial)e.GetUInt32(0)) is not PlayerMobile { AccessLevel: AccessLevel.Player } target)
        {
            e.Mobile.SendMessage("Specify the serial of a player character.");
            return;
        }

        FaintMemoriesService.TryGrant(target, out var message);
        e.Mobile.SendMessage(message);
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
