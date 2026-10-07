using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// Skill Bank restoration in steps of 0.2 (owner ruling 2026-10-07) and Discard, the player's own way of throwing a skill's banked
/// points away. The ledger is pure policy, so both are pinned here.
/// </summary>
public class SkillBankStepAndDiscardTests
{
    private const int Anatomy = 1;
    private const int Tactics = 2;

    private static SkillBankLedger Bank(int anatomy, int capacity = 3000)
    {
        var bank = new SkillBankLedger(capacity);
        bank.Deposit(Anatomy, "Anatomy", anatomy, 1000);
        return bank;
    }

    private static SkillBankActiveSkill Down(int id, string name, int baseTenths) => new(id, name, baseTenths, 1000, true);

    // ---- restoring two tenths at a time

    [Fact]
    public void BelowTheCapAStepOfTwoReturnsTwoTenthsAndTakesThemFromTheBank()
    {
        var bank = Bank(5);

        Assert.True(bank.TryPlanRestoration(Anatomy, 3000, 7000, [], out var plan, stepTenths: 2));

        Assert.Equal(2, plan.RestoredTenths);
        Assert.Null(plan.DownSkillId);
        Assert.Equal(0, plan.DownTenths);
        Assert.Equal(3, plan.BankAfter.GetBalance(Anatomy));
        Assert.Equal(3, plan.BankAfter.TotalTenths);
    }

    [Fact]
    public void WhenOnlyOneTenthIsBankedOnlyOneTenthComesBack()
    {
        Assert.True(Bank(1).TryPlanRestoration(Anatomy, 3000, 7000, [], out var plan, stepTenths: 2));

        Assert.Equal(1, plan.RestoredTenths);
        Assert.Equal(0, plan.BankAfter.GetBalance(Anatomy));
    }

    [Fact]
    public void WhenOnlyOneTenthOfRoomIsLeftUnderTheSkillsCapOnlyOneTenthComesBack()
    {
        Assert.True(Bank(5).TryPlanRestoration(Anatomy, 3000, 7000, [], out var plan, stepTenths: 2, roomTenths: 1));

        Assert.Equal(1, plan.RestoredTenths);
        Assert.Equal(4, plan.BankAfter.GetBalance(Anatomy));
    }

    [Fact]
    public void AtTheTotalCapTwoTenthsComeOutOfOneDownSkillAndTheBankKeepsThemForIt()
    {
        var bank = Bank(5);

        Assert.True(bank.TryPlanRestoration(Anatomy, 7000, 7000, [Down(Tactics, "Tactics", 950)], out var plan, stepTenths: 2));

        Assert.Equal(2, plan.RestoredTenths);
        Assert.Equal(Tactics, plan.DownSkillId);
        Assert.Equal(2, plan.DownTenths);
        Assert.Equal(3, plan.BankAfter.GetBalance(Anatomy));
        Assert.Equal(2, plan.BankAfter.GetBalance(Tactics));
        Assert.Equal(bank.TotalTenths, plan.BankAfter.TotalTenths);
    }

    [Fact]
    public void OneTenthBelowTheTotalCapOnlyOneTenthHasToComeOutOfADownSkill()
    {
        Assert.True(Bank(5).TryPlanRestoration(Anatomy, 6999, 7000, [Down(Tactics, "Tactics", 950)], out var plan, stepTenths: 2));

        Assert.Equal(2, plan.RestoredTenths);
        Assert.Equal(1, plan.DownTenths);
        Assert.Equal(1, plan.BankAfter.GetBalance(Tactics));
    }

    [Fact]
    public void WhenNoDownSkillCanGiveTwoTenthsItFallsBackToOne()
    {
        Assert.True(Bank(5).TryPlanRestoration(Anatomy, 7000, 7000, [Down(Tactics, "Tactics", 1)], out var plan, stepTenths: 2));

        Assert.Equal(1, plan.RestoredTenths);
        Assert.Equal(1, plan.DownTenths);
        Assert.Equal(4, plan.BankAfter.GetBalance(Anatomy));
        Assert.Equal(1, plan.BankAfter.GetBalance(Tactics));
    }

