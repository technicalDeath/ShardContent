using System.Globalization;
using Server;
using Server.Accounting;
using Server.Misc;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Runs 90.0+ Mastery in the game (docs/Beta-2a-Mastery-Audit.md). The rules are <see cref="MasteryEngine"/>. This
/// subscribes once to <see cref="SkillEvents.SkillGainOverride"/>, which stock calls after its eligibility checks
/// and before its own gain roll, so a decision made here never reaches the gain-chance multiplier or any
/// temporary gain bonus. Skill Bank restoration still acts first.
/// </summary>
public static class MasteryProgression
{
    public const int ThresholdFixedPoint = MasteryEngine.ThresholdFixedPoint;
    public const int GrandmasterFixedPoint = MasteryEngine.GrandmasterFixedPoint;

    private const string TagPrefix = "BritanniaRenaissance.Mastery.";
    private static readonly Dictionary<int, MasteryCharacterState> States = new();
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        SkillEvents.SkillGainOverride += HandleSkillGain;
        EventSink.Connected += OnConnected;
    }

    private static MasteryRules Rules => ShardRulesConfiguration.Settings?.Mastery ?? new MasteryRules();

    private static TimeSpan CycleLength => TimeSpan.FromHours(Rules.CycleHours);

    public static int AllowanceTenths(SkillName skill)
    {
        var rules = Rules;
        var className = ShardRulesConfiguration.Settings is { } settings
            ? SkillGainCurveService.ClassOf(settings.SkillGain, skill)
            : null;

        return rules.AllowanceTenths.TryGetValue(className ?? "standard", out var tenths)
            ? tenths
            : rules.AllowanceTenths.GetValueOrDefault("standard", 10);
    }

    public static string ClassName(SkillName skill) =>
        (ShardRulesConfiguration.Settings is { } settings ? SkillGainCurveService.ClassOf(settings.SkillGain, skill) : null) ??
        "standard";

    public static IEnumerable<string> DescribeStatus(Mobile viewer, Mobile subject)
    {
        if (subject is not PlayerMobile pm)
        {
            yield return "Mastery applies to player characters.";
            yield break;
        }

        var rules = Rules;
        var now = Core.Now;
        var state = GetState(pm);

        if (!ReferenceEquals(viewer, subject))
        {
            yield return $"Mastery for {pm.Name}:";
        }

        yield return $"Mastery: a skill at {MasteryEngine.ThresholdText} or above gains +0.1 for each valid, successful use while it has allowance.";
        yield return "A use is valid only if it had a real chance of failing. Trivially easy actions and failed attempts count for nothing.";
        yield return $"Your Mastery cycle is {rules.CycleHours} hours. A skill claims its allowance for a cycle with its first valid use in that cycle; a cycle it does not use is lost. Unspent allowance carries up to {rules.BankCycles} cycles.";

        if (state.AnchorUtc is not { } anchor)
        {
            var waiting = false;
            for (var i = 0; i < pm.Skills.Length; i++)
            {
                waiting |= pm.Skills[i] is { } s && s.BaseFixedPoint >= ThresholdFixedPoint &&
                           s.BaseFixedPoint < GrandmasterFixedPoint;
            }

            yield return waiting
                ? $"Your Mastery cycle begins with your next valid use of a skill at {MasteryEngine.ThresholdText} or above."
                : $"No skill is in Mastery yet (Mastery begins at {MasteryEngine.ThresholdText}).";
            yield break;
        }

        var cycle = MasteryEngine.CycleId(anchor, now, CycleLength);
        var next = MasteryEngine.NextRefresh(anchor, now, CycleLength);
        yield return $"Your next cycle begins in {MasteryEngine.FormatDuration(next - now)}.";

        var any = false;
        for (var i = 0; i < pm.Skills.Length; i++)
        {
            var skill = pm.Skills[i];
            if (skill is null || skill.BaseFixedPoint < ThresholdFixedPoint)
            {
                continue;
            }

            any = true;
            var allowance = AllowanceTenths(skill.SkillName);
            state.Skills.TryGetValue(skill.SkillID, out var skillState);
            var claimed = skillState is not null && MasteryEngine.HasClaimed(skillState, cycle);
            yield return string.Format(
                CultureInfo.InvariantCulture,
                "{0} {1:0.0} ({2}): {3:0.0} per cycle, {4:0.0} stored (holds up to {5:0.0}), {6}, {7:0.0} points to reach 100.0.",
                skill.Info.Name,
                skill.Base,
                ClassName(skill.SkillName),
                allowance / 10.0,
                (skillState?.AllowanceTenths ?? 0) / 10.0,
                allowance * rules.BankCycles / 10.0,
                claimed ? "claimed this cycle" : "not claimed this cycle",
                MasteryEngine.GainsLeft(skill.BaseFixedPoint) / 10.0
            );
        }

        if (!any)
        {
            yield return $"No skill is at {MasteryEngine.ThresholdText} or above right now; Mastery state for skills that fell below it is kept.";
        }
    }

    private static void OnConnected(Mobile mobile)
    {
        if (mobile is not PlayerMobile pm || pm.AccessLevel != AccessLevel.Player)
        {
            return;
        }

        var state = GetState(pm);
        var now = Core.Now;
        var inMastery = false;

        for (var i = 0; i < pm.Skills.Length; i++)
        {
            if (pm.Skills[i] is { } skill && skill.BaseFixedPoint >= ThresholdFixedPoint &&
                skill.BaseFixedPoint < GrandmasterFixedPoint)
            {
                inMastery = true;
                break;
            }
        }

        if (!inMastery)
        {
            return;
        }

        if (state.AnchorUtc is null)
        {
            state.AnchorUtc = now;
            SaveState(pm, state);
        }

        var cycle = MasteryEngine.CycleId(state.AnchorUtc.Value, now, CycleLength);
        var unclaimed = 0;

        for (var i = 0; i < pm.Skills.Length; i++)
        {
            if (pm.Skills[i] is { } skill && skill.BaseFixedPoint >= ThresholdFixedPoint &&
                skill.BaseFixedPoint < GrandmasterFixedPoint &&
                (!state.Skills.TryGetValue(skill.SkillID, out var s) || !MasteryEngine.HasClaimed(s, cycle)))
            {
                unclaimed++;
            }
        }

        if (unclaimed > 0)
        {
            // The client is not ready for messages while the connection event runs.
            Server.Timer.DelayCall(TimeSpan.FromSeconds(3), () =>
            {
                if (!pm.Deleted && pm.NetState?.Running == true)
                {
                    pm.SendMessage(
                        $"Mastery: {unclaimed} of your Mastery skills can claim this cycle's allowance with a valid use. Use [MasteryStatus for details."
                    );
                }
            });
        }
    }

    /// <summary>
    /// A gain is possible if the skill is Up-locked and below its cap, and either the character is under the total
    /// cap or a Down-locked skill can be lowered, which is the stock way of making room.
    /// </summary>
    public static bool CanGain(PlayerMobile pm, Skill skill)
    {
        if (skill.Lock != SkillLock.Up || skill.BaseFixedPoint >= skill.CapFixedPoint)
        {
            return false;
        }

        if (pm.Skills.Total < pm.Skills.Cap)
        {
            return true;
        }

        for (var i = 0; i < pm.Skills.Length; i++)
        {
            var other = pm.Skills[i];
            if (other is not null && other != skill && other.Lock == SkillLock.Down &&
                other.BaseFixedPoint >= MasteryEngine.AwardTenths)
            {
                return true;
            }
        }

        return false;
    }

    /// <summary>
    /// Called by the ModernUO skill engine after region and anti-macro eligibility checks. Returning true always
    /// suppresses the stock gain path for player skills at the threshold and above, including when nothing is awarded.
    /// </summary>
    public static bool HandleSkillGain(Mobile mobile, Skill skill, bool success)
    {
        if (mobile is not PlayerMobile pm || pm.AccessLevel != AccessLevel.Player)
        {
            return false;
        }

        if (SkillBankService.TryRestore(pm, skill) != SkillBankRestoreOutcome.NotApplicable)
        {
            return true;
        }

        if (skill.BaseFixedPoint < ThresholdFixedPoint)
        {
            return false;
        }

        if (skill.BaseFixedPoint >= GrandmasterFixedPoint)
        {
            return true;
        }

        var now = Core.Now;
        var state = GetState(pm);
        var changed = false;

        if (state.AnchorUtc is null)
        {
            state.AnchorUtc = now;
            changed = true;
        }

        if (!state.Skills.TryGetValue(skill.SkillID, out var skillState))
        {
            skillState = new MasterySkillState();
            state.Skills[skill.SkillID] = skillState;
            changed = true;
            pm.SendMessage(
                $"{skill.Info.Name} has reached {MasteryEngine.ThresholdText}: ordinary gain has ended and Mastery begins. Use [MasteryStatus to see your allowance."
            );
        }

        // A valid use: the check succeeded and a gain is actually possible. Anything else claims and spends nothing.
        if (!success || !CanGain(pm, skill))
        {
            if (changed)
            {
                SaveState(pm, state);
            }

            return true;
        }

        var rules = Rules;
        var allowance = AllowanceTenths(skill.SkillName);
        var cycle = MasteryEngine.CycleId(state.AnchorUtc.Value, now, CycleLength);

        if (MasteryEngine.TryClaim(skillState, cycle, allowance, allowance * rules.BankCycles))
        {
            changed = true;
            pm.SendMessage($"Mastery: {skill.Info.Name} claims this cycle's allowance of {allowance / 10.0:0.0}.");
        }

        if (MasteryEngine.TrySpend(skillState))
        {
            var before = skill.BaseFixedPoint;
            SkillCheck.Gain(pm, skill, organicAttempt: true);

            if (skill.BaseFixedPoint <= before)
            {
                // Stock declined the gain (nothing to displace after all): give the allowance back.
                skillState.AllowanceTenths += MasteryEngine.AwardTenths;
            }
            else
            {
                if (skill.BaseFixedPoint > before + MasteryEngine.AwardTenths)
                {
                    // Never more than +0.1 per consumed use, whatever stock multiplied it by.
                    skill.BaseFixedPoint = before + MasteryEngine.AwardTenths;
                }

                if (skill.BaseFixedPoint >= GrandmasterFixedPoint)
                {
                    // Mastery ends at 100.0 and unused allowance goes with it.
                    state.Skills.Remove(skill.SkillID);
                    pm.SendMessage($"{skill.Info.Name} has reached Grandmaster ({skill.Base:0.0}).");
                }
                else
                {
                    pm.SendMessage(
                        $"Mastery advanced {skill.Info.Name} to {skill.Base:0.0}. Allowance left: {skillState.AllowanceTenths / 10.0:0.0}."
                    );
                }
            }

            changed = true;
        }

        if (changed)
        {
            SaveState(pm, state);
        }

        return true;
    }

    private static MasteryCharacterState GetState(PlayerMobile pm)
    {
        var serial = unchecked((int)pm.Serial.Value);
        if (States.TryGetValue(serial, out var state))
        {
            return state;
        }

        state = LoadState(pm);
        States[serial] = state;
        return state;
    }

    private static MasteryCharacterState LoadState(PlayerMobile pm)
    {
        if (pm.Account is not Account account)
        {
            return new MasteryCharacterState();
        }

        return MasteryEngine.Parse(account.GetTag(TagFor(pm)), out _);
    }

    private static void SaveState(PlayerMobile pm, MasteryCharacterState state)
    {
        if (pm.Account is Account account)
        {
            account.SetTag(TagFor(pm), MasteryEngine.Serialize(state));
        }
    }

    private static string TagFor(PlayerMobile pm) =>
        TagPrefix + pm.Serial.Value.ToString("X8", CultureInfo.InvariantCulture);

    /// <summary>Test and staff support: forget the cached state so the next use reloads it from the account tag.</summary>
    public static void ForgetCachedState(PlayerMobile pm) => States.Remove(unchecked((int)pm.Serial.Value));

    /// <summary>Staff support: move this character's cycle anchor back, to rehearse time passing.</summary>
    public static void ShiftAnchorEarlier(PlayerMobile pm, TimeSpan by)
    {
        var state = GetState(pm);
        if (state.AnchorUtc is { } anchor)
        {
            state.AnchorUtc = anchor - by;
            SaveState(pm, state);
        }
    }
}

