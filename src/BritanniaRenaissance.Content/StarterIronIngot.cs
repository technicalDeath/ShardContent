using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>Character-bound iron that keeps its starter provenance until consumed by crafting.</summary>
public sealed class StarterIronIngot : IronIngot, IStarterIssued, ICommodity
{
    public StarterIronIngot(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
    }

    public StarterIronIngot(Serial serial) : base(serial)
    {
    }

    public Serial OwnerSerial { get; private set; }

    public override bool Nontransferable => true;

    bool ICommodity.IsDeedable => false;

    int ICommodity.DescriptionNumber => LabelNumber;

    // A starter stack must never absorb an unrestricted stack or another character's grant.
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterIronIngot other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);

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
