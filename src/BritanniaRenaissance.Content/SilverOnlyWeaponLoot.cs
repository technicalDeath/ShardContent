using Server;
using Server.Items;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Weapons that monsters drop may carry the Silver slayer and no other (owner ruling, 2026-10-13: he does not remember monster slayers from UO:R; "keep only silver weapons", other slayer
/// types may come back later as craftable items). The stock pre-Age-of-Shadows loot gives a magic weapon a 5% Silver chance and, failing that, a 5% chance of its monster's own slayer;
/// this lets only the Silver ones through (docs/Slayer-Loot-Evidence.md). Not behind a flag: it is an era ruling, like the Mastery change. Weapons that already carry another slayer are not touched.
/// </summary>
public static class SilverOnlyWeaponLoot
{
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        LootPackEntry.WeaponLootSlayerAllowed = Allowed;
    }

    public static bool Allowed(SlayerName slayer) => slayer == SlayerName.Silver;
}
