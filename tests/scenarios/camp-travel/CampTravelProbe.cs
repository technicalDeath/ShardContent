using System.Globalization;
using System.Reflection;
using System.Text.Json;
using BritanniaRenaissance.Content;
using Server;
using Server.Accounting;
using Server.Commands;
using Server.Engines.PartySystem;
using Server.Gumps;
using Server.Items;
using Server.Mobiles;
using Server.Regions;

namespace CampTravelTools;

// Test-only, disposable-host-only. Stages camp travel and Hot Zone travel warning checks and reports the result as JSON
// beside the host's Server.dll (campprobe-<hex serial>.json), so a driver reads authoritative server state.
//   [TestOnlyCamp <hex> skill <value>            Camping skill (the Value the game reads, which is Base plus a stat offset)
//   [TestOnlyCamp <hex> magic                    Magery 100, full mana, exactly 10 Recall scrolls
//   [TestOnlyCamp <hex> rune <x> <y> [<z>]       a marked Recall rune to that Felucca spot (ground level unless z is given), in the pack
//   [TestOnlyCamp <hex> gate <x> <y> [<z>]       a moongate one tile east of the player, to that Felucca spot
//   [TestOnlyCamp <hex> move <x> <y> [<z>]       move the player there (Felucca, ground level unless z is given)
//   [TestOnlyCamp <hex> fire                     a campfire lit by the player on their tile
//   [TestOnlyCamp <hex> gump list|confirm|confirmhot|hotzone   open that gump on the player's client (to look at it)
//   [TestOnlyCamp <hex> setpass <text>          set the account's password (disposable hosts only)
//   [TestOnlyCamp <hex> cmd <text>              run a player command as that player (e.g. [Welcome)
//   [TestOnlyCamp <hex> hurt <n>                 take n hits off the player (never below 1)
//   [TestOnlyCamp <hex> firekill                 delete every campfire
//   [TestOnlyCamp <hex> pgate                    a public moongate one tile east of the player
//   [TestOnlyCamp <hex> kindling <n>             exactly n Kindling in the pack
//   [TestOnlyCamp <hex> party <hex2> [<hex3>..]  a party led by the first serial (an existing party is disbanded)
//   [TestOnlyCamp <hex> leave                    the player leaves their party
//   [TestOnlyCamp <hex> cond <name> [<hex2>]     criminal | clear | combat <hex2> | heavy | light | paralyze | unparalyze
//   [TestOnlyCamp <hex> cooldown clear|<minutes> the account's camp travel cooldown
//   [TestOnlyCamp <hex> warning on|off           the account's Hot Zone travel warning choice
//   [TestOnlyCamp <hex> pet                      a bonded horse set to follow, one tile west
//   [TestOnlyCamp <hex> report                   state of the player, the account tags and every fire
public static class CampTravelProbe
{
    private static readonly Dictionary<Serial, Item> Heavy = [];

    public static void Configure() => CommandSystem.Register("TestOnlyCamp", AccessLevel.Administrator, OnCommand);

