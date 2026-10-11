using System.Text.Json;
using Xunit;
using static BritanniaRenaissance.Content.FurnishersService;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The Furnisher (docs/Design-Proposal-3-House-Decoration-Gold-Sink.md): the shipped data (what is sold, the approved price curve, the
/// hall), the rules that reject bad data, the flag, the decision about when the world is touched, and the matching of the hall's display
/// items against the world. Buying, placing, turning, re-deeding and respawning are checked live on a disposable host.
/// </summary>
public class FurnishersTests
{
    private static readonly string DataRoot = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration");

    private static FurnishersRules Shipped() =>
        FurnishersConfiguration.Parse(File.ReadAllText(Path.Combine(DataRoot, "furnishers.json")));

    private static ShardRules ShippedRules() =>
        JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(Path.Combine(DataRoot, "shard-rules.json")))!;

    private static FurnishersRules Copy() =>
        FurnishersConfiguration.Parse(JsonSerializer.Serialize(Shipped()));

    // ---- the shipped data

    [Fact]
    public void TheShippedFileValidates() => Assert.Empty(FurnishersConfiguration.Validate(Shipped()));

    [Fact]
    public void TheShopSellsTheApprovedSelection()
    {
        var rules = Shipped();
        var byRarity = rules.Pieces.GroupBy(p => p.Rarity).ToDictionary(g => g.Key, g => g.Count());

        Assert.Equal(37, rules.Pieces.Count);
        Assert.Equal(new Dictionary<int, int> { [1] = 8, [2] = 8, [3] = 8, [4] = 6, [5] = 4, [6] = 3 }, byRarity);
        Assert.Equal(80_000, rules.PriceCeiling);
        Assert.Equal(999, rules.StockDepth);
    }

    [Fact]
    public void EveryPriceFollowsTheApprovedCurve()
    {
        // base 2,000 gp x rarity multiplier x (0.85 to 1.15 across the rarity), rounded to 50 gp, nothing above 80,000 gp.
        var multiplier = new Dictionary<int, double> { [1] = 1, [2] = 2, [3] = 4, [4] = 8, [5] = 16, [6] = 35 };

        foreach (var piece in Shipped().Pieces)
        {
            var low = Math.Min(80_000, 2000 * multiplier[piece.Rarity] * 0.85) - 25;
            var high = Math.Min(80_000, 2000 * multiplier[piece.Rarity] * 1.15) + 25;

            Assert.True(piece.Price >= low && piece.Price <= high, $"{piece.Id} {piece.Name}: {piece.Price} gp is outside {low}-{high} for rarity {piece.Rarity}");
            Assert.Equal(0, piece.Price % 50);
        }
    }

    [Fact]
    public void ADeedHasSeveralGraphicsAndAnItemHasOne()
    {
        foreach (var piece in Shipped().Pieces)
        {
            if (piece.IsDeed)
            {
                Assert.Contains(piece.Facings, f => f.Parts.Count > 1);
            }
            else
            {
                Assert.All(piece.Facings, f => Assert.Single(f.Parts));
            }
        }
    }

    [Fact]
    public void AnItemThatTurnsHasADifferentGraphicInEveryFacing()
    {
        foreach (var piece in Shipped().Pieces.Where(p => !p.IsDeed && p.Facings.Count > 1))
        {
            var ids = piece.Facings.Select(f => f.Parts[0].Id).ToList();

            Assert.True(ids.Distinct().Count() == ids.Count, $"{piece.Id} {piece.Name} has two facings that look the same");
        }
    }

    [Fact]
    public void EveryPieceIsInTheHallAndTheFurnisherStandsInIt()
    {
        var rules = Shipped();
        var shown = rules.Hall.Items.Select(i => i.Piece).ToHashSet();

        Assert.All(rules.Pieces, p => Assert.Contains(p.Id, shown));
        Assert.Equal(229, rules.Hall.Items.Count);
        Assert.Equal([1622, 1654, 1641, 1680], rules.Hall.Bounds);
        Assert.Equal((1631, 1668), (rules.Vendor.X, rules.Vendor.Y));
    }

    [Fact]
    public void TheHallHoldsNoTwoDisplayItemsOfOnePieceOnOneSpot()
    {
        var keys = Shipped().Hall.Items.Select(KeyOf).ToList();

        Assert.Equal(keys.Count, keys.Distinct().Count());
    }

    // ---- bad data is rejected

    [Fact]
    public void ADuplicatePieceIdIsRejected()
    {
        var rules = Copy();
        rules.Pieces[1].Id = rules.Pieces[0].Id;

        Assert.Contains(FurnishersConfiguration.Validate(rules), e => e.Contains("listed twice"));
    }

    [Fact]
    public void APriceAboveTheCeilingIsRejected()
    {
        var rules = Copy();
        rules.Pieces[0].Price = rules.PriceCeiling + 1;

        Assert.Contains(FurnishersConfiguration.Validate(rules), e => e.Contains("ceiling"));
    }

    [Fact]
    public void ARarityThatIsNotDearerThanTheOneBelowIsRejected()
    {
        var rules = Copy();
        rules.Pieces.First(p => p.Rarity == 3).Price = rules.Pieces.Where(p => p.Rarity == 2).Max(p => p.Price);

        Assert.Contains(FurnishersConfiguration.Validate(rules), e => e.Contains("not above the dearest rarity 2"));
    }

    [Fact]
    public void AnItemWithTwoGraphicsIsRejected()
    {
        var rules = Copy();
        var item = rules.Pieces.First(p => !p.IsDeed);
        item.Facings[0].Parts.Add(new FurnishingPart { Id = 0x100 });

        Assert.Contains(FurnishersConfiguration.Validate(rules), e => e.Contains("exactly one graphic"));
    }

    [Fact]
    public void AWallPieceThatIsNotNorthOrWestIsRejected()
    {
        var rules = Copy();
        rules.Pieces.First(p => p.IsWall).Facings[0].Facing = "south";

        Assert.Contains(FurnishersConfiguration.Validate(rules), e => e.Contains("faces north or west"));
    }

    [Fact]
    public void ANoneFacingBesideOthersIsRejected()
    {
        var rules = Copy();
        rules.Pieces.First(p => p.Facings.Count > 1).Facings[0].Facing = "none";

        Assert.Contains(FurnishersConfiguration.Validate(rules), e => e.Contains("facing of none"));
    }

    [Fact]
    public void AVendorOutsideTheHallIsRejected()
    {
        var rules = Copy();
        rules.Vendor.X = 100;

        Assert.Contains(FurnishersConfiguration.Validate(rules), e => e.Contains("vendor") && e.Contains("outside"));
    }

    [Fact]
    public void ADisplayItemOfAnUnknownPieceOrOutsideTheHallIsRejected()
    {
        var rules = Copy();
        rules.Hall.Items[0].Piece = "CR-XXX-999";
        rules.Hall.Items[1].X = 5;

        var errors = FurnishersConfiguration.Validate(rules);

        Assert.Contains(errors, e => e.Contains("not a piece"));
        Assert.Contains(errors, e => e.Contains("outside hall.bounds"));
    }

    [Fact]
    public void APieceNotShownInTheHallIsRejected()
    {
        var rules = Copy();
        var gone = rules.Pieces[0].Id;
        rules.Hall.Items.RemoveAll(i => i.Piece == gone);

        Assert.Contains(FurnishersConfiguration.Validate(rules), e => e.Contains("not shown anywhere"));
    }

    // ---- the flag

    [Fact]
    public void TheShippedFlagIsOnSinceTheOwnerActivatedItOn2026_10_11()
    {
        var rules = ShippedRules();

        Assert.True(rules.FeatureFlags.Furnishers);
        Assert.Contains(nameof(DeferredFeatureFlags.Furnishers), rules.FeatureFlags.EnabledNames());
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void FurnishersNeedNoOtherFlagAndShowWhenOn()
    {
        var rules = ShippedRules();
        rules.FeatureFlags.Furnishers = true;

        Assert.Empty(ShardRulesConfiguration.Validate(rules));
        Assert.Contains(nameof(DeferredFeatureFlags.Furnishers), rules.FeatureFlags.EnabledNames());
    }

    [Fact]
    public void WithoutLoadedSettingsTheFurnishersAreOff() => Assert.False(Enabled);

    // ---- when the world is touched

    [Theory]
    [InlineData(false, false, EnsureAction.Remove)]
    [InlineData(false, true, EnsureAction.Remove)]
    [InlineData(true, true, EnsureAction.SkipFreshWorld)]
    [InlineData(true, false, EnsureAction.Place)]
    public void TheFlagAndTheWorldDecideWhatIsDone(bool enabled, bool fresh, EnsureAction expected) =>
        Assert.Equal(expected, Decide(enabled, fresh));

    // ---- matching the hall's display items against the world

    private static List<DisplayKey> StandingAsFiled(FurnishersRules rules) => rules.Hall.Items.Select(KeyOf).ToList();

    [Fact]
    public void ARightHallNeedsNothing()
    {
        var rules = Shipped();
        var plan = PlanDisplay(rules.Hall.Items, StandingAsFiled(rules));

        Assert.Empty(plan.Create);
        Assert.Empty(plan.RemoveIndices);
    }

    [Fact]
    public void AnEmptyWorldGetsTheWholeHall()
    {
        var rules = Shipped();
        var plan = PlanDisplay(rules.Hall.Items, []);

        Assert.Equal(rules.Hall.Items.Count, plan.Create.Count);
        Assert.Empty(plan.RemoveIndices);
    }

    [Fact]
    public void AMissingItemIsCreatedAndAnExtraOrRepeatedOneRemoved()
    {
        var rules = Shipped();
        var standing = StandingAsFiled(rules);
        var lost = standing[10];

        standing.RemoveAt(10);
        standing.Add(standing[0]);                                 // a second one on a filled spot
        standing.Add(new DisplayKey("CR-XXX-999", 0x100, 1, 1, 0, 0)); // something the file does not list

        var plan = PlanDisplay(rules.Hall.Items, standing);

        Assert.Single(plan.Create);
        Assert.Equal(lost, KeyOf(plan.Create[0]));
        Assert.Equal(2, plan.RemoveIndices.Count);
        Assert.Contains(standing.Count - 1, plan.RemoveIndices);
    }

    [Fact]
    public void AnItemThatDriftedIsReplacedWhereTheFileSaysItBelongs()
    {
        var rules = Shipped();
        var standing = StandingAsFiled(rules);
        standing[5] = standing[5] with { X = standing[5].X + 1 };

        var plan = PlanDisplay(rules.Hall.Items, standing);

        Assert.Single(plan.Create);
        Assert.Equal([5], plan.RemoveIndices);
    }

    // ---- the shelf

    [Fact]
    public void TheShelfListsEveryPieceAtItsPriceInFullDepthAndBuysNothing()
    {
        var rules = Shipped();
        FurnishersConfiguration.Install(rules);

        var entries = CreateBuyInfo();

        Assert.Equal(rules.Pieces.Count, entries.Count);

        for (var i = 0; i < entries.Count; i++)
        {
            var piece = rules.Pieces[i];
            var entry = entries[i];

            Assert.Equal(piece.Name, entry.Name);
            Assert.Equal(piece.Price, entry.Price);
            Assert.Equal(rules.StockDepth, entry.Amount);
            Assert.Equal(piece.IsDeed ? typeof(FurnishingDeed) : typeof(FurnishingItem), entry.Type);
            Assert.Equal(piece.Id, Assert.Single(entry.Args));
            Assert.Equal(piece.DefaultFacing.Parts[0].Id, entry.ItemID);
        }

        var sell = new SBFurnisher().SellInfo;

        Assert.Empty(sell.Types);
    }

    [Fact]
    public void ThePieceLookupFindsEveryPieceAndNothingElse()
    {
        FurnishersConfiguration.Install(Shipped());

        Assert.All(Shipped().Pieces, p => Assert.Same(FurnishersConfiguration.Find(p.Id), FurnishersConfiguration.Find(p.Id)));
        Assert.NotNull(FurnishersConfiguration.Find("CR-FRN-037"));
        Assert.Null(FurnishersConfiguration.Find("CR-XXX-999"));
        Assert.Null(FurnishersConfiguration.Find(null));
    }
}
