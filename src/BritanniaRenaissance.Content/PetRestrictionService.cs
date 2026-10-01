using Server;
using Server.Mobiles;
using Server.Regions;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Beta 1 pet rules, all behind <c>featureFlags.petRestrictions</c>:
/// a tamed pet never attacks a player, and never stays inside a dungeon region, with one exception: an
/// owner may ride one mount in, dismount, and keep it there (it fights monsters, never players; see
/// <see cref="MountMayStay"/>). A ridden mount is on the Internal map, so it is never "inside".
/// The test for "tamed pet" is <see cref="IsRestrictedKind"/>.
/// </summary>
public static class PetRestrictionService
{
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.PetRestrictions == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;

        var previous = BaseCreature.CanFollowMasterHandler;
        BaseCreature.CanFollowMasterHandler = (pet, location, map) =>
            (previous?.Invoke(pet, location, map) ?? true) && CanFollow(pet, location, map);
        BaseCreature.ControlledPlacementChangedHandler += OnPlacementChanged;

        var previousTame = BaseCreature.TameAttemptRefusalHandler;
        BaseCreature.TameAttemptRefusalHandler = (tamer, creature) =>
            previousTame?.Invoke(tamer, creature) ?? TameRefusal(tamer, creature);

        var previousRefusal = BaseCreature.AttackCommandRefusalHandler;
        BaseCreature.AttackCommandRefusalHandler = (pet, target) =>
            previousRefusal?.Invoke(pet, target) ?? AttackRefusal(pet, target);

        var previousRelease = BaseCreature.ReleaseCommandRefusalHandler;
        BaseCreature.ReleaseCommandRefusalHandler = (pet, from) =>
            previousRelease?.Invoke(pet, from) ?? ReleaseRefusal(pet);
        BaseCreature.LoyaltyReleaseHandler += OnLoyaltyRelease;

