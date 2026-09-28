using System.Reflection;
using Server;
using Server.Items;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// Owner ruling (2026-09-28): starter-issued items use stock UOR newbied death behavior and the
/// starter bag is an ordinary stock Bag. No starter type may bring back a custom death rule.
/// </summary>
public class StarterDeathRuleTests
{
    private static readonly Assembly ShardAssembly = typeof(StarterBagIssuance).Assembly;

    private static List<Type> FindStarterTypes() =>
        ShardAssembly.GetTypes()
            .Where(type => !type.IsAbstract && typeof(Item).IsAssignableFrom(type) &&
                           (typeof(IStarterIssued).IsAssignableFrom(type) || type == typeof(BackpackWard)))
            .ToList();

    public static TheoryData<Type> StarterTypes()
    {
        var data = new TheoryData<Type>();
        foreach (var type in FindStarterTypes())
        {
            data.Add(type);
        }

        return data;
    }

    [Theory]
    [MemberData(nameof(StarterTypes))]
    public void StarterItemsUseStockDeathRouting(Type type)
    {
        foreach (var name in new[] { nameof(Item.OnInventoryDeath), nameof(Item.OnParentDeath) })
        {
            var method = type.GetMethod(name, [typeof(Mobile)]);
            Assert.NotNull(method);
            Assert.NotEqual(type, method.DeclaringType);
        }
    }

    [Fact]
    public void EveryStarterItemTypeIsCovered() =>
        Assert.Equal(27, FindStarterTypes().Count);

    [Fact]
    public void StarterBagIsAPlainStockBag() =>
        Assert.Null(ShardAssembly.GetType("BritanniaRenaissance.Content.StarterBag"));
}
