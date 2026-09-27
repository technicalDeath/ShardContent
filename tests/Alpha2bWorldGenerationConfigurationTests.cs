using BritanniaRenaissance.Content;
using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class Alpha2bWorldGenerationConfigurationTests
{
    private const string Commit = "9fb5448445c0a53ebb77a4ad9d72e9ec06ce8f3d";

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
        Assert.Equal(2, manifest.DecorationRewrites.Length);
        Assert.Contains(
            manifest.DecorationRewrites,
            rewrite => rewrite.Source == "Britannia/_orccave.cfg" &&
                       rewrite.Match == "CampFire 0x0DE3" &&
                       rewrite.Replacement.StartsWith("Static 0x0DE3", StringComparison.Ordinal)
        );
        Assert.Equal(4, manifest.DecorationDuplicateCleanup.Length);
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

    private static Alpha2bWorldGenerationManifest ValidManifest() => new()
    {
        SchemaVersion = 1,
        PinnedModernUoCommit = Commit,
        Era = "UOR",
        TargetMap = "Felucca",
        GeneratedDataRoot = "Data/BritanniaRenaissance/Alpha2b",
        MaximumEraMapXExclusive = 6144,
        DecorationsDirectory = "Decoration",
        SpawnersDirectory = "Spawns",
        SignsFile = "signs.cfg",
        TeleportersFile = "teleporters.json",
        DecorationFiles = ["Britannia/britain.cfg"],
        SpawnerFiles = ["Vendors.json"],
        ExpectedPublicMoongates = 9,
        GenerateKhaldunPuzzles = true,
        ExpectedKhaldunDynamicItems = 63
    };
}
