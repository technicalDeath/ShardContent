using Server;
using Server.Items;
using Server.Mobiles;
using Server.Spells;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Behind <c>featureFlags.scrollSuccessChance</c>: a single click on a spell scroll adds the viewer's chance of casting it to the scroll's name, such as
/// "recall (62%)". The chance is the one the cast itself rolls: the spell's own cast skill range from <c>GetCastSkills</c> (a scroll's range already starts
/// lower than a book's) against the viewer's current value of the cast skill, the same measure <c>SkillCheck</c> uses.
/// </summary>
public static class ScrollChanceService
{
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.ScrollSuccessChance == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;

        var previous = SpellScroll.SingleClickPostfixHandler;
        SpellScroll.SingleClickPostfixHandler = (scroll, from) => (Enabled ? Postfix(scroll, from) : null) ?? previous?.Invoke(scroll, from);
    }

    /// <summary>The whole percent chance, rounded down so 100 means certain: nothing below the range's start, certain at or above its end, even in between.</summary>
    public static int Percent(double skill, double min, double max)
    {
        if (skill < min)
        {
            return 0;
        }

        if (skill >= max || min >= max)
        {
            return 100;
        }

        return (int)Math.Floor((skill - min) / (max - min) * 100.0);
    }

    public static string? Postfix(SpellScroll scroll, Mobile from)
    {
        if (from is not PlayerMobile || SpellRegistry.NewSpell(scroll.SpellID, from, scroll) is not { } spell)
        {
            return null;
        }

        spell.GetCastSkills(out var min, out var max);

        return $" ({Percent(from.Skills[spell.CastSkill].Value, min, max)}% chance)";
    }
}
