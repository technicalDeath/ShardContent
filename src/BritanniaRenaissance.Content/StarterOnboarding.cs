using Server;
using Server.Engines.CharacterCreation;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>Opens the [Welcome guide for a new character. The guide's text lives in <see cref="WelcomeGuide"/>.</summary>
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
    public const string CreationPrompt = $"Welcome to {ShardBranding.Name}. Type [Welcome any time to read the guide again.";

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
