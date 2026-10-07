using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class ShardBrandingTests
{
    private static readonly string SourceDirectory = Path.GetFullPath(
        Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "src", "BritanniaRenaissance.Content")
    );

    private const string OldName = "Britannia Renaissance";

    [Fact]
    public void TheShardIsCalledUORekindledWithItsTagline()
    {
        Assert.Equal("UO Rekindled", ShardBranding.Name);
        Assert.Equal("Felucca, without the griefing", ShardBranding.Tagline);
    }

    [Fact]
    public void PlayerFacingGreetingsUseTheNewName()
    {
        Assert.Contains("UO Rekindled", StarterOnboarding.CreationPrompt);

        var welcome = WelcomeGuide.Topics(new WelcomeGuide.Context(true, true, true, true, true), new CampTravelRules())
            .Single(t => t.Key == "welcome");

        // The window's header already shows the name and the tagline, so the first page greets without repeating the tagline.
        Assert.Contains("Welcome to UO Rekindled.", welcome.Paragraphs[0]);
        Assert.DoesNotContain(ShardBranding.Tagline, welcome.Paragraphs[0]);
    }

    [Fact]
    public void NoSourceFileStillCallsTheShardByItsOldName()
    {
        // Identifiers keep the old spelling (BritanniaRenaissance.Content, tag keys) and contain no space, so a space-separated
        // old name in code, comments or messages is a rename that was missed.
        var offenders = Directory.EnumerateFiles(SourceDirectory, "*.cs", SearchOption.TopDirectoryOnly)
            .Where(file => Path.GetFileName(file) != "ShardBranding.cs") // it records the old name on purpose
            .Where(file => File.ReadAllText(file).Contains(OldName, StringComparison.Ordinal))
            .Select(Path.GetFileName)
            .ToList();

        Assert.Empty(offenders);
    }

    [Fact]
    public void TheShippedServerNameDocumentationAgreesWithTheBranding()
    {
        // The server list name lives in the untracked runtime config (Configuration/modernuo.json, serverListing.serverName);
        // the rename note records the value so a fresh distribution gets it right.
        var note = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "docs", "Shard-Name-UO-Rekindled.md");

        Assert.True(File.Exists(note), "docs/Shard-Name-UO-Rekindled.md records the rename and the server-list setting");
        Assert.Contains($"\"serverListing.serverName\": \"{ShardBranding.Name}\"", File.ReadAllText(note));
    }
}
