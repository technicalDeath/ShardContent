namespace BritanniaRenaissance.Content;

/// <summary>
/// The shard's character-creation templates (Beta 1): the Ultima Online professions of August 1999 that were in force
/// through Renaissance. They are defined once in <c>data/professions/Prof.txt</c>, which the deployment copies to the
/// server (named by the <c>characterCreation.professionFile</c> setting) and ships beside the distributed client. IDs 8 to
/// 23 are the shard's; IDs 1 to 7 stay undefined (a client sending one, such as the later official Warrior or Necromancer,
/// falls back to Advanced).
/// </summary>
public static class ShardProfessions
{
    public const string SettingKey = "characterCreation.professionFile";

    /// <summary>The profession names in ID order, starting at <see cref="FirstId"/>.</summary>
    public static readonly string[] Names =
    [
        "Archer", "Bard", "Ranger",
        "Pure Mage", "Warlock",
        "Mace Fighter", "Fencer", "Swordsman",
        "Blacksmith", "Carpenter", "Tailor", "Tinker",
        "Animal Tamer", "Fisherman", "Prospector", "Sorcerer"
    ];

    public const int FirstId = 8;

    public static readonly int[] TemplateIds = Enumerable.Range(FirstId, Names.Length).ToArray();

    public static readonly int[] UndefinedIds = [1, 2, 3, 4, 5, 6, 7];
}
