using System.Text.Json;
using Server;
using Server.Collections;
using Server.Commands;
using Server.Engines.CannedEvil;
using Server.Engines.Spawners;
using Server.Factions;
using Server.Items;
using Server.Json;
using Server.Mobiles;
using Server.Network;
using Server.Saves;

namespace BritanniaRenaissance.Content;

public static class Alpha2bWorldGenerationCommands
{
    private const string Confirmation = "CONFIRM-UOR-FELUCCA";

    public static void Register()
    {
        CommandSystem.Register("Alpha2bWorldGen", AccessLevel.Owner, OnCommand);
    }

    [Usage("Alpha2bWorldGen preview|apply CONFIRM-UOR-FELUCCA [rerun]|audit")]
    [Description("Previews, generates, or audits the era-reviewed Alpha 2b UOR/Felucca world baseline.")]
    private static void OnCommand(CommandEventArgs e)
    {
        var operation = e.GetString(0).ToLowerInvariant();

        switch (operation)
        {
            case "preview":
                Preview(e.Mobile);
                break;
            case "apply":
                Apply(e);
                break;
            case "audit":
                Audit(e.Mobile, true, null, "audit");
                break;
            default:
                e.Mobile.SendMessage(
                    $"Usage: {CommandSystem.Prefix}Alpha2bWorldGen preview|apply {Confirmation} [rerun]|audit"
                );
                break;
        }
    }

    private static void Preview(Mobile from)
    {
        if (!TryLoadInputs(from, out var inputs))
        {
            return;
        }

        var (feluccaItems, feluccaMobiles) = CountWorldObjects(Map.Felucca);
        from.SendMessage("Alpha 2b input validation passed: UOR / Felucca only.");
        from.SendMessage(
            $"Inputs: {inputs.DecorationFiles.Length} decoration files, {inputs.Signs.Count} signs, " +
            $"{inputs.TeleporterPlacementCount} teleporter placements, {inputs.Spawners.Count} spawners, " +
            $"and {inputs.DoorPlacementCount} Felucca door placements " +
            $"(manifest expects {inputs.Manifest.DoorGeneration.ExpectedPlacements})."
        );
        from.SendMessage($"Current Felucca world roots: {feluccaItems} items and {feluccaMobiles} non-player mobiles.");
        from.SendMessage($"Apply requires: {CommandSystem.Prefix}Alpha2bWorldGen apply {Confirmation}");
    }

    private static void Apply(CommandEventArgs e)
    {
        var from = e.Mobile;

        if (e.GetString(1) != Confirmation)
        {
            from.SendMessage($"Refusing generation without the exact confirmation token: {Confirmation}");
            return;
        }

        var rerun = string.Equals(e.GetString(2), "rerun", StringComparison.OrdinalIgnoreCase);
        if (e.Length > 2 && !rerun)
        {
            from.SendMessage("The only supported third argument is rerun.");
            return;
        }

        if (World.Saving)
        {
            from.SendMessage("Refusing generation while a world save is active.");
            return;
        }

        if (!TryLoadInputs(from, out var inputs))
        {
            return;
        }

        var (existingItems, existingMobiles) = CountWorldObjects(Map.Felucca);
        if ((existingItems != 0 || existingMobiles != 0) && !rerun)
        {
            from.SendMessage(
                $"Refusing a non-fresh world: Felucca has {existingItems} root items and {existingMobiles} non-player mobiles. " +
                "Use the explicit rerun argument only for a controlled convergence rehearsal."
            );
            return;
        }


        if (rerun)
        {
            from.SendMessage(
                $"Alpha 2b convergence rerun accepted over {existingItems} Felucca root items and " +
                $"{existingMobiles} non-player mobiles."
            );
        }

        if (!InactiveFacetsAreEmpty(out var inactiveError))
        {
            from.SendMessage($"Refusing generation: {inactiveError}");
            return;
        }

        try
        {
            var operations = new List<GenerationOperationReport>();
            NetState.FlushAll();
            from.SendMessage("Alpha 2b: generating era-reviewed Felucca decorations.");
            operations.AddRange(GenerateDecorations(inputs.DecorationFiles));
            operations.Add(NormalizeDecorationDuplicates(inputs.Manifest));

            from.SendMessage("Alpha 2b: generating pinned UOR Felucca town and shop doors.");
            operations.Add(GenerateDoors(inputs.DoorSets));

            from.SendMessage("Alpha 2b: generating Felucca teleporters.");
            operations.Add(GenerateTeleporters(inputs.Teleporters));

            from.SendMessage("Alpha 2b: generating UOR public moongates.");
            var moongatesBefore = CountItems<PublicMoongate>(Map.Felucca);
            PublicMoongate.MoonGen_OnCommand(new CommandEventArgs(from, "MoonGen", "", []));
            var moongatesAfter = CountItems<PublicMoongate>(Map.Felucca);
            operations.Add(
                new GenerationOperationReport(
                    "moongates", "PublicMoongate.MoonGen", "Felucca", moongatesAfter, moongatesBefore, 0, 0
                )
            );

            from.SendMessage("Alpha 2b: generating era-reviewed Felucca spawners.");
            operations.Add(GenerateSpawners(inputs.Spawners));

            from.SendMessage("Alpha 2b: generating Felucca shop and location signs.");
            operations.Add(GenerateSigns(inputs.Signs));

            if (inputs.Manifest.GenerateKhaldunPuzzles)
            {
                from.SendMessage("Alpha 2b: generating UOR Khaldun puzzle infrastructure.");
                var khaldunBefore = CountKhaldunDynamicItems();
                GenKhaldun.GenKhaldun_OnCommand(new CommandEventArgs(from, "GenKhaldun", "", []));
                var khaldunAfter = CountKhaldunDynamicItems();
                operations.Add(
                    new GenerationOperationReport(
                        "khaldun", "GenKhaldun", "Felucca", khaldunAfter - khaldunBefore, 0, khaldunBefore, 0
                    )
                );
            }

            var decorationCount = operations.Where(result => result.Stage == "decorations").Sum(result => result.Created);
            var teleporterCount = operations.Single(result => result.Stage == "teleporters").Created;
            var spawnerCount = operations.Single(result => result.Stage == "spawners").Created;
            var doorResult = operations.Single(result => result.Stage == "doors");
            from.SendMessage(
                $"Alpha 2b generated {decorationCount} decorations, {teleporterCount} teleporters, " +
                $"{spawnerCount} spawners, {inputs.Signs.Count} signs, and {doorResult.Created} doors " +
                $"({doorResult.Skipped} existing)."
            );

            if (!Audit(from, false, operations, rerun ? "rerun" : "apply"))
            {
                from.SendMessage("Alpha 2b audit failed. The world was not saved; stop the server and repeat from a clean reset.");
                return;
            }

            from.SendMessage("Alpha 2b audit passed. Saving the clean generated world now.");
            AutoSave.Save();
            from.SendMessage("Alpha 2b world generation and save completed.");
        }
        catch (Exception ex)
        {
            from.SendMessage($"Alpha 2b generation failed: {ex.GetType().Name}: {ex.Message}");
            from.SendMessage("The world was not saved; stop the server and repeat from a clean reset.");
        }
    }

