using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// A physical Backpack Ward (see docs/BACKPACK-WARD-DESIGN.md). The rules live in <see cref="WardState"/> and
/// <see cref="BackpackWardService"/>; the item persists that state, shows it in its name, and keeps the character
/// blessing in step with it. A regular Ward is blessed to the character it protects while it is Primed or Activated; the
/// starter Ward is newbied and bound to its owner from creation.
/// </summary>
public sealed class BackpackWard : Item
{
    public const int DefaultItemId = 0x1F14;

    private bool _starterIssued;
    private Serial _starterOwnerSerial;

    [Constructible]
    public BackpackWard() : base(DefaultItemId)
    {
        Weight = 1.0;
    }

    public BackpackWard(Serial serial) : base(serial)
    {
    }

    public WardState State { get; } = new();

    public bool IsStarterIssued => _starterIssued;

    public Serial StarterOwnerSerial => _starterOwnerSerial;

    public override bool Nontransferable => _starterIssued || base.Nontransferable;

    public override string DefaultName => $"a backpack ward ({State.Phase.ToString().ToLowerInvariant()})";

    /// <summary>The character this Ward is protecting while it is Primed or Activated.</summary>
    public Mobile? ProtectedCharacter =>
        State.IsTracking ? World.FindMobile((Serial)State.ProtectedSerial) : null;

    public bool MarkStarterIssued(PlayerMobile owner)
    {
        if (_starterIssued)
        {
            return _starterOwnerSerial == owner.Serial;
        }

        _starterIssued = true;
        _starterOwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
        InvalidateProperties();
        return true;
    }

    public override void OnDoubleClick(Mobile from) => BackpackWardService.Inspect(from, this);

    public override bool VerifyMove(Mobile from) =>
        base.VerifyMove(from) && (!_starterIssued || from.AccessLevel > AccessLevel.Player ||
            from.Serial == _starterOwnerSerial);

    /// <summary>Primes this Ward for the character holding it.</summary>
    public void Prime(PlayerMobile holder)
    {
        if (State.Prime(holder.Serial.Value, Core.Now))
        {
            SyncBlessing(holder);
            InvalidateProperties();
        }
    }

    public void Activate()
    {
        State.Activate(Core.Now);
        InvalidateProperties();
    }

    /// <summary>Back to an ordinary Unprimed Ward: no history, no caught thieves, no blessing.</summary>
    public void ResetAll()
    {
        State.Reset();
        SyncBlessing(null);
        InvalidateProperties();
    }

    /// <summary>
    /// A Ward that is tracking thieves for one character resets completely when a different character comes to hold it.
    /// Moving it between that character's own containers, or onto the ground, changes nothing.
    /// </summary>
    public void EnforceHolder()
    {
        if (State.IsTracking && RootParent is Mobile holder && holder.Serial.Value != State.ProtectedSerial)
        {
            ResetAll();
        }
    }

    public override void OnAdded(IEntity parent)
    {
        base.OnAdded(parent);
        EnforceHolder();
    }

    private void SyncBlessing(Mobile? protectedCharacter)
    {
        if (_starterIssued)
        {
            return;
        }

        if (State.IsTracking && protectedCharacter is not null)
        {
            LootType = LootType.Blessed;
            BlessedFor = protectedCharacter;
        }
        else
        {
            LootType = LootType.Regular;
            BlessedFor = null;
        }
    }

    public override void Serialize(IGenericWriter writer)
    {
        base.Serialize(writer);
        writer.WriteEncodedInt(3);
        writer.Write(_starterIssued);
        writer.Write(_starterOwnerSerial);
        writer.WriteEncodedInt((int)State.Phase);
        writer.Write(State.ProtectedSerial);
        writer.Write(State.LastActivityUtc);
        writer.WriteEncodedInt(State.Successes.Count);

        foreach (var (account, count) in State.Successes)
        {
            writer.Write(account);
            writer.WriteEncodedInt(count);
        }

        writer.WriteEncodedInt(State.Caught.Count);

        foreach (var account in State.Caught)
        {
            writer.Write(account);
        }
    }

    public override void Deserialize(IGenericReader reader)
    {
        base.Deserialize(reader);
        var version = reader.ReadEncodedInt();

        if (version >= 3)
        {
            _starterIssued = reader.ReadBool();
            _starterOwnerSerial = reader.ReadSerial();
            var phase = (WardPhase)reader.ReadEncodedInt();
            var protectedSerial = reader.ReadUInt();
            var lastActivity = reader.ReadDateTime();

            var successes = new List<KeyValuePair<string, int>>();
            var successCount = reader.ReadEncodedInt();
            for (var i = 0; i < successCount; i++)
            {
                successes.Add(new KeyValuePair<string, int>(reader.ReadString(), reader.ReadEncodedInt()));
            }

            var caught = new List<string>();
            var caughtCount = reader.ReadEncodedInt();
            for (var i = 0; i < caughtCount; i++)
            {
                caught.Add(reader.ReadString());
            }

            State.Restore(phase, protectedSerial, lastActivity, successes, caught);
            return;
        }

        // Saves from the earlier model: its primed flag, account binding and per-thief counts described a different
        // mechanic, so a Ward loaded from one starts fresh. Only the starter marking carries over.
        reader.ReadBool();
        if (version >= 1)
        {
            reader.ReadString();
        }

        if (version >= 2)
        {
            _starterIssued = reader.ReadBool();
            _starterOwnerSerial = reader.ReadSerial();
        }

        var legacyCount = reader.ReadEncodedInt();
        for (var i = 0; i < legacyCount; i++)
        {
            reader.ReadString();
            reader.ReadEncodedInt();
        }
    }
}
