# No pop-in at the edge of the game view (client)

Owner, 2026-11-04: "It annoys me that at the edge of the play window trees and other static map deco pop in and out. Instead, they should stay loaded so they only disappear once totally off screen."

## Cause

The client (`ClassicUO` `Game/Scenes/GameSceneDrawingSorting.cs`) decided whether to draw a piece of art from the screen position of its tile, with a margin of one tile (44 px) around the view. Nothing is unloaded: statics come from the client's own map files and stay in memory. But art is drawn upward from the bottom of its tile, so:
- **At the bottom edge**, a tree whose tile had moved 44 px below the view stopped being drawn while its crown (up to about 100 px more) was still on screen.
- **At the left edge**, wide art (centered on its tile, up to 180 px wide) stopped while its right part still showed.
- The top and right edges were already fine: art never reaches above-left of its tile's anchor in a way the 44 px margin misses.

## Change

Art is now culled by what it covers:
- A static, multi piece or item is dropped below the view only when the top of its art is below the bottom edge (`screenY - ArtRise(graphic) > _maxPixel.Y`, with `ArtRise` = the art's height less one tile, from the loaded texture). Three places: chunk-mesh statics, the non-mesh static and multi path (trees), and items (the shard's flavor objects are items).
- A tile is skipped at the left edge only once it is 112 px further out (`WIDE_ART_REACH`: half the widest art, 90 px, plus the 22 px from tile corner to centre).
- The tile range the scene walks grows by 26 tiles along +X and +Y (`TALLEST_ART_TILES`: the tallest static rises 547 px above its tile, at 22 px per tile) and by 6 along -X (`WIDE_ART_TILES`), so the extra art below and left of the view is visited at all.

The art sizes are measured from `UOData/artLegacyMUL.uop` (39,509 static art pieces): height median 74 px, 99th percentile 437, tallest 591; width 99th percentile 125, widest 180.

Not changed: creatures and people (animations, not art) still use the tile margin; land tiles, which do not rise.

## Installed (2026-11-04)

Owner, 2026-11-04: "Can you push it to my regular client so i cna test it?". The new `cuo.dll` and `cuo.pdb` (SHA-256 `A55BC2D0...1A9A`, NativeAOT publish) are in `ClassicUO/bin/dist`, used by the root launchers; the previous pair is in `work/cuo-backups/cuo-20261104-210718-before-edge-cull` (copy both back to undo). A test copy of the whole client is in `work/player-client/dist-edge-cull`. The ClassicUO change is uncommitted.

## Verification

Owner, after playing on it in the regular client: "it's so much better, commit and push this". Not recorded by an agent in the real client.
