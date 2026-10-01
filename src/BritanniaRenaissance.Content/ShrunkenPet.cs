using Server;
using Server.Mobiles;
using Server.Regions;

namespace BritanniaRenaissance.Content;

/// <summary>
/// A pet held out of the world, in its owner's pack. The restriction service creates one only when
/// a restricted pet would otherwise end up inside a dungeon; the item is Blessed and Nontransferable
/// so it cannot be looted, stolen, traded or sold. The pet stays a saved Internal-map mobile that the
/// item refers to by serial; deleting the item deletes the pet.
/// </summary>
public sealed class ShrunkenPet : Item
{
    // Items currently bound to a pet. Stock does not save IsStabled on the creature (it rebuilds it from the
    // owner's Stabled list at load), so without this a restart would leave a shrunken pet unflagged and
    // start stock's 3-day abandoned-pet delete timer on it.
    private static readonly HashSet<ShrunkenPet> Bound = [];

    private Serial _petSerial = Serial.MinusOne;
    private Serial _ownerSerial = Serial.MinusOne;

    [Constructible]
    public ShrunkenPet() : base(ShrinkTable.DefaultItemID)
    {
        Weight = 1.0;
        LootType = LootType.Blessed;
    }

    public ShrunkenPet(Serial serial) : base(serial)
    {
    }

    public BaseCreature? Pet => _petSerial == Serial.MinusOne ? null : World.FindMobile(_petSerial) as BaseCreature;

    public Mobile? Owner => _ownerSerial == Serial.MinusOne ? null : World.FindMobile(_ownerSerial);

    public override bool Nontransferable => true;

    // A shrunken pet left on the ground (pack was full) may be lifted only by its owner or staff.
    public override bool VerifyMove(Mobile from) =>
        base.VerifyMove(from) && (from.AccessLevel > AccessLevel.Player || from.Serial == _ownerSerial);

    public override string DefaultName => Pet is { Deleted: false } pet ? $"a shrunken {pet.Name}" : "a shrunken pet";

    /// <summary>
    /// Takes the pet out of play and binds this item to it. The pet is released from its master (freeing
    /// follower slots) and parked on the Internal map flagged as stabled, which keeps stock cleanup away.
    /// </summary>
    public void Shrink(BaseCreature pet, Mobile owner)
    {
        pet.SetControlMaster(null);
        pet.ControlOrder = OrderType.Stay;
        pet.Internalize();
        pet.IsStabled = true;
        pet.StabledBy = owner;

        _petSerial = pet.Serial;
        _ownerSerial = owner.Serial;
        Bound.Add(this);
        ItemID = ShrinkTable.Lookup(pet);
        Hue = pet.Hue;
        InvalidateProperties();
    }

    /// <summary>Re-flags every shrunken pet after a world load, which also cancels its pending delete timer.</summary>
    public static void RestoreStabledFlags()
    {
        foreach (var item in Bound)
        {
            if (item.Deleted || item.Pet is not { Deleted: false } pet)
            {
                continue;
            }

            pet.IsStabled = true;
            pet.StabledBy = item.Owner;
        }
    }

    public override void OnDoubleClick(Mobile from)
    {
        if (!IsChildOf(from.Backpack))
        {
            from.SendLocalizedMessage(1042001); // That must be in your pack for you to use it.
            return;
        }

        var pet = Pet;
        if (pet is null || pet.Deleted)
        {
            from.SendMessage("The animal this represents is gone.");
            Delete();
            return;
        }

        if (from.Serial != _ownerSerial)
        {
            from.SendMessage("This is not your pet.");
            return;
        }

        if (!from.Alive)
        {
            return;
        }

        if (from is PlayerMobile player && !PetRestrictionService.MayRelease(player, pet))
        {
            from.SendMessage(
                pet is BaseMount
                    ? "Only one mount may be out in a dungeon, and only while you are not riding."
                    : "Your pet cannot be released inside a dungeon."
            );
            return;
        }

        if (from.Followers + pet.ControlSlots > from.FollowersMax)
        {
            from.SendLocalizedMessage(1049607); // You have too many followers to control that creature.
            return;
        }

        pet.IsStabled = false;
        pet.StabledBy = null;

        if (!pet.SetControlMaster(from))
        {
            pet.IsStabled = true;
            pet.StabledBy = from;
            return;
        }

        pet.ControlTarget = from;
        pet.ControlOrder = OrderType.Follow;
        pet.MoveToWorld(from.Location, from.Map);

        _petSerial = Serial.MinusOne;
        Bound.Remove(this);
        Delete();
    }

    public override void OnDelete()
    {
        // A pet still bound to this item is deleted with it; an unshrunk pet cleared its serial first.
        if (Pet is { Deleted: false } pet)
        {
            pet.Delete();
        }

        Bound.Remove(this);
        base.OnDelete();
    }

    public override void Serialize(IGenericWriter writer)
    {
        base.Serialize(writer);
        writer.WriteEncodedInt(0);
        writer.Write(_petSerial);
        writer.Write(_ownerSerial);
    }

    public override void Deserialize(IGenericReader reader)
    {
        base.Deserialize(reader);
        reader.ReadEncodedInt();
        _petSerial = reader.ReadSerial();
        _ownerSerial = reader.ReadSerial();

        if (_petSerial != Serial.MinusOne)
        {
            Bound.Add(this);
        }
    }
}
