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

    /// <summary>Said in chat once the guide has opened for a new character, so the way back to it stays on screen.</summary>
    public const string CreationPrompt = "Welcome to Britannia Renaissance. Type [Welcome any time to read the guide again.";

    public const string Intro = "Welcome to Britannia Renaissance. Use [IntentStatus to review player combat consent.";

    public const string WardWhat =
        "Your Backpack Ward sits in your backpack and cannot be lost or traded. A thief whose successful theft you notice, or the Ward detects, is caught: that thief cannot steal from you again until the Ward has run its course, 30 minutes after the last theft attempt against you.";

    public const string WardAlert =
        "A thief who steals from you unnoticed makes the Ward more alert to them: it detects their next successful theft 25% of the time, then 50%, then every time. A thief keeps the item that got them caught, and the Ward does not stop thieves it has not caught. It does nothing inside a Hot Zone (Fire Island, Buccaneer's Den island or Hythloth).";

    public const string LootProtection =
        "Loot Protection: after someone unlawfully loots a monster corpse you have loot rights to, they are blocked from doing it to you again for ten minutes. It does not guard your backpack, player corpses, public monster corpses or Hot-Zone loot.";

    // [TheftStatus is a staff command, so players are pointed at the Ward itself.
    public const string WardTip = "Double-click your Backpack Ward to see what it is, where it stands and how many quiet minutes are left.";

    public static IEnumerable<string> DescribeRules()
    {
        yield return Intro;
        yield return WardWhat;
        yield return WardAlert;
        yield return LootProtection;
        yield return WardTip;
    }

    private static void PromptNewCharacter(CharacterCreatedEventArgs args)
    {
        if (args.Mobile is not PlayerMobile { AccessLevel: AccessLevel.Player } player)
        {
            return;
        }

        // CharacterCreated fires before the client is fully in-world; defer the guide until
        // the connection can display it. The [Welcome command opens it again later.
        Server.Timer.DelayCall(TimeSpan.FromSeconds(1), () =>
        {
            if (!player.Deleted && player.NetState is not null)
            {
                WelcomeGuide.Open(player);
                player.SendMessage(CreationPrompt);
            }
        });
    }
}
