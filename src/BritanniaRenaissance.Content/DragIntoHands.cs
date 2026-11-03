using Server;
using Server.Items;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Dragging something into full hands swaps it in (docs/Drag-Into-Hands-Evidence.md), behind <c>featureFlags.dragIntoHands</c>. The owner (2026-11-02):
/// "when you attempt to drag something into your hands, but your hands are full, the game should automatically unequip the item in your hands to free
/// them up". Stock refuses the drop ("You can only wield one weapon at a time.", "You already have something in both hands.") and bounces the item
/// back. Here, for a player dropping a hand item on their own paperdoll, what the stock hand rules would not allow beside it goes into the pack and the
/// new one is equipped (<see cref="WorldActions.Equip"/>, the same rule the left-click menus use). If the pack cannot take it, or the stock equip still
/// refuses (too little Strength, say), everything stays as it was and the item bounces back as stock. Armor and clothing are untouched.
/// </summary>
public static class DragIntoHands
{
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.DragIntoHands == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        IncomingItemPackets.EquipRequestHandler = OnEquipRequest;
    }

    /// <summary>Whether a drop swaps: the flag is on, a player drops onto their own paperdoll, and the item is held in the hands.</summary>
    public static bool Applies(bool enabled, bool ownPaperdoll, Layer layer) =>
        enabled && ownPaperdoll && layer is Layer.OneHanded or Layer.TwoHanded;

    private static bool OnEquipRequest(Mobile from, Mobile to, Item item) =>
        Applies(Enabled, from == to && from is PlayerMobile, item.Layer) ? WorldActions.Equip((PlayerMobile)from, item) : to.EquipItem(item);
}
