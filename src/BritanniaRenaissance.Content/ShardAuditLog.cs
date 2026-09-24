using Server;
using Server.Accounting;
using Server.Logging;

namespace BritanniaRenaissance.Content;

/// <summary>Stable, low-volume Alpha 2 decision audit events for staff investigation.</summary>
public static class ShardAuditLog
{
    private static readonly ILogger Logger = LogFactory.GetLogger(typeof(ShardAuditLog));

    public static void Record(string category, string decision, Mobile? subject = null, Mobile? other = null,
        string? details = null)
    {
        Logger.Information(
            "Alpha2 {Category} {Decision}: subject={Subject}; other={Other}; details={Details}",
            category,
            decision,
            Identity(subject),
            Identity(other),
            details ?? string.Empty
        );
    }

    private static string Identity(Mobile? mobile)
    {
        if (mobile is null)
        {
            return "none";
        }

        var account = mobile.Account as Account;
        return account is null ? mobile.Serial.ToString() : $"{mobile.Serial}/{account.Username}";
    }
}
