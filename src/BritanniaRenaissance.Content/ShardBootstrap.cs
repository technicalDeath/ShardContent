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
        Alpha2bWorldGenerationConfiguration.Load();
        ShardRulesCommands.Register();
        Alpha2bWorldGenerationCommands.Register();
        HousingPlacementSurveyCommands.Register();
        HousingStatusCommands.Register();
        MasteryProgression.Configure();
        SkillBankService.Configure();
        FaintMemoriesService.Configure();
        OutdoorHotZoneBoundaryService.Configure();
        HousingGeographyPolicy.Configure();
        MurderAdjudicationService.Configure();
        TheftProtectionService.Configure();
        Alpha3StartingStats.Configure();
        StarterScissorsIssuance.Configure();
        StarterBagIssuance.Configure();
        StarterGoldPolicy.Configure();
        StarterCraftMaterialIssuance.Configure();
        StarterCombatIssuance.Configure();
        StarterOnboarding.Configure();
        KnockedOutService.Configure();
        LocalAccountRequest.Configure();
        KeptItemDeathRouting.Configure();
        PostUorSystemGates.Configure();
        PetRestrictionService.Configure();
        SkillGainCurveService.Configure();
        HarvestRepeatService.Configure();
        ActionRepeatService.Configure();
        CampingService.Configure();
        CampTravelService.Configure();
        TravelWarningService.Configure();
        BuffIconService.Configure();
        GuardCallNotice.Configure();
        StarterWeightBudget.Register(); // after every starter issuer; stays ahead of the Elf observer below
        CosmeticElfCreationService.Register(); // keep last among CharacterCreatedHandler observers
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
        KnockedOutService.RebindAfterStockHandlers();
        EraGateConfiguration.ValidatePostBootFeatureFlags();
        EraGateConfiguration.ValidatePostBootProfessions();
        OutdoorHotZonePolicy.ValidatePostBootDungeonRegions();
    }
}
