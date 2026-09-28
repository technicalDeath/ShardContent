using Server;
using Server.Engines.CharacterCreation;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>Short, repeatable guidance for the two distinct Ward rules.</summary>
public static class StarterOnboarding
{
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CharacterCreation.CharacterCreatedHandler += PromptNewCharacter;
    }

    public static IEnumerable<string> DescribeRules()
    {
        yield return "Welcome to Britannia Renaissance. Use [IntentStatus to review player combat consent.";
        yield return "Your physical Backpack Ward sits in your backpack. It primes when eligible theft activity begins; a detected theft consumes it and protects your backpack from further stealing for two minutes.";
        yield return "A Backpack Ward does not prevent the theft that activates it, and it has no effect inside an outdoor Hot Zone.";
        yield return "Your invisible Loot Protection entitlement is permanent. After one unlawful transfer from a monster corpse you have loot rights to, that offender is blocked from repeating it for ten minutes.";
        yield return "Loot Protection does not guard your backpack, player corpses, public monster corpses or Hot-Zone loot. Use [TheftStatus for current Ward and entitlement status.";
    }

    private static void PromptNewCharacter(CharacterCreatedEventArgs args)
    {
        if (!TheftProtectionService.Enabled || args.Mobile is not PlayerMobile { AccessLevel: AccessLevel.Player } player)
        {
            return;
        }

        // CharacterCreated fires before the client is fully in-world; defer the prompt until
        // the connection can display it. The [Welcome command remains available later.
        Server.Timer.DelayCall(TimeSpan.FromSeconds(1), () =>
        {
            if (!player.Deleted && player.NetState is not null)
            {
                player.SendMessage("Welcome to Britannia Renaissance. Type [Welcome to learn about your Backpack Ward and Loot Protection.");
            }
        });
    }
}
