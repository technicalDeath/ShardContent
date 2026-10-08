using System.Globalization;
using Server;
using Server.Engines.BuffIcons;
using Server.Mobiles;
using Server.Network;
using Server.Spells.Fourth;
using Server.Spells.Second;
using Server.Spells.Seventh;

namespace BritanniaRenaissance.Content;

/// <summary>What one state says about a player right now: the named values its text may use, and when it ends, if it knows.</summary>
public sealed record BuffStateReading(IReadOnlyDictionary<string, string> Values, DateTime? UntilUtc = null);

/// <summary>
/// The buff bar. Turned on by the stock server setting <c>buffIcons.enable</c>; this class makes it say what this shard's rules say.
/// Stock icons pass through <see cref="BuffInfo.Override"/> and get their text from the table (<see cref="BuffIconRules"/>); effects
/// stock shows no icon for in UOR, and the shard's own states, are added and removed by a once-a-second watch that reads the same
/// public state the rules themselves use, so no spell or service needs to know about icons.
/// </summary>
public static class BuffIconService
{
    private static readonly Dictionary<Serial, Dictionary<BuffIcon, BuffShown>> Shown = [];
    private static readonly List<NetState> Online = [];
    private static bool _configured;
    private static int _ticks;

    /// <summary>
    /// The buff packet keeps the time left in a signed 16-bit number of seconds, so a longer wait would show the wrong time. A state
    /// that ends later than this shows no countdown until it is within reach, and says how long is left in its text instead.
    /// </summary>
    public static readonly TimeSpan MaxCountdown = TimeSpan.FromSeconds(short.MaxValue - 600);

    public static BuffIconRules Rules { get; private set; } = null!;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        Rules = BuffIconRulesLoader.Load();

        var previous = BuffInfo.Override;
        BuffInfo.Override = previous is null ? Present : (m, b) => previous(m, b) is { } kept ? Present(m, kept) : null;

