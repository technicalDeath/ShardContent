using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Owner ruling (2026-09-28): an item the owner would keep on death keeps that protection when it
/// sits inside a bag. Stock death routing only asks top-level backpack items, so a regular bag
/// carries its newbied or blessed contents to the corpse. After the corpse is built, this pulls
/// every such item (the owner's own stock rule decides; a murderer still loses newbied items)
/// back into the backpack. A kept container returns whole with its contents.
/// </summary>
public static class KeptItemDeathRouting
{
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        PlayerMobile.PlayerDeathHandler += ReturnKeptContents;
    }

    private static void ReturnKeptContents(PlayerMobile player)
    {
        if (player.Backpack is not { Deleted: false } backpack || player.Corpse is not Corpse { Deleted: false } corpse)
        {
            return;
        }

        var kept = new List<Item>();
        foreach (var item in corpse.Items)
        {
            if (item is Container container)
            {
                CollectKept(player, container, kept);
            }
        }

        foreach (var item in kept)
        {
            backpack.DropItem(item);
        }
    }

    private static void CollectKept(PlayerMobile player, Container container, List<Item> kept)
    {
        foreach (var item in container.Items)
        {
            if (player.GetInventoryMoveResultFor(item) != DeathMoveResult.MoveToCorpse)
            {
                kept.Add(item);
            }
            else if (item is Container nested)
            {
                CollectKept(player, nested, kept);
            }
        }
    }
}