    private static List<GenerationOperationReport> GenerateDecorations(IEnumerable<string> files)
    {
        var results = new List<GenerationOperationReport>();

        foreach (var file in files)
        {
            var before = CaptureRootItemSerials(Map.Felucca);
            var generated = 0;
            foreach (var list in DecorationList.ReadAll(file))
            {
                generated += list.Generate([Map.Felucca]);
            }

            var placements = CountDecorationPlacements(file);
            results.Add(
                new GenerationOperationReport(
                    "decorations",
                    Path.GetFileName(file),
                    "Felucca",
                    generated,
                    0,
                    placements - generated,
                    0
                )
                {
                    Details = DescribeNewRootItems(Map.Felucca, before)
                }
            );
        }

        return results;
    }

    private static GenerationOperationReport NormalizeDecorationDuplicates(
        Alpha2bWorldGenerationManifest manifest
    )
    {
        var removed = 0;
        var details = new List<string>();

        foreach (var cleanup in manifest.DecorationDuplicateCleanup)
        {
            var location = new Point3D(cleanup.X, cleanup.Y, cleanup.Z);
            var matches = new List<SpikeTrap>();
            foreach (var item in Map.Felucca.GetItemsAt<SpikeTrap>(location))
            {
                if (item.Z == cleanup.Z && item.ItemID == cleanup.ItemId)
                {
                    matches.Add(item);
                }
            }

            matches.Sort((left, right) => left.Serial.CompareTo(right.Serial));

            for (var index = cleanup.Keep; index < matches.Count; index++)
            {
                var duplicate = matches[index];
                details.Add(
                    $"removed {duplicate.GetType().FullName}|0x{duplicate.ItemID:X4}|" +
                    $"{duplicate.X},{duplicate.Y},{duplicate.Z}|{duplicate.Serial}"
                );
                duplicate.Delete();
                removed++;
            }
        }

        return new GenerationOperationReport(
            "decoration-cleanup", "manifest duplicate cleanup", "Felucca", 0, removed, 0, 0
        )
        {
            Details = details.ToArray()
        };
    }

    private static GenerationOperationReport GenerateDoors(IReadOnlyCollection<DoorSetDefinition> doorSets)
    {
        var created = 0;
        var skipped = 0;
        var failed = 0;
        var details = new List<string>();

        foreach (var doorSet in doorSets)
        {
            var resolved = new BaseDoor?[doorSet.Placements.Length];
            var newDoors = new List<BaseDoor>();
            var setFailed = false;

            for (var index = 0; index < doorSet.Placements.Length; index++)
            {
                var placement = doorSet.Placements[index];
                var matches = FindDoorsAtClosedLocation(placement.Location);
                if (matches.Count > 1)
                {
                    details.Add($"duplicate existing doors at {placement.Location}");
                    failed++;
                    setFailed = true;
                    continue;
                }

                if (matches.Count == 1)
                {
                    resolved[index] = matches[0];
                    skipped++;
                    continue;
                }

                if (!Map.Felucca.CanFit(
                        placement.Location.X,
                        placement.Location.Y,
                        placement.Location.Z,
                        16,
                        false,
                        false
                    ))
                {
                    details.Add($"blocked door placement at {placement.Location}");
                    failed++;
                    setFailed = true;
                    continue;
                }

                var door = new DarkWoodDoor(placement.Facing);
                door.MoveToWorld(placement.Location, Map.Felucca);
                resolved[index] = door;
                newDoors.Add(door);
            }

            if (!setFailed && resolved.Length == 2)
            {
                var first = resolved[0]!;
                var second = resolved[1]!;
                if ((first.Link is not null && first.Link != second) ||
                    (second.Link is not null && second.Link != first))
                {
                    details.Add($"conflicting door link at {first.Location} / {second.Location}");
                    failed++;
                    setFailed = true;
                }
                else
                {
                    first.Link = second;
                    second.Link = first;
                }
            }

            if (setFailed)
            {
                foreach (var door in newDoors)
                {
                    door.Delete();
                }
            }
            else
            {
                created += newDoors.Count;
                details.AddRange(
                    newDoors.Select(
                        door => $"created {door.GetType().FullName}|0x{door.ItemID:X4}|" +
                                $"{door.X},{door.Y},{door.Z}|{door.Serial}"
                    )
                );
            }
        }

        return new GenerationOperationReport(
            "doors", "pinned DoorGenerator Felucca scan", "Felucca", created, 0, skipped, failed
        )
        {
            Details = details.ToArray()
        };
    }

