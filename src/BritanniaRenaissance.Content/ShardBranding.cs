namespace BritanniaRenaissance.Content;

/// <summary>
/// The shard's player-facing name and tagline, in one place so a rename is one edit. The name was "Britannia Renaissance"
/// until 2026-10-06. Internal identifiers (this assembly and namespace, account tag keys, repository and folder names) keep
/// the old spelling on purpose: renaming them would orphan saved data and tooling for no player-visible gain.
/// </summary>
public static class ShardBranding
{
    public const string Name = "UO Rekindled";

    public const string Tagline = "Felucca, without the griefing";
}
