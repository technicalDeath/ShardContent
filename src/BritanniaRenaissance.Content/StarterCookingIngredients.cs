using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>Sixty ordinary fish-steak cooking attempts with bound raw input.</summary>
public sealed class StarterRawFishSteak : RawFishSteak, IStarterIssued
{
    public StarterRawFishSteak(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterRawFishSteak(Serial serial) : base(serial) { }

    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterRawFishSteak other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);

    public override void Serialize(IGenericWriter writer)
    {
        base.Serialize(writer);
        writer.WriteEncodedInt(0);
        writer.Write(OwnerSerial);
    }

    public override void Deserialize(IGenericReader reader)
    {
        base.Deserialize(reader);
        _ = reader.ReadEncodedInt();
        OwnerSerial = reader.ReadSerial();
    }
}

public sealed class StarterKindling : Kindling, IStarterIssued
{
    public StarterKindling(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterKindling(Serial serial) : base(serial) { }

    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterKindling other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);

    public override void Serialize(IGenericWriter writer)
    {
        base.Serialize(writer);
        writer.WriteEncodedInt(0);
        writer.Write(OwnerSerial);
    }

    public override void Deserialize(IGenericReader reader)
    {
        base.Deserialize(reader);
        _ = reader.ReadEncodedInt();
        OwnerSerial = reader.ReadSerial();
    }
}