        EventSink.Connected += DeliverPendingNotices;
        EventSink.ServerStarted += SweepDungeons;
    }

    private static readonly Dictionary<Serial, List<string>> PendingNotices = [];

    /// <summary>Tells the owner now, or at their next login if they are offline, so a pet is never just gone.</summary>
    public static void Notify(PlayerMobile? owner, string text)
    {
        if (owner is null)
        {
            return;
        }

        if (owner.NetState is not null)
        {
            owner.SendMessage(text);
            return;
        }

        if (!PendingNotices.TryGetValue(owner.Serial, out var list))
        {
            PendingNotices[owner.Serial] = list = [];
        }

        list.Add(text);
    }

    private static void DeliverPendingNotices(Mobile mobile)
    {
        if (mobile is PlayerMobile player && PendingNotices.Remove(player.Serial, out var list))
        {
            // A moment after login, once the client is in the world; messages sent during login can be dropped.
            Server.Timer.DelayCall(TimeSpan.FromSeconds(3), () =>
            {
                foreach (var text in list)
                {
                    player.SendMessage(text);
                }
            });
        }
    }

    /// <summary>
    /// A player may not release a restricted pet while it is inside a dungeon: a released pet turns wild and
    /// aggressive, and dungeons have no guards. Releasing outside a dungeon is stock.
    /// </summary>
    public static string? ReleaseRefusal(BaseCreature pet) =>
        Enabled && IsRestrictedPet(pet) && InDungeon(pet.Region)
            ? "You cannot release a pet inside a dungeon. Take it outside first."
            : null;

    /// <summary>
    /// A restricted pet whose loyalty ran out inside a dungeon abandons its owner, but is moved outside the
    /// dungeon first so it never turns wild in there. The owner is told (at next login if offline).
    /// </summary>
    private static void OnLoyaltyRelease(BaseCreature pet)
    {
        if (!Enabled || !IsRestrictedPet(pet) || pet.Map is null || pet.Map == Map.Internal ||
            !InDungeon(pet.Region))
        {
            return;
        }

        var owner = pet.ControlMaster as PlayerMobile;
        var name = pet.Name;
        var dungeon = pet.Region.GetRegion<DungeonRegion>()?.Name ?? "the dungeon";

        if (DungeonEntrances.TryFindOutside(pet.Map, pet.Location, out var outside))
        {
            pet.MoveToWorld(outside, pet.Map);
            Notify(owner, $"{name} has abandoned you and wandered out of {dungeon}.");
        }
        else if (owner is not null)
        {
            // No known way out of this dungeon: shrink it into the pack rather than let it turn wild inside.
            ShrinkNow(pet, owner);
            Notify(owner, $"{name} was about to abandon you in {dungeon}, so it has been shrunk into your pack.");
        }
    }

    /// <summary>
    /// The exact creature test: controlled, not spell-summoned, and not one of the exempt followers
    /// (hirelings, familiars, escortees, pack llamas and pack horses). Mounts count; a ridden mount is
    /// not in the world, so the region checks never see it.
    /// </summary>
    public static bool IsRestrictedKind(Type creatureType, bool controlled, bool summoned) =>
        controlled && !summoned &&
        !typeof(BaseHire).IsAssignableFrom(creatureType) &&
        !typeof(BaseFamiliar).IsAssignableFrom(creatureType) &&
        !typeof(BaseEscortable).IsAssignableFrom(creatureType) &&
        creatureType != typeof(PackLlama) &&
        creatureType != typeof(PackHorse);

    public static bool IsRestrictedPet(BaseCreature creature) =>
        IsRestrictedKind(creature.GetType(), creature.Controlled, creature.Summoned) &&
        creature.ControlMaster is PlayerMobile { AccessLevel: AccessLevel.Player };

    /// <summary>
    /// The one dungeon exception: a mount may stay when its owner is not riding another mount and no other
    /// mount of the owner is already standing in a dungeon. Anything that is not a mount never stays.
    /// </summary>
    public static bool MountMayStay(bool isMount, bool ownerIsMounted, bool anotherMountInDungeon) =>
        isMount && !ownerIsMounted && !anotherMountInDungeon;

    /// <summary>
    /// Whether a shrunken pet may be released where its owner stands: anywhere outside a dungeon, and inside one only
    /// for a mount that <see cref="MountMayStay"/> would let stand.
    /// </summary>
    public static bool MayReleaseInDungeon(
        bool rulesEnabled, bool ownerInDungeon, bool isMount, bool ownerIsMounted, bool anotherMountInDungeon
    ) => !rulesEnabled || !ownerInDungeon || MountMayStay(isMount, ownerIsMounted, anotherMountInDungeon);

    public static bool MayRelease(PlayerMobile owner, BaseCreature pet) =>
        MayReleaseInDungeon(
            Enabled,
            InDungeon(owner.Region),
            pet is BaseMount,
            owner.Mounted,
            AnotherMountInDungeon(owner, pet)
        );

    /// <summary>
    /// Taming inside a dungeon is allowed, but a creature that would then be shrunk needs room in the tamer's pack,
    /// so the attempt is refused up front rather than failing after the tame. A mount that may stay needs no room.
    /// </summary>
    public static string? TameRefusal(Mobile tamer, BaseCreature creature)
    {
        if (!Enabled || tamer is not PlayerMobile { AccessLevel: AccessLevel.Player } player ||
            !InDungeon(creature.Region) || !IsRestrictedKind(creature.GetType(), true, false))
        {
            return null;
        }

        if (creature is BaseMount && MountMayStay(true, player.Mounted, AnotherMountInDungeon(player, creature)))
        {
            return null;
        }

        var probe = new ShrunkenPet();
        try
        {
            if (player.Backpack is { } pack && pack.CheckHold(player, probe, false))
            {
                return null;
            }
        }
        finally
        {
            probe.Delete();
        }

        return "You need room in your backpack for a shrunken pet before you can tame that creature in a dungeon.";
    }

    /// <summary>True when a restricted pet's attack on this target must be refused.</summary>
    public static bool BlocksAttack(Mobile from, Mobile target) =>
        Enabled && target is PlayerMobile && from is BaseCreature creature && IsRestrictedPet(creature);

    /// <summary>What a pet says when its owner orders it onto a player; null when the order is fine.</summary>
    public static string? AttackRefusal(BaseCreature pet, Mobile target) =>
        BlocksAttack(pet, target) ? "Your pet refuses to attack other players." : null;

    private static bool InDungeon(Region? region) => region?.IsPartOf<DungeonRegion>() == true;

    private static bool CanFollow(BaseCreature pet, Point3D location, Map map)
    {
        if (!Enabled || !IsRestrictedPet(pet) || !InDungeon(Region.Find(location, map)))
        {
            return true;
        }

        Notify(pet.ControlMaster as PlayerMobile, $"{pet.Name} cannot follow you into a dungeon.");
        return false;
    }

    private static void OnPlacementChanged(BaseCreature pet)
    {
        if (!Enabled || pet.Deleted || pet.Map is null || pet.Map == Map.Internal || !InDungeon(pet.Region) ||
            !IsRestrictedPet(pet))
        {
            return;
        }

        // The tame/dismount/teleport that triggered this is still mid-flight; act on the next tick.
        Server.Timer.DelayCall(() => ShrinkIfInDungeon(pet));
    }

    private static void SweepDungeons()
    {
        // Independent of the flag: shrunken pets must stay protected even if the rules are switched off.
        ShrunkenPet.RestoreStabledFlags();

        if (!Enabled)
        {
            return;
        }

        foreach (var region in Region.Regions)
        {
            if (region is not DungeonRegion)
            {
                continue;
            }

            foreach (var mobile in region.GetMobiles())
            {
                if (mobile is BaseCreature pet && IsRestrictedPet(pet))
                {
                    ShrinkIfInDungeon(pet);
                }
            }
        }
    }

    public static bool ShrinkIfInDungeon(BaseCreature pet)
    {
        if (!Enabled || pet.Deleted || pet.Map is null || pet.Map == Map.Internal || !InDungeon(pet.Region) ||
            !IsRestrictedPet(pet) || pet.ControlMaster is not PlayerMobile owner)
        {
            return false;
        }

        // Decided on the next tick, so a dismount in progress has finished and the owner is no longer mounted.
        if (MountMayStay(pet is BaseMount, owner.Mounted, AnotherMountInDungeon(owner, pet)))
        {
            return false;
        }

        var name = pet.Name;
        ShrinkNow(pet, owner);
        Notify(
            owner,
            pet is BaseMount
                ? $"Only one mount may be left standing in a dungeon, so {name} has been shrunk into your pack."
                : $"{name} cannot stay in a dungeon, so it has been shrunk into your pack."
        );
        return true;
    }

    private static void ShrinkNow(BaseCreature pet, PlayerMobile owner)
    {
        var item = new ShrunkenPet();
        item.Shrink(pet, owner);

        if (owner.Backpack is not { } pack || !pack.TryDropItem(owner, item, false))
        {
            // Pack missing or full (it filled after the up-front check): at the owner's feet, never the bank.
            // Only the owner can pick it up (ShrunkenPet.VerifyMove).
            item.MoveToWorld(owner.Location, owner.Map);
        }
    }

    public static bool AnotherMountInDungeon(PlayerMobile owner, BaseCreature pet)
    {
        if (owner.AllFollowers is null)
        {
            return false;
        }

        foreach (var follower in owner.AllFollowers)
        {
            if (follower is BaseMount mount && mount != pet && !mount.Deleted && mount.Map is not null &&
                mount.Map != Map.Internal && InDungeon(mount.Region))
            {
                return true;
            }
        }

        return false;
    }
}
