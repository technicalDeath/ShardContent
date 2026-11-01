using Server;
using Server.Collections;
using Server.ContextMenus;
using Server.Items;
using Server.Mobiles;
using Server.Regions;
using Server.SkillHandlers;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Wave 4, creatures (owner, 2026-11-01: "Do wave 4"): the stock Tame entry says why it is greyed (the Animal Taming it needs, too many followers, tame
/// already, too far), and a creature that can never be tamed says so; your own pet can be ridden, fed from your pack and bandaged; another player can be
/// bandaged; and your own menu offers to bandage yourself and to dismount. Each runs the stock use, so every stock rule and message still applies; the menu
/// only says in advance what the stock use would refuse. It needs the engine's mobile menu hook, <c>ContextMenuSystem.MobileEntriesHandler</c>.
/// </summary>
public static partial class WorldActions
{
    public const byte TameId = 140;
    public const byte RideId = 141;
    public const byte FeedId = 142;
    public const byte BandageId = 143;
    public const byte BandageSelfId = 144;
    public const byte DismountId = 145;

    /// <summary>The stock Tame entry's number (BaseCreature.TameEntry passes 6130; the engine stores numbers below 0x8000 as 3000000 + n).</summary>
    public const int StockTameNumber = 3006130;

    /// <summary>Taming reaches 2 tiles before AOS (AnimalTaming.InternalTarget).</summary>
    public const int TameRange = 2;

    /// <summary>A pet takes food dropped on it from 2 tiles, as feeding from the pack does (wave 3b).</summary>
    public const int FeedRange = 2;

    public const string CannotBeTamed = "That creature cannot be tamed.";
    public const string LooksTame = "That animal looks tame already.";
    public const string OnlyMalesTame = "That creature can only be tamed by males.";
    public const string OnlyFemalesTame = "That creature can only be tamed by females.";
    public const string TooManyFollowers = "You have too many followers to tame that creature.";
    public const string TooManyOwners = "This animal has had too many owners and is too upset for you to tame.";
    public const string MustSubdue = "You must subdue this creature before you can tame it.";
    public const string TooFarToTame = "Too far away. Stand within 2 tiles.";
    public const string CannotRideNow = "You may not ride at this time.";
    public const string Polymorphed = "You can't do that while polymorphed.";
    public const string DismountFirst = "Please dismount first.";
    public const string MountTooIll = "This mount is too ill to ride.";
    public const string TooFarToRide = "Too far away to ride. Stand next to it.";
    public const string NoFoodItEats = "You carry no food it eats.";
    public const string TooFarToFeed = "Too far away. Stand within 2 tiles.";
    public const string NoBandages = "Requires bandages.";
    public const string ItIsNotHurt = "It is not hurt.";
    public const string TheyAreNotHurt = "They are not hurt.";
    public const string YoungCannotHeal = "As a young player, you may not heal older players.";
    public const string TooFarToBandage = "Too far away. Stand next to them.";

    /// <summary>"You need 35.1 Animal Taming to tame this."</summary>
    public static string NeedTaming(double minimum) => $"You need {minimum:0.0} Animal Taming to tame this.";

    /// <summary>
    /// Why a taming attempt would fail before it starts, in the stock order (AnimalTaming.InternalTarget.OnTarget) for what the creature is, then the skill,
    /// then getting close, then the skill timer.
    /// </summary>
    public static string? TameReason(bool tamable, bool tameAlready, string? sexRule, bool tooManyFollowers, string? refusal, bool tooManyOwners, bool mustSubdue,
        double skill, double minimum, bool inRange, bool skillResting) =>
        !tamable ? CannotBeTamed : tameAlready ? LooksTame : sexRule ?? (tooManyFollowers ? TooManyFollowers : refusal ??
            (tooManyOwners ? TooManyOwners : mustSubdue ? MustSubdue : skill < minimum ? NeedTaming(minimum) : !inRange ? TooFarToTame :
                skillResting ? SkillResting : null));

    /// <summary>Why your mount would not let you ride, in the stock order (BaseMount.OnDoubleClick).</summary>
    public static string? RideReason(bool polymorphed, bool allowedHere, bool mounted, bool poisoned, bool inRange) =>
        polymorphed ? Polymorphed : !allowedHere ? CannotRideNow : mounted ? DismountFirst : !inRange ? TooFarToRide : poisoned ? MountTooIll : null;

    public static string? FeedReason(bool hasFood, bool inRange) => !hasFood ? NoFoodItEats : !inRange ? TooFarToFeed : null;

    /// <summary>Why a bandage on someone would be refused (Bandage, BandageContext.BeginHeal): the bandages, then whether they are hurt, then the rules, then range.</summary>
    public static string? BandageReason(bool hasBandage, bool hurt, string notHurt, bool youngOnOlder, bool inRange) =>
        !hasBandage ? NoBandages : !hurt ? notHurt : youngOnOlder ? YoungCannotHeal : !inRange ? TooFarToBandage : null;

    private static void ConfigureMobileMenu()
    {
        var previous = ContextMenuSystem.MobileEntriesHandler;
        ContextMenuSystem.MobileEntriesHandler = (Mobile mobile, Mobile from, ref PooledRefList<ContextMenuEntry> list) =>
        {
            AddMobileEntries(mobile, from, ref list);
            previous?.Invoke(mobile, from, ref list);
        };
    }

    private static void AddMobileEntries(Mobile mobile, Mobile from, ref PooledRefList<ContextMenuEntry> list)
    {
        if (!Enabled || from is not PlayerMobile { Alive: true } player || player.NetState is not { } state || mobile.Deleted)
        {
            return;
        }

        var texts = new List<(int Index, WorldAction Action)>();
        var stockTame = false;

        for (var i = 0; i < list.Count; i++)
        {
            if (list[i].Number == StockTameNumber && mobile is BaseCreature creature)
            {
                stockTame = true;
                var reason = TameReasonFor(player, creature);
                list[i].Enabled = reason is null;
                texts.Add((i, new WorldAction(0, "Tame", reason)));
            }
        }

        foreach (var action in MobileActions(player, mobile, stockTame))
        {
            texts.Add((list.Count, action));
            list.Add(new MobileActionEntry(mobile, action.Id) { Enabled = action.Available });
        }

        if (texts.Count > 0)
        {
            state.Send(ItemTexts(mobile.Serial.Value, texts));
        }
    }

    private static List<WorldAction> MobileActions(PlayerMobile player, Mobile mobile, bool stockTame)
    {
        var actions = new List<WorldAction>();

        if (mobile == player)
        {
            var hurt = player.Hits < player.HitsMax || player.Poisoned;
            actions.Add(new WorldAction(BandageSelfId, "Heal yourself", FindBandage(player) is null ? NoBandages : hurt ? null : NotHurt));

            if (player.Mounted)
            {
                actions.Add(new WorldAction(DismountId, "Dismount", null));
            }

            return actions;
        }

        if (!mobile.Alive)
        {
            return actions;
        }

        if (mobile is BaseCreature creature)
        {
            if (creature.Controlled && creature.ControlMaster == player)
            {
                AddPetActions(player, creature, actions);
            }
            else if (!stockTame && !creature.Summoned && !creature.Body.IsHuman && creature is not BaseVendor)
            {
                // a creature without the stock entry: one that can never be tamed, or someone's pet
                actions.Add(new WorldAction(TameId, "Tame", creature.Controlled ? LooksTame : CannotBeTamed));
            }
        }
        else if (mobile is PlayerMobile other)
        {
            actions.Add(new WorldAction(BandageId, "Heal with a bandage", BandageReasonFor(player, other, TheyAreNotHurt)));
        }

        return actions;
    }

    private static void AddPetActions(PlayerMobile player, BaseCreature pet, List<WorldAction> actions)
    {
        if (pet is BaseMount mount && !mount.IsDeadPet)
        {
            var reason = RideReason(
                player.IsBodyMod && !player.Body.IsHuman,
                player.Region is not BaseRegion { MountsAllowed: false } && player.MountBlockReason == BlockMountType.None && !player.HasTrade,
                player.Mounted,
                mount.Poisoned,
                player.InRange(mount, 1)
            );
            actions.Add(new WorldAction(RideId, "Ride", reason));
        }

        var food = FoodFor(player, pet);
        var label = food is { Amount: > 1 } ? $"Feed (all {food.Amount})" : "Feed";
        actions.Add(new WorldAction(FeedId, label, FeedReason(food is not null, player.InRange(pet, FeedRange))));
        actions.Add(new WorldAction(BandageId, "Heal with a bandage", BandageReasonFor(player, pet, ItIsNotHurt)));
    }

    private static string? TameReasonFor(PlayerMobile player, BaseCreature creature)
    {
        string? sexRule = player.Female ? creature.AllowFemaleTamer ? null : OnlyMalesTame : creature.AllowMaleTamer ? null : OnlyFemalesTame;
        var skill = AnimalTaming.CheckMastery(player, creature) ? double.MaxValue : player.Skills.AnimalTaming.Value;

        return TameReason(
            creature.Tamable,
            creature.Controlled,
            sexRule,
            player.Followers + creature.ControlSlots > player.FollowersMax,
            BaseCreature.TameAttemptRefusalHandler?.Invoke(player, creature),
            creature.Owners.Count >= BaseCreature.MaxOwners && !creature.Owners.Contains(player),
            AnimalTaming.MustBeSubdued(creature),
            skill,
            creature.MinTameSkill,
            player.InRange(creature, TameRange),
            Core.TickCount - player.NextSkillTime < 0
        );
    }

    private static string? BandageReasonFor(PlayerMobile player, Mobile patient, string notHurt) =>
        BandageReason(
            FindBandage(player) is not null,
            patient.Hits < patient.HitsMax || patient.Poisoned,
            notHurt,
            player.Young && patient is PlayerMobile { Young: false },
            player.InRange(patient, Bandage.Range)
        );

    private static Bandage? FindBandage(PlayerMobile player) => player.Backpack?.FindItemByType<Bandage>();

    /// <summary>Food in the pack the pet eats: never a container or gold, which some pets would take too (a goat eats bags; CheckFeed eats the whole stack).</summary>
    private static Item? FoodFor(PlayerMobile player, BaseCreature pet) =>
        player.Backpack?.FindItemByType<Item>(predicate: item => item is not (Container or Gold) && pet.CheckFoodPreference(item));

    private static void PerformMobile(PlayerMobile player, Mobile mobile, byte action)
    {
        // the menu may be stale: the action must still be offered, and its reason is said if it cannot be done now
        WorldAction? chosen = null;

        foreach (var a in MobileActions(player, mobile, false))
        {
            if (a.Id == action)
            {
                chosen = a;
            }
        }

        if (chosen is not { } offered || Refused(player, offered.Reason))
        {
            return;
        }

        switch (action)
        {
            case RideId:
                {
                    mobile.OnDoubleClick(player);
                    break;
                }
            case FeedId when mobile is BaseCreature pet && FoodFor(player, pet) is { } food:
                {
                    pet.CheckFeed(player, food);
                    break;
                }
            case BandageId or BandageSelfId when FindBandage(player) is { } bandage:
                {
                    Bandage.BandageTargetRequest(player, bandage, mobile);
                    break;
                }
            case DismountId:
                {
                    BaseMount.Dismount(player);
                    break;
                }
        }
    }

    private sealed class MobileActionEntry : ContextMenuEntry
    {
        private readonly Mobile _mobile;
        private readonly byte _action;

        public MobileActionEntry(Mobile mobile, byte action) : base(EntryNumber)
        {
            _mobile = mobile;
            _action = action;
        }

        public override void OnClick(Mobile from, IEntity target)
        {
            if (Enabled && from is PlayerMobile { Alive: true } player && !_mobile.Deleted && player.Map == _mobile.Map)
            {
                PerformMobile(player, _mobile, _action);
            }
        }
    }
}