        Server.Timer.StartTimer(TimeSpan.FromSeconds(1.0), TimeSpan.FromSeconds(1.0), Poll);
    }

    // ---- stock icons

    public static BuffInfo? Present(PlayerMobile m, BuffInfo b) => Present(Rules, b, name => StockValue(m, name));

    /// <summary>
    /// A stock icon is shown with the table's text, or not at all when the table does not list it. A buff already in the shard's
    /// own form (the generic title) is one the watch added, and goes through as it is.
    /// </summary>
    public static BuffInfo? Present(BuffIconRules rules, BuffInfo b, Func<string, string?> value)
    {
        if (b.TitleCliloc == BuffIconCatalog.GenericTitleCliloc)
        {
            return b;
        }

        if (rules.Stock.TryGetValue(b.ID.ToString(), out var text))
        {
            return new BuffInfo(
                b.ID,
                BuffIconCatalog.GenericTitleCliloc,
                0,
                b.Duration,
                BuffIconRulesLoader.Render(text, value),
                b.RetainThroughDeath
            );
        }

        return rules.UnlistedStockIcons == "show" ? b : null;
    }

    /// <summary>"buff.Str" is the Strength the player's Bless-type spell added; "curse.Dex" the Dexterity a curse-type spell took away.</summary>
    public static string? StockValue(PlayerMobile m, string name)
    {
        var dot = name.IndexOf('.');

        if (dot < 0)
        {
            return null;
        }

        var curse = name.StartsWith("curse", StringComparison.Ordinal);
        var mod = m.GetStatMod($"[Magic] {name[(dot + 1)..]} {(curse ? "Curse" : "Buff")}");
        var amount = mod is null ? 0 : curse ? -mod.Offset : mod.Offset;

        return amount > 0 ? amount.ToString(CultureInfo.InvariantCulture) : null;
    }

    // ---- the watch

    private static void Poll()
    {
        if (!BuffInfo.Enabled)
        {
            return;
        }

        var now = DateTime.UtcNow;
        Online.Clear();
        Online.AddRange(NetState.Instances);

        foreach (var ns in Online)
        {
            if (ns.BuffIcon && ns.Mobile is PlayerMobile { Deleted: false } player)
            {
                Reconcile(player, now);
            }
        }

        if (++_ticks % 60 == 0)
        {
            Forget();
        }
    }

    /// <summary>What an icon shows: its text and, when the state knows its end, when that is.</summary>
    public readonly record struct BuffShown(string Text, DateTime? UntilUtc);

    /// <summary>An icon to show (or show again) with this text and end, or, when <see cref="Show"/> is null, to take away.</summary>
    public readonly record struct BuffChange(BuffIcon Icon, BuffShown? Show);

    /// <summary>
    /// What to send so the icons shown become the icons wanted: new ones and ones whose text changed or whose end moved by more than
    /// three seconds (an icon's own countdown keeps time, so a small drift is not worth a resend), and a removal for each one no
    /// longer wanted.
    /// </summary>
    public static List<BuffChange> Diff(IReadOnlyDictionary<BuffIcon, BuffShown>? shown, IReadOnlyDictionary<BuffIcon, BuffShown> wanted)
    {
        var changes = new List<BuffChange>();

        foreach (var (icon, want) in wanted)
        {
            if (shown is null || !shown.TryGetValue(icon, out var current) || current.Text != want.Text || !SameEnd(current.UntilUtc, want.UntilUtc))
            {
                changes.Add(new BuffChange(icon, want));
            }
        }

        if (shown is not null)
        {
            foreach (var icon in shown.Keys)
            {
                if (!wanted.ContainsKey(icon))
                {
                    changes.Add(new BuffChange(icon, null));
                }
            }
        }

        return changes;
    }

    private static bool SameEnd(DateTime? shown, DateTime? now) =>
        shown is null || now is null ? shown is null && now is null : Math.Abs((shown.Value - now.Value).TotalSeconds) <= 3;

    /// <summary>Makes the player's icons match their states.</summary>
    public static void Reconcile(PlayerMobile player, DateTime now)
    {
        var wanted = new Dictionary<BuffIcon, BuffShown>();

        foreach (var (state, entry) in Rules.States)
        {
            if (!BuffIconRulesLoader.TryResolveIcon(Rules, entry.Icon, out var icon) || wanted.ContainsKey(icon))
            {
                continue;
            }

            if (BuffStateProbes.Read(state, player, now) is { } reading)
            {
                var until = entry.Countdown && reading.UntilUtc is { } end && end > now.AddSeconds(1) && end - now <= MaxCountdown ? end : (DateTime?)null;
                wanted[icon] = new BuffShown(BuffIconRulesLoader.Render(entry, name => reading.Values.GetValueOrDefault(name)), until);
            }
        }

        Shown.TryGetValue(player.Serial, out var shown);

        if (wanted.Count == 0 && shown is null)
        {
            return;
        }

        foreach (var (icon, show) in Diff(shown, wanted))
        {
            shown ??= Shown[player.Serial] = [];

            if (show is not { } to)
            {
                shown.Remove(icon);
                player.RemoveBuff(icon);
                continue;
            }

            shown[icon] = to;

            // Kept through death: the engine strips every other buff then, and the watch is what removes these.
            player.AddBuff(
                new BuffInfo(
                    icon,
                    BuffIconCatalog.GenericTitleCliloc,
                    0,
                    to.UntilUtc is { } until2 ? until2 - now : default,
                    to.Text,
                    retainThroughDeath: true
                )
            );
        }

        if (shown is { Count: 0 })
        {
            Shown.Remove(player.Serial);
        }
    }

    /// <summary>Drops the records of characters that no longer exist.</summary>
    private static void Forget()
    {
        foreach (var serial in Shown.Keys.Where(static serial => World.FindMobile(serial) is not { Deleted: false }).ToArray())
        {
            Shown.Remove(serial);
        }
    }

    /// <summary>Staff diagnostics: the switch, the table, and what the watch is showing this viewer.</summary>
    public static IEnumerable<string> DescribeStatus(Mobile viewer)
    {
        yield return $"Buff icons (server setting buffIcons.enable): {BuffInfo.Enabled}.";
        yield return $"Table: {Rules.Stock.Count} stock icons rewritten, {Rules.States.Count} states, {Rules.CustomIcons.Count} custom icons; unlisted stock icons are {Rules.UnlistedStockIcons}.";

        if (viewer is PlayerMobile player)
        {
            foreach (var line in Describe(player))
            {
                yield return line;
            }
        }
    }

    /// <summary>The shard-added icons this player has right now.</summary>
    public static IEnumerable<string> Describe(PlayerMobile player)
    {

        if (!Shown.TryGetValue(player.Serial, out var shown) || shown.Count == 0)
        {
            yield return "The shard is showing no state icons for this player.";
            yield break;
        }

        foreach (var (icon, buff) in shown)
        {
            yield return $"{icon}: {buff.Text.Replace("<br>", " / ")}";
        }
    }
}

/// <summary>
/// What each state in the table is, in terms of the game. Every probe reads state the rules already keep (a spell's registry, a
/// service's own record), so adding an icon never means touching the spell or the service.
/// </summary>
public static class BuffStateProbes
{
    private static readonly Dictionary<Serial, (BackpackWard? Ward, DateTime NextScanUtc)> WardScans = [];

    private static readonly IReadOnlyDictionary<string, string> None = new Dictionary<string, string>();

