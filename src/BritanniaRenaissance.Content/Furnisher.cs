using Server;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The Furnisher, the vendor who stands in the showroom hall in Britain and sells furnishings for gold (docs/Design-Proposal-3-House-Decoration-Gold-Sink.md).
/// The stock is Configuration/furnishers.json: every piece, at its price, in a depth that is refilled after every purchase, so the shop never
/// runs out and a bulk buyer cannot starve the next. Nothing is bought back, so the gold paid for a furnishing leaves the world for good.
/// The Furnisher is a fixture: it does not wander and cannot be harmed. Behind the <c>furnishers</c> flag; with the flag off it does not sell and
/// the service removes it.
/// </summary>
public sealed class Furnisher : BaseVendor
{
    private readonly List<SBInfo> _sbInfos = [];

    [Constructible]
    public Furnisher() : base("the furnisher")
    {
        CantWalk = true;
    }

    public Furnisher(Serial serial) : base(serial)
    {
    }

    protected override List<SBInfo> SBInfos => _sbInfos;

    public override bool IsActiveVendor => FurnishersService.Enabled;

    // Never a buyer: a furnishing is a gold sink and is not bought back at any price.
    public override bool IsActiveBuyer => false;

    public override bool IsInvulnerable => true;

    // The price curve is the price a player pays; no town tax on top of it.
    public override int GetPriceScalar() => 100;

    public override void InitSBInfo() => _sbInfos.Add(new SBFurnisher());

    public override void Restock()
    {
        LastRestock = Core.Now;
        FurnishersService.RefillShelf(this);
    }

    // No state of its own (the shelf is rebuilt from the file on load); a version is written so the format can grow without a migration guess.
    public override void Serialize(IGenericWriter writer)
    {
        base.Serialize(writer);
        writer.WriteEncodedInt(0);
    }

    public override void Deserialize(IGenericReader reader)
    {
        base.Deserialize(reader);
        _ = reader.ReadEncodedInt();
    }
}

public sealed class SBFurnisher : SBInfo
{
    public override IShopSellInfo SellInfo { get; } = new GenericSellInfo();

    public override List<GenericBuyInfo> BuyInfo { get; } = FurnishersService.CreateBuyInfo();
}
