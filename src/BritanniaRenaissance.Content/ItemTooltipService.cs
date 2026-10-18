using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Hover tooltips on items (docs/Item-Tooltips-Evidence.md), behind <c>featureFlags.itemTooltips</c>. A deliberate departure from the era: property lists arrived with Age of Shadows.
/// <para>
/// ModernUO's stock lists must not reach a player: the 136 <c>GetProperties</c> overrides print exact magical damage, resist and durability bonuses, slayers, poison and charges that
/// Item Identification, Arms Lore and Taste Identification exist to tell. So the shard does not filter them, it replaces them: <see cref="Item.PropertyListBuilder"/> hands every item's
/// list to <see cref="Build"/>, which writes only what is below. What it says is a fact of the item's <i>kind</i> (a Katana's damage, a plate chest's armor rating, a bag's weight), never of
/// the one in the hand, with one exception: once Item Identification has been used on a magic weapon, armor or wand, its tooltip lists what that skill found (the levels, a wand's effect and charges), as its single-click label does. Until then, and always for how worn it is, a tooltip says nothing about the one in the hand. A shop's display copy gets the same tooltip as any item: what a buyer receives is a separate new item, so its durability is not quoted.
/// </para>
/// <list type="bullet">
/// <item>Every item that can be moved, is locked down or is in something: its name (the stock name line, with the amount), who made it and whether it is exceptional (both already on the
/// single-click label), newbied or blessed, and its weight (a pile or a bag's contents included).</item>
/// <item>A weapon (not a wand): damage, speed, range if it shoots, Strength needed, one or two hands and the skill it uses.</item>
/// <item>Armor and shields: the armor rating of the kind and the Strength needed.</item>
/// <item>Identified magic: the levels Item Identification found (weapons, armor), and a wand's effect and charges. Slayers are not listed.</item>
/// </list>
/// Doors, signs, corpses and the like get nothing. The server turns the stock property switch on once it has started; the client draws item tooltips only (not mobiles) because the mask
/// the server sends at login says so (<see cref="MenuBarService.Tooltips"/>), and keeps its single-click name labels.
/// </summary>
public static class ItemTooltipService
{
    private const int PlainText = 0;
    private const int CraftedBy = 1050043;
    private const int Exceptional = 1060636;
    private const int Blessed = 1038021;
    private const int Damage = 1061168;
    private const int Speed = 1061167;
    private const int Range = 1061169;
    private const int StrengthRequirement = 1061170;
    private const int TwoHanded = 1061171;
    private const int OneHanded = 1061824;

    /// <summary>The line the newbied starter items carry.</summary>
    public const string NewbiedText = "newbied: kept when you die";

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.ItemTooltips == true;

    /// <summary>One line of a tooltip: a client text number with its argument, or (number 0) plain text.</summary>
    public readonly record struct Line(int Number, string? Argument = null)
    {
        public static Line Text(string text) => new(0, text);
    }

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        Item.PropertyListBuilder = Build;

