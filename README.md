# Britannia Renaissance Shard Content

Custom server content, data, and original assets for Britannia Renaissance. This is a standalone
repository and intentionally sits beside `../ModernUO`; it does not contain a copy or fork of the
server engine.

## Layout

- `src/` — C# assemblies loaded by ModernUO.
- `data/` — shard-owned configuration, spawns, regions, and decoration source files.
- `assets/source/` — editable original art, audio, and other authoring files.
- `assets/processed/` — game-ready assets generated from the source assets.
- `docs/` — shard design notes and content conventions.
- `tools/` — repeatable build, import, validation, and deployment tooling.
- `tests/` — automated tests for custom content.

## ModernUO dependency

The default project path assumes this repository is checked out next to `ModernUO`:

```text
Britannia Renaissance/
├── ModernUO/
└── ShardContent/
```

Override `ModernUOPath` when your workspace uses a different layout:

```powershell
dotnet build .\src\BritanniaRenaissance.Content\BritanniaRenaissance.Content.csproj `
  -p:ModernUOPath=C:\path\to\ModernUO
```

ModernUO discovers content assemblies from `ModernUO/Distribution/Assemblies`. The content
project therefore emits its DLL there by default, without making this repository a child of the
ModernUO repository.

Do not commit server saves, accounts, installed UO client files, or generated build output here.
