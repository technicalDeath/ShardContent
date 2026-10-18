using System.Text.Json;
using System.Text.RegularExpressions;
using Server;
using Server.Items;
using Server.Logging;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The sell-price line of an item's tooltip (docs/Tooltip-Sell-Price-Plan.md), behind <c>featureFlags.sellPriceTooltips</c>: "Value: 3gp at Butcher". The price is asked of
/// the same shop lists a vendor uses when it buys (stock lists, the crafted-goods pricing and the extra buyers are all inside them), for the vendor types that spawn in this world's
/// generated data, so the tooltip cannot disagree with the sale. Items a vendor would refuse (newbied or blessed, a container with something in it, not movable) say nothing, and so do
/// unidentified magic and Low-quality weapons and armor, whose stock price would give the magic or the quality away.
/// </summary>
public static class SellPriceTooltips
{
    public readonly record struct Quote(string Shop, int Price);

    private static readonly ILogger Logger = LogFactory.GetLogger(typeof(SellPriceTooltips));
    private static readonly List<(string Shop, IShopSellInfo[] Info)> Shops = [];
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.SellPriceTooltips == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        EventSink.ServerStarted += Build;
    }

    /// <summary>"AnimalTrainer" becomes "Animal Trainer": the shop as a player knows it.</summary>
    public static string ShopName(string typeName) => Regex.Replace(typeName, "(?<=[a-z])(?=[A-Z])", " ");

    /// <summary>
    /// The best price and the shop that pays it: "Value: 22gp at Blacksmith". A stack says "each" after the price. Equal best prices go to the shop that comes first alphabetically.
    /// No quote, no line.
    /// </summary>
    public static string? Describe(IReadOnlyList<Quote> quotes, int amount)
    {
        if (quotes.Count == 0)
        {
            return null;
        }

        var best = quotes.OrderByDescending(q => q.Price).ThenBy(q => q.Shop, StringComparer.Ordinal).First();
        var each = amount > 1 ? " each" : string.Empty;

        return $"Value: {best.Price}gp{each} at {best.Shop}";
    }

    /// <summary>The line for an item, or null when the shops would not buy it or the tooltip must not say.</summary>
    public static string? LineFor(Item item)
    {
        if (!Enabled || Shops.Count == 0 || !item.Movable || !item.IsStandardLoot() || item is Container { Items.Count: > 0 })
        {
            return null;
        }

        if (item is BaseWeapon { Quality: WeaponQuality.Low } or BaseArmor { Quality: ArmorQuality.Low })
        {
            return null;
        }

        var quotes = new List<Quote>();

        foreach (var (shop, info) in Shops)
        {
            var best = 0;

            foreach (var ssi in info)
            {
                if (item.InTypeList(ssi.Types) && ssi.IsSellable(item))
                {
                    best = Math.Max(best, ssi.GetSellPriceFor(item));
                }
            }

            if (best > 0)
            {
                quotes.Add(new Quote(shop, best));
            }
        }

        return Describe(quotes, item.Amount);
    }

    private static void Build()
    {
        Shops.Clear();

        if (!Enabled)
        {
            return;
        }

        foreach (var name in VendorNames().OrderBy(n => n, StringComparer.OrdinalIgnoreCase))
        {
            var type = AssemblyHandler.FindTypeByName(name);

            if (type is null || type.IsAbstract || !typeof(BaseVendor).IsAssignableFrom(type))
            {
                continue;
            }

            BaseVendor? vendor = null;

            try
            {
                vendor = Activator.CreateInstance(type) as BaseVendor;

                if (vendor?.GetSellInfo() is { Length: > 0 } info)
                {
                    Shops.Add((ShopName(type.Name), info));
                }
            }
            catch (Exception e)
            {
                Logger.Warning(e, "Sell price tooltips: could not read the shop lists of {Vendor}", name);
            }
            finally
            {
                vendor?.Delete();
            }
        }

        Logger.Information("Sell price tooltips: {Count} vendor types read from the world's spawn data", Shops.Count);
    }

    /// <summary>Vendor type names in the generated spawn data (Vendors.json and Britain's overrides): every spawner entry name.</summary>
    private static HashSet<string> VendorNames()
    {
        var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var directory = Path.Combine(Core.BaseDirectory, "Data", "BritanniaRenaissance", "Alpha2b", "Spawns");

        foreach (var file in new[] { "Vendors.json", "britain-vendor-overrides.json" })
        {
            var path = Path.Combine(directory, file);

            if (!File.Exists(path))
            {
                continue;
            }

            try
            {
                using var doc = JsonDocument.Parse(File.ReadAllText(path));
                Collect(doc.RootElement, names);
            }
            catch (Exception e)
            {
                Logger.Warning(e, "Sell price tooltips: could not read {File}", file);
            }
        }

        return names;
    }

    private static void Collect(JsonElement element, HashSet<string> names)
    {
        switch (element.ValueKind)
        {
            case JsonValueKind.Object:
                foreach (var property in element.EnumerateObject())
                {
                    if (property.NameEquals("entries") && property.Value.ValueKind == JsonValueKind.Array)
                    {
                        foreach (var entry in property.Value.EnumerateArray())
                        {
                            if (entry.ValueKind == JsonValueKind.Object && entry.TryGetProperty("name", out var n) && n.ValueKind == JsonValueKind.String && n.GetString() is { } text)
                            {
                                names.Add(text);
                            }
                        }
                    }
                    else
                    {
                        Collect(property.Value, names);
                    }
                }

                break;
            case JsonValueKind.Array:
                foreach (var child in element.EnumerateArray())
                {
                    Collect(child, names);
                }

                break;
        }
    }
}
