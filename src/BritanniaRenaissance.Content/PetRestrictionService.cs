using Server;
using Server.Mobiles;
using Server.Regions;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Beta 1 pet rules, all behind <c>featureFlags.petRestrictions</c>:
/// a tamed pet never attacks a player, and never stays inside a dungeon region (a ridden mount is on
/// the Internal map, so it is never "inside"). The test for "tamed pet" is <see cref="IsRestrictedKind"/>.
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

        var previousRefusal = BaseCreature.AttackCommandRefusalHandler;
        BaseCreature.AttackCommandRefusalHandler = (pet, target) =>
            previousRefusal?.Invoke(pet, target) ?? AttackRefusal(pet, target);
        EventSink.ServerStarted += SweepDungeons;
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

        pet.ControlMaster?.SendMessage($"{pet.Name} cannot follow you into a dungeon.");
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

        var name = pet.Name;
        var item = new ShrunkenPet();
        item.Shrink(pet, owner);

        if (owner.Backpack is not { } pack || !pack.TryDropItem(owner, item, false))
        {
            // Pack missing or full: the owner's bank keeps it safe, else the feet of a living owner.
            if (owner.BankBox is not { } bank || !bank.TryDropItem(owner, item, false))
            {
                item.MoveToWorld(owner.Location, owner.Map);
            }
        }

        owner.SendMessage($"{name} cannot stay in a dungeon, so it has been shrunk into your pack.");
        return true;
    }
}
