using System.Diagnostics;
using Server;
using Server.Engines.Spawners;
using Server.Items;
using Server.Logging;
using Server.Mobiles;
using Server.Multis;
using Server.Systems.FeatureFlags;

namespace BritanniaRenaissance.Content;

/// <summary>Read-only, bounded sampling of the stock Felucca house-placement verdict.</summary>
public static class HousingPlacementSurveyCommands
{
    private const int MaximumSamples = 4096;
    private const int MaximumChecksPerSlice = 16;
    private const int CentersPerPage = 20;
    private static readonly ILogger Logger = LogFactory.GetLogger(typeof(HousingPlacementSurveyCommands));
    private static SurveyRun? _active;
    private static SurveyRun? _lastCompleted;

    public static void Register() =>
        CommandSystem.Register("HousingSurvey", AccessLevel.Administrator, OnCommand);

    [Usage("HousingSurvey run <xMin> <yMin> <xMax> <yMax> <classicEntryIndex> <step> | spawns <x> <y> <classicEntryIndex> | status | results [page] | cancel")]
    [Description("Samples stock Felucca house placement without changing the world.")]
    private static void OnCommand(CommandEventArgs e)
    {
        switch (e.GetString(0).ToLowerInvariant())
        {
            case "run":
                Start(e);
                break;
            case "status":
                e.Mobile.SendMessage(_active is null
                    ? "No housing placement survey is running. Use results to inspect the last completed run."
                    : _active.DescribeProgress());
                break;
            case "results":
                ShowResults(e);
                break;
            case "spawns":
                ShowSpawnConflicts(e);
                break;
            case "cancel":
                if (_active is null)
                {
                    e.Mobile.SendMessage("No housing placement survey is running.");
                }
                else
                {
                    _active.Requester.SendMessage("Housing placement survey cancelled.");
                    _active = null;
                    e.Mobile.SendMessage("Housing placement survey cancelled.");
                }
                break;
            default:
                e.Mobile.SendMessage($"Usage: {CommandSystem.Prefix}HousingSurvey run <xMin> <yMin> <xMax> <yMax> <classicEntryIndex> <step> | spawns <x> <y> <classicEntryIndex> | status | results [page] | cancel");
                break;
        }
    }

    private static void ShowSpawnConflicts(CommandEventArgs e)
    {
        var entries = HousePlacementEntry.ClassicHouses;
        if (e.Length != 4)
        {
            e.Mobile.SendMessage("Specify a center and a valid classic house entry index.");
            return;
        }

        var index = e.GetInt32(3);
        if (index < 0 || index >= entries.Length)
        {
            e.Mobile.SendMessage("Specify a center and a valid classic house entry index.");
            return;
        }

        var centerX = e.GetInt32(1);
        var centerY = e.GetInt32(2);
        if (centerX < 0 || centerY < 0 || centerX >= Map.Felucca.Width || centerY >= Map.Felucca.Height)
        {
            e.Mobile.SendMessage("The center must be on Felucca.");
            return;
        }

        var components = MultiData.GetComponents(entries[index].MultiID);
        const int yardBuffer = 8;
        var minX = centerX + components.Min.X - yardBuffer;
        var minY = centerY + components.Min.Y - yardBuffer;
        var maxX = minX + components.Width + yardBuffer * 2 - 1;
        var maxY = minY + components.Height + yardBuffer * 2 - 1;
        var count = 0;
        var shown = 0;
        var allMap = new Rectangle2D(0, 0, Map.Felucca.Width, Map.Felucca.Height);
        foreach (var spawner in Map.Felucca.GetItemsInBounds<BaseSpawner>(allMap))
        {
            var bounds = spawner.SpawnBounds;
            var spawnMinX = bounds == default ? spawner.X : bounds.Start.X;
            var spawnMinY = bounds == default ? spawner.Y : bounds.Start.Y;
            var spawnMaxX = bounds == default ? spawner.X : bounds.End.X;
            var spawnMaxY = bounds == default ? spawner.Y : bounds.End.Y;
            if (!HousingSpawnOverlap.Intersects(minX, minY, maxX, maxY,
                    spawnMinX, spawnMinY, spawnMaxX, spawnMaxY))
            {
                continue;
            }

            count++;
            if (shown++ < 12)
            {
                e.Mobile.SendMessage($"Spawner {spawner.Guid} at ({spawner.X},{spawner.Y}): {spawner.GetType().Name}, home range {spawner.HomeRange}, bounds ({spawnMinX},{spawnMinY})–({spawnMaxX},{spawnMaxY}).");
            }
        }

        e.Mobile.SendMessage($"Spawn-area overlap: {count} spawners for {entries[index].Type.Name} at ({centerX},{centerY}), including an {yardBuffer}-tile foundation buffer; showing {Math.Min(count, 12)}. This is a conflict screen, not lot approval. Region-wide spawns and active mobile movement need separate review.");
    }

