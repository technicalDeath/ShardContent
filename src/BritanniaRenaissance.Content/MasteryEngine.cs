using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The rules of 80.0+ Mastery with no game types, so they can be tested directly. A character has one durable
/// cycle anchor; each skill claims its allowance for a cycle with its first valid use in that cycle, banks at most
/// a few cycles of it, and spends 0.1 per valid use as a guaranteed gain. Every other use gains by chance through the
/// stock roll. See docs/Mastery-Layered-Plan.md (supersedes docs/Beta-2a-Mastery-Audit.md).
/// </summary>
public static class MasteryEngine
{
    /// <summary>Mastery begins at 80.0 (the "Adept" title); owner ruling 2026-10-09. The allowance is layered on ordinary gain, which carries on to 100.</summary>
    public const int ThresholdFixedPoint = 800;

    /// <summary>The threshold as players read it, e.g. "80.0".</summary>
    public static string ThresholdText => (ThresholdFixedPoint / 10.0).ToString("0.0", CultureInfo.InvariantCulture);
    public const int GrandmasterFixedPoint = 1000;
    public const int AwardTenths = 1;

    /// <summary>The cycle containing <paramref name="nowUtc"/>, counted from the anchor; -1 before the anchor.</summary>
    public static long CycleId(DateTime anchorUtc, DateTime nowUtc, TimeSpan cycleLength)
    {
        var elapsed = nowUtc - anchorUtc;
        return elapsed < TimeSpan.Zero ? -1 : elapsed.Ticks / cycleLength.Ticks;
    }

    public static DateTime NextRefresh(DateTime anchorUtc, DateTime nowUtc, TimeSpan cycleLength)
    {
        var id = CycleId(anchorUtc, nowUtc, cycleLength);
        return anchorUtc + TimeSpan.FromTicks(cycleLength.Ticks * (id + 1));
    }

    public static bool HasClaimed(MasterySkillState skill, long cycleId) => skill.LastClaimedCycle >= cycleId;

    /// <summary>
    /// Claims the allowance for this cycle once. False when this cycle was already claimed or no cycle has begun
    /// (the clock is before the anchor, or went backwards). The bank never exceeds <paramref name="bankCap"/>.
    /// </summary>
    public static bool TryClaim(MasterySkillState skill, long cycleId, int allowanceTenths, int bankCap)
    {
        if (cycleId < 0 || cycleId <= skill.LastClaimedCycle)
        {
            return false;
        }

        skill.LastClaimedCycle = cycleId;
        skill.AllowanceTenths = Math.Min(bankCap, skill.AllowanceTenths + allowanceTenths);
        return true;
    }

    /// <summary>Spends one award from the bank. False when it is empty.</summary>
    public static bool TrySpend(MasterySkillState skill)
    {
        if (skill.AllowanceTenths < AwardTenths)
        {
            return false;
        }

        skill.AllowanceTenths -= AwardTenths;
        return true;
    }

    public static int GainsLeft(int baseFixedPoint) => Math.Max(0, GrandmasterFixedPoint - baseFixedPoint);

    /// <summary>The whole-cycle count a skill needs to climb from Mastery's threshold to 100.0 on its allowance alone.</summary>
    public static int MinimumCycles(int allowanceTenths) =>
        allowanceTenths < 1 ? 0 : (GrandmasterFixedPoint - ThresholdFixedPoint + allowanceTenths - 1) / allowanceTenths;

    /// <summary>What a skill check at or above the threshold does to the skill.</summary>
    public enum UseOutcome
    {
        /// <summary>Below the threshold: ordinary gain only.</summary>
        NotMastery,

        /// <summary>At 100.0 there is nothing left to gain.</summary>
        Finished,

        /// <summary>Not a valid use, or no allowance to spend: stock rolls for a gain, with the class multiplier.</summary>
        ChanceRoll,

        /// <summary>A valid use with allowance in hand: the skill gains +0.1 for certain and the allowance pays for it.</summary>
        Guaranteed
    }

    /// <summary>
    /// The layered rule for one check. A valid use is a success with a gain actually possible. When the cycle's
    /// allowance has not been claimed, a valid use claims it first (up to <paramref name="bankCap"/> in store).
    /// </summary>
    public static UseOutcome Decide(
        int baseFixedPoint, bool validUse, bool claimedThisCycle, int storedTenths, int allowanceTenths, int bankCap
    )
    {
        if (baseFixedPoint < ThresholdFixedPoint)
        {
            return UseOutcome.NotMastery;
        }

        if (baseFixedPoint >= GrandmasterFixedPoint)
        {
            return UseOutcome.Finished;
        }

        if (!validUse)
        {
            return UseOutcome.ChanceRoll;
        }

        var available = claimedThisCycle ? storedTenths : Math.Min(bankCap, storedTenths + allowanceTenths);
        return available >= AwardTenths ? UseOutcome.Guaranteed : UseOutcome.ChanceRoll;
    }

    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.General);

    public static string Serialize(MasteryCharacterState state) => JsonSerializer.Serialize(state, JsonOptions);

    /// <summary>
    /// Reads saved state. Anything unreadable, empty, or from an earlier mechanic (version 1: shared UTC periods,
    /// login days, pending increments) yields a fresh state and sets <paramref name="discarded"/> for a non-empty value.
    /// </summary>
    public static MasteryCharacterState Parse(string? json, out bool discarded)
    {
        discarded = false;

        if (string.IsNullOrWhiteSpace(json))
        {
            return new MasteryCharacterState();
        }

        try
        {
            var state = JsonSerializer.Deserialize<MasteryCharacterState>(json, JsonOptions);

            if (state is { Version: MasteryCharacterState.CurrentVersion })
            {
                state.Skills ??= [];
                return state;
            }
        }
        catch (JsonException)
        {
        }

        discarded = true;
        return new MasteryCharacterState();
    }

    public static string FormatDuration(TimeSpan span)
    {
        if (span < TimeSpan.Zero)
        {
            span = TimeSpan.Zero;
        }

        return span.TotalHours >= 1
            ? string.Format(CultureInfo.InvariantCulture, "{0}h {1}m", (int)span.TotalHours, span.Minutes)
            : string.Format(CultureInfo.InvariantCulture, "{0}m", Math.Max(1, (int)Math.Ceiling(span.TotalMinutes)));
    }
}

public sealed class MasteryCharacterState
{
    public const int CurrentVersion = 2;

    [JsonPropertyName("version")]
    public int Version { get; set; } = CurrentVersion;

    /// <summary>When the character's Mastery cycles began (UTC); null until the character first holds a skill at the Mastery threshold.</summary>
    [JsonPropertyName("anchor")]
    public DateTime? AnchorUtc { get; set; }

    [JsonPropertyName("skills")]
    public Dictionary<int, MasterySkillState> Skills { get; set; } = [];
}

public sealed class MasterySkillState
{
    /// <summary>The last cycle this skill claimed; -1 for none.</summary>
    [JsonPropertyName("claimed")]
    public long LastClaimedCycle { get; set; } = -1;

    /// <summary>Unspent allowance in tenths of a skill point.</summary>
    [JsonPropertyName("allowance")]
    public int AllowanceTenths { get; set; }
}
