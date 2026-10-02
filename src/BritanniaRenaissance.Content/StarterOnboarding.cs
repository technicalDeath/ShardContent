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

    public const string CreationPrompt =
        "Welcome to Britannia Renaissance. Type [Welcome to learn about your Backpack Ward and Loot Protection.";

    public static IEnumerable<string> DescribeRules()
    {
        yield return "Welcome to Britannia Renaissance. Use [IntentStatus to review player combat consent.";
        yield return "Your Backpack Ward sits in your backpack and cannot be lost or traded. A thief whose successful theft you notice, or the Ward detects, is caught: that thief cannot steal from you again until the Ward has run its course, 30 minutes after the last theft attempt against you.";
        yield return "A thief who steals from you unnoticed makes the Ward more alert to them: it detects their next successful theft 25% of the time, then 50%, then every time. A thief keeps the item that got them caught, and the Ward does not stop thieves it has not caught. It does nothing inside a Hot Zone (Fire Island, Buccaneer's Den island or Hythloth).";
        yield return "Loot Protection: after someone unlawfully loots a monster corpse you have loot rights to, they are blocked from doing it to you again for ten minutes. It does not guard your backpack, player corpses, public monster corpses or Hot-Zone loot.";
        yield return "Use [TheftStatus to see the state of your Ward.";
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
                player.SendMessage(CreationPrompt);
            }
        });
    }
}
