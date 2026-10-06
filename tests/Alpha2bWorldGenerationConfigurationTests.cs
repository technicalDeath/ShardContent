using BritanniaRenaissance.Content;
using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class Alpha2bWorldGenerationConfigurationTests
{
    private const string Commit = "ac1d0e2c8c6a7908773ae75bec0421f888bfc7a3";

    [Fact]
    public void AcceptsPinnedUorFeluccaManifest()
    {
        var manifest = ValidManifest();

        Alpha2bWorldGenerationConfiguration.Validate(manifest, Commit);
    }

    [Fact]
    public void RejectsDifferentModernUoCommit()
    {
        var manifest = ValidManifest() with { PinnedModernUoCommit = new string('a', 40) };

        var error = Assert.Throws<InvalidDataException>(
            () => Alpha2bWorldGenerationConfiguration.Validate(manifest, Commit)
        );

        Assert.Contains("different ModernUO commits", error.Message);
    }

    [Theory]
    [InlineData("AOS", "Felucca")]
    [InlineData("UOR", "Trammel")]
    public void RejectsWrongEraOrFacet(string era, string map)
    {
        var manifest = ValidManifest() with { Era = era, TargetMap = map };

        Assert.Throws<InvalidDataException>(
            () => Alpha2bWorldGenerationConfiguration.Validate(manifest, Commit)
        );
    }

    [Fact]
    public void RejectsGeneratedDataPathTraversal()
    {
        var manifest = ValidManifest() with { GeneratedDataRoot = "../Data" };

        Assert.Throws<InvalidDataException>(
            () => Alpha2bWorldGenerationConfiguration.Validate(manifest, Commit)
        );
    }

    [Fact]
    public void RejectsUnexpectedKhaldunDynamicItemCount()
    {
        var manifest = ValidManifest() with { ExpectedKhaldunDynamicItems = 62 };

        var error = Assert.Throws<InvalidDataException>(
            () => Alpha2bWorldGenerationConfiguration.Validate(manifest, Commit)
        );

        Assert.Contains("Khaldun expectation", error.Message);
    }

    [Fact]
    public void SourceManifestEnablesTheExactKhaldunContract()
    {
        var path = Path.GetFullPath(
            Path.Combine(
                AppContext.BaseDirectory,
                "..", "..", "..", "..", "data", "world-generation", "alpha2b", "world-generation.json"
            )
        );
        var manifest = JsonSerializer.Deserialize<Alpha2bWorldGenerationManifest>(
            File.ReadAllText(path),
            new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
        );

        Assert.NotNull(manifest);
        Assert.True(manifest.GenerateKhaldunPuzzles);
        Assert.Equal(63, manifest.ExpectedKhaldunDynamicItems);
        Assert.Equal(
            new Alpha2bRectangleBounds { XMin = 1280, YMin = 1400, XMax = 1750, YMax = 1900 },
            manifest.BritainBounds
        );
        Assert.Equal(["TownsPeople.json", "Vendors.json"], manifest.BritainOnlySpawnerFiles);
        Assert.Equal(2, manifest.DecorationRewrites.Length);
        Assert.Contains(
            manifest.DecorationRewrites,
            rewrite => rewrite.Source == "Britannia/_orccave.cfg" &&
                       rewrite.Match == "CampFire 0x0DE3" &&
                       rewrite.Replacement.StartsWith("Static 0x0DE3", StringComparison.Ordinal)
        );
        Assert.Equal(4, manifest.DecorationDuplicateCleanup.Length);
        Assert.True(manifest.DoorGeneration.Enabled);
        Assert.Equal(16, manifest.DoorGeneration.Regions.Length);
        Assert.Equal(4, manifest.DoorGeneration.Exclusions.Length);
        Assert.True(manifest.DoorGeneration.ExpectedPlacements > 0);
        Alpha2bWorldGenerationConfiguration.Validate(manifest, Commit);
    }

    [Fact]
    public void RejectsDecorationRewriteOutsideTheAllowlist()
    {
        var manifest = ValidManifest() with
        {
            DecorationRewrites =
            [
                new Alpha2bDecorationRewrite
                {
                    Source = "Felucca/not-allowed.cfg",
                    Match = "CampFire 0x0DE3",
                    Replacement = "Static 0x0DE3",
                    ExpectedMatches = 1,
                    Reason = "test"
                }
            ]
        };

        Assert.Throws<InvalidDataException>(
            () => Alpha2bWorldGenerationConfiguration.Validate(manifest, Commit)
        );
    }

    [Fact]
    public void RejectsUnsupportedDecorationDuplicateCleanup()
    {
        var manifest = ValidManifest() with
        {
            DecorationDuplicateCleanup =
            [
                new Alpha2bDecorationDuplicateCleanup
                {
                    Type = "Static", ItemId = 0x111B, X = 1, Y = 1, Z = 0, Keep = 1
                }
            ]
        };

        Assert.Throws<InvalidDataException>(
            () => Alpha2bWorldGenerationConfiguration.Validate(manifest, Commit)
        );
    }

    [Fact]
    public void RejectsBritainOnlySpawnerSourceOutsideTheAllowlist()
    {
        var manifest = ValidManifest() with { BritainOnlySpawnerFiles = ["TownsPeople.json"] };

        var error = Assert.Throws<InvalidDataException>(
            () => Alpha2bWorldGenerationConfiguration.Validate(manifest, Commit)
        );

        Assert.Contains("Britain-only spawner source", error.Message);
    }

    [Fact]
    public void RejectsChangedGreaterBritainBoundary()
    {
        var manifest = ValidManifest() with
        {
            BritainBounds = new Alpha2bRectangleBounds { XMin = 1281, YMin = 1400, XMax = 1750, YMax = 1900 }
        };

        var error = Assert.Throws<InvalidDataException>(
            () => Alpha2bWorldGenerationConfiguration.Validate(manifest, Commit)
        );

        Assert.Contains("Greater Britain boundary", error.Message);
    }

    private static Alpha2bWorldGenerationManifest ValidManifest() => new()
    {
        SchemaVersion = 2,
        PinnedModernUoCommit = Commit,
        Era = "UOR",
        TargetMap = "Felucca",
        GeneratedDataRoot = "Data/BritanniaRenaissance/Alpha2b",
        MaximumEraMapXExclusive = 6144,
        BritainBounds = new Alpha2bRectangleBounds { XMin = 1280, YMin = 1400, XMax = 1750, YMax = 1900 },
        DecorationsDirectory = "Decoration",
        SpawnersDirectory = "Spawns",
        SignsFile = "signs.cfg",
        TeleportersFile = "teleporters.json",
        DecorationFiles = ["Britannia/britain.cfg"],
        SpawnerFiles = ["Vendors.json"],
        BritainOnlySpawnerFiles = ["Vendors.json"],
        ExpectedPublicMoongates = 9,
        GenerateKhaldunPuzzles = true,
        ExpectedKhaldunDynamicItems = 63,
        DoorGeneration = ValidDoorGeneration()
    };

    private static Alpha2bDoorGeneration ValidDoorGeneration() => new()
    {
        Enabled = true,
        SourceFile = "Projects/UOContent/Misc/DoorGenerator.cs",
        ExpectedPlacements = 1,
        Regions = Enumerable.Range(0, 16).Select(
            index => new Alpha2bScanRectangle
            {
                XMin = index,
                YMin = index,
                XMaxExclusive = index + 1,
                YMaxExclusive = index + 1
            }
        ).ToArray(),
        Exclusions = Enumerable.Range(0, 4).Select(
            index => new Alpha2bDoorExclusion
            {
                XMin = index,
                YMin = index,
                XMax = index,
                YMax = index,
                Reason = "Pinned stock exclusion."
            }
        ).ToArray()
    };
}
