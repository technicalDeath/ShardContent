using Server.Mobiles;
using Server.Spells;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Monsters say their spell's power words (owner, 2026-10-17: "Monsters speak + names on"), behind <c>featureFlags.monsterSpellWords</c>. Stock
/// ModernUO speaks the words only for player casters, so a lich or an evil mage cast in silence and the client's "Enable Overhead Spell Format"
/// switch had nothing to rename. Now any creature caster says them over its head like a player, and new client profiles show the spell's name
/// beside them ("In Por Ylem [Magic Arrow]", data/client/default-profile.json). Nothing changes how casting works.
/// </summary>
public static class MonsterSpellWords
{
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.MonsterSpellWords == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        var previous = Spell.NonPlayerSaysMantra;
        Spell.NonPlayerSaysMantra = spell => Speaks(Enabled, spell.Caster is BaseCreature) || previous?.Invoke(spell) == true;
    }

    public static bool Speaks(bool enabled, bool creatureCaster) => enabled && creatureCaster;
}
