using System.Text.Json;
using Server;

namespace BritanniaRenaissance.Content;

public sealed record Alpha2bWorldGenerationManifest
{
    public int SchemaVersion { get; init; }
    public string PinnedModernUoCommit { get; init; } = "";
    public string Era { get; init; } = "";
    public string TargetMap { get; init; } = "";
    public string GeneratedDataRoot { get; init; } = "";
    public int MaximumEraMapXExclusive { get; init; }
    public Alpha2bRectangleBounds BritainBounds { get; init; } = new();
    public string DecorationsDirectory { get; init; } = "";
    public string SpawnersDirectory { get; init; } = "";
    public string SignsFile { get; init; } = "";
    public string TeleportersFile { get; init; } = "";
    public string[] DecorationFiles { get; init; } = [];
    public string[] CustomDecorationFiles { get; init; } = [];
    public Alpha2bDecorationRewrite[] DecorationRewrites { get; init; } = [];
    public Alpha2bDecorationDuplicateCleanup[] DecorationDuplicateCleanup { get; init; } = [];
    public string[] CustomSpawnerFiles { get; init; } = [];
    public string[] SpawnerFiles { get; init; } = [];
    public string[] BritainOnlySpawnerFiles { get; init; } = [];
    public string[] ExcludedSpawnerTypes { get; init; } = [];
    public bool GeneratePublicMoongates { get; init; }
    public int ExpectedPublicMoongates { get; init; }
    public bool GenerateKhaldunPuzzles { get; init; }
    public int ExpectedKhaldunDynamicItems { get; init; }
}

public sealed record Alpha2bRectangleBounds
{
    public int XMin { get; init; }
    public int YMin { get; init; }
    public int XMax { get; init; }
    public int YMax { get; init; }

    public bool Contains(Point3D location) =>
        location.X >= XMin && location.X <= XMax && location.Y >= YMin && location.Y <= YMax;
}

public sealed record Alpha2bDecorationRewrite
{
    public string Source { get; init; } = "";
    public string Match { get; init; } = "";
    public string Replacement { get; init; } = "";
    public int ExpectedMatches { get; init; }
    public string Reason { get; init; } = "";
}

public sealed record Alpha2bDecorationDuplicateCleanup
{
    public string Type { get; init; } = "";
    public int ItemId { get; init; }
    public int X { get; init; }
    public int Y { get; init; }
    public int Z { get; init; }
    public int Keep { get; init; }
}