    [Fact]
    public void AtTheTotalCapWithNoDownSkillNothingIsRestoredEvenWithAStep()
    {
        Assert.False(Bank(5).TryPlanRestoration(Anatomy, 7000, 7000, [], out _, stepTenths: 2));
        Assert.False(Bank(5).TryPlanRestoration(Anatomy, 7000, 7000, [new SkillBankActiveSkill(Tactics, "Tactics", 900, 1000, false)], out _, stepTenths: 2));
    }

    [Fact]
    public void ADownSkillCannotPayForItselfAndAboveTheCapNothingIsRestored()
    {
        Assert.False(Bank(5).TryPlanRestoration(Anatomy, 7000, 7000, [Down(Anatomy, "Anatomy", 950)], out _, stepTenths: 2));
        Assert.False(Bank(5).TryPlanRestoration(Anatomy, 7001, 7000, [Down(Tactics, "Tactics", 950)], out _, stepTenths: 2));
    }

    [Fact]
    public void WithoutAStepTheOldOneTenthBehaviourIsUnchanged()
    {
        Assert.True(Bank(5).TryPlanRestoration(Anatomy, 7000, 7000, [Down(Tactics, "Tactics", 950)], out var plan));

        Assert.Equal(1, plan.RestoredTenths);
        Assert.Equal(1, plan.DownTenths);
        Assert.Equal(4, plan.BankAfter.GetBalance(Anatomy));
    }

    [Fact]
    public void ARestorationAtAFullBankStillFitsBecauseItFreesWhatItNeeds()
    {
        // The bank is full, but consuming two tenths frees exactly the room the Down skill's two tenths need.
        var bank = new SkillBankLedger(5);
        bank.Deposit(Anatomy, "Anatomy", 2, 1000);
        bank.Deposit(Tactics, "Tactics", 3, 1000);

        Assert.True(bank.TryPlanRestoration(Anatomy, 7000, 7000, [Down(3, "Magery", 900)], out var plan, stepTenths: 2));
        Assert.Equal(5, plan.BankAfter.TotalTenths);
        Assert.Equal(2, plan.BankAfter.GetBalance(3));
    }

    [Fact]
    public void ManyStepsNeverLoseOrCreateABankedPoint()
    {
        var random = new Random(20261007);
        var bank = new SkillBankLedger(40);
        bank.Deposit(Anatomy, "Anatomy", 15, 1000);
        bank.Deposit(Tactics, "Tactics", 10, 1000);
        var activeTotal = 7000;
        var banked = bank.TotalTenths;
        var restored = 0;
        var givenUp = 0;

        for (var i = 0; i < 200; i++)
        {
            var target = random.Next(2) == 0 ? Anatomy : Tactics;
            var other = target == Anatomy ? Tactics : Anatomy;

            if (!bank.TryPlanRestoration(target, activeTotal, 7000, [Down(other, "Other", 900), Down(3, "Magery", 900)], out var plan, stepTenths: 2))
            {
                continue;
            }

            Assert.InRange(plan.RestoredTenths, 1, 2);
            restored += plan.RestoredTenths;
            givenUp += plan.DownTenths;
            activeTotal += plan.RestoredTenths - plan.DownTenths;
            bank = plan.BankAfter;

            Assert.Equal(bank.TotalTenths, bank.Balances.Sum(b => b.Tenths));
            Assert.InRange(bank.TotalTenths, 0, bank.CapacityTenths);
        }

        // What left the bank went into skills; what Down skills gave up went in. At the cap those are the same points.
        Assert.Equal(banked - restored + givenUp, bank.TotalTenths);
        Assert.Equal(7000, activeTotal);
    }

    // ---- consuming several at once, and discarding

    [Fact]
    public void ConsumingSeveralTenthsNeedsThemAllToBeThere()
    {
        var bank = Bank(3);

        Assert.False(bank.TryConsume(Anatomy, 4));
        Assert.False(bank.TryConsume(Anatomy, 0));
        Assert.Equal(3, bank.GetBalance(Anatomy));

        Assert.True(bank.TryConsume(Anatomy, 2));
        Assert.Equal(1, bank.GetBalance(Anatomy));
        Assert.Equal(1, bank.TotalTenths);
    }

