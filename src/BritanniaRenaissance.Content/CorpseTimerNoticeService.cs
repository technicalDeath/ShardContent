using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Tells a player who dies how long their corpse lasts (docs/Corpse-Timer-Notice-Evidence.md), behind <c>featureFlags.corpseTimerNotice</c>. The owner (2026-10-17):
/// "Show the player the message about how long they have." A player's corpse turns to bones after <see cref="Corpse.DefaultDecayTime"/>, keeping what it
/// holds (10 minutes for a player with <c>longerPlayerCorpses</c>), and the bones and everything in them are gone <see cref="Corpse.BoneDecayTime"/> later;
/// nothing in the game said so.
/// </summary>
public static class CorpseTimerNoticeService
{
    /// <summary>After a death the client shows the death screen first; a line sent at once would scroll past unread. Ahead of the healer reminder (4 s).</summary>
    public static readonly TimeSpan AfterDeath = TimeSpan.FromSeconds(3);

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.CorpseTimerNotice == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        PlayerMobile.PlayerDeathHandler += player => Server.Timer.DelayCall(AfterDeath, () => Tell(player));
    }

    public static string Text(TimeSpan untilBones, TimeSpan bonesLast) =>
        $"Your corpse will turn to bones in {Minutes(untilBones)}, and the bones and everything in them will be gone {Minutes(bonesLast)} after that.";

    private static string Minutes(TimeSpan span)
    {
        var minutes = Math.Max(1, (int)Math.Round(span.TotalMinutes));
        return minutes == 1 ? "1 minute" : $"{minutes} minutes";
    }

    private static void Tell(PlayerMobile player)
    {
        if (!Enabled || player.Deleted || player.Alive || player.NetState is null || player.Corpse is not Corpse { Deleted: false } corpse)
        {
            return;
        }

        player.SendMessage(0x35, Text(Corpse.InitialDecayTimeFor(corpse), Corpse.BoneDecayTime));
    }
}
