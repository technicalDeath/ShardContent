using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The rules of 95.0+ Mastery with no game types, so they can be tested directly. A character has one durable
/// cycle anchor; each skill claims its allowance for a cycle with its first valid use in that cycle, banks at most
/// a few cycles of it, and spends 0.1 per valid use. See docs/Beta-2a-Mastery-Audit.md.
/// </summary>
public static class MasteryEngine
{
    public const int ThresholdFixedPoint = 950;
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

    /// <summary>When the character's Mastery cycles began (UTC); null until the character first holds a 95+ skill.</summary>
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