    [Fact]
    public void DiscardingRemovesEverythingBankedForThatSkillAndFreesTheRoom()
    {
        var bank = new SkillBankLedger(10);
        bank.Deposit(Anatomy, "Anatomy", 6, 1000);
        bank.Deposit(Tactics, "Tactics", 4, 1000);
        Assert.Equal(0, bank.Deposit(3, "Magery", 1, 1000).BankedTenths);

        Assert.Equal(6, bank.Discard(Anatomy));

        Assert.Equal(0, bank.GetBalance(Anatomy));
        Assert.Equal(4, bank.GetBalance(Tactics));
        Assert.Equal(4, bank.TotalTenths);
        Assert.Equal(1, bank.Deposit(3, "Magery", 1, 1000).BankedTenths);
    }

    [Fact]
    public void DiscardingASkillWithNothingBankedDoesNothing()
    {
        var bank = Bank(3);

        Assert.Equal(0, bank.Discard(Tactics));
        Assert.Equal(0, bank.Discard(99));
        Assert.Equal(3, bank.TotalTenths);
    }

    [Fact]
    public void ADiscardedBalanceStaysGoneAfterSavingAndLoading()
    {
        var bank = Bank(3);
        bank.Deposit(Tactics, "Tactics", 2, 1000);
        bank.Discard(Anatomy);

        Assert.True(SkillBankLedger.TryDeserialize(
            bank.Serialize(), 3000, id => id switch { Anatomy => ("Anatomy", 1000), Tactics => ("Tactics", 1000), _ => null }, out var loaded));

        Assert.Equal(0, loaded.GetBalance(Anatomy));
        Assert.Equal(2, loaded.GetBalance(Tactics));
        Assert.Equal(2, loaded.TotalTenths);
    }

    // ---- the Discard button and its confirmation

    [Theory]
    [InlineData(3000, 0)]
    [InlineData(3012, 12)]
    [InlineData(3999, 999)]
    public void ADiscardButtonIdNamesItsSkill(int buttonId, int skillId) => Assert.Equal(skillId, SkillBankGump.ParseDiscardButton(buttonId));

    [Theory]
    [InlineData(0)]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(3)]
    [InlineData(1005)]
    [InlineData(2005)]
    [InlineData(4000)]
    public void NothingElseIsADiscardButton(int buttonId) => Assert.Null(SkillBankGump.ParseDiscardButton(buttonId));

    [Fact]
    public void DiscardButtonsAreNotMistakenForRetentionButtons()
    {
        Assert.Null(SkillBankGump.ParseRetentionButton(3005));
        Assert.Equal((5, BankRetention.Locked), SkillBankGump.ParseRetentionButton(1005));
        Assert.Equal((5, BankRetention.Down), SkillBankGump.ParseRetentionButton(2005));
    }

    [Fact]
    public void TheWordToTypeIsDiscard() => Assert.Equal("discard", SkillBankDiscardGump.ConfirmWord);

    [Theory]
    [InlineData("discard")]
    [InlineData("Discard")]
    [InlineData("DISCARD")]
    [InlineData("  discard ")]
    public void TheConfirmationWordIsAcceptedWhateverItsCaseAndSpacing(string typed) => Assert.True(SkillBankDiscardGump.IsConfirmed(typed));

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    [InlineData("yes")]
    [InlineData("no")]
    [InlineData("discard it")]
    [InlineData("discards")]
    [InlineData("dis card")]
    [InlineData("remove")]
    public void AnythingElseIsNotAConfirmation(string? typed) => Assert.False(SkillBankDiscardGump.IsConfirmed(typed));

    [Fact]
    public void TheConfirmationSaysExactlyWhatWillBeDeletedAndThatTheSkillStays()
    {
        Assert.Equal("Discard the banked points of Swords?", SkillBankDiscardGump.DescribeQuestion("Swords"));
        Assert.Equal(
            "12.3 banked points will be deleted for good. They do not go back to Swords, and Swords stays at 55.0.",
            SkillBankDiscardGump.DescribeConsequence("Swords", 123, 550)
        );
        Assert.Equal("Type discard in the box to confirm:", SkillBankDiscardGump.DescribePrompt());
    }

    // ---- paging with and without the Faint Memories banner

    [Theory]
    [InlineData(0, false, 1)]
    [InlineData(6, false, 1)]
    [InlineData(7, false, 2)]
    [InlineData(0, true, 1)]
    [InlineData(4, true, 1)]
    [InlineData(5, true, 2)]
    [InlineData(12, true, 3)]
    public void TheBannerLeavesRoomForFourRowsInsteadOfSix(int rows, bool banner, int pages) =>
        Assert.Equal(pages, SkillBankGump.PageCount(rows, banner));
}
