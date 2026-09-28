namespace BritanniaRenaissance.Content;

public enum HousingLandClass
{
    Residential,
    FireIslandResidential,
    Rural,
    Protected
}

public readonly record struct HousingPlacementQuote(
    int NormalValue,
    int RuralPremium,
    int DueAtPlacement,
    int TotalEconomicCost
);

public static class HousingPlacementEconomics
{
    public static bool TryQuote(
        HousingLandClass landClass,
        int normalValue,
        bool normalValueAlreadyPaid,
        out HousingPlacementQuote quote,
        decimal ruralCostMultiplier = 2m
    )
    {
        quote = default;
        if (!Enum.IsDefined(landClass) || landClass == HousingLandClass.Protected || normalValue <= 0 ||
            ruralCostMultiplier is < 2m or > 5m)
        {
            return false;
        }

        var premiumValue = landClass == HousingLandClass.Rural
            ? decimal.Ceiling(normalValue * (ruralCostMultiplier - 1m))
            : 0m;
        if (premiumValue > int.MaxValue)
        {
            return false;
        }

        var premium = (int)premiumValue;
        var due = (long)(normalValueAlreadyPaid ? 0 : normalValue) + premium;
        var total = (long)normalValue + premium;
        if (due > int.MaxValue || total > int.MaxValue)
        {
            return false;
        }

        quote = new HousingPlacementQuote(normalValue, premium, (int)due, (int)total);
        return true;
    }
}
