using System.Globalization;
using System.Reflection;
using BritanniaRenaissance.Content;
using Server;
using Server.Commands;
using Server.Gumps;
using Server.Items;
using Server.Misc;
using Server.Mobiles;
using Server.Accounting;

namespace Alpha3TestOnlyTools;

// Test-only, disposable-host-only. Reusable across Alpha 3 letters: several feature flags are
// validator-rejected outright in ShardRulesConfiguration.Validate (currently
// alpha3StarterCraftMaterials, alpha3StarterCombatGear, housingGeography, expeditions, pilgrimage,
// roadSpeed, retentionContent, coolZones), so they can never be true in shard-rules.json, not even
// on a disposable host - Load() throws before the server starts. TestOnlyFlagOverride flips an
// already-loaded flag's in-memory value directly, after Load()'s validation already passed with it
// false, so an ordinary gameplay packet can exercise the gated code path. Never touches disk;
// discarded on restart. Pair with New-TestCharacter.ps1's -NoRestart switch so the override
// survives across every character you create with it. TestOnlyInventoryInspect reports a player's
// items authoritatively from the server side (type, amount, LootType, Nontransferable), instead of
// relying on client tooltip text.
public static class TestOnlyProbe
{
    public static void Configure()
    {
        CommandSystem.Register("TestOnlyFlagOverride", AccessLevel.Administrator, OnFlagCommand);
        CommandSystem.Register("TestOnlyInventoryInspect", AccessLevel.Administrator, OnInspectCommand);
        CommandSystem.Register("TestOnlyCorpseAggressors", AccessLevel.Administrator, OnCorpseAggressorsCommand);
        CommandSystem.Register("TestOnlyCorpseInventory", AccessLevel.Administrator, OnCorpseInventoryCommand);
        CommandSystem.Register("TestOnlyReportFlags", AccessLevel.Administrator, OnReportFlagsCommand);
        CommandSystem.Register("TestOnlySkillBankSeed", AccessLevel.Administrator, OnSkillBankSeedCommand);
        CommandSystem.Register("TestOnlyDoubleClick", AccessLevel.Administrator, OnDoubleClickCommand);
        CommandSystem.Register("TestOnlySkillUse", AccessLevel.Administrator, OnSkillUseCommand);
        CommandSystem.Register("TestOnlyFaintAge", AccessLevel.Administrator, OnFaintAgeCommand);
        CommandSystem.Register("TestOnlySkillCap", AccessLevel.Administrator, OnSkillCapCommand);
        CommandSystem.Register("TestOnlyBuff", AccessLevel.Administrator, OnBuffCommand);
        CommandSystem.Register("TestOnlyBuffOff", AccessLevel.Administrator, OnBuffOffCommand);
        CommandSystem.Register("TestOnlyTabs", AccessLevel.Administrator, e => FindPlayer(e)?.SendGump(new TabArtProbe()));
        CommandSystem.Register("TestOnlyGump", AccessLevel.Administrator, OnGumpCommand);
        CommandSystem.Register("TestOnlyShow", AccessLevel.Administrator, OnShowCommand);
        CommandSystem.Register("TestOnlyMage", AccessLevel.Administrator, OnMageCommand);
        CommandSystem.Register("TestOnlyCast", AccessLevel.Administrator, OnCastCommand);
        CommandSystem.Register("TestOnlyState", AccessLevel.Administrator, OnStateCommand);
        CommandSystem.Register("TestOnlyFires", AccessLevel.Administrator, OnFiresCommand);
        CommandSystem.Register("TestOnlyGuild", AccessLevel.Administrator, OnGuildCommand);
    }

    // [TestOnlyGuild <leader-serial> <name> [member-serial ...]] founds an old-system guild (no guildstone) with that leader and members, for the guild
    // chat live checks; [TestOnlyGuild <serial> none] takes that player out of their guild. Reports "Guild <name> members=<n>" or "Guild none".
    private static void OnGuildCommand(CommandEventArgs e)
    {
        if (FindPlayer(e) is not { } player || e.Length < 2)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyGuild <leader-serial> <name> [member-serial ...]  or  [TestOnlyGuild <serial> none");
            return;
        }

        if (e.GetString(1).Equals("none", StringComparison.OrdinalIgnoreCase))
        {
            (player.Guild as Server.Guilds.Guild)?.RemoveMember(player);
            e.Mobile.SendMessage("Guild none");
            return;
        }

        var name = e.GetString(1);
        var guild = new Server.Guilds.Guild(player, name, name.Length > 3 ? name[..3] : name);

        player.Guild = guild;

        for (var i = 2; i < e.Length; i++)
        {
            var raw = e.GetString(i);
            var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;

            if (uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) && World.FindMobile((Serial)serial) is { } member)
            {
                guild.AddMember(member);
            }
        }

