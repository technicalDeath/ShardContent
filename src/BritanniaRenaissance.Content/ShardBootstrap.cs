namespace BritanniaRenaissance.Content;

/// <summary>
/// Assembly-level entry point for shard-owned ModernUO content.
/// Add configuration and event registrations here, then keep gameplay systems in focused files.
/// </summary>
public static class ShardBootstrap
{
    public static void Configure()
    {
        ShardRulesConfiguration.Load();
        EraGateConfiguration.Load();
        ShardRulesCommands.Register();
        MasteryProgression.Configure();
        MurderAdjudicationService.Configure();
    }

    public static void Initialize() => PvpIntentService.Configure();
}
