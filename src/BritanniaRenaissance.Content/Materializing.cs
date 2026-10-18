using Server;
using Server.Engines.BuffIcons;
using Server.Gumps;
using Server.Items;
using Server.Mobiles;
using Server.Network;
using Server.Spells;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Materializing (<c>featureFlags.materializing</c>, docs/Death-Recovery-Plan.md), the owner's design (2026-10-16/17): after any resurrection a player is
/// between ghost and fully alive. Monsters cannot see them (the creature-sight hook), and other players see them in a ghostly hue. Moving items between
/// their pack, bank and own corpse and putting on gear keeps the state; any other action (an item use, a skill, a spell, an attack, a lift from anywhere
/// else, buying or selling) is held and a dialog asks first, like the client's criminal-action query (the owner, 2026-10-17: "The materializing warning
/// should be a dialog like the criminal action warning"): OKAY ends materializing and carries the action out, CANCEL keeps it. It ends by itself <see cref="DeathRecoveryRules.MaterializingAfterOpenSeconds"/> after the player first opens their own corpse, or after
/// <see cref="DeathRecoveryRules.MaterializingMinutes"/> at most, or on death or logout. Nothing is saved: a restart simply ends it.
/// </summary>
public static class Materializing
{
    public const BuffIcon Icon = BuffIcon.HidingAndOrStealth;

    /// <summary>What players see it called (the owner, 2026-10-17: "Rename materializing to between worlds with the b and in the w capitalized"); code and the flag keep "materializing".</summary>
    public const string Name = "Between Worlds";

    public const string Warning = "This will bring you fully back from Between Worlds, and monsters will be able to see you again.";
    public const string Ended = "You are fully back in the world. Monsters can see you again.";
    public const string Kept = "You stay Between Worlds.";
    public const string LiftAgain = "Pick it up again.";

    private static bool _configured;
    private static readonly Dictionary<PlayerMobile, State> States = [];

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.Materializing == true;

