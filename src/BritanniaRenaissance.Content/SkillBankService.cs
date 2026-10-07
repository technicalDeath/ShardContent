using Server;
using Server.Logging;
using Server.Misc;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

public enum SkillBankRestoreOutcome
{
    NotApplicable,
    Restored,
    Blocked
}

public static class SkillBankService
{
    private static readonly ILogger Logger = LogFactory.GetLogger(typeof(SkillBankService));
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.SkillBank == true;

    /// <summary>How much one restoration returns, in tenths: 0.2 (owner ruling 2026-10-07), or 0.1 when that is all there is.</summary>
    public static int RestoreStepTenths => ShardRulesConfiguration.Settings?.SkillBank.RestoreStepTenths ?? 2;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        SkillEvents.SkillDisplaced += OnSkillDisplaced;
    }

    /// <summary>One banked skill as the Skill Bank window shows it: the skill now, what is banked, and how the bank may treat it.</summary>
    public sealed record SkillBankRow(int SkillId, string Name, int ActiveTenths, int BankedTenths, BankRetention Retention);

    public sealed record SkillBankView(
        int TotalTenths,
        int CapacityTenths,
        IReadOnlyList<SkillBankRow> Rows,
        FaintMemoriesView? FaintMemories = null
    )
    {
        public bool HasDown => Rows.Any(row => row.Retention == BankRetention.Down);
    }

    public readonly record struct SkillBankDiscardResult(bool Discarded, int Tenths, string Message);

    /// <summary>What the player's Skill Bank holds, or null when the bank is off or its data needs staff review.</summary>
    public static SkillBankView? GetView(PlayerMobile player)
    {
        if (!Enabled || !TryLoad(player, out var ledger))
        {
            return null;
        }

        return new SkillBankView(
            ledger.TotalTenths,
            ledger.CapacityTenths,
            ledger.Balances
                .Select(balance => new SkillBankRow(
                    balance.SkillId,
                    player.Skills[balance.SkillId].Info.Name,
                    player.Skills[balance.SkillId].BaseFixedPoint,
                    balance.Tenths,
                    balance.Retention
                ))
                .ToArray(),
            FaintMemoriesService.GetView(player)
        );
    }

    /// <summary>
    /// Throws away every banked point of one skill, at the player's own request (the window asks them to type the word first).
    /// The skill itself is untouched and the freed room can be used at once.
    /// </summary>
    public static SkillBankDiscardResult Discard(PlayerMobile player, int skillId)
    {
        if (!Enabled)
        {
            return new SkillBankDiscardResult(false, 0, "The Skill Bank is not enabled.");
        }

        if (skillId < 0 || skillId >= player.Skills.Length || player.Skills[skillId] is not { } skill)
        {
            return new SkillBankDiscardResult(false, 0, "That is not a skill.");
        }

        if (!TryLoad(player, out var ledger))
        {
            return new SkillBankDiscardResult(false, 0, "Skill Bank data requires staff review.");
        }

        var name = skill.Info.Name;
        var tenths = ledger.Discard(skillId);
        if (tenths == 0)
        {
            return new SkillBankDiscardResult(false, 0, $"Nothing is banked for {name}.");
        }

        player.SkillBankData = ledger.Serialize();
        ShardAuditLog.Record("skillbank", "discarded", player, null, $"skill={name}; tenths={tenths}");
        return new SkillBankDiscardResult(true, tenths, $"Discarded {GumpStyle.Points(tenths)} banked points of {name}.");
    }

    /// <summary>
    /// A line about how full the bank is, in a player's words, or nothing while there is plenty of room. "Down" is the setting that
    /// lets a banked skill's points be replaced when the bank has no room for new ones.
    /// </summary>
    public static string DescribeFullness(int totalTenths, int capacityTenths, bool hasDown)
    {
        var freeTenths = capacityTenths - totalTenths;
        if (freeTenths > capacityTenths / 10)
        {
            return string.Empty;
        }

        if (freeTenths <= 0)
        {
            return hasDown
                ? "The bank is full. New points can still be saved by replacing points from a skill set to Down."
                : "The bank is full, so new points cannot be saved. Set a banked skill to Down to let its points be replaced.";
        }

        return hasDown
            ? $"The bank is nearly full: room for {GumpStyle.Points(freeTenths)} more points. Points from a skill set to Down can be replaced."
            : $"The bank is nearly full: room for {GumpStyle.Points(freeTenths)} more points. Set a banked skill to Down if you want its points to be replaceable.";
    }

    public static IEnumerable<string> DescribeForStaff(PlayerMobile player)
    {
        yield return $"Skill Bank player: {player.Name} ({player.Serial}); feature enabled: {Enabled}.";
        yield return $"Active skills: {player.Skills.Total / 10.0:0.0}/{player.Skills.Cap / 10.0:0.0} points.";
        yield return player.SkillBankRecoveryArchive is null
            ? "Recovery archive: none."
            : $"Recovery archive: preserved ({player.SkillBankRecoveryArchive.Length} characters).";

        if (!SkillBankLedger.TryDeserialize(
                player.SkillBankData,
                ShardRulesConfiguration.Settings.SkillBank.CapacityTenths,
                id => ResolveSkill(player, id),
                out var ledger
            ))
        {
            yield return "Saved Skill Bank payload is invalid; bank changes are suspended. Do not edit active skills or the payload without a recovery plan.";
            yield break;
        }

        yield return $"Saved Skill Bank payload is valid; {ledger.TotalTenths / 10.0:0.0}/{ledger.CapacityTenths / 10.0:0.0} points across {ledger.Balances.Count} entries; restores {RestoreStepTenths / 10.0:0.0} at a time.";
        foreach (var line in FaintMemoriesService.DescribeForStaff(player))
        {
            yield return line;
        }

        foreach (var balance in ledger.Balances)
        {
            yield return $"{balance.SkillName} ({balance.SkillId}): active {player.Skills[balance.SkillId].Base:0.0}, banked {balance.Tenths / 10.0:0.0}, {balance.Retention}.";
        }
    }

    public static string SetRetention(PlayerMobile player, int skillId, BankRetention retention)
    {
        if (!Enabled)
        {
            return "The Skill Bank is not enabled.";
        }

        if (!TryLoad(player, out var ledger))
        {
            return "Skill Bank data requires staff review.";
        }

        if (!ledger.SetRetention(skillId, retention))
        {
            return "No banked balance exists for that skill.";
        }

        player.SkillBankData = ledger.Serialize();
        return $"{player.Skills[skillId].Info.Name} bank retention set to {retention}.";
    }

    public static string RecoverInvalidPayload(PlayerMobile player, bool isAuthorizedStaff, int capacityTenths)
    {
        var recovery = SkillBankRecovery.Recover(
            player.SkillBankData,
            player.SkillBankRecoveryArchive,
            isAuthorizedStaff,
            capacityTenths,
            id => ResolveSkill(player, id)
        );
        if (recovery.Changed)
        {
            player.SkillBankRecoveryArchive = recovery.ArchivedPayload;
            player.SkillBankData = recovery.ActivePayload;
        }

        if (!recovery.Changed || !isAuthorizedStaff || recovery.Message != SkillBankRecovery.SuccessMessage)
        {
            return recovery.Message;
        }

        Logger.Warning("Staff recovered invalid Skill Bank payload for player={Serial}; original payload archived.",
            player.Serial);
        return recovery.Message;
    }

    public static SkillBankRestoreOutcome TryRestore(PlayerMobile player, Skill skill)
    {
        if (!Enabled || player.Deleted || player.AccessLevel != AccessLevel.Player)
        {
            return SkillBankRestoreOutcome.NotApplicable;
        }

        if (!TryLoad(player, out var ledger))
        {
            return SkillBankRestoreOutcome.Blocked;
        }

        var outcome = RestoreFromValidatedLedger(
            player,
            skill,
            ledger,
            ShardRulesConfiguration.Settings.Character.IndividualSkillCap * 10,
            RestoreStepTenths
        );

        // A skill with no banked points of its own may draw on Faint Memories, which comes back the same way.
        return outcome == SkillBankRestoreOutcome.NotApplicable ? FaintMemoriesService.TryRestore(player, skill) : outcome;
    }

    public static SkillBankRestoreOutcome RestoreFromValidatedLedger(
        PlayerMobile player,
        Skill skill,
        SkillBankLedger ledger,
        int configuredIndividualCapTenths,
        int stepTenths = 1
    )
    {
        if (skill.Owner.Owner != player || configuredIndividualCapTenths <= 0)
        {
            return SkillBankRestoreOutcome.Blocked;
        }

        if (ledger.GetBalance(skill.SkillID) == 0)
        {
            return SkillBankRestoreOutcome.NotApplicable;
        }

        var individualCap = Math.Min(skill.CapFixedPoint, configuredIndividualCapTenths);
        if (skill.Lock != SkillLock.Up || skill.BaseFixedPoint >= individualCap ||
            player.Skills.Total > player.Skills.Cap)
        {
            return SkillBankRestoreOutcome.Blocked;
        }

        var downSkills = new List<SkillBankActiveSkill>();
        if (player.Skills.Total == player.Skills.Cap)
        {
            for (var i = 0; i < player.Skills.Length; i++)
            {
                var candidate = player.Skills[i];
                downSkills.Add(new SkillBankActiveSkill(
                    candidate.SkillID,
                    candidate.Info.Name,
                    candidate.BaseFixedPoint,
                    Math.Min(candidate.CapFixedPoint, configuredIndividualCapTenths),
                    candidate.Lock == SkillLock.Down
                ));
            }
        }

        if (!ledger.TryPlanRestoration(
                skill.SkillID,
                player.Skills.Total,
                player.Skills.Cap,
                downSkills,
                out var plan,
                stepTenths,
                individualCap - skill.BaseFixedPoint
            ))
        {
            return SkillBankRestoreOutcome.Blocked;
        }

        var payload = plan.BankAfter.Serialize();
        var downSkill = plan.DownSkillId is int downId ? player.Skills[downId] : null;
        if (downSkill is not null)
        {
            downSkill.BaseFixedPoint -= plan.DownTenths;
        }

        skill.BaseFixedPoint += plan.RestoredTenths;
        player.SkillBankData = payload;
        return SkillBankRestoreOutcome.Restored;
    }

    private static void OnSkillDisplaced(Mobile mobile, Skill displaced, int lostTenths)
    {
        if (!Enabled || mobile is not PlayerMobile { AccessLevel: AccessLevel.Player } player ||
            lostTenths <= 0 || !TryLoad(player, out var ledger))
        {
            return;
        }

        var individualCap = Math.Min(displaced.CapFixedPoint,
            ShardRulesConfiguration.Settings.Character.IndividualSkillCap * 10);
        if (individualCap <= 0)
        {
            Logger.Warning("Skill Bank deposit rejected for player={Serial}, skill={Skill}: invalid individual cap.",
                player.Serial, displaced.SkillID);
            player.SendMessage("Skill Bank could not store the displaced point. Ask staff to review your skill caps.");
            return;
        }

        var result = ledger.Deposit(displaced.SkillID, displaced.Info.Name, lostTenths, individualCap);
        if (result.BankedTenths > 0)
        {
            player.SkillBankData = ledger.Serialize();
        }

        if (result.UnbankedTenths > 0)
        {
            player.SendMessage($"Skill Bank full: {result.UnbankedTenths / 10.0:0.0} lost skill points were not banked.");
        }

        if (result.ReplacedTenths > 0)
        {
            Logger.Information(
                "Skill Bank replacement: player={Serial}, skill={Skill}, replacedTenths={Replaced}, bankTotalTenths={Total}.",
                player.Serial,
                displaced.SkillID,
                result.ReplacedTenths,
                ledger.TotalTenths
            );
        }
    }

    private static bool TryLoad(PlayerMobile player, out SkillBankLedger ledger)
    {
        if (SkillBankLedger.TryDeserialize(
                player.SkillBankData,
                ShardRulesConfiguration.Settings.SkillBank.CapacityTenths,
                id => ResolveSkill(player, id),
                out ledger
            ))
        {
            return true;
        }

        Logger.Warning("Skill Bank payload rejected for player={Serial}; bank changes suspended.", player.Serial);
        return false;
    }

    private static (string Name, int IndividualCapTenths)? ResolveSkill(PlayerMobile player, int id)
    {
        if (id < 0 || id >= player.Skills.Length)
        {
            return null;
        }

        var skill = player.Skills[id];
        return skill is null ? null : (skill.Info.Name, skill.CapFixedPoint);
    }
}
