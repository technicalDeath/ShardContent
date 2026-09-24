using Server;
using Server.Items;

namespace BritanniaRenaissance.Content;

/// <summary>
/// A physical, single-use Backpack Ward. The theft service owns priming and consumption; the
/// item only persists its identity, primed state, and per-thief-account counters.
/// </summary>
public sealed class BackpackWard : Item
{
    private readonly Dictionary<string, int> _successfulThefts = new(StringComparer.OrdinalIgnoreCase);

    public BackpackWard() : base(0x1F14)
    {
        Weight = 1.0;
    }

    public BackpackWard(Serial serial) : base(serial)
    {
    }

    public bool Primed { get; private set; }

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

    public override void Serialize(IGenericWriter writer)
    {
        base.Serialize(writer);
        writer.WriteEncodedInt(0);
        writer.Write(Primed);
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
        _ = reader.ReadEncodedInt();
        Primed = reader.ReadBool();

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
