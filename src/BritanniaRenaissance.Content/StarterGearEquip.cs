using Server;
using Server.Engines.CharacterCreation;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// A new character wears what it was given. Stock creation hands out each profession's armor, shield and weapon with
/// <c>EquipItem</c>, which quietly drops an item into the backpack when it cannot be worn, and it does so while the
/// character still has the packet's stat spread. The client's new-character screens send a spread that does not add up
/// to the 90 points stock expects, so stock falls back to 10/10/10; studded armor needs 25 to 35 Strength, so only the
/// helm and boots were worn and the rest sat in the pack. The shard sets the real starting stats afterwards
/// (<see cref="Alpha3StartingStats"/>); this observer runs after that and wears every starter armor piece, shield and
/// weapon that fits an empty slot. It never takes anything off and never touches an occupied slot.
/// </summary>
public static class StarterGearEquip
{
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CharacterCreation.CharacterCreatedHandler += Equip;
    }

    public static void Equip(CharacterCreatedEventArgs args)
    {
        if (args.Mobile is not PlayerMobile { AccessLevel: AccessLevel.Player, Backpack: not null } player)
        {
            return;
        }

        Wear(player);
    }

    /// <summary>Wears armor, then a shield, then a weapon from the backpack into free slots. Returns the number of items worn.</summary>
    public static int Wear(PlayerMobile player)
    {
        var pack = player.Backpack;
        if (pack is null)
        {
            return 0;
        }

        var worn = 0;

        // armor first (a body piece never blocks a hand), then the shield, then a weapon, so a two-handed weapon cannot take the shield's place
        foreach (var item in pack.Items.OfType<BaseArmor>().Where(a => a is not BaseShield).ToList())
        {
            worn += TryWear(player, pack, item) ? 1 : 0;
        }

        foreach (var shield in pack.Items.OfType<BaseShield>().ToList())
        {
            worn += TryWear(player, pack, shield) ? 1 : 0;
        }

        // the weapon the character is best at: an archer's bow, not the dagger or knife that came with another skill. A worn weapon gives way
        // only to one of a strictly higher skill, and comes back if the better one cannot be worn.
        int SkillOf(BaseWeapon weapon) => player.Skills[weapon.GetUsedSkill(player, false)].BaseFixedPoint;

        var current = player.FindItemOnLayer(Layer.OneHanded) as BaseWeapon ?? player.FindItemOnLayer(Layer.TwoHanded) as BaseWeapon;
        var currentSkill = current is null ? -1 : SkillOf(current);

        foreach (var weapon in pack.Items.OfType<BaseWeapon>().OrderByDescending(SkillOf).ToList())
        {
            if (SkillOf(weapon) <= currentSkill)
            {
                break;
            }

            if (current is not null)
            {
                player.RemoveItem(current);
                pack.DropItem(current);
            }

            if (TryWear(player, pack, weapon))
            {
                worn++;
                break;
            }

            if (current is not null)
            {
                pack.RemoveItem(current);
                player.EquipItem(current);
            }
        }

        return worn;
    }

    private static bool TryWear(PlayerMobile player, Container pack, Item item)
    {
        Item? displaced = null;

        if (item.Layer == Layer.Invalid)
        {
            return false;
        }

        if (player.FindItemOnLayer(item.Layer) is { } occupant)
        {
            // plain clothing gives way to armor (stock dresses a new character in pants, and leggings use the same layer); anything else stays
            if (item is not BaseArmor || occupant is not BaseClothing || occupant.LootType != LootType.Regular && occupant.LootType != LootType.Newbied)
            {
                return false;
            }

            displaced = occupant;
            pack.DropItem(occupant);
        }

        // a weapon that needs both hands needs the shield's place too
        if (item is BaseWeapon && item.Layer == Layer.TwoHanded && player.FindItemOnLayer(Layer.OneHanded) is not null)
        {
            return false;
        }

        pack.RemoveItem(item);

        if (player.EquipItem(item))
        {
            return true;
        }

        pack.DropItem(item);

        if (displaced is not null)
        {
            pack.RemoveItem(displaced);
            player.EquipItem(displaced);
        }

        return false;
    }
}
