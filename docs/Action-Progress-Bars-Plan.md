# Action progress bars: phased plan

Owner, 2026-11-02: "make a phased plan for all the actions that it makes sense to have bars", and "Include in the plan color themes for the bars. For example gathering could use one color, crafting another, healing or beneficial one color, and so on."

Built so far (flag `actionProgressBars`, OFF): **Chopping** (lumberjacking) and **Bandaging**. Evidence: `Action-Progress-Bars-Evidence.md`.

## What gets a bar

An action gets a bar when all of these hold:

1. **The player waits for it.** The result comes a second or more after the player starts it. Instant actions (a lore skill, hiding, snooping) get none.
2. **The server knows the length when it starts.** The bar shows the stock action's real length and never changes the action's rules. Where the stock code decides the length later, or the action has no end, there's no bar.
3. **It ends in a result the player sees:** a heal, logs, a tamed pet, a cast. A bar that ran out with nothing to show would read as a bug.
4. **Cut short means cleared.** Wherever the stock action can be cut short (moving off, being hit, a new action), the bar clears there too.

Only the player doing the action sees its bar (owner, 2026-11-02: "Only show your bars"). Bots don't read it.

## Colour themes

The bar's fill colour says what kind of action it is. The server sends a theme number as one more byte at the end of 0xB4. A client that predates it reads no theme byte and keeps today's amber, so the change is backward compatible both ways. The background stays dark and the text white with a black outline, so every fill must keep white text readable.