    private static GenerationOperationReport GenerateTeleporters(IEnumerable<TeleporterDefinition> definitions)
    {
        var generated = 0;
        var replaced = 0;

        foreach (var definition in definitions)
        {
            replaced += DeleteGenericTeleporters(definition.Source);
            new Teleporter(definition.Destination, Map.Felucca).MoveToWorld(definition.Source, Map.Felucca);
            generated++;

            if (definition.Back)
            {
                replaced += DeleteGenericTeleporters(definition.Destination);
                new Teleporter(definition.Source, Map.Felucca).MoveToWorld(definition.Destination, Map.Felucca);
                generated++;
            }
        }

        return new GenerationOperationReport(
            "teleporters", "teleporters.json", "Felucca", generated, replaced, 0, 0
        );
    }

    private static int DeleteGenericTeleporters(WorldLocation location)
    {
        using var queue = PooledRefQueue<Item>.Create();

        foreach (var item in Map.Felucca.GetItemsAt<Teleporter>(location))
        {
            if (item is not (KeywordTeleporter or SkillTeleporter) && Math.Abs(item.Z - location.Z) <= 12)
            {
                queue.Enqueue(item);
            }
        }

        var deleted = queue.Count;
        while (queue.Count > 0)
        {
            queue.Dequeue().Delete();
        }

        return deleted;
    }

    private static GenerationOperationReport GenerateSpawners(IEnumerable<SpawnerDto> definitions)
    {
        var generated = 0;
        var replaced = 0;
        var existingByGuid = CountSpawnersByGuid();

        foreach (var definition in definitions)
        {
            var spawner = definition.ToSpawner();
            var type = spawner.GetType();
            var obsolete = new HashSet<BaseSpawner>();

            if (existingByGuid.TryGetValue(definition.Guid, out var priorMatches))
            {
                foreach (var prior in priorMatches)
                {
                    if (prior != spawner && !prior.Deleted)
                    {
                        obsolete.Add(prior);
                    }
                }
            }

            foreach (var existing in Map.Felucca.GetItemsAt<BaseSpawner>(definition.Location))
            {
                if (existing != spawner && existing.GetType() == type)
                {
                    obsolete.Add(existing);
                }
            }

            foreach (var prior in obsolete)
            {
                prior.Delete();
                replaced++;
            }

            try
            {
                spawner.MoveToWorld(definition.Location, Map.Felucca);
                spawner.Respawn();
                generated++;
            }
            catch
            {
                spawner.Delete();
                throw;
            }
        }

        return new GenerationOperationReport(
            "spawners", "manifest allowlist", "Felucca", generated, replaced, 0, 0
        );
    }

    private static GenerationOperationReport GenerateSigns(IEnumerable<SignDefinition> definitions)
    {
        var generated = 0;
        var replaced = 0;
        foreach (var definition in definitions)
        {
            replaced += CountSignsAtPlacement(definition);
            SignParser.Add_Static(definition.ItemId, definition.Location, Map.Felucca, definition.Text);
            generated++;
        }

        return new GenerationOperationReport("signs", "signs.cfg", "Felucca", generated, replaced, 0, 0);
    }