    private sealed class State
    {
        public DateTime Started;
        public DateTime? Opened;
        public bool Hued;
    }

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        PlayerMobile.Resurrected += Start;
        PlayerMobile.ActionGate = Gate;
        PlayerMobile.PlayerDeathHandler += player => End(player, null);
        Corpse.OwnerOpened += (owner, _) =>
        {
            if (owner is PlayerMobile player && States.TryGetValue(player, out var state) && state.Opened is null)
            {
                state.Opened = Core.Now;
                ShowBuff(player, Until(state, DeathRecovery.Rules) - Core.Now);
            }
        };
        EventSink.Logout += m =>
        {
            if (m is PlayerMobile player)
            {
                End(player, null);
            }
        };
        Server.Timer.StartTimer(TimeSpan.FromSeconds(1), TimeSpan.FromSeconds(1), Tick);
    }

    public static bool IsMaterializing(PlayerMobile player) => States.ContainsKey(player);

    public static string StartText(DeathRecoveryRules rules) =>
        $"You are Between Worlds: monsters cannot see you for up to {rules.MaterializingMinutes} minutes, or until {rules.MaterializingAfterOpenSeconds} seconds " +
        "after you open your corpse. Taking things from your corpse, sorting your pack and putting on your gear keep you there; any other action asks you first, even taking from your bank.";

    /// <summary>When the state ends by itself: the earlier of the longest time and the time after the corpse was first opened.</summary>
    public static DateTime Until(DateTime started, DateTime? opened, DeathRecoveryRules rules)
    {
        var longest = started + TimeSpan.FromMinutes(rules.MaterializingMinutes);
        return opened is { } at && at + TimeSpan.FromSeconds(rules.MaterializingAfterOpenSeconds) < longest
            ? at + TimeSpan.FromSeconds(rules.MaterializingAfterOpenSeconds)
            : longest;
    }

    private static DateTime Until(State state, DeathRecoveryRules rules) => Until(state.Started, state.Opened, rules);

    /// <summary>What the action is on, as the rule needs it.</summary>
    public enum Target
    {
        Other,
        Door,
        OwnContainer,
        OwnCorpse,
        CorpseItem,
        BankItem,
        OwnGear,
        OwnItem
    }

    /// <summary>
    /// Whether an action keeps a player Between Worlds. Looking is free: a door, one's own pack, bank or a bag in them, one's own corpse or a bag in it.
    /// Taking from the corpse is free (the owner, 2026-10-17: "only allow them to pick up items from their corpse that way they can't equip a bunch of stuff
    /// they want to use after dying and while in the between world state to go where they want to go"), and so is one's own pack and worn gear ("Equipping
    /// items from your own inventory / pack should not take you out of it this way you can get your corpse items and get situated before you perform it in
    /// world action that will take you out"). The bank is not: after a death the pack holds only kept starting items and what came off the corpse, while the
    /// bank could arm a player for the walk. Anything taken from the bank, and anything else, asks first.
    /// </summary>
    public static bool Keeps(PlayerAction action, Target target) =>
        action switch
        {
            PlayerAction.UseItem => target is Target.Door or Target.OwnContainer or Target.OwnCorpse or Target.OwnGear,
            PlayerAction.Lift    => target is Target.CorpseItem or Target.OwnGear or Target.OwnItem,
            _                    => false
        };

    /// <summary>The creature-sight hook: a monster cannot see a player Between Worlds; townsfolk still can, so the banker and the healer answer.</summary>
    public static bool Hides(BaseCreature creature, PlayerMobile player) => States.Count > 0 && States.ContainsKey(player) && DeathRecovery.IsMonster(creature);

    private static void Start(PlayerMobile player)
    {
        if (!Enabled || player.Deleted || !player.Alive)
        {
            return;
        }

        var rules = DeathRecovery.Rules;
        var state = new State { Started = Core.Now };
        States[player] = state;

        if (player.SolidHueOverride == -1)
        {
            player.SolidHueOverride = rules.MaterializingHue;
            state.Hued = true;
        }

        // anything already fighting the player lets go
        foreach (var creature in player.GetMobilesInRange<BaseCreature>(Core.GlobalUpdateRange))
        {
            if (creature.Combatant == player && DeathRecovery.IsWild(creature))
            {
                creature.Combatant = null;
                creature.FocusMob = null;
            }
        }

        ShowBuff(player, Until(state, rules) - state.Started);
        player.SendMessage(0x35, StartText(rules));
    }

    private static void ShowBuff(PlayerMobile player, TimeSpan left) =>
        player.AddBuff(
            new BuffInfo(
                Icon,
                BuffIconCatalog.GenericTitleCliloc,
                0,
                left,
                "Between Worlds<br>Monsters cannot see you. Taking things from your corpse, sorting your pack and putting on your gear keep you here; any other action asks you first."
            )
        );

    private static bool Gate(PlayerMobile player, PlayerAction action, object on)
    {
        if (States.Count == 0 || !States.ContainsKey(player) || Keeps(action, Classify(player, on)))
        {
            return true;
        }

        player.SendGump(new ConfirmGump(action, on));
        return false;
    }

    /// <summary>The action again, after OKAY: everything the server can start itself. A lift is the player dragging, so they are asked to pick it up again.</summary>
    private static void Replay(PlayerMobile player, PlayerAction action, object on)
    {
        switch (action)
        {
            case PlayerAction.UseItem when on is Item { Deleted: false } item:
                player.Use(item);
                break;
            case PlayerAction.UseSkill when on is SkillName skill:
                Skills.UseSkill(player, skill);
                break;
            case PlayerAction.CastSpell when on is Spell spell:
                spell.Cast();
                break;
            case PlayerAction.Attack when on is Mobile { Deleted: false } target:
                player.Attack(target);
                break;
            case PlayerAction.Buy when on is BaseVendor { Deleted: false } vendor:
                vendor.VendorBuy(player);
                break;
            case PlayerAction.Sell when on is BaseVendor { Deleted: false } vendor:
                vendor.VendorSell(player);
                break;
            case PlayerAction.Lift:
                player.SendMessage(0x35, LiftAgain);
                break;
        }
    }

    /// <summary>The OKAY/CANCEL question, in the shard dialog style (docs/Gump-Style-Guide.md), like the Hot Zone travel warning.</summary>
    public sealed class ConfirmGump : DynamicGump
    {
        public const int Height = 220;
        private const int TextWidth = GumpStyle.DialogWidth - 2 * GumpStyle.Margin;

        private readonly PlayerAction _action;
        private readonly object _on;

        public override bool Singleton => true;

        public ConfirmGump(PlayerAction action, object on) : base(GumpStyle.DialogX, GumpStyle.DialogY)
        {
            _action = action;
            _on = on;
        }

        protected override void BuildLayout(ref DynamicGumpBuilder builder)
        {
            builder.AddPage();
            GumpStyle.Frame(ref builder, Name, "Come fully back?", GumpStyle.DialogWidth, Height);
            GumpStyle.Banner(ref builder, BannerKind.Danger, Warning, width: TextWidth - 38, height: 54);
            GumpStyle.Rule(ref builder, GumpStyle.RuleInset, Height - GumpStyle.FooterRoom, GumpStyle.DialogWidth - 2 * GumpStyle.RuleInset);
            GumpStyle.OkayCancel(
                ref builder, GumpStyle.Margin, GumpStyle.DialogWidth - GumpStyle.Margin - GumpStyle.OvalWidths[0], GumpStyle.FooterButtonsY(Height), 1, 0
            );
        }

        public override void OnResponse(NetState sender, in RelayInfo info)
        {
            if (sender.Mobile is not PlayerMobile player || !States.ContainsKey(player))
            {
                return;
            }

            if (info.ButtonID != 1)
            {
                // CANCEL or a right-click
                player.SendMessage(0x35, Kept);
                return;
            }

            End(player, Ended);
            Replay(player, _action, _on);
        }
    }

    private static Target Classify(PlayerMobile player, object on)
    {
        if (on is not Item item)
        {
            return Target.Other;
        }

        var bank = player.FindBankNoCreate();

        return item switch
        {
            BaseDoor                                                                => Target.Door,
            Corpse corpse when corpse.Owner == player                               => Target.OwnCorpse,
            Container when item.RootParent is Corpse { } c && c.Owner == player     => Target.OwnContainer,
            _ when item.RootParent is Corpse { } c && c.Owner == player             => Target.CorpseItem,
            Container c when c == player.Backpack || c == bank || Within(c, player, bank) => Target.OwnContainer,
            _ when bank is not null && item.IsChildOf(bank)                         => Target.BankItem,
            BaseWeapon or BaseArmor or BaseClothing or BaseJewel when Mine(item, player, bank) => Target.OwnGear,
            _ when Mine(item, player, bank)                                          => Target.OwnItem,
            _                                                                       => Target.Other
        };
    }

    private static bool Within(Item item, PlayerMobile player, BankBox? bank) =>
        player.Backpack is { } pack && item.IsChildOf(pack) || bank is not null && item.IsChildOf(bank);

    private static bool Mine(Item item, PlayerMobile player, BankBox? bank) => item.Parent == player || Within(item, player, bank);

    private static void Tick()
    {
        if (States.Count == 0)
        {
            return;
        }

        var now = Core.Now;
        var rules = DeathRecovery.Rules;
        using var done = Server.Collections.PooledRefList<PlayerMobile>.Create();

        foreach (var (player, state) in States)
        {
            if (player.Deleted || !player.Alive || now >= Until(state, rules))
            {
                done.Add(player);
            }
        }

        foreach (var player in done)
        {
            End(player, player.Alive ? Ended : null);
        }
    }

    private static void End(PlayerMobile player, string? message)
    {
        if (!States.Remove(player, out var state))
        {
            return;
        }

        if (state.Hued && player.SolidHueOverride == DeathRecovery.Rules.MaterializingHue)
        {
            player.SolidHueOverride = -1;
        }

        player.RemoveBuff(Icon);

        if (message is not null)
        {
            player.SendMessage(0x35, message);
        }
    }
}
