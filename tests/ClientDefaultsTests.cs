using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The player client's defaults for a new profile (docs/Client-Defaults.md): data/client/default-profile.json is read by ClassicUO as a Profile with
/// snake_case names, where an acronym is split letter by letter (<c>show_mobiles_h_p</c>, not <c>show_mobiles_hp</c>); a misspelt key is silently
/// ignored by the client, so the names are pinned here. Also the shard's own client text.
/// </summary>
public class ClientDefaultsTests
{
    private static readonly string ClientData = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "client");

    private static JsonElement Defaults() => JsonDocument.Parse(File.ReadAllText(Path.Combine(ClientData, "default-profile.json"))).RootElement;

    [Theory]
    [InlineData("show_mobiles_h_p", true)]
    [InlineData("use_circle_of_transparency", true)]
    [InlineData("auto_open_corpses", true)]
    [InlineData("counter_bar_enabled", true)]     // the blank hotbar (CounterBarGump), opened once by GameScene.OfferBlankHotbar
    [InlineData("always_run", true)]              // walking is running (client defaults item 7)
    [InlineData("always_run_unless_hidden", true)] // but not while hidden, which would give a sneaking player away
    [InlineData("auto_open_doors", true)]         // walking into a door opens it
    [InlineData("combat_bar_enabled", true)]      // the combat bar under the potion bar (CombatBarGump)
    [InlineData("potion_bar_enabled", true)]      // the potion bar under the game window (PotionBarGump)
    [InlineData("hold_down_key_alt_to_close_anchored", false)]
    public void TheSwitchedDefaultsAreSpelledTheWayTheClientWritesThem(string key, bool expected)
    {
        Assert.True(Defaults().TryGetProperty(key, out var value), $"{key} is missing");
        Assert.Equal(expected, value.GetBoolean());
    }

    [Theory]
    [InlineData("mobile_h_p_type", 1)]            // 0 a percentage, 1 a bar, 2 both
    [InlineData("mobile_h_p_show_when", 0)]       // 0 always, 1 only below full health
    [InlineData("circle_of_transparency_type", 0)] // 0 the normal circle, 1 like the original client
    [InlineData("corpse_open_options", 3)]        // 3 skips while a target cursor is up and while hidden
    [InlineData("close_health_bar_type", 2)]      // 2 closes the bar of a mobile that dies
    public void TheNumberedDefaultsAreTheOwnersChoices(string key, int expected)
    {
        Assert.True(Defaults().TryGetProperty(key, out var value), $"{key} is missing");
        Assert.Equal(expected, value.GetInt32());
    }

    [Fact]
    public void TheWindowSizeDefaultIsStillThere() =>
        Assert.Equal(0.7, Defaults().GetProperty("game_window_start_fraction").GetDouble());

    [Fact]
    public void TheClientTextSaysHowToLogOffSafelyAtASecureCamp()
    {
        var lines = File.ReadAllLines(Path.Combine(ClientData, "Clilocs.txt")).Where(static l => l.Length > 0 && l[0] != '#').ToArray();
        var line = Assert.Single(lines, static l => l.StartsWith("500621\t", StringComparison.Ordinal));

        Assert.Contains("The camp is now secure.", line);
        Assert.Contains("log off safely", line);
        Assert.Contains("Bedroll", line);
        Assert.DoesNotContain("Britannia Renaissance", line, StringComparison.OrdinalIgnoreCase);
    }
}