        // ExpansionConfiguration sets the stock value while the server configures (off for a pre-AoS era); the shard's word comes after it
        EventSink.ServerStarted += ApplySetting;
    }

    private static void ApplySetting()
    {
        if (Enabled)
        {
            ObjectPropertyList.Enabled = true;
        }
    }

    /// <summary>Writes the item's tooltip and says so (the stock list is then not built), or says it did not, when the flag is off.</summary>
    private static bool Build(Item item, ObjectPropertyList list)
    {
        if (!Enabled)
        {
            return false;
        }

        if (!ShowsTooltip(item.Movable, item.IsLockedDown, item.IsSecure, item.Parent is not null))
        {
            return true;
        }

        if (IsUnidentifiedMagic(item))
        {
            // the stock name line of armor and weapons says "exceptional" and the metal; the single-click label of such an item says only "unidentified"
            if (item.Name is { Length: > 0 } plain)
            {
                list.Add(plain);
            }
            else
            {
                list.Add(item.LabelNumber);
            }
        }
        else
        {
            item.AddNameProperty(list);
        }

        foreach (var line in Lines(item))
        {
            Write(list, line);
        }

        item.AddWeightProperty(list);

        return true;
    }

    private static void Write(ObjectPropertyList list, Line line)
    {
        if (line.Number == PlainText)
        {
            list.Add(line.Argument ?? "");
        }
        else if (string.IsNullOrEmpty(line.Argument))
        {
            list.Add(line.Number);
        }
        else
        {
            list.Add(line.Number, line.Argument);
        }
    }

    /// <summary>Doors, signs, corpses and scenery say nothing: an item has a tooltip when a player could pick it up, it is locked down in a house, or it is inside something or worn.</summary>
    public static bool ShowsTooltip(bool movable, bool lockedDown, bool secure, bool hasParent) => movable || lockedDown || secure || hasParent;

    /// <summary>The lines between the name and the weight: what the maker, the loot type and the kind of item add.</summary>
    private static IEnumerable<Line> Lines(Item item)
    {
        switch (item)
        {
            case BaseWand wand:
                {
                    // a wand is a weapon only by its class: its numbers are not the point. Its effect and charges are what Item Identification tells, so they show only once it has been identified
                    if (wand.Identified && wand.Charges > 0)
                    {
                        foreach (var line in WandLines(wand.WandEffect, wand.Charges))
                        {
                            yield return line;
                        }
                    }

                    break;
                }
            case BaseTool tool:
                {
                    // a crafting tool says what it is for (the Bowyer's fletcher's tools are listed as "Arrow Fletching", which a new archer takes for ammunition); its uses left are wear, which the tooltip never shows
                    yield return Line.Text(ToolLine(tool is FletcherTools));

                    foreach (var line in LootLines(item.LootType))
                    {
                        yield return line;
                    }

                    yield break;
                }
            case BaseIngot ingot when !CraftResources.IsStandard(ingot.Resource):
                {
                    // stock names every ingot "Ingots" and puts the metal on a line of its own; without it dull copper and iron read alike
                    yield return Line.Text(MetalLine(CraftResources.GetName(ingot.Resource)));
                    break;
                }
            case BaseOre ore when !CraftResources.IsStandard(ore.Resource):
                {
                    yield return Line.Text(MetalLine(CraftResources.GetName(ore.Resource)));
                    break;
                }
            case BaseWeapon weapon:
                {
                    // the maker and the quality are on the single-click label too, except for magic nobody has identified: that label says only "unidentified"
                    var magical = weapon.DamageLevel != WeaponDamageLevel.Regular || weapon.AccuracyLevel != WeaponAccuracyLevel.Regular ||
                                  weapon.DurabilityLevel != WeaponDurabilityLevel.Regular || weapon.Slayer != SlayerName.None;

                    if (!HidesMaker(magical, weapon.Identified) && weapon.Crafter is { } crafter)
                    {
                        yield return new Line(CraftedBy, crafter);
                    }

                    if (!HidesMaker(magical, weapon.Identified) && weapon.Quality == WeaponQuality.Exceptional)
                    {
                        yield return new Line(Exceptional);
                    }

                    foreach (var line in LootLines(item.LootType))
                    {
                        yield return line;
                    }

                    // what Item Identification found, once it has found it (the same facts the identified single-click label gives)
                    if (magical && weapon.Identified)
                    {
                        foreach (var line in WeaponMagicLines(weapon.DurabilityLevel, weapon.AccuracyLevel, weapon.DamageLevel))
                        {
                            yield return line;
                        }
                    }

                    foreach (var line in WeaponLines(weapon.MinDamage, weapon.MaxDamage, weapon.Speed, weapon.MaxRange, weapon.StrRequirement, weapon.Layer == Layer.TwoHanded, weapon.Skill))
                    {
                        yield return line;
                    }

                    yield break;
                }
            case BaseArmor armor:
                {
                    var magical = armor.Durability != ArmorDurabilityLevel.Regular || armor.ProtectionLevel != ArmorProtectionLevel.Regular;

                    if (!HidesMaker(magical, armor.Identified) && armor.Crafter is { } crafter)
                    {
                        yield return new Line(CraftedBy, crafter);
                    }

                    if (!HidesMaker(magical, armor.Identified) && armor.Quality == ArmorQuality.Exceptional)
                    {
                        yield return new Line(Exceptional);
                    }

                    foreach (var line in LootLines(item.LootType))
                    {
                        yield return line;
                    }

                    if (magical && armor.Identified)
                    {
                        foreach (var line in ArmorMagicLines(armor.Durability, armor.ProtectionLevel))
                        {
                            yield return line;
                        }
                    }

                    foreach (var line in ArmorLines(armor.BaseArmorRating, armor.ComputeStatReq(StatType.Str)))
                    {
                        yield return line;
                    }

                    yield break;
                }
        }

        foreach (var line in LootLines(item.LootType))
        {
            yield return line;
        }
    }

    /// <summary>The line that names a rare metal on its ingots and ore.</summary>
    public static string MetalLine(string metal) => $"Metal: {metal}";

    /// <summary>The sentence a crafting tool's tooltip carries.</summary>
    public static string ToolLine(bool fletcher) =>
        fletcher
            ? "A tool, not ammunition: double-click it to make arrows, bolts and bows."
            : "A tool: double-click it to open its crafting menu.";

    private static bool IsUnidentifiedMagic(Item item) =>
        item switch
        {
            BaseWand => false,
            BaseWeapon w => HidesMaker(
                w.DamageLevel != WeaponDamageLevel.Regular || w.AccuracyLevel != WeaponAccuracyLevel.Regular || w.DurabilityLevel != WeaponDurabilityLevel.Regular || w.Slayer != SlayerName.None,
                w.Identified
            ),
            BaseArmor a => HidesMaker(a.Durability != ArmorDurabilityLevel.Regular || a.ProtectionLevel != ArmorProtectionLevel.Regular, a.Identified),
            _ => false
        };

    private static string Capitalize(string text) => text.Length == 0 ? text : char.ToUpperInvariant(text[0]) + text[1..];

    /// <summary>What Item Identification finds on a weapon, one line each, in the words of its single-click label: the durability level, the accuracy level and the damage level as "of ...". A slayer is left out on purpose: the owner does not remember them from UO:R (2026-10-13).</summary>
    public static IEnumerable<Line> WeaponMagicLines(WeaponDurabilityLevel durability, WeaponAccuracyLevel accuracy, WeaponDamageLevel damage)
    {
        var durable = durability switch
        {
            WeaponDurabilityLevel.Durable => "durable",
            WeaponDurabilityLevel.Substantial => "substantial",
            WeaponDurabilityLevel.Massive => "massive",
            WeaponDurabilityLevel.Fortified => "fortified",
            WeaponDurabilityLevel.Indestructible => "indestructible",
            _ => null
        };

        var accurate = accuracy switch
        {
            WeaponAccuracyLevel.Accurate => "accurate",
            WeaponAccuracyLevel.Surpassingly => "surpassingly accurate",
            WeaponAccuracyLevel.Eminently => "eminently accurate",
            WeaponAccuracyLevel.Exceedingly => "exceedingly accurate",
            WeaponAccuracyLevel.Supremely => "supremely accurate",
            _ => null
        };

        var harm = damage switch
        {
            WeaponDamageLevel.Ruin => "ruin",
            WeaponDamageLevel.Might => "might",
            WeaponDamageLevel.Force => "force",
            WeaponDamageLevel.Power => "power",
            WeaponDamageLevel.Vanq => "vanquishing",
            _ => null
        };

        if (durable != null)
        {
            yield return Line.Text(Capitalize(durable));
        }

        if (accurate != null)
        {
            yield return Line.Text(Capitalize(accurate));
        }

        if (harm != null)
        {
            yield return Line.Text($"Of {harm}");
        }
    }

    /// <summary>What Item Identification finds on armor: the durability level, and the protection level as "of ...".</summary>
    public static IEnumerable<Line> ArmorMagicLines(ArmorDurabilityLevel durability, ArmorProtectionLevel protection)
    {
        var durable = durability switch
        {
            ArmorDurabilityLevel.Durable => "durable",
            ArmorDurabilityLevel.Substantial => "substantial",
            ArmorDurabilityLevel.Massive => "massive",
            ArmorDurabilityLevel.Fortified => "fortified",
            ArmorDurabilityLevel.Indestructible => "indestructible",
            _ => null
        };

        var guard = protection switch
        {
            ArmorProtectionLevel.Defense => "defense",
            ArmorProtectionLevel.Guarding => "guarding",
            ArmorProtectionLevel.Hardening => "hardening",
            ArmorProtectionLevel.Fortification => "fortification",
            ArmorProtectionLevel.Invulnerability => "invulnerability",
            _ => null
        };

        if (durable != null)
        {
            yield return Line.Text(Capitalize(durable));
        }

        if (guard != null)
        {
            yield return Line.Text($"Of {guard}");
        }
    }

    /// <summary>An identified wand: its effect as "of ..." and its charges.</summary>
    public static IEnumerable<Line> WandLines(WandEffect effect, int charges)
    {
        var name = effect switch
        {
            WandEffect.Clumsiness => "clumsiness",
            WandEffect.Identification => "identification",
            WandEffect.Healing => "healing",
            WandEffect.Feeblemindedness => "feeblemindedness",
            WandEffect.Weakness => "weakness",
            WandEffect.MagicArrow => "magic arrow",
            WandEffect.Harming => "harming",
            WandEffect.Fireball => "fireball",
            WandEffect.GreaterHealing => "greater healing",
            WandEffect.Lightning => "lightning",
            WandEffect.ManaDraining => "mana draining",
            _ => null
        };

        if (name != null)
        {
            yield return Line.Text($"Of {name}");
        }

        yield return Line.Text(charges == 1 ? "1 charge" : $"{charges} charges");
    }

    /// <summary>The single-click label of a magic weapon or armor nobody has identified says only "unidentified", so the tooltip does not name its maker or quality either.</summary>
    public static bool HidesMaker(bool magical, bool identified) => magical && !identified;

    /// <summary>Newbied (the shard's starter and permanently bound items) and blessed (a spellbook, a runebook).</summary>
    public static IEnumerable<Line> LootLines(LootType lootType)
    {
        if (lootType == LootType.Newbied)
        {
            yield return Line.Text(NewbiedText);
        }
        else if (lootType == LootType.Blessed)
        {
            yield return new Line(Blessed);
        }
    }

    /// <summary>A weapon's numbers as the stock list prints them (the same client texts), without anything an item of that kind does not have by itself.</summary>
    public static IEnumerable<Line> WeaponLines(int minDamage, int maxDamage, float speed, int maxRange, int strength, bool twoHanded, SkillName skill)
    {
        yield return new Line(Damage, $"{minDamage}\t{maxDamage}");
        yield return new Line(Speed, $"{speed}");

        if (maxRange > 1)
        {
            yield return new Line(Range, $"{maxRange}");
        }

        if (strength > 0)
        {
            yield return new Line(StrengthRequirement, $"{strength}");
        }

        yield return new Line(twoHanded ? TwoHanded : OneHanded);

        if (SkillText(skill) is { } skillLine)
        {
            yield return new Line(skillLine);
        }
    }

    /// <summary>The armor rating of the kind (not what a material, a quality or a magic level adds) and the Strength it needs.</summary>
    public static IEnumerable<Line> ArmorLines(int armorRating, int strength)
    {
        yield return Line.Text($"armor rating {armorRating}");

        if (strength > 0)
        {
            yield return new Line(StrengthRequirement, $"{strength}");
        }
    }

    /// <summary>The stock "skill required" texts for the four combat skills of this era.</summary>
    public static int? SkillText(SkillName skill) =>
        skill switch
        {
            SkillName.Swords  => 1061172,
            SkillName.Macing  => 1061173,
            SkillName.Fencing => 1061174,
            SkillName.Archery => 1061175,
            _                 => null
        };
}
