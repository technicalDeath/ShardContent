using Server.Items;

namespace BritanniaRenaissance.Content;

/// <summary>
/// House-addon deeds made as ordinary goods (docs/Bot-Farm-QoL-Findings.md, last section), behind <c>featureFlags.ordinaryAddonDeeds</c>. Pre-AOS every
/// addon deed (bed, forge, loom, oven...) is made newbied, and no vendor buys a newbied item, so the Carpenter could never take one even with
/// <c>extraVendorBuyers</c>. The owner (2026-10-17) chose "Stop newbie-ing deeds": a new deed is an ordinary item, sold and lost on death like other
/// goods. Deeds already made keep their state.
/// </summary>
public static class OrdinaryAddonDeeds
{
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.OrdinaryAddonDeeds == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        var previous = BaseAddonDeed.NewbiedBeforeAos;
        BaseAddonDeed.NewbiedBeforeAos = deed => !Enabled && previous?.Invoke(deed) != false;
    }
}