    private static bool Audit(
        Mobile from,
        bool reportSuccess,
        IReadOnlyCollection<GenerationOperationReport>? operations,
        string operation
    )
    {
        if (!TryLoadInputs(from, out var inputs))
        {
            return false;
        }

        var errors = new List<string>();

        if (!InactiveFacetsAreEmpty(out var inactiveError))
        {
            errors.Add(inactiveError);
        }

        var doorPlacementCounts = inputs.DoorSets.SelectMany(set => set.Placements)
            .Select(placement => FindDoorsAtClosedLocation(placement.Location).Count)
            .ToArray();
        var doorsFound = doorPlacementCounts.Count(count => count == 1);
        var doorLinksValid = inputs.DoorSets.Where(set => set.Placements.Length == 2).Count(
            set =>
            {
                var first = FindDoorsAtClosedLocation(set.Placements[0].Location);
                var second = FindDoorsAtClosedLocation(set.Placements[1].Location);
                return first.Count == 1 && second.Count == 1 &&
                       first[0].Link == second[0] && second[0].Link == first[0];
            }
        );
        var expectedLinkedDoorSets = inputs.DoorSets.Count(set => set.Placements.Length == 2);
        if (inputs.DoorPlacementCount != inputs.Manifest.DoorGeneration.ExpectedPlacements ||
            doorsFound != inputs.DoorPlacementCount || doorPlacementCounts.Any(count => count != 1) ||
            doorLinksValid != expectedLinkedDoorSets)
        {
            errors.Add(
                $"doors exact {doorsFound}/{inputs.DoorPlacementCount}, " +
                $"manifest expectation {inputs.Manifest.DoorGeneration.ExpectedPlacements}; " +
                $"duplicate or missing placements {doorPlacementCounts.Count(count => count != 1)}, " +
                $"linked pairs {doorLinksValid}/{expectedLinkedDoorSets}"
            );
        }

        var operationFailures = operations?.Sum(result => result.Failed) ?? 0;
        if (operationFailures != 0)
        {
            errors.Add($"generation operation failures {operationFailures}/0");
        }

        var signCounts = inputs.Signs.Select(CountMatchingSigns).ToArray();
        var signPlacementCounts = inputs.Signs.Select(CountSignsAtPlacement).ToArray();
        var signsFound = signCounts.Count(count => count == 1);
        if (signsFound != inputs.Signs.Count || signPlacementCounts.Any(count => count != 1))
        {
            errors.Add(
                $"signs exact {signsFound}/{inputs.Signs.Count}; " +
                $"duplicate or unexpected-label placements {signPlacementCounts.Count(count => count != 1)}"
            );
        }

        var teleporterMatches = inputs.Teleporters.Select(CountMatchingTeleporters).ToArray();
        var teleporterPlacementCounts = inputs.Teleporters.Select(
            definition => CountGenericTeleportersAt(definition.Source)
        ).ToArray();
        var teleportersFound = teleporterMatches.Count(count => count == 1);
        if (teleportersFound != inputs.TeleporterPlacementCount || teleporterPlacementCounts.Any(count => count != 1))
        {
            errors.Add(
                $"teleporters exact {teleportersFound}/{inputs.TeleporterPlacementCount}; " +
                $"duplicate or conflicting placements {teleporterPlacementCounts.Count(count => count != 1)}"
            );
        }

        var spawnersByGuid = CountSpawnersByGuid();
        var spawnersFound = inputs.Spawners.Count(
            definition => spawnersByGuid.TryGetValue(definition.Guid, out var matches) &&
                          matches.Count == 1 && matches[0].Location == definition.Location
        );
        if (spawnersFound != inputs.Spawners.Count)
        {
            var duplicates = inputs.Spawners.Count(
                definition => spawnersByGuid.TryGetValue(definition.Guid, out var matches) && matches.Count > 1
            );
            errors.Add($"spawners exact {spawnersFound}/{inputs.Spawners.Count}; duplicate GUIDs {duplicates}");
        }

        var moongates = CountItems<PublicMoongate>(Map.Felucca);
        if (moongates != inputs.Manifest.ExpectedPublicMoongates)
        {
            errors.Add($"public moongates {moongates}/{inputs.Manifest.ExpectedPublicMoongates}");
        }

        var khaldunItems = CountKhaldunDynamicItems();
        if (inputs.Manifest.GenerateKhaldunPuzzles &&
            khaldunItems != inputs.Manifest.ExpectedKhaldunDynamicItems)
        {
            errors.Add(
                $"Khaldun dynamic items {khaldunItems}/{inputs.Manifest.ExpectedKhaldunDynamicItems}"
            );
        }

        var championSpawns = CountItems<ChampionSpawn>(Map.Felucca);
        if (championSpawns != 0)
        {
            errors.Add($"excluded champion spawns {championSpawns}/0");
        }

        var factionInfrastructure = CountItems<BaseMonolith>(Map.Felucca) +
                                    CountItems<JoinStone>(Map.Felucca) +
                                    CountItems<FactionStone>(Map.Felucca) +
                                    CountItems<TownStone>(Map.Felucca) +
                                    CountItems<Sigil>(Map.Felucca);
        if (FactionSystem.Enabled || factionInfrastructure != 0)
        {
            errors.Add(
                $"excluded Faction state enabled={FactionSystem.Enabled}, infrastructure={factionInfrastructure}/0"
            );
        }

        var (items, mobiles) = CountWorldObjects(Map.Felucca);
        try
        {
            WriteExecutionReport(
                inputs,
                operation,
                operations ?? [],
                signsFound,
                doorsFound,
                inputs.DoorPlacementCount,
                doorLinksValid,
                expectedLinkedDoorSets,
                teleportersFound,
                spawnersFound,
                moongates,
                khaldunItems,
                championSpawns,
                factionInfrastructure,
                items,
                mobiles,
                errors
            );
        }
        catch (Exception ex)
        {
            errors.Add($"execution report could not be written: {ex.Message}");
        }

        if (errors.Count > 0)
        {
            from.SendMessage($"Alpha 2b audit failed: {string.Join("; ", errors)}.");
            return false;
        }

        if (reportSuccess)
        {
            from.SendMessage(
                $"Alpha 2b audit passed: {signsFound} signs, {teleportersFound} teleporters, " +
                $"{spawnersFound} spawners, {doorsFound} doors, {moongates} moongates, " +
                $"{khaldunItems} Khaldun dynamic items; " +
                $"excluded champions {championSpawns}, Faction infrastructure {factionInfrastructure}; " +
                $"Felucca roots {items} items/{mobiles} non-player mobiles."
            );
        }

        return true;
    }

    private static int CountDecorationPlacements(string path)
    {
        var count = 0;
        foreach (var line in File.ReadLines(path))
        {
            var parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length >= 3 && int.TryParse(parts[0], out _) && int.TryParse(parts[1], out _) &&
                int.TryParse(parts[2], out _))
            {
                count++;
            }
        }

