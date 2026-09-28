using Server;
using Server.Engines.CharacterCreation;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

public static class CosmeticElfCreationService
{
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CharacterCreation.CharacterCreatedHandler += ApplyAppearance;
    }

    public static void ApplyAppearance(CharacterCreatedEventArgs args)
    {
        if (Core.Expansion != Expansion.UOR ||
            !ExpansionInfo.CoreExpansion.CharacterListFlags.HasFlag(CharacterListFlags.ML) ||
            args.Race != Race.Elf || args.Mobile is not PlayerMobile { AccessLevel: AccessLevel.Player } player)
        {
            return;
        }

        // Stock UOR creation supplies the Human starter package before this appearance conversion.
        player.Race = Race.Elf;
        player.Hue = Race.Elf.ClipSkinHue(args.Hue & 0x3FFF) | 0x8000;

        if (args.HairID != 0 && Race.Elf.ValidateHair(player, args.HairID))
        {
            player.HairItemID = args.HairID;
            player.HairHue = Race.Elf.ClipHairHue(args.HairHue & 0x3FFF);
        }
        else
        {
            player.HairItemID = 0;
            player.HairHue = 0;
        }

        player.FacialHairItemID = 0;
        player.FacialHairHue = 0;
    }
}