        e.Mobile.SendMessage($"Guild {name} members={guild.Members.Count}");
    }

    // [TestOnlyFires <player-serial> <hue> [hue ...]] lights one campfire per hue in a grid around the player, four to a row and three tiles apart
    // (so the grid reads as straight rows on the screen), with the hue number labelled over each; [TestOnlyFires <player-serial> clear] puts every
    // fire out. For choosing the blue of a travel fire in the real client (Camp-Travel-Blue-Fire-Proposal.md section 4).
    private static void OnFiresCommand(CommandEventArgs e)
    {
        if (FindPlayer(e) is not { Map: { } map } player || e.Length < 2)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyFires <player-serial> <hue> [hue ...]  or  [TestOnlyFires <player-serial> clear");
            return;
        }

        if (e.GetString(1).Equals("clear", StringComparison.OrdinalIgnoreCase))
        {
            foreach (var fire in Campfire.Active.ToArray())
            {
                fire.Delete();
            }

            e.Mobile.SendMessage("Fires put out.");
            return;
        }

        // [TestOnlyFires <player-serial> flat] moves the player to the middle of the nearest bare, level, dry 25 x 25 patch of open ground.
        if (e.GetString(1).Equals("flat", StringComparison.OrdinalIgnoreCase))
        {
            const int Half = 12;
            var candidates = new List<(int X, int Y)>();

            for (var dx = -150; dx <= 150; dx += 5)
            {
                for (var dy = -150; dy <= 150; dy += 5)
                {
                    candidates.Add((player.X + dx, player.Y + dy));
                }
            }

            candidates.Sort((a, b) => (Math.Abs(a.X - player.X) + Math.Abs(a.Y - player.Y)).CompareTo(Math.Abs(b.X - player.X) + Math.Abs(b.Y - player.Y)));

            foreach (var (cx, cy) in candidates)
            {
                if (cx - Half < 0 || cy - Half < 0 || cx + Half >= map.Width || cy + Half >= map.Height)
                {
                    continue;
                }

                var z = map.Tiles.GetLandTile(cx, cy).Z;
                var clear = true;

                for (var x = cx - Half; x <= cx + Half && clear; x++)
                {
                    for (var y = cy - Half; y <= cy + Half && clear; y++)
                    {
                        var land = map.Tiles.GetLandTile(x, y);
                        var flags = TileData.LandTable[land.ID & TileData.MaxLandValue].Flags;

                        clear = land.Z == z && (flags & (TileFlag.Impassable | TileFlag.Wet)) == 0;

                        // Decoration (leaves, bones, small plants) does not count; walls, floors, doors, trees and roofs do.
                        foreach (var stat in map.Tiles.GetStaticTiles(x, y))
                        {
                            const TileFlag Blocking = TileFlag.Impassable | TileFlag.Surface | TileFlag.Wall | TileFlag.Window | TileFlag.Roof | TileFlag.Foliage |
                                                      TileFlag.Door | TileFlag.Bridge | TileFlag.Wet;

                            if ((TileData.ItemTable[stat.ID & TileData.MaxItemValue].Flags & Blocking) != 0)
                            {
                                clear = false;
                                break;
                            }
                        }
                    }
                }

                if (clear)
                {
                    player.MoveToWorld(new Point3D(cx, cy, z), map);
                    e.Mobile.SendMessage($"Level open ground at {cx},{cy},{z}.");
                    return;
                }
            }

            e.Mobile.SendMessage("No level open ground within 150 tiles.");
            return;
        }

        // [TestOnlyFires <player-serial> step <n> <hue> ...] sets the tiles between fires (three if not given).
        const int Columns = 4;
        var step = 3;
        var first = 1;

        if (e.GetString(1).Equals("step", StringComparison.OrdinalIgnoreCase) && e.Length > 3 && int.TryParse(e.GetString(2), out var tiles) && tiles > 0)
        {
            step = tiles;
            first = 3;
        }

        var hues = new List<int>();

        for (var i = first; i < e.Length; i++)
        {
            if (int.TryParse(e.GetString(i), out var hue))
            {
                hues.Add(hue);
            }
        }

        var centre = (Columns - 1) * step / 2;

        for (var k = 0; k < hues.Count; k++)
        {
            // On screen, (+x, -y) runs right and (+x, +y) runs down.
            var across = k % Columns * step - centre;
            var down = k / Columns * step - centre;
            var x = player.X + across + down;
            var y = player.Y - across + down;
            var fire = new Campfire(player) { Hue = hues[k] };

            fire.MoveToWorld(new Point3D(x, y, map.GetAverageZ(x, y)), map);
            fire.LabelTo(player, hues[k].ToString(CultureInfo.InvariantCulture));
        }

        e.Mobile.SendMessage($"Lit {hues.Count} fires.");
    }

    // [TestOnlyBuff <player-serial> <BuffIcon> <titleCliloc> <secondaryCliloc> <seconds> [text ...]] adds a buff icon to the player, for the
    // buff-icon spike: which stock art stands for which shard state, and whether a generic argument cliloc shows custom text in the client.
    // Needs buffIcons.enable true on the host. Reports "Buff <icon> title=<n> secondary=<n> seconds=<n> text=<text>".
    private static void OnBuffCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player ||
            e.Length < 5 || !Enum.TryParse<Server.Engines.BuffIcons.BuffIcon>(e.GetString(1), true, out var icon) ||
            !int.TryParse(e.GetString(2), out var title) || !int.TryParse(e.GetString(3), out var secondary) ||
            !int.TryParse(e.GetString(4), out var seconds))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyBuff <player-serial> <BuffIcon> <titleCliloc> <secondaryCliloc> <seconds> [text ...]");
            return;
        }

        var text = e.Length > 5 ? string.Join(' ', Enumerable.Range(5, e.Length - 5).Select(e.GetString)) : null;
        player.AddBuff(new Server.Engines.BuffIcons.BuffInfo(icon, title, secondary, TimeSpan.FromSeconds(seconds), text));
        e.Mobile.SendMessage($"Buff {icon} title={title} secondary={secondary} seconds={seconds} text={text}");
    }

    // [TestOnlyShow <player-serial> <window> [argument]] opens one of the shard's real windows on that player's client, including the ones a
    // normal play-through reaches only with a party, a campfire or a Recall into a Hot Zone, so a window can be photographed before and after
    // a restyle with the same command. Windows: welcome [topic-key], skillclasses, intent, travelwarning, ward, skillbank, discard [skill-id],
    // mastery, camplist, campconfirm, campconfirmhot, hotzone.
    private static void OnShowCommand(CommandEventArgs e)
    {
        if (FindPlayer(e) is not { } player || e.Length < 2)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyShow <player-serial> <window> [argument]");
            return;
        }

        const System.Reflection.BindingFlags Hidden = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public;
        var arg = e.Length > 2 ? e.GetString(2) : null;
        var camp = typeof(CampTravelService);

        switch (e.GetString(1).ToLowerInvariant())
        {
            case "welcome":
                WelcomeGuide.Open(player, arg);
                break;
            case "skillclasses":
                SkillClassesGump.Open(player);
                break;
            case "intent":
                StatusWindows.OpenIntent(player);
                break;
            case "travelwarning":
                StatusWindows.OpenTravelWarning(player);
                break;
            case "ward":
                StatusWindows.OpenWard(
                    player, true, WardPhase.Primed,
                    ["Status: Primed. Your Ward is watching your backpack.", "A thief it detects cannot steal from you again until it has run its course."]
                );
                break;
            case "skillbank":
                SkillBankGump.Open(player, 0, arg);
                break;
            case "discard":
                SkillBankDiscardGump.Open(player, int.TryParse(arg, out var skillId) ? skillId : 0, 0);
                break;
            case "mastery":
                MasteryGump.Open(player, player);
                break;
            case "camplist":
            {
                var entryType = camp.GetNestedType("ListEntry", Hidden)!;
                var list = Activator.CreateInstance(typeof(List<>).MakeGenericType(entryType))!;
                var add = list.GetType().GetMethod("Add")!;

                foreach (var (name, distance, label, hot, place) in new[]
                         {
                             ("Rowan", 9.0, "ready", false, "Britain"), ("Tessa", 41.0, "ready", true, "Buccaneer's Den island"),
                             ("Bram", 17.0, "securing", false, "Yew"), ("Ilsa", 63.0, "full", false, "Minoc")
                         })
                {
                    add.Invoke(list, [Activator.CreateInstance(entryType, [null, name, distance, label, hot, place])]);
                }

                player.SendGump((BaseGump)Activator.CreateInstance(camp.GetNestedType("CampTravelListGump", Hidden)!, list)!);
                break;
            }
            case "campconfirm":
            case "campconfirmhot":
                player.SendGump(
                    (BaseGump)Activator.CreateInstance(
                        camp.GetNestedType("CampTravelConfirmGump", Hidden)!, [null, "Rowan", 3, 4, e.GetString(1).EndsWith("hot", StringComparison.OrdinalIgnoreCase)]
                    )!
                );
                break;
            case "hotzone":
                player.SendGump(
                    (BaseGump)Activator.CreateInstance(
                        typeof(TravelWarningService).GetNestedType("HotZoneTravelGump", Hidden)!, [new Action(static () => { }), Core.Now.AddMinutes(2)]
                    )!
                );
                break;
            default:
                e.Mobile.SendMessage("Unknown window.");
                return;
        }

        e.Mobile.SendMessage($"Window {e.GetString(1)} shown to {player.Name}");
    }

    // [TestOnlyGump <player-serial> <script-name>] draws the gump described by <script-name>.gs (see GumpScriptProbe) on that player's client.
    private static void OnGumpCommand(CommandEventArgs e)
    {
        if (FindPlayer(e) is not { } player || e.Length < 2)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyGump <player-serial> <script-name>");
            return;
        }

        var gump = GumpScriptProbe.Load(e.GetString(1), out var error);

        if (gump is null)
        {
            e.Mobile.SendMessage(error);
            return;
        }

        player.SendGump(gump);
        e.Mobile.SendMessage($"Gump {e.GetString(1)} sent to {player.Name}");
    }

    private static PlayerMobile? FindPlayer(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        return uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) ? World.FindMobile((Serial)serial) as PlayerMobile : null;
    }

    // [TestOnlyMage <player-serial>] makes the player a caster for the buff-bar check: Magery and Evaluating Intelligence 100, full mana, a
    // spellbook with every Magery spell and a stack of every reagent in the backpack. Nothing here ships.
    private static void OnMageCommand(CommandEventArgs e)
    {
        if (FindPlayer(e) is not { } player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyMage <player-serial>");
            return;
        }

        player.Skills[SkillName.Magery].Base = 100.0;
        player.Skills[SkillName.EvalInt].Base = 100.0;
        player.RawInt = 100;
        player.Mana = player.ManaMax;
        player.AddToBackpack(new Spellbook(ulong.MaxValue));
        player.AddToBackpack(new BlackPearl(50));
        player.AddToBackpack(new Bloodmoss(50));
        player.AddToBackpack(new Garlic(50));
        player.AddToBackpack(new Ginseng(50));
        player.AddToBackpack(new MandrakeRoot(50));
        player.AddToBackpack(new Nightshade(50));
        player.AddToBackpack(new SulfurousAsh(50));
        player.AddToBackpack(new SpidersSilk(50));
        e.Mobile.SendMessage($"Mage {player.Name}: Magery {player.Skills[SkillName.Magery].Base}, mana {player.Mana}/{player.ManaMax}");
    }

    // [TestOnlyCast <player-serial> <SpellName>] starts a stock spell for the player through the engine's normal path (cast delay, then the
    // target cursor goes to their client). Reports whether the cast started.
    private static void OnCastCommand(CommandEventArgs e)
    {
        if (FindPlayer(e) is not { } player || e.Length < 2)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyCast <player-serial> <SpellName>");
            return;
        }

        var spell = Server.Spells.SpellRegistry.NewSpell(e.GetString(1), player, null);
        e.Mobile.SendMessage(spell is null ? $"Cast {e.GetString(1)}: no such spell" : $"Cast {e.GetString(1)}: started={spell.Cast()}");
    }

    // [TestOnlyState <player-serial> <what> [argument]] puts a test character into a state the buff bar shows, for the buff-icon check:
    // poison <Lesser|Regular|Greater|Deadly|Lethal> | curepoison | body <id> | criminal <on|off> | ward <primed|activated|reset> |
    // ko <on|off> | koattacker <serial> | kofrom <serial> | polymorph <body> | endpolymorph | kill | resurrect | cleardefense (ends Protection, Reactive Armor, Magic Reflect and Arch Protection) | describe (lists what the watch shows).
    private static void OnStateCommand(CommandEventArgs e)
    {
        if (FindPlayer(e) is not { } player || e.Length < 2)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyState <player-serial> <what> [argument]");
            return;
        }

        var what = e.GetString(1).ToLowerInvariant();
        var arg = e.Length > 2 ? e.GetString(2).ToLowerInvariant() : "";

        switch (what)
        {
            case "poison":
                var level = arg switch
                {
                    "regular" => Poison.Regular,
                    "greater" => Poison.Greater,
                    "deadly" => Poison.Deadly,
                    "lethal" => Poison.Lethal,
                    _ => Poison.Lesser
                };
                player.ApplyPoison(player, level);
                break;
            case "curepoison":
                player.Poison = null;
                break;
            case "body":
                player.BodyMod = int.TryParse(arg, out var body) ? body : 0;
                break;
            case "criminal":
                player.Criminal = arg != "off";
                break;
            case "ward":
                var ward = BackpackWardService.FindWard(player);
                if (ward is null)
                {
                    e.Mobile.SendMessage("No Backpack Ward in that pack.");
                    return;
                }

                if (arg == "reset")
                {
                    ward.State.Reset();
                }
                else
                {
                    ward.State.Prime(player.Serial.Value, Core.Now);

                    if (arg == "activated")
                    {
                        ward.State.Activate(Core.Now);
                        ward.State.MarkCaught("test-thief");
                    }
                }

                break;
            case "ko":
                if (player.Account is Account account)
                {
                    var key = "BritanniaRenaissance.KnockedOut.UntilUtc." + player.Serial.Value.ToString("X8", CultureInfo.InvariantCulture);

                    if (arg == "off")
                    {
                        account.RemoveTag(key);
                    }
                    else
                    {
                        account.SetTag(key, Core.Now.AddSeconds(90).ToUniversalTime().ToString("O", CultureInfo.InvariantCulture));
                    }
                }

                break;
            case "koattacker":
                // Records who knocked the player out (arg: that character's serial, hex), so that character has the right to execute them.
                if (player.Account is Account koAccount && uint.TryParse(arg.Replace("0x", ""), NumberStyles.HexNumber, null, out var attackerSerial))
                {
                    koAccount.SetTag(
                        "BritanniaRenaissance.KnockedOut.Attacker." + player.Serial.Value.ToString("X8", CultureInfo.InvariantCulture),
                        attackerSerial.ToString(CultureInfo.InvariantCulture)
                    );
                }

                break;
            case "kofrom":
                // The real Knocked Out entry (timers, countdown labels, recorded attacker), as a lethal blow from that character (arg: serial, hex)
                // would cause it; for real-client checks where the attacker is a person at a keyboard and cannot land the blow on cue.
                if (uint.TryParse(arg.Replace("0x", ""), NumberStyles.HexNumber, null, out var koFrom) && World.FindMobile((Serial)koFrom) is { } koAttacker)
                {
                    e.Mobile.SendMessage($"KnockedOut entered={KnockedOutService.TryInterceptLethalDamage(player, koAttacker, 1000)}");
                }

                break;
            case "cleardefense":
                player.MeleeDamageAbsorb = 0;
                player.MagicDamageAbsorb = 0;
                Server.Spells.Second.ProtectionSpell.Registry.Remove(player);
                Server.Spells.Fourth.ArchProtectionSpell.RemoveEntry(player);
                player.EndAction<DefensiveSpell>();
                break;
            case "polymorph":
                e.Mobile.SendMessage(
                    $"Polymorph started={new Server.Spells.Seventh.PolymorphSpell(player, null, int.TryParse(arg, out var form) ? form : 5).Cast()}"
                );
                return;
            case "endpolymorph":
                Server.Spells.Seventh.PolymorphSpell.EndPolymorph(player);
                break;
            case "kill":
                player.Kill();
                break;
            case "resurrect":
                player.Resurrect();
                break;
            case "describe":
                foreach (var line in BuffIconService.Describe(player))
                {
                    e.Mobile.SendMessage(line);
                }

                return;
            default:
                e.Mobile.SendMessage($"Unknown state '{what}'.");
                return;
        }

        e.Mobile.SendMessage($"State {what} {arg}: done.");
    }

    // [TestOnlyBuffOff <player-serial> <BuffIcon>] removes one buff icon.
    private static void OnBuffOffCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player ||
            e.Length < 2 || !Enum.TryParse<Server.Engines.BuffIcons.BuffIcon>(e.GetString(1), true, out var icon))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyBuffOff <player-serial> <BuffIcon>");
            return;
        }

        player.RemoveBuff(icon);
        e.Mobile.SendMessage($"BuffOff {icon}");
    }

    // [TestOnlySkillUse <player-serial> <Skill> <count>] makes that many skill checks that always succeed, each at a place the anti-macro
    // check has not seen, so every one reaches the gain hook (Skill Bank, Faint Memories, Mastery, then the stock roll) the way a real use
    // does. Count 0 only reports. Reports "SkillUse <Skill> before=<tenths> after=<tenths> lock=<Up|Down|Locked> total=<tenths>/<cap>".
    private static void OnSkillUseCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player ||
            e.Length < 3 || !Enum.TryParse<SkillName>(e.GetString(1), true, out var name) || !int.TryParse(e.GetString(2), out var count))
        {
            e.Mobile.SendMessage("Usage: [TestOnlySkillUse <player-serial> <Skill> <count>");
            return;
        }

        var skill = player.Skills[name];
        var before = skill.BaseFixedPoint;

        for (var i = 0; i < count; i++)
        {
            SkillCheck.CheckSkill(player, skill, new object(), 1.0);
        }

        e.Mobile.SendMessage($"SkillUse {name} before={before} after={skill.BaseFixedPoint} lock={skill.Lock} total={player.Skills.Total}/{player.Skills.Cap}");
    }

    // [TestOnlySkillCap <player-serial> <tenths>] sets the character's total skill cap, so the "at the cap" cases need no 700 points of skills.
    // Reports "SkillCap <tenths> total=<tenths>".
    private static void OnSkillCapCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player ||
            e.Length < 2 || !int.TryParse(e.GetString(1), out var cap) || cap <= 0)
        {
            e.Mobile.SendMessage("Usage: [TestOnlySkillCap <player-serial> <tenths>");
            return;
        }

        player.Skills.Cap = cap;
        e.Mobile.SendMessage($"SkillCap {player.Skills.Cap} total={player.Skills.Total}");
    }

    // [TestOnlyFaintAge <player-serial> <hours>] moves the character's Faint Memories grant that far into the past, so the wait can be
    // rehearsed without waiting. Reports "FaintAge remaining=<tenths> granted=<UTC>".
    private static void OnFaintAgeCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player ||
            player.Account is not Account account || e.Length < 2 ||
            !double.TryParse(e.GetString(1), NumberStyles.Float, CultureInfo.InvariantCulture, out var hours) ||
            !FaintMemoriesService.TryLoad(player, out var state))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyFaintAge <player-serial> <hours> (the character must have Faint Memories)");
            return;
        }

        state = state with { GrantedUtc = state.GrantedUtc.AddHours(-hours) };
        account.SetTag("BritanniaRenaissance.FaintMemories.v1." + player.Serial.Value.ToString("X8", CultureInfo.InvariantCulture), FaintMemoriesPolicy.Serialize(state));
        e.Mobile.SendMessage($"FaintAge remaining={state.RemainingTenths} granted={state.GrantedUtc:u}");
    }

    // [TestOnlyDoubleClick <player-serial> <ItemTypeName>] double-clicks the first item of that type in the player's backpack for them (a
    // player's client does the same when they double-click it), so what that opens can be checked without finding the item on screen.
    private static void OnDoubleClickCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (e.Length < 2 || !uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyDoubleClick <player-serial> <ItemTypeName>");
            return;
        }

        Item? item = null;

        if (player.Backpack is { } pack)
        {
            foreach (var held in pack.FindItemsByType<Item>(true))
            {
                if (held.GetType().Name == e.GetString(1))
                {
                    item = held;
                    break;
                }
            }
        }

        if (item is null)
        {
            e.Mobile.SendMessage($"DoubleClick {e.GetString(1)} none");
            return;
        }

        item.OnDoubleClick(player);
        e.Mobile.SendMessage($"DoubleClick {e.GetString(1)} done");
    }

    // [TestOnlySkillBankSeed <player-serial> [+] Anatomy=35 Hiding=12:down ...] replaces the player's Skill Bank with these entries (tenths of
    // a point, optionally set Down), or with "+" adds to what is there (a typed line is short, so a long bank is seeded in pieces), so the
    // [SkillBank window can be looked at with something in it. Reports "SkillBankSeed player=<name> total=<tenths> entries=<n>".
    private static void OnSkillBankSeedCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlySkillBankSeed <player-serial> Skill=tenths[:down] ...");
            return;
        }

        var capacity = ShardRulesConfiguration.Settings!.SkillBank.CapacityTenths;
        var add = e.Length > 1 && e.GetString(1) == "+";
        var ledger = new SkillBankLedger(capacity);

        if (add && !SkillBankLedger.TryDeserialize(player.SkillBankData, capacity, id => (player.Skills[id].Info.Name, player.Skills[id].CapFixedPoint), out ledger))
        {
            ledger = new SkillBankLedger(capacity);
        }

        var entries = 0;

        for (var i = add ? 2 : 1; i < e.Length; i++)
        {
            var parts = e.GetString(i).Split('=', 2);
            var amount = parts.Length == 2 ? parts[1].Split(':') : [];

            if (amount.Length == 0 || !Enum.TryParse<SkillName>(parts[0], true, out var name) || !int.TryParse(amount[0], out var tenths))
            {
                e.Mobile.SendMessage($"Skipped '{e.GetString(i)}'.");
                continue;
            }

            var skill = player.Skills[(int)name];
            ledger.Deposit((int)name, skill.Info.Name, tenths, skill.CapFixedPoint);

            if (amount.Length > 1 && amount[1].Equals("down", StringComparison.OrdinalIgnoreCase))
            {
                ledger.SetRetention((int)name, BankRetention.Down);
            }

            entries++;
        }

        player.SkillBankData = ledger.Serialize();
        e.Mobile.SendMessage($"SkillBankSeed player={player.Name} total={ledger.TotalTenths} entries={entries}");
    }

    // Reports a mobile's aggressor records, "ReportFlags target=<name> aggressors=<attacker>:can=<0|1>:crim=<0|1>:rep=<0|1>,...|none":
    // can = the murder report would be offered for that attacker if the mobile died now, crim = the attacker's last hit was criminal,
    // rep = already reported. For watching how a fight moves the stock report flag.
    private static void OnReportFlagsCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyReportFlags <mobile-serial>");
            return;
        }

        if (World.FindMobile((Serial)serial) is not { } target)
        {
            e.Mobile.SendMessage($"ReportFlags target={serial:X} aggressors=unknown");
            return;
        }

        var rows = target.Aggressors
            .Select(i => $"{i.Attacker.Name}:can={(i.CanReportMurder ? 1 : 0)}:crim={(i.CriminalAggression ? 1 : 0)}:rep={(i.Reported ? 1 : 0)}")
            .ToArray();
        e.Mobile.SendMessage($"ReportFlags target={target.Name} aggressors={(rows.Length == 0 ? "none" : string.Join(",", rows))}");
    }

    // Reports the contents of the newest corpse owned by the given player serial, the same way
    // OnInspectCommand reports a live backpack - for confirming kept-item-death-routing left the
    // corpse without Newbied/Blessed/Nontransferable items after a K4 Execute-triggered death.
    private static void OnCorpseInventoryCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyCorpseInventory <owner-player-serial>");
            return;
        }

        Corpse? newest = null;
        foreach (var item in World.Items.Values)
        {
            if (item is Corpse { Owner: { } owner } corpse && owner.Serial.Value == serial &&
                (newest is null || corpse.Serial.Value > newest.Serial.Value))
            {
                newest = corpse;
            }
        }

        if (newest is null)
        {
            e.Mobile.SendMessage($"CorpseInventory owner={serial:X} corpse=none");
            return;
        }

        e.Mobile.SendMessage($"CorpseInventory owner={serial:X} corpse={newest.Serial.Value:X}; items follow.");
        foreach (var item in newest.Items)
        {
            Report(e.Mobile, "corpse", item);
        }
    }

    // Reports the private Corpse._aggressors list (built at death from the owner's aggressor lists) for the newest
    // corpse owned by the given player serial, as "CorpseAggressors owner=<serial> corpse=<serial> aggressors=<serial,...|none>".
    private static void OnCorpseAggressorsCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyCorpseAggressors <owner-player-serial>");
            return;
        }

        var field = typeof(Corpse).GetField("_aggressors", BindingFlags.NonPublic | BindingFlags.Instance);
        Corpse? newest = null;
        foreach (var item in World.Items.Values)
        {
            if (item is Corpse { Owner: { } owner } corpse && owner.Serial.Value == serial &&
                (newest is null || corpse.Serial.Value > newest.Serial.Value))
            {
                newest = corpse;
            }
        }

        if (newest is null || field?.GetValue(newest) is not List<Mobile> list)
        {
            e.Mobile.SendMessage($"CorpseAggressors owner={serial:X} corpse=none");
            return;
        }

        var names = list.Count == 0 ? "none" : string.Join(",", list.Select(m => m.Serial.Value.ToString(CultureInfo.InvariantCulture)));
        e.Mobile.SendMessage($"CorpseAggressors owner={serial:X} corpse={newest.Serial.Value:X} aggressors={names}");
    }

    private static void OnFlagCommand(CommandEventArgs e)
    {
        if (e.Length < 1)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyFlagOverride <FeatureFlags property name, e.g. Alpha3StarterCraftMaterials> [true|false]");
            return;
        }

        var settings = ShardRulesConfiguration.Settings;
        if (settings is null)
        {
            e.Mobile.SendMessage("Shard rules configuration is not loaded.");
            return;
        }

        var name = e.GetString(0);
        var value = e.Length < 2 || !string.Equals(e.GetString(1), "false", StringComparison.OrdinalIgnoreCase);
        var property = settings.FeatureFlags.GetType().GetProperty(name, BindingFlags.Public | BindingFlags.Instance);
        if (property is null || property.PropertyType != typeof(bool) || !property.CanWrite)
        {
            e.Mobile.SendMessage($"No writable bool feature flag named '{name}' (use the C# property name, e.g. Alpha3StarterCraftMaterials).");
            return;
        }

        property.SetValue(settings.FeatureFlags, value);
        e.Mobile.SendMessage($"Flag override: {name} in-memory = {value}. Disk config unchanged; discarded on restart.");
    }

    private static void OnInspectCommand(CommandEventArgs e)
    {
        if (e.Length < 1)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyInventoryInspect <player-serial>");
            return;
        }

        var raw = e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) ||
            World.FindMobile((Serial)serial) is not PlayerMobile { Backpack: { } pack } player)
        {
            e.Mobile.SendMessage("TestOnlyInventoryInspect requires a live player serial with a backpack.");
            return;
        }

        e.Mobile.SendMessage($"Inspect {player.Name} ({player.Serial}): equipped+backpack items follow.");
        foreach (var item in player.Items)
        {
            if (item != pack)
            {
                Report(e.Mobile, "equipped", item);
            }
        }

        foreach (var item in pack.Items)
        {
            Report(e.Mobile, "backpack", item);
        }
    }

    private static void Report(Mobile to, string where, Item item) =>
        to.SendMessage(
            $"{where}: {item.GetType().Name} serial={item.Serial} amount={item.Amount} " +
            $"lootType={item.LootType} nontransferable={item.Nontransferable}" +
            (item is IUsesRemaining uses ? $" usesRemaining={uses.UsesRemaining}" : "")
        );
}