    public static BuffStateReading? Read(string state, PlayerMobile player, DateTime now) => state switch
    {
        "protection" => Protection(player),
        "archProtection" => ArchProtection(player),
        "reactiveArmor" => Points(player.MeleeDamageAbsorb),
        "magicReflect" => Points(player.MagicDamageAbsorb),
        "poison" => player.Poison is { } poison ? new BuffStateReading(Values(("level", poison.Name))) : null,
        "polymorph" => PolymorphSpell.UnderEffect(player)
            ? new BuffStateReading(None, PolymorphSpell.TryGetEnd(player, out var ends) ? ends : null)
            : null,
        "knockedOut" => KnockedOutService.IsKnockedOut(player) ? new BuffStateReading(None, KnockedOutService.GetUntilUtc(player)) : null,
        "criminal" => player.Criminal ? new BuffStateReading(None) : null,
        "intent" => PvpIntentService.SafeWorldEnabled && PvpIntentService.IsIntentEnabled(player) ? new BuffStateReading(None) : null,
        "wardPrimed" => Ward(player, now, WardPhase.Primed),
        "wardActivated" => Ward(player, now, WardPhase.Activated),
        "faintMemoriesLocked" => FaintMemories(player, FaintMemoriesPhase.Locked, now),
        "faintMemoriesReady" => FaintMemories(player, FaintMemoriesPhase.Ready, now),
        _ => null
    };

    private static Dictionary<string, string> Values(params (string Name, string Value)[] values) =>
        values.ToDictionary(static v => v.Name, static v => v.Value);

    private static BuffStateReading? Points(int points) =>
        points > 0 ? new BuffStateReading(Values(("points", points.ToString(CultureInfo.InvariantCulture)))) : null;

    /// <summary>
    /// UOR Protection is a self spell that keeps a hit from interrupting a cast (chance in tenths of a percent in the registry) for twice
    /// the caster's Magery in seconds, 15 to 240. The spell notes its end for the countdown.
    /// </summary>
    private static BuffStateReading? Protection(PlayerMobile player)
    {
        if (!ProtectionSpell.Registry.TryGetValue(player, out var tenths))
        {
            return null;
        }

        return new BuffStateReading(
            Values(("chance", (tenths / 10).ToString(CultureInfo.InvariantCulture))),
            ProtectionSpell.TryGetEnd(player, out var ends) ? ends : null
        );
    }

    /// <summary>UOR Arch Protection raises armor for a time set by its caster's Magery, who need not be the player; the spell notes both.</summary>
    private static BuffStateReading? ArchProtection(PlayerMobile player) =>
        ArchProtectionSpell.TryGetEffect(player, out var bonus, out var ends)
            ? new BuffStateReading(Values(("bonus", bonus.ToString(CultureInfo.InvariantCulture))), ends)
            : null;

    private static BackpackWard? ScanWard(PlayerMobile player, DateTime now)
    {
        if (WardScans.TryGetValue(player.Serial, out var scan) && now < scan.NextScanUtc && scan.Ward is not { Deleted: true })
        {
            return scan.Ward;
        }

        // Looking through a backpack for a Ward is the one probe that costs anything, so it is done every few seconds.
        var ward = BackpackWardService.FindWard(player);
        WardScans[player.Serial] = (ward, now.AddSeconds(5));

        return ward;
    }

    private static BuffStateReading? Ward(PlayerMobile player, DateTime now, WardPhase phase)
    {
        if (ScanWard(player, now)?.State is not { IsTracking: true } state || state.Phase != phase || state.ProtectedSerial != player.Serial.Value)
        {
            return null;
        }

        return new BuffStateReading(
            Values(
                ("minutes", Math.Max(1, (int)Math.Ceiling(state.Remaining(now).TotalMinutes)).ToString(CultureInfo.InvariantCulture)),
                ("caught", state.Caught.Count.ToString(CultureInfo.InvariantCulture))
            ),
            state.DeadlineUtc
        );
    }

    private static BuffStateReading? FaintMemories(PlayerMobile player, FaintMemoriesPhase phase, DateTime now)
    {
        if (FaintMemoriesService.GetView(player) is not { } view || view.Phase != phase)
        {
            return null;
        }

        return new BuffStateReading(
            Values(("points", GumpStyle.Points(view.RemainingTenths)), ("unlock", Span(view.UnlockIn))),
            phase == FaintMemoriesPhase.Locked ? now + view.UnlockIn : null
        );
    }

    /// <summary>A wait in words that only change when they have to: whole hours while it is long, then minutes.</summary>
    public static string Span(TimeSpan span)
    {
        if (span.TotalHours > 1.0)
        {
            var hours = (int)Math.Ceiling(span.TotalHours);

            return $"{hours} hours";
        }

        var minutes = Math.Max(1, (int)Math.Ceiling(span.TotalMinutes));

        return minutes == 1 ? "a minute" : $"{minutes} minutes";
    }
}
