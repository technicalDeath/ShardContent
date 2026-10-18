using System.Text;
using Server;
using Server.Engines.Craft.T2A;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Says why the smithing menu is empty (docs/Bot-Farm-QoL-Findings.md item 24), behind <c>featureFlags.metalSkillNotice</c>. The owner (2026-10-17)
/// chose "Say why, name the skill": the T2A smithing menu filters every build by the metal chosen with the tongs, so a smith who targets dull copper
/// below Blacksmithy 65 gets only Repair and Smelt with no word. One line now names the skill the metal needs and points to iron. Nothing else changes.
/// </summary>
public static class MetalSkillNoticeService
{
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.MetalSkillNotice == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        BlacksmithMenu.MetalBeyondSkill += OnMetalBeyondSkill;
    }

    /// <summary>"DullCopperIngot" becomes "dull copper".</summary>
    public static string MetalName(string ingotTypeName)
    {
        var name = ingotTypeName.EndsWith("Ingot", StringComparison.Ordinal) ? ingotTypeName[..^5] : ingotTypeName;
        var text = new StringBuilder();

        foreach (var c in name)
        {
            if (char.IsUpper(c) && text.Length > 0)
            {
                text.Append(' ');
            }

            text.Append(char.ToLowerInvariant(c));
        }

        return text.ToString();
    }

    public static string Text(string ingotTypeName, double required) =>
        $"You need Blacksmithy {required:0} to work {MetalName(ingotTypeName)}. Target iron ingots to make things now.";

    private static void OnMetalBeyondSkill(Mobile from, Type ingot, double required)
    {
        if (Enabled && from is PlayerMobile)
        {
            from.SendMessage(Text(ingot.Name, required));
        }
    }
}
