using System.Text.Json;
using Server;
using Server.Engines.CharacterCreation;
using Server.Misc;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class CosmeticElfCreationServiceTests
{
    private static readonly object RaceLock = new();

    public CosmeticElfCreationServiceTests()
    {
        lock (RaceLock)
        {
            if (Race.Races[1] == null)
            {
                RaceDefinitions.Configure();
            }
        }
    }

    [Fact]
    public void AppliesOnlyToPlayerElfRequestsOnUorWithTheCharacterListBit()
    {
        const CharacterListFlags uor = CharacterListFlags.ContextMenus;
        const CharacterListFlags uorElf = CharacterListFlags.ContextMenus | CharacterListFlags.ML;

        Assert.True(CosmeticElfCreationService.AppliesTo(Expansion.UOR, uorElf, Race.Elf, AccessLevel.Player));

        Assert.False(CosmeticElfCreationService.AppliesTo(Expansion.UOR, uor, Race.Elf, AccessLevel.Player));
        Assert.False(CosmeticElfCreationService.AppliesTo(Expansion.ML, uorElf, Race.Elf, AccessLevel.Player));
        Assert.False(CosmeticElfCreationService.AppliesTo(Expansion.UOR, uorElf, Race.Human, AccessLevel.Player));
        Assert.False(CosmeticElfCreationService.AppliesTo(Expansion.UOR, uorElf, Race.Gargoyle, AccessLevel.Player));
        Assert.False(CosmeticElfCreationService.AppliesTo(Expansion.UOR, uorElf, Race.Elf, AccessLevel.Counselor));
        Assert.False(CosmeticElfCreationService.AppliesTo(Expansion.UOR, uorElf, Race.Elf, AccessLevel.Administrator));
    }

    [Theory]
    [InlineData(0x4DE, 0x4DE)]   // valid Elf skin hue is kept
    [InlineData(0x84DE, 0x4DE)]  // client-set high bits are ignored
    [InlineData(1002, 0x0BF)]    // a Human skin hue falls back to the first Elf hue
    [InlineData(0, 0x0BF)]
    public void SkinHueIsClippedToTheElfTableAndFlaggedAsSkin(int requested, int expected)
    {
        var (skinHue, _, _) = CosmeticElfCreationService.ResolveAppearance(false, requested, 0, 0);

        Assert.Equal(expected | 0x8000, skinHue);
    }

    [Theory]
    [InlineData(false, 0x2FBF)]
    [InlineData(false, 0x2FC2)]
    [InlineData(false, 0x2FCD)]
    [InlineData(false, 0x2FD1)]
    [InlineData(true, 0x2FC0)]
    [InlineData(true, 0x2FCC)]
    [InlineData(true, 0x2FD0)]
    public void ValidElfHairIsKept(bool female, int hairId)
    {
        var (_, hair, hairHue) = CosmeticElfCreationService.ResolveAppearance(female, 0x4DE, hairId, 0x034);

        Assert.Equal(hairId, hair);
        Assert.Equal(0x034, hairHue);
    }

    [Theory]
    [InlineData(false, 0x2FCC)]  // the female-only styles
    [InlineData(false, 0x2FD0)]
    [InlineData(true, 0x2FBF)]   // the male-only styles
    [InlineData(true, 0x2FCD)]
    [InlineData(false, 0x203B)]  // Human hair
    [InlineData(true, 0x2044)]
    [InlineData(false, 0x2FD2)]  // past the Elf range
    [InlineData(false, 0)]
    public void HairOutsideTheElfSetForThatGenderBecomesBald(bool female, int hairId)
    {
        var (_, hair, hairHue) = CosmeticElfCreationService.ResolveAppearance(female, 0x4DE, hairId, 0x034);

        Assert.Equal(0, hair);
        Assert.Equal(0, hairHue);
    }

    [Fact]
    public void HairHueIsClippedToTheElfTable()
    {
        var (_, _, valid) = CosmeticElfCreationService.ResolveAppearance(false, 0x4DE, 0x2FC0, 0x853);
        var (_, _, invalid) = CosmeticElfCreationService.ResolveAppearance(false, 0x4DE, 0x2FC0, 0x1001);

        Assert.Equal(0x853, valid);
        Assert.Equal(0x034, invalid);
    }

    [Fact]
    public void ElvesNeverHaveFacialHairAndUseTheNativeBodies()
    {
        Assert.True(Race.Elf.ValidateFacialHair(false, 0));
        Assert.False(Race.Elf.ValidateFacialHair(false, 0x203E));
        Assert.False(Race.Elf.ValidateFacialHair(true, 0x204D));

        Assert.Equal(605, Race.Elf.AliveBody(false));
        Assert.Equal(606, Race.Elf.AliveBody(true));
        Assert.Equal(607, Race.Elf.GhostBody(false));
        Assert.Equal(608, Race.Elf.GhostBody(true));
    }

    [Fact]
    public void RegisterIsIdempotent()
    {
        CosmeticElfCreationService.Register();
        CosmeticElfCreationService.Register();

        var registered = CharacterCreation.CharacterCreatedHandler!.GetInvocationList()
            .Count(d => d.Method.DeclaringType == typeof(CosmeticElfCreationService));

        Assert.Equal(1, registered);
    }

    [Fact]
    public void ExpansionConfigKeepsTheMlFeatureBitOffAndGargoyleOff()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "data", "expansion.json")));
        var root = doc.RootElement;

        Assert.Equal(2, root.GetProperty("Id").GetInt32());
        Assert.False(root.GetProperty("SupportedFeatures").GetProperty("ML").GetBoolean());
        Assert.False(root.GetProperty("SupportedFeatures").GetProperty("SA").GetBoolean());
        Assert.False(root.GetProperty("CharacterListFlags").GetProperty("SE").GetBoolean());
        Assert.True(root.GetProperty("CharacterListFlags").GetProperty("ML").GetBoolean());
    }
}
