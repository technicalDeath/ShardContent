using BritanniaRenaissance.Content;
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
        ExpectedPublicMoongates = 9
    };
}