        return count;
    }

    private static HashSet<Serial> CaptureRootItemSerials(Map map)
    {
        var serials = new HashSet<Serial>();
        var bounds = new Rectangle2D(0, 0, map.Width, map.Height);
        foreach (var item in map.GetItemsInBounds(bounds))
        {
            if (item.Parent is null)
            {
                serials.Add(item.Serial);
            }
        }

        return serials;
    }

    private static string[] DescribeNewRootItems(Map map, HashSet<Serial> before)
    {
        var details = new List<string>();
        var bounds = new Rectangle2D(0, 0, map.Width, map.Height);
        foreach (var item in map.GetItemsInBounds(bounds))
        {
            if (item.Parent is null && !before.Contains(item.Serial))
            {
                details.Add(
                    $"{item.GetType().FullName}|0x{item.ItemID:X4}|{item.X},{item.Y},{item.Z}|{item.Serial}"
                );
            }
        }

        details.Sort(StringComparer.Ordinal);
        return details.ToArray();
    }

    private static int CountKhaldunDynamicItems()
    {
        var bounds = new Rectangle2D(5380, 1320, 160, 200);
        return CountItemsInBounds<MorphItem>(Map.Felucca, bounds) +
               CountItemsInBounds<EffectController>(Map.Felucca, bounds) +
               CountItemsInBounds<RaiseSwitch>(Map.Felucca, bounds) +
               CountItemsInBounds<RaisableItem>(Map.Felucca, bounds);
    }

    private static void WriteExecutionReport(
        GenerationInputs inputs,
        string operation,
        IReadOnlyCollection<GenerationOperationReport> operations,
        int signs,
        int doors,
        int doorPlacements,
        int linkedDoorSets,
        int expectedLinkedDoorSets,
        int teleporters,
        int spawners,
        int moongates,
        int khaldunItems,
        int championSpawns,
        int factionInfrastructure,
        int feluccaItems,
        int feluccaMobiles,
        IReadOnlyCollection<string> errors
    )
    {
        var utcNow = DateTime.UtcNow;
        var report = new
        {
            schemaVersion = 2,
            generatedUtc = utcNow.ToString("O"),
            operation,
            manifestSchemaVersion = inputs.Manifest.SchemaVersion,
            inputs.Manifest.PinnedModernUoCommit,
            targetEra = inputs.Manifest.Era,
            targetMap = inputs.Manifest.TargetMap,
            operations,
            audit = new
            {
                passed = errors.Count == 0,
                signs,
                doors,
                doorPlacements,
                expectedDoorPlacements = inputs.Manifest.DoorGeneration.ExpectedPlacements,
                linkedDoorSets,
                expectedLinkedDoorSets,
                teleporters,
                spawners,
                moongates,
                khaldunDynamicItems = khaldunItems,
                championSpawns,
                factionEnabled = FactionSystem.Enabled,
                factionInfrastructure,
                inactiveFacetsEmpty = !errors.Any(error => error.StartsWithOrdinal("inactive facet")),
                britainOnlySpawners = inputs.BritainOnlySpawners,
                britainOnlySpawnersOutsideGreaterBritain = 0,
                feluccaRootItems = feluccaItems,
                feluccaNonPlayerMobiles = feluccaMobiles,
                errors
            }
        };

        var directory = Path.Combine(Core.BaseDirectory, "Logs", "BritanniaRenaissance", "Alpha2b");
        Directory.CreateDirectory(directory);
        var fileName = $"{utcNow:yyyyMMdd-HHmmss-fff}-{operation}-{Guid.NewGuid():N}.json";
        File.WriteAllText(
            Path.Combine(directory, fileName),
            JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true })
        );
    }

    private static bool TryLoadInputs(Mobile from, out GenerationInputs inputs)
    {
        inputs = default!;

        if (Core.Expansion != Expansion.UOR)
        {
            from.SendMessage($"Alpha 2b requires Expansion.UOR; the server reports {Core.Expansion}.");
            return false;
        }

        Alpha2bWorldGenerationConfiguration.Load();
        var manifest = Alpha2bWorldGenerationConfiguration.Manifest;
        if (manifest is null)
        {
            from.SendMessage($"Alpha 2b configuration is invalid: {Alpha2bWorldGenerationConfiguration.Error}");
            return false;
        }

        try
        {
            var decorationDirectory = Alpha2bWorldGenerationConfiguration.ResolveGeneratedPath(
                manifest.DecorationsDirectory
            );
            var decorationFiles = Directory.GetFiles(decorationDirectory, "*.cfg").Order().ToArray();
            var expectedDecorationFiles = manifest.DecorationFiles.Length + manifest.CustomDecorationFiles.Length;
            if (decorationFiles.Length != expectedDecorationFiles)
            {
                throw new InvalidDataException(
                    $"Expected {expectedDecorationFiles} decoration files but found {decorationFiles.Length}."
                );
            }

            var signs = ReadSigns(Alpha2bWorldGenerationConfiguration.ResolveGeneratedPath(manifest.SignsFile));
            var teleporters = JsonConfig.Deserialize<List<TeleporterDefinition>>(
                Alpha2bWorldGenerationConfiguration.ResolveGeneratedPath(manifest.TeleportersFile)
            );
            var spawners = new List<SpawnerDto>();
            var britainOnlySpawners = 0;
            var britainOnlySources = manifest.BritainOnlySpawnerFiles.ToHashSet(StringComparer.OrdinalIgnoreCase);

            foreach (var fileName in manifest.SpawnerFiles)
            {
                var path = Alpha2bWorldGenerationConfiguration.ResolveGeneratedPath(
                    Path.Combine(manifest.SpawnersDirectory, fileName)
                );
                var definitions = JsonConfig.Deserialize<List<SpawnerDto>>(path, SpawnerJsonSerializer.Options);
                if (britainOnlySources.Contains(fileName))
                {
                    var outsideBritain = definitions.Count(
                        definition => !manifest.BritainBounds.Contains(definition.Location)
                    );
                    if (outsideBritain != 0)
                    {
                        throw new InvalidDataException(
                            $"Britain-only spawner source {fileName} contains {outsideBritain} placements outside Greater Britain."
                        );
                    }

                    britainOnlySpawners += definitions.Count;
                }

                spawners.AddRange(definitions);
            }

            foreach (var fileName in manifest.CustomSpawnerFiles)
            {
                var path = Alpha2bWorldGenerationConfiguration.ResolveGeneratedPath(
                    Path.Combine(manifest.SpawnersDirectory, fileName)
                );
                spawners.AddRange(JsonConfig.Deserialize<List<SpawnerDto>>(path, SpawnerJsonSerializer.Options));
            }

            var canonicalTeleporters = CanonicalizeTeleporters(teleporters);
            var canonicalSpawners = CanonicalizeSpawners(spawners);
            var doorSets = ReadDoorSets(manifest.DoorGeneration);
            ValidateInputs(manifest, signs, canonicalTeleporters, canonicalSpawners);
            inputs = new GenerationInputs(
                manifest,
                decorationFiles,
                signs,
                canonicalTeleporters,
                canonicalSpawners,
                britainOnlySpawners,
                doorSets
            );
            return true;
        }
        catch (Exception ex)
        {
            from.SendMessage($"Alpha 2b input validation failed: {ex.Message}");
            return false;
        }
    }

    private static void ValidateInputs(
        Alpha2bWorldGenerationManifest manifest,
        IReadOnlyCollection<SignDefinition> signs,
        IReadOnlyCollection<TeleporterDefinition> teleporters,
        IReadOnlyCollection<SpawnerDto> spawners
    )
    {
        if (signs.Count == 0 || signs.Any(sign => sign.MapCode != 1))
        {
            throw new InvalidDataException("Every generated sign must explicitly target Felucca.");
        }

        if (teleporters.Count == 0 || teleporters.Any(
                teleporter => teleporter.Source.Map != Map.Felucca || teleporter.Destination.Map != Map.Felucca ||
                              teleporter.Source.X >= manifest.MaximumEraMapXExclusive ||
                              teleporter.Destination.X >= manifest.MaximumEraMapXExclusive
            ))
        {
            throw new InvalidDataException("Every generated teleporter must remain inside the UOR Felucca map boundary.");
        }

        var excludedTypes = manifest.ExcludedSpawnerTypes.ToHashSet(StringComparer.OrdinalIgnoreCase);
        if (spawners.Count == 0 || spawners.Any(
                spawner => spawner.Map != Map.Felucca ||
                           spawner.EntryView.Any(entry => excludedTypes.Contains(entry.SpawnedName))
            ))
        {
            throw new InvalidDataException("Generated spawners contain a disabled facet or excluded post-UOR type.");
        }
    }

    private static List<TeleporterDefinition> CanonicalizeTeleporters(
        IEnumerable<TeleporterDefinition> definitions
    )
    {
        var placements = new List<TeleporterDefinition>();

        void AddPlacement(WorldLocation source, WorldLocation destination)
        {
            for (var i = placements.Count - 1; i >= 0; i--)
            {
                var existing = placements[i].Source;
                if (existing.X == source.X && existing.Y == source.Y && Math.Abs(existing.Z - source.Z) <= 12)
                {
                    placements.RemoveAt(i);
                }
            }

            placements.Add(new TeleporterDefinition { Source = source, Destination = destination, Back = false });
        }

        foreach (var definition in definitions)
        {
            AddPlacement(definition.Source, definition.Destination);
            if (definition.Back)
            {
                AddPlacement(definition.Destination, definition.Source);
            }
        }

        return placements;
    }

    private static List<SpawnerDto> CanonicalizeSpawners(IReadOnlyList<SpawnerDto> definitions)
    {
        var locations = new HashSet<string>(StringComparer.Ordinal);
        var guids = new HashSet<Guid>();
        var canonical = new List<SpawnerDto>();

        for (var i = definitions.Count - 1; i >= 0; i--)
        {
            var definition = definitions[i];
            var locationKey = $"{definition.GetType().FullName}|{definition.Map}|" +
                              $"{definition.Location.X}|{definition.Location.Y}|{definition.Location.Z}";

            if (locations.Add(locationKey) && guids.Add(definition.Guid))
            {
                canonical.Add(definition);
            }
        }

        canonical.Reverse();
        return canonical;
    }

    private static List<SignDefinition> ReadSigns(string path)
    {
        var signs = new List<SignDefinition>();

        foreach (var line in File.ReadLines(path))
        {
            if (string.IsNullOrWhiteSpace(line))
            {
                continue;
            }

            var parts = line.Split(' ', 6, StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length != 6)
            {
                throw new InvalidDataException($"Invalid sign record: {line}");
            }

            signs.Add(
                new SignDefinition(
                    int.Parse(parts[0]),
                    int.Parse(parts[1]),
                    new Point3D(int.Parse(parts[2]), int.Parse(parts[3]), int.Parse(parts[4])),
                    parts[5]
                )
            );
        }

        return signs;
    }

    private static List<DoorSetDefinition> ReadDoorSets(Alpha2bDoorGeneration configuration)
    {
        var sets = new List<DoorSetDefinition>();
        var seen = new HashSet<DoorLocationKey>();

        foreach (var region in configuration.Regions)
        {
            for (var x = region.XMin; x < region.XMaxExclusive; x++)
            {
                for (var y = region.YMin; y < region.YMaxExclusive; y++)
                {
                    foreach (var tile in Map.Felucca.Tiles.GetStaticTiles(x, y))
                    {
                        if (DoorGenerator.IsWestFrame(tile.ID))
                        {
                            if (TryFindFrameZ(x + 2, y, tile.Z, DoorGenerator.IsEastFrame, out var newZ))
                            {
                                AddDoorSet(
                                    [new DoorPlacement(new Point3D(x + 1, y, Math.Min(tile.Z, newZ)), DoorFacing.WestCW)]
                                );
                            }
                            else if (TryFindFrameZ(x + 3, y, tile.Z, DoorGenerator.IsEastFrame, out newZ))
                            {
                                AddDoorSet(
                                    [
                                        new DoorPlacement(
                                            new Point3D(x + 1, y, Math.Min(tile.Z, newZ)), DoorFacing.WestCW
                                        ),
                                        new DoorPlacement(
                                            new Point3D(x + 2, y, Math.Min(tile.Z, newZ)), DoorFacing.EastCCW
                                        )
                                    ]
                                );
                            }
                        }
                        else if (DoorGenerator.IsNorthFrame(tile.ID))
                        {
                            if (TryFindFrameZ(x, y + 2, tile.Z, DoorGenerator.IsSouthFrame, out var newZ))
                            {
                                AddDoorSet(
                                    [new DoorPlacement(new Point3D(x, y + 1, Math.Min(tile.Z, newZ)), DoorFacing.SouthCW)]
                                );
                            }
                            else if (TryFindFrameZ(x, y + 3, tile.Z, DoorGenerator.IsSouthFrame, out newZ))
                            {
                                AddDoorSet(
                                    [
                                        new DoorPlacement(
                                            new Point3D(x, y + 1, Math.Min(tile.Z, newZ)), DoorFacing.NorthCCW
                                        ),
                                        new DoorPlacement(
                                            new Point3D(x, y + 2, Math.Min(tile.Z, newZ)), DoorFacing.SouthCW
                                        )
                                    ]
                                );
                            }
                        }
                    }
                }
            }
        }

        return sets;

        void AddDoorSet(DoorPlacement[] placements)
        {
            if (placements.Any(
                    placement => configuration.Exclusions.Any(
                        exclusion => exclusion.Contains(placement.Location.X, placement.Location.Y)
                    )
                ))
            {
                return;
            }

            var keys = placements.Select(placement => DoorLocationKey.From(placement.Location)).ToArray();
            if (keys.Any(seen.Contains) || placements.Any(
                    placement => !CanFitStaticDoor(placement.Location)
                ))
            {
                return;
            }

            foreach (var key in keys)
            {
                seen.Add(key);
            }

            sets.Add(new DoorSetDefinition(placements));
        }
    }

    private static bool CanFitStaticDoor(Point3D location)
    {
        const int height = 16;
        var map = Map.Felucca;
        var hasSurface = false;
        var landTile = map.Tiles.GetLandTile(location.X, location.Y);
        map.GetAverageZ(location.X, location.Y, out var lowZ, out var averageZ, out _);
        var landFlags = TileData.LandTable[landTile.ID & TileData.MaxLandValue].Flags;

        if ((landFlags & TileFlag.Impassable) != 0 && averageZ > location.Z &&
            location.Z + height > lowZ)
        {
            return false;
        }

        if ((landFlags & TileFlag.Impassable) == 0 && location.Z == averageZ && !landTile.Ignored)
        {
            hasSurface = true;
        }

        foreach (var tile in map.Tiles.GetStaticTiles(location.X, location.Y))
        {
            var data = TileData.ItemTable[tile.ID & TileData.MaxItemValue];
            if ((data.Surface || data.Impassable) && tile.Z + data.CalcHeight > location.Z &&
                location.Z + height > tile.Z)
            {
                return false;
            }

            if (data.Surface && !data.Impassable && location.Z == tile.Z + data.CalcHeight)
            {
                hasSurface = true;
            }
        }

        return hasSurface;
    }

    private static bool TryFindFrameZ(
        int x,
        int y,
        int z,
        Func<int, bool> isFrame,
        out int newZ
    )
    {
        foreach (var tile in Map.Felucca.Tiles.GetStaticTiles(x, y))
        {
            if (isFrame(tile.ID) && tile.Z - z is >= -1 and <= 1)
            {
                newZ = tile.Z;
                return true;
            }
        }

        newZ = -1;
        return false;
    }

    private static List<BaseDoor> FindDoorsAtClosedLocation(Point3D location)
    {
        var matches = new List<BaseDoor>();
        foreach (var door in Map.Felucca.GetItemsInRange<BaseDoor>(location, 2))
        {
            var closedLocation = door.Open
                ? new Point3D(door.X - door.Offset.X, door.Y - door.Offset.Y, door.Z - door.Offset.Z)
                : door.Location;
            // Stock decoration data contains a small number of intentional doors one or two Z
            // units away from the map-frame Z. DoorGenerator's CanFit check treats those doors as
            // occupying the candidate, so the shard-owned pass must preserve and audit them too.
            if (closedLocation.X == location.X && closedLocation.Y == location.Y &&
                Math.Abs(closedLocation.Z - location.Z) <= 2)
            {
                matches.Add(door);
            }
        }

        return matches;
    }

    private static int CountMatchingSigns(SignDefinition definition)
    {
        var count = 0;
        foreach (var sign in Map.Felucca.GetItemsAt<Sign>(definition.Location))
        {
            if (sign.Z != definition.Location.Z || sign.ItemID != definition.ItemId)
            {
                continue;
            }

            if (definition.Text.StartsWithOrdinal("#"))
            {
                if (sign is LocalizedSign localized &&
                    localized.LabelNumber == int.Parse(definition.Text.AsSpan()[1..]))
                {
                    count++;
                }
            }
            else if (sign is not LocalizedSign && string.Equals(sign.Name, definition.Text, StringComparison.Ordinal))
            {
                count++;
            }
        }

        return count;
    }

    private static int CountSignsAtPlacement(SignDefinition definition)
    {
        var count = 0;
        foreach (var sign in Map.Felucca.GetItemsAt<Sign>(definition.Location))
        {
            if (sign.Z == definition.Location.Z && sign.ItemID == definition.ItemId)
            {
                count++;
            }
        }

        return count;
    }

    private static int CountMatchingTeleporters(TeleporterDefinition definition)
    {
        var count = 0;
        foreach (var teleporter in Map.Felucca.GetItemsAt<Teleporter>(definition.Source))
        {
            if (teleporter is not (KeywordTeleporter or SkillTeleporter) &&
                Math.Abs(teleporter.Z - definition.Source.Z) <= 12 &&
                teleporter.PointDest == definition.Destination && teleporter.MapDest == Map.Felucca)
            {
                count++;
            }
        }

        return count;
    }

    private static int CountGenericTeleportersAt(WorldLocation source)
    {
        var count = 0;
        foreach (var teleporter in Map.Felucca.GetItemsAt<Teleporter>(source))
        {
            if (teleporter is not (KeywordTeleporter or SkillTeleporter) && Math.Abs(teleporter.Z - source.Z) <= 12)
            {
                count++;
            }
        }

        return count;
    }

    private static Dictionary<Guid, List<BaseSpawner>> CountSpawnersByGuid()
    {
        var result = new Dictionary<Guid, List<BaseSpawner>>();
        var bounds = new Rectangle2D(0, 0, Map.Felucca.Width, Map.Felucca.Height);
        foreach (var spawner in Map.Felucca.GetItemsInBounds<BaseSpawner>(bounds))
        {
            if (!result.TryGetValue(spawner.Guid, out var matches))
            {
                matches = [];
                result.Add(spawner.Guid, matches);
            }

            matches.Add(spawner);
        }

        return result;
    }

    private static bool InactiveFacetsAreEmpty(out string error)
    {
        foreach (var map in new[] { Map.Trammel, Map.Ilshenar, Map.Malas, Map.Tokuno, Map.TerMur })
        {
            var (items, mobiles) = CountWorldObjects(map);
            if (items != 0 || mobiles != 0)
            {
                error = $"inactive facet {map.Name} contains {items} root items and {mobiles} non-player mobiles";
                return false;
            }
        }

        error = "";
        return true;
    }

    private static (int Items, int Mobiles) CountWorldObjects(Map map)
    {
        var bounds = new Rectangle2D(0, 0, map.Width, map.Height);
        var items = 0;
        var mobiles = 0;

        foreach (var item in map.GetItemsInBounds(bounds))
        {
            if (item.Parent is null)
            {
                items++;
            }
        }

        foreach (var mobile in map.GetMobilesInBounds(bounds))
        {
            if (mobile is not PlayerMobile)
            {
                mobiles++;
            }
        }

        return (items, mobiles);
    }

    private static int CountItems<T>(Map map) where T : Item =>
        CountItemsInBounds<T>(map, new Rectangle2D(0, 0, map.Width, map.Height));

    private static int CountItemsInBounds<T>(Map map, Rectangle2D bounds) where T : Item
    {
        var count = 0;
        foreach (var item in map.GetItemsInBounds<T>(bounds))
        {
            count++;
        }

        return count;
    }

    private sealed record SignDefinition(int MapCode, int ItemId, Point3D Location, string Text);

    private readonly record struct DoorLocationKey(int X, int Y, int Z)
    {
        public static DoorLocationKey From(Point3D point) => new(point.X, point.Y, point.Z);
    }

    private sealed record DoorPlacement(Point3D Location, DoorFacing Facing);

    private sealed record DoorSetDefinition(DoorPlacement[] Placements);

    private sealed record GenerationOperationReport(
        string Stage,
        string Source,
        string Facet,
        int Created,
        int Replaced,
        int Skipped,
        int Failed
    )
    {
        public string[] Details { get; init; } = [];
    }

    private sealed record GenerationInputs(
        Alpha2bWorldGenerationManifest Manifest,
        string[] DecorationFiles,
        List<SignDefinition> Signs,
        List<TeleporterDefinition> Teleporters,
        List<SpawnerDto> Spawners,
        int BritainOnlySpawners,
        List<DoorSetDefinition> DoorSets
    )
    {
        public int TeleporterPlacementCount => Teleporters.Sum(teleporter => teleporter.Back ? 2 : 1);
        public int DoorPlacementCount => DoorSets.Sum(set => set.Placements.Length);
    }
}
