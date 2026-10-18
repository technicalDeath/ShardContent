using System.Text.Json.Serialization;
using Server;
using Server.Misc;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Fast skill starts (docs/Fast-Healing-Evidence.md): Healing behind <c>featureFlags.fastHealing</c>, Meditation behind
/// <c>featureFlags.fastMeditation</c> (the owner, 2026-10-17: Healing's bands, from any Meditation check, so mana comes back quicker early on).
/// Healing: The owner (2026-10-17), on bandages that barely help
/// without the skill: "Have healing skill gain go very fast until 40 skill to help make it effective faster", then "Below 20 it gains 5.0 to 10.0, and below 40
/// 1.0 to 5.0" (whole points: about ten bandages from 0 to 40). Every Healing check that would roll for a gain (a bandage applied to a patient who needs it) is instead a sure gain of
/// the band's amount, for every player alike. Above the last band stock gain and the shard's curve apply unchanged. The skill cap, the total cap and
/// skills set to go down behave as in stock <c>SkillCheck.Gain</c>, and a displaced point is published so the Skill Bank keeps it.
/// </summary>
public static class FastSkillStart
{
    /// <summary>The bands for a skill when its flag is on, or null when it has no fast start.</summary>
    public static FastSkillStartRules? RulesFor(SkillName skill)
    {
        var settings = ShardRulesConfiguration.Settings;

        return skill switch
        {
            SkillName.Healing when settings?.FeatureFlags.FastHealing == true => settings.FastHealing,
            SkillName.Meditation when settings?.FeatureFlags.FastMeditation == true => settings.FastMeditation,
            _ => null,
        };
    }

    /// <summary>The band for a base value in tenths, or null above every band.</summary>
    public static FastSkillStartBand? BandFor(FastSkillStartRules rules, int baseTenths)
    {
        FastSkillStartBand? found = null;

        foreach (var band in rules.Bands)
        {
            if (baseTenths < band.BelowTenths && (found is null || band.BelowTenths < found.BelowTenths))
            {
                found = band;
            }
        }

        return found;
    }

    /// <summary>
    /// Called from the shard's one gain-override handler, after Skill Bank restoration: true when this gain was handled here (the stock roll is
    /// skipped), false to leave it to stock.
    /// </summary>
    public static bool TryGain(PlayerMobile pm, Skill skill)
    {
        if (RulesFor(skill.SkillName) is not { } rules || BandFor(rules, skill.BaseFixedPoint) is not { } band)
        {
            return false;
        }

        if (skill.Lock == SkillLock.Up && skill.BaseFixedPoint < skill.CapFixedPoint)
        {
            Apply(pm, skill, Utility.RandomMinMax(band.MinTenths, band.MaxTenths));
        }

        return true;
    }

    // stock SkillCheck.Gain with a chosen amount: a skill set to go down may give way (as often as stock), and the total cap is never passed
    private static void Apply(PlayerMobile pm, Skill skill, int toGain)
    {
        var skills = pm.Skills;
        Skill? displaced = null;
        var displacedTenths = 0;

        if (skills.Total / (double)skills.Cap >= Utility.RandomDouble())
        {
            for (var i = 0; i < skills.Length; ++i)
            {
                var toLower = skills[i];

                if (toLower != skill && toLower.Lock == SkillLock.Down && toLower.BaseFixedPoint > 0)
                {
                    var before = toLower.BaseFixedPoint;
                    toLower.BaseFixedPoint = Math.Max(before - toGain, 0);
                    displacedTenths = before - toLower.BaseFixedPoint;
                    displaced = toLower;
                    break;
                }
            }
        }

        var room = Math.Min(skills.Cap - skills.Total, skill.CapFixedPoint - skill.BaseFixedPoint);

        if (room <= 0)
        {
            return;
        }

        skill.BaseFixedPoint += Math.Min(toGain, room);

        if (displaced is not null && displacedTenths > 0)
        {
            SkillEvents.InvokeSkillDisplaced(pm, displaced, displacedTenths);
        }
    }

    public static void Validate(string name, FastSkillStartRules rules, List<string> errors)
    {
        if (rules.Bands.Count == 0)
        {
            errors.Add($"{name}.bands must list at least one band.");
        }

        foreach (var band in rules.Bands)
        {
            if (band.BelowTenths is < 1 or > 1000 || band.MinTenths < 1 || band.MaxTenths < band.MinTenths || band.MaxTenths > 200)
            {
                errors.Add($"{name}.bands: each needs belowTenths 1-1000 and 1 <= minTenths <= maxTenths <= 200.");
            }
        }
    }
}

/// <summary>The bands for <see cref="FastSkillStart"/>, in tenths of a point.</summary>
public sealed class FastSkillStartRules
{
    [JsonPropertyName("bands")]
    public List<FastSkillStartBand> Bands { get; set; } =
    [
        new() { BelowTenths = 200, MinTenths = 50, MaxTenths = 100 },
        new() { BelowTenths = 400, MinTenths = 10, MaxTenths = 50 },
    ];
}

public sealed class FastSkillStartBand
{
    /// <summary>The band covers base values below this (in tenths) and at or above the next lower band's.</summary>
    [JsonPropertyName("belowTenths")]
    public int BelowTenths { get; set; }

    [JsonPropertyName("minTenths")]
    public int MinTenths { get; set; }

    [JsonPropertyName("maxTenths")]
    public int MaxTenths { get; set; }
}
