using System.Globalization;
using Server;
using Server.Accounting;
using Server.Engines.CharacterCreation;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>What a character has left of Faint Memories and when it was granted (the character's creation).</summary>
public readonly record struct FaintMemoriesState(DateTime GrantedUtc, int RemainingTenths);

public enum FaintMemoriesPhase
{
    Locked,
    Ready
}

/// <summary>What the Skill Bank window shows for Faint Memories. There is no view once the points are used up.</summary>
public sealed record FaintMemoriesView(
    FaintMemoriesPhase Phase,
    int RemainingTenths,
    int PointsTenths,
    double UnlockFraction,
    TimeSpan UnlockIn
);

/// <summary>
/// The rules of Faint Memories with no game types, so they can be tested directly (owner request 2026-10-07). Every new character
/// holds a small pool of free skill points. Twenty-four hours after the character was created they come back the way Skill Bank
/// points do: on a skill use the anti-macro check allows, into a skill set to Up, a step at a time, instead of the gain roll.
/// </summary>
public static class FaintMemoriesPolicy
{
    public const string Name = "Faint Memories";
    public const string Theme = "Faint memories of a past in Britannia linger, and skills of the past come back to you.";

    private const int TagVersion = 1;

    public static int PointsTenths(FaintMemoriesRules rules) => ToTenths(rules.Points);

    public static int FloorTenths(FaintMemoriesRules rules) => ToTenths(rules.Floor);

    public static int CeilingTenths(FaintMemoriesRules rules) => ToTenths(rules.Ceiling);

    private static int ToTenths(double points) => (int)Math.Round(points * 10.0, MidpointRounding.AwayFromZero);

    public static void Validate(FaintMemoriesRules rules, List<string> errors)
    {
        static bool IsWholeTenths(double value) => Math.Abs(value * 10.0 - Math.Round(value * 10.0)) < 1e-6;

        if (rules.Points < 0.1 || rules.Points > 50.0 || !IsWholeTenths(rules.Points))
        {
            errors.Add("faintMemories.points must be between 0.1 and 50.0, in tenths.");
        }

        if (rules.UnlockHours < 0.0 || rules.UnlockHours > 720.0)
        {
            errors.Add("faintMemories.unlockHours must be between 0 and 720.");
        }

        if (rules.Floor < 0.0 || rules.Floor > 100.0 || !IsWholeTenths(rules.Floor))
        {
            errors.Add("faintMemories.floor must be between 0.0 and 100.0, in tenths.");
        }

        if (rules.Ceiling <= rules.Floor || rules.Ceiling > MasteryEngine.ThresholdFixedPoint / 10.0 || !IsWholeTenths(rules.Ceiling))
        {
            errors.Add($"faintMemories.ceiling must be above the floor and no higher than {MasteryEngine.ThresholdText}, where Mastery begins.");
        }
    }

    // ---- the saved state ("1|<granted UTC ticks>|<tenths remaining>")

    public static string Serialize(FaintMemoriesState state) =>
        string.Create(
            CultureInfo.InvariantCulture,
            $"{TagVersion}|{state.GrantedUtc.Ticks}|{state.RemainingTenths}"
        );

    public static bool TryParse(string? tag, out FaintMemoriesState state)
    {
        state = default;
        if (string.IsNullOrEmpty(tag) || tag.Length > 64)
        {
            return false;
        }

        var parts = tag.Split('|');
        if (parts.Length != 3 ||
            !int.TryParse(parts[0], NumberStyles.None, CultureInfo.InvariantCulture, out var version) || version != TagVersion ||
            !long.TryParse(parts[1], NumberStyles.None, CultureInfo.InvariantCulture, out var ticks) ||
            ticks < DateTime.MinValue.Ticks || ticks > DateTime.MaxValue.Ticks ||
            !int.TryParse(parts[2], NumberStyles.None, CultureInfo.InvariantCulture, out var remaining) || remaining > 10000)
        {
            return false;
        }

        state = new FaintMemoriesState(new DateTime(ticks, DateTimeKind.Utc), remaining);
        return true;
    }

    // ---- the unlock clock

    public static DateTime UnlockAtUtc(FaintMemoriesState state, FaintMemoriesRules rules) =>
        state.GrantedUtc + TimeSpan.FromHours(rules.UnlockHours);

    public static bool IsUnlocked(FaintMemoriesState state, DateTime nowUtc, FaintMemoriesRules rules) =>
        nowUtc >= UnlockAtUtc(state, rules);

    public static TimeSpan UnlockIn(FaintMemoriesState state, DateTime nowUtc, FaintMemoriesRules rules)
    {
        var left = UnlockAtUtc(state, rules) - nowUtc;
        return left < TimeSpan.Zero ? TimeSpan.Zero : left;
    }

    /// <summary>How far through the wait it is, from 0 to 1.</summary>
    public static double UnlockFraction(FaintMemoriesState state, DateTime nowUtc, FaintMemoriesRules rules)
    {
        var total = TimeSpan.FromHours(rules.UnlockHours);
        if (total <= TimeSpan.Zero)
        {
            return 1.0;
        }

        return Math.Clamp((nowUtc - state.GrantedUtc).TotalSeconds / total.TotalSeconds, 0.0, 1.0);
    }

    /// <summary>"9 hours 14 minutes", "40 minutes", "under a minute": how long is left, as a player reads it. Rounded up to the minute.</summary>
    public static string DescribeUnlockIn(TimeSpan left)
    {
        var minutes = (int)Math.Ceiling(left.TotalMinutes);
        if (minutes <= 1)
        {
            return "under a minute";
        }

        var hours = minutes / 60;
        var rest = minutes % 60;
        string Unit(int n, string word) => n == 1 ? $"1 {word}" : $"{n} {word}s";

        return hours == 0
            ? Unit(rest, "minute")
            : rest == 0
                ? Unit(hours, "hour")
                : $"{Unit(hours, "hour")} {Unit(rest, "minute")}";
    }

    // ---- using it

    /// <summary>
    /// How many tenths one skill use brings back, or 0 when it does not apply. A step, but never more than is left, never past the
    /// ceiling (where Mastery takes over) or the skill's own cap, never below the floor (stock already gains faster there), and
    /// never past the total skill cap: free points cannot make room by taking from another skill.
    /// </summary>
    public static int PlanRestore(
        int remainingTenths,
        int skillTenths,
        int individualCapTenths,
        FaintMemoriesRules rules,
        int totalTenths,
        int totalCapTenths,
        int stepTenths
    )
    {
        var ceiling = Math.Min(CeilingTenths(rules), individualCapTenths);
        if (remainingTenths <= 0 || stepTenths < 1 || skillTenths < FloorTenths(rules) || skillTenths >= ceiling)
        {
            return 0;
        }

        var amount = Math.Min(Math.Min(stepTenths, remainingTenths), ceiling - skillTenths);
        return Math.Max(0, Math.Min(amount, totalCapTenths - totalTenths));
    }

    /// <summary>The window's view of a character's pool, or null when there is none to show (never granted, or used up).</summary>
    public static FaintMemoriesView? BuildView(FaintMemoriesState? state, DateTime nowUtc, FaintMemoriesRules rules)
    {
        if (state is not { RemainingTenths: > 0 } s)
        {
            return null;
        }

        return new FaintMemoriesView(
            IsUnlocked(s, nowUtc, rules) ? FaintMemoriesPhase.Ready : FaintMemoriesPhase.Locked,
            s.RemainingTenths,
            PointsTenths(rules),
            UnlockFraction(s, nowUtc, rules),
            UnlockIn(s, nowUtc, rules)
        );
    }

    // ---- what a player reads

    public static string UnlockedMessage(int remainingTenths, int stepTenths) =>
        $"{Name}: {GumpStyle.Points(remainingTenths)} points are ready. Train a skill you have set to Up and they come back to you, " +
        $"{GumpStyle.Points(stepTenths)} at a time. [SkillBank shows what is left.";

    public static string UsedUpMessage(string skillName) =>
        $"{Name}: the last of them has come back to you, into {skillName}. There is nothing left to remember.";
}

/// <summary>
/// Faint Memories in the game: grants the pool to every new character, brings points back through
/// <see cref="SkillBankService.TryRestore"/>, and tells the player when it is ready. State lives in one account tag per
/// character (like Mastery and Intent), so no ModernUO save format changes. The window is <see cref="SkillBankGump"/>.
/// </summary>
public static class FaintMemoriesService
{
    private const string TagPrefix = "BritanniaRenaissance.FaintMemories.v1.";

    private static readonly Dictionary<Serial, Server.Timer> Notices = [];
    private static bool _configured;

    public static bool Enabled =>
        ShardRulesConfiguration.Settings?.FeatureFlags.FaintMemories == true && SkillBankService.Enabled;

    private static FaintMemoriesRules Rules => ShardRulesConfiguration.Settings?.FaintMemories ?? new FaintMemoriesRules();

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CharacterCreation.CharacterCreatedHandler += Grant;
        EventSink.Connected += OnConnected;
    }

    private static string TagFor(PlayerMobile player) =>
        TagPrefix + player.Serial.Value.ToString("X8", CultureInfo.InvariantCulture);

    public static bool TryLoad(PlayerMobile player, out FaintMemoriesState state)
    {
        state = default;
        return player.Account is Account account && FaintMemoriesPolicy.TryParse(account.GetTag(TagFor(player)), out state);
    }

    private static void Save(PlayerMobile player, FaintMemoriesState state)
    {
        if (player.Account is Account account)
        {
            account.SetTag(TagFor(player), FaintMemoriesPolicy.Serialize(state));
        }
    }

    /// <summary>What the Skill Bank window shows for this character, or null while the feature is off and once the points are used up.</summary>
    public static FaintMemoriesView? GetView(PlayerMobile player)
    {
        if (!Enabled)
        {
            return null;
        }

        return FaintMemoriesPolicy.BuildView(TryLoad(player, out var state) ? state : null, Core.Now, Rules);
    }

    // ---- granting

    private static void Grant(CharacterCreatedEventArgs args)
    {
        if (args.Mobile is PlayerMobile { AccessLevel: AccessLevel.Player } player)
        {
            TryGrant(player, out _);
        }
    }

    /// <summary>Gives the character the standard pool, once. Never again after it has been used up.</summary>
    public static bool TryGrant(PlayerMobile player, out string message)
    {
        if (!Enabled)
        {
            message = $"{FaintMemoriesPolicy.Name} is not enabled.";
            return false;
        }

        if (player.Account is not Account)
        {
            message = "That character has no account to keep it on.";
            return false;
        }

        if (TryLoad(player, out var existing))
        {
            message = $"That character already has {FaintMemoriesPolicy.Name} ({GumpStyle.Points(existing.RemainingTenths)} left); it is never granted twice.";
            return false;
        }

        var points = FaintMemoriesPolicy.PointsTenths(Rules);
        Save(player, new FaintMemoriesState(Core.Now, points));
        ShardAuditLog.Record("faintmemories", "granted", player, null, $"tenths={points}");
        message = $"Granted {GumpStyle.Points(points)} points of {FaintMemoriesPolicy.Name}.";
        return true;
    }

    // ---- using

    /// <summary>
    /// Called from <see cref="SkillBankService.TryRestore"/> for a skill with no banked points of its own. Restored means the stock
    /// gain is replaced; NotApplicable leaves the gain (and Mastery) to carry on as usual.
    /// </summary>
    public static SkillBankRestoreOutcome TryRestore(PlayerMobile player, Skill skill)
    {
        if (!Enabled || !TryLoad(player, out var state) || state.RemainingTenths <= 0)
        {
            return SkillBankRestoreOutcome.NotApplicable;
        }

        var rules = Rules;
        if (skill.Lock != SkillLock.Up || !FaintMemoriesPolicy.IsUnlocked(state, Core.Now, rules))
        {
            return SkillBankRestoreOutcome.NotApplicable;
        }

        var individualCap = Math.Min(skill.CapFixedPoint, ShardRulesConfiguration.Settings?.Character.IndividualSkillCap * 10 ?? 1000);
        var amount = FaintMemoriesPolicy.PlanRestore(
            state.RemainingTenths,
            skill.BaseFixedPoint,
            individualCap,
            rules,
            player.Skills.Total,
            player.Skills.Cap,
            SkillBankService.RestoreStepTenths
        );

        if (amount <= 0)
        {
            return SkillBankRestoreOutcome.NotApplicable;
        }

        skill.BaseFixedPoint += amount;
        state = state with { RemainingTenths = state.RemainingTenths - amount };
        Save(player, state);

        if (state.RemainingTenths == 0)
        {
            ShardAuditLog.Record("faintmemories", "used-up", player, null, $"lastSkill={skill.Info.Name}");
            player.SendMessage(FaintMemoriesPolicy.UsedUpMessage(skill.Info.Name));
        }

        return SkillBankRestoreOutcome.Restored;
    }

    // ---- telling the player

    private static void OnConnected(Mobile mobile)
    {
        if (mobile is not PlayerMobile { AccessLevel: AccessLevel.Player } player)
        {
            return;
        }

        CancelNotice(player.Serial);

        if (!Enabled || !TryLoad(player, out var state) || state.RemainingTenths <= 0)
        {
            return;
        }

        var left = FaintMemoriesPolicy.UnlockIn(state, Core.Now, Rules);

        // The client is not ready for messages while the connection event runs; a locked pool speaks up when it unlocks.
        Notices[player.Serial] = Server.Timer.DelayCall(
            left + TimeSpan.FromSeconds(left == TimeSpan.Zero ? 3 : 1),
            static p => Announce(p),
            player
        );
    }

    private static void Announce(PlayerMobile player)
    {
        Notices.Remove(player.Serial);

        if (player.Deleted || player.NetState?.Running != true || !Enabled || !TryLoad(player, out var state) ||
            state.RemainingTenths <= 0 || !FaintMemoriesPolicy.IsUnlocked(state, Core.Now, Rules))
        {
            return;
        }

        player.SendMessage(FaintMemoriesPolicy.UnlockedMessage(state.RemainingTenths, SkillBankService.RestoreStepTenths));
    }

    private static void CancelNotice(Serial serial)
    {
        if (Notices.Remove(serial, out var timer))
        {
            timer.Stop();
        }
    }

    // ---- staff

    public static IEnumerable<string> DescribeForStaff(PlayerMobile player)
    {
        if (!Enabled)
        {
            yield return $"{FaintMemoriesPolicy.Name}: not enabled.";
            yield break;
        }

        if (!TryLoad(player, out var state))
        {
            yield return $"{FaintMemoriesPolicy.Name}: none (this character was created before it was enabled, or was never granted it).";
            yield break;
        }

        var rules = Rules;
        var unlockAt = FaintMemoriesPolicy.UnlockAtUtc(state, rules);
        var phase = FaintMemoriesPolicy.IsUnlocked(state, Core.Now, rules)
            ? "ready"
            : $"locked for {FaintMemoriesPolicy.DescribeUnlockIn(FaintMemoriesPolicy.UnlockIn(state, Core.Now, rules))}";
        yield return $"{FaintMemoriesPolicy.Name}: {GumpStyle.Points(state.RemainingTenths)} of {GumpStyle.Points(FaintMemoriesPolicy.PointsTenths(rules))} left, {phase}; " +
                     $"granted {state.GrantedUtc:u}, unlocks {unlockAt:u}.";
    }
}
