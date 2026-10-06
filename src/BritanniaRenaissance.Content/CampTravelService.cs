using System.Globalization;
using Server;
using Server.Accounting;
using Server.Engines.PartySystem;
using Server.Factions;
using Server.Gumps;
using Server.Items;
using Server.Misc;
using Server.Mobiles;
using Server.Network;
using Server.Spells;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Rekindled camp travel (Beta 2b item 4, behind <c>campingTravel</c>, off until the owner acknowledges it): a party member
/// can travel to a secure campfire lit by a member of their party. Every rule is a refusal in <see cref="Plan"/>, a pure
/// function of <see cref="TravelFacts"/>, and it runs when the player asks, when they confirm, on every tick of the wait,
/// and again at the moment of arrival. How many people a fire takes comes from its lighter's real Camping skill, so travel
/// is something a trained camper gives their party. The lighter is kept informed of the fire and of the command. Docs:
/// docs/Beta-2b-Camp-Travel-Plan.md.
/// </summary>
public static class CampTravelService
{
    public const string Command = "[CampTravel";

    /// <summary>Said in the confirmation (after "WARNING: ") and again on arrival when the camp is inside a Hot Zone.</summary>
    public const string HotZoneWarning = "This camp is inside a Hot Zone. " + TravelWarningService.Risk;

    public const string CooldownTag = "CampTravelReadyUtc";
    private const int RefusalHue = 0x22;
    private const int ArrivalSound = 0x1FC; // Recall
    private const int MaxListed = 8;

    public enum Refusal
    {
        None,
        Disabled,
        NotAlive,
        FireGone,
        OwnFire,
        NotInParty,
        WrongMap,
        Embers,
        NotSecure,
        LighterTooLow,
        Full,
        AlreadyThere,
        Criminal,
        Murderer,
        KnockedOut,
        Combat,
        Frozen,
        Overloaded,
        CarriesSigil,
        FromHotZone,
        LeaveBlocked,
        DestinationBlocked,
        NoArrivalTile,
        Cooldown,
        NoKindling
    }

    /// <summary>What a trip depends on. The defaults describe a trip with nothing in the way, so a test changes one thing.</summary>
    public sealed record TravelFacts
    {
        public bool Enabled { get; init; } = true;
        public bool TravelerAlive { get; init; } = true;
        public bool FireExists { get; init; } = true;
        public bool FireIsOwn { get; init; }
        public bool LighterInParty { get; init; } = true;
        public bool SameMap { get; init; } = true;
        public bool FireEmbers { get; init; }
        public bool FireSecure { get; init; } = true;
        public int Capacity { get; init; } = 3;
        public int Arrivals { get; init; }
        public bool AlreadyThere { get; init; }
        public bool Criminal { get; init; }
        public bool Murderer { get; init; }
        public bool KnockedOut { get; init; }
        public bool InCombat { get; init; }
        public bool Frozen { get; init; }
        public bool Overloaded { get; init; }
        public bool CarriesSigil { get; init; }
        public bool InHotZone { get; init; }
        public bool LeaveAllowed { get; init; } = true;
        public bool DestinationAllowed { get; init; } = true;
        public bool HasArrivalTile { get; init; } = true;
        public int Kindling { get; init; } = 5;
        public TimeSpan CooldownRemaining { get; init; } = TimeSpan.Zero;
    }

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.CampingTravel == true;

