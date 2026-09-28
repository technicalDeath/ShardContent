using System.Text.Json;
using System.Text.Json.Serialization;

namespace BritanniaRenaissance.Content;

public enum BankRetention
{
    Locked,
    Down
}

public readonly record struct SkillBankBalance(int SkillId, string SkillName, int Tenths, BankRetention Retention);

public readonly record struct SkillBankDeposit(int BankedTenths, int UnbankedTenths, int ReplacedTenths);

public readonly record struct SkillBankActiveSkill(
    int SkillId, string SkillName, int BaseTenths, int IndividualCapTenths, bool IsDown
);

public readonly record struct SkillBankRestorationPlan(SkillBankLedger BankAfter, int? DownSkillId);
public readonly record struct SkillBankRecoveryResult(bool Changed, string? ArchivedPayload, string? ActivePayload, string Message);

public static class SkillBankRecovery
{
    public const string SuccessMessage = "Invalid Skill Bank data archived and bank reset to empty. Active skills were not changed.";

    public static SkillBankRecoveryResult Recover(
        string? payload,
        string? archive,
        bool isAuthorizedStaff,
        int capacityTenths,
        Func<int, (string Name, int IndividualCapTenths)?> resolveSkill
    )
    {
        if (!isAuthorizedStaff)
        {
            return new(false, archive, payload, "Only authorized staff may recover Skill Bank data.");
        }

        if (SkillBankLedger.TryDeserialize(payload, capacityTenths, resolveSkill, out _))
        {
            return new(false, archive, payload, "The saved Skill Bank payload is valid; no recovery was needed.");
        }

        if (archive is not null)
        {
            return new(false, archive, payload, "A prior invalid Skill Bank payload is already archived; recovery was not repeated.");
        }

        return new(true, payload, new SkillBankLedger(capacityTenths).Serialize(), SuccessMessage);
    }
}

/// <summary>
/// Per-character Skill Bank policy. The gameplay adapter must supply only actual organic
/// skill-cap losses and commit this ledger with the corresponding active-skill changes.
/// </summary>
public sealed class SkillBankLedger
{
    private const int SnapshotVersion = 1;
    private const int MaximumSnapshotLength = 65536;
    private readonly Dictionary<int, SkillBankBalance> _balances = [];

    public SkillBankLedger(int capacityTenths = 3000)
    {
        if (capacityTenths <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(capacityTenths));
        }