    private static void OnCommand(CommandEventArgs e)
    {
        if (e.Length < 2 || !TryHex(e.GetString(0), out var serial) ||
            World.FindMobile((Serial)serial) is not PlayerMobile player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyCamp <hex serial> <verb> ...");
            return;
        }

        var verb = e.GetString(1).ToLowerInvariant();
        var result = "ok";

        switch (verb)
        {
            case "skill":
                {
                    // The skill the game reads is Value, which adds a stat-based offset to Base, so aim Value at the target.
                    var camping = player.Skills[SkillName.Camping];
                    var target = double.Parse(e.GetString(2), CultureInfo.InvariantCulture);

                    camping.Base = 0.0;

                    var offset = camping.Value / 100.0;

                    camping.Base = Math.Clamp((target - 100.0 * offset) / (1.0 - offset), 0.0, 100.0);
                    result = $"value={camping.Value:0.0} base={camping.Base:0.0}";
                    break;
                }
            case "magic":
                player.Skills[SkillName.Magery].Base = 100.0;
                player.Mana = player.ManaMax;

                if (player.Backpack is { } bag)
                {
                    var old = new List<RecallScroll>();

                    foreach (var scroll in bag.FindItemsByType<RecallScroll>())
                    {
                        old.Add(scroll);
                    }

                    foreach (var scroll in old)
                    {
                        scroll.Delete();
                    }

                    bag.DropItem(new RecallScroll(10));
                }

                break;
            case "rune":
                {
                    var rune = new RecallRune
                    {
                        Marked = true,
                        Target = Ground(e),
                        TargetMap = Map.Felucca,
                        Description = "probe"
                    };

                    player.Backpack?.DropItem(rune);
                    result = $"rune={rune.Serial}";
                    break;
                }
            case "gate":
                {
                    var gate = new Moongate(Ground(e), Map.Felucca);

                    gate.MoveToWorld(new Point3D(player.X + 1, player.Y, player.Z), player.Map ?? Map.Felucca);
                    result = $"gate={gate.Serial} at {gate.X},{gate.Y},{gate.Z}";
                    break;
                }
            case "move":
                {
                    var x = Int(e, 2);
                    var y = Int(e, 3);
                    var z = e.Length > 4 ? Int(e, 4) : Map.Felucca.GetAverageZ(x, y);

                    player.MoveToWorld(new Point3D(x, y, z), Map.Felucca);
                    result = $"at {player.X},{player.Y},{player.Z}";
                    break;
                }
            case "fire":
                {
                    var fire = new Campfire(player);

                    fire.MoveToWorld(player.Location, player.Map ?? Map.Felucca);
                    result = $"fire={fire.Serial} at {fire.X},{fire.Y},{fire.Z}";
                    break;
                }
            case "gump":
                result = ShowGump(player, e.GetString(2));
                break;
            case "setpass":
                // For driving the real client by hand on a disposable host: a short password it can type.
                (player.Account as Account)?.SetPassword(e.GetString(2));
                break;
            case "cmd":
                // Runs a player command as that player, as if they had typed it (the text after the verb, e.g. [Welcome).
                CommandSystem.Handle(player, e.ArgString[(e.ArgString.IndexOf("cmd", StringComparison.Ordinal) + 4)..].Trim());
                result = "ran";
                break;
            case "hurt":
                player.Hits = Math.Max(1, player.Hits - Int(e, 2));
                break;
            case "firekill":
                {
                    var count = 0;

                    foreach (var fire in Campfire.Active.ToArray())
                    {
                        fire.Delete();
                        count++;
                    }

                    result = $"deleted {count} fires";
                    break;
                }
            case "pgate":
                {
                    var gate = new PublicMoongate();

                    gate.MoveToWorld(new Point3D(player.X + 1, player.Y, player.Z), player.Map ?? Map.Felucca);
                    result = $"pgate={gate.Serial}";
                    break;
                }
            case "kindling":
                {
                    var wanted = Int(e, 2);
                    var pack = player.Backpack!;

                    var existing = new List<Kindling>();

                    foreach (var item in pack.FindItemsByType<Kindling>())
                    {
                        existing.Add(item);
                    }

                    foreach (var item in existing)
                    {
                        item.Delete();
                    }

                    if (wanted > 0)
                    {
                        pack.DropItem(new Kindling(wanted));
                    }

                    break;
                }
            case "party":
                {
                    var members = new List<PlayerMobile> { player };

                    for (var i = 2; i < e.Length; i++)
                    {
                        if (TryHex(e.GetString(i), out var other) &&
                            World.FindMobile((Serial)other) is PlayerMobile member)
                        {
                            members.Add(member);
                        }
                    }

                    foreach (var member in members)
                    {
                        Party.Get(member)?.Disband();
                    }

                    var party = new Party(player);

                    player.Party = party;

                    foreach (var member in members.Skip(1))
                    {
                        party.Add(member);
                    }

                    result = $"party of {party.Count}";
                    break;
                }
            case "leave":
                {
                    var party = Party.Get(player);

                    if (party is null)
                    {
                        result = "no party";
                    }
                    else
                    {
                        party.Remove(player);
                        result = "left";
                    }

                    break;
                }
            case "cond":
                result = Condition(e, player);
                break;
            case "cooldown":
                {
                    if (player.Account is Account account)
                    {
                        var arg = e.GetString(2);

                        if (arg == "clear")
                        {
                            account.RemoveTag(CampTravelService.CooldownTag);
                        }
                        else
                        {
                            account.SetTag(
                                CampTravelService.CooldownTag,
                                (Core.Now + TimeSpan.FromMinutes(double.Parse(arg, CultureInfo.InvariantCulture)))
                                .ToString("O", CultureInfo.InvariantCulture)
                            );
                        }
                    }

                    break;
                }
            case "warning":
                TravelWarningService.SetSuppressed(player, e.GetString(2) == "off");
                break;
            case "pet":
                {
                    var horse = new Horse { Controlled = true, ControlMaster = player, IsBonded = true };

                    horse.MoveToWorld(new Point3D(player.X - 1, player.Y, player.Z), player.Map ?? Map.Felucca);
                    horse.IssueOrder(OrderType.Follow, player, player);
                    result = $"pet={horse.Serial}";
                    break;
                }
            case "report":
                break;
            default:
                e.Mobile.SendMessage($"Unknown verb {verb}.");
                return;
        }

        Write(player);
        e.Mobile.SendMessage($"TestOnlyCamp {verb}: {result}");
    }

    // The gumps are private to the shard assembly; a test-only probe builds them by reflection so a real client can show them.
    private static string ShowGump(PlayerMobile player, string which)
    {
        var flags = BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.Instance;

        switch (which)
        {
            case "list":
                CommandSystem.Handle(player, "[CampTravel");
                return "list requested";
            case "confirm":
            case "confirmhot":
                {
                    var fire = Campfire.Active.FirstOrDefault(f => f.Lighter is not null && f.Lighter != player);

                    if (fire is null)
                    {
                        return "no fire lit by someone else";
                    }

                    var type = typeof(CampTravelService).GetNestedType("CampTravelConfirmGump", BindingFlags.NonPublic)!;
                    var gump = Activator.CreateInstance(type, flags, null, [fire, fire.Lighter!.Name ?? "someone", 1, 2, which == "confirmhot"], null)!;

                    player.SendGump((BaseGump)gump);
                    return which;
                }
            case "hotzone":
                {
                    var type = typeof(TravelWarningService).GetNestedType("HotZoneTravelGump", BindingFlags.NonPublic)!;
                    var gump = Activator.CreateInstance(type, flags, null, [(Action)(() => { }), Core.Now + TimeSpan.FromMinutes(2)], null)!;

                    player.SendGump((BaseGump)gump);
                    return which;
                }
            default:
                return "unknown gump";
        }
    }

