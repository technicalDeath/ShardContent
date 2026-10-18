using Server;
using Server.Engines.Craft;
using Server.Engines.Craft.T2A;
using Server.Misc;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Gain and make chances on the craft menus (docs/Craft-Chances-Evidence.md), behind <c>featureFlags.craftChances</c>. The owner (2026-10-17) asked for the
/// gain chance on the craft menu, with the make chance too, then: "this info would do better in the existing tooltip". After a craft menu page is sent
/// (<see cref="T2ACraftMenu.Sent"/>), extended command 0xAE follows with, for each entry that makes an item, the chance one attempt raises the player's
/// skill and the chance it succeeds; the client adds them to that entry's tooltip, under its name. Nothing changes how crafting works.
/// </summary>
public static class CraftChancesService
{
    public const int Command = 0xAE;

    /// <summary>The byte for an entry that is not an item (a category, repair, smelt).</summary>
    public const byte None = 255;

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.CraftChances == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        T2ACraftMenu.Sent += OnSent;
    }

    /// <summary>
    /// The chance one attempt raises the skill, as <c>SkillCheck.CheckSkill</c> rolls it for a craft's skill check (once per attempt, in
    /// <c>CraftItem.CompleteCraft</c>): none when the check is no challenge (always made) or out of reach, or the skill cannot rise; certain below 10;
    /// otherwise the stock gain chance on a success and on a failure, weighted by the check's chance, after the gain factor and the shard's curve.
    /// </summary>
    public static double GainChance(
        double value, double skillBase, double skillCap, int total, int totalCap, double min, double max, double gainFactor, double multiplier,
        bool canRise
    )
    {
        if (!canRise || max <= min)
        {
            return 0;
        }

        var chance = (value - min) / (max - min);

        if (chance < 0.0 || chance >= 1.0)
        {
            return 0;
        }

        if (skillBase < 10.0)
        {
            return 1.0;
        }

        double Roll(bool success)
        {
            var gc = (double)(totalCap - total) / totalCap;
            gc += (skillCap - skillBase) / skillCap;
            gc /= 2;
            gc += (1.0 - chance) * (success ? 0.5 : 0.2);
            gc /= 2;
            gc *= gainFactor * multiplier;
            return Math.Clamp(gc, 0.01, 1.0);
        }

        return chance * Roll(true) + (1.0 - chance) * Roll(false);
    }

    /// <summary>A chance as the byte the client shows: a gain is rounded up (a real chance never shows as 0), a make chance down.</summary>
    public static byte Percent(double chance, bool roundUp) =>
        (byte)Math.Clamp(roundUp ? Math.Ceiling(chance * 100.0) : Math.Floor(chance * 100.0), 0, 100);

    /// <summary>0xBF, the length, the command, the menu serial, the count, then a gain and a make byte per entry.</summary>
    public static byte[] Packet(int menuSerial, byte[] gains, byte[] makes)
    {
        var count = gains.Length;
        var length = 11 + 2 * count;
        var packet = new byte[length];
        packet[0] = 0xBF;
        packet[1] = (byte)(length >> 8);
        packet[2] = (byte)length;
        packet[3] = Command >> 8;
        packet[4] = Command & 0xFF;
        packet[5] = (byte)(menuSerial >> 24);
        packet[6] = (byte)(menuSerial >> 16);
        packet[7] = (byte)(menuSerial >> 8);
        packet[8] = (byte)menuSerial;
        packet[9] = (byte)(count >> 8);
        packet[10] = (byte)count;

        for (var i = 0; i < count; i++)
        {
            packet[11 + 2 * i] = gains[i];
            packet[12 + 2 * i] = makes[i];
        }

        return packet;
    }

    private static void OnSent(NetState state, T2ACraftMenu menu)
    {
        if (!Enabled || state.Mobile is not PlayerMobile player)
        {
            return;
        }

        var entries = menu.Entries;
        var gains = new byte[entries.Length];
        var makes = new byte[entries.Length];
        var any = false;

        for (var i = 0; i < entries.Length; i++)
        {
            gains[i] = makes[i] = None;

            if (menu.ItemFor(entries[i]) is not { } item)
            {
                continue;
            }

            any = true;
            var make = item.GetSuccessChance(player, menu.ResourceType, menu.System, false, out var allRequired);
            makes[i] = Percent(allRequired ? make : 0, false);
            gains[i] = Percent(Gain(player, item, menu.System), true);
        }

        if (any)
        {
            state.Send(Packet(menu.Serial, gains, makes));
        }
    }

    /// <summary>The chance one check of <paramref name="name"/> against the range raises it, for this player now (the spell tooltips use it too).</summary>
    public static double GainChanceFor(PlayerMobile player, SkillName name, double min, double max)
    {
        var skill = player.Skills[name];
        var skills = player.Skills;
        var room = skills.Total < skills.Cap || HasSkillGoingDown(skills);

        return GainChance(
            skill.Value, skill.Base, skill.Cap, skills.Total, skills.Cap, min, max, skill.Info.GainFactor,
            SkillEvents.InvokeGainChanceMultiplier(player, skill), skill.Lock == SkillLock.Up && skill.Base < skill.Cap && room
        );
    }

    private static double Gain(PlayerMobile player, CraftItem item, CraftSystem system)
    {
        CraftSkill? main = null;

        foreach (var craftSkill in item.Skills)
        {
            if (main is null || craftSkill.SkillToMake == system.MainSkill)
            {
                main = craftSkill;
            }
        }

        if (main is null)
        {
            return 0;
        }

        return GainChanceFor(player, main.SkillToMake, main.MinSkill, main.MaxSkill);
    }

    private static bool HasSkillGoingDown(Skills skills)
    {
        for (var i = 0; i < skills.Length; i++)
        {
            if (skills[i] is { Lock: SkillLock.Down, Base: > 0 })
            {
                return true;
            }
        }

        return false;
    }
}
