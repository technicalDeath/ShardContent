using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

public sealed class StarterBandage : Bandage, IStarterIssued
{
    public StarterBandage(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterBandage(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterBandage other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
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

public sealed class StarterArrow : Arrow, IStarterIssued, ICommodity
{
    public StarterArrow(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterArrow(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    bool ICommodity.IsDeedable => false;
    int ICommodity.DescriptionNumber => LabelNumber;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterArrow other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
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
