using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Wave 3b, gear (owner, 2026-11-01): weapons, shields, armour, clothing and jewellery are worn or wielded from the pack and taken off when worn; a light is
/// lit or put out; an instrument is played or used for Peacemaking or Provocation; a dye tub, dyes and hair dye are used. Wearing does what a player does
/// by hand: whatever is in the way goes into the pack first (a two-handed weapon needs both hands; a one-handed weapon may keep a shield or light). The stock
/// equip check still decides, so its messages still come; the menu says in advance the requirement a player does not meet.
/// </summary>
public static partial class WorldActions
{
    public const byte WearId = 80;
    public const byte TakeOffId = 81;
    public const byte LightId = 82;
    public const byte DouseId = 83;
    public const byte PlayId = 84;
    public const byte PeacemakingId = 85;
    public const byte ProvocationId = 86;
    public const byte DyeItemId = 87;
    public const byte FillTubId = 88;
    public const byte DyeHairId = 89;

    public const string BurntOut = "It has burnt out.";
    public const string InstrumentResting = "You must wait a moment before playing again.";
    public const string SkillResting = "You must wait a few moments to use another skill.";
    public const string NoHair = "You have no hair to dye.";
    public const string PackFull = "Your pack has no room for what you are holding.";

    /// <summary>The stat a piece of gear asks for that the player lacks, in the stock order (strength, dexterity, intelligence for weapons; dexterity first for armour).</summary>
    public static string? WearReason(string? sexRule, int str, int strReq, int dex, int dexReq, int intel, int intReq, bool armour)
    {
        if (sexRule is not null)
        {
            return sexRule;
        }

        string? strShort = str < strReq ? $"You are not strong enough to wear that: it needs {strReq} Strength." : null;
        string? dexShort = dex < dexReq ? $"You are not nimble enough to wear that: it needs {dexReq} Dexterity." : null;
        string? intShort = intel < intReq ? $"You are not smart enough to wear that: it needs {intReq} Intelligence." : null;

        return armour ? dexShort ?? strShort ?? intShort : dexShort ?? strShort ?? intShort;
    }

    private static void AddGearActions(PlayerMobile player, Item item, List<WorldAction> actions)
    {
        var worn = item.Parent == player;

        if (IsWearable(item))
        {
            if (worn)
            {
                actions.Add(new WorldAction(TakeOffId, "Take off", null));
            }
            else if (item.IsChildOf(player.Backpack))
            {
                actions.Add(new WorldAction(WearId, item is BaseWeapon ? "Wield" : "Wear", GearReason(player, item)));
            }
        }

        switch (item)
        {
            case BaseLight light when !light.Protected && (worn || item.IsChildOf(player.Backpack) || item.Parent is null && player.InRange(item.GetWorldLocation(), 2)):
                {
                    if (light.Burning)
                    {
                        actions.Add(new WorldAction(DouseId, "Put out", null));
                    }
                    else
                    {
                        actions.Add(new WorldAction(LightId, "Light", light.BurntOut ? BurntOut : null));
                    }

                    break;
                }
            case BaseInstrument when item.IsChildOf(player.Backpack):
                {
                    actions.Add(new WorldAction(PlayId, "Play", player.CanBeginAction<BaseInstrument>() ? null : InstrumentResting));
                    var skillReason = Core.TickCount - player.NextSkillTime < 0 || player.Spell is not null ? SkillResting : null;
                    actions.Add(new WorldAction(PeacemakingId, "Peacemaking", skillReason));
                    actions.Add(new WorldAction(ProvocationId, "Provocation", skillReason));
                    break;
                }
            case DyeTub when item.IsChildOf(player.Backpack) || item.Parent is null && player.InRange(item.GetWorldLocation(), 1):
                {
                    actions.Add(new WorldAction(DyeItemId, "Dye an item", null));
                    break;
                }
            case Dyes when item.IsChildOf(player.Backpack):
                {
                    actions.Add(new WorldAction(FillTubId, "Fill a dye tub", null));
                    break;
                }
            case HairDye or SpecialHairDye when item.IsChildOf(player.Backpack):
                {
                    var hasHair = player.HairItemID != 0 || player.FacialHairItemID != 0;
                    actions.Add(new WorldAction(DyeHairId, "Dye your hair", hasHair ? null : NoHair));
                    break;
                }
        }
    }

