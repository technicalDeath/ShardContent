using BritanniaRenaissance.Content;
using Server.Engines.BuffIcons;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public sealed class BuffIconRulesTests
{
    private static readonly string DataRoot = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data");

    private static BuffIconRules Shipped() =>
        BuffIconRulesLoader.Parse(File.ReadAllText(Path.Combine(DataRoot, "configuration", "buff-icons.json")));

    private static BuffIconRules Minimal() => new()
    {
        SchemaVersion = 1,
        Stock = new() { ["Bless"] = new BuffText { Title = "Bless", Lines = ["+{buff.Str} Strength."] } }
    };

    // ---- the shipped data

    [Fact]
    public void TheShippedFileParsesAndValidates() => Assert.Empty(BuffIconRulesLoader.Validate(Shipped()));

    [Fact]
    public void EveryStockIconTheEngineAddsInUorHasItsOwnText()
    {
        var stock = Shipped().Stock.Keys;

        foreach (var icon in new[]
                 {
                     "Clumsy", "FeebleMind", "Weaken", "Agility", "Cunning", "Strength", "Bless", "Curse",
                     "NightSight", "HidingAndOrStealth", "ActiveMeditation", "Invisibility", "Incognito", "Paralyze"
                 })
        {
            Assert.Contains(icon, stock);
        }
    }

    [Fact]
    public void LaterErasEffectsAreNotInTheTable()
    {
        // Their stock icons are AoS or later: the engine only adds them for those eras, and a listed one would show text this shard cannot back.
        var everything = Shipped();
        var listed = everything.Stock.Keys.Concat(everything.States.Values.Select(s => s.Icon)).ToHashSet();

        foreach (var icon in new[] { "MortalStrike", "EnemyOfOne", "DivineFury", "AnimalForm", "StoneForm", "Fly", "WraithForm", "MassCurse" })
        {
            Assert.DoesNotContain(icon, listed);
        }

        Assert.Equal("hide", everything.UnlistedStockIcons);
    }

    [Fact]
    public void NoTextClaimsAResistanceAndTheStatSpellsGiveFlatPointsNotPercent()
    {
        var rules = Shipped();
        var all = rules.Stock.Values.Cast<BuffText>().Concat(rules.States.Values);

        Assert.All(all, text => Assert.DoesNotContain("resist", string.Join(" ", text.Lines.Append(text.Title)), StringComparison.OrdinalIgnoreCase));

        foreach (var line in rules.Stock.Values.SelectMany(t => t.Lines).Where(l => l.Contains("{buff.") || l.Contains("{curse.")))
        {
            Assert.DoesNotContain('%', line);
        }
    }

    [Fact]
    public void TheTableAndTheCatalogOfStatesAgree()
    {
        var rules = Shipped();

        Assert.Equal(BuffIconCatalog.StateValueNames.Keys.OrderBy(k => k), rules.States.Keys.OrderBy(k => k));
        Assert.All(rules.States.Values, s => Assert.True(BuffIconRulesLoader.TryResolveIcon(rules, s.Icon, out _), s.Icon));
    }

    [Fact]
    public void CustomIconsComeAfterTheLastStockIcon()
    {
        var lastStock = Enum.GetValues<BuffIcon>().Max();

        Assert.True(BuffIconCatalog.FirstCustomIconId > (int)lastStock, "a custom id would collide with a stock icon");

        foreach (var custom in Shipped().CustomIcons)
        {
            Assert.True(BuffIconRulesLoader.TryResolveIcon(Shipped(), custom.Name, out var icon));
            Assert.Equal(BuffIconCatalog.FirstCustomIconId + custom.Slot, (int)icon);
        }
    }

    // ---- text

    [Fact]
    public void TheTitleAndEachLineGoOnTheirOwnLine()
    {
        var text = Shipped().Stock["Bless"];
        var rendered = BuffIconRulesLoader.Render(text, name => name switch { "buff.Str" => "11", "buff.Dex" => "11", "buff.Int" => "11", _ => null });

        Assert.Equal("Bless<br>+11 Strength.<br>+11 Dexterity.<br>+11 Intelligence.", rendered);
    }

    [Fact]
    public void ALineWithAValueTheEffectDoesNotHaveIsLeftOut()
    {
        var text = Shipped().Stock["Bless"];
        var rendered = BuffIconRulesLoader.Render(text, name => name == "buff.Str" ? "7" : null);

        Assert.Equal("Bless<br>+7 Strength.", rendered);
        Assert.Equal("Bless", BuffIconRulesLoader.Render(text, _ => null));
    }

    [Fact]
    public void CurseNamesTheThreeStatsItTookAndNothingElse()
    {
        var rendered = BuffIconRulesLoader.Render(Shipped().Stock["Curse"], name => name.StartsWith("curse.") ? "11" : null);

        Assert.Equal("Curse<br>-11 Strength.<br>-11 Dexterity.<br>-11 Intelligence.", rendered);
    }

    [Fact]
    public void ArchProtectionNamesTheArmorItGaveAndTheTimedStatesCountDown()
    {
        var rules = Shipped();

        Assert.Equal(
            "Arch Protection<br>Your armor rating is raised by 5.",
            BuffIconRulesLoader.Render(rules.States["archProtection"], name => name == "bonus" ? "5" : null)
        );

        // Each of these ends on a timer the spell now reports, so each shows a countdown.
        foreach (var state in new[] { "protection", "archProtection", "polymorph", "knockedOut", "wardPrimed", "wardActivated", "faintMemoriesLocked" })
        {
            Assert.True(rules.States[state].Countdown, state);
        }
    }

    [Fact]
    public void ProtectionStatesItsChanceAsAPercentage() =>
        Assert.Equal(
            "Protection<br>Each hit has a 75% chance of not interrupting your spell.",
            BuffIconRulesLoader.Render(Shipped().States["protection"], name => name == "chance" ? "75" : null)
        );

    [Fact]
    public void AWaitIsSaidInWholeHoursWhileLongAndInMinutesWhenShort()
    {
        Assert.Equal("24 hours", BuffStateProbes.Span(TimeSpan.FromHours(23.2)));
        Assert.Equal("2 hours", BuffStateProbes.Span(TimeSpan.FromMinutes(61)));
        Assert.Equal("45 minutes", BuffStateProbes.Span(TimeSpan.FromMinutes(44.2)));
        Assert.Equal("a minute", BuffStateProbes.Span(TimeSpan.FromSeconds(20)));
    }

    [Fact]
    public void ACountdownNeverExceedsWhatThePacketCanHold() =>
        Assert.True(BuffIconService.MaxCountdown < TimeSpan.FromSeconds(short.MaxValue));

    // ---- the stock rewrite

    [Fact]
    public void AStockIconInTheTableIsShownInTheGenericFormWithTheTablesText()
    {
        var rules = Shipped();
        var stock = new BuffInfo(BuffIcon.Bless, 1075847, 1075848, TimeSpan.FromSeconds(90), "11\t11\t11", retainThroughDeath: false);

        var shown = BuffIconService.Present(rules, stock, name => name.StartsWith("buff.") ? "11" : null)!;

        Assert.Equal(BuffIcon.Bless, shown.ID);
        Assert.Equal(BuffIconCatalog.GenericTitleCliloc, shown.TitleCliloc);
        Assert.Equal(0, shown.SecondaryCliloc);
        Assert.Equal(TimeSpan.FromSeconds(90), shown.Duration);
        Assert.Equal("Bless<br>+11 Strength.<br>+11 Dexterity.<br>+11 Intelligence.", shown.Args?.ToString());
    }

    [Fact]
    public void AStockIconTheTableDoesNotListIsHiddenUnlessTheTableSaysShow()
    {
        var rules = Shipped();
        var stock = new BuffInfo(BuffIcon.MortalStrike, 1075810);

        Assert.Null(BuffIconService.Present(rules, stock, _ => null));

        rules.UnlistedStockIcons = "show";
        Assert.Same(stock, BuffIconService.Present(rules, stock, _ => null));
    }

    [Fact]
    public void ABuffAlreadyInTheShardsFormGoesThroughAsItIs()
    {
        var own = new BuffInfo(BuffIcon.Protection, BuffIconCatalog.GenericTitleCliloc, 0, default, "Protection<br>x");

        Assert.Same(own, BuffIconService.Present(Shipped(), own, _ => null));
    }

    // ---- what the watch sends

    private static readonly DateTime Now = new(2026, 10, 7, 12, 0, 0, DateTimeKind.Utc);

    private static BuffIconService.BuffShown Shown(string text, DateTime? until = null) => new(text, until);

    [Fact]
    public void AStateThatStartsIsShownOnce()
    {
        var wanted = new Dictionary<BuffIcon, BuffIconService.BuffShown> { [BuffIcon.Poison] = Shown("Poisoned") };

        var first = BuffIconService.Diff(null, wanted);

        Assert.Equal([new BuffIconService.BuffChange(BuffIcon.Poison, Shown("Poisoned"))], first);
        Assert.Empty(BuffIconService.Diff(wanted, wanted));
    }

    [Fact]
    public void ATextThatChangesIsSentAgainAndAStateThatEndsIsTakenAway()
    {
        var shown = new Dictionary<BuffIcon, BuffIconService.BuffShown>
        {
            [BuffIcon.ReactiveArmor] = Shown("Reactive Armor<br>40 points left"),
            [BuffIcon.Poison] = Shown("Poisoned")
        };
        var wanted = new Dictionary<BuffIcon, BuffIconService.BuffShown> { [BuffIcon.ReactiveArmor] = Shown("Reactive Armor<br>31 points left") };

        var changes = BuffIconService.Diff(shown, wanted);

        Assert.Contains(new BuffIconService.BuffChange(BuffIcon.ReactiveArmor, Shown("Reactive Armor<br>31 points left")), changes);
        Assert.Contains(new BuffIconService.BuffChange(BuffIcon.Poison, null), changes);
        Assert.Equal(2, changes.Count);
    }

    [Fact]
    public void AnEndThatDriftsASecondOrTwoIsLeftAloneAndOneThatMovesALotIsSentAgain()
    {
        var shown = new Dictionary<BuffIcon, BuffIconService.BuffShown> { [BuffIcon.Knockout] = Shown("Knocked Out", Now.AddSeconds(90)) };

        Assert.Empty(BuffIconService.Diff(shown, new Dictionary<BuffIcon, BuffIconService.BuffShown> { [BuffIcon.Knockout] = Shown("Knocked Out", Now.AddSeconds(92)) }));
        Assert.Single(BuffIconService.Diff(shown, new Dictionary<BuffIcon, BuffIconService.BuffShown> { [BuffIcon.Knockout] = Shown("Knocked Out", Now.AddSeconds(30)) }));
        Assert.Single(BuffIconService.Diff(shown, new Dictionary<BuffIcon, BuffIconService.BuffShown> { [BuffIcon.Knockout] = Shown("Knocked Out") }));
    }

    // ---- validation

    private static IReadOnlyList<string> Errors(Action<BuffIconRules> change)
    {
        var rules = Minimal();
        change(rules);

        return BuffIconRulesLoader.Validate(rules);
    }

    [Fact]
    public void AMinimalValidFileHasNoErrors() => Assert.Empty(BuffIconRulesLoader.Validate(Minimal()));

    [Fact]
    public void TheValidatorNamesWhatIsWrong()
    {
        Assert.Contains(Errors(r => r.SchemaVersion = 2), e => e.Contains("schemaVersion"));
        Assert.Contains(Errors(r => r.UnlistedStockIcons = "maybe"), e => e.Contains("unlistedStockIcons"));
        Assert.Contains(Errors(r => r.Stock["NoSuchIcon"] = new BuffText { Title = "x" }), e => e.Contains("not a stock buff icon"));
        Assert.Contains(Errors(r => r.Stock["Bless"].Lines.Add("+{buff.Wis} Wisdom.")), e => e.Contains("buff.Wis"));
        Assert.Contains(Errors(r => r.Stock["Bless"].Lines.Add("a\tb")), e => e.Contains("tab"));
        Assert.Contains(Errors(r => r.Stock["Bless"].Lines.Add("<b>x</b>")), e => e.Contains("<"));
        Assert.Contains(Errors(r => r.Stock["Bless"].Lines.Add("open { brace")), e => e.Contains("brace"));
        Assert.Contains(Errors(r => r.Stock["Bless"].Title = ""), e => e.Contains("title"));
        Assert.Contains(Errors(r => r.Stock["Bless"].Lines.Add(new string('x', 121))), e => e.Contains("121"));
        Assert.Contains(Errors(r => r.States["wizardry"] = new BuffStateText { Icon = "Bless", Title = "x" }), e => e.Contains("not a state"));
        Assert.Contains(Errors(r => r.States["poison"] = new BuffStateText { Icon = "Nothing", Title = "x" }), e => e.Contains("neither a stock icon"));
        Assert.Contains(
            Errors(r => r.States["poison"] = new BuffStateText { Icon = "Poison", Title = "x", Lines = ["{points} left"] }),
            e => e.Contains("{points}")
        );
    }

    [Fact]
    public void TheValidatorChecksCustomIcons()
    {
        static BuffCustomIcon Icon(string name, int slot, int art) => new() { Name = name, Slot = slot, Art = art };

        Assert.Contains(Errors(r => r.CustomIcons.Add(Icon("Bless", 0, 50000))), e => e.Contains("already a stock icon"));
        Assert.Contains(Errors(r => r.CustomIcons.AddRange([Icon("A", 0, 50000), Icon("B", 0, 50001)])), e => e.Contains("slot 0 is used twice"));
        Assert.Contains(Errors(r => r.CustomIcons.AddRange([Icon("A", 0, 50000), Icon("B", 1, 50000)])), e => e.Contains("art 50000 is used twice"));
        Assert.Contains(Errors(r => r.CustomIcons.Add(Icon("A", 16, 50000))), e => e.Contains("slot"));
        Assert.Contains(Errors(r => r.CustomIcons.Add(Icon("A", 0, 100))), e => e.Contains("art"));
        Assert.Contains(Errors(r => r.CustomIcons.Add(Icon("A1", 0, 50000))), e => e.Contains("letters"));
    }
}
