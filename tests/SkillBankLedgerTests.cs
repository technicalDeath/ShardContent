using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class SkillBankLedgerTests
{
    [Fact]
    public void InvalidPayloadRecoveryRequiresStaffArchivesOriginalAndCannotRepeat()
    {
        var rejected = SkillBankRecovery.Recover("not json", null, false, 3000, _ => null);
        Assert.False(rejected.Changed);
        Assert.Equal("not json", rejected.ActivePayload);
        Assert.Null(rejected.ArchivedPayload);

        var recovered = SkillBankRecovery.Recover("not json", null, true, 3000, _ => null);
        Assert.True(recovered.Changed);
        Assert.Equal("not json", recovered.ArchivedPayload);
        Assert.True(SkillBankLedger.TryDeserialize(recovered.ActivePayload, 3000, _ => null, out var empty));
        Assert.Empty(empty.Balances);

        var repeated = SkillBankRecovery.Recover(
            recovered.ActivePayload, recovered.ArchivedPayload, true, 3000, _ => null);
        Assert.False(repeated.Changed);
        Assert.Equal("not json", repeated.ArchivedPayload);
    }

    [Fact]
    public void NewDepositsDefaultLockedAndCannotDisplaceEachOther()
    {
        var bank = new SkillBankLedger(2);

        Assert.Equal(new SkillBankDeposit(2, 0, 0), bank.Deposit(1, "Anatomy", 2, 1000));
        Assert.Equal(new SkillBankDeposit(0, 1, 0), bank.Deposit(2, "Tactics", 1, 1000));
        Assert.Equal(2, bank.GetBalance(1));
        Assert.Equal(0, bank.GetBalance(2));
        Assert.Equal(BankRetention.Locked, Assert.Single(bank.Balances).Retention);
    }

    [Fact]
    public void FullBankDrainsLargestDownBalanceBeforeNewLoss()
    {
        var bank = new SkillBankLedger(5);
        bank.Deposit(1, "Anatomy", 3, 1000);
        bank.Deposit(2, "Tactics", 2, 1000);
        bank.SetRetention(1, BankRetention.Down);
        bank.SetRetention(2, BankRetention.Down);

        Assert.Equal(new SkillBankDeposit(2, 0, 2), bank.Deposit(3, "Magery", 2, 1000));
        Assert.Equal(1, bank.GetBalance(1));
        Assert.Equal(2, bank.GetBalance(2));
        Assert.Equal(2, bank.GetBalance(3));
        Assert.Equal(5, bank.TotalTenths);
    }

    [Fact]
    public void TiesDrainAlphabeticallyAndZeroEntriesLoseTheirRetention()
    {
        var bank = new SkillBankLedger(2);
        bank.Deposit(1, "Tactics", 1, 1000);
        bank.Deposit(2, "Anatomy", 1, 1000);
        bank.SetRetention(1, BankRetention.Down);
        bank.SetRetention(2, BankRetention.Down);

        Assert.Equal(new SkillBankDeposit(1, 0, 1), bank.Deposit(3, "Magery", 1, 1000));
        Assert.Equal(0, bank.GetBalance(2));
        Assert.Equal(1, bank.GetBalance(1));
        Assert.Equal(BankRetention.Locked, bank.Balances.Single(balance => balance.SkillId == 3).Retention);
    }

    [Fact]
    public void IndividualCapAndConsumptionNeverMintPoints()
    {
        var bank = new SkillBankLedger(5);

        Assert.Equal(new SkillBankDeposit(2, 2, 0), bank.Deposit(1, "Anatomy", 4, 2));
        Assert.True(bank.TryConsume(1));
        Assert.True(bank.TryConsume(1));
        Assert.False(bank.TryConsume(1));
        Assert.Empty(bank.Balances);
        Assert.Equal(0, bank.TotalTenths);
    }

    [Fact]
    public void ReplacingOwnDownEntryPreservesTotalAndBalance()
    {
        var bank = new SkillBankLedger(2);
        bank.Deposit(1, "Anatomy", 2, 1000);
        bank.SetRetention(1, BankRetention.Down);

        Assert.Equal(new SkillBankDeposit(1, 0, 1), bank.Deposit(1, "Anatomy", 1, 1000));
        Assert.Equal(2, bank.GetBalance(1));
        Assert.Equal(2, bank.TotalTenths);
    }

    [Fact]
    public void SnapshotRoundTripsAndUsesCanonicalSkillNames()
    {
        var bank = new SkillBankLedger(5);
        bank.Deposit(1, "Old Anatomy Label", 3, 1000);
        bank.SetRetention(1, BankRetention.Down);

        Assert.True(SkillBankLedger.TryDeserialize(
            bank.Serialize(),
            5,
            id => id == 1 ? ("Anatomy", 1000) : null,
            out var loaded
        ));
        Assert.Equal(3, loaded.TotalTenths);
        var balance = Assert.Single(loaded.Balances);
        Assert.Equal("Anatomy", balance.SkillName);
        Assert.Equal(BankRetention.Down, balance.Retention);
    }

    [Fact]
    public void RepeatedDepositRestoreAndSnapshotSequencePreservesBalances()
    {
        static SkillBankLedger Reload(SkillBankLedger source)
        {
            Assert.True(SkillBankLedger.TryDeserialize(source.Serialize(), source.CapacityTenths,
                id => id switch { 1 => ("Anatomy", 1000), 2 => ("Tactics", 1000), _ => null }, out var loaded));
            return loaded;
        }

        var bank = new SkillBankLedger(8);
        bank.Deposit(1, "Anatomy", 3, 1000);
        Assert.True(bank.SetRetention(1, BankRetention.Down));
        bank = Reload(bank);
        Assert.Equal(3, bank.GetBalance(1));

        Assert.True(bank.TryPlanRestoration(1, 6999, 7000, [], out var belowCap));
        bank = Reload(belowCap.BankAfter);
        Assert.Equal(2, bank.GetBalance(1));
        bank.Deposit(2, "Tactics", 2, 1000);
        Assert.True(bank.SetRetention(2, BankRetention.Down));
        bank = Reload(bank);

        Assert.True(bank.TryPlanRestoration(1, 7000, 7000,
            [new SkillBankActiveSkill(2, "Tactics", 950, 1000, true)], out var atCap));
        bank = Reload(atCap.BankAfter);
        Assert.Equal(1, bank.GetBalance(1));
        Assert.Equal(3, bank.GetBalance(2));
        Assert.Equal(4, bank.TotalTenths);
        Assert.Equal(BankRetention.Down, bank.Balances.Single(balance => balance.SkillId == 2).Retention);
    }

    [Theory]
    [InlineData("not json")]
    [InlineData("null")]
    [InlineData("{}")]
    [InlineData("   ")]
    [InlineData("{\"version\":1,\"balances\":null}")]
    [InlineData("{\"version\":2,\"balances\":[]}")]
    [InlineData("{\"version\":1,\"balances\":[{\"SkillId\":99,\"Tenths\":1,\"Retention\":0}]}")]
    [InlineData("{\"version\":1,\"balances\":[{\"SkillId\":1,\"Tenths\":-1,\"Retention\":0}]}")]
    [InlineData("{\"version\":1,\"balances\":[{\"SkillId\":1,\"Tenths\":6,\"Retention\":0}]}")]
    [InlineData("{\"version\":1,\"balances\":[{\"SkillId\":1,\"Tenths\":1,\"Retention\":0},{\"SkillId\":1,\"Tenths\":1,\"Retention\":0}]}")]
    [InlineData("{\"version\":1,\"balances\":[{\"SkillId\":1,\"Tenths\":1,\"Retention\":99}]}")]
    public void InvalidSnapshotIsRejectedWithoutMinting(string payload)
    {
        Assert.False(SkillBankLedger.TryDeserialize(
            payload,
            5,
            id => id == 1 ? ("Anatomy", 1000) : null,
            out var loaded
        ));
        Assert.Equal(0, loaded.TotalTenths);
        Assert.Empty(loaded.Balances);
    }

    [Fact]
    public void OversizedSnapshotIsRejectedWithoutMinting()
    {
        Assert.False(SkillBankLedger.TryDeserialize(
            new string(' ', 65537),
            5,
            id => id == 1 ? ("Anatomy", 1000) : null,
            out var loaded
        ));
        Assert.Equal(0, loaded.TotalTenths);
        Assert.Empty(loaded.Balances);
    }

    [Fact]
    public void FreeActiveCapacityRestorationConsumesOneBankedTenth()
    {
        var bank = new SkillBankLedger();
        bank.Deposit(1, "Anatomy", 2, 1000);

        Assert.True(bank.TryPlanRestoration(1, 6999, 7000, [], out var plan));
        Assert.Null(plan.DownSkillId);
        Assert.Equal(1, plan.BankAfter.GetBalance(1));
        Assert.Equal(2, bank.GetBalance(1));
    }

    [Fact]
    public void FullActiveCapRestorationBanksDownSkillAsAnExchange()
    {
        var bank = new SkillBankLedger(1);
        bank.Deposit(1, "Anatomy", 1, 1000);

        Assert.True(bank.TryPlanRestoration(
            1,
            7000,
            7000,
            [new SkillBankActiveSkill(2, "Tactics", 100, 1000, true)],
            out var plan
        ));
        Assert.Equal(2, plan.DownSkillId);
        Assert.Equal(0, plan.BankAfter.GetBalance(1));
        Assert.Equal(1, plan.BankAfter.GetBalance(2));
        Assert.Equal(1, plan.BankAfter.TotalTenths);
        Assert.Equal(1, bank.GetBalance(1));
    }

    [Fact]
    public void FullActiveCapWithoutEligibleDownSkillDoesNotConsumeBank()
    {
        var bank = new SkillBankLedger(1);
        bank.Deposit(1, "Anatomy", 1, 1000);

        Assert.False(bank.TryPlanRestoration(
            1,
            7000,
            7000,
            [new SkillBankActiveSkill(2, "Tactics", 100, 1000, false)],
            out _
        ));
        Assert.Equal(1, bank.GetBalance(1));
        Assert.Equal(1, bank.TotalTenths);
    }

    [Fact]
    public void ExchangeSkipsDownSkillWhoseBankIsAtItsIndividualCap()
    {
        var bank = new SkillBankLedger(3);
        bank.Deposit(1, "Anatomy", 1, 1000);
        bank.Deposit(2, "Tactics", 1, 1);

        Assert.True(bank.TryPlanRestoration(
            1,
            7000,
            7000,
            [
                new SkillBankActiveSkill(2, "Tactics", 100, 1, true),
                new SkillBankActiveSkill(3, "Magery", 100, 1000, true)
            ],
            out var plan
        ));
        Assert.Equal(3, plan.DownSkillId);
        Assert.Equal(1, plan.BankAfter.GetBalance(2));
        Assert.Equal(1, plan.BankAfter.GetBalance(3));
        Assert.Equal(1, bank.GetBalance(1));
    }

    [Fact]
    public void MixedDepositsRetentionAndFullCapExchangesPreserveBankInvariants()
    {
        var random = new Random(23197);
        var bank = new SkillBankLedger(7);
        var names = new[] { "Anatomy", "Magery", "Tactics" };

        for (var turn = 0; turn < 1000; turn++)
        {
            var skillId = random.Next(names.Length);
            switch (random.Next(4))
            {
                case 0:
                    bank.Deposit(skillId, names[skillId], random.Next(1, 4), 5);
                    break;
                case 1:
                    bank.SetRetention(skillId, random.Next(2) == 0 ? BankRetention.Locked : BankRetention.Down);
                    break;
                case 2:
                    bank.TryConsume(skillId);
                    break;
                case 3:
                    if (bank.TryPlanRestoration(
                            skillId, 7000, 7000,
                            Enumerable.Range(0, names.Length).Select(id =>
                                new SkillBankActiveSkill(id, names[id], 100, 5, true)),
                            out var plan
                        ))
                    {
                        Assert.NotNull(plan.DownSkillId);
                        Assert.Equal(bank.TotalTenths, plan.BankAfter.TotalTenths);
                        bank = plan.BankAfter;
                    }
                    break;
            }

            Assert.Equal(bank.TotalTenths, bank.Balances.Sum(balance => balance.Tenths));
            Assert.InRange(bank.TotalTenths, 0, bank.CapacityTenths);
            Assert.All(bank.Balances, balance => Assert.InRange(balance.Tenths, 1, 5));
            Assert.Equal(bank.Balances.Count, bank.Balances.Select(balance => balance.SkillId).Distinct().Count());
        }
    }

    [Fact]
    public void CapacityStatusWarnsBeforeLossAndExplainsFullBankReplacement()
    {
        var bank = new SkillBankLedger(10);
        bank.Deposit(1, "Anatomy", 9, 1000);

        Assert.Contains("0.1 points remain", Assert.Single(SkillBankService.DescribeCapacityRisk(bank)));

        bank.Deposit(1, "Anatomy", 1, 1000);
        Assert.Contains("cannot be banked", Assert.Single(SkillBankService.DescribeCapacityRisk(bank)));

        Assert.True(bank.SetRetention(1, BankRetention.Down));
        Assert.Contains("may replace", Assert.Single(SkillBankService.DescribeCapacityRisk(bank)));
    }

}
