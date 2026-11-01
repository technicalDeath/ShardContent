using Server;
using Server.Items;
using Server.Misc;
using Server.Mobiles;
using Server.Spells;
using Server.Spells.Fourth;
using Server.Spells.Seventh;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Wave 3b, magic and travel (owner, 2026-11-01): a spell scroll is cast, a spellbook or runebook opened, a marked rune recalled to or gated to (from the
/// spellbook when it has the spell, else from a scroll), and a wand used (it goes into the hands first, as the axe does). The stock spell does the work, so
/// the Magery roll, travel rules, the shard's travel warning and every refusal still apply; the menu says in advance what is plainly missing.
/// </summary>
public static partial class WorldActions
{
    public const byte CastScrollId = 100;
    public const byte OpenSpellbookId = 101;
    public const byte RecallId = 102;
    public const byte GateId = 103;
    public const byte RenameRuneId = 104;
    public const byte OpenRunebookId = 105;
    public const byte UseWandId = 106;

    public const int RecallSpellId = 31;
    public const int GateSpellId = 51;

    public const string AlreadyCasting = "You are already casting a spell.";
    public const string Frozen = "You cannot cast a spell while frozen.";
    public const string SpellbookTooDeep = "Put the spellbook straight in your backpack (not in a bag) to open it.";
    public const string RuneNotMarked = "That rune is not yet marked.";
    public const string NoRecallMeans = "Requires a Recall scroll, or the Recall spell in your spellbook.";
    public const string NoGateMeans = "Requires a Gate Travel scroll, or the Gate Travel spell in your spellbook.";
    public const string CriminalCannotTravel = "You are a criminal and cannot escape so easily.";
    public const string InCombatCannotTravel = "You cannot flee during the heat of battle.";
    public const string TooHeavyToTravel = "You are carrying too much to travel by magic.";
    public const string RunebookRecharging = "This book needs time to recharge.";
    public const string WandEmpty = "This wand is out of charges.";
    public const string WandRecharging = "The wand is recharging.";

    /// <summary>"Not enough mana: Recall needs 11."</summary>
    public static string NotEnoughMana(string spell, int mana) => $"Not enough mana: {spell} needs {mana}.";

    /// <summary>"Requires black pearl, bloodmoss and mandrake root."</summary>
    public static string NeedsReagents(IReadOnlyList<string> names) =>
        names.Count switch
        {
            0 => "",
            1 => $"Requires {names[0]}.",
            _ => $"Requires {string.Join(", ", names.Take(names.Count - 1))} and {names[^1]}."
        };

    /// <summary>Why a spell cannot be cast now: casting already, frozen, then mana; null when it can.</summary>
    public static string? CastReason(bool casting, bool frozen, int mana, int cost, string spell) =>
        casting ? AlreadyCasting : frozen ? Frozen : mana < cost ? NotEnoughMana(spell, cost) : null;

    /// <summary>Why a travel spell cannot be cast now, in the order the stock spell checks (the means first, then reagents, then the caster).</summary>
    public static string? TravelReason(bool marked, bool hasMeans, string noMeans, string? missingReagents, string? castReason, bool criminal, bool fighting, bool overloaded) =>
        !marked ? RuneNotMarked : !hasMeans ? noMeans : !string.IsNullOrEmpty(missingReagents) ? missingReagents : castReason ??
        (criminal ? CriminalCannotTravel : fighting ? InCombatCannotTravel : overloaded ? TooHeavyToTravel : null);

    private static void AddMagicActions(PlayerMobile player, Item item, List<WorldAction> actions)
    {
        switch (item)
        {
            case SpellScroll scroll when SpellRegistry.NewSpell(scroll.SpellID, player, scroll) is { } spell:
                {
                    var name = spell.Info.Name;
                    actions.Add(new WorldAction(CastScrollId, $"Cast {name}", CastReason(player.Spell is not null, player.Frozen || player.Paralyzed, player.Mana, spell.ScaleMana(spell.GetMana()), name)));
                    break;
                }
            case Spellbook book:
                {
                    var openable = book.Parent == player || book.Parent == player.Backpack;
                    actions.Add(new WorldAction(OpenSpellbookId, "Open", openable ? null : SpellbookTooDeep));
                    break;
                }
            case RecallRune rune:
                {
                    actions.Add(new WorldAction(RecallId, "Recall", TravelSpellReason(player, rune.Marked, RecallSpellId, NoRecallMeans)));
                    actions.Add(new WorldAction(GateId, "Open a gate", TravelSpellReason(player, rune.Marked, GateSpellId, NoGateMeans)));

                    if (rune.Marked)
                    {
                        actions.Add(new WorldAction(RenameRuneId, "Rename", null));
                    }

                    break;
                }
            case Runebook runebook:
                {
                    actions.Add(new WorldAction(OpenRunebookId, "Open", Core.Now < runebook.NextUse ? RunebookRecharging : null));
                    break;
                }
            case BaseWand wand:
                {
                    var reason = wand.Charges <= 0 ? WandEmpty : !player.CanBeginAction<BaseWand>() ? WandRecharging : null;
                    actions.Add(new WorldAction(UseWandId, "Use the wand", reason));
                    break;
                }
        }
    }

    /// <summary>
    /// How a travel spell would be cast: the spellbook when it holds the spell and the reagents are there, else a scroll of it. Null when neither.
    /// </summary>
    private static (Item? Scroll, Spell Spell)? TravelMeans(PlayerMobile player, int spellId)
    {
        if (Spellbook.Find(player, spellId) is not null && SpellRegistry.NewSpell(spellId, player, null) is { } bookSpell && MissingReagents(player, bookSpell).Count == 0)
        {
            return (null, bookSpell);
        }

        var scrollType = spellId == RecallSpellId ? typeof(RecallScroll) : typeof(GateTravelScroll);

        if (player.Backpack?.FindItemByType(scrollType) is { } scroll && SpellRegistry.NewSpell(spellId, player, scroll) is { } scrollSpell)
        {
            return (scroll, scrollSpell);
        }

        // the book holds the spell but reagents are short: say which
        if (Spellbook.Find(player, spellId) is not null && SpellRegistry.NewSpell(spellId, player, null) is { } shortSpell)
        {
            return (null, shortSpell);
        }

        return null;
    }

    private static string? TravelSpellReason(PlayerMobile player, bool marked, int spellId, string noMeans)
    {
        var means = TravelMeans(player, spellId);
        string? missing = null;
        string? cast = null;

        if (means is var (scroll, spell))
        {
            missing = scroll is null ? NeedsReagents(MissingReagents(player, spell)) : null;
            cast = CastReason(player.Spell is not null, player.Frozen || player.Paralyzed, player.Mana, spell.ScaleMana(spell.GetMana()), spell.Info.Name);
        }

        return TravelReason(
            marked, means is not null, noMeans, missing, cast, player.Criminal, SpellHelper.CheckCombat(player), spellId == RecallSpellId && StaminaSystem.IsOverloaded(player)
        );
    }

    /// <summary>The reagents a book cast lacks, by name, read without taking any (the stock check consumes them).</summary>
    private static List<string> MissingReagents(PlayerMobile player, Spell spell)
    {
        var missing = new List<string>();
        var reagents = spell.Info.Reagents;

        for (var i = 0; i < reagents.Length; i++)
        {
            var needed = i < spell.Info.Amounts.Length ? spell.Info.Amounts[i] : 1;

            if ((player.Backpack?.GetAmount(reagents[i]) ?? 0) < needed)
            {
                missing.Add(ReagentName(reagents[i]));
            }
        }

        return missing;
    }

    /// <summary>"BlackPearl" as "black pearl".</summary>
    public static string ReagentName(Type type)
    {
        var name = type.Name;
        var text = new System.Text.StringBuilder(name.Length + 4);

        for (var i = 0; i < name.Length; i++)
        {
            if (i > 0 && char.IsUpper(name[i]))
            {
                text.Append(' ');
            }

            text.Append(char.ToLowerInvariant(name[i]));
        }

        return text.ToString();
    }

    private static bool PerformMagic(PlayerMobile player, Item item, byte action)
    {
        switch (action)
        {
            case CastScrollId or RenameRuneId or OpenRunebookId:
                {
                    // the stock use: the scroll casts, the marked rune asks for its new name, the runebook opens
                    item.OnDoubleClick(player);
                    return true;
                }
            case OpenSpellbookId when item is Spellbook book:
                {
                    book.DisplayTo(player);
                    return true;
                }
            case RecallId or GateId when item is RecallRune rune && TravelMeans(player, action == RecallId ? RecallSpellId : GateSpellId) is var (scroll, _):
                {
                    var entry = new RunebookEntry(null, rune.Target, rune.TargetMap, rune.Description);
                    Spell spell = action == RecallId ? new RecallSpell(player, entry, null, scroll) : new GateTravelSpell(player, entry, scroll);
                    spell.Cast();
                    return true;
                }
            case UseWandId when item is BaseWand wand:
                {
                    if (wand.Parent != player && !TakeUp(player, wand))
                    {
                        return true;
                    }

                    wand.OnDoubleClick(player);
                    return true;
                }
        }

        return false;
    }
}
