using Server;
using Server.Accounting;
using Server.Engines.CharacterCreation;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

public interface IStarterIssued
{
}

/// <summary>
/// One ordinary pair issued at creation. Its type remains an economic marker after
/// the four logged-in hours of death protection have expired.
/// </summary>
public sealed class StarterScissors : Scissors, IStarterIssued
{
    public static readonly TimeSpan ProtectionDuration = TimeSpan.FromHours(4);

    public StarterScissors(PlayerMobile owner)
    {
        OwnerSerial = owner.Serial;
    }

    public StarterScissors(Serial serial) : base(serial)
    {
    }

    public Serial OwnerSerial { get; private set; }

    // Stock transfer and vendor checks use this property. The marker is permanent;
    // death routing below has its own time-limited rule.
    public override bool Nontransferable => true;

    public static bool IsProtected(TimeSpan ownerGameTime) => ownerGameTime < ProtectionDuration;

    private bool IsProtectedFor(Mobile parent) =>
        parent is PlayerMobile player && player.Serial == OwnerSerial && IsProtected(player.GameTime);

    public override DeathMoveResult OnInventoryDeath(Mobile parent) =>
        IsProtectedFor(parent) || KeepByOrdinaryDeathRules(parent)
            ? DeathMoveResult.MoveToBackpack
            : DeathMoveResult.MoveToCorpse;

    public override DeathMoveResult OnParentDeath(Mobile parent)
    {
        if (!Movable)
        {
            return DeathMoveResult.RemainEquipped;
        }

        return IsProtectedFor(parent) || KeepByOrdinaryDeathRules(parent)
            ? DeathMoveResult.MoveToBackpack
            : DeathMoveResult.MoveToCorpse;
    }

    private bool KeepByOrdinaryDeathRules(Mobile parent) =>
        !Movable || parent.KeepsItemsOnDeath || CheckBlessed(parent) ||
        CheckNewbied() && !parent.Murderer;

    public override void Serialize(IGenericWriter writer)
    {
        base.Serialize(writer);
        writer.WriteEncodedInt(0);
        writer.Write(OwnerSerial);
    }

    public override void Deserialize(IGenericReader reader)
    {
        base.Deserialize(reader);
        _ = reader.ReadEncodedInt();
        OwnerSerial = reader.ReadSerial();
    }
}

public static class StarterScissorsIssuance
{
    private const string IssuanceTagPrefix = "BritanniaRenaissance.StarterScissors.v1.";
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CharacterCreation.CharacterCreatedHandler += Issue;
    }

    public static void Issue(CharacterCreatedEventArgs args)
    {
        if (ShardRulesConfiguration.Settings?.FeatureFlags.Alpha3StarterScissors != true ||
            args.Mobile is not PlayerMobile { AccessLevel: AccessLevel.Player, Backpack: not null } player ||
            player.Account is not Account account)
        {
            return;
        }

        var tag = $"{IssuanceTagPrefix}{player.Serial.Value}";
        if (account.GetTag(tag) is not null)
        {
            return;
        }

        // Stock skill packages can issue one or more unmarked pairs before this hook runs.
        var stockPairs = new List<Scissors>();
        foreach (var item in player.Backpack.Items)
        {
            if (item.GetType() == typeof(Scissors))
            {
                stockPairs.Add((Scissors)item);
            }
        }

        foreach (var stockPair in stockPairs)
        {
            stockPair.Delete();
        }

        player.Backpack.DropItem(new StarterScissors(player));
        account.SetTag(tag, "issued");
    }
}
