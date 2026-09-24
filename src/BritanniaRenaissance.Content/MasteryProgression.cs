using System.Diagnostics;
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;
using Server;
using Server.Accounting;
using Server.Misc;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Alpha 1's server-controlled 95.0+ skill progression. Periods are aligned to UTC and are
/// identical for every character; only dates on which the character logged in are eligible.
/// </summary>
public static class MasteryProgression
{
    public const int ThresholdFixedPoint = 950;
    public const int GrandmasterFixedPoint = 1000;
    public const int AwardTenths = 1;
    public const int PendingCapTenths = 6;
    public static readonly TimeSpan PeriodLength = TimeSpan.FromHours(4);

    private const int StateVersion = 1;
    private const string TagPrefix = "BritanniaRenaissance.Mastery.";
    private const int OnlineBatchSize = 64;
    private const double OnlineBatchBudgetMilliseconds = 2.0;
    private const int PeriodsPerUtcDay = 6;
    private static readonly Dictionary<int, CharacterState> States = new();
    private static readonly Queue<OnlineReconcileRequest> PendingOnlineReconciliations = new();
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.General);
    private static long _lastObservedCompletedPeriodId = -1;
    private static bool _onlineBatchScheduled;

    public static void Configure()
    {
        SkillEvents.SkillGainOverride += HandleSkillGain;
        EventSink.Connected += OnConnected;
        Server.Timer.StartTimer(TimeSpan.FromSeconds(2), TimeSpan.FromSeconds(10), ProcessOnlinePlayers);
    }

    public static long GetPeriodId(DateTime utc)
    {
        utc = utc.ToUniversalTime();
        return (utc.Ticks - DateTime.UnixEpoch.Ticks) / PeriodLength.Ticks;
    }

    public static DateTime GetPeriodStart(long periodId) =>
        DateTime.UnixEpoch.AddTicks(periodId * PeriodLength.Ticks);

    public static DateTime GetNextBoundary(DateTime utc) =>
        GetPeriodStart(GetPeriodId(utc) + 1);

    public static int GetUtcDayKey(DateTime utc)
    {
        var date = DateOnly.FromDateTime(utc.ToUniversalTime());
        return date.DayNumber - DateOnly.FromDateTime(DateTime.UnixEpoch).DayNumber;
    }

    public static IEnumerable<string> DescribeStatus(Mobile mobile)
    {
        var now = Core.Now;
        yield return $"Mastery schedule: fixed 4-hour UTC periods at 00:00, 04:00, 08:00, 12:00, 16:00, and 20:00.";
        yield return $"Next award boundary: {GetNextBoundary(now):yyyy-MM-dd HH:mm} UTC.";

        if (mobile is not PlayerMobile pm)
        {
            yield break;
        }

        var state = GetState(pm);
        var today = GetUtcDayKey(now);
        yield return $"Today qualified: {state.QualifiedDays.Contains(today)}.";

        var any = false;
        for (var i = 0; i < pm.Skills.Length; i++)
        {
            var skill = pm.Skills[i];
            if (skill is null || skill.BaseFixedPoint < ThresholdFixedPoint)
            {
                continue;
            }

            any = true;
            var skillState = state.Skills.TryGetValue(skill.SkillID, out var existingSkillState)
                ? existingSkillState
                : new SkillState { LastProcessedPeriodId = GetPeriodId(now) };
            var remaining = Math.Max(0, GrandmasterFixedPoint - skill.BaseFixedPoint);
            yield return string.Format(
                CultureInfo.InvariantCulture,
                "{0}: {1:0.0}, pending {2:0.0}/{3:0.0}, {4} tenths remaining.",
                skill.Info.Name,
                skill.Base,
                skillState.PendingTenths / 10.0,
                PendingCapTenths / 10.0,
                remaining
            );
        }

        if (!any)
        {
            yield return "No skill is currently in Mastery (Mastery begins at 95.0).";
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
        var day = GetUtcDayKey(now);
        var newlyQualified = state.QualifiedDays.Add(day);
        var deposited = Reconcile(pm, now, out var reconciledStateChanged);
        if (newlyQualified && !reconciledStateChanged)
        {
            SaveState(pm, state);
        }

        if (newlyQualified || deposited > 0)
        {
            pm.SendMessage(
                $"Mastery schedule: this UTC day is qualified. Reconciled {deposited / 10.0:0.0} pending skill across your Mastery skills."
            );
        }
    }

    private static void ProcessOnlinePlayers()
    {
        // Timer callbacks run on the ModernUO loop. Keep world/account mutations on that loop and
        // use the ten-second callback only as a cheap boundary observer; there is no reason to
        // scan online players between four-hour period changes.
        var now = Core.Now;
        var lastCompletedPeriodId = GetPeriodId(now) - 1;
        if (lastCompletedPeriodId <= _lastObservedCompletedPeriodId)
        {
            return;
        }

        _lastObservedCompletedPeriodId = lastCompletedPeriodId;

        foreach (var netState in NetState.Instances)
        {
            if (netState.Mobile is not PlayerMobile pm || pm.AccessLevel != AccessLevel.Player)
            {
                continue;
            }

            PendingOnlineReconciliations.Enqueue(new OnlineReconcileRequest(pm, now));
        }

        ScheduleOnlineBatch();
    }

    private static void ScheduleOnlineBatch()
    {
        if (_onlineBatchScheduled || PendingOnlineReconciliations.Count == 0)
        {
            return;
        }

        _onlineBatchScheduled = true;
        Server.Timer.DelayCall(TimeSpan.Zero, ProcessOnlineBatch);
    }

    private static void ProcessOnlineBatch()
    {
        // A zero-delay timer yields to the next server loop slice without moving state to a
        // background thread. The count and time budget together keep a large population from
        // monopolizing one tick.
        _onlineBatchScheduled = false;
        var startedAt = Stopwatch.GetTimestamp();
        var processed = 0;

        while (PendingOnlineReconciliations.Count > 0 && processed < OnlineBatchSize &&
               (processed == 0 || Stopwatch.GetElapsedTime(startedAt).TotalMilliseconds < OnlineBatchBudgetMilliseconds))
        {
            var request = PendingOnlineReconciliations.Dequeue();
            processed++;

            if (request.Player.Deleted || request.Player.AccessLevel != AccessLevel.Player ||
                request.Player.NetState?.Running != true)
            {
                continue;
            }

            var deposited = Reconcile(request.Player, request.ObservedAt, out _);
            if (deposited > 0)
            {
                request.Player.SendMessage(
                    $"Mastery period awarded {deposited / 10.0:0.0} pending skill. Use eligible skills to consume it."
                );
            }
        }

        ScheduleOnlineBatch();
    }

    /// <summary>
    /// Called by the ModernUO skill engine after region and anti-macro eligibility checks. Returning
    /// true always suppresses the stock gain path for player skills at 95+, including when no
    /// pending increment is available.
    /// </summary>
    public static bool HandleSkillGain(Mobile mobile, Skill skill, bool success)
    {
        if (mobile is not PlayerMobile pm || pm.AccessLevel != AccessLevel.Player ||
            skill.BaseFixedPoint < ThresholdFixedPoint)
        {
            return false;
        }

        var now = Core.Now;
        var state = GetState(pm);
        _ = state.QualifiedDays.Contains(GetUtcDayKey(now));
        Reconcile(pm, now, out _);

        var skillState = GetSkillState(pm, skill, now, out _);

        if (skill.BaseFixedPoint >= GrandmasterFixedPoint || skill.Lock != SkillLock.Up ||
            pm.Skills.Total >= pm.Skills.Cap || skill.BaseFixedPoint >= skill.CapFixedPoint ||
            skillState.PendingTenths < AwardTenths)
        {
            return true;
        }

        skill.BaseFixedPoint += AwardTenths;
        skillState.PendingTenths -= AwardTenths;

        if (skill.BaseFixedPoint >= GrandmasterFixedPoint)
        {
            // Unused pending increments cannot be carried beyond Grandmaster.
            skillState.PendingTenths = 0;
        }

        SaveState(pm, state);
        pm.SendMessage($"Mastery advanced {skill.Info.Name} to {skill.Base:0.0}. Pending: {skillState.PendingTenths / 10.0:0.0}/{PendingCapTenths / 10.0:0.0}.");
        return true;
    }

    private static int Reconcile(PlayerMobile pm, DateTime now, out bool stateChanged)
    {
        var state = GetState(pm);
        var deposited = 0;
        stateChanged = false;
        var lastCompleted = GetPeriodId(now) - 1;

        for (var i = 0; i < pm.Skills.Length; i++)
        {
            var skill = pm.Skills[i];
            if (skill is null || skill.BaseFixedPoint < ThresholdFixedPoint)
            {
                continue;
            }

            var skillState = GetSkillState(pm, skill, now, out var skillStateCreated);
            stateChanged |= skillStateCreated;
            if (skillState.LastProcessedPeriodId >= lastCompleted)
            {
                continue;
            }

            var availablePending = PendingCapTenths - skillState.PendingTenths;
            if (skill.BaseFixedPoint < GrandmasterFixedPoint && availablePending > 0)
            {
                var eligiblePeriods = CountEligiblePeriods(
                    skillState.LastProcessedPeriodId + 1,
                    lastCompleted,
                    state.QualifiedDays,
                    availablePending
                );
                var awarded = Math.Min(eligiblePeriods, availablePending);
                if (awarded > 0)
                {
                    skillState.PendingTenths += awarded * AwardTenths;
                    deposited += awarded * AwardTenths;
                    stateChanged = true;
                }
            }

            // A full bank deliberately consumes all observed periods: the cap prevents hoarding
            // and requires active skill use before later periods can bank additional points.
            if (skillState.LastProcessedPeriodId != lastCompleted)
            {
                skillState.LastProcessedPeriodId = lastCompleted;
                stateChanged = true;
            }
        }

        if (stateChanged)
        {
            SaveState(pm, state);
        }

        return deposited;
    }

    private static int CountEligiblePeriods(
        long firstPeriod,
        long lastPeriod,
        HashSet<int> qualifiedDays,
        int maximum)
    {
        if (firstPeriod > lastPeriod || maximum <= 0 || qualifiedDays.Count == 0)
        {
            return 0;
        }

        var firstDay = GetUtcDayKey(GetPeriodStart(firstPeriod));
        var lastDay = GetUtcDayKey(GetPeriodStart(lastPeriod));
        var total = 0;

        // Qualified dates are sparse and the pending cap is six tenths, so counting the small
        // number of eligible dates is substantially cheaper than walking every missed period.
        foreach (var day in qualifiedDays)
        {
            if (day < firstDay || day > lastDay)
            {
                continue;
            }

            var dayFirstPeriod = GetPeriodId(DateTime.UnixEpoch.AddDays(day));
            var dayLastPeriod = dayFirstPeriod + PeriodsPerUtcDay - 1;
            var overlapStart = Math.Max(firstPeriod, dayFirstPeriod);
            var overlapEnd = Math.Min(lastPeriod, dayLastPeriod);
            if (overlapStart > overlapEnd)
            {
                continue;
            }

            total += (int)Math.Min(maximum - total, overlapEnd - overlapStart + 1);
            if (total >= maximum)
            {
                return maximum;
            }
        }

        return total;
    }

    private static CharacterState GetState(PlayerMobile pm)
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

    private static SkillState GetSkillState(PlayerMobile pm, Skill skill, DateTime now, out bool created)
    {
        var state = GetState(pm);
        if (!state.Skills.TryGetValue(skill.SkillID, out var skillState))
        {
            skillState = new SkillState
            {
                LastProcessedPeriodId = GetPeriodId(now)
            };
            state.Skills[skill.SkillID] = skillState;
            created = true;
            return skillState;
        }

        created = false;
        return skillState;
    }

    private static CharacterState LoadState(PlayerMobile pm)
    {
        if (pm.Account is not Account account)
        {
            return new CharacterState();
        }

        var value = account.GetTag(TagPrefix + pm.Serial.Value.ToString("X8", CultureInfo.InvariantCulture));
        if (string.IsNullOrWhiteSpace(value))
        {
            return new CharacterState();
        }

        try
        {
            return JsonSerializer.Deserialize<CharacterState>(value, JsonOptions) ?? new CharacterState();
        }
        catch (JsonException)
        {
            return new CharacterState();
        }
    }

    private static void SaveState(PlayerMobile pm, CharacterState state)
    {
        if (pm.Account is Account account)
        {
            account.SetTag(
                TagPrefix + pm.Serial.Value.ToString("X8", CultureInfo.InvariantCulture),
                JsonSerializer.Serialize(state, JsonOptions)
            );
        }
    }

    private readonly record struct OnlineReconcileRequest(PlayerMobile Player, DateTime ObservedAt);

    public sealed class CharacterState
    {
        public CharacterState()
        {
        }

        [JsonPropertyName("version")]
        public int Version { get; set; } = StateVersion;

        [JsonPropertyName("qualifiedDays")]
        public HashSet<int> QualifiedDays { get; set; } = [];

        [JsonPropertyName("skills")]
        public Dictionary<int, SkillState> Skills { get; set; } = [];
    }

    public sealed class SkillState
    {
        public SkillState()
        {
        }

        [JsonPropertyName("lastProcessedPeriodId")]
        public long LastProcessedPeriodId { get; set; } = -1;

        [JsonPropertyName("pendingTenths")]
        public int PendingTenths { get; set; }
    }
}
