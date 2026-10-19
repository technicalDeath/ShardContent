using BritanniaRenaissance.Content;
using Server;
using Server.Items;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>Item hover tooltips (docs/Item-Tooltips-Evidence.md): what the shard lets a tooltip say, which items have one, and how the client is told to draw it.</summary>
public class ItemTooltipTests
{
    private static string Describe(IEnumerable<ItemTooltipService.Line> lines) => string.Join(" | ", lines.Select(l => l.Number == 0 ? l.Argument : $"{l.Number}:{l.Argument}"));

    // ---- the flag and the mask

    [Fact]
    public void AToolSaysWhatItIsFor()
    {
        Assert.Contains("not ammunition", ItemTooltipService.ToolLine(true));
        Assert.Contains("make arrows", ItemTooltipService.ToolLine(true));
        Assert.Contains("crafting menu", ItemTooltipService.ToolLine(false));
        Assert.DoesNotContain("uses", ItemTooltipService.ToolLine(false), StringComparison.OrdinalIgnoreCase);   // wear is never on a tooltip
    }

    [Fact]
    public void TheFlagIsOffUntilTheOwnerActivatesItAndOnInTheShippedRules()
    {
        Assert.False(new DeferredFeatureFlags().ItemTooltips);

        var rules = System.Text.Json.JsonSerializer.Deserialize<ShardRules>(
            File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"))
        )!;

        Assert.True(rules.FeatureFlags.ItemTooltips);   // activated 2026-10-13 on the owner's "Item and weapon tooltips should be turned on"
        Assert.Contains(nameof(DeferredFeatureFlags.ItemTooltips), rules.FeatureFlags.EnabledNames());
    }

    [Fact]
    public void TheMaskCarriesTheTooltipBitWithOrWithoutTheShardBar()
    {
        Assert.Equal(0, MenuBarService.MaskFor(new DeferredFeatureFlags()));
        Assert.Equal(MenuBarService.Tooltips, MenuBarService.MaskFor(new DeferredFeatureFlags { ItemTooltips = true }));

        var both = MenuBarService.MaskFor(new DeferredFeatureFlags { ItemTooltips = true, MenuBar = true });

        Assert.Equal(MenuBarService.Tooltips | MenuBarService.ShardBar | MenuBarService.About, both);
        Assert.Equal(0, MenuBarService.MaskFor(new DeferredFeatureFlags { MenuBar = true }) & MenuBarService.Tooltips);
    }

    // ---- which items have one

    [Theory]
    [InlineData(true, false, false, false, true)]    // something a player could pick up
    [InlineData(false, true, false, false, true)]    // locked down in a house
    [InlineData(false, false, true, false, true)]    // secure
    [InlineData(false, false, false, true, true)]    // in a bag, worn, or on a corpse
    [InlineData(false, false, false, false, false)]  // a door, a sign, a corpse, scenery
    public void OnlyItemsAPlayerCouldHandleHaveATooltip(bool movable, bool lockedDown, bool secure, bool hasParent, bool expected) =>
        Assert.Equal(expected, ItemTooltipService.ShowsTooltip(movable, lockedDown, secure, hasParent));

    // ---- what a weapon says

    [Fact]
    public void AKatanaSaysItsKindsNumbersInTheStockTexts()
    {
        // Katana: 5-26, speed 58, Strength 10, one-handed, Swordsmanship (the numbers the About page used to list)
        Assert.Equal(
            "1061168:5\t26 | 1061167:58 | 1061170:10 | 1061824: | 1061172:",
            Describe(ItemTooltipService.WeaponLines(5, 26, 58f, 1, 10, false, SkillName.Swords))
        );
    }

    [Fact]
    public void ABowAlsoSaysItsRangeAndThatItNeedsBothHands() =>
        Assert.Equal(
            "1061168:9\t41 | 1061167:20 | 1061169:10 | 1061170:20 | 1061171: | 1061175:",
            Describe(ItemTooltipService.WeaponLines(9, 41, 20f, 10, 20, true, SkillName.Archery))
        );

    [Fact]
    public void AWeaponThatNeedsNoStrengthLeavesThatLineOut() =>
        Assert.DoesNotContain("1061170", Describe(ItemTooltipService.WeaponLines(1, 8, 30f, 1, 0, false, SkillName.Wrestling)));

    [Theory]
    [InlineData(SkillName.Swords, 1061172)]
    [InlineData(SkillName.Macing, 1061173)]
    [InlineData(SkillName.Fencing, 1061174)]
    [InlineData(SkillName.Archery, 1061175)]
    public void TheSkillIsNamedForTheFourCombatSkills(SkillName skill, int number) => Assert.Equal(number, ItemTooltipService.SkillText(skill));

