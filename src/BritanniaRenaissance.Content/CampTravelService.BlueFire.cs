using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The blue travel fire (<c>campTravelBlueFire</c>, off until the owner acknowledges it; docs/Camp-Travel-Blue-Fire-Proposal.md): of the
/// fires a player lights, one at a time is their travel fire, drawn in a blue hue, and only a travel fire is on the camp travel list.
/// The first fire a player lights while they hold no travel fire takes it (when their Camping can take at least one traveler), and
/// they keep it until that fire is down to embers or gone. A fire's arrivals are still counted over its own whole life, so one travel
/// fire at a time is also what stops a lighter's places being multiplied by lighting more fires. With the flag off none of this runs
/// and every fire is a travel fire, as before.
/// </summary>
public static partial class CampTravelService
{
    public static bool BlueFireEnabled => Enabled && ShardRulesConfiguration.Settings?.FeatureFlags.CampTravelBlueFire == true;

    /// <summary>What a fire is to camp travel. <see cref="Stock"/> is the old rule: every fire is a travel fire.</summary>
    public enum FireClass
    {
        Stock,

        /// <summary>The lighter's one travel fire: blue, on the list.</summary>
        Travel,

        /// <summary>Ordinary: the lighter already has a burning travel fire.</summary>
        AlreadyHave,

        /// <summary>Ordinary: the lighter's Camping cannot take even one traveler.</summary>
        LowCamping,

        /// <summary>Ordinary: down to embers (a travel fire gives up its claim here).</summary>
        Embers
    }

    /// <summary>What decides a fire's class. <c>HoldsOther</c> is a different, living fire of the same lighter that holds the claim.</summary>
    public readonly record struct FireClassFacts(int Capacity, bool Embers, bool HoldsThis, bool HoldsOther);

    /// <summary>The rule, free of game objects so it can be tested directly.</summary>
    public static FireClass Classify(FireClassFacts f)
    {
        if (f.Capacity < 1)
        {
            return FireClass.LowCamping;
        }

        if (f.Embers)
        {
            return FireClass.Embers;
        }

        if (f.HoldsThis)
        {
            return FireClass.Travel;
        }

        return f.HoldsOther ? FireClass.AlreadyHave : FireClass.Travel;
    }

    /// <summary>What a single click on a travel fire reads.</summary>
    public static string TravelFireName(string? lighterName) => $"{lighterName ?? "someone"}'s travel campfire";

    /// <summary>The lighter's one-off message when a fire's class changes after it was first told (the first telling is the "lit" notice).</summary>
    public static string? ClassChangeText(FireClass from, FireClass to, CampTravelRules rules) =>
        (from, to) switch
        {
            (FireClass.AlreadyHave or FireClass.LowCamping, FireClass.Travel) => BurnsBlueText(),
            (FireClass.Travel, FireClass.LowCamping) =>
                $"Your campfire no longer burns blue: party members can travel to a fire only when its lighter has Camping {SkillForFirstPlace(rules):0} or more.",
            _ => null
        };

    public static string BurnsBlueText() =>
        $"Your campfire burns blue. Party members can travel to it with {Command}. You can have one travel fire at a time.";

    // ---- in the game

    /// <summary>The lighter's travel fire, if it is alive and still theirs.</summary>
    private static readonly Dictionary<Mobile, Campfire> _claims = [];

    /// <summary>Whether camp travel treats this fire as a travel fire: every fire when the flag is off, otherwise only the lighter's claimed one.</summary>
    public static bool IsTravelFire(Campfire fire) =>
        !BlueFireEnabled || (fire.Lighter is { } lighter && _claims.TryGetValue(lighter, out var held) && ReferenceEquals(held, fire));

    /// <summary>The travel fire a mobile holds right now, or null.</summary>
    public static Campfire? TravelFireOf(Mobile lighter) => _claims.TryGetValue(lighter, out var held) ? held : null;

    private static void ClearBlueFire()
    {
        _claims.Clear();
    }

    /// <summary>
    /// Once a second, for every fire a player lit: release a claim that no longer holds, then give each fire its class, oldest fire
    /// first (so when several fires burn at once, as when the flag is first switched on, the oldest takes the claim), and dress it.
    /// </summary>
    private static void ClassifyFires()
    {
        var rules = Rules;
        List<Mobile>? freed = null;

        foreach (var (lighter, fire) in _claims)
        {
            if (lighter.Deleted || fire.Deleted || fire.Status == CampfireStatus.Off || !ReferenceEquals(fire.Lighter, lighter) ||
                Capacity(rules, lighter.Skills[SkillName.Camping].Value) < 1)
            {
                (freed ??= []).Add(lighter);
            }
        }

        if (freed is not null)
        {
            foreach (var lighter in freed)
            {
                _claims.Remove(lighter);
            }
        }

        var fires = new List<Campfire>();

        foreach (var fire in Campfire.Active)
        {
            if (!fire.Deleted && fire.Lighter is PlayerMobile { Deleted: false })
            {
                fires.Add(fire);
            }
        }

        fires.Sort(static (a, b) => a.CreatedAt.CompareTo(b.CreatedAt));

        foreach (var fire in fires)
        {
            var lighter = fire.Lighter!;
            var record = RecordOf(fire);
            _claims.TryGetValue(lighter, out var held);

            var facts = new FireClassFacts(
                Capacity(rules, lighter.Skills[SkillName.Camping].Value),
                fire.Status == CampfireStatus.Off,
                ReferenceEquals(held, fire),
                held is not null && !ReferenceEquals(held, fire)
            );
            var fireClass = Classify(facts);

            if (fireClass == FireClass.Travel)
            {
                _claims[lighter] = fire;
                record.EverTravel = true;
            }

            record.Class = fireClass;
            Dress(fire, fireClass, rules);
        }
    }

    /// <summary>Tells the lighter when a fire's class changes after the "lit" notice (blue gained, or lost to a drop in Camping).</summary>
    private static void TellClassChange(Campfire fire, FireRecord record, CampTravelRules rules)
    {
        var told = record.Told;

        record.Told = record.Class;

        // The first telling is the "lit" notice; the embers and relit notices already cover a change into or out of embers.
        if (told is null || told == record.Class || told == FireClass.Embers || record.Class == FireClass.Embers)
        {
            return;
        }

        if (ClassChangeText(told.Value, record.Class, rules) is { } text && fire.Lighter?.NetState is not null)
        {
            fire.Lighter.SendMessage(text);
        }
    }

    /// <summary>The travel fire's flames are blue and its single-click name says what it is; any other fire is as stock.</summary>
    private static void Dress(Campfire fire, FireClass fireClass, CampTravelRules rules)
    {
        var travel = fireClass == FireClass.Travel;
        var hue = travel ? rules.FireHue : 0;
        var name = travel ? TravelFireName(fire.Lighter?.Name) : null;

        if (fire.Hue != hue)
        {
            fire.Hue = hue;
        }

        if (fire.Name != name)
        {
            fire.Name = name;
        }
    }
}
