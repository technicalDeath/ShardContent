using System.Text.Json.Serialization;
using Server;
using Server.Misc;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Stamina relief (docs/Stamina-Relief-Evidence.md), behind <c>featureFlags.staminaRelief</c>. The owner's rulings (2026-10-16): "The stamina lost at
/// low health when taking hits seems like the most obvious problem. Let's tune that down so that you lose at most 3 stamina per hit", and
/// "Also fix the message". Stock pre-AOS fatigue takes damage x stamina / hit points - 5 per hit (<see cref="StaminaSystem.FatigueOnDamage"/>), so a
/// hurt character loses most of what is left in two or three hits, just when it needs to run; here a player loses at most
/// <c>staminaRelief.maxLossPerHit</c>. And at 0 stamina a run attempt said "You are too fatigued to move." though walking still works. ClassicUO never
/// sends that run: it switches to walking by itself at 1 stamina (PlayerMobile.cs, <c>Stamina &lt;= 1</c>) and says nothing, so the line is also sent
/// when a running step leaves a player at <see cref="WalkThreshold"/> or less, the step after which the client walks.
/// Every player, not only new ones (the owner: no new-player-only fixes); creatures keep the stock drain.
/// </summary>
public static class StaminaReliefService
{
    public const string TooTiredToRunText = "You are too tired to run, but you can still walk. Your stamina comes back as you go.";

    /// <summary>A blocked run is retried on every step the client takes, so the line is said at most this often.</summary>
    public static readonly TimeSpan NoticeInterval = TimeSpan.FromSeconds(5);

    /// <summary>The stamina at which ClassicUO stops running: it walks at 1 or less.</summary>
    public const int WalkThreshold = 1;

    private static bool _configured;
    private static readonly Dictionary<Mobile, DateTime> LastNotice = [];

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.StaminaRelief == true;

    public static StaminaReliefRules Rules => ShardRulesConfiguration.Settings?.StaminaRelief ?? new StaminaReliefRules();

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        StaminaSystem.DamageFatigueFilter = Filter;
        StaminaSystem.TooTiredToRunNotice = Notice;
        EventSink.Logout += m => LastNotice.Remove(m);
        EventSink.Movement += OnMovement;
    }

    /// <summary>Whether a running step should say the line: it leaves the player at the client's walking point or below.</summary>
    public static bool RunningOutOfBreath(bool enabled, bool isPlayer, bool running, int staminaBefore) =>
        enabled && isPlayer && running && staminaBefore - 1 <= WalkThreshold;

    // The handler runs before the stamina system takes the step's cost, so "before" is the stamina the step started with; a running step at
    // the lowest tenth costs at least one more point.
    private static void OnMovement(MovementEventArgs e)
    {
        if (e.Mobile is PlayerMobile { Alive: true, AccessLevel: AccessLevel.Player } player &&
            RunningOutOfBreath(Enabled, true, (e.Direction & Direction.Running) != 0, player.Stam))
        {
            Notice(player);
        }
    }

    /// <summary>The rule, free of the game: the stock loss, capped for a player while the relief is on.</summary>
    public static int LossPerHit(bool enabled, bool isPlayer, int stockLoss, int maxLossPerHit) =>
        enabled && isPlayer ? Math.Min(stockLoss, maxLossPerHit) : stockLoss;

    /// <summary>Whether the line is due: the first time, or once the interval has passed since the last one.</summary>
    public static bool NoticeDue(DateTime? last, DateTime now, TimeSpan interval) => last is null || now - last.Value >= interval;

    private static int Filter(Mobile m, int stockLoss) => LossPerHit(Enabled, m.Player, stockLoss, Rules.MaxLossPerHit);

    private static bool Notice(Mobile m)
    {
        if (!Enabled)
        {
            return false;
        }

        var now = Core.Now;

        if (NoticeDue(LastNotice.TryGetValue(m, out var last) ? last : null, now, NoticeInterval))
        {
            LastNotice[m] = now;
            m.SendMessage(TooTiredToRunText);
        }

        return true;
    }

    public static void Validate(StaminaReliefRules rules, List<string> errors)
    {
        if (rules.MaxLossPerHit is < 0 or > 30)
        {
            errors.Add("staminaRelief.maxLossPerHit must be between 0 and 30.");
        }
    }
}

public sealed class StaminaReliefRules
{
    /// <summary>The most stamina one hit can take from a player (stock has no limit).</summary>
    [JsonPropertyName("maxLossPerHit")]
    public int MaxLossPerHit { get; set; } = 3;
}