public static class Alpha2bWorldGenerationConfiguration
{
    private const string RelativeManifestPath = "Configuration/alpha2b-world-generation.json";
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };

    public static Alpha2bWorldGenerationManifest? Manifest { get; private set; }
    public static string? Error { get; private set; }

    public static void Load()
    {
        Manifest = null;
        Error = null;

        try
        {
            var path = Path.Combine(Core.BaseDirectory, RelativeManifestPath);
            var manifest = JsonSerializer.Deserialize<Alpha2bWorldGenerationManifest>(File.ReadAllText(path), JsonOptions)
                           ?? throw new InvalidDataException("The Alpha 2b manifest is empty.");
            Validate(manifest, ShardRulesConfiguration.Settings.PinnedModernUoCommit);
            Manifest = manifest;
        }
        catch (Exception ex)
        {
            Error = ex.Message;
        }
    }

    public static string ResolveGeneratedPath(string relativePath)
    {
        var manifest = Manifest ?? throw new InvalidOperationException(Error ?? "The Alpha 2b manifest is not loaded.");
        var root = Path.GetFullPath(Path.Combine(Core.BaseDirectory, manifest.GeneratedDataRoot));
        var path = Path.GetFullPath(Path.Combine(root, relativePath));

        if (!path.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidDataException($"Alpha 2b path escapes its generated data root: {relativePath}");
        }

        return path;
    }

    public static void Validate(Alpha2bWorldGenerationManifest manifest, string expectedPinnedCommit)
    {
        if (manifest.SchemaVersion != 1)
        {
            throw new InvalidDataException($"Unsupported Alpha 2b manifest schema {manifest.SchemaVersion}.");
        }

        if (!string.Equals(manifest.Era, "UOR", StringComparison.Ordinal) ||
            !string.Equals(manifest.TargetMap, "Felucca", StringComparison.Ordinal))
        {
            throw new InvalidDataException("Alpha 2b generation must target the UOR era on Felucca.");
        }

        if (!string.Equals(
                manifest.PinnedModernUoCommit,
                expectedPinnedCommit,
                StringComparison.OrdinalIgnoreCase
            ))
        {
            throw new InvalidDataException("The Alpha 2b manifest and shard rules pin different ModernUO commits.");
        }

        if (manifest.MaximumEraMapXExclusive != 6144 || manifest.ExpectedPublicMoongates != 9 ||
            manifest.GenerateKhaldunPuzzles && manifest.ExpectedKhaldunDynamicItems != 63)
        {
            throw new InvalidDataException(
                "The Alpha 2b UOR map boundary, moongate expectation, or Khaldun expectation is invalid."
            );
        }

        ValidateRelativePath(manifest.GeneratedDataRoot, nameof(manifest.GeneratedDataRoot));
        ValidateRelativePath(manifest.DecorationsDirectory, nameof(manifest.DecorationsDirectory));
        ValidateRelativePath(manifest.SpawnersDirectory, nameof(manifest.SpawnersDirectory));
        ValidateRelativePath(manifest.SignsFile, nameof(manifest.SignsFile));
        ValidateRelativePath(manifest.TeleportersFile, nameof(manifest.TeleportersFile));

        if (manifest.DecorationFiles.Length == 0 || manifest.SpawnerFiles.Length == 0)
        {
            throw new InvalidDataException("The Alpha 2b generation allowlists cannot be empty.");
        }

        if (manifest.BritainBounds != new Alpha2bRectangleBounds
            {
                XMin = 1280, YMin = 1400, XMax = 1750, YMax = 1900
            })
        {
            throw new InvalidDataException("The Alpha 2b Greater Britain boundary is invalid.");
        }

        var spawnerFiles = manifest.SpawnerFiles.ToHashSet(StringComparer.OrdinalIgnoreCase);
        if (manifest.BritainOnlySpawnerFiles.Length == 0 ||
            manifest.BritainOnlySpawnerFiles.Any(file => !spawnerFiles.Contains(file)))
        {
            throw new InvalidDataException("Every Britain-only spawner source must be explicitly allowlisted.");
        }

        var decorationFiles = manifest.DecorationFiles.ToHashSet(StringComparer.OrdinalIgnoreCase);
        if (manifest.DecorationRewrites.Any(
                rewrite => !decorationFiles.Contains(rewrite.Source) ||
                           string.IsNullOrWhiteSpace(rewrite.Match) ||
                           string.IsNullOrWhiteSpace(rewrite.Replacement) ||
                           string.IsNullOrWhiteSpace(rewrite.Reason) || rewrite.ExpectedMatches <= 0
            ))
        {
            throw new InvalidDataException("Every Alpha 2b decoration rewrite must be explicit and allowlisted.");
        }

        if (manifest.DecorationDuplicateCleanup.Any(
                cleanup => cleanup.Type != nameof(Server.Items.SpikeTrap) || cleanup.ItemId != 0x111B ||
                           cleanup.Keep != 1
            ))
        {
            throw new InvalidDataException("Alpha 2b decoration duplicate cleanup contains an unsupported target.");
        }
    }

    private static void ValidateRelativePath(string path, string name)
    {
        if (string.IsNullOrWhiteSpace(path) || Path.IsPathRooted(path) || path.Split('/', '\\').Contains(".."))
        {
            throw new InvalidDataException($"{name} must be a safe relative path.");
        }
    }
}
