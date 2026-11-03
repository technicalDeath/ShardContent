using Server;
using Server.Engines.Craft;
using Server.Engines.Harvest;
using Server.Items;
using Server.Mobiles;
using Server.SkillHandlers;

namespace BritanniaRenaissance.Content;

/// <summary>
/// A progress bar over your own character while a timed action runs (docs/Action-Progress-Bars-Evidence.md, plan docs/Action-Progress-Bars-Plan.md),
/// behind <c>featureFlags.actionProgressBars</c>. The owner (2026-11-02): "give actions that take time a progress bar over the character ... a small
/// progress bar (big enough to fit text) above the character saying "chopping" that fills while the action completes". Every action keeps its stock
/// timing; each bar's length is that action's own, known when it starts. The shard sends extended command 0xB4 to the player, and to nobody else
/// (owner: "Only show your bars"), with the label, the length and a colour theme; the client fills the bar over that time. Every action that can be
/// cut short clears its bar where the stock code stops it (owner: "make sure all bars clear if an action is canceled"): a harvest swing that fails its
/// checks, a bandage stopped early, a craft the crafter can no longer perform, a taming attempt broken off, a camp left before it is secure, a treasure
/// dig cut short. The rest (lockpicking, cooking, spinning, milling, poisoning, begging) have no way to stop before their result; the client also drops
/// a bar when its mobile dies or leaves the world. Each action has its own bar, known by its label; bars of actions running at once stack over the head
/// (owner, 2026-11-03: "we need bars to stack when multiple are up, so they don't overlap"). A clear names its bar and takes away only that one, and
/// only while it still runs, so a camp left half made does not take away the chopping bar of a player who went on to chop.
/// </summary>
public static class ActionProgressBars
{
    public const int Command = 0xB4;
    public const int MaxLabelLength = 24;

    /// <summary>The bar's colour, by the kind of action (owner, 2026-11-02, on the mock: "Color pallete looks good"). The client holds the colours.</summary>
    public enum Theme : byte
    {
        Gathering = 1,
        Crafting = 2,
        Healing = 3,
        Harmful = 4,
        Magic = 5,
        Animals = 6,
        StealthAndLocks = 7,
        CampAndRest = 8
    }

    public const string BandagingLabel = "Bandaging";
    public const string LockpickingLabel = "Picking lock";
    public const string CookingLabel = "Cooking";
    public const string SpinningLabel = "Spinning";
    public const string MillingLabel = "Milling";
    public const string TamingLabel = "Taming";
    public const string PoisoningLabel = "Poisoning";
    public const string MakingCampLabel = "Making camp";
    public const string DiggingLabel = "Digging";
    public const string BeggingLabel = "Begging";

    // the bars each player was sent, by label, and when each ends
    private static readonly Dictionary<Mobile, Dictionary<string, DateTime>> _shown = [];

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.ActionProgressBars == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        HarvestSystem.AttemptTimed += OnAttemptTimed;
        HarvestSystem.AttemptAborted += OnAborted;
        BandageContext.Started += (context, delay) => Show(context.Healer, delay, BandagingLabel, Theme.Healing);
        Lockpick.AttemptStarted += (from, _, _) => Show(from, Lockpick.AttemptDelay, LockpickingLabel, Theme.StealthAndLocks);
        CookableFood.CookStarted += (from, _, _) => Show(from, CookableFood.CookDelay, CookingLabel, Theme.Crafting);
        SpinningWheelEvents.SpinStarted += (_, _, from) => Show(from, SpinningWheelEvents.SpinDelay, SpinningLabel, Theme.Crafting);

        // phase 2 (owner, 2026-11-02): crafting, milling, taming, poisoning
        CraftEvents.CraftStarted += (from, system, _, duration) => Show(from, duration, CraftLabel(system), Theme.Crafting);
        FlourMillEvents.GrindStarted += (from, _) => Show(from, FlourMillEvents.GrindDelay, MillingLabel, Theme.Crafting);
        AnimalTaming.AttemptTimed += (from, _, duration) => Show(from, duration, TamingLabel, Theme.Animals);
        Poisoning.PoisonStarted += (from, _) => Show(from, Poisoning.PoisonDelay, PoisoningLabel, Theme.Harmful);

        // phase 3 (owner, 2026-11-03): the long waits
        Campfire.EntryStarted += entry => Show(entry.Player, Campfire.SecureDelay, MakingCampLabel, Theme.CampAndRest);
        TreasureMap.DigStarted += (from, _) => Show(from, TreasureMap.DigDuration, DiggingLabel, Theme.Gathering);
        Begging.BegStarted += (from, _) => Show(from, Begging.BegDelay, BeggingLabel, Theme.StealthAndLocks);

