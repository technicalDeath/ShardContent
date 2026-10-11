using System.Globalization;
using BritanniaRenaissance.Content;
using Server;
using Server.Commands;
using Server.Items;
using Server.Mobiles;

namespace NoviceCombatTools;

// Test-only, disposable-host-only. Reports go back to the staff caller as system messages; the real engine formulas run (BaseWeapon.CheckHit,
// GetDelay, ScaleDamageOld), the flag is switched in memory for the length of a run.
//   [TestOnlyNoviceFlag on|off|status]
//   [TestOnlyCombatHit <attacker> <defender> <attacker-skill> <n> <on|off|asis>]  n real CheckHit calls with the attacker's weapon skill held at that value
//   [TestOnlyCombatDelay <mobile> <stamina> <on|off|asis>]                         the weapon's swing delay with that stamina
//   [TestOnlyCombatDamage <mobile> <tactics> <on|off|asis>]                        ScaleDamageOld(100) with that Tactics value
//   [TestOnlyCombatSpawn <player> <orc-wrestling> [dx]]                            an Orc with that Wrestling next to the player, serial reported
//   [TestOnlyCombatEquip <player> <bow|katana>]                                    replaces what the player holds with a fresh weapon of that kind
// <attacker> and <defender> are a hex serial (a player or any mobile) or "orc:<wrestling>" (a throwaway Orc with that Wrestling, at the staff caller).
public static class NoviceCombatProbe
{
    public static void Configure()
    {
        CommandSystem.Register("TestOnlyNoviceFlag", AccessLevel.Administrator, OnFlag);
        CommandSystem.Register("TestOnlyCombatHit", AccessLevel.Administrator, OnHit);
        CommandSystem.Register("TestOnlyCombatDelay", AccessLevel.Administrator, OnDelay);
        CommandSystem.Register("TestOnlyCombatDamage", AccessLevel.Administrator, OnDamage);
        CommandSystem.Register("TestOnlyCombatSpawn", AccessLevel.Administrator, OnSpawn);
        CommandSystem.Register("TestOnlyCombatEquip", AccessLevel.Administrator, OnEquip);
    }

    private static DeferredFeatureFlags Flags => ShardRulesConfiguration.Settings!.FeatureFlags;

    private static void OnFlag(CommandEventArgs e)
    {
        var mode = e.Length > 0 ? e.GetString(0).ToLowerInvariant() : "status";

        if (mode == "on")
        {
            Flags.NoviceCombat = true;
        }
        else if (mode == "off")
        {
            Flags.NoviceCombat = false;
        }

        e.Mobile.SendMessage($"NoviceFlag on={Flags.NoviceCombat}");
    }

