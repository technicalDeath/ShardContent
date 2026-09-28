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

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        SkillEvents.SkillDisplaced += OnSkillDisplaced;
    }

    public static IEnumerable<string> Describe(Mobile mobile)
    {
        if (!Enabled)
        {
            yield return "The Skill Bank is not enabled.";
            yield break;
        }

        if (mobile is not PlayerMobile player)
        {
            yield break;
        }

        if (!TryLoad(player, out var ledger))
        {
            yield return "Skill Bank data requires staff review.";
            yield break;
        }

        yield return $"Skill Bank: {ledger.TotalTenths / 10.0:0.0}/{ledger.CapacityTenths / 10.0:0.0} points.";
        yield return $"Free bank capacity: {(ledger.CapacityTenths - ledger.TotalTenths) / 10.0:0.0} points.";
        foreach (var warning in DescribeCapacityRisk(ledger))
        {
            yield return warning;
        }

        yield return "Use [SkillBank lock <skill> or [SkillBank down <skill> to set bank retention.";
        foreach (var balance in ledger.Balances)
        {
            var active = player.Skills[balance.SkillId].Base;
            yield return $"{balance.SkillName} ({balance.SkillId}): active {active:0.0}, banked {balance.Tenths / 10.0:0.0}, {balance.Retention}.";
        }
    }

    public static IEnumerable<string> DescribeCapacityRisk(SkillBankLedger ledger)
    {
        var freeTenths = ledger.CapacityTenths - ledger.TotalTenths;
        if (freeTenths > ledger.CapacityTenths / 10)
        {
            yield break;
        }

        var hasDownBalance = ledger.Balances.Any(balance => balance.Retention == BankRetention.Down);
        if (freeTenths == 0)
        {
            yield return hasDownBalance
                ? "Skill Bank full: a new eligible loss may replace points from the largest banked Down entry."
                : "The next displaced skill point cannot be banked until capacity is freed or a banked entry is set Down.";
            yield break;
        }

        yield return hasDownBalance
            ? $"Skill Bank nearing capacity: {freeTenths / 10.0:0.0} points remain; later eligible losses may replace banked Down entries."
            : $"Skill Bank nearing capacity: {freeTenths / 10.0:0.0} points remain; eligible losses beyond that amount will not be banked unless an entry is set Down.";
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

        yield return $"Saved Skill Bank payload is valid; {ledger.TotalTenths / 10.0:0.0}/{ledger.CapacityTenths / 10.0:0.0} points across {ledger.Balances.Count} entries.";
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

        return RestoreFromValidatedLedger(
            player,
            skill,
            ledger,
            ShardRulesConfiguration.Settings.Character.IndividualSkillCap * 10
        );
    }

    public static SkillBankRestoreOutcome RestoreFromValidatedLedger(
        PlayerMobile player,
        Skill skill,
        SkillBankLedger ledger,
        int configuredIndividualCapTenths
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
                out var plan
            ))
        {
            return SkillBankRestoreOutcome.Blocked;
        }

        var payload = plan.BankAfter.Serialize();
        var downSkill = plan.DownSkillId is int downId ? player.Skills[downId] : null;
        if (downSkill is not null)
        {
            downSkill.BaseFixedPoint--;
        }

        skill.BaseFixedPoint++;
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
