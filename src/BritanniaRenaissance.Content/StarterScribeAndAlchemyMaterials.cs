using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

public sealed class StarterBlankScroll : BlankScroll, IStarterIssued, ICommodity
{
    public StarterBlankScroll(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterBlankScroll(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    bool ICommodity.IsDeedable => false;
    int ICommodity.DescriptionNumber => LabelNumber;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterBlankScroll other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
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

public sealed class StarterBottle : Bottle, IStarterIssued, ICommodity
{
    public StarterBottle(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterBottle(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    bool ICommodity.IsDeedable => false;
    int ICommodity.DescriptionNumber => LabelNumber;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterBottle other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
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
