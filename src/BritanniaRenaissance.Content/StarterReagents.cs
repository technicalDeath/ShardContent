using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

public sealed class StarterBlackPearl : BlackPearl, IStarterIssued
{
    public StarterBlackPearl(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterBlackPearl(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    public override bool IsDeedable => false;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterBlackPearl other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
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

public sealed class StarterBloodmoss : Bloodmoss, IStarterIssued
{
    public StarterBloodmoss(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterBloodmoss(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    public override bool IsDeedable => false;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterBloodmoss other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
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

public sealed class StarterGarlic : Garlic, IStarterIssued
{
    public StarterGarlic(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterGarlic(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    public override bool IsDeedable => false;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterGarlic other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
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

public sealed class StarterGinseng : Ginseng, IStarterIssued
{
    public StarterGinseng(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterGinseng(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    public override bool IsDeedable => false;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterGinseng other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
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

public sealed class StarterMandrakeRoot : MandrakeRoot, IStarterIssued
{
    public StarterMandrakeRoot(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterMandrakeRoot(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    public override bool IsDeedable => false;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterMandrakeRoot other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
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

public sealed class StarterNightshade : Nightshade, IStarterIssued
{
    public StarterNightshade(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterNightshade(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    public override bool IsDeedable => false;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterNightshade other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
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

public sealed class StarterSulfurousAsh : SulfurousAsh, IStarterIssued
{
    public StarterSulfurousAsh(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterSulfurousAsh(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    public override bool IsDeedable => false;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterSulfurousAsh other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
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

public sealed class StarterSpidersSilk : SpidersSilk, IStarterIssued
{
    public StarterSpidersSilk(PlayerMobile owner, int amount) : base(amount)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterSpidersSilk(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    public override bool IsDeedable => false;
    public override bool CanStackWith(Item dropped) =>
        dropped is StarterSpidersSilk other && other.OwnerSerial == OwnerSerial && base.CanStackWith(dropped);
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
