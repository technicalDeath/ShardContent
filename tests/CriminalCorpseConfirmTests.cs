using Server.Items;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class CriminalCorpseConfirmTests
{
    [Fact]
    public void AMonsterCorpseSaysItIsNotYourKill() =>
        Assert.StartsWith("This is not your kill: carving it is a criminal act.", CriminalCorpseConfirm.Warning(CriminalCorpseAct.Carve, false));

    [Fact]
    public void APlayerCorpseSaysItIsNotYoursToLoot() =>
        Assert.StartsWith("This corpse is not yours to loot: taking from it", CriminalCorpseConfirm.Warning(CriminalCorpseAct.Loot, true));

    [Theory]
    [InlineData(CriminalCorpseAct.Loot, "Pick it up again.")]
    [InlineData(CriminalCorpseAct.Use, "Use it again.")]
    [InlineData(CriminalCorpseAct.Steal, "Use Stealing on it again.")]
    public void AfterOkayThePlayerIsToldWhatToDo(CriminalCorpseAct act, string text) => Assert.Equal(text, CriminalCorpseConfirm.Again(act));

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().CriminalCorpseConfirm);
}
