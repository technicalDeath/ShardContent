using BritanniaRenaissance.Content;
using System;
using System.IO;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class MenuBarTests
{
    [Fact]
    public void FlagOffSendsNothing() => Assert.Equal(0, MenuBarService.MaskFor(new DeferredFeatureFlags { GuildChat = true }));

    [Fact]
    public void ShardBarAloneShowsOnlyTheAlwaysButtons() =>
        Assert.Equal(MenuBarService.ShardBar | MenuBarService.About, MenuBarService.MaskFor(new DeferredFeatureFlags { MenuBar = true }));

    [Fact]
    public void EachFeatureAddsItsOwnBit()
    {
        Assert.Equal(MenuBarService.ShardBar | MenuBarService.About, MenuBarService.MaskFor(new DeferredFeatureFlags { MenuBar = true, SkillBank = true }));   // no Skill Bank button
        Assert.Equal(MenuBarService.ShardBar | MenuBarService.About | MenuBarService.Camp, MenuBarService.MaskFor(new DeferredFeatureFlags { MenuBar = true, CampingTravel = true }));
        Assert.Equal(MenuBarService.ShardBar | MenuBarService.About | MenuBarService.GuildChat, MenuBarService.MaskFor(new DeferredFeatureFlags { MenuBar = true, GuildChat = true }));
        // About opens the Welcome guide, which is not behind a flag, so the skill guide flag changes nothing here
        Assert.Equal(MenuBarService.ShardBar | MenuBarService.About, MenuBarService.MaskFor(new DeferredFeatureFlags { MenuBar = true, HelpGumps = true }));
    }

    [Fact]
    public void PacketBytes()
    {
        var packet = MenuBarService.Packet(MenuBarService.ShardBar | MenuBarService.GuildChat);

        Assert.Equal(new byte[] { 0xBF, 0, 7, 0, 0xA8, 0x80, 0x04 }, packet);
    }

    [Fact]
    public void TheBarIsOnInTheShippedRulesSinceTheOwnerActivatedIt()
    {
        var rules = System.Text.Json.JsonSerializer.Deserialize<ShardRules>(
            File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"))
        )!;

        Assert.True(rules.FeatureFlags.MenuBar);   // activated 2026-10-12 on the owner's explicit "Activate"
    }
}
