using Server.Gumps;
using Server;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// [SkillClasses: how fast each skill trains, in the guide's window. An overview page (the classes and their speeds in one place), then
/// a page per class with its speeds between skill 10 and 90, its Mastery allowance and the skills in it. A button opens [Mastery.
/// </summary>
public static class SkillClassesGump
{
    private const int ButtonMastery = 1;

    /// <summary>One class as the window shows it. <paramref name="Skills"/> are display names, in alphabetical order.</summary>
    public sealed record SkillClassView(
        string Key, string Title, IReadOnlyList<string> Speeds, string Summary, string Mastery, IReadOnlyList<string> Skills
    );

    /// <summary>The classes that have skills, quickest first. <paramref name="skillName"/> maps a configured skill to its display name, or null to skip it.</summary>
    public static IReadOnlyList<SkillClassView> BuildViews(SkillGainRules rules, MasteryRules mastery, Func<string, string?> skillName)
    {
        var views = new List<SkillClassView>();

        foreach (var key in SkillGainCurveService.ClassNames)
        {
            if (!rules.Classes.TryGetValue(key, out var bands))
            {
                continue;
            }

            var skills = rules.Skills
                .Where(pair => string.Equals(pair.Value, key, StringComparison.OrdinalIgnoreCase))
                .Select(pair => skillName(pair.Key))
                .OfType<string>()
                .OrderBy(name => name, StringComparer.OrdinalIgnoreCase)
                .ToArray();

            if (skills.Length == 0)
            {
                continue;
            }

            mastery.AllowanceTenths.TryGetValue(key, out var allowance);

            views.Add(
                new SkillClassView(
                    key,
                    $"{MasteryProgression.ClassLabel(key)} skills",
                    SkillGainCurveService.SpeedLines(bands),
                    SkillGainCurveService.SpeedSummary(bands),
                    $"From {MasteryEngine.ThresholdText} a skill in this class has an allowance of {GumpStyle.Points(allowance)} each cycle, " +
                    $"about {allowance} successful uses.",
                    skills
                )
            );
        }

        return views;
    }

    /// <summary>The window's pages: an overview, then one per class.</summary>
    public static IReadOnlyList<WelcomeGuide.Topic> BuildTopics(IReadOnlyList<SkillClassView> views)
    {
        var overview = new List<string>
        {
            $"Every skill trains in one of these classes. From skill 10 to {MasteryEngine.ThresholdText} your skills gain faster than in stock Ultima Online, " +
            $"as each class's page shows. From {MasteryEngine.ThresholdText} a skill is in Mastery and grows by a daily allowance instead: [Mastery shows yours."
        };

        foreach (var view in views)
        {
            overview.Add($"{WelcomeGuide.HeadingMark}{view.Title} ({view.Skills.Count})");
            overview.Add(char.ToUpperInvariant(view.Summary[0]) + view.Summary[1..] + ".");
        }

        var topics = new List<WelcomeGuide.Topic> { new("overview", "Overview", overview) };

        foreach (var view in views)
        {
            topics.Add(
                new WelcomeGuide.Topic(
                    view.Key,
                    view.Title,
                    [
                        $"{WelcomeGuide.HeadingMark}Training speed",
                        string.Join("<BR>", view.Speeds),
                        $"{WelcomeGuide.HeadingMark}Mastery",
                        view.Mastery,
                        $"{WelcomeGuide.HeadingMark}The {view.Skills.Count} skills",
                        string.Join(", ", view.Skills)
                    ]
                )
            );
        }

        return topics;
    }

    public static void Open(PlayerMobile player)
    {
        if (player.NetState is null)
        {
            return;
        }

        var settings = ShardRulesConfiguration.Settings;

        if (settings is null || !SkillGainCurveService.Enabled)
        {
            player.SendMessage("Skills gain at the stock rate on this shard.");
            return;
        }

        var views = BuildViews(settings.SkillGain, settings.Mastery, key =>
            Enum.TryParse<SkillName>(key, false, out var skill) && Enum.IsDefined(skill) ? SkillInfo.Table[(int)skill].Name : null);

        player.SendGump(
            new GuideWindow(
                "Skill Training Speeds",
                "How fast each skill gains, compared with stock Ultima Online",
                "Type [SkillClasses to open this again.",
                BuildTopics(views),
                actions: [new GuideWindow.WindowAction("Open Mastery", ButtonMastery)],
                onAction: (viewer, button) =>
                {
                    if (button == ButtonMastery)
                    {
                        MasteryGump.Open(viewer, viewer);
                    }
                }
            )
        );
    }
}