    private static bool TryHex(string text, out uint value) =>
        uint.TryParse(
            text.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? text[2..] : text,
            NumberStyles.HexNumber,
            null,
            out value
        );

    private static Point3D Ground(CommandEventArgs e) =>
        new(Int(e, 2), Int(e, 3), e.Length > 4 ? Int(e, 4) : Map.Felucca.GetAverageZ(Int(e, 2), Int(e, 3)));

    private static int Int(CommandEventArgs e, int index) => int.Parse(e.GetString(index), CultureInfo.InvariantCulture);

    private static string Condition(CommandEventArgs e, PlayerMobile player)
    {
        switch (e.GetString(2).ToLowerInvariant())
        {
            case "criminal":
                player.Criminal = true;
                return "criminal";
            case "clear":
                player.Criminal = false;
                player.Aggressed.Clear();
                player.Aggressors.Clear();
                return "cleared";
            case "combat":
                if (TryHex(e.GetString(3), out var other) &&
                    World.FindMobile((Serial)other) is PlayerMobile victim)
                {
                    player.Aggressed.Add(AggressorInfo.Create(player, victim, false));
                    return $"in combat with {victim.Name}";
                }

                return "no such target";
            case "heavy":
                {
                    var load = new Item(0x1BF2) { Weight = 600.0 };

                    player.Backpack!.DropItem(load);
                    Heavy[player.Serial] = load;
                    return "heavy";
                }
            case "light":
                if (Heavy.Remove(player.Serial, out var item))
                {
                    item.Delete();
                }

                return "light";
            case "paralyze":
                player.Frozen = true;
                return "frozen";
            case "unparalyze":
                player.Frozen = false;
                return "unfrozen";
            default:
                return "unknown condition";
        }
    }

    private static void Write(PlayerMobile player)
    {
        var rules = ShardRulesConfiguration.Settings;
        var account = player.Account as Account;
        var party = Party.Get(player);
        var kindling = 0;
        var scrolls = 0;

        if (player.Backpack is { } pack)
        {
            foreach (var item in pack.FindItemsByType<Kindling>())
            {
                kindling += item.Amount;
            }

            foreach (var item in pack.FindItemsByType<RecallScroll>())
            {
                scrolls += item.Amount;
            }
        }

        var pets = new List<object>();

        foreach (var follower in player.AllFollowers ?? [])
        {
            pets.Add(
                new
                {
                    serial = follower.Serial.Value,
                    x = follower.X,
                    y = follower.Y,
                    map = follower.Map?.Name,
                    order = (follower as BaseCreature)?.ControlOrder.ToString(),
                    bonded = (follower as BaseCreature)?.IsBonded
                }
            );
        }

        var fires = new List<object>();

        foreach (var fire in Campfire.Active)
        {
            fires.Add(
                new
                {
                    serial = fire.Serial.Value,
                    x = fire.X,
                    y = fire.Y,
                    lighter = fire.Lighter?.Serial.Value ?? 0u,
                    status = fire.Status.ToString(),
                    arrivals = CampTravelService.ArrivalsOf(fire),
                    secure = CampTravelService.IsSecure(fire),
                    hot = OutdoorHotZonePolicy.IsHot(fire)
                }
            );
        }

        var report = new
        {
            serial = player.Serial.Value,
            x = player.X,
            y = player.Y,
            z = player.Z,
            map = player.Map?.Name,
            hits = player.Hits,
            mana = player.Mana,
            alive = player.Alive,
            camping = player.Skills[SkillName.Camping].Value,
            kindling,
            recallScrolls = scrolls,
            criminal = player.Criminal,
            hot = OutdoorHotZonePolicy.IsHot(player),
            region = player.Region?.Name,
            dungeon = player.Region?.GetRegion<DungeonRegion>() is not null,
            cooldownTag = account?.GetTag(CampTravelService.CooldownTag),
            warningTag = account?.GetTag("HotZoneTravelWarning"),
            party = party?.Members.Select(m => m.Mobile.Serial.Value).ToArray() ?? [],
            flags = new
            {
                campingTravel = rules?.FeatureFlags.CampingTravel,
                hotZoneTravelWarning = rules?.FeatureFlags.HotZoneTravelWarning
            },
            pets,
            fires
        };

        File.WriteAllText(
            Path.Combine(Core.BaseDirectory, $"campprobe-{player.Serial.Value:X}.json"),
            JsonSerializer.Serialize(report)
        );
    }
}
