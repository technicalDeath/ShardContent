using System.Reflection;
using Server;
using Server.Collections;
using Server.Commands;
using Server.ContextMenus;
using Server.Gumps;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Item help and the skill guide (docs/Help-Gumps-Plan.md), behind <c>featureFlags.helpGumps</c>. A single click on an item the player holds, or on a movable item
/// within reach on the ground, offers About in its context menu; About opens a window about that kind of item with buttons to the skill pages that matter for it. The
/// skill guide ([SkillGuide) is the Welcome guide's window with six category tabs and a page for each of the era's 49 skills. The text is data (HelpCatalog).
/// </summary>
public static class HelpService
{
    /// <summary>The client text number of the menu entry ("About"), added in <c>Data/Client/Clilocs.txt</c>.</summary>
    public const int HelpEntryNumber = 3050002;

    private const int BackAction = 1;
    private const int PageStaffAction = 2;
    private const int SkillAction = 100;
    private const int RelatedAction = 200;
    private const int GroundReach = 2;

    private static readonly Dictionary<Serial, List<Location>> History = [];

    private static bool _configured;

    /// <summary>Where a player is in the help: an item topic (and the item it was opened from, when there was one) or a skill page.</summary>
    private readonly record struct Location(string? ItemTopic, Serial Item, SkillName? Skill);

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.HelpGumps == true;

    public static HelpCatalog? Catalog { get; private set; }

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        Catalog = Load();

        var previous = ContextMenuSystem.ItemEntriesHandler;
        ContextMenuSystem.ItemEntriesHandler = (Item item, Mobile from, ref PooledRefList<ContextMenuEntry> list) =>
        {
            previous?.Invoke(item, from, ref list);

            if (CanOfferHelp(item, from))
            {
                list.Add(new HelpEntry(item));
            }
        };

