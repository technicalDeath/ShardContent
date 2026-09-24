using System.Globalization;
using Server;
using Server.Accounting;
using Server.Items;
using Server.Mobiles;
using Server.SkillHandlers;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Feature-gated Backpack Ward behavior layered around stock Stealing. Bank polygons, the Cool
/// Dungeon, and the invisible corpse-loot ward remain separate region/corpse work; this service
/// only handles the physical backpack item and its post-resolution detection contract.
/// </summary>
public static class TheftProtectionService
{
    private const string ProtectionTagPrefix = "BritanniaRenaissance.BackpackWard.ProtectedUntil.";
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.TheftProtection == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        Stealing.TheftEligibility = CanAttemptTheft;
        Stealing.TheftResolved = ResolveTheft;
    }

    public static bool IsProtectionWindowActive(DateTime nowUtc, DateTime protectedUntilUtc) =>
        protectedUntilUtc.ToUniversalTime() > nowUtc.ToUniversalTime();

    public static double AdditionalDetectionChance(int successfulUndetectedThefts) =>
        successfulUndetectedThefts switch
        {
            <= 0 => 0.0,
            1 => 0.25,
            2 => 0.50,
            _ => 1.0
        };

    public static IEnumerable<string> DescribeStatus(Mobile mobile)
    {
        yield return $"Backpack Ward protection enabled: {Enabled}.";
        yield return "Stock stealing success, criminality and snooping remain authoritative.";
        yield return "Bank polygons, Cool Dungeon restrictions and Loot Protection Ward are not enabled by this slice.";

        if (mobile is PlayerMobile player)
        {
            yield return $"Equipped-backpack wards present: {(FindEligibleWard(player) is not null ? "yes" : "no")}.";
        }
    }

    private static bool CanAttemptTheft(Mobile thief, Item item, Mobile victim)
    {
        if (!Enabled || victim is not PlayerMobile playerVictim)
        {
            return true;
        }

        if (item is BackpackWard)
        {
            thief.SendMessage("That ward cannot be stolen.");
            return false;
        }

        if (IsProtectionActive(playerVictim))
        {
            thief.SendMessage("That backpack is protected from stealing for a short time.");
            return false;
        }

        return true;
    }

    private static void ResolveTheft(Mobile thief, Item item, Mobile victim, Item stolen, bool caught)
    {
        if (!Enabled || victim is not PlayerMobile playerVictim || thief is not PlayerMobile playerThief ||
            playerVictim == playerThief)
        {
            return;
        }

        var ward = FindEligibleWard(playerVictim);
        if (ward is null)
        {
            return;
        }

        // Ordinary victim detection, including a detected failure, consumes one physical ward
        // after the stock outcome has resolved.
        if (caught)
        {
            ActivateProtection(playerVictim, ward);
            return;
        }

        // Only an undetected successful transfer advances the per-thief account counter.
        if (stolen is null || playerThief.Account is not Account account)
        {
            return;
        }

        var successes = ward.RecordSuccessfulTheft(account.Username);
        if (AdditionalDetectionChance(successes) >= Utility.RandomDouble())
        {
            playerVictim.SendMessage("You detect a theft from your backpack.");
            ActivateProtection(playerVictim, ward);
        }
    }

    private static BackpackWard? FindEligibleWard(PlayerMobile victim)
    {
        var backpack = victim.Backpack;
        if (backpack is null)
        {
            return null;
        }

        var wards = new List<BackpackWard>();
        CollectWards(backpack, wards);
        wards.Sort(static (left, right) => left.Serial.Value.CompareTo(right.Serial.Value));
        return wards.Count == 0 ? null : wards[0];
    }

    private static void CollectWards(Container container, List<BackpackWard> wards)
    {
        foreach (var item in container.Items)
        {
            if (item is BackpackWard ward && !ward.Deleted)
            {
                wards.Add(ward);
            }

            if (item is Container child)
            {
                CollectWards(child, wards);
            }
        }
    }

    private static bool IsProtectionActive(PlayerMobile victim)
    {
        if (victim.Account is not Account account ||
            !DateTime.TryParse(
                account.GetTag(ProtectionTag(victim)),
                CultureInfo.InvariantCulture,
                DateTimeStyles.RoundtripKind,
                out var protectedUntil
            ))
        {
            return false;
        }

        return IsProtectionWindowActive(Core.Now, protectedUntil);
    }

    private static void ActivateProtection(PlayerMobile victim, BackpackWard ward)
    {
        if (victim.Account is Account account)
        {
            account.SetTag(
                ProtectionTag(victim),
                Core.Now.AddSeconds(120).ToString("O", CultureInfo.InvariantCulture)
            );
        }

        victim.SendMessage("Your backpack ward activates and protects you from stealing for two minutes.");
        ward.Delete();
    }

    private static string ProtectionTag(PlayerMobile victim) =>
        ProtectionTagPrefix + victim.Serial.Value.ToString("X8", CultureInfo.InvariantCulture);
}
