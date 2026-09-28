using Server;
using Server.Accounting;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// A physical, single-use Backpack Ward. The theft service owns priming and consumption; the
/// item only persists its identity, primed state, and per-thief-account counters.
/// </summary>
public sealed class BackpackWard : Item
{
    private readonly Dictionary<string, int> _successfulThefts = new(StringComparer.OrdinalIgnoreCase);
    private bool _starterIssued;
    private Serial _starterOwnerSerial;

    [Constructible]
    public BackpackWard() : base(0x1F14)
    {
        Weight = 1.0;
    }

    public BackpackWard(Serial serial) : base(serial)
    {
    }

    public bool Primed { get; private set; }

    public string? BoundAccount { get; private set; }

    public bool IsStarterIssued => _starterIssued;

    public Serial StarterOwnerSerial => _starterOwnerSerial;

    public override bool Nontransferable => _starterIssued || base.Nontransferable;

    public override string DefaultName => Primed ? "a primed backpack ward" : "a backpack ward";

    public int RecordSuccessfulTheft(string thiefAccount)
    {
        Primed = true;
        _successfulThefts.TryGetValue(thiefAccount, out var count);
        count++;
        _successfulThefts[thiefAccount] = count;
        InvalidateProperties();
        return count;
    }

    public void Prime()
    {
        Primed = true;
        InvalidateProperties();
    }

    public bool TryBindTo(PlayerMobile owner)
    {
        if (_starterIssued && owner.Serial != _starterOwnerSerial)
        {
            return false;
        }

        if (owner.Account is not Account account)
        {
            return false;
        }

        if (string.IsNullOrWhiteSpace(BoundAccount))
        {
            BoundAccount = account.Username;
            InvalidateProperties();
            return true;
        }

        return string.Equals(BoundAccount, account.Username, StringComparison.OrdinalIgnoreCase);
    }

    public bool MarkStarterIssued(PlayerMobile owner)
    {
        if (_starterIssued)
        {
            return _starterOwnerSerial == owner.Serial;
        }

        if (!TryBindTo(owner))
        {
            return false;
        }

        _starterIssued = true;
        _starterOwnerSerial = owner.Serial;
        LootType = LootType.Newbied;
        InvalidateProperties();
        return true;
    }

    public override bool VerifyMove(Mobile from) =>
        base.VerifyMove(from) && (!_starterIssued || from.AccessLevel > AccessLevel.Player ||
            from.Serial == _starterOwnerSerial);

    public override void Serialize(IGenericWriter writer)
    {
        base.Serialize(writer);
        writer.WriteEncodedInt(2);
        writer.Write(Primed);
        writer.Write(BoundAccount);
        writer.Write(_starterIssued);
        writer.Write(_starterOwnerSerial);
        writer.WriteEncodedInt(_successfulThefts.Count);

        foreach (var (account, count) in _successfulThefts)
        {
            writer.Write(account);
            writer.WriteEncodedInt(count);
        }
    }

    public override void Deserialize(IGenericReader reader)
    {
        base.Deserialize(reader);
        var version = reader.ReadEncodedInt();
        Primed = reader.ReadBool();
        BoundAccount = version >= 1 ? reader.ReadString() : null;
        if (version >= 2)
        {
            _starterIssued = reader.ReadBool();
            _starterOwnerSerial = reader.ReadSerial();
        }

        // Starter Wards issued before the newbied ruling were destroyed on death instead.
        if (_starterIssued && LootType == LootType.Regular)
        {
            LootType = LootType.Newbied;
        }

        var count = reader.ReadEncodedInt();
        for (var i = 0; i < count; i++)
        {
            var account = reader.ReadString();
            var successes = reader.ReadEncodedInt();
            if (!string.IsNullOrWhiteSpace(account) && successes > 0)
            {
                _successfulThefts[account] = successes;
            }
        }
    }
}