    private static CampTravelRules Rules => ShardRulesConfiguration.Settings?.CampTravel ?? new CampTravelRules();

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CommandSystem.Register("CampTravel", AccessLevel.Player, OnCommand);
        Server.Timer.StartTimer(TimeSpan.FromSeconds(1.0), TimeSpan.FromSeconds(1.0), Poll);
    }

    // ---- what the [Welcome guide tells a player

    public const string HotZoneWarningHelp =
        "If Recall, a gate or camp travel is about to take you into a Hot Zone from outside one, you are asked to confirm first. " +
        "Tick the box on the warning, or use [TravelWarning off, to stop being asked; [TravelWarning on brings the warning back.";

    /// <summary>The guide's Camp travel page, from the numbers in force.</summary>
    public static IReadOnlyList<string> GuideParagraphs(CampTravelRules rules) =>
    [
        $"Use {Command} to travel to a secure campfire lit by a member of your party. A fire is secure once it has burned for " +
        $"{rules.SecureSeconds:0} seconds and is not down to embers.",
        $"It costs {rules.KindlingCost} Kindling, you wait {rules.ChannelSeconds:0} seconds without moving, and you can travel this way once every " +
        $"{Span(TimeSpan.FromMinutes(rules.CooldownMinutes))}.",
        $"A fire takes as many travelers as its lighter's Camping skill allows: 1 at Camping {SkillForFirstPlace(rules):0}, one more for each {rules.SkillPerArrival:0} points, up to {rules.MaxArrivals}. " +
        "Criminals, murderers and anyone in recent player combat cannot use it, and it cannot be used to leave a Hot Zone."
    ];

    // ---- the rules, free of game objects so they can be tested directly

    /// <summary>
    /// Arrivals a fire takes: none below <c>capacityBaseSkill + skillPerArrival</c> real Camping, then one more for each
    /// <c>skillPerArrival</c> points, at most <c>maxArrivals</c> (1 at 50, 2 at 60, ... 6 at 100 with the shipped numbers).
    /// </summary>
    public static int Capacity(CampTravelRules rules, double lighterCamping)
    {
        var places = (int)Math.Floor((lighterCamping - rules.CapacityBaseSkill) / rules.SkillPerArrival + 1e-9);
        return Math.Clamp(places, 0, rules.MaxArrivals);
    }

    /// <summary>The Camping skill at which a fire takes its first traveler.</summary>
    public static double SkillForFirstPlace(CampTravelRules rules) => rules.CapacityBaseSkill + rules.SkillPerArrival;

    /// <summary>The first thing in the way of a trip, in the order the player should hear about it, or None.</summary>
    public static Refusal Plan(CampTravelRules rules, TravelFacts f)
    {
        if (!f.Enabled)
        {
            return Refusal.Disabled;
        }

        if (!f.TravelerAlive)
        {
            return Refusal.NotAlive;
        }

        if (!f.FireExists)
        {
            return Refusal.FireGone;
        }

        if (f.FireIsOwn)
        {
            return Refusal.OwnFire;
        }

        if (!f.LighterInParty)
        {
            return Refusal.NotInParty;
        }

        if (!f.SameMap)
        {
            return Refusal.WrongMap;
        }

        if (f.FireEmbers)
        {
            return Refusal.Embers;
        }

        if (!f.FireSecure)
        {
            return Refusal.NotSecure;
        }

        if (f.Capacity <= 0)
        {
            return Refusal.LighterTooLow;
        }

        if (f.Arrivals >= f.Capacity)
        {
            return Refusal.Full;
        }

        if (f.AlreadyThere)
        {
            return Refusal.AlreadyThere;
        }

        if (f.Criminal)
        {
            return Refusal.Criminal;
        }

        if (f.Murderer)
        {
            return Refusal.Murderer;
        }

        if (f.KnockedOut)
        {
            return Refusal.KnockedOut;
        }

        if (f.InCombat)
        {
            return Refusal.Combat;
        }

        if (f.Frozen)
        {
            return Refusal.Frozen;
        }

        if (f.Overloaded)
        {
            return Refusal.Overloaded;
        }

        if (f.CarriesSigil)
        {
            return Refusal.CarriesSigil;
        }

        if (f.InHotZone)
        {
            return Refusal.FromHotZone;
        }

        if (!f.LeaveAllowed)
        {
            return Refusal.LeaveBlocked;
        }

        if (!f.DestinationAllowed)
        {
            return Refusal.DestinationBlocked;
        }

        if (!f.HasArrivalTile)
        {
            return Refusal.NoArrivalTile;
        }

        if (f.CooldownRemaining > TimeSpan.Zero)
        {
            return Refusal.Cooldown;
        }

        return f.Kindling < rules.KindlingCost ? Refusal.NoKindling : Refusal.None;
    }

    /// <summary>What the player is told when a trip is refused. The four stock Recall refusals keep Recall's words.</summary>
    public static string Describe(Refusal refusal, CampTravelRules rules, TravelFacts f) =>
        refusal switch
        {
            Refusal.Disabled           => "Camp travel is not available.",
            Refusal.NotAlive           => "You are in no state to travel.",
            Refusal.FireGone           => "That campfire has burned out.",
            Refusal.OwnFire            => "That is your own campfire.",
            Refusal.NotInParty         => "The one who lit that campfire is no longer in your party.",
            Refusal.WrongMap           => "You cannot travel to a camp in another land.",
            Refusal.Embers             => "That campfire is down to embers. Camp travel needs a burning fire.",
            Refusal.NotSecure          => $"That camp is not secure yet. Its fire must have burned for {rules.SecureSeconds:0} seconds.",
            Refusal.LighterTooLow      => $"The one who lit that fire needs Camping {SkillForFirstPlace(rules):0} or higher before party members can travel to it.",
            Refusal.Full               => $"That camp has no places left ({f.Arrivals} of {f.Capacity} used).",
            Refusal.AlreadyThere       => "You are already at that camp.",
            Refusal.Criminal           => "Thou'rt a criminal and cannot escape so easily.",
            Refusal.Murderer           => "Murderers cannot use camp travel.",
            Refusal.KnockedOut         => "You cannot travel while you are knocked out.",
            Refusal.Combat             => "Wouldst thou flee during the heat of battle??",
            Refusal.Frozen             => "You cannot travel while you are unable to move.",
            Refusal.Overloaded         => "Thou art too encumbered to move.",
            Refusal.CarriesSigil       => "You can't do that while carrying the sigil.",
            Refusal.FromHotZone        => "You cannot use camp travel to leave a Hot Zone.",
            Refusal.LeaveBlocked       => "You cannot travel from this place.",
            Refusal.DestinationBlocked => "You cannot travel to that camp.",
            Refusal.NoArrivalTile      => "There is no open ground beside that campfire.",
            Refusal.Cooldown           => $"You cannot use camp travel again for {Span(f.CooldownRemaining)}.",
            Refusal.NoKindling         => $"You need {rules.KindlingCost} Kindling in your backpack to travel.",
            _                          => string.Empty
        };

    /// <summary>A word or two for the list gump beside a camp.</summary>
    public static string ShortLabel(Refusal refusal) =>
        refusal switch
        {
            Refusal.None          => "ready",
            Refusal.NotSecure     => "securing",
            Refusal.Embers        => "embers",
            Refusal.Full          => "full",
            Refusal.LighterTooLow => "needs more Camping",
            Refusal.Cooldown      => "cooldown",
            Refusal.NoKindling    => "no Kindling",
            Refusal.AlreadyThere  => "you are here",
            _                     => "not now"
        };

    /// <summary>"23 minutes", "40 seconds": time left, rounded up to the unit the player reads.</summary>
    public static string Span(TimeSpan span)
    {
        if (span.TotalMinutes > 1.0)
        {
            var minutes = (int)Math.Ceiling(span.TotalMinutes);
            return minutes == 1 ? "1 minute" : $"{minutes} minutes";
        }

        var seconds = Math.Max(1, (int)Math.Ceiling(span.TotalSeconds));
        return seconds == 1 ? "1 second" : $"{seconds} seconds";
    }

    public static TimeSpan CooldownRemaining(string? readyUtcTag, DateTime nowUtc)
    {
        if (string.IsNullOrEmpty(readyUtcTag) ||
            !DateTime.TryParse(readyUtcTag, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind, out var ready))
        {
            return TimeSpan.Zero;
        }

        var remaining = ready.ToUniversalTime() - nowUtc;
        return remaining > TimeSpan.Zero ? remaining : TimeSpan.Zero;
    }

    /// <summary>A fire is secure once it has burned for <c>secureSeconds</c> and is not down to embers (a fed fire stays secure).</summary>
    public static bool IsSecure(CampTravelRules rules, TimeSpan age, bool embers) =>
        !embers && age >= TimeSpan.FromSeconds(rules.SecureSeconds);

    // ---- where a camp is

    /// <summary>The first name there is: a town or dungeon, then a Hot Zone, then sextant coordinates, so a camp always says where.</summary>
    public static string PlaceLabel(string? regionName, string? hotZoneName, string? sextant) =>
        !string.IsNullOrWhiteSpace(regionName) ? regionName :
        !string.IsNullOrWhiteSpace(hotZoneName) ? hotZoneName :
        !string.IsNullOrWhiteSpace(sextant) ? sextant : "the wilderness";

    public static string SextantText(int latitude, int latMinutes, bool south, int longitude, int longMinutes, bool east) =>
        $"{latitude}\u00b0 {latMinutes}'{(south ? 'S' : 'N')}, {longitude}\u00b0 {longMinutes}'{(east ? 'E' : 'W')}";

    /// <summary>Where a point is, in words a player can use.</summary>
    public static string PlaceName(Map? map, Point3D location)
    {
        if (map is null)
        {
            return PlaceLabel(null, null, null);
        }

        string? regionName = null;

        for (var region = Region.Find(location, map); region is not null; region = region.Parent)
        {
            if (!string.IsNullOrWhiteSpace(region.Name))
            {
                regionName = region.Name;
                break;
            }
        }

        var hot = OutdoorHotZonePolicy.GetRegionName(map, location);
        int lat = 0, latMinutes = 0, @long = 0, longMinutes = 0;
        var south = false;
        var east = false;
        var sextant = Sextant.Format(location, map, ref @long, ref lat, ref longMinutes, ref latMinutes, ref east, ref south)
            ? SextantText(lat, latMinutes, south, @long, longMinutes, east)
            : null;

        return PlaceLabel(regionName, hot is null ? null : OutdoorHotZoneBoundaryService.DisplayName(hot), sextant);
    }

    // ---- keeping the lighter informed

    public enum FireNotice
    {
        Lit,
        Secure,
        Dimming,
        Embers,
        Relit,
        Out
    }

    public readonly record struct FireView(bool Gone, CampfireStatus Status, bool Secure);

    /// <summary>Which moments of a fire's life the lighter has been told about, so each is told once.</summary>
    public sealed class NoticeTracker
    {
        private bool _lit;
        private bool _secure;
        private bool _out;
        private CampfireStatus _status = CampfireStatus.Burning; // a fire is lit burning

        public IReadOnlyList<FireNotice> Advance(FireView view)
        {
            var notices = new List<FireNotice>();

            if (_out)
            {
                return notices;
            }

            if (!_lit)
            {
                _lit = true;
                notices.Add(FireNotice.Lit);
            }

            if (view.Gone)
            {
                _out = true;
                notices.Add(FireNotice.Out);
                return notices;
            }

            if (view.Status != _status)
            {
                notices.Add(
                    view.Status switch
                    {
                        CampfireStatus.Burning       => FireNotice.Relit,
                        CampfireStatus.Extinguishing => FireNotice.Dimming,
                        _                            => FireNotice.Embers
                    }
                );
                _status = view.Status;
            }

            if (!_secure && view.Secure)
            {
                _secure = true;
                notices.Add(FireNotice.Secure);
            }

            return notices;
        }
    }

    public readonly record struct NoticeContext(int Capacity, int Arrivals, bool FedByLighter);

    /// <summary>The words for a notice, or null when the lighter has nothing to learn from it.</summary>
    public static string? NoticeText(CampTravelRules rules, FireNotice notice, NoticeContext c)
    {
        var left = Math.Max(0, c.Capacity - c.Arrivals);
        var travel = c.Capacity > 0 && left > 0
            ? $"Party members can travel to it with {Command} ({left} of {c.Capacity} {Places(c.Capacity)} left)."
            : string.Empty;

        switch (notice)
        {
            case FireNotice.Lit:
                return c.Capacity > 0
                    ? $"Your campfire is lit. Once it has burned for {rules.SecureSeconds:0} seconds, party members can travel to it with {Command} " +
                      $"(your Camping skill gives {c.Capacity} {Places(c.Capacity)})."
                    : $"Your campfire is lit. Party members can travel to your camps with {Command} once your Camping skill is {SkillForFirstPlace(rules):0} or higher.";
            case FireNotice.Secure:
                return string.IsNullOrEmpty(travel) ? null : $"Your camp is secure. {travel}";
            case FireNotice.Dimming:
                return "Your campfire is burning low. Use Kindling beside it to keep it burning.";
            case FireNotice.Embers:
                return c.Capacity > 0
                    ? "Your campfire is down to embers. Party members cannot travel to it until you feed it with Kindling."
                    : "Your campfire is down to embers. Use Kindling beside it to relight it.";
            case FireNotice.Relit:
                var relit = c.FedByLighter ? string.Empty : "Your campfire burns brightly again.";
                var both = (relit + " " + travel).Trim();
                return both.Length == 0 ? null : both;
            case FireNotice.Out:
                return c.Arrivals > 0
                    ? $"Your campfire has burned out. {c.Arrivals} {(c.Arrivals == 1 ? "party member" : "party members")} travelled to it."
                    : "Your campfire has burned out.";
            default:
                return null;
        }
    }

    public static string ArrivalNoticeText(string travelerName, int arrivals, int capacity) =>
        arrivals >= capacity
            ? $"{travelerName} has travelled to your camp ({arrivals} of {capacity} {Places(capacity)} used). Your camp has no places left."
            : $"{travelerName} has travelled to your camp ({arrivals} of {capacity} {Places(capacity)} used).";

    private static string Places(int count) => count == 1 ? "place" : "places";

    public static void Validate(CampTravelRules rules, List<string> errors)
    {
        if (rules.ChannelSeconds is < 1.0 or > 30.0)
        {
            errors.Add($"campTravel.channelSeconds must be between 1 and 30, but was {rules.ChannelSeconds}.");
        }

        if (rules.CooldownMinutes is < 0.0 or > 1440.0)
        {
            errors.Add($"campTravel.cooldownMinutes must be between 0 and 1440, but was {rules.CooldownMinutes}.");
        }

        if (rules.KindlingCost is < 0 or > 20)
        {
            errors.Add($"campTravel.kindlingCost must be between 0 and 20, but was {rules.KindlingCost}.");
        }

        if (rules.CapacityBaseSkill is < 0.0 or > 100.0)
        {
            errors.Add($"campTravel.capacityBaseSkill must be between 0 and 100, but was {rules.CapacityBaseSkill}.");
        }

        if (rules.SkillPerArrival is < 1.0 or > 50.0)
        {
            errors.Add($"campTravel.skillPerArrival must be between 1 and 50, but was {rules.SkillPerArrival}.");
        }

        if (rules.MaxArrivals is < 1 or > 20)
        {
            errors.Add($"campTravel.maxArrivals must be between 1 and 20, but was {rules.MaxArrivals}.");
        }

        if (rules.SecureSeconds is < 0.0 or > 600.0)
        {
            errors.Add($"campTravel.secureSeconds must be between 0 and 600, but was {rules.SecureSeconds}.");
        }

        if (rules.ArrivalRange is < 1 or > 5)
        {
            errors.Add($"campTravel.arrivalRange must be between 1 and 5, but was {rules.ArrivalRange}.");
        }
    }

    // ---- what is known about each fire

    private sealed class FireRecord
    {
        public readonly NoticeTracker Tracker = new();
        public Mobile? Lighter;
        public Mobile? LastFeeder;
        public int Arrivals;
    }

    private static readonly Dictionary<Campfire, FireRecord> _records = [];

    private static FireRecord RecordOf(Campfire fire)
    {
        if (!_records.TryGetValue(fire, out var record))
        {
            _records[fire] = record = new FireRecord { Lighter = fire.Lighter };
        }

        return record;
    }

    /// <summary>Called when somebody feeds a fire, so the lighter is not told twice about their own feeding.</summary>
    public static void NoteFed(Campfire fire, Mobile feeder)
    {
        if (Enabled)
        {
            RecordOf(fire).LastFeeder = feeder;
        }
    }

    /// <summary>How many party members have travelled to this fire so far.</summary>
    public static int ArrivalsOf(Campfire fire) => _records.TryGetValue(fire, out var record) ? record.Arrivals : 0;

    /// <summary>Whether travel counts this fire as secure right now.</summary>
    public static bool IsSecure(Campfire fire) =>
        IsSecure(Rules, Core.Now - fire.CreatedAt, fire.Status == CampfireStatus.Off);

    private static int CapacityOf(Campfire fire) =>
        fire.Lighter is { Deleted: false } lighter
            ? Capacity(Rules, lighter.Skills[SkillName.Camping].Value)
            : 0;

    private static void Poll()
    {
        if (!Enabled)
        {
            if (_records.Count > 0)
            {
                _records.Clear();
            }

            return;
        }

        var rules = Rules;
        var now = Core.Now;
        List<Campfire>? gone = null;

        foreach (var fire in _records.Keys)
        {
            if (fire.Deleted)
            {
                (gone ??= []).Add(fire);
            }
        }

        if (gone is not null)
        {
            foreach (var fire in gone)
            {
                var record = _records[fire];

                _records.Remove(fire);
                Tell(
                    record.Lighter,
                    rules,
                    record.Tracker.Advance(new FireView(true, CampfireStatus.Off, false)),
                    new NoticeContext(record.Lighter is { Deleted: false } l ? Capacity(rules, l.Skills[SkillName.Camping].Value) : 0, record.Arrivals, false)
                );
            }
        }

        foreach (var fire in Campfire.Active)
        {
            if (fire.Lighter is null)
            {
                continue;
            }

            var record = RecordOf(fire);
            var embers = fire.Status == CampfireStatus.Off;
            var view = new FireView(false, fire.Status, IsSecure(rules, now - fire.CreatedAt, embers));
            var notices = record.Tracker.Advance(view);

            if (notices.Count > 0)
            {
                Tell(
                    fire.Lighter,
                    rules,
                    notices,
                    new NoticeContext(CapacityOf(fire), record.Arrivals, record.LastFeeder == fire.Lighter)
                );
            }
        }
    }

    private static void Tell(Mobile? lighter, CampTravelRules rules, IReadOnlyList<FireNotice> notices, NoticeContext context)
    {
        if (lighter?.NetState is null)
        {
            return;
        }

        foreach (var notice in notices)
        {
            if (NoticeText(rules, notice, context) is { } text)
            {
                lighter.SendMessage(text);
            }
        }
    }

    // ---- gathering the facts of a trip

    private static TravelFacts Gather(PlayerMobile traveler, Campfire fire, out Point3D arrival)
    {
        var rules = Rules;
        var now = Core.Now;
        var lighter = fire.Lighter;
        var party = Party.Get(traveler);
        var embers = fire.Status == CampfireStatus.Off;
        var sameMap = !fire.Deleted && fire.Map == Map.Felucca && traveler.Map == Map.Felucca;

        arrival = Point3D.Zero;

        var arrivalFound = false;
        var leaveAllowed = true;
        var destinationAllowed = true;

        if (!fire.Deleted && sameMap)
        {
            leaveAllowed = SpellHelper.CheckTravel(traveler, TravelCheckType.RecallFrom, out _);
            destinationAllowed = SpellHelper.CheckTravel(traveler, fire.Map, fire.Location, TravelCheckType.RecallTo, out _);
            arrivalFound = destinationAllowed && TryFindArrival(traveler, fire, rules.ArrivalRange, out arrival);
        }

        return new TravelFacts
        {
            Enabled = Enabled,
            TravelerAlive = traveler.Alive,
            FireExists = !fire.Deleted && lighter is { Deleted: false },
            FireIsOwn = lighter == traveler,
            LighterInParty = lighter is not null && party?.Contains(lighter) == true,
            SameMap = sameMap,
            FireEmbers = embers,
            FireSecure = IsSecure(rules, now - fire.CreatedAt, embers),
            Capacity = CapacityOf(fire),
            Arrivals = _records.TryGetValue(fire, out var record) ? record.Arrivals : 0,
            AlreadyThere = sameMap && traveler.InRange(fire, Campfire.SecureRange),
            Criminal = traveler.Criminal,
            Murderer = traveler.Murderer,
            KnockedOut = KnockedOutService.IsKnockedOut(traveler),
            InCombat = SpellHelper.CheckCombat(traveler),
            Frozen = traveler.Frozen,
            Overloaded = StaminaSystem.IsOverloaded(traveler),
            CarriesSigil = Sigil.ExistsOn(traveler),
            InHotZone = OutdoorHotZonePolicy.IsHot(traveler),
            LeaveAllowed = leaveAllowed,
            DestinationAllowed = destinationAllowed,
            HasArrivalTile = arrivalFound,
            Kindling = traveler.Backpack?.GetAmount(typeof(Kindling)) ?? 0,
            CooldownRemaining = CooldownRemaining((traveler.Account as Account)?.GetTag(CooldownTag), now)
        };
    }

    /// <summary>
    /// An open tile within <paramref name="range"/> of the fire that is on the same side of any Hot Zone edge as the fire, so
    /// the warning given for the camp is true of the tile the traveler lands on. Tiles nobody stands on come first.
    /// </summary>
    private static bool TryFindArrival(PlayerMobile traveler, Campfire fire, int range, out Point3D arrival)
    {
        var map = fire.Map;
        var fireHot = OutdoorHotZonePolicy.IsHot(fire);
        var free = new List<Point3D>();
        var taken = new List<Point3D>();

        for (var dx = -range; dx <= range; dx++)
        {
            for (var dy = -range; dy <= range; dy++)
            {
                if (dx == 0 && dy == 0)
                {
                    continue;
                }

                var x = fire.X + dx;
                var y = fire.Y + dy;

                foreach (var z in new[] { fire.Z, map.GetAverageZ(x, y) })
                {
                    var point = new Point3D(x, y, z);

                    if (!map.CanSpawnMobile(point) || SpellHelper.CheckMulti(point, map) ||
                        OutdoorHotZonePolicy.IsHot(map, point) != fireHot ||
                        !SpellHelper.CheckTravel(traveler, map, point, TravelCheckType.RecallTo, out _))
                    {
                        continue;
                    }

                    var occupied = false;

                    foreach (var _ in map.GetMobilesInRange(point, 0))
                    {
                        occupied = true;
                        break;
                    }

                    (occupied ? taken : free).Add(point);
                    break;
                }
            }
        }

        var pool = free.Count > 0 ? free : taken;

        if (pool.Count == 0)
        {
            arrival = Point3D.Zero;
            return false;
        }

        arrival = pool[Utility.Random(pool.Count)];
        return true;
    }

    private static void Refuse(PlayerMobile traveler, Refusal refusal, TravelFacts facts) =>
        traveler.SendMessage(RefusalHue, Describe(refusal, Rules, facts));

    private static string LighterName(Campfire fire) => fire.Lighter?.Name ?? "someone";

    // ---- the command, the lists and the wait

    [Usage("CampTravel")]
    [Description("Travel to a secure campfire lit by a member of your party.")]
    private static void OnCommand(CommandEventArgs e)
    {
        if (e.Mobile is not PlayerMobile traveler)
        {
            return;
        }

        if (!Enabled)
        {
            traveler.SendMessage(RefusalHue, Describe(Refusal.Disabled, Rules, new TravelFacts()));
            return;
        }

        var rules = Rules;
        var party = Party.Get(traveler);
        var entries = new List<ListEntry>();

        if (party is not null)
        {
            foreach (var fire in Campfire.Active)
            {
                if (fire.Lighter is { Deleted: false } lighter && lighter != traveler && party.Contains(lighter) &&
                    fire.Map == traveler.Map)
                {
                    var facts = Gather(traveler, fire, out _);
                    var refusal = Plan(rules, facts);

                    entries.Add(
                        new ListEntry(
                            fire,
                            lighter.Name ?? "someone",
                            traveler.GetDistanceToSqrt(fire),
                            ShortLabel(refusal),
                            OutdoorHotZonePolicy.IsHot(fire),
                            PlaceName(fire.Map, fire.Location)
                        )
                    );
                }
            }
        }

        if (entries.Count == 0)
        {
            traveler.SendMessage(
                RefusalHue,
                "None of your party has a campfire burning. Party members light one with Kindling, and you can travel to it with " +
                $"{Command} once it is secure."
            );
            return;
        }

        entries.Sort(static (a, b) => a.Distance.CompareTo(b.Distance));

        if (entries.Count > MaxListed)
        {
            entries.RemoveRange(MaxListed, entries.Count - MaxListed);
        }

        traveler.SendGump(new CampTravelListGump(entries));
    }

    private readonly record struct ListEntry(Campfire Fire, string LighterName, double Distance, string Label, bool Hot, string Place);

    /// <summary>A pick from the list: re-check, then ask for confirmation (with the Hot Zone warning when the camp is in one).</summary>
    private static void Select(PlayerMobile traveler, Campfire fire)
    {
        var facts = Gather(traveler, fire, out _);
        var refusal = Plan(Rules, facts);

        if (refusal != Refusal.None)
        {
            Refuse(traveler, refusal, facts);
            return;
        }

        if (_channels.ContainsKey(traveler))
        {
            traveler.SendMessage(RefusalHue, "You are already travelling.");
            return;
        }

        traveler.SendGump(
            new CampTravelConfirmGump(
                fire,
                LighterName(fire),
                facts.Capacity - facts.Arrivals,
                facts.Capacity,
                TravelWarningService.Applies(traveler, true, OutdoorHotZonePolicy.IsHot(fire))
            )
        );
    }

    private sealed class Channel
    {
        public required PlayerMobile Traveler { get; init; }
        public required Campfire Fire { get; init; }
        public required Point3D Start { get; init; }
        public required DateTime Until { get; init; }
        public int Hits { get; set; }
        public TimerExecutionToken Token;
    }

    private static readonly Dictionary<Mobile, Channel> _channels = [];

    private static void Begin(PlayerMobile traveler, Campfire fire)
    {
        var rules = Rules;
        var facts = Gather(traveler, fire, out _);
        var refusal = Plan(rules, facts);

        if (refusal != Refusal.None)
        {
            Refuse(traveler, refusal, facts);
            return;
        }

        if (_channels.ContainsKey(traveler))
        {
            traveler.SendMessage(RefusalHue, "You are already travelling.");
            return;
        }

        var channel = new Channel
        {
            Traveler = traveler,
            Fire = fire,
            Start = traveler.Location,
            Until = Core.Now + TimeSpan.FromSeconds(rules.ChannelSeconds),
            Hits = traveler.Hits
        };

        _channels[traveler] = channel;
        traveler.SendMessage(
            $"You prepare to travel to {LighterName(fire)}'s camp. Stand still for {rules.ChannelSeconds:0} seconds."
        );
        Server.Timer.StartTimer(
            TimeSpan.FromMilliseconds(250),
            TimeSpan.FromMilliseconds(250),
            () => Tick(channel),
            out channel.Token
        );
    }

    private static void Tick(Channel channel)
    {
        var traveler = channel.Traveler;

        if (_channels.GetValueOrDefault(traveler) != channel)
        {
            channel.Token.Cancel();
            return;
        }

        if (traveler.Deleted || !traveler.Alive || traveler.NetState is null)
        {
            Stop(channel, null);
            return;
        }

        if (traveler.Location != channel.Start)
        {
            Stop(channel, "You move, and the travel is cancelled.");
            return;
        }

        if (traveler.Hits < channel.Hits)
        {
            Stop(channel, "The pain breaks your concentration, and the travel is cancelled.");
            return;
        }

        channel.Hits = traveler.Hits;

        if (traveler.Spell is { IsCasting: true })
        {
            Stop(channel, "You cannot travel while casting.");
            return;
        }

        var facts = Gather(traveler, channel.Fire, out var arrival);
        var refusal = Plan(Rules, facts);

        if (refusal != Refusal.None)
        {
            Stop(channel, null);
            Refuse(traveler, refusal, facts);
            ShardAuditLog.Record("camp-travel", "refused", traveler, channel.Fire.Lighter, $"reason={refusal}");
            return;
        }

        if (Core.Now >= channel.Until)
        {
            Stop(channel, null);
            Arrive(traveler, channel.Fire, arrival, facts);
        }
    }

    private static void Stop(Channel channel, string? message)
    {
        channel.Token.Cancel();
        _channels.Remove(channel.Traveler);

        if (message is not null)
        {
            channel.Traveler.SendMessage(RefusalHue, message);
        }
    }

    private static void Arrive(PlayerMobile traveler, Campfire fire, Point3D arrival, TravelFacts facts)
    {
        var rules = Rules;
        var lighter = fire.Lighter!;
        var map = fire.Map!;

        if (traveler.Backpack?.ConsumeTotal(typeof(Kindling), rules.KindlingCost) == false)
        {
            Refuse(traveler, Refusal.NoKindling, facts);
            return;
        }

        var hot = OutdoorHotZonePolicy.IsHot(map, arrival);
        var warn = TravelWarningService.Applies(traveler, true, hot);
        var record = RecordOf(fire);

        record.Arrivals++;

        if (traveler.Account is Account account)
        {
            account.SetTag(
                CooldownTag,
                (Core.Now + TimeSpan.FromMinutes(rules.CooldownMinutes)).ToString("O", CultureInfo.InvariantCulture)
            );
        }

        BaseCreature.TeleportPets(traveler, arrival, map, true);
        traveler.PlaySound(ArrivalSound);
        traveler.MoveToWorld(arrival, map);
        traveler.PlaySound(ArrivalSound);

        traveler.SendMessage($"You arrive at {lighter.Name}'s camp.");

        if (warn)
        {
            traveler.SendMessage(RefusalHue, HotZoneWarning);
        }

        if (lighter.NetState is not null && lighter != traveler)
        {
            lighter.SendMessage(ArrivalNoticeText(traveler.Name ?? "A party member", record.Arrivals, facts.Capacity));
        }

        ShardAuditLog.Record(
            "camp-travel",
            "arrived",
            traveler,
            lighter,
            $"fire={fire.Serial}; places={record.Arrivals}/{facts.Capacity}; hot={hot}; kindling={rules.KindlingCost}"
        );
    }

    // ---- the gumps

    private sealed class CampTravelListGump : DynamicGump
    {
        private readonly List<ListEntry> _entries;

        public override bool Singleton => true;

        public CampTravelListGump(List<ListEntry> entries) : base(60, 60) => _entries = entries;

        protected override void BuildLayout(ref DynamicGumpBuilder builder)
        {
            var height = 90 + _entries.Count * 46;

            builder.AddPage();
            builder.AddBackground(0, 0, 480, height, 9200);
            builder.AddImageTiled(10, 10, 460, height - 20, 2624);
            builder.AddAlphaRegion(10, 10, 460, height - 20);
            builder.AddHtml(20, 18, 440, 20, "Travel to a party member's camp", "#FFD060", align: TextAlignment.Center);
            builder.AddHtml(20, 40, 440, 20, "Pick a camp. You will be asked to confirm.", "#CCCCCC", align: TextAlignment.Center);

            for (var i = 0; i < _entries.Count; i++)
            {
                var entry = _entries[i];
                var y = 70 + i * 46;

                builder.AddButton(20, y + 8, 4005, 4007, i + 1);
                builder.AddHtml(60, y, 280, 22, $"{entry.LighterName}'s camp: {entry.Label}", entry.Label == "ready" ? "#FFFFFF" : "#999999");
                builder.AddHtml(60, y + 22, 400, 20, $"{entry.Place}, {entry.Distance:0} tiles away", "#BBBBBB");

                if (entry.Hot)
                {
                    builder.AddHtml(350, y, 110, 22, "[HOT ZONE]", "#FF4040");
                }
            }
        }

        public override void OnResponse(NetState sender, in RelayInfo info)
        {
            var index = info.ButtonID - 1;

            if (sender.Mobile is PlayerMobile traveler && index >= 0 && index < _entries.Count)
            {
                Select(traveler, _entries[index].Fire);
            }
        }
    }

    private sealed class CampTravelConfirmGump : DynamicGump
    {
        private readonly Campfire _fire;
        private readonly string _name;
        private readonly int _left;
        private readonly int _capacity;
        private readonly bool _warn;

        public override bool Singleton => true;

        public CampTravelConfirmGump(Campfire fire, string name, int left, int capacity, bool warn) : base(80, 80)
        {
            _fire = fire;
            _name = name;
            _left = left;
            _capacity = capacity;
            _warn = warn;
        }

        protected override void BuildLayout(ref DynamicGumpBuilder builder)
        {
            var rules = Rules;
            var height = _warn ? 290 : 200;

            builder.AddPage();
            builder.AddBackground(0, 0, 420, height, 9200);
            builder.AddImageTiled(10, 10, 400, height - 20, 2624);
            builder.AddAlphaRegion(10, 10, 400, height - 20);
            builder.AddHtml(20, 18, 380, 20, $"Travel to {_name}'s camp?", "#FFD060", align: TextAlignment.Center);

            var y = 46;

            if (_warn)
            {
                builder.AddHtml(20, y, 380, 66, $"WARNING: {HotZoneWarning}", "#FF4040");
                y += 72;
            }

            builder.AddHtml(
                20,
                y,
                380,
                70,
                $"It costs {rules.KindlingCost} Kindling, and you cannot use camp travel again for {Span(TimeSpan.FromMinutes(rules.CooldownMinutes))}. " +
                $"Stand still for {rules.ChannelSeconds:0} seconds. Bonded pets beside you come too. {_left} of {_capacity} {Places(_capacity)} left at this camp.",
                "#FFFFFF"
            );

            if (_warn)
            {
                builder.AddCheckbox(20, height - 82, 210, 211, false, 1);
                builder.AddHtml(55, height - 80, 350, 36, TravelWarningService.CheckboxLabel, "#FFFFFF");
            }

            builder.AddButton(30, height - 45, 4005, 4007, 1);
            builder.AddHtml(70, height - 43, 120, 22, "Travel", "#FFFFFF");
            builder.AddButton(230, height - 45, 4005, 4007, 0);
            builder.AddHtml(270, height - 43, 120, 22, "Cancel", "#FFFFFF");
        }

        public override void OnResponse(NetState sender, in RelayInfo info)
        {
            if (info.ButtonID == 1 && sender.Mobile is PlayerMobile traveler)
            {
                if (_warn)
                {
                    TravelWarningService.ApplyChoice(traveler, info.IsSwitched(1));
                }

                Begin(traveler, _fire);
            }
        }
    }

    // ---- staff

    /// <summary>One line for [CampStatus: what travel makes of this fire.</summary>
    public static string DescribeFire(Campfire fire)
    {
        var rules = Rules;
        var capacity = CapacityOf(fire);
        var arrivals = _records.TryGetValue(fire, out var record) ? record.Arrivals : 0;
        var secure = IsSecure(rules, Core.Now - fire.CreatedAt, fire.Status == CampfireStatus.Off);

        return $"  travel: {(secure ? "secure" : "not secure")}, {arrivals} of {capacity} {Places(capacity)} used" +
               $"{(OutdoorHotZonePolicy.IsHot(fire) ? ", HOT ZONE" : string.Empty)}.";
    }

    public static IEnumerable<string> DescribeSettings(Mobile viewer)
    {
        var rules = Rules;

        yield return $"Camp travel (campingTravel): {(Enabled ? "on" : "off")}. Channel {rules.ChannelSeconds:0} s, cooldown {rules.CooldownMinutes:0} min, " +
                     $"cost {rules.KindlingCost} Kindling, secure after {rules.SecureSeconds:0} s, arrival within {rules.ArrivalRange} tiles. " +
                     $"Places: 1 at Camping {SkillForFirstPlace(rules):0}, +1 per {rules.SkillPerArrival:0} more, at most {rules.MaxArrivals}.";

        var remaining = CooldownRemaining((viewer.Account as Account)?.GetTag(CooldownTag), Core.Now);

        yield return remaining > TimeSpan.Zero
            ? $"Your camp travel is on cooldown for {Span(remaining)}."
            : "Your camp travel is ready.";
    }
}
