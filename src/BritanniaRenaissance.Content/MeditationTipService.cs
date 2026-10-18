using Server;
using Server.Mobiles;
using Server.Spells;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The Meditation pointer (docs/Fast-Healing-Evidence.md), behind <c>featureFlags.meditationTip</c>. The owner (2026-10-17), on new casters who never
/// find Meditation: point them to it. When a cast is refused for want of mana and the caster is not meditating, one line says what Meditation does
/// and where the button is, at most once every ten minutes for a character. Nothing changes how mana works.
/// </summary>
public static class MeditationTipService
{
    public const string Text =
        "Out of mana? Press Meditate on the spell bar (or use Meditation from your skills) with your hands free and keep still: your mana comes back twice as fast, and the Meditation skill rises as it does.";

    public const long CooldownMilliseconds = 10 * 60 * 1000;

    private static readonly Dictionary<Serial, long> LastTip = [];
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.MeditationTip == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        Spell.InsufficientMana += OnInsufficientMana;
        EventSink.Disconnected += m => LastTip.Remove(m.Serial);
    }

    /// <summary>A tip is due when none was given yet or the last one is at least the cooldown old (tick counts compared by subtraction).</summary>
    public static bool Due(long? lastTick, long now, long cooldown) => lastTick is not { } last || now - last >= cooldown;

    private static void OnInsufficientMana(Spell spell)
    {
        if (!Enabled || spell.Caster is not PlayerMobile pm || pm.AccessLevel != AccessLevel.Player || pm.Meditating)
        {
            return;
        }

        var now = Core.TickCount;

        if (!Due(LastTip.TryGetValue(pm.Serial, out var last) ? last : null, now, CooldownMilliseconds))
        {
            return;
        }

        LastTip[pm.Serial] = now;
        pm.SendMessage(Text);
    }
}
