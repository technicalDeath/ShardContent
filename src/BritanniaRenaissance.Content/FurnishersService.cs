using Server;
using Server.Commands;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The Furnisher and the showroom hall (behind <c>furnishers</c>, off until the owner acknowledges it;
/// docs/Design-Proposal-3-House-Decoration-Gold-Sink.md). Configuration/furnishers.json says what is sold, where the vendor stands and what
/// every display item of the hall is, and this service makes the world match it on every start and on <c>[FurnisherRefresh</c>: a respawned
/// world gets the vendor and the hall back with no hand work, an edited file is picked up, and with the flag off both are removed.
/// Only objects inside the hall's bounds are managed, so nothing else in Britain is touched. A fresh world (no root items, no non-player
/// mobiles) is left alone, because world generation refuses a world that is not empty; the first start after generation places the hall.
/// </summary>
public static class FurnishersService
{
    public const string StatusCommand = "FurnisherStatus";
    public const string RefreshCommand = "FurnisherRefresh";

    private static readonly Dictionary<int, long> GoldByRarity = [];
    private static readonly Dictionary<string, int> SoldByPiece = [];
    private static bool _configured;

    public enum EnsureAction
    {
        /// <summary>The flag is off: take the vendor and the hall away.</summary>
        Remove,

        /// <summary>The world is empty: leave it empty so world generation can run.</summary>
        SkipFreshWorld,

        /// <summary>Make the world match the file.</summary>
        Place
    }

    /// <summary>A display item as it stands in the world, for comparing with the file.</summary>
    public readonly record struct DisplayKey(string Piece, int Id, int X, int Y, int Z, int Hue);

    /// <summary>What to do about the hall's display items: which wanted ones are missing, and which standing ones are extra or repeated.</summary>
    public readonly record struct DisplayPlan(IReadOnlyList<FurnisherDisplay> Create, IReadOnlyList<int> RemoveIndices);

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.Furnishers == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;

        FurnishersConfiguration.Load();
        BaseVendor.ItemsBought += OnItemsBought;
        EventSink.ServerStarted += OnServerStarted;
        CommandSystem.Register(StatusCommand, AccessLevel.Administrator, OnStatus);
        CommandSystem.Register(RefreshCommand, AccessLevel.Administrator, OnRefresh);
    }

    // ---- the rules, free of game objects so they can be tested directly

    public static EnsureAction Decide(bool enabled, bool worldIsFresh) =>
        !enabled ? EnsureAction.Remove : worldIsFresh ? EnsureAction.SkipFreshWorld : EnsureAction.Place;

    /// <summary>
    /// Matches the standing display items against the file one for one. A wanted item with no standing twin is created; a standing item with no
    /// wanted twin, or a second one on a spot already filled, is removed.
    /// </summary>
    public static DisplayPlan PlanDisplay(IReadOnlyList<FurnisherDisplay> wanted, IReadOnlyList<DisplayKey> standing)
    {
        var unmatched = new Dictionary<DisplayKey, List<int>>();

        for (var i = 0; i < standing.Count; i++)
        {
            if (!unmatched.TryGetValue(standing[i], out var list))
            {
                unmatched[standing[i]] = list = [];
            }

            list.Add(i);
        }

        var create = new List<FurnisherDisplay>();

        foreach (var item in wanted)
        {
            var key = KeyOf(item);

            if (unmatched.TryGetValue(key, out var list) && list.Count > 0)
            {
                list.RemoveAt(list.Count - 1);
            }
            else
            {
                create.Add(item);
            }
        }

        var remove = unmatched.Values.SelectMany(l => l).Order().ToList();
        return new DisplayPlan(create, remove);
    }

    public static DisplayKey KeyOf(FurnisherDisplay item) => new(item.Piece, item.Id, item.X, item.Y, item.Z, item.Hue);

    public static List<GenericBuyInfo> CreateBuyInfo()
    {
        var rules = FurnishersConfiguration.Settings;
        var entries = new List<GenericBuyInfo>();

        if (rules is null)
        {
            return entries;
        }

        foreach (var piece in rules.Pieces)
        {
            var icon = piece.DefaultFacing.Parts[0];

            entries.Add(
                new GenericBuyInfo(
                    piece.Name,
                    piece.IsDeed ? typeof(FurnishingDeed) : typeof(FurnishingItem),
                    piece.Price,
                    rules.StockDepth,
                    icon.Id,
                    icon.Hue,
                    [piece.Id]
                )
            );
        }

        return entries;
    }

    /// <summary>The shelf is full again: the stock vendor rule that halves or doubles a shelf would let one bulk buyer shrink it for everyone.</summary>
    public static void RefillShelf(BaseVendor vendor)
    {
        var depth = FurnishersConfiguration.Settings?.StockDepth ?? FurnishersConfiguration.MaxStockDepth;

        foreach (var entry in vendor.GetBuyInfo())
        {
            if (entry is GenericBuyInfo info)
            {
                info.MaxAmount = depth;
                info.Amount = depth;
            }
        }
    }

    // ---- the world

    /// <summary>Makes the world match the file and the flag. Returns what it did, for the log and the staff command.</summary>
    public static string Ensure()
    {
        var rules = FurnishersConfiguration.Settings;

        if (rules is null)
        {
            return "no furnishers configuration is loaded";
        }

        var map = Map.Felucca;
        var bounds = new Rectangle2D(
            rules.Hall.Bounds[0],
            rules.Hall.Bounds[1],
            rules.Hall.Bounds[2] - rules.Hall.Bounds[0] + 1,
            rules.Hall.Bounds[3] - rules.Hall.Bounds[1] + 1
        );

        var action = Decide(Enabled, Enabled && WorldIsFresh(map));
        var vendors = FindVendors(map, bounds);
        var displays = FindDisplays(map, bounds);

        switch (action)
        {
            case EnsureAction.SkipFreshWorld:
                return "left alone: Felucca is empty, so the hall is placed on the first start after world generation";

            case EnsureAction.Remove:
                foreach (var vendor in vendors)
                {
                    vendor.Delete();
                }

                foreach (var display in displays)
                {
                    display.Delete();
                }

                return vendors.Count + displays.Count == 0
                    ? "the flag is off and nothing is in the hall"
                    : $"the flag is off: removed {vendors.Count} vendor(s) and {displays.Count} display item(s)";
        }

        var plan = PlanDisplay(rules.Hall.Items, displays.ConvertAll(d => new DisplayKey(d.PieceId, d.ItemID, d.X, d.Y, d.Z, d.Hue)));

        foreach (var index in plan.RemoveIndices.Reverse())
        {
            displays[index].Delete();
        }

        foreach (var wanted in plan.Create)
        {
            new FurnisherDisplayItem(wanted.Piece, wanted.Id, wanted.Hue).MoveToWorld(new Point3D(wanted.X, wanted.Y, wanted.Z), map);
        }

        var spot = new Point3D(rules.Vendor.X, rules.Vendor.Y, rules.Vendor.Z);
        var vendorNote = "vendor in place";

        // Keep the one standing closest to the spot; a second would sell the same thing to the same queue.
        vendors.Sort((a, b) => a.GetDistanceToSqrt(spot).CompareTo(b.GetDistanceToSqrt(spot)));

        for (var i = 1; i < vendors.Count; i++)
        {
            vendors[i].Delete();
        }

        if (vendors.Count == 0)
        {
            var created = new Furnisher { Direction = ToDirection(rules.Vendor.Direction) };
            created.MoveToWorld(spot, map);
            vendorNote = "vendor created";
        }
        else if (vendors[0].Location != spot)
        {
            vendors[0].MoveToWorld(spot, map);
            vendors[0].Direction = ToDirection(rules.Vendor.Direction);
            vendorNote = "vendor moved back to the spot in the file";
        }

        if (vendors.Count > 1)
        {
            vendorNote += $", {vendors.Count - 1} extra removed";
        }

        return $"{vendorNote}; display items: {plan.Create.Count} created, {plan.RemoveIndices.Count} removed, " +
               $"{rules.Hall.Items.Count - plan.Create.Count} already in place";
    }

    private static Direction ToDirection(string name) =>
        FurnishersConfiguration.TryParseDirection(name, out var direction) ? direction : Direction.South;

    private static List<Furnisher> FindVendors(Map map, Rectangle2D bounds)
    {
        var found = new List<Furnisher>();

        foreach (var mobile in map.GetMobilesInBounds(bounds))
        {
            if (mobile is Furnisher furnisher)
            {
                found.Add(furnisher);
            }
        }

        return found;
    }

    private static List<FurnisherDisplayItem> FindDisplays(Map map, Rectangle2D bounds)
    {
        var found = new List<FurnisherDisplayItem>();

        foreach (var item in map.GetItemsInBounds<FurnisherDisplayItem>(bounds))
        {
            found.Add(item);
        }

        return found;
    }

    /// <summary>The same test world generation uses: an empty Felucca has no root items and no mobiles that are not players.</summary>
    private static bool WorldIsFresh(Map map)
    {
        var all = new Rectangle2D(0, 0, map.Width, map.Height);

        foreach (var item in map.GetItemsInBounds(all))
        {
            if (item.Parent is null)
            {
                return false;
            }
        }

        foreach (var mobile in map.GetMobilesInBounds(all))
        {
            if (mobile is not PlayerMobile)
            {
                return false;
            }
        }

        return true;
    }

    private static void OnServerStarted()
    {
        EventSink.ServerStarted -= OnServerStarted;

        try
        {
            var result = Ensure();
            ShardAuditLog.Record("furnishers", "ensure", details: $"flag={(Enabled ? "on" : "off")}; {result}");
        }
        catch (Exception ex)
        {
            ShardAuditLog.Record("furnishers", "ensure-failed", details: ex.Message);
            throw;
        }
    }

    // ---- sales

    private static void OnItemsBought(BaseVendor vendor, Mobile buyer, GenericBuyInfo info, int amount)
    {
        if (vendor is not Furnisher)
        {
            return;
        }

        info.Amount = info.MaxAmount = FurnishersConfiguration.Settings?.StockDepth ?? FurnishersConfiguration.MaxStockDepth;

        var pieceId = info.Args is { Length: > 0 } ? info.Args[0] as string : null;
        var piece = FurnishersConfiguration.Find(pieceId);
        var total = (long)info.Price * amount;

        if (piece is not null)
        {
            GoldByRarity[piece.Rarity] = GoldByRarity.GetValueOrDefault(piece.Rarity) + total;
            SoldByPiece[piece.Id] = SoldByPiece.GetValueOrDefault(piece.Id) + amount;
        }

        ShardAuditLog.Record(
            "furnishers",
            "bought",
            buyer,
            details: $"vendor={vendor.Serial.Value}; piece={pieceId}; rarity={piece?.Rarity}; count={amount}; unitPrice={info.Price}; total={total}"
        );
    }

    // ---- staff commands

    [Usage("FurnisherStatus"), Description("Shows the Furnisher: the flag, what the file lists, what stands in the hall, and what has sold since the server started.")]
    private static void OnStatus(CommandEventArgs e)
    {
        var from = e.Mobile;
        var rules = FurnishersConfiguration.Settings;

        if (rules is null)
        {
            from.SendMessage("No furnishers configuration is loaded.");
            return;
        }

        var map = Map.Felucca;
        var bounds = new Rectangle2D(
            rules.Hall.Bounds[0], rules.Hall.Bounds[1], rules.Hall.Bounds[2] - rules.Hall.Bounds[0] + 1, rules.Hall.Bounds[3] - rules.Hall.Bounds[1] + 1
        );
        var vendors = FindVendors(map, bounds);
        var displays = FindDisplays(map, bounds);

        from.SendMessage($"Furnishers flag: {(Enabled ? "ON" : "off")}. File: {rules.Pieces.Count} pieces ({rules.Pieces.Count(p => !p.IsDeed)} items, {rules.Pieces.Count(p => p.IsDeed)} deeds), {rules.Hall.Items.Count} hall display items.");
        from.SendMessage($"In the hall: {vendors.Count} vendor(s) (expected {(Enabled ? 1 : 0)}), {displays.Count} display item(s) (expected {(Enabled ? rules.Hall.Items.Count : 0)}).");
        from.SendMessage($"Sold since start: {SoldByPiece.Values.Sum()} piece(s), {GoldByRarity.Values.Sum():N0} gp ({string.Join(", ", GoldByRarity.OrderBy(kv => kv.Key).Select(kv => $"rarity {kv.Key}: {kv.Value:N0}"))}).");
    }

    [Usage("FurnisherRefresh"), Description("Makes the world match the furnishers file and flag now: places or repairs the vendor and the hall, or removes them.")]
    private static void OnRefresh(CommandEventArgs e)
    {
        if (World.Saving)
        {
            e.Mobile.SendMessage("Refusing to change the hall while a world save is active.");
            return;
        }

        var result = Ensure();
        ShardAuditLog.Record("furnishers", "refresh", e.Mobile, details: result);
        e.Mobile.SendMessage($"Furnishers: {result}.");
    }
}
