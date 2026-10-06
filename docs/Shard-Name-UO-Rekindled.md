# The shard is called UO Rekindled

**Decision (owner, 2026-10-06):** the shard's name is **UO Rekindled**. It was *Britannia Renaissance* until then. The roadmap had the rename in Beta 3 ("Identity gate"); the owner asked for it now, so the player-facing part is done and the rest of Beta 3's rename item is what is listed under "Still open" below. The tagline is unchanged: "Felucca, without the griefing".

## What players see now
- **The server list.** The name the client shows for the shard comes from the server's own setting. In `ModernUO/Distribution/Configuration/modernuo.json` (an untracked runtime file, so a fresh distribution must set it):

  ```json
  "serverListing.serverName": "UO Rekindled",
  ```

  Disposable test hosts copy that file, so they show the new name too. The client remembers the name it last saw (`last_server_name` in its settings); that updates on the next login.
- **The `[Welcome` guide:** its title, its first line ("Welcome to UO Rekindled: Felucca, without the griefing."), the one-line note a new character gets, and the intro sentence.
- **The player documents:** the root `README.md` (title, with a note about the old name) and `PLAYER_GUIDE.md`.
- **The website:** the page title, description, the brand mark (UO / Rekindled), the lead paragraph and the footer. The hero headline and the "Return to Britannia" button talk about the world, Britannia, and stay.
- **For the owner's own use:** the `Start Server.cmd` console title, the staff command description of `[ShardRulesStatus`, and the `Set-RemoteAccountRegistration.ps1` description.

## Where the name lives in code
`ShardBranding.Name` and `ShardBranding.Tagline` (`ShardContent/src/BritanniaRenaissance.Content/ShardBranding.cs`). Player-facing strings use them, and `ShardBrandingTests` fails if any source file still contains the old name with a space in it, so a missed rename shows up in the test run.

## What was deliberately not renamed
These keep the old spelling because renaming them would orphan saved data, break tooling or serve nobody:
- **Identifiers:** the shard assembly and namespace `BritanniaRenaissance.Content`, the project and file names, and the account tag keys such as `BritanniaRenaissance.Mastery.<serial>` (renaming a key would lose every player's saved state).
- **Client data files:** `BritanniaRenaissance.Prof.txt` and `Distribution/Data/BritanniaRenaissance/`. The first line of `Prof.txt` is a comment that still names the old shard; it is not displayed, and editing it would make the source, deployed, client and Navrey copies differ until a redeploy.
- **Folders and repositories:** the workspace folder `Britannia Renaissance`, the GitHub repositories, and the paths in tools and skills.
- **The Windows Firewall rule names** ("Britannia Renaissance UO Server"): `Set-RemoteAccountRegistration.ps1` removes a rule by its name, so renaming it would leave an existing rule behind.
- **Agent-facing documents and skills** (`CLAUDE.md`, `.claude/skills`, evidence and audit documents under `docs`): they record what was true when they were written. `CLAUDE.md` carries a note that the player-facing name is UO Rekindled.
- **"Renaissance" as an era.** The shard still plays the Renaissance rules (April 2000); that sentence in the README is about the era, not the shard.

## Still open (owner decides)
- **Client branding and art.** The ClassicUO window title and its credit lines say ClassicUO, and the login art is the client's. Changing them means a client build and publish (see `CLAUDE.md`, "Player client dist"); the owner has said the client may be modified.
- **Website art and logo.** The campfire mark is unchanged and the hero image file names still say "britannia".
- **Renaming folders, repositories, namespaces and tag keys.** Only worth doing with a data migration and a tooling pass; ask first.

## Checked
Unit: `ShardBrandingTests` and the Welcome guide tests. In the real ClassicUO client: the `[Welcome` guide shows the new title and first line, and the client's own record of the shard name changed after login (screenshots in the report of 2026-10-06).