    private static Mobile? Resolve(CommandEventArgs e, string spec, Mobile caller, List<Mobile> temporary)
    {
        if (spec.StartsWith("orc:", StringComparison.OrdinalIgnoreCase) &&
            double.TryParse(spec[4..], NumberStyles.Float, CultureInfo.InvariantCulture, out var wrestling))
        {
            var orc = new Orc();
            orc.Skills.Wrestling.Base = wrestling;
            orc.RawStr = 100; // a fixed strength, so two throwaway Orcs deal the same damage
            orc.MoveToWorld(caller.Location, caller.Map);
            temporary.Add(orc);
            return orc;
        }

        var hex = spec.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? spec[2..] : spec;
        return uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) ? World.FindMobile((Serial)serial) : null;
    }

    private static T WithMode<T>(string mode, Func<T> body)
    {
        var original = Flags.NoviceCombat;

        try
        {
            if (mode is "on" or "off")
            {
                Flags.NoviceCombat = mode == "on";
            }

            return body();
        }
        finally
        {
            Flags.NoviceCombat = original;
        }
    }

    private static string Kind(Mobile m) => m is PlayerMobile pm ? (pm.AccessLevel == AccessLevel.Player ? "player" : "staff") : "monster";

    private static void OnHit(CommandEventArgs e)
    {
        var temporary = new List<Mobile>();

        try
        {
            if (e.Length < 5 || Resolve(e, e.GetString(0), e.Mobile, temporary) is not { } attacker ||
                Resolve(e, e.GetString(1), e.Mobile, temporary) is not { } defender ||
                !double.TryParse(e.GetString(2), NumberStyles.Float, CultureInfo.InvariantCulture, out var value) ||
                !int.TryParse(e.GetString(3), out var n))
            {
                e.Mobile.SendMessage("Usage: [TestOnlyCombatHit <attacker> <defender> <attacker-skill> <n> <on|off|asis>");
                return;
            }

            var mode = e.GetString(4).ToLowerInvariant();

            if (attacker.Weapon is not BaseWeapon weapon)
            {
                e.Mobile.SendMessage("CombatHit error=no-weapon");
                return;
            }

            var skill = attacker.Skills[weapon.GetUsedSkill(attacker, true)];
            var original = skill.BaseFixedPoint;
            var start = (int)Math.Round(value * 10);
            skill.BaseFixedPoint = start;
            var effective = skill.Value; // the engine rolls with Skill.Value: the base plus the stat bonus
            var defendSkill = (defender.Weapon as BaseWeapon)?.GetDefendSkillValue(attacker, defender) ?? 0.0;

            var (hits, gains) = WithMode(mode, () =>
            {
                var h = 0;
                var g = 0;

                for (var i = 0; i < n; i++)
                {
                    skill.BaseFixedPoint = start;

                    if (weapon.CheckHit(attacker, defender))
                    {
                        h++;
                    }

                    if (skill.BaseFixedPoint > start)
                    {
                        g++;
                    }
                }

                return (h, g);
            });

            skill.BaseFixedPoint = original;
            var stock = Math.Min(1.0, (effective + 50.0) / ((defendSkill + 50.0) * 2.0));
            e.Mobile.SendMessage(
                string.Create(
                    CultureInfo.InvariantCulture,
                    $"CombatHit mode={mode} n={n} hits={hits} gains={gains} atkSkill={value} atkEff={effective:0.###} defSkill={defendSkill:0.###} stock={stock:0.0000} attacker={Kind(attacker)} defender={Kind(defender)} usedSkill={skill.SkillName}"
                )
            );
        }
        finally
        {
            foreach (var mobile in temporary)
            {
                mobile.Delete();
            }
        }
    }

    private static void OnDelay(CommandEventArgs e)
    {
        var temporary = new List<Mobile>();

        try
        {
            if (e.Length < 3 || Resolve(e, e.GetString(0), e.Mobile, temporary) is not { } mobile || !int.TryParse(e.GetString(1), out var stamina) ||
                mobile.Weapon is not BaseWeapon weapon)
            {
                e.Mobile.SendMessage("Usage: [TestOnlyCombatDelay <mobile> <stamina> <on|off|asis>");
                return;
            }

            var originalStamina = mobile.Stam;
            mobile.Stam = Math.Min(stamina, mobile.StamMax);
            var used = mobile.Stam;
            var seconds = WithMode(e.GetString(2).ToLowerInvariant(), () => weapon.GetDelay(mobile).TotalSeconds);
            mobile.Stam = originalStamina;
            e.Mobile.SendMessage(
                string.Create(CultureInfo.InvariantCulture, $"CombatDelay seconds={seconds:0.0000} stam={used} stamMax={mobile.StamMax} speed={weapon.Speed} kind={Kind(mobile)} weapon={weapon.GetType().Name}")
            );
        }
        finally
        {
            foreach (var mobile in temporary)
            {
                mobile.Delete();
            }
        }
    }

    private static void OnDamage(CommandEventArgs e)
    {
        var temporary = new List<Mobile>();

        try
        {
            if (e.Length < 3 || Resolve(e, e.GetString(0), e.Mobile, temporary) is not { } mobile ||
                !double.TryParse(e.GetString(1), NumberStyles.Float, CultureInfo.InvariantCulture, out var tactics) || mobile.Weapon is not BaseWeapon weapon)
            {
                e.Mobile.SendMessage("Usage: [TestOnlyCombatDamage <mobile> <tactics> <on|off|asis>");
                return;
            }

            var original = mobile.Skills.Tactics.Base;
            mobile.Skills.Tactics.Base = tactics;
            var scaled = WithMode(e.GetString(2).ToLowerInvariant(), () => weapon.ScaleDamageOld(mobile, 100.0, false));
            mobile.Skills.Tactics.Base = original;
            e.Mobile.SendMessage(
                string.Create(
                    CultureInfo.InvariantCulture,
                    $"CombatDamage scaled={scaled:0.####} tactics={tactics} str={mobile.Str} anatomy={mobile.Skills.Anatomy.Value:0.#} kind={Kind(mobile)}"
                )
            );
        }
        finally
        {
            foreach (var mobile in temporary)
            {
                mobile.Delete();
            }
        }
    }

    private static void OnEquip(CommandEventArgs e)
    {
        if (e.Length < 2 || Resolve(e, e.GetString(0), e.Mobile, new List<Mobile>()) is not { } who)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyCombatEquip <player> <bow|katana>");
            return;
        }

        BaseWeapon weapon = e.GetString(1).Equals("katana", StringComparison.OrdinalIgnoreCase) ? new Katana() : new Bow();

        foreach (var layer in new[] { Layer.OneHanded, Layer.TwoHanded })
        {
            if (who.FindItemOnLayer(layer) is BaseWeapon held && (layer == weapon.Layer || weapon.Layer == Layer.TwoHanded))
            {
                held.Delete();
            }
        }

        if (weapon.Layer == Layer.TwoHanded && who.FindItemOnLayer(Layer.OneHanded) is BaseWeapon oneHand)
        {
            oneHand.Delete();
        }

        who.AddItem(weapon);
        e.Mobile.SendMessage($"CombatEquip weapon={weapon.GetType().Name} held={who.Weapon.GetType().Name} skill={weapon.GetUsedSkill(who, true)}");
    }

    private static void OnSpawn(CommandEventArgs e)
    {
        if (e.Length < 2 || Resolve(e, e.GetString(0), e.Mobile, new List<Mobile>()) is not { } player ||
            !double.TryParse(e.GetString(1), NumberStyles.Float, CultureInfo.InvariantCulture, out var wrestling))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyCombatSpawn <player> <orc-wrestling> [dx]");
            return;
        }

        var dx = e.Length > 2 && int.TryParse(e.GetString(2), out var d) ? d : 3;
        var orc = new Orc();
        orc.Skills.Wrestling.Base = wrestling;
        orc.MoveToWorld(new Point3D(player.X + dx, player.Y, player.Z), player.Map);
        e.Mobile.SendMessage($"CombatSpawn serial=0x{orc.Serial.Value:X8} hits={orc.HitsMax}");
    }
}
