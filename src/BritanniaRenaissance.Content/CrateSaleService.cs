using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Crafted crates sell with their key (docs/Bot-Farm-QoL-Findings.md item 28), behind <c>featureFlags.sellCratesWithKeys</c>. A carpenter with a little
/// Tinkering makes boxes and crates lockable with the key inside, and a vendor never lists a container that holds anything, so they never sold. The
/// owner (2026-10-17) chose "Sell it, key and all": a lockable container whose only contents are its own keys sells as if empty, the keys going
/// with it. Anything else inside still keeps it off the list.
/// </summary>
public static class CrateSaleService
{
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.SellCratesWithKeys == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        var previous = BaseVendor.ContainerSellsAsEmpty;
        BaseVendor.ContainerSellsAsEmpty = container => Enabled && SellsAsEmpty(container) || previous?.Invoke(container) == true;
    }

    public static bool SellsAsEmpty(Container container) =>
        container is LockableContainer lockable && OnlyItsOwnKeys(lockable.KeyValue, lockable.Items);

    /// <summary>True when the contents are one or more keys, all cut for this lock (key value 0 is a blank key and does not count).</summary>
    public static bool OnlyItsOwnKeys(uint lockValue, IReadOnlyList<Item> contents)
    {
        if (lockValue == 0 || contents.Count == 0)
        {
            return false;
        }

        foreach (var item in contents)
        {
            if (item is not Key key || key.KeyValue != lockValue)
            {
                return false;
            }
        }

        return true;
    }
}
