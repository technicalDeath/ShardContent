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
        TheftProtectionService.Configure();
        KnockedOutService.Configure();
    }

    // ModernUO's stock Initialize methods include NotorietyHandlers, which installs the
    // baseline delegate. Run the shard bridge after those handlers so the Alpha 2 policy is
    // not silently replaced during startup.
    [Server.CallPriority(1000)]
    public static void Initialize()
    {
        PvpIntentService.Configure();
        KnockedOutService.Initialize();
    }
}
