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
        Server.EventSink.ServerStarted += RebindAlpha2AfterStockHandlers;
    }

    // Keep world-dependent initialization at the normal assembly boundary. The Intent
    // presentation delegate is rebound from the ServerStarted callback below, after every
    // stock UOContent Initialize method has completed.
    [Server.CallPriority(1000)]
    public static void Initialize()
    {
        KnockedOutService.Initialize();
    }

    private static void RebindAlpha2AfterStockHandlers()
    {
        Server.EventSink.ServerStarted -= RebindAlpha2AfterStockHandlers;
        PvpIntentService.RebindAfterStockHandlers();
    }
}
