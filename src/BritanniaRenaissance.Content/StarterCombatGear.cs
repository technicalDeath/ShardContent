using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

public sealed class StarterKatana : Katana, IStarterIssued
{
    public StarterKatana(PlayerMobile owner) : base()
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterKatana(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
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

public sealed class StarterClub : Club, IStarterIssued
{
    public StarterClub(PlayerMobile owner) : base()
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterClub(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
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

public sealed class StarterKryss : Kryss, IStarterIssued
{
    public StarterKryss(PlayerMobile owner) : base()
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterKryss(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
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

public sealed class StarterBow : Bow, IStarterIssued
{
    public StarterBow(PlayerMobile owner) : base()
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterBow(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
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

public sealed class StarterDagger : Dagger, IStarterIssued
{
    public StarterDagger(PlayerMobile owner) : base()
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterDagger(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
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

public sealed class StarterStuddedChest : StuddedChest, IStarterIssued
{
    public StarterStuddedChest(PlayerMobile owner) : base()
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterStuddedChest(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
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

public sealed class StarterStuddedLegs : StuddedLegs, IStarterIssued
{
    public StarterStuddedLegs(PlayerMobile owner) : base()
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterStuddedLegs(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
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

public sealed class StarterLeatherChest : LeatherChest, IStarterIssued
{
    public StarterLeatherChest(PlayerMobile owner) : base()
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterLeatherChest(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
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

public sealed class StarterLeatherLegs : LeatherLegs, IStarterIssued
{
    public StarterLeatherLegs(PlayerMobile owner) : base()
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterLeatherLegs(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
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

public sealed class StarterWoodenShield : WoodenShield, IStarterIssued
{
    public StarterWoodenShield(PlayerMobile owner) : base()
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterWoodenShield(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
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

public sealed class StarterSpellbook : Spellbook, IStarterIssued
{
    public StarterSpellbook(PlayerMobile owner) : base(0x382A8C38ul)
    {
        OwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
    }
    public StarterSpellbook(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
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