    /// <summary>Weapons, shields, armour, clothing and jewellery: things with a layer a player wears. A light or a spellbook has its own entries.</summary>
    private static bool IsWearable(Item item) =>
        item is BaseWeapon or BaseArmor or BaseClothing or BaseJewel && item.Layer is not (Layer.Invalid or Layer.Backpack);

    private static string? GearReason(PlayerMobile player, Item item)
    {
        string? sex(bool male, bool female) =>
            player.Female ? female ? null : "Only males can wear this." : male ? null : "Only females can wear this.";

        return item switch
        {
            BaseWeapon w   => WearReason(null, player.Str, w.StrRequirement, player.Dex, w.DexRequirement, player.Int, w.IntRequirement, false),
            BaseArmor a    => WearReason(sex(a.AllowMaleWearer, a.AllowFemaleWearer), player.Str, a.StrRequirement, player.Dex, a.DexRequirement, player.Int, a.IntRequirement, true),
            BaseClothing c => WearReason(sex(c.AllowMaleWearer, c.AllowFemaleWearer), player.Str, c.StrRequirement, 0, 0, 0, 0, false),
            _              => null
        };
    }

    /// <summary>
    /// Puts an item on as a player would: what is on its layer goes into the pack, and for things held in the hands, what the stock hand rules would not
    /// allow beside it goes too (a two-handed weapon needs both hands; a one-handed one cannot share with a two-handed weapon). If the stock equip still
    /// refuses, the moved things go back on.
    /// </summary>
    public static bool Equip(PlayerMobile player, Item item)
    {
        var moved = new List<Item>();

        bool Clear(Layer layer)
        {
            if (player.FindItemOnLayer(layer) is not { } held || held == item)
            {
                return true;
            }

            if (!player.PlaceInBackpack(held))
            {
                player.SendMessage(PackFull);
                return false;
            }

            moved.Add(held);
            return true;
        }

        var ok = Clear(item.Layer);

        if (ok && item is BaseWeapon && item.Layer == Layer.TwoHanded)
        {
            ok = Clear(Layer.OneHanded);
        }
        else if (ok && item.Layer == Layer.OneHanded && player.FindItemOnLayer(Layer.TwoHanded) is BaseWeapon)
        {
            ok = Clear(Layer.TwoHanded);
        }

        if (ok && player.EquipItem(item))
        {
            return true;
        }

        foreach (var back in moved)
        {
            player.EquipItem(back);
        }

        return false;
    }

    private static bool PerformGear(PlayerMobile player, Item item, byte action)
    {
        switch (action)
        {
            case WearId:
                {
                    Equip(player, item);
                    return true;
                }
            case TakeOffId:
                {
                    if (!player.PlaceInBackpack(item))
                    {
                        player.SendMessage("Your pack has no room for it.");
                    }

                    return true;
                }
            case LightId when item is BaseLight light:
                {
                    // a torch, candle or lantern goes in the hand first, or the stock lighting would put it at your feet when the hand is full
                    if (light is BaseEquipableLight && light.Parent != player && light.IsChildOf(player.Backpack) && !Equip(player, light))
                    {
                        return true;
                    }

                    light.Ignite();
                    return true;
                }
            case DouseId when item is BaseLight light:
                {
                    light.Douse();
                    return true;
                }
            case PlayId or DyeItemId or FillTubId or DyeHairId:
                {
                    // the stock use: the instrument plays, the tub and dyes ask what to dye, the hair dye opens its colours
                    item.OnDoubleClick(player);
                    return true;
                }
            case PeacemakingId or ProvocationId when item is BaseInstrument instrument:
                {
                    BaseInstrument.SetInstrument(player, instrument);
                    player.UseSkill(action == PeacemakingId ? SkillName.Peacemaking : SkillName.Provocation);
                    return true;
                }
        }

        return false;
    }
}