        // cut short: the bar goes at once
        BandageContext.Stopped += context => Clear(context.Healer, BandagingLabel);
        CraftEvents.CraftCancelled += (from, system) => Clear(from, CraftLabel(system));
        AnimalTaming.AttemptEnded += (from, _, result) =>
        {
            if (result == TameResult.Aborted)
            {
                Clear(from, TamingLabel);
            }
        };
        Campfire.EntryEnded += entry =>
        {
            if (!entry.Secured)
            {
                Clear(entry.Player, MakingCampLabel);
            }
        };
        TreasureMap.DigStopped += (from, _) => Clear(from, DiggingLabel);
    }

    /// <summary>What the bar says while a craft is made, by the craft.</summary>
    public static string CraftLabel(CraftSystem system) => system switch
    {
        DefGlassblowing => "Glassblowing",
        DefMasonry => "Carving stone",
        _ => system.MainSkill switch
        {
            SkillName.Blacksmith => "Smithing",
            SkillName.Tailoring => "Tailoring",
            SkillName.Carpentry => "Carpentry",
            SkillName.Fletching => "Fletching",
            SkillName.Tinkering => "Tinkering",
            SkillName.Alchemy => "Grinding",
            SkillName.Inscribe => "Inscribing",
            SkillName.Cartography => "Drawing a map",
            SkillName.Cooking => "Cooking",
            _ => "Crafting"
        }
    };

    /// <summary>What the bar says for a harvest, or null for one that has no bar. Mining tells ore from sand by its definition.</summary>
    public static string? LabelFor(HarvestSystem system, HarvestDefinition? def = null) => system switch
    {
        Lumberjacking => "Chopping",
        Mining mining => def != null && def == mining.Sand ? "Digging sand" : "Mining",
        Fishing => "Fishing",
        _ => null
    };

    /// <summary>
    /// 0xBF, the length, the command, the serial, the length in milliseconds (two bytes; 0 clears the bar), the label as a length byte and ASCII, then
    /// the theme. A client that predates the theme stops reading at the label and keeps its one colour.
    /// </summary>
    public static byte[] Packet(uint serial, TimeSpan duration, string label, Theme theme = Theme.Gathering)
    {
        var text = label.Length > MaxLabelLength ? label[..MaxLabelLength] : label;
        var ms = (int)Math.Clamp(Math.Round(duration.TotalMilliseconds), 0, ushort.MaxValue);
        var packet = new byte[13 + text.Length];

        packet[0] = 0xBF;
        packet[1] = (byte)(packet.Length >> 8);
        packet[2] = (byte)packet.Length;
        packet[3] = Command >> 8;
        packet[4] = Command & 0xFF;
        packet[5] = (byte)(serial >> 24);
        packet[6] = (byte)(serial >> 16);
        packet[7] = (byte)(serial >> 8);
        packet[8] = (byte)serial;
        packet[9] = (byte)(ms >> 8);
        packet[10] = (byte)ms;
        packet[11] = (byte)text.Length;

        for (var i = 0; i < text.Length; i++)
        {
            packet[12 + i] = text[i] is >= ' ' and <= '~' ? (byte)text[i] : (byte)'?';
        }

        packet[^1] = (byte)theme;
        return packet;
    }

    /// <summary>Whether a clear for <paramref name="label" /> has a bar to take away: that action's bar is up and still runs.</summary>
    public static bool Clears(IReadOnlyDictionary<string, DateTime>? shown, string label, DateTime now) =>
        shown != null && shown.TryGetValue(label, out var ends) && now < ends;

    /// <summary>Clears the player's bar for <paramref name="label" /> if it still runs (a length of 0 with the label takes away that bar only).</summary>
    public static void Clear(Mobile from, string label)
    {
        if (Clears(_shown.GetValueOrDefault(from), label, Core.Now))
        {
            Show(from, TimeSpan.Zero, label, Theme.Gathering);
        }
    }

    private static void Show(Mobile from, TimeSpan duration, string label, Theme theme)
    {
        if (Enabled && from is PlayerMobile { NetState: { } state })
        {
            Remember(from, label, duration > TimeSpan.Zero ? Core.Now + duration : null);
            state.Send(Packet(from.Serial.Value, duration, label, theme));
        }
    }

    // keeps the player's running bars, dropping those that have run out
    private static void Remember(Mobile from, string label, DateTime? ends)
    {
        if (!_shown.TryGetValue(from, out var bars))
        {
            if (ends == null)
            {
                return;
            }

            _shown[from] = bars = [];
        }

        var now = Core.Now;

        foreach (var (name, end) in bars)
        {
            if (end <= now)
            {
                bars.Remove(name);
            }
        }

        if (ends is { } until)
        {
            bars[label] = until;
        }
        else
        {
            bars.Remove(label);
        }

        if (bars.Count == 0)
        {
            _shown.Remove(from);
        }
    }

    private static void OnAttemptTimed(HarvestSystem system, Mobile from, HarvestDefinition def, TimeSpan duration)
    {
        if (LabelFor(system, def) is { } label)
        {
            Show(from, duration, label, Theme.Gathering);
        }
    }

    // a harvest cut short at a swing (the last one included) clears its bar; mining's bar says Mining or Digging sand
    private static void OnAborted(HarvestSystem system, Mobile from)
    {
        if (LabelFor(system) is { } label)
        {
            Clear(from, label);

            if (system is Mining mining && LabelFor(mining, mining.Sand) is { } sand)
            {
                Clear(from, sand);
            }
        }
    }
}
