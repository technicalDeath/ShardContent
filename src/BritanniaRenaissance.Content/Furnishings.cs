using Server;
using Server.Items;
using Server.Multis;

namespace BritanniaRenaissance.Content;

/// <summary>
/// What the Furnisher sells, as items (docs/Design-Proposal-3-House-Decoration-Gold-Sink.md). Each piece is described in
/// Configuration/furnishers.json and an object stores only the piece's id, so retuning a name or price needs no migration and a piece
/// that is later dropped from the file still exists as the graphic it was bought with. A one-graphic piece is a <see cref="FurnishingItem"/>
/// (locked down in a house like any furniture); a piece of several graphics is sold as a <see cref="FurnishingDeed"/> that places a
/// <see cref="FurnishingAddon"/> through the stock addon rules (own house, no doors, a wall for a hanging), is re-deeded by chopping it, and
/// is turned with the Interior Decorator through the facings the file lists.
/// </summary>
internal static class FurnishingText
{
    public const string UnknownName = "a furnishing";

    /// <summary>The tooltip lines every part of a furnishing carries after its name: how rare it is and which collection it belongs to.</summary>
    public static void AddLines(IPropertyList list, FurnisherPiece? piece)
    {
        if (piece is null)
        {
            return;
        }

        list.Add($"{piece.RarityName}");
        list.Add($"{piece.Collection}");
    }

    public static string DeedName(FurnisherPiece? piece) => piece is null ? "a furnishing deed" : $"{piece.Name} (deed)";
}

/// <summary>Turns a one-graphic furnishing through the facings its piece lists, for the Interior Decorator and the staff Flip command.</summary>
[AttributeUsage(AttributeTargets.Class)]
public sealed class FurnishingFlippableAttribute : FlippableAttribute
{
    public override void Flip(Item item)
    {
        if (item is not FurnishingItem { Piece: { Facings.Count: > 1 } piece })
        {
            return;
        }

        var current = piece.Facings.FindIndex(f => f.Parts[0].Id == item.ItemID);
        var next = piece.Facings[(current + 1) % piece.Facings.Count].Parts[0];

        item.ItemID = next.Id;
        item.Hue = next.Hue;
    }
}

/// <summary>A one-graphic furnishing: sold, carried, traded, dropped and locked down as the item itself.</summary>
[FurnishingFlippable]
public sealed class FurnishingItem : Item
{
    private string _pieceId = "";

    [Constructible]
    public FurnishingItem(string pieceId) : base(FurnishersConfiguration.Find(pieceId)?.DefaultFacing.Parts[0].Id ?? 0x1)
    {
        _pieceId = pieceId;
        Hue = FurnishersConfiguration.Find(pieceId)?.DefaultFacing.Parts[0].Hue ?? 0;
    }

    public FurnishingItem(Serial serial) : base(serial)
    {
    }

    public string PieceId => _pieceId;

    public FurnisherPiece? Piece => FurnishersConfiguration.Find(_pieceId);

    public override double DefaultWeight => 5.0;

    public override string DefaultName => Piece?.Name ?? FurnishingText.UnknownName;

    public override void GetProperties(IPropertyList list)
    {
        base.GetProperties(list);
        FurnishingText.AddLines(list, Piece);
    }

    public override void Serialize(IGenericWriter writer)
    {
        base.Serialize(writer);
        writer.WriteEncodedInt(0);
        writer.Write(_pieceId);
    }

    public override void Deserialize(IGenericReader reader)
    {
        base.Deserialize(reader);
        _ = reader.ReadEncodedInt();
        _pieceId = reader.ReadString() ?? "";
    }
}

/// <summary>
/// A multi-graphic furnishing in the backpack. The stock deed makes a bought deed Newbied before the Age of Shadows, but a furnishing is
/// tradeable and lootable like any other item (owner ruling, 2026-10-08), so it is made ordinary again.
/// </summary>
public sealed class FurnishingDeed : BaseAddonDeed
{
    private string _pieceId = "";

    [Constructible]
    public FurnishingDeed(string pieceId)
    {
        _pieceId = pieceId;
        LootType = LootType.Regular;
    }

    public FurnishingDeed(Serial serial) : base(serial)
    {
    }

    public string PieceId => _pieceId;

    public FurnisherPiece? Piece => FurnishersConfiguration.Find(_pieceId);

    public override BaseAddon Addon => new FurnishingAddon(_pieceId);

    public override string DefaultName => FurnishingText.DeedName(Piece);

    public override void GetProperties(IPropertyList list)
    {
        base.GetProperties(list);
        FurnishingText.AddLines(list, Piece);
    }

    public override void Serialize(IGenericWriter writer)
    {
        base.Serialize(writer);
        writer.WriteEncodedInt(0);
        writer.Write(_pieceId);
    }

    public override void Deserialize(IGenericReader reader)
    {
        base.Deserialize(reader);
        _ = reader.ReadEncodedInt();
        _pieceId = reader.ReadString() ?? "";
    }
}

/// <summary>Turns a placed multi-graphic furnishing through the facings its piece lists, keeping it where it fits and refusing where it does not.</summary>
[AttributeUsage(AttributeTargets.Class)]
public sealed class FurnishingFlippableAddonAttribute : FlippableAddonAttribute
{
    public override void Flip(Mobile from, Item addon)
    {
        if (addon is FurnishingAddon furnishing)
        {
            furnishing.TurnToNextFacing(from);
        }
    }
}

[FurnishingFlippableAddon]
public sealed class FurnishingAddon : BaseAddon
{
    private string _pieceId = "";

    [Constructible]
    public FurnishingAddon(string pieceId)
    {
        _pieceId = pieceId;

        if (Piece is { } piece)
        {
            Direction = FurnishersConfiguration.ToDirection(piece.DefaultFacing.Facing);
            BuildComponents(piece.DefaultFacing);
        }
    }

