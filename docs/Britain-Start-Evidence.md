# New characters start in Britain only (2026-10-13)

Owner rulings, 2026-10-13: asked what new characters should do about the nine starting towns when only Britain has shops, a bank, healers, trainers and guildmasters (`Moongates-Evidence.md`), the owner chose **"Offer only Britain"**, then added: "Make sure the client only lets players select Britain during character creation. Don't present them with other towns and give an error or something like that." Built, checked in the real client, **activated** (`featureFlags.startInBritainOnly` true) and deployed to the dev distribution; server stopped. Uncommitted.

## What changed

| Piece | What it does |
| --- | --- |
| ModernUO `CharacterCreation.StartingCitiesFilter` (new, `Engines/Character Creation/CharacterCreation.cs`) | An optional filter on the starting cities. `GetStartingCities()` returns the filtered list, and that one list is both sent to the client at login and indexed when the character is made, so what the client shows and what the server accepts cannot disagree. No filter, no change (3 tests, `CharacterCreationStartingCitiesTests`) |
| `BritainStartService` (new) | Installs the filter. With the flag on it reduces the list to Britain; a list with no Britain is left alone (a world that cannot start anyone is worse than one that offers too many towns) |
| `featureFlags.startInBritainOnly` | New flag, true in the shipped rules since this ruling |
| Guide text | With the flag on, the Welcome, Your first hour and Moongates pages say every new character starts in Britain and drop the advice for "if you began in another town" |

## What a player sees

- **The client's town page** shows one town: Britain, on the Felucca map, already selected, with the stock description ("The City of Bards"). There is nothing else to click. Real client, a brand-new account, shown to the owner.
- **The character starts in Britain**: server log `started.city=Britain, started.location=(1496, 1628, 10)` (Sweet Dreams Inn, inside the town), for a character made through Navrey and one made through the real client's creation screens.
- **The "error"**: the list the client gets has only Britain, so a player cannot ask for another town. A request for any other town number (only a modified client or a forged packet can send one) is refused by the server's own stock check (`cityIndex >= info.Length`): no character is created and the connection is closed. Tested live by forging city index 5 from the test client (new `city=N` option on Navrey's `createcharacter`): no character created, server log shows the connection dropped. The player is not shown a message, since only a forged request can reach it.

## Evidence

- Shard tests: 1396 passed (run `20261013T210225572Z-b07617`): `BritainStartTests` (4) and the guide tests; ModernUO `CharacterCreationStartingCitiesTests` 3 of 3 (run `20261013T205525257Z-c4cf21`).
- Real client: the character-creation screens of a new account (appearance, trade, Warrior, Mace Fighter, the town page), then in game the Welcome page.
- Deployed: ModernUO rebuilt into `Distribution` (`UOContent.dll`), shard deployed, rules show the flag, dev server boot-checked and stopped.

## Limits

- Existing characters are not moved; characters made before this may stand in another town, which is why the Moongates page stays.
- A character slot's starting town cannot be chosen at all now. If more towns later get shops (the owner's idea of towns as housing), switch the flag off or widen the filter.
- Navrey's `createcharacter` gained `city=N` (a test tool; Navrey is uncommitted).

## Files

ModernUO: `Projects/UOContent/Engines/Character Creation/CharacterCreation.cs`, `Projects/UOContent.Tests/Tests/Engines/CharacterCreationStartingCitiesTests.cs`. ShardContent: `src/BritanniaRenaissance.Content/BritainStartService.cs`, `ShardRulesConfiguration.cs`, `ShardBootstrap.cs`, `WelcomeGuide.cs`, `WelcomeGuide.GettingStarted.cs`, `data/configuration/shard-rules.json`, `tests/BritainStartTests.cs`, `tests/GuideGettingStartedTests.cs`. Navrey: `src/ClassicUO.Client/Agent/Commands/CommandEngine.Actions.cs`.
