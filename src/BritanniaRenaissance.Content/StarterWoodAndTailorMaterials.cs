using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

public sealed class StarterBoard : Board, IStarterIssued, ICommodity
{
    public StarterBoard(PlayerMobile owner, int amount) : base(amount) => OwnerSerial = owner.Serial;
    public StarterBoard(Serial serial) : base(serial) { }

    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    bool ICommodity.IsDeedable => false;
    int ICommodity.DescriptionNumber => LabelNumber;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterBoard other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
    public override DeathMoveResult OnInventoryDeath(Mobile parent) => DeathMoveResult.MoveToBackpack;
    public override DeathMoveResult OnParentDeath(Mobile parent) => DeathMoveResult.MoveToBackpack;

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

public sealed class StarterFeather : Feather, IStarterIssued, ICommodity
{
    public StarterFeather(PlayerMobile owner, int amount) : base(amount) => OwnerSerial = owner.Serial;
    public StarterFeather(Serial serial) : base(serial) { }

    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    bool ICommodity.IsDeedable => false;
    int ICommodity.DescriptionNumber => LabelNumber;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterFeather other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
    public override DeathMoveResult OnInventoryDeath(Mobile parent) => DeathMoveResult.MoveToBackpack;
    public override DeathMoveResult OnParentDeath(Mobile parent) => DeathMoveResult.MoveToBackpack;

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

public sealed class StarterCloth : Cloth, IStarterIssued, ICommodity
{
    public StarterCloth(PlayerMobile owner, int amount) : base(amount) => OwnerSerial = owner.Serial;
    public StarterCloth(Serial serial) : base(serial) { }

    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    bool ICommodity.IsDeedable => false;
    int ICommodity.DescriptionNumber => LabelNumber;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterCloth other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
    public override DeathMoveResult OnInventoryDeath(Mobile parent) => DeathMoveResult.MoveToBackpack;
    public override DeathMoveResult OnParentDeath(Mobile parent) => DeathMoveResult.MoveToBackpack;

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

public sealed class StarterLeather : Leather, IStarterIssued, ICommodity
{
    public StarterLeather(PlayerMobile owner, int amount) : base(amount) => OwnerSerial = owner.Serial;
    public StarterLeather(Serial serial) : base(serial) { }

    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    bool ICommodity.IsDeedable => false;
    int ICommodity.DescriptionNumber => LabelNumber;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterLeather other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
    public override DeathMoveResult OnInventoryDeath(Mobile parent) => DeathMoveResult.MoveToBackpack;
    public override DeathMoveResult OnParentDeath(Mobile parent) => DeathMoveResult.MoveToBackpack;

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