        CommandSystem.Register("SkillGuide", AccessLevel.Player, OnSkillGuide);
        CommandSystem.Register("HelpStatus", AccessLevel.GameMaster, OnStatus);
    }

    // ---- loading

    public static string DataFolder => Path.Combine(Core.BaseDirectory, "Configuration", "help");

    public static IEnumerable<Assembly> ItemAssemblies() =>
        AppDomain.CurrentDomain.GetAssemblies().Where(static a => a.GetName().Name is "Server" or "UOContent" or "BritanniaRenaissance.Content");

    private static HelpCatalog Load()
    {
        var skills = Path.Combine(DataFolder, "skills.json");
        var items = Path.Combine(DataFolder, "items.json");

        if (!File.Exists(skills) || !File.Exists(items))
        {
            throw new InvalidOperationException($"The help text is missing: {skills} and {items}");
        }

        var errors = new List<string>();
        var catalog = HelpCatalog.Parse(File.ReadAllText(skills), File.ReadAllText(items), errors);
        var assemblies = ItemAssemblies().ToArray();
        errors.AddRange(catalog.Validate(HelpCatalog.TypeLookup(assemblies), HelpCatalog.HoldableTypes(assemblies)));

        if (errors.Count > 0)
        {
            throw new InvalidOperationException(
                $"The help text failed validation:{Environment.NewLine}- {string.Join(Environment.NewLine + "- ", errors.Take(40))}"
            );
        }

        return catalog;
    }

    // ---- the menu entry

    /// <summary>Items the player holds (pack, bank box, worn) and movable items within reach on the ground; never another player's, never a shop's.</summary>
    public static bool CanOfferHelp(Item item, Mobile from)
    {
        if (!Enabled || Catalog is null || from is not PlayerMobile || item.Deleted || Catalog.TopicFor(item.GetType()) is null)
        {
            return false;
        }

        if (item.RootParent == from || from.BankBox is { } box && item.IsChildOf(box))
        {
            return true;
        }

        return item.Parent is null && item.Movable && item.Visible && from.InRange(item.GetWorldLocation(), GroundReach);
    }

    private sealed class HelpEntry : ContextMenuEntry
    {
        private readonly Item _item;

        public HelpEntry(Item item) : base(HelpEntryNumber) => _item = item;

        public override void OnClick(Mobile from, IEntity target)
        {
            if (from is PlayerMobile player && !_item.Deleted)
            {
                History.Remove(player.Serial);
                OpenItem(player, _item);
            }
        }
    }

    // ---- gating and expansion of the text

    public static bool GateOn(string? gate)
    {
        if (gate is null)
        {
            return true;
        }

        var flags = ShardRulesConfiguration.Settings?.FeatureFlags;
        var property = typeof(DeferredFeatureFlags).GetProperty(gate, BindingFlags.Public | BindingFlags.Instance);

        return flags is not null && property?.GetValue(flags) is true;
    }

    /// <summary>The paragraphs of a page with the flag-gated ones kept or dropped and the generated blocks filled in.</summary>
    public static List<string> Expand(IEnumerable<HelpCatalog.Paragraph> paragraphs, SkillName? skill = null)
    {
        var result = new List<string>();

        foreach (var paragraph in paragraphs)
        {
            if (!GateOn(paragraph.Requires))
            {
                continue;
            }

            if (paragraph.Text is { } text)
            {
                result.Add(text);
            }
            else if (paragraph.Generate is { } generate)
            {
                result.AddRange(HelpGenerators.Generate(generate, skill));
            }
        }

        return result;
    }

    // ---- the windows

    public static string ItemName(Item item)
    {
        if (!string.IsNullOrWhiteSpace(item.Name))
        {
            return item.Name;
        }

        return item.LabelNumber > 0 && Localization.GetText(item.LabelNumber) is { Length: > 0 } text ? text : HelpGenerators.Spaced(item.GetType().Name);
    }

    public static void OpenItem(PlayerMobile player, Item item)
    {
        if (Catalog?.TopicFor(item.GetType()) is { } topic)
        {
            ShowItemTopic(player, topic, item);
        }
    }

    private static void ShowItemTopic(PlayerMobile player, HelpCatalog.ItemTopic topic, Item? item)
    {
        if (player.NetState is null || Catalog is null)
        {
            return;
        }

        var current = new Location(topic.Key, item?.Serial ?? Serial.Zero, null);
        var actions = new List<GuideWindow.WindowAction>();
        var targets = new List<Action<PlayerMobile>>();

        if (History.TryGetValue(player.Serial, out var trail) && trail.Count > 0)
        {
            actions.Add(new GuideWindow.WindowAction("Back", BackAction));
        }

        for (var i = 0; i < topic.Skills.Count; i++)
        {
            var skill = topic.Skills[i];
            actions.Add(new GuideWindow.WindowAction($"{SkillTitle(skill)} skill", SkillAction + i));
        }

        for (var i = 0; i < topic.Related.Count; i++)
        {
            var related = Catalog.ItemByKey(topic.Related[i]);

            if (related is not null)
            {
                actions.Add(new GuideWindow.WindowAction(related.Title, RelatedAction + i));
            }
        }

        var page = new WelcomeGuide.Topic(topic.Key, topic.Title, Expand(topic.Paragraphs));
        var subtitle = item is not null ? HelpGenerators.Capitalised(ItemName(item)) : topic.Title;

        player.SendGump(
            new GuideWindow(
                "About", subtitle, "Type [SkillGuide to open the skill guide.", [page], 0, actions,
                (p, id) => OnItemAction(p, id, topic, current),
                art: new GuideWindow.ItemArt(item?.ItemID ?? topic.Art, item?.Hue ?? 0)
            )
        );
    }

    private static void OnItemAction(PlayerMobile player, int id, HelpCatalog.ItemTopic topic, Location current)
    {
        if (id == BackAction)
        {
            GoBack(player);
        }
        else if (id is >= SkillAction and < RelatedAction && id - SkillAction < topic.Skills.Count)
        {
            Push(player, current);
            OpenSkills(player, topic.Skills[id - SkillAction]);
        }
        else if (id >= RelatedAction && id - RelatedAction < topic.Related.Count && Catalog?.ItemByKey(topic.Related[id - RelatedAction]) is { } related)
        {
            Push(player, current);
            ShowItemTopic(player, related, null);
        }
    }

    public static string SkillTitle(SkillName skill) => SkillInfo.Table[(int)skill].Name;

    public static void OpenSkills(PlayerMobile player, SkillName? skill = null)
    {
        if (player.NetState is null || Catalog is not { Categories.Count: > 0 } catalog)
        {
            return;
        }

        var category = (skill is { } s ? catalog.CategoryOf(s) : null) ?? catalog.Categories[0];
        var categoryIndex = catalog.Categories.ToList().IndexOf(category);
        var topics = category.Skills
            .Select(sk => new WelcomeGuide.Topic(sk.ToString(), SkillTitle(sk), SkillParagraphs(catalog, sk)))
            .ToList();
        var first = skill is { } want ? Math.Max(0, category.Skills.ToList().IndexOf(want)) : 0;
        var actions = new List<GuideWindow.WindowAction>();

        if (History.TryGetValue(player.Serial, out var trail) && trail.Count > 0)
        {
            actions.Add(new GuideWindow.WindowAction("Back", BackAction));
        }

        // the top bar's Help button became About, so the way to page a staff member lives here
        actions.Add(new GuideWindow.WindowAction("Page staff", PageStaffAction));

        player.SendGump(
            new GuideWindow(
                "Skill Guide", "How every skill works", "Type [SkillGuide to open this guide again.", topics, first, actions,
                (p, id) => OnSkillAction(p, id, catalog),
                serverTabs: new GuideWindow.ServerTabs(catalog.Categories.Select(static c => c.Title).ToArray(), categoryIndex, GuideWindow.DefaultServerTabButtonBase)
            )
        );
    }

    private static List<string> SkillParagraphs(HelpCatalog catalog, SkillName skill)
    {
        var page = catalog.PageOf(skill);

        if (page is null)
        {
            return [];
        }

        var paragraphs = Expand(page.Paragraphs, skill);
        var related = catalog.ItemsFor(skill).Select(static i => char.ToLowerInvariant(i.Title[0]) + i.Title[1..]).ToArray();

        if (related.Length > 0)
        {
            paragraphs.Add(WelcomeGuide.HeadingMark + "Related items");
            paragraphs.Add($"Click one of these items in your pack and choose About to read about it: {string.Join(", ", related)}.");
        }

        return paragraphs;
    }

    private static void OnSkillAction(PlayerMobile player, int id, HelpCatalog catalog)
    {
        if (id == BackAction)
        {
            GoBack(player);
        }
        else if (id == PageStaffAction)
        {
            Server.Engines.Help.HelpGump.HelpRequest(player);
        }
        else if (id >= GuideWindow.DefaultServerTabButtonBase && id - GuideWindow.DefaultServerTabButtonBase < catalog.Categories.Count)
        {
            OpenSkills(player, catalog.Categories[id - GuideWindow.DefaultServerTabButtonBase].Skills[0]);
        }
    }

    // ---- going back

    private static void Push(PlayerMobile player, Location where)
    {
        if (!History.TryGetValue(player.Serial, out var trail))
        {
            History[player.Serial] = trail = [];
        }

        trail.Add(where);

        if (trail.Count > 12)
        {
            trail.RemoveAt(0);
        }
    }

    private static void GoBack(PlayerMobile player)
    {
        if (!History.TryGetValue(player.Serial, out var trail) || trail.Count == 0 || Catalog is null)
        {
            return;
        }

        var where = trail[^1];
        trail.RemoveAt(trail.Count - 1);

        if (where.Skill is { } skill)
        {
            OpenSkills(player, skill);
        }
        else if (where.ItemTopic is { } key && Catalog.ItemByKey(key) is { } topic)
        {
            ShowItemTopic(player, topic, where.Item != Serial.Zero ? World.FindItem(where.Item) : null);
        }
    }

    // ---- commands

    /// <summary>The skill a typed name means: its display name or the name of its enum, ignoring case and spaces, or the start of either or of a word in it. Null when none or several match.</summary>
    public static SkillName? FindSkill(string typed)
    {
        var wanted = new string(typed.Where(char.IsLetter).ToArray()).ToLowerInvariant();

        if (wanted.Length == 0)
        {
            return null;
        }

        var all = HelpCatalog.EraSkills;
        var exact = all.Where(s => Squash(SkillTitle(s)) == wanted || Squash(s.ToString()) == wanted).ToArray();

        if (exact.Length == 1)
        {
            return exact[0];
        }

        var start = all.Where(s => Squash(SkillTitle(s)).StartsWith(wanted, StringComparison.Ordinal) || Squash(s.ToString()).StartsWith(wanted, StringComparison.Ordinal)).ToArray();

        if (start.Length == 1)
        {
            return start[0];
        }

        // "taming" for Animal Taming: a word inside the name.
        var word = all.Where(s => SkillTitle(s).Split(' ', '/').Any(w => Squash(w).StartsWith(wanted, StringComparison.Ordinal))).ToArray();

        return word.Length == 1 ? word[0] : null;
    }

    private static string Squash(string text) => new string(text.Where(char.IsLetter).ToArray()).ToLowerInvariant();

    [Usage("SkillGuide [skill]")]
    [Description("Opens the skill guide: a page for each skill, in six tabs. Add a skill name to open its page.")]
    private static void OnSkillGuide(CommandEventArgs e)
    {
        if (e.Mobile is not PlayerMobile player)
        {
            return;
        }

        if (!Enabled || Catalog is null)
        {
            player.SendMessage("The skill guide is not available.");
            return;
        }

        SkillName? skill = null;

        if (e.Length > 0)
        {
            skill = FindSkill(e.ArgString);

            if (skill is null)
            {
                player.SendMessage($"\"{e.ArgString}\" is not one skill. Try a fuller name, or open the guide with no name.");
                return;
            }
        }

        History.Remove(player.Serial);
        OpenSkills(player, skill);
    }

    [Usage("HelpStatus")]
    [Description("Shows whether item help and the skill guide are on, and how much of the help text there is.")]
    private static void OnStatus(CommandEventArgs e)
    {
        var catalog = Catalog;

        if (catalog is null)
        {
            e.Mobile.SendMessage("The help text is not loaded.");
            return;
        }

        var holdable = HelpCatalog.HoldableTypes(ItemAssemblies());
        var generic = catalog.GeneralPageTypes(holdable).Count;

        e.Mobile.SendMessage(
            $"Help: {(Enabled ? "ON" : "off (flag featureFlags.helpGumps)")}. {catalog.Categories.Count} skill categories, {catalog.Skills.Count} skill pages, " +
            $"{catalog.Items.Count} item topics; {holdable.Count} item types can be held and {generic} of them reach only the general page."
        );
    }
}
