using Server;
using Server.Commands;
using Server.Targeting;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Staff: open a targeted mobile's backpack from any distance, the way <c>[Bank</c> opens the bank box.
/// A double-click on a worn pack goes through Snooping, whose harm check refuses staff for a blessed
/// or staff owner and for a region that disallows harm.
/// </summary>
public static class StaffPackCommand
{
    public static void Register()
    {
        CommandSystem.Register("Pack", AccessLevel.GameMaster, OnCommand);
    }

    [Usage("Pack")]
    [Description("Opens the backpack of a targeted player or creature, from any distance. Logged like [Bank.")]
    private static void OnCommand(CommandEventArgs e)
    {
        e.Mobile.Target = new PackTarget();
    }

    private sealed class PackTarget() : Target(-1, false, TargetFlags.None)
    {
        protected override void OnTarget(Mobile from, object targeted)
        {
            if (targeted is not Mobile owner)
            {
                from.SendMessage("Select a player or creature.");
                return;
            }

            var pack = owner.Backpack;

            if (pack is null)
            {
                from.SendMessage($"{owner.Name} has no backpack.");
                return;
            }

            CommandLogging.WriteLine(
                from,
                $"{from.AccessLevel} {CommandLogging.Format(from)} opening backpack of {CommandLogging.Format(owner)}"
            );

            pack.DisplayTo(from);
        }
    }
}
