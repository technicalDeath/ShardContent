namespace BritanniaRenaissance.Content;

public enum WardPhase
{
    Unprimed = 0,
    Primed = 1,
    Activated = 2
}

/// <summary>What the 30-minute inactivity window does to a Ward whose window has run out.</summary>
public enum WardExpiry
{
    None = 0,

    /// <summary>A Primed Ward forgets the encounter and becomes an ordinary reusable Ward.</summary>
    Reset = 1,

    /// <summary>An Activated Ward is consumed.</summary>
    Consume = 2
}

/// <summary>
/// The rules of one Backpack Ward (see docs/BACKPACK-WARD-DESIGN.md), kept free of the game engine so they can be tested
/// directly. A Ward is Unprimed until theft activity first needs it, Primed while it tracks thieves, and Activated once it
/// has detected a theft. It remembers each thief account's successful undetected thefts (25%, 50%, 100% extra detection),
/// and a thief account whose successful theft was detected is <em>caught</em>: while the Ward stays Activated that account is
/// blocked from every theft attempt against the protected character. Thirty minutes without a qualifying theft attempt
/// resets a Primed Ward and consumes an Activated one.
/// </summary>
public sealed class WardState
{
    public static readonly TimeSpan InactivityWindow = TimeSpan.FromMinutes(30);

    private readonly Dictionary<string, int> _successes = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> _caught = new(StringComparer.OrdinalIgnoreCase);

    public WardPhase Phase { get; private set; }

    /// <summary>The character this Ward is protecting while it is Primed or Activated; zero when Unprimed.</summary>
    public uint ProtectedSerial { get; private set; }

    public DateTime LastActivityUtc { get; private set; }

    public IReadOnlyDictionary<string, int> Successes => _successes;

    public IReadOnlyCollection<string> Caught => _caught;

    public bool IsTracking => Phase != WardPhase.Unprimed;

    public DateTime DeadlineUtc => LastActivityUtc + InactivityWindow;

    /// <summary>Thirty minutes of quiet from the last qualifying theft attempt.</summary>
    public TimeSpan Remaining(DateTime nowUtc)
    {
        if (!IsTracking)
        {
            return TimeSpan.Zero;
        }

        var left = DeadlineUtc - nowUtc;
        return left > TimeSpan.Zero ? left : TimeSpan.Zero;
    }

    /// <summary>The first theft activity that needs the Ward primes it for this character.</summary>
    public bool Prime(uint protectedSerial, DateTime nowUtc)
    {
        if (Phase != WardPhase.Unprimed)
        {
            return false;
        }

        Phase = WardPhase.Primed;
        ProtectedSerial = protectedSerial;
        LastActivityUtc = nowUtc;
        return true;
    }

    /// <summary>A genuine theft attempt against the protected character restarts the inactivity window.</summary>
    public void Refresh(DateTime nowUtc)
    {
        if (IsTracking)
        {
            LastActivityUtc = nowUtc;
        }
    }

    /// <summary>
    /// Records a successful theft that escaped ordinary detection, then returns the thief account's running count
    /// (1, 2, 3 ...). The count rises before the extra detection roll.
    /// </summary>
    public int RecordUndetectedSuccess(string thiefAccount, DateTime nowUtc)
    {
        _successes.TryGetValue(thiefAccount, out var count);
        _successes[thiefAccount] = ++count;
        Refresh(nowUtc);
        return count;
    }

    /// <summary>The Ward has detected a theft. Primed becomes Activated; an Activated Ward stays so.</summary>
    public void Activate(DateTime nowUtc)
    {
        if (Phase == WardPhase.Primed)
        {
            Phase = WardPhase.Activated;
        }

        Refresh(nowUtc);
    }

    /// <summary>A thief whose successful theft was detected is caught and blocked for the rest of the encounter.</summary>
    public void MarkCaught(string thiefAccount) => _caught.Add(thiefAccount);

    /// <summary>True when this account has been caught by an Activated Ward and may not attempt theft.</summary>
    public bool IsBlocked(string thiefAccount) => Phase == WardPhase.Activated && _caught.Contains(thiefAccount);

    public WardExpiry CheckExpiry(DateTime nowUtc)
    {
        if (!IsTracking || nowUtc < DeadlineUtc)
        {
            return WardExpiry.None;
        }

        return Phase == WardPhase.Primed ? WardExpiry.Reset : WardExpiry.Consume;
    }

    /// <summary>Forgets everything: back to an ordinary Unprimed Ward with no history and no caught thieves.</summary>
    public void Reset()
    {
        Phase = WardPhase.Unprimed;
        ProtectedSerial = 0;
        LastActivityUtc = default;
        _successes.Clear();
        _caught.Clear();
    }

    /// <summary>Rebuilds state from saved data.</summary>
    public void Restore(
        WardPhase phase,
        uint protectedSerial,
        DateTime lastActivityUtc,
        IEnumerable<KeyValuePair<string, int>> successes,
        IEnumerable<string> caught
    )
    {
        // The arguments may be this state's own collections, which Reset empties.
        var keptSuccesses = successes.ToArray();
        var keptCaught = caught.ToArray();
        Reset();

        if (phase == WardPhase.Unprimed)
        {
            return;
        }

        Phase = phase;
        ProtectedSerial = protectedSerial;
        LastActivityUtc = lastActivityUtc;

        foreach (var (account, count) in keptSuccesses)
        {
            if (!string.IsNullOrWhiteSpace(account) && count > 0)
            {
                _successes[account] = count;
            }
        }

        foreach (var account in keptCaught)
        {
            if (!string.IsNullOrWhiteSpace(account))
            {
                _caught.Add(account);
            }
        }
    }
}
