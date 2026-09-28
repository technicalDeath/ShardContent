using Server;
using Server.Accounting;
using Server.Engines.CharacterCreation;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>An ordinary organization bag issued once at character creation.</summary>
public sealed class StarterBag : Bag, IStarterIssued
{
    public static readonly TimeSpan ProtectionDuration = TimeSpan.FromHours(4);

    public StarterBag(PlayerMobile owner)
    {
        OwnerSerial = owner.Serial;
    }

    public StarterBag(Serial serial) : base(serial)
    {
    }

    public Serial OwnerSerial { get; private set; }

    public override bool Nontransferable => true;

    public override string DefaultName => "a starter bag";

    public static bool IsProtected(TimeSpan ownerGameTime) => ownerGameTime < ProtectionDuration;

    public override DeathMoveResult OnInventoryDeath(Mobile parent) =>
        IsProtectedFor(parent) || KeepByOrdinaryDeathRules(parent)
            ? DeathMoveResult.MoveToBackpack
            : DeathMoveResult.MoveToCorpse;

    public override DeathMoveResult OnParentDeath(Mobile parent) => OnInventoryDeath(parent);

    private bool IsProtectedFor(Mobile parent) =>
        parent is PlayerMobile player && player.Serial == OwnerSerial && IsProtected(player.GameTime);

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

public static class StarterBagIssuance
{
    private const string IssuanceTagPrefix = "BritanniaRenaissance.StarterBag.v1.";
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CharacterCreation.CharacterCreatedHandler += Issue;
        PlayerMobile.PlayerDeathHandler += RouteContentsOnDeath;
    }

    public static void Issue(CharacterCreatedEventArgs args)
    {
        if (ShardRulesConfiguration.Settings?.FeatureFlags.Alpha3StarterBag != true ||
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

        player.Backpack.DropItem(new StarterBag(player));
        account.SetTag(tag, "issued");
    }

    private static void RouteContentsOnDeath(PlayerMobile player)
    {
        if (player.Backpack is null || player.Corpse is not Corpse corpse)
        {
            return;
        }

        var bags = new List<StarterBag>();
        foreach (var bag in player.Backpack.FindItemsByType<StarterBag>())
        {
            bags.Add(bag);
        }

        foreach (var bag in corpse.FindItemsByType<StarterBag>())
        {
            bags.Add(bag);
        }

        foreach (var bag in bags)
        {
            var contents = new List<Item>();
            CollectContentsPostorder(bag, contents);
            foreach (var item in contents)
            {
                if (item.Deleted)
                {
                    continue;
                }

                if (player.GetInventoryMoveResultFor(item) == DeathMoveResult.MoveToCorpse)
                {
                    corpse.DropItem(item);
                }
                else
                {
                    player.Backpack.DropItem(item);
                }
            }
        }
    }

    private static void CollectContentsPostorder(Container container, List<Item> contents)
    {
        foreach (var item in container.Items)
        {
            if (item is Container childContainer)
            {
                CollectContentsPostorder(childContainer, contents);
            }

            contents.Add(item);
        }
    }
}
