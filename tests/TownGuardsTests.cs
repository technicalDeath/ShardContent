using System.Text.Json;
using Server.Mobiles;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>Town guards kill monsters, and the guard zones shrink where no vendor stands (docs/Town-Guards-Monsters-Evidence.md).</summary>
public class TownGuardsTests
{
    private static readonly string Data = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data");

    private static readonly string Spawns = Path.Combine(
        AppContext.BaseDirectory, "..", "..", "..", "..", "..", "ModernUO", "Distribution", "Data", "BritanniaRenaissance", "Alpha2b", "Spawns"
    );

    private static ShardRules Shipped() =>
        JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(Path.Combine(Data, "configuration", "shard-rules.json")))!;

    private static bool Target(
        bool enabled = true, bool alive = true, bool pet = false, bool invulnerable = false, bool townsperson = false,
        FightMode mode = FightMode.Closest, bool guarded = true
    ) => TownGuardsService.ShouldTarget(enabled, alive, pet, invulnerable, townsperson, mode, guarded);

    [Fact]
    public void AWildMonsterThatAttacksOnSightIsATargetWhereGuardsWork() => Assert.True(Target());

    [Theory]
    [InlineData(FightMode.Closest, true)]
    [InlineData(FightMode.Strongest, true)]
    [InlineData(FightMode.Weakest, true)]
    [InlineData(FightMode.Aggressor, false)] // town animals, bears, vendors' guards, hirelings, escorts: they only fight back
    [InlineData(FightMode.Evil, false)]
    [InlineData(FightMode.None, false)]
    public void OnlyCreaturesThatAttackOnSightCount(FightMode mode, bool counts) => Assert.Equal(counts, Target(mode: mode));

    [Fact]
    public void NothingIsATargetWhileTheFlagIsOff() => Assert.False(Target(enabled: false));

    [Fact]
    public void PetsSummonsTownspeopleTheDeadAndTheInvulnerableAreLeftAlone()
    {
        Assert.False(Target(pet: true));
        Assert.False(Target(townsperson: true));
        Assert.False(Target(alive: false));
        Assert.False(Target(invulnerable: true));
    }

    [Fact]
    public void AMonsterOutsideTheGuardZoneIsLeftAlone() => Assert.False(Target(guarded: false));

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().TownGuardsKillMonsters);

    [Fact]
    public void TheShippedRulesValidate()
    {
        var errors = new List<string>();
        TownGuardsService.Validate(Shipped().TownGuards, errors);

        Assert.Empty(errors);
        Assert.Contains(Shipped().TownGuards.UnguardedAreas, a => a.Name == "Britain Outskirts");
        Assert.Contains(Shipped().TownGuards.UnguardedAreas, a => a.Name == "Moonglow Zoo");
    }

    [Fact]
    public void BadAreasAreRefused()
    {
        var errors = new List<string>();
        TownGuardsService.Validate(
            new TownGuardRules
            {
                UnguardedAreas =
                [
                    new UnguardedArea { Name = "A", Map = "Trammel", Rectangles = [new UnguardedRectangle { X1 = 10, Y1 = 10, X2 = 5, Y2 = 20 }] },
                    new UnguardedArea { Name = "a", Map = "Felucca" }
                ]
            },
            errors
        );

        Assert.Equal(4, errors.Count);
    }

    [Fact]
    public void TheGuardZoneShrinksOnlyWhereNoVendorOrTownspersonStands()
    {
        // the owner, 2026-10-16: "Shrink the guard zone only where there are no vendors."
        var people = new[] { Path.Combine(Spawns, "Vendors.json"), Path.Combine(Spawns, "TownsPeople.json"), Path.Combine(Data, "world-generation", "alpha2b", "britain-vendor-overrides.json") };
        var areas = Shipped().TownGuards.UnguardedAreas;

        foreach (var file in people)
        {
            Assert.True(File.Exists(file), file);

            foreach (var spawner in JsonDocument.Parse(File.ReadAllText(file)).RootElement.EnumerateArray())
            {
                if (spawner.GetProperty("map").GetString() != "Felucca")
                {
                    continue;
                }

                var at = spawner.GetProperty("location").EnumerateArray().Select(v => v.GetInt32()).ToArray();
                var range = spawner.TryGetProperty("homeRange", out var r) ? r.GetInt32() : 0;

                foreach (var area in areas)
                {
                    Assert.DoesNotContain(
                        area.Rectangles,
                        rect => Overlaps(rect, at[0] - range, at[1] - range, at[0] + range + 1, at[1] + range + 1)
                    );
                }
            }
        }
    }

    [Fact]
    public void EveryBeginnerSpawnerSpawnsOnlyOnUnguardedGround()
    {
        // the owner, 2026-10-16: "Monsters should not spawn inside" a guard zone; each spawner's whole home square is in Britain Outskirts
        var outskirts = Shipped().TownGuards.UnguardedAreas.Single(a => a.Name == "Britain Outskirts").Rectangles;
        var spawners = JsonDocument.Parse(File.ReadAllText(Path.Combine(Data, "world-generation", "alpha2b", "britain-beginner-hunting.json"))).RootElement;

        foreach (var s in spawners.EnumerateArray())
        {
            var at = s.GetProperty("location").EnumerateArray().Select(v => v.GetInt32()).ToArray();
            var range = s.GetProperty("homeRange").GetInt32();

            for (var x = at[0] - range; x <= at[0] + range; x++)
            {
                for (var y = at[1] - range; y <= at[1] + range; y++)
                {
                    Assert.True(outskirts.Any(rect => rect.Contains(x, y)), $"{s.GetProperty("name").GetString()} can spawn at {x},{y}, inside the guard zone");
                }
            }
        }
    }

    [Fact]
    public void TheFirstHourPageSaysWhatTheGuardsDo()
    {
        var off = FirstHour(new WelcomeGuide.Context(false, false, false, false, false));
        var on = FirstHour(new WelcomeGuide.Context(false, false, false, false, false, TownGuardsKillMonsters: true));

        Assert.Contains("If a monster follows you into town and attacks you, shout guards and the guards will kill it; if you struck it first, they will not help", off);
        Assert.Contains("If a monster follows you into a guarded town, shout guards and the guards will kill it, even if you struck it first", on);
        Assert.Contains("Britain's woods and fields west of the castle, and south of the south-west houses, are not guarded.", on);
        Assert.DoesNotContain("is not stopped by the guards", off + on);
    }

    private static string FirstHour(WelcomeGuide.Context c) =>
        string.Join(" ", WelcomeGuide.Topics(c, new CampTravelRules(), camping: new CampingRules()).Single(t => t.Key == "firsthour").Paragraphs);

    private static bool Overlaps(UnguardedRectangle r, int x1, int y1, int x2, int y2) => r.X1 < x2 && x1 < r.X2 && r.Y1 < y2 && y1 < r.Y2;
}