    private static void ShowResults(CommandEventArgs e)
    {
        if (_lastCompleted is null)
        {
            e.Mobile.SendMessage("No completed housing placement survey is available in this server session.");
            return;
        }

        var page = e.Length > 1 ? e.GetInt32(1) : 1;
        foreach (var line in _lastCompleted.DescribeValidCenters(page))
        {
            e.Mobile.SendMessage(line);
        }
    }

    private static void Start(CommandEventArgs e)
    {
        if (_active is not null)
        {
            e.Mobile.SendMessage("A housing placement survey is already running.");
            return;
        }

        if (e.Length != 7)
        {
            e.Mobile.SendMessage("Specify four rectangle bounds, a classic house entry index, and a step.");
            return;
        }

        if (!ContentFeatureFlags.HousePlacement)
        {
            e.Mobile.SendMessage("Stock house placement is disabled; a placement survey would not measure usable sites.");
            return;
        }

        var entries = HousePlacementEntry.ClassicHouses;
        var entryIndex = e.GetInt32(5);
        if (entryIndex < 0 || entryIndex >= entries.Length)
        {
            e.Mobile.SendMessage($"Classic house entry index must be 0 through {entries.Length - 1}.");
            return;
        }

        if (!HousingSurveyBounds.TryCreate(
                e.GetInt32(1), e.GetInt32(2), e.GetInt32(3), e.GetInt32(4), e.GetInt32(6),
                Map.Felucca.Width, Map.Felucca.Height, MaximumSamples, out var bounds
            ))
        {
            e.Mobile.SendMessage($"Rectangle must fit Felucca and contain at most {MaximumSamples} sampled centers; step must be 1–16.");
            return;
        }

        var run = new SurveyRun(e.Mobile, entries[entryIndex], bounds);
        _active = run;
        _lastCompleted = null;
        e.Mobile.SendMessage($"Housing survey started: {bounds.SampleCount} centers, {entries[entryIndex].Type.Name} (classic entry {entryIndex}); housing geography enabled: {ShardRulesConfiguration.Settings.FeatureFlags.HousingGeography}. Valid centers may overlap and are not distinct lots.");
        Server.Timer.DelayCall(TimeSpan.Zero, () => Process(run));
    }

    private static void Process(SurveyRun? run)
    {
        if (run is null || _active != run)
        {
            return;
        }

        if (World.Saving)
        {
            Server.Timer.DelayCall(TimeSpan.FromSeconds(1), () => Process(run));
            return;
        }

        var probe = new PlayerMobile(World.NewMobile);
        try
        {
            probe.DefaultMobileInit();
            probe.Player = true;
            probe.Map = Map.Felucca;
            var started = Stopwatch.GetTimestamp();
            for (var i = 0; i < MaximumChecksPerSlice && !run.Done; i++)
            {
                try
                {
                    var z = Map.Felucca.GetAverageZ(run.X, run.Y);
                    var center = new Point3D(run.X, run.Y, z);
                    var result = HousePlacement.Check(probe, run.Entry.MultiID, center,
                        out _, run.Entry.HouseDirection);
                    run.Record(result);
                }
                catch (Exception ex)
                {
                    Logger.Error(ex, "Housing placement survey failed at ({X}, {Y})", run.X, run.Y);
                    run.Requester.SendMessage($"Housing survey stopped after an error at ({run.X}, {run.Y}). Review the server log.");
                    _active = null;
                    return;
                }

                if (Stopwatch.GetElapsedTime(started) >= TimeSpan.FromMilliseconds(5))
                {
                    break;
                }
            }
        }
        finally
        {
            probe.Delete();
        }

        if (run.Done)
        {
            _lastCompleted = run;
            foreach (var line in run.DescribeResult())
            {
                run.Requester.SendMessage(line);
            }

            _active = null;
            return;
        }

        Server.Timer.DelayCall(TimeSpan.FromMilliseconds(50), () => Process(run));
    }