/// <summary>Mastery settings from shard-rules.json (<c>mastery</c>).</summary>
public sealed class MasteryRules
{
    [System.Text.Json.Serialization.JsonPropertyName("cycleHours")]
    public int CycleHours { get; set; } = 24;

    [System.Text.Json.Serialization.JsonPropertyName("bankCycles")]
    public int BankCycles { get; set; } = 3;

    /// <summary>Allowance per cycle in tenths of a skill point, by <c>skillGain</c> class.</summary>
    [System.Text.Json.Serialization.JsonPropertyName("allowanceTenths")]
    public Dictionary<string, int> AllowanceTenths { get; set; } = new(StringComparer.OrdinalIgnoreCase)
    {
        ["easy"] = 20,
        ["standard"] = 10,
        ["hard"] = 6,
        ["veryHard"] = 4
    };

    private static readonly string[] ClassNames = ["easy", "standard", "hard", "veryHard"];

    public static void Validate(MasteryRules rules, List<string> errors)
    {
        if (rules.CycleHours is < 1 or > 168)
        {
            errors.Add("mastery.cycleHours must be between 1 and 168.");
        }

        if (rules.BankCycles is < 1 or > 10)
        {
            errors.Add("mastery.bankCycles must be between 1 and 10.");
        }

        foreach (var name in ClassNames)
        {
            if (!rules.AllowanceTenths.TryGetValue(name, out var tenths))
            {
                errors.Add($"mastery.allowanceTenths must define '{name}'.");
            }
            else if (tenths is < 1 or > 50)
            {
                errors.Add($"mastery.allowanceTenths '{name}' must be between 1 and 50 tenths.");
            }
        }

        foreach (var name in rules.AllowanceTenths.Keys)
        {
            if (!ClassNames.Contains(name, StringComparer.OrdinalIgnoreCase))
            {
                errors.Add($"mastery.allowanceTenths '{name}' is not one of {string.Join(", ", ClassNames)}.");
            }
        }
    }
}
