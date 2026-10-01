using Server;
using Server.Engines.CharacterCreation;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

public static class CosmeticElfCreationService
{
    private static bool _configured;

    // Deliberately not named Configure: ModernUO invokes every public static Configure in an
    // unspecified order, and this observer must run after every starter handler so they all
    // see the Human the stock creation built. ShardBootstrap registers it last.
    public static void Register()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CharacterCreation.CharacterCreatedHandler += ApplyAppearance;
    }

    public static bool AppliesTo(Expansion expansion, CharacterListFlags listFlags, Race requested, AccessLevel access) =>
        expansion == Expansion.UOR && listFlags.HasFlag(CharacterListFlags.ML) && requested == Race.Elf &&
        access == AccessLevel.Player;

    public static (int SkinHue, int HairItemID, int HairHue) ResolveAppearance(
        bool female, int requestedSkinHue, int requestedHairID, int requestedHairHue
    )
    {
        var skinHue = Race.Elf.ClipSkinHue(requestedSkinHue & 0x3FFF) | 0x8000;

        return requestedHairID != 0 && Race.Elf.ValidateHair(female, requestedHairID)
            ? (skinHue, requestedHairID, Race.Elf.ClipHairHue(requestedHairHue & 0x3FFF))
            : (skinHue, 0, 0);
    }

    public static void ApplyAppearance(CharacterCreatedEventArgs args)
    {
        if (args.Mobile is not PlayerMobile player ||
            !AppliesTo(Core.Expansion, ExpansionInfo.CoreExpansion.CharacterListFlags, args.Race, player.AccessLevel))
        {
            return;
        }

        // Stock UOR creation supplies the Human starter package before this appearance conversion.
        var (skinHue, hairItemID, hairHue) = ResolveAppearance(player.Female, args.Hue, args.HairID, args.HairHue);

        player.Race = Race.Elf;
        player.Hue = skinHue;
        player.HairItemID = hairItemID;
        player.HairHue = hairHue;

        // Elves have no facial hair.
        player.FacialHairItemID = 0;
        player.FacialHairHue = 0;
    }
}
