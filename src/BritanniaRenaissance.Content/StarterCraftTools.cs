using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

// Starter tools retain their concrete stock type so the ordinary craft and harvest
// paths accept them. The owner marker survives save/restart and death protection
// follows the owner's logged-in GameTime.
internal static class StarterToolDeathPolicy
{
    public static bool Keep(Mobile parent, Serial ownerSerial, bool ordinaryKeep) =>
        ordinaryKeep || parent is PlayerMobile player && player.Serial == ownerSerial &&
        StarterScissors.IsProtected(player.GameTime);
}

public sealed class StarterTongs : Tongs, IStarterIssued
{
    public StarterTongs(PlayerMobile owner) : base(50) => OwnerSerial = owner.Serial;
    public StarterTongs(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    private bool KeepOnDeath(Mobile parent) => StarterToolDeathPolicy.Keep(parent, OwnerSerial,
        !Movable || parent.KeepsItemsOnDeath || CheckBlessed(parent) ||
        CheckNewbied() && !parent.Murderer);
    public override DeathMoveResult OnInventoryDeath(Mobile parent) =>
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
    public override DeathMoveResult OnParentDeath(Mobile parent) =>
        !Movable ? DeathMoveResult.RemainEquipped :
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
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

public sealed class StarterPickaxe : Pickaxe, IStarterIssued
{
    public StarterPickaxe(PlayerMobile owner) : base() => OwnerSerial = owner.Serial;
    public StarterPickaxe(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    private bool KeepOnDeath(Mobile parent) => StarterToolDeathPolicy.Keep(parent, OwnerSerial,
        !Movable || parent.KeepsItemsOnDeath || CheckBlessed(parent) ||
        CheckNewbied() && !parent.Murderer);
    public override DeathMoveResult OnInventoryDeath(Mobile parent) =>
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
    public override DeathMoveResult OnParentDeath(Mobile parent) =>
        !Movable ? DeathMoveResult.RemainEquipped :
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
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

public sealed class StarterTinkerTools : TinkerTools, IStarterIssued
{
    public StarterTinkerTools(PlayerMobile owner) : base(50) => OwnerSerial = owner.Serial;
    public StarterTinkerTools(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    private bool KeepOnDeath(Mobile parent) => StarterToolDeathPolicy.Keep(parent, OwnerSerial,
        !Movable || parent.KeepsItemsOnDeath || CheckBlessed(parent) ||
        CheckNewbied() && !parent.Murderer);
    public override DeathMoveResult OnInventoryDeath(Mobile parent) =>
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
    public override DeathMoveResult OnParentDeath(Mobile parent) =>
        !Movable ? DeathMoveResult.RemainEquipped :
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
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

public sealed class StarterSewingKit : SewingKit, IStarterIssued
{
    public StarterSewingKit(PlayerMobile owner) : base(50) => OwnerSerial = owner.Serial;
    public StarterSewingKit(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    private bool KeepOnDeath(Mobile parent) => StarterToolDeathPolicy.Keep(parent, OwnerSerial,
        !Movable || parent.KeepsItemsOnDeath || CheckBlessed(parent) ||
        CheckNewbied() && !parent.Murderer);
    public override DeathMoveResult OnInventoryDeath(Mobile parent) =>
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
    public override DeathMoveResult OnParentDeath(Mobile parent) =>
        !Movable ? DeathMoveResult.RemainEquipped :
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
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

public sealed class StarterSaw : Saw, IStarterIssued
{
    public StarterSaw(PlayerMobile owner) : base(50) => OwnerSerial = owner.Serial;
    public StarterSaw(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    private bool KeepOnDeath(Mobile parent) => StarterToolDeathPolicy.Keep(parent, OwnerSerial,
        !Movable || parent.KeepsItemsOnDeath || CheckBlessed(parent) ||
        CheckNewbied() && !parent.Murderer);
    public override DeathMoveResult OnInventoryDeath(Mobile parent) =>
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
    public override DeathMoveResult OnParentDeath(Mobile parent) =>
        !Movable ? DeathMoveResult.RemainEquipped :
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
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

public sealed class StarterFletcherTools : FletcherTools, IStarterIssued
{
    public StarterFletcherTools(PlayerMobile owner) : base(50) => OwnerSerial = owner.Serial;
    public StarterFletcherTools(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    private bool KeepOnDeath(Mobile parent) => StarterToolDeathPolicy.Keep(parent, OwnerSerial,
        !Movable || parent.KeepsItemsOnDeath || CheckBlessed(parent) ||
        CheckNewbied() && !parent.Murderer);
    public override DeathMoveResult OnInventoryDeath(Mobile parent) =>
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
    public override DeathMoveResult OnParentDeath(Mobile parent) =>
        !Movable ? DeathMoveResult.RemainEquipped :
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
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

public sealed class StarterScribesPen : ScribesPen, IStarterIssued
{
    public StarterScribesPen(PlayerMobile owner) : base(50) => OwnerSerial = owner.Serial;
    public StarterScribesPen(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    private bool KeepOnDeath(Mobile parent) => StarterToolDeathPolicy.Keep(parent, OwnerSerial,
        !Movable || parent.KeepsItemsOnDeath || CheckBlessed(parent) ||
        CheckNewbied() && !parent.Murderer);
    public override DeathMoveResult OnInventoryDeath(Mobile parent) =>
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
    public override DeathMoveResult OnParentDeath(Mobile parent) =>
        !Movable ? DeathMoveResult.RemainEquipped :
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
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

public sealed class StarterMortarPestle : MortarPestle, IStarterIssued
{
    public StarterMortarPestle(PlayerMobile owner) : base(50) => OwnerSerial = owner.Serial;
    public StarterMortarPestle(Serial serial) : base(serial) { }
    public Serial OwnerSerial { get; private set; }
    public override bool Nontransferable => true;
    private bool KeepOnDeath(Mobile parent) => StarterToolDeathPolicy.Keep(parent, OwnerSerial,
        !Movable || parent.KeepsItemsOnDeath || CheckBlessed(parent) ||
        CheckNewbied() && !parent.Murderer);
    public override DeathMoveResult OnInventoryDeath(Mobile parent) =>
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
    public override DeathMoveResult OnParentDeath(Mobile parent) =>
        !Movable ? DeathMoveResult.RemainEquipped :
        KeepOnDeath(parent) ? DeathMoveResult.MoveToBackpack : DeathMoveResult.MoveToCorpse;
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

