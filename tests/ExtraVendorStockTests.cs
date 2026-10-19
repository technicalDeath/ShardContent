using System.Text.Json;
using Server;
using Server.Engines.Craft;
using Server.Items;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>The owner (2026-10-18) chose "Mage shops sell Recall/Mark" and "Crafted pricing for scrolls".</summary>
public class ExtraVendorStockTests
{
    private static List<ExtraVendorStockEntry> SourceEntries()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        return doc.RootElement.GetProperty("extraVendorStock").Deserialize<List<ExtraVendorStockEntry>>()!;
    }

    [Fact]
    public void TheMageSellsRecallAndMarkScrolls()
    {
        var shelves = ExtraVendorStock.ShelvesFor("Mage", SourceEntries());
        Assert.Contains(shelves, s => s.Type == typeof(RecallScroll) && s.Price == 42 && s.ItemId == 0x1F4C);
        Assert.Contains(shelves, s => s.Type == typeof(MarkScroll) && s.Price == 62 && s.ItemId == 0x1F59);
        Assert.Empty(ExtraVendorStock.ShelvesFor("Blacksmith", SourceEntries()));
    }

    [Fact]
    public void TheSourceEntriesValidate()
    {
        var errors = new List<string>();
        ExtraVendorStock.Validate(SourceEntries(), errors);
        Assert.Empty(errors);
    }

    [Fact]
    public void ABadEntryIsRefused()
    {
        var errors = new List<string>();
        ExtraVendorStock.Validate([new ExtraVendorStockEntry { Item = "NoSuchScroll", Price = 0, Amount = 0, Vendors = [] }], errors);
        Assert.True(errors.Count >= 2);
    }

    [Fact]
    public void AnEmptyListAddsNothing() => Assert.Empty(ExtraVendorStock.ShelvesFor("Mage", []));

    [Fact]
    public void InscribedSpellScrollsArePricedFromBlankScrollAndReagents()
    {
        var previous = Core.Expansion;
        try
        {
            Core.Expansion = Expansion.UOR;
            DefInscription.Initialize();
            var costs = CraftedGoodsPricing.BuildCosts();
            // Recall: blank scroll 5, black pearl 5, blood moss 5, mandrake root 3
            Assert.Equal(18, costs[typeof(RecallScroll)]);
            Assert.Equal(18, costs[typeof(MarkScroll)]);
            Assert.Equal(23, CraftedGoodsPricing.VendorPays(10, costs[typeof(RecallScroll)]));
            Assert.Equal(42, CraftedGoodsPricing.VendorCharges(42, costs[typeof(RecallScroll)]));
            // books and runebooks keep their stock prices
            Assert.False(costs.ContainsKey(typeof(Runebook)));
            Assert.False(costs.ContainsKey(typeof(Spellbook)));
        }
        finally
        {
            Core.Expansion = previous;
        }
    }
}