    [Fact]
    public void ASkillThatIsNoCombatSkillHasNoSkillLine() => Assert.Null(ItemTooltipService.SkillText(SkillName.Wrestling));

    // ---- what armor says, and the loot type

    [Theory]
    [InlineData(false, false, false)]   // ordinary: maker and quality show
    [InlineData(false, true, false)]
    [InlineData(true, true, false)]     // magic that Item Identification has revealed
    [InlineData(true, false, true)]     // unidentified magic: the single-click label says only "unidentified"
    public void AnUnidentifiedMagicItemHidesItsMakerAndQualityJustAsItsSingleClickLabelDoes(bool magical, bool identified, bool hidden) =>
        Assert.Equal(hidden, ItemTooltipService.HidesMaker(magical, identified));

    [Fact]
    public void AnIdentifiedWeaponListsWhatItemIdentificationFound()
    {
        Assert.Equal(
            "Indestructible | Supremely accurate | Of vanquishing",
            Describe(ItemTooltipService.WeaponMagicLines(WeaponDurabilityLevel.Indestructible, WeaponAccuracyLevel.Supremely, WeaponDamageLevel.Vanq))
        );

        Assert.Equal("Durable", Describe(ItemTooltipService.WeaponMagicLines(WeaponDurabilityLevel.Durable, WeaponAccuracyLevel.Regular, WeaponDamageLevel.Regular)));
        Assert.Equal("Of might", Describe(ItemTooltipService.WeaponMagicLines(WeaponDurabilityLevel.Regular, WeaponAccuracyLevel.Regular, WeaponDamageLevel.Might)));
        Assert.Empty(ItemTooltipService.WeaponMagicLines(WeaponDurabilityLevel.Regular, WeaponAccuracyLevel.Regular, WeaponDamageLevel.Regular));
    }

    [Theory]
    [InlineData(WeaponAccuracyLevel.Accurate, "Accurate")]
    [InlineData(WeaponAccuracyLevel.Surpassingly, "Surpassingly accurate")]
    [InlineData(WeaponAccuracyLevel.Eminently, "Eminently accurate")]
    [InlineData(WeaponAccuracyLevel.Exceedingly, "Exceedingly accurate")]
    public void EveryAccuracyLevelHasItsOwnWords(WeaponAccuracyLevel level, string expected) =>
        Assert.Equal(expected, Describe(ItemTooltipService.WeaponMagicLines(WeaponDurabilityLevel.Regular, level, WeaponDamageLevel.Regular)));

    [Fact]
    public void IdentifiedArmorListsItsDurabilityAndProtectionLevels()
    {
        Assert.Equal("Indestructible | Of invulnerability", Describe(ItemTooltipService.ArmorMagicLines(ArmorDurabilityLevel.Indestructible, ArmorProtectionLevel.Invulnerability)));
        Assert.Equal("Of defense", Describe(ItemTooltipService.ArmorMagicLines(ArmorDurabilityLevel.Regular, ArmorProtectionLevel.Defense)));
        Assert.Empty(ItemTooltipService.ArmorMagicLines(ArmorDurabilityLevel.Regular, ArmorProtectionLevel.Regular));
    }

    [Fact]
    public void AnIdentifiedWandListsItsEffectAndItsCharges()
    {
        Assert.Equal("Of fireball | 7 charges", Describe(ItemTooltipService.WandLines(WandEffect.Fireball, 7)));
        Assert.Equal("Of greater healing | 1 charge", Describe(ItemTooltipService.WandLines(WandEffect.GreaterHealing, 1)));
    }

    [Fact]
    public void ArmorSaysItsKindsRatingAndStrengthOnly() =>
        Assert.Equal("armor rating 40 | 1061170:60", Describe(ItemTooltipService.ArmorLines(40, 60)));

    [Fact]
    public void ArmorThatNeedsNoStrengthSaysOnlyItsRating() => Assert.Equal("armor rating 2", Describe(ItemTooltipService.ArmorLines(2, 0)));

    [Fact]
    public void NewbiedItemsSayTheyAreKeptWhenYouDieAndBlessedOnesSayBlessed()
    {
        Assert.Equal(ItemTooltipService.NewbiedText, Describe(ItemTooltipService.LootLines(LootType.Newbied)));
        Assert.Equal("1038021:", Describe(ItemTooltipService.LootLines(LootType.Blessed)));
        Assert.Empty(ItemTooltipService.LootLines(LootType.Regular));
        Assert.Empty(ItemTooltipService.LootLines(LootType.Cursed));
    }

    [Theory]
    [InlineData(1, "Stamina from eating: 6-8")]
    [InlineData(5, "Stamina from eating: 7-9")]
    [InlineData(20, "Stamina from eating: 10-12")]
    public void FoodSaysHowMuchStaminaItGives(int fill, string line) => Assert.Equal(line, ItemTooltipService.FoodLine(fill));
}