        CapacityTenths = capacityTenths;
    }

    public int CapacityTenths { get; }

    public int TotalTenths { get; private set; }

    public IReadOnlyList<SkillBankBalance> Balances =>
        _balances.Values.OrderBy(balance => balance.SkillName, StringComparer.Ordinal).ToArray();

    public int GetBalance(int skillId) =>
        _balances.TryGetValue(skillId, out var balance) ? balance.Tenths : 0;

    public SkillBankLedger Clone()
    {
        var copy = new SkillBankLedger(CapacityTenths) { TotalTenths = TotalTenths };
        foreach (var (id, balance) in _balances)
        {
            copy._balances.Add(id, balance);
        }

        return copy;
    }

    public bool SetRetention(int skillId, BankRetention retention)
    {
        if (!Enum.IsDefined(retention) || !_balances.TryGetValue(skillId, out var balance))
        {
            return false;
        }

        _balances[skillId] = balance with { Retention = retention };
        return true;
    }

    public SkillBankDeposit Deposit(int skillId, string skillName, int tenths, int individualCapTenths)
    {
        if (skillId < 0 || string.IsNullOrWhiteSpace(skillName) || tenths < 0 || individualCapTenths <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(tenths));
        }

        var banked = 0;
        var replaced = 0;
        for (var i = 0; i < tenths; i++)
        {
            var current = GetBalance(skillId);
            if (current >= individualCapTenths)
            {
                continue;
            }

            if (TotalTenths == CapacityTenths)
            {
                var candidate = _balances.Values
                    .Where(balance => balance.Retention == BankRetention.Down)
                    .OrderByDescending(balance => balance.Tenths)
                    .ThenBy(balance => balance.SkillName, StringComparer.Ordinal)
                    .FirstOrDefault();

                if (candidate.Tenths == 0)
                {
                    continue;
                }

                RemoveOne(candidate.SkillId);
                replaced++;
                current = GetBalance(skillId);
            }

            var retention = _balances.TryGetValue(skillId, out var existing)
                ? existing.Retention
                : BankRetention.Locked;
            _balances[skillId] = new SkillBankBalance(skillId, skillName, current + 1, retention);
            TotalTenths++;
            banked++;
        }

        return new SkillBankDeposit(banked, tenths - banked, replaced);
    }

    public bool TryConsume(int skillId)
    {
        if (!_balances.ContainsKey(skillId))
        {
            return false;
        }

        RemoveOne(skillId);
        return true;
    }

    public bool TryPlanRestoration(
        int targetSkillId,
        int activeTotalTenths,
        int activeCapTenths,
        IEnumerable<SkillBankActiveSkill> downSkills,
        out SkillBankRestorationPlan plan
    )
    {
        plan = default;
        if (GetBalance(targetSkillId) == 0 || activeTotalTenths > activeCapTenths)
        {
            return false;
        }

        var afterConsumption = Clone();
        afterConsumption.TryConsume(targetSkillId);
        if (activeTotalTenths < activeCapTenths)
        {
            plan = new SkillBankRestorationPlan(afterConsumption, null);
            return true;
        }

        foreach (var candidate in downSkills)
        {
            if (!candidate.IsDown || candidate.SkillId == targetSkillId ||
                candidate.BaseTenths < 1 || candidate.IndividualCapTenths <= 0)
            {
                continue;
            }

            var candidatePlan = afterConsumption.Clone();
            var deposit = candidatePlan.Deposit(
                candidate.SkillId,
                candidate.SkillName,
                1,
                candidate.IndividualCapTenths
            );
            if (deposit.BankedTenths == 1 && deposit.ReplacedTenths == 0)
            {
                plan = new SkillBankRestorationPlan(candidatePlan, candidate.SkillId);
                return true;
            }
        }

        return false;
    }

    public string Serialize() => JsonSerializer.Serialize(new SkillBankSnapshot
    {
        Version = SnapshotVersion,
        Balances = Balances.ToList()
    });

    public static bool TryDeserialize(
        string? payload,
        int capacityTenths,
        Func<int, (string Name, int IndividualCapTenths)?> resolveSkill,
        out SkillBankLedger ledger
    )
    {
        ledger = new SkillBankLedger(capacityTenths);
        if (string.IsNullOrEmpty(payload))
        {
            return true;
        }

        if (payload.Length > MaximumSnapshotLength || string.IsNullOrWhiteSpace(payload))
        {
            return false;
        }

        SkillBankSnapshot? snapshot;
        try
        {
            snapshot = JsonSerializer.Deserialize<SkillBankSnapshot>(payload);
        }
        catch (JsonException)
        {
            return false;
        }

        if (snapshot is not { Version: SnapshotVersion, Balances: not null })
        {
            return false;
        }

        var total = 0;
        foreach (var balance in snapshot.Balances)
        {
            var skill = resolveSkill(balance.SkillId);
            if (skill is null || string.IsNullOrWhiteSpace(skill.Value.Name) ||
                skill.Value.IndividualCapTenths <= 0 || balance.Tenths <= 0 ||
                balance.Tenths > skill.Value.IndividualCapTenths ||
                !Enum.IsDefined(balance.Retention) ||
                ledger._balances.ContainsKey(balance.SkillId) ||
                total > capacityTenths - balance.Tenths)
            {
                ledger = new SkillBankLedger(capacityTenths);
                return false;
            }

            ledger._balances.Add(
                balance.SkillId,
                balance with { SkillName = skill.Value.Name }
            );
            total += balance.Tenths;
        }

        ledger.TotalTenths = total;
        return true;
    }

    private void RemoveOne(int skillId)
    {
        var balance = _balances[skillId];
        if (balance.Tenths == 1)
        {
            _balances.Remove(skillId);
        }
        else
        {
            _balances[skillId] = balance with { Tenths = balance.Tenths - 1 };
        }

        TotalTenths--;
    }

    private sealed class SkillBankSnapshot
    {
        [JsonPropertyName("version")]
        public int Version { get; set; }

        [JsonPropertyName("balances")]
        public List<SkillBankBalance>? Balances { get; set; }
    }
}
