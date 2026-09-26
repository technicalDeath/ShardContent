using Server;
using Server.Collections;
using Server.Commands;
using Server.Engines.Spawners;
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
                Audit(e.Mobile, true);
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
            $"{inputs.TeleporterPlacementCount} teleporter placements, {inputs.Spawners.Count} spawners."
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
            NetState.FlushAll();
            from.SendMessage("Alpha 2b: generating era-reviewed Felucca decorations.");
            var decorationCount = GenerateDecorations(inputs.DecorationFiles);

            from.SendMessage("Alpha 2b: generating Felucca teleporters.");
            var teleporterCount = GenerateTeleporters(inputs.Teleporters);

            from.SendMessage("Alpha 2b: generating UOR public moongates.");
            PublicMoongate.MoonGen_OnCommand(new CommandEventArgs(from, "MoonGen", "", []));

            from.SendMessage("Alpha 2b: generating era-reviewed Felucca spawners.");
            var spawnerCount = GenerateSpawners(inputs.Spawners);

            from.SendMessage("Alpha 2b: generating Felucca shop and location signs.");
            GenerateSigns(inputs.Signs);

            from.SendMessage("Alpha 2b: generating UOR Khaldun puzzle infrastructure.");
            GenKhaldun.GenKhaldun_OnCommand(new CommandEventArgs(from, "GenKhaldun", "", []));

            from.SendMessage(
                $"Alpha 2b generated {decorationCount} decorations, {teleporterCount} teleporters, " +
                $"{spawnerCount} spawners, and {inputs.Signs.Count} signs."
            );

            if (!Audit(from, false))
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

    private static int GenerateDecorations(IEnumerable<string> files)
    {
        var generated = 0;

        foreach (var file in files)
        {
            foreach (var list in DecorationList.ReadAll(file))
            {
                generated += list.Generate([Map.Felucca]);
            }
        }

        return generated;
    }

    private static int GenerateTeleporters(IEnumerable<TeleporterDefinition> definitions)
    {
        var generated = 0;

        foreach (var definition in definitions)
        {
            DeleteGenericTeleporters(definition.Source);
            new Teleporter(definition.Destination, Map.Felucca).MoveToWorld(definition.Source, Map.Felucca);
            generated++;

            if (definition.Back)
            {
                DeleteGenericTeleporters(definition.Destination);
                new Teleporter(definition.Source, Map.Felucca).MoveToWorld(definition.Destination, Map.Felucca);
                generated++;
            }
        }

        return generated;
    }

    private static void DeleteGenericTeleporters(WorldLocation location)
    {
        using var queue = PooledRefQueue<Item>.Create();

        foreach (var item in Map.Felucca.GetItemsAt<Teleporter>(location))
        {
            if (item is not (KeywordTeleporter or SkillTeleporter) && Math.Abs(item.Z - location.Z) <= 12)
            {
                queue.Enqueue(item);
            }
        }

        while (queue.Count > 0)
        {
            queue.Dequeue().Delete();
        }
    }

    private static int GenerateSpawners(IEnumerable<SpawnerDto> definitions)
    {
        var generated = 0;

        foreach (var definition in definitions)
        {
            var spawner = definition.ToSpawner();
            var type = spawner.GetType();
            using var queue = PooledRefQueue<Item>.Create();

            foreach (var existing in Map.Felucca.GetItemsAt<BaseSpawner>(definition.Location))
            {
                if (existing != spawner && existing.GetType() == type)
                {
                    queue.Enqueue(existing);
                }
            }

            while (queue.Count > 0)
            {
                queue.Dequeue().Delete();
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

        return generated;
    }

    private static void GenerateSigns(IEnumerable<SignDefinition> definitions)
    {
        foreach (var definition in definitions)
        {
            SignParser.Add_Static(definition.ItemId, definition.Location, Map.Felucca, definition.Text);
        }
    }

    private static bool Audit(Mobile from, bool reportSuccess)
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

        var signsFound = inputs.Signs.Count(SignExists);
        if (signsFound != inputs.Signs.Count)
        {
            errors.Add($"signs {signsFound}/{inputs.Signs.Count}");
        }

        var teleportersFound = CountExpectedTeleporters(inputs.Teleporters);
        if (teleportersFound != inputs.TeleporterPlacementCount)
        {
            errors.Add($"teleporters {teleportersFound}/{inputs.TeleporterPlacementCount}");
        }

        var spawnersFound = inputs.Spawners.Count(SpawnerExists);
        if (spawnersFound != inputs.Spawners.Count)
        {
            errors.Add($"spawners {spawnersFound}/{inputs.Spawners.Count}");
        }

        var moongates = CountItems<PublicMoongate>(Map.Felucca);
        if (moongates != inputs.Manifest.ExpectedPublicMoongates)
        {
            errors.Add($"public moongates {moongates}/{inputs.Manifest.ExpectedPublicMoongates}");
        }

        var khaldunItems = CountItemsInBounds<MorphItem>(Map.Felucca, new Rectangle2D(5400, 1350, 150, 150));
        if (inputs.Manifest.GenerateKhaldunPuzzles && khaldunItems == 0)
        {
            errors.Add("Khaldun puzzle infrastructure is absent");
        }

        if (errors.Count > 0)
        {
            from.SendMessage($"Alpha 2b audit failed: {string.Join("; ", errors)}.");
            return false;
        }

        if (reportSuccess)
        {
            var (items, mobiles) = CountWorldObjects(Map.Felucca);
            from.SendMessage(
                $"Alpha 2b audit passed: {signsFound} signs, {teleportersFound} teleporters, " +
                $"{spawnersFound} spawners, {moongates} moongates; Felucca roots {items} items/{mobiles} non-player mobiles."
            );
        }

        return true;
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

            foreach (var fileName in manifest.SpawnerFiles)
            {
                var path = Alpha2bWorldGenerationConfiguration.ResolveGeneratedPath(
                    Path.Combine(manifest.SpawnersDirectory, fileName)
                );
                spawners.AddRange(JsonConfig.Deserialize<List<SpawnerDto>>(path, SpawnerJsonSerializer.Options));
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
            ValidateInputs(manifest, signs, canonicalTeleporters, canonicalSpawners);
            inputs = new GenerationInputs(manifest, decorationFiles, signs, canonicalTeleporters, canonicalSpawners);
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

    private static bool SignExists(SignDefinition definition)
    {
        foreach (var sign in Map.Felucca.GetItemsAt<Sign>(definition.Location))
        {
            if (sign.Z == definition.Location.Z && sign.ItemID == definition.ItemId)
            {
                return true;
            }
        }

        return false;
    }

    private static bool SpawnerExists(SpawnerDto definition)
    {
        foreach (var spawner in Map.Felucca.GetItemsAt<BaseSpawner>(definition.Location))
        {
            if (spawner.Guid == definition.Guid)
            {
                return true;
            }
        }

        return false;
    }

    private static int CountExpectedTeleporters(IEnumerable<TeleporterDefinition> definitions)
    {
        var count = 0;

        foreach (var definition in definitions)
        {
            if (TeleporterExists(definition.Source, definition.Destination))
            {
                count++;
            }

            if (definition.Back && TeleporterExists(definition.Destination, definition.Source))
            {
                count++;
            }
        }

        return count;
    }

    private static bool TeleporterExists(WorldLocation source, WorldLocation destination)
    {
        foreach (var teleporter in Map.Felucca.GetItemsAt<Teleporter>(source))
        {
            if (teleporter is not (KeywordTeleporter or SkillTeleporter) &&
                Math.Abs(teleporter.Z - source.Z) <= 12 && teleporter.PointDest == destination &&
                teleporter.MapDest == Map.Felucca)
            {
                return true;
            }
        }

        return false;
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

    private sealed record GenerationInputs(
        Alpha2bWorldGenerationManifest Manifest,
        string[] DecorationFiles,
        List<SignDefinition> Signs,
        List<TeleporterDefinition> Teleporters,
        List<SpawnerDto> Spawners
    )
    {
        public int TeleporterPlacementCount => Teleporters.Sum(teleporter => teleporter.Back ? 2 : 1);
    }
}
