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
    [InlineData("use_old_status_gump", true)]     // the labeled STR/DEX/INT/HITS/MANA/STAM/GOLD/AR/WGHT status window, not the icon grid of resistances and bonuses that mean nothing in 2000
    [InlineData("always_run", true)]              // walking is running (client defaults item 7)
    [InlineData("always_run_unless_hidden", true)] // but not while hidden, which would give a sneaking player away
    [InlineData("auto_pickup_arrows", true)]      // the shard picks up the kinds a player's skills use; the switches are on the combat bar and in Options
    [InlineData("auto_pickup_bolts", true)]
    [InlineData("auto_pickup_reagents", true)]
    [InlineData("show_target_range_indicator", true)] // a target cursor shows how far away the target is, for bows and spells
    [InlineData("auto_open_doors", true)]         // walking into a door opens it
    [InlineData("combat_bar_enabled", true)]      // the combat bar under the potion bar (CombatBarGump)
    [InlineData("potion_bar_enabled", true)]      // the potion bar under the game window (PotionBarGump)
    [InlineData("auto_bandage", true)]            // the four auto-use switches (AutoUse) start on for a new profile (owner, 2026-10-13); they only act while the shard allows them
    [InlineData("auto_heal_potion", true)]
    [InlineData("auto_refresh_potion", true)]
    [InlineData("auto_cure", true)]
    [InlineData("show_d_p_s_with_damage_numbers", false)] // damage numbers without the "(DPS: n)" suffix, which is combat analytics and clutter for a new player
    [InlineData("enabled_spell_format", true)] // spoken spell words show the spell's name too, "In Por Ylem [Magic Arrow]" (monsterSpellWords makes creatures speak them)
    [InlineData("enabled_beneficial_criminal_action_query", true)] // "This may flag you criminal!" before a bandage or spell helps a grey, criminal or red player (stock ModernUO flags the helper)
    [InlineData("party_invite_gump", true)]       // an invitation to a party opens an Accept / Decline window, not only a chat line (camp travel needs a party)
    [InlineData("buff_bar_time", true)]           // a countdown on each buff icon
    [InlineData("cast_spells_by_one_click", true)] // spell, skill and macro buttons act on one click, as the spell bar does
    [InlineData("counter_bar_highlight_on_amount", true)] // an item shortcut turns red when it runs low
    [InlineData("hold_down_key_tab", false)]      // Tab switches war mode on and off instead of holding it
    [InlineData("show_info_bar", false)]          // the separate info bar is not offered: hits, mana and stamina are numbers on the player's own minimal health bar
    [InlineData("custom_bars_toggled", true)]     // health bars are the minimal bars (the player's own bar carries the numbers)
    [InlineData("hold_down_key_alt_to_close_anchored", false)]
    public void TheSwitchedDefaultsAreSpelledTheWayTheClientWritesThem(string key, bool expected)
    {
        Assert.True(Defaults().TryGetProperty(key, out var value), $"{key} is missing");
        Assert.Equal(expected, value.GetBoolean());
    }

    [Theory]
    [InlineData("mobile_h_p_type", 1)]            // 0 a percentage, 1 a bar, 2 both
    [InlineData("mobile_h_p_show_when", 0)]       // 0 always, 1 only below full health
    [InlineData("circle_of_transparency_type", 1)] // 0 the full circle, 1 the gradient (owner, 2026-10-14)
    [InlineData("corpse_open_options", 3)]        // 3 skips while a target cursor is up and while hidden
    [InlineData("close_health_bar_type", 2)]      // 2 closes the bar of a mobile that dies
    [InlineData("container_style", 1)]            // 0 the classic container window, 1 the shard grid of cells (ContainerGump.Grid.cs); a new profile gets the grid, an existing one keeps the classic look until Options > Containers is changed
    [InlineData("name_overhead_type_allowed", 510)] // names for every mobile and corpse, not for items on the ground (1 items, 2 corpses, 4 to 256 the mobile kinds)
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

    [Theory]
    [InlineData("500955", "Bandages need someone hurt")]
    [InlineData("500961", "makes the bandage heal less")]
    [InlineData("500968", "Healing skill decides")]
    public void TheClientTextExplainsTheBandageMessages(string id, string expected)
    {
        var lines = File.ReadAllLines(Path.Combine(ClientData, "Clilocs.txt")).Where(static l => l.Length > 0 && l[0] != '#').ToArray();
        var line = Assert.Single(lines, l => l.StartsWith(id + "\t", StringComparison.Ordinal));

        Assert.Contains(expected, line);
    }
}
