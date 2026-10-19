using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// One more minute for a corpse about to vanish (owner, 2026-10-18: "I just found a corpse, went to loot it and it disappeared. Let's extend corpse loot by 1
/// minute if a player opens it, when it has less than 2 minutes left, but only 1 extension is allowed"), behind <c>featureFlags.corpseLootExtension</c>.
/// When a player opens a corpse whose next decay step deletes it with what is in it (bones, or a corpse that never turns to bones) and less than
/// <see cref="Threshold"/> is left, the step moves <see cref="Extension"/> later, once in the corpse's life. Turning to bones loses nothing, so that step
/// is never extended.
/// </summary>
public static class CorpseLootExtension
{
    public static readonly TimeSpan Threshold = TimeSpan.FromMinutes(2);
    public static readonly TimeSpan Extension = TimeSpan.FromMinutes(1);

    private static readonly HashSet<Serial> Extended = [];
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.CorpseLootExtension == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        Corpse.Opened += OnOpened;
    }

    /// <summary>The time the step should get instead, or null to leave it: only a step that deletes, below the threshold, never twice.</summary>
    public static TimeSpan? Extend(bool decaysAway, TimeSpan left, bool alreadyExtended) =>
        decaysAway && !alreadyExtended && left > TimeSpan.Zero && left < Threshold ? left + Extension : null;

    private static void OnOpened(Mobile from, Corpse corpse)
    {
        if (!Enabled || from is not PlayerMobile { AccessLevel: AccessLevel.Player })
        {
            return;
        }

        if (Extend(corpse.DecaysAway, corpse.DecayLeft, Extended.Contains(corpse.Serial)) is { } longer)
        {
            Extended.Add(corpse.Serial);
            corpse.BeginDecay(longer);
        }

        // a corpse that is gone frees its place in the set
        if (Extended.Count > 512)
        {
            Extended.RemoveWhere(serial => World.FindItem(serial) is not { Deleted: false });
        }
    }
}