    public FurnishingAddon(Serial serial) : base(serial)
    {
    }

    public string PieceId => _pieceId;

    public FurnisherPiece? Piece => FurnishersConfiguration.Find(_pieceId);

    public override BaseAddonDeed Deed => new FurnishingDeed(_pieceId);

    // Each graphic keeps the hue the catalog gave it: the stock rule would paint the whole piece the colour of the last part set.
    public override bool ShareHue => false;

    public override string DefaultName => Piece?.Name ?? FurnishingText.UnknownName;

    private void BuildComponents(FurnishingFacing facing)
    {
        foreach (var part in facing.Parts)
        {
            AddComponent(new FurnishingComponent(part.Id) { Hue = part.Hue }, part.Dx, part.Dy, part.Dz);
        }
    }

    private void Rebuild(FurnishingFacing facing)
    {
        foreach (var component in Components.ToArray())
        {
            component.Addon = null;
            component.Delete();
        }

        ClearComponents();
        Direction = FurnishersConfiguration.ToDirection(facing.Facing);
        BuildComponents(facing);
    }

    /// <summary>
    /// The next facing in the piece's list. The new facing has to fit where the piece stands (floor clear, a wall behind a hanging);
    /// if it does not, the piece goes back to the facing it had and the player is told why, as the stock addon turn does.
    /// </summary>
    public void TurnToNextFacing(Mobile from)
    {
        if (Piece is not { Facings.Count: > 1 } piece)
        {
            return;
        }

        var current = Math.Max(0, piece.Facings.FindIndex(f => FurnishersConfiguration.ToDirection(f.Facing) == Direction));
        var next = (current + 1) % piece.Facings.Count;

        Rebuild(piece.Facings[next]);

        BaseHouse? house = null;
        var map = Map;

        // Checked with the addon off the map so the old and new graphics do not block themselves.
        Map = Map.Internal;
        var result = CouldFit(Location, from.Map, from, ref house);
        Map = map;

        if (result == AddonFitResult.Valid)
        {
            return;
        }

        Rebuild(piece.Facings[current]);

        switch (result)
        {
            case AddonFitResult.Blocked:
                from.SendLocalizedMessage(500269); // You cannot build that there.
                break;
            case AddonFitResult.NotInHouse:
                from.SendLocalizedMessage(500274); // You can only place this in a house that you own!
                break;
            case AddonFitResult.DoorTooClose:
                from.SendLocalizedMessage(500271); // You cannot build near the door.
                break;
            case AddonFitResult.NoWall:
                from.SendLocalizedMessage(500268); // This object needs to be mounted on something.
                break;
        }
    }

    public override void GetProperties(IPropertyList list)
    {
        base.GetProperties(list);
        FurnishingText.AddLines(list, Piece);
    }

    public override void Serialize(IGenericWriter writer)
    {
        base.Serialize(writer);
        writer.WriteEncodedInt(0);
        writer.Write(_pieceId);
    }

    public override void Deserialize(IGenericReader reader)
    {
        base.Deserialize(reader);
        _ = reader.ReadEncodedInt();
        _pieceId = reader.ReadString() ?? "";
    }
}

/// <summary>One graphic of a placed multi-graphic furnishing. It carries no state of its own: the piece, and so the name and the wall rule, come from its addon.</summary>
public sealed class FurnishingComponent : AddonComponent
{
    public FurnishingComponent(int itemId) : base(itemId)
    {
    }

    public FurnishingComponent(Serial serial) : base(serial)
    {
    }

    private FurnisherPiece? Piece => (Addon as FurnishingAddon)?.Piece;

    public override string DefaultName => Piece?.Name ?? FurnishingText.UnknownName;

    public override bool NeedsWall => Piece?.IsWall == true;

    /// <summary>A "west" hanging is on the wall to its west; any other (north) is on the wall to its north.</summary>
    public override Point3D WallPosition => Addon?.Direction == Direction.West ? new Point3D(-1, 0, 0) : new Point3D(0, -1, 0);

    public override void GetProperties(IPropertyList list)
    {
        base.GetProperties(list);
        FurnishingText.AddLines(list, Piece);
    }

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

/// <summary>
/// One graphic of the showroom hall, placed from Configuration/furnishers.json by <see cref="FurnishersService"/>: an unmovable look-alike of
/// part of a piece that names it and gives its price when pointed at. It has no use of its own and is removed with the feature flag.
/// </summary>
public sealed class FurnisherDisplayItem : Item
{
    private string _pieceId = "";

    public FurnisherDisplayItem(string pieceId, int itemId, int hue) : base(itemId)
    {
        _pieceId = pieceId;
        Hue = hue;
        Movable = false;
    }

    public FurnisherDisplayItem(Serial serial) : base(serial)
    {
    }

    public string PieceId => _pieceId;

    public FurnisherPiece? Piece => FurnishersConfiguration.Find(_pieceId);

    public override string DefaultName => Piece?.Name ?? FurnishingText.UnknownName;

    public override void GetProperties(IPropertyList list)
    {
        base.GetProperties(list);

        if (Piece is { } piece)
        {
            FurnishingText.AddLines(list, piece);
            list.Add($"{"Price (gp)"}\t{piece.Price:N0}");
        }
    }

    public override void Serialize(IGenericWriter writer)
    {
        base.Serialize(writer);
        writer.WriteEncodedInt(0);
        writer.Write(_pieceId);
    }

    public override void Deserialize(IGenericReader reader)
    {
        base.Deserialize(reader);
        _ = reader.ReadEncodedInt();
        _pieceId = reader.ReadString() ?? "";
    }
}
