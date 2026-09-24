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

    public override void Serialize(IGenericWriter writer)
    {
        base.Serialize(writer);
        writer.WriteEncodedInt(1);
        writer.Write(Primed);
        writer.Write(BoundAccount);
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
