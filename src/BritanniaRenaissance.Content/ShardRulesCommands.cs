using Server;

namespace BritanniaRenaissance.Content;

/// <summary>Staff diagnostics for the loaded shard policy document.</summary>
public static class ShardRulesCommands
{
    public static void Register()
    {
        CommandSystem.Register("ShardRulesStatus", AccessLevel.Administrator, OnStatus);
        CommandSystem.Register("MasteryStatus", AccessLevel.Player, OnMasteryStatus);
    }

    [Usage("ShardRulesStatus")]
    [Description("Displays the validated Britannia Renaissance shard policy baseline.")]
    private static void OnStatus(CommandEventArgs e)
    {
        foreach (var line in ShardRulesConfiguration.Describe())
        {
            e.Mobile.SendMessage(line);
        }

        foreach (var line in EraGateConfiguration.Describe())
        {
            e.Mobile.SendMessage(line);
        }
    }

    [Usage("MasteryStatus")]
    [Description("Displays the server-controlled Mastery schedule and your pending increments.")]
    private static void OnMasteryStatus(CommandEventArgs e)
    {
        foreach (var line in MasteryProgression.DescribeStatus(e.Mobile))
        {
            e.Mobile.SendMessage(line);
        }
    }
}