| # | Theme | Fill (RGB) | For |
| --- | --- | --- | --- |
| 1 | Gathering | amber 150, 104, 40 (today's colour) | chopping, mining, fishing, digging up treasure |
| 2 | Crafting | steel blue 55, 95, 150 | smithing, carpentry, tailoring, tinkering, bowcraft, alchemy, inscription, cartography, cooking, spinning, milling |
| 3 | Healing and help | green 45, 125, 60 | bandaging, resurrecting with a bandage, healing, curing and other helpful spells |
| 4 | Harmful | red 155, 40, 40 | harmful spells, poisoning a weapon or food |
| 5 | Magic | violet 110, 65, 150 | spells that are neither (recall, gate, mark, light, reveal, summons) |
| 6 | Animals | teal 35, 118, 112 | taming (a bandage on a pet is healing, theme 3) |
| 7 | Stealth and locks | slate 92, 92, 104 | picking a lock, begging |
| 8 | Camp and rest | rose 140, 50, 95 | making camp |

**Owner, 2026-11-02, on the mock: "Color pallete looks good".** The palette is settled.

A mock of all eight over real-client ground is in `work/progress-bars/theme-swatches-mock.png`. It is a drawing, not the client font. Each theme gets real-client shots when it is built.

**How the theme is chosen:** a spell's theme comes from the spell itself, so a heal is green and a harmful spell red. Everything else takes its theme from the action. The client keeps the colour table; the server sends only the number, so a colour can change in the client alone.

## Phases

All durations are the stock pre-AOS ones from the engine code (survey 2026-11-02; paths under `ModernUO/Projects/UOContent`). Every phase ends with unit tests, a live check on a disposable host, and real-client shots of each new bar, sent to the owner. Everything stays behind `actionProgressBars`.

### Phase 1: themes, the actions whose hooks already exist, and the gathered-item pop-up

| Action | Label | Theme | Length | Hook |
| --- | --- | --- | --- | --- |
| Colour themes | — | — | — | the theme byte in 0xB4, server and client; Chopping and Bandaging take their colours |
| Mining ore | Mining | 1 | 0.9 s (one swing, `Mining.cs:101`) | `HarvestSystem.AttemptTimed`, a label only |
| Mining sand | Digging sand | 1 | 8.9 s (six swings, `Mining.cs:240`) | same |
| Fishing | Fishing | 1 | 8.0 s (`Fishing.cs:88`) | same |
| Picking a lock | Picking lock | 7 | 3.0 s (`LockPick.cs:112`) | `Lockpick.AttemptStarted` / `AttemptEnded` |
| Cooking on a fire | Cooking | 2 | 5.0 s (`CookableFood.cs:10`) | `CookableFood.CookStarted` / `CookFinished` |
| Spinning | Spinning | 2 | 3.0 s (`SpinningwheelEastAddon.cs:84`) | `SpinningWheelEvents.SpinStarted` / `Spun` |

**What you gathered pops up** (owner, 2026-11-02: "For gathering, lets add a little floaty text with the icon of the item that was acquired and a count like "Logs +5" but with an icon"). When a gather succeeds, a small line floats up from your character and fades, like the heal numbers: the item's own picture in its colour, then the count, "+10". The picture takes the place of the word (owner, 2026-11-02: "Why does it say logs, its supposed to be an icon"). Coloured ore shows in its colour. Only you see it, and it comes with each gather of auto-repeat too.
- **Engine hook (new):** `HarvestSystem.ResourceGained(system, from, item)`, raised in `FinishHarvesting` just before `Give` (`HarvestSystem.cs:230`), and again for a bonus item. Before `Give`, because a gathered pile merges into the one already in your pack, and then its picture and amount are gone. A full pack ("You can't carry any more") pops up nothing.
- **Server to client:** extended command 0xB5 with your serial, the item's art number, its hue, the amount gained and a short name of at most 24 characters ("Logs", "Iron ore", "Fish"), which the client shows only for an item it has no picture for.
- **Client:** draws the item's art in a 30 px box with the count beside it in white with a black outline, on a faint dark plate so the picture reads against trees and rock. It starts just above the progress bar's place, so the next bar of auto-repeat never covers it, then rises 34 px over 1.6 s and fades. It has an Options switch, "Show what you gather over your head".
- **Later, if wanted:** the same pop-up for a crafted item ("Shield +1") or loot from a corpse. The command is general; only the server decides when to send it.

Mining ore is short at 0.9 s, but it repeats with harvest auto-repeat, and a bar that matches chopping reads as one system.

### Phase 2: crafting, taming and the short waits

| Action | Label | Theme | Length | Hook |
| --- | --- | --- | --- | --- |
| Crafting from any T2A menu (smithing, tailoring, carpentry, bowcraft, tinkering, alchemy, inscription, cartography) | Smithing, Tailoring, ... by the craft | 2 | 1.25 s, fixed in every craft system (`CraftItem.cs:1850`) | new event in both `CraftItem.Craft` paths |
| Flour mill | Milling | 2 | 5.0 s (`FlourMillEastAddon.cs:73`) | new event |
| Taming | Taming | 6 | 9 or 12 s (three or four 3 s steps, picked at the start, `AnimalTaming.cs:268`) | `AnimalTaming.AttemptStarted` gains the length; `AttemptEnded` clears the bar when it is cut short |
| Poisoning a weapon or food | Poisoning | 4 | 2.0 s (`Poisoning.cs:113`) | new event |

Crafting is short (1.25 s), but every item made shows it, and craft make-N repeat will show one bar per item.

### Phase 3: the long waits (built 2026-11-03, flag OFF; see the evidence doc)

| Action | Label | Theme | Length | Hook |
| --- | --- | --- | --- | --- |
| Making camp (within 7 tiles of your lit campfire) | Making camp | 8 | 30 s (`Campfire.cs:190`), up to 1 s later by the fire's poll | new event when the camp entry is made and when it is lost (moving off, the fire going out) |
| Digging up a treasure chest | Digging | 1 | about 25 s, until the chest reaches the ground (`TreasureMap.cs:685`) | new event; clears when the dig is cut short (moving, another action, something on the spot) |
| Begging | Begging | 7 | 2.0 s (`Begging.cs:90`) | new event |

Making camp is the bar that matters most here: a player waits 30 s with nothing on screen but one line of text at the start. Phase 3 also checks how the shard's own camp travel and camp logout timings sit with the stock 30 s, before building.

### Phase 4: spellcasting (dropped, owner 2026-11-03: "let's also skip spellcasting - no bars for it")

Not built: casting a spell has no bar. What was planned is kept below for the record.

| Action | Label | Theme | Length |
| --- | --- | --- | --- |
| Casting any spell | the spell's name ("Greater Heal") | 3, 4 or 5 by the spell | 0.5 s + 0.25 s per circle above the first (1st 0.5 s to 8th 2.25 s; `MagerySpell.cs:101`). Summon Creature and Blade Spirits 6.0 s. Scrolls the same, wands none |

- **Engine hooks (new):** `Spell.CastStarted(spell, delay)` where the cast timer starts (`Spell.cs:577`), and `Spell.CastDisturbed` in `Disturb()` (`Spell.cs:409`), which clears the bar. A spell is disturbed by damage (except 1st circle before AOS), equipping, death and disconnecting. Moving is blocked during a cast, not cancelled.
- **Theme by spell:** a table in `shard-rules.json` names the helpful spells (green: Heal, Cure, Greater Heal, Arch Cure, Protection, Bless and the stat spells, Reactive Armor, Magic Reflection, Resurrection, Night Sight, ...) and the harmful ones (red: every damage, curse, poison and paralyze spell, Dispel, Mana Drain, ...). Everything else is violet: Recall, Mark, Gate, Teleport, Light, summons, Reveal, ...
- The bar ends when the target cursor opens, which is when the stock cast "finishes".

## Not getting a bar

- **Instant actions:** carving and skinning, scissors and dyes, the loom, kindling, hiding, a stealth step, the lore and identify skills, Detect Hidden, Snooping, Stealing, Remove Trap, Tracking, the bard skills, Spirit Speak (before AOS), copying a book, decoding a map, placing a tinker trap, the teleport after Recall and Mark (their cast delay is in phase 4).
- **The explosion potion's fuse** (3.75 s): the stock potion already counts 3, 2, 1 over itself, and once thrown it is not over you, so a bar over your head would point at the wrong place.
- **Cooldowns are not actions:** the skill delay after Hiding, Stealth, Tracking, Begging, taming and the bard skills (1 to 30 s), the 10 s between heal potions, a weapon's swing time, the 0.75 s after a cast. Nothing happens at the end of a cooldown, so a bar would look like a wait for nothing. A cooldown display is a separate idea (see the questions).
- **Open-ended:** meditation (until mana is full or you act), hearing ghosts with Spirit Speak (15-180 s, better as a buff icon), the tracking arrow, a burning campfire.
- **Logging out:** stock logout waits happen after the player has gone, so there is no one to show a bar to.

## Open questions for the owner

1. **The spell bar's label: moot.** Owner, 2026-11-03: no bars for spellcasting.
2. **Who sees a bar: settled.** Owner, 2026-11-02: "Only show your bars". Nobody sees another player's or a creature's bar.
3. **Cooldowns: not yet.** Owner, 2026-11-02: "No cooldown display yet". Earlier wording of the question: A small separate display for the skill delay (for example "Hiding again in 8 s") is possible, but it is not part of this plan.
4. **Heal numbers and the stack: settled.** Owner, 2026-11-03: "let's leave the heal numbers as-is". The heal number still floats up from the head through any bars.
