using Server;
using Server.Engines.CharacterCreation;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Rekindled camping (Beta 2b; docs/Cooking-Era-Restore-Research.md has the cooking tie, Rekindled-Camping-Design.md the
/// design). Two flags, both off until the owner acknowledges them:
/// <c>campingStarterKit</c> gives every new character a Bedroll and Kindling; <c>campingFires</c> lets everyone light
/// Kindling at a chance of at least the skill floor, scales how long a fire burns and smoulders with the lighter's real
/// Camping skill, and lets Kindling used within a tile of a fire feed it (reset its burn, or relight embers). Secure camps, the Bedroll logout, the
/// dungeon refusal and the fact that fires are not saved all stay stock. With a flag off the stock behavior returns.
/// </summary>
public static class CampingService
{
    /// <summary>What a new character is still missing from the camping kit.</summary>
    public readonly record struct KitPlan(bool AddBedroll, int AddKindling);

    private static bool _configured;

    public static bool FiresEnabled => ShardRulesConfiguration.Settings?.FeatureFlags.CampingFires == true;

    public static bool KitEnabled => ShardRulesConfiguration.Settings?.FeatureFlags.CampingStarterKit == true;

    private static CampingRules Rules => ShardRulesConfiguration.Settings?.Camping ?? new CampingRules();

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        Campfire.TimingProvider = TimingForLighter;
        Kindling.IgniteCheck = Ignites;
        Kindling.FeedHandler = Feed;
        CharacterCreation.CharacterCreatedHandler += IssueKit;
    }

    // ---- the rules, free of game objects so they can be tested directly

    /// <summary>Camping skill as the lighting roll sees it: everyone counts as at least the floor, so everyone can light a fire.</summary>
    public static double EffectiveSkill(CampingRules rules, double skill) => Math.Max(skill, rules.SkillFloor);

    public static double IgniteChance(CampingRules rules, double skill) =>
        Math.Clamp(EffectiveSkill(rules, skill) / 100.0, 0.0, 1.0);

    /// <summary>
    /// A fire's life: lit for the base plus a few seconds per point of real Camping skill (the last share of it dim), then
    /// embers. The floor does not apply here, so every point of skill from zero lengthens the fire. The stock fire is 90
    /// seconds lit and 10 of embers.
    /// </summary>
    public static CampfireTiming TimingFor(CampingRules rules, double skill)
    {
        var effective = Math.Clamp(skill, 0.0, 100.0);
        var lit = rules.LitBaseSeconds + rules.LitPerSkillSeconds * effective;
        var embers = rules.EmberBaseSeconds + rules.EmberPerSkillSeconds * effective;

        return new CampfireTiming(
            TimeSpan.FromSeconds(lit * (1.0 - rules.DimShare)),
            TimeSpan.FromSeconds(lit),
            TimeSpan.FromSeconds(lit + embers)
        );
    }

    /// <summary>A Bedroll if there is none, and enough Kindling to reach the target. Stock Camping and Cooking grants count.</summary>
    public static KitPlan PlanKit(CampingRules rules, int bedrolls, int kindling) =>
        new(bedrolls == 0, Math.Max(0, rules.StarterKindling - kindling));

    public static void Validate(CampingRules rules, List<string> errors)
    {
        if (rules.SkillFloor is < 0.0 or > 100.0)
        {
            errors.Add($"camping.skillFloor must be between 0 and 100, but was {rules.SkillFloor}.");
        }

        if (rules.LitBaseSeconds is < 5.0 or > 3600.0)
        {
            errors.Add($"camping.litBaseSeconds must be between 5 and 3600, but was {rules.LitBaseSeconds}.");
        }

        if (rules.LitPerSkillSeconds is < 0.0 or > 30.0)
        {
            errors.Add($"camping.litPerSkillSeconds must be between 0 and 30, but was {rules.LitPerSkillSeconds}.");
        }

        if (rules.DimShare is <= 0.0 or >= 1.0)
        {
            errors.Add($"camping.dimShare must be above 0 and below 1, but was {rules.DimShare}.");
        }

        if (rules.EmberBaseSeconds is < 0.0 or > 3600.0)
        {
            errors.Add($"camping.emberBaseSeconds must be between 0 and 3600, but was {rules.EmberBaseSeconds}.");
        }

        if (rules.EmberPerSkillSeconds is < 0.0 or > 30.0)
        {
            errors.Add($"camping.emberPerSkillSeconds must be between 0 and 30, but was {rules.EmberPerSkillSeconds}.");
        }

        if (rules.FeedCooldownSeconds is < 0.0 or > 60.0)
        {
            errors.Add($"camping.feedCooldownSeconds must be between 0 and 60, but was {rules.FeedCooldownSeconds}.");
        }

        if (rules.StarterKindling is < 0 or > 20)
        {
            errors.Add($"camping.starterKindling must be between 0 and 20, but was {rules.StarterKindling}.");
        }
    }

    // ---- in the game

    private static double CampingOf(Mobile mobile) => mobile.Skills[SkillName.Camping].Value;

    private static CampfireTiming TimingForLighter(Mobile lighter) =>
        FiresEnabled ? TimingFor(Rules, CampingOf(lighter)) : CampfireTiming.Stock;

    private static bool Ignites(Mobile from) =>
        FiresEnabled
            ? from.CheckSkill(SkillName.Camping, IgniteChance(Rules, CampingOf(from)))
            : from.CheckSkill(SkillName.Camping, 0.0, 100.0);

    private static KindlingFeed Feed(Mobile from, Campfire fire)
    {
        if (!FiresEnabled)
        {
            return KindlingFeed.NotHandled;
        }

        if (Core.Now - fire.LitAt < TimeSpan.FromSeconds(Rules.FeedCooldownSeconds))
        {
            from.SendMessage("The fire has only just been tended.");
            return KindlingFeed.Refused;
        }

        var embers = fire.Status == CampfireStatus.Off;

        fire.Feed(TimingFor(Rules, CampingOf(from)));
        from.SendMessage(embers ? "The embers flare back to life." : "You feed the fire.");
        return KindlingFeed.Fed;
    }

    /// <summary>Gives a new character a Bedroll and Kindling, newbied and loose in the pack (the Bedroll has to be dropped to be used).</summary>
    public static void IssueKit(CharacterCreatedEventArgs args)
    {
        if (!KitEnabled || args.Mobile is not PlayerMobile { AccessLevel: AccessLevel.Player, Backpack: not null } player)
        {
            return;
        }

        var pack = player.Backpack;
        var bedrolls = 0;
        var kindling = 0;

        foreach (var item in pack.FindItemsByType<Bedroll>())
        {
            bedrolls += item.Amount;
        }

        foreach (var item in pack.FindItemsByType<Kindling>())
        {
            kindling += item.Amount;
        }

        var plan = PlanKit(Rules, bedrolls, kindling);

        if (plan.AddBedroll)
        {
            pack.DropItem(Newbied(new Bedroll()));
        }

        if (plan.AddKindling <= 0)
        {
            return;
        }

        if (pack.FindItemByType<Kindling>() is { } existing)
        {
            existing.Amount += plan.AddKindling;
        }
        else
        {
            pack.DropItem(Newbied(new Kindling(plan.AddKindling)));
        }
    }

    private static T Newbied<T>(T item) where T : Item
    {
        item.LootType = LootType.Newbied;
        return item;
    }

    /// <summary>Lines for [CampStatus: the flags, the numbers, and the fires near the staff member.</summary>
    public static IReadOnlyList<string> DescribeStatus(Mobile viewer)
    {
        var rules = Rules;
        var lines = new List<string>
        {
            $"Camping starter kit (campingStarterKit): {(KitEnabled ? "on" : "off")}. " +
            $"Camping fires (campingFires): {(FiresEnabled ? "on" : "off")}.",
            $"Skill floor {rules.SkillFloor:0.#}, lit {rules.LitBaseSeconds:0.#} s + {rules.LitPerSkillSeconds:0.#} s per point, " +
            $"embers {rules.EmberBaseSeconds:0.#} s + {rules.EmberPerSkillSeconds:0.#} s per point, feed cooldown {rules.FeedCooldownSeconds:0.#} s."
        };

        if (viewer.Map is null)
        {
            return lines;
        }

        var now = Core.Now;
        var count = 0;

        foreach (var fire in viewer.Map.GetItemsInRange<Campfire>(viewer.Location, 40))
        {
            count++;

            var age = now - fire.LitAt;
            var timing = fire.Timing;

            lines.Add(
                $"Fire {fire.Serial} at {fire.X},{fire.Y}: {fire.Status}, lit by {fire.Lighter?.Name ?? "unknown"}, " +
                $"{age.TotalSeconds:0} s since lit or fed; dims at {timing.Dim.TotalSeconds:0} s, embers at {timing.Out.TotalSeconds:0} s, " +
                $"gone at {timing.Expire.TotalSeconds:0} s."
            );
        }

        lines.Add($"Fires within 40 tiles: {count}.");
        return lines;
    }
}