    private sealed class SurveyRun(
        Mobile requester, HousePlacementEntry entry, HousingSurveyBounds bounds
    )
    {
        private readonly int[] _counts = new int[Enum.GetValues<HousePlacementResult>().Length];
        private readonly List<Point2D> _validCenters = [];
        private int _sampled;

        public Mobile Requester { get; } = requester;
        public HousePlacementEntry Entry { get; } = entry;
        public int X { get; private set; } = bounds.XMin;
        public int Y { get; private set; } = bounds.YMin;
        public bool Done => Y > bounds.YMax;

        public void Record(HousePlacementResult result)
        {
            _counts[(int)result]++;
            if (result == HousePlacementResult.Valid)
            {
                _validCenters.Add(new Point2D(X, Y));
            }

            _sampled++;
            X += bounds.Step;
            if (X > bounds.XMax)
            {
                X = bounds.XMin;
                Y += bounds.Step;
            }
        }

        public string DescribeProgress() =>
            $"Housing survey: {_sampled}/{bounds.SampleCount} centers checked; {_counts[(int)HousePlacementResult.Valid]} valid so far.";

        public IEnumerable<string> DescribeResult()
        {
            yield return $"Housing survey complete: {_sampled} centers checked; {_counts[(int)HousePlacementResult.Valid]} valid candidate centers (overlapping, not distinct lots).";
            yield return "Use [HousingSurvey results [page] to inspect valid center coordinates in this server session.";
            foreach (var result in Enum.GetValues<HousePlacementResult>())
            {
                if (result != HousePlacementResult.Valid && _counts[(int)result] > 0)
                {
                    yield return $"{result}: {_counts[(int)result]}.";
                }
            }
        }

        public IEnumerable<string> DescribeValidCenters(int page)
        {
            var pages = Math.Max(1, (_validCenters.Count + CentersPerPage - 1) / CentersPerPage);
            if (page < 1 || page > pages)
            {
                yield return $"Results page must be 1 through {pages}.";
                yield break;
            }

            yield return $"Housing survey: {Entry.Type.Name}, rectangle {bounds.XMin},{bounds.YMin}–{bounds.XMax},{bounds.YMax}, step {bounds.Step}; {_validCenters.Count} valid centers; page {page}/{pages}.";
            if (_validCenters.Count == 0)
            {
                yield return "No valid centers were found.";
                yield break;
            }

            var start = (page - 1) * CentersPerPage;
            var end = Math.Min(start + CentersPerPage, _validCenters.Count);
            for (var i = start; i < end; i += 5)
            {
                yield return string.Join("  ", _validCenters.Skip(i).Take(Math.Min(5, end - i)).Select(point => $"({point.X},{point.Y})"));
            }
        }
    }
}

public static class HousingSpawnOverlap
{
    public static bool Intersects(int aMinX, int aMinY, int aMaxX, int aMaxY,
        int bMinX, int bMinY, int bMaxX, int bMaxY) =>
        aMinX <= bMaxX && bMinX <= aMaxX && aMinY <= bMaxY && bMinY <= aMaxY;
}

public readonly record struct HousingSurveyBounds(
    int XMin, int YMin, int XMax, int YMax, int Step, int SampleCount
)
{
    public static bool TryCreate(
        int xMin, int yMin, int xMax, int yMax, int step,
        int mapWidth, int mapHeight, int maximumSamples, out HousingSurveyBounds bounds
    )
    {
        bounds = default;
        if (xMin < 0 || yMin < 0 || xMax < xMin || yMax < yMin ||
            xMax >= mapWidth || yMax >= mapHeight || step is < 1 or > 16 || maximumSamples <= 0)
        {
            return false;
        }

        var columns = (long)(xMax - xMin) / step + 1;
        var rows = (long)(yMax - yMin) / step + 1;
        var count = columns * rows;
        if (count > maximumSamples)
        {
            return false;
        }

        bounds = new HousingSurveyBounds(xMin, yMin, xMax, yMax, step, (int)count);
        return true;
    }
}
