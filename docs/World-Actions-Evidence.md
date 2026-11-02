# World actions: a left-click menu of what you can do (proof of concept: chopping a tree)

**Owner, 2026-11-01:** "every item that has an action that can be performed with it gives that action as a left click in a context menu ... If an action can not be performed, it is sorted to the bottom of the context menu options, and has a tooltip explaining why it can't be performed. For example, chopping would say "Requires an axe." as the tooltip. Implement this specific one as a proof of concept. I'll test it out myself."

Flag `worldActions`: **off** in the source config (not activated). For the owner's test it is set **on** in the farm host's own config only.

## What a player sees

- A left click on a tree still shows the tree's name. It also opens a small menu with **Chop wood**.
- If chopping can be done, the entry is white and choosing it chops.
- If it cannot, the entry is grey, sits below the actions that can be done, does nothing when clicked, and its tooltip says why. The reasons, in the order a player would fix them:
  - **Requires an axe.** No axe in the hands or the pack. A pickaxe mines and a war axe harvests nothing, so neither counts.
  - **Too far away. Stand next to the tree.** Further than the stock Lumberjacking reach of 2 tiles.
  - **There's not enough wood here to harvest.** The tree's wood is used up (stock wording, 500493).
- Choosing **Chop wood** with the axe in the pack puts it in the hands first, as a player would. Whatever is held goes into the pack, because an axe needs both hands and stock Lumberjacking refuses an axe that is not equipped ("The axe must be equipped for any serious wood chopping."). It then starts stock Lumberjacking on that tree: the skill check, yields, messages and the shard's gathering repeat all behave as when you double-click the axe and target the tree.

## How it works

A map tree is a static tile with no serial, so the stock server context menu (which needs a serial) cannot open on it. The menu is the client's own, filled in by the server:

| Step | Who | What |
| --- | --- | --- |
| Ask | client | Extended command 0xB1, mode 0: the clicked static's x, y, z and graphic. Sent only when the server's menu mask has bit 1 << 7 (`MenuBarService.Actions`, set when `worldActions` is on). |
| Answer | server | 0xB1: the tile's x, y and graphic, then each action: id, 1 if it can be done, its label and its reason (length byte plus UTF-8). The server checks the static really is at that place. A click on a tree's leaves finds the trunk on the same tile. |
| Menu | client | Actions that can be done first, then the greyed ones with their reason as the tooltip. Only the answer to the latest click opens a menu. |
| Do | client, then server | 0xB1 mode 1 with the action id. The server checks again and either says the reason or chops. |

Code:
- Server: `ShardContent/src/BritanniaRenaissance.Content/WorldActions.cs`, the mask bit in `MenuBarService.cs`, and the flag in `ShardRulesConfiguration.cs`.
- Client: `ClassicUO` `Game/Managers/WorldActions.cs`, `Send_WorldAction` in `OutgoingPackets.cs`, the 0xB1 case in `PacketHandlers.cs`, the ask on a static click in `GameSceneInputHandler.cs`, and `WorldActionsAllowed` in `TopBarGump.cs`.
- The client's context menu gained greyed entries with tooltips (`ContextMenuItemEntry.Disabled` / `Tooltip`, `ContextMenuControl.cs`), for this menu and any later one.

No engine (ModernUO) change: `HarvestSystem.StartHarvesting` with a `StaticTarget` is public.

## Verification

- Unit tests: `WorldActionsTests` (the reasons and their order, the reply bytes, the mask bit, the flag). Full shard suite, 1,784 pass (run `20261101T163457434Z-39c550`).
- Client: a Release NativeAOT build (`work/client-builds/world-actions-20261101`) is installed in `ClassicUO/bin/dist`. The old one is in `work/cuo-backups/dist-20261101-before-world-actions`.
- Live: on the farm host since 2026-11-01 12:17 (the BotFarm Watcher deployed it; the flag is on in the farm's own config only, and the old DLLs are in `work/hosts/farm/Assemblies-backup-20261101-121718`). The owner is testing it himself.

## Toward the full pass

The same channel extends to any static, by adding actions to `WorldActions` (for example: a bladed item on a tree for kindling, mining a rock face, fishing water, drinking from a trough). Items and creatures have serials. They could use the stock server context menu, which can grey an entry but has no tooltip, or this same client menu asked by serial.

## Wave 1: kindling, mining, fishing (built 2026-11-01, on the owner's "Yes to wave 1")

The owner's answers to the plan's questions (2026-11-01):
- Items in the backpack get their actions too (that is wave 3).
- An action never walks the player: too far is a reason.
- Wave 1 first.

| Clicked | Action | Greyed, with the reason |
| --- | --- | --- |
| Tree (trunk or leaves) | Chop wood; Cut kindling | "Requires an axe." / "Requires a knife, dagger or sword." / "Too far away. Stand next to the tree." / "There's not enough wood here to harvest." |
| Mountainside, cave floor (ground) or cave rock | Mine | "Requires a pickaxe or shovel." / "You can't mine while riding." / "Too far away. Stand next to where you want to dig." / "There is no metal here to mine." |
| Water (ground or static) | Fish | "Requires a fishing pole." / "You can't fish while riding." / "Too far away. Stand within 4 tiles of the water." / "The fish aren't biting here. Try water at least 8 tiles away." |

How each action runs, and the rules it follows:
- **Mine** and **Fish** start the stock harvest directly, with the tool from the pack or the hands. Neither tool has to be equipped.
- **Cut kindling** answers the stock bladed-item cursor in code. It takes 5 wood from the tree for one Kindling and needs no skill.
- **Sand** is left off the menu: it needs a Mining book.
- **Fished-out water:** a fishing spot is an 8x8 patch of water, chosen by the tile you cast at, so 8 tiles away is always a different patch. A player carrying an SOS within 60 tiles of its target is never told the water is fished out, because stock fishing ignores the empty patch for them.

Client:
- A left click on the ground now asks too (mountainside, cave floor and water are ground tiles).
- The menu opens only after the double-click time has passed, and a double click cancels it, so double-clicking the ground to walk there never opens a menu.

Verification: full shard suite, 1,800 pass (run `20261101T172854692Z-3a7f96`). Client build in `work/client-builds/world-actions-wave1-20261101`.

## Wave 2: workstations (built 2026-11-01, on the owner's "go ahead and do wave 2")

| Clicked | Action | Greyed, with the reason |
| --- | --- | --- |
| Forge | Smelt ore (the first pile your Mining can smelt) | "Requires ore." / "You need more Mining to smelt this ore." / "Too far away. Stand next to the forge." |
| Anvil | Smith (the stock smithing menu) | "Requires a smith's hammer or tongs." / "Too far away. Stand next to the anvil." / "You need a forge nearby as well." |
| Campfire, oven, fireplace, forge | One entry per kind of raw food carried: "Cook raw ribs (3)", "Bake a meat pie (1)", and so on | "Too far away. Stand next to the fire." Greyed "Cook" when you carry none: "Requires raw food." |
| Spinning wheel | "Spin wool (n)", "Spin cotton (n)", "Spin flax (n)" | "That spinning wheel is being used." / "Too far away. Stand next to the spinning wheel." Greyed "Spin" when you carry none: "Requires wool, cotton or flax." |
| Loom | Weave | "Requires yarn or thread." / "Too far away. Stand next to the loom." |

The rules are the stock ones:
- Coloured ore needs its Mining: dull copper 65 up to valorite 99 (`Ore.cs`).
- Reach: a forge or anvil within 2 tiles, a heat source within 1, a wheel or loom within 3.
- A forge is also a heat source, so it shows both Smelt and Cook.

How each action runs: it uses the material or tool as a double click would and answers its cursor with the workstation. Spinning calls the stock `SpinOn`.

**The item menu:**
- Britain's forges, anvils, oven, wheels and looms are items and addons with serials. Their actions go into the stock context menu that a left click already opens, through `ContextMenuSystem.ItemEntriesHandler`. They come before the About entry.
- Those menu entries carry client text 3050003 "Action" (`Clilocs.txt`). The server sends each entry's real label and its reason just before the menu, in command 0xB2 (the item's serial, then each entry's place, label and reason).
- The client's `PopupMenuGump` uses those labels, lists greyed entries below the rest, puts the reason in the greyed entry's tooltip, and ignores a click on a greyed entry.
- A workstation that is a map static (an oven or fireplace built into the map) uses the 0xB1 menu instead.

Verification: full shard suite, 1,823 pass (run `20261101T173921534Z-7bdb4c`). The client build `work/client-builds/world-actions-wave2-20261101` and the new `Clilocs.txt` are installed in `ClassicUO/bin/dist`.

### Real-client check of waves 1 and 2 (2026-11-01, farm host, test character PoisonT at Britain's smithy, 1422,1557)

| Shot (`work/player-client/PoisonT/shots/`) | Shows |
| --- | --- |
| `20261101-125308-anvil-menu.png` | Left click on the anvil: the stock item menu with the shard's label "Smith" (not the placeholder "Action"), greyed. |
| `20261101-125319-anvil-tooltip.png` | Hovering it: "Requires a smith's hammer or tongs." The hover highlight made the grey label hard to read, so greyed entries in the item menu are no longer lit on hover (client rebuilt as `world-actions-wave2b-20261101` and installed; that change has not been photographed). |
| `20261101-125351-forge-menu.png` | The small forge: "Smelt ore" and "Cook", both greyed (no ore, no raw food). |
| `20261101-125403-tree-menu.png` | A click on a cedar's needles (the leaves) opens the tree menu: "Chop wood" and "Cut kindling", both greyed. |
| `20261101-125413-tree-tooltip.png` | "Cut kindling": "Too far away. Stand next to the tree." The character carries a dagger, so the reason is the distance, as it should be. |

Not yet exercised live: an action that can be done, carried out from the menu (the owner is testing these himself).

## Wave 3: things you carry, and locks (built 2026-11-01, on the owner's "you can work on wave 3 now")

A left click on an item in the backpack (grid or classic container) already opens its stock context menu. The shard's entries go into that menu with their labels and reasons, as in wave 2, so the client needed no change.

| Item | Action | Greyed, with the reason |
| --- | --- | --- |
| Bandage | Heal yourself; Heal someone (opens the stock cursor) | Heal yourself: "You are not hurt." (neither hurt nor poisoned) |
| Heal potion | Drink | "You are already at full health." / "You are poisoned. Cure the poison first." / "You must wait 10 seconds before drinking another heal potion." / "You must have a free hand to drink a potion." |
| Cure potion | Drink | "You are not poisoned." / no free hand |
| Refresh potion | Drink | "You are already at full stamina." / no free hand |
| Other drinkable potions (strength, agility, night sight) | Drink | No free hand. Thrown potions (explosion) and poison potions get no Drink entry. |
| Food | the stock Eat entry | Greyed when full: "You are simply too full to eat any more!" |
| Kindling | "Feed the fire" with a campfire within 1 tile, else "Light a fire" | "You cannot light a fire in a dungeon." |
| Anything scissors cut (hides, cloth, clothing) | Cut with scissors | "Requires scissors." |
| Ore | Smelt ore | "You need more Mining to smelt this ore." / "Needs a forge within 2 tiles." |
| Raw food | Cook | "Needs a fire, oven or forge next to you." |
| Locked container or door (pack or world) | Unlock; Pick the lock (containers) | "Requires its key." / "Requires a lockpick." / "That lock can't be picked." / "This lock is beyond your Lockpicking skill." / "Too far away. Stand next to it." |
| Unlocked, with its key | Lock | Too far away |

Notes on how the actions run:
- The 10-second heal-potion wait is read with `CanBeginAction`. That only checks the wait: the stock drink check would start it.
- A key on a key ring counts.
- Each action runs the stock use: drinking and lighting are a double click; bandaging yourself is `Bandage.BandageTargetRequest`; scissors, smelting, cooking, keys and lockpicks answer their stock cursor with the item. Every stock rule and message still applies.

Verification: full shard suite, 1,842 pass (run `20261101T180043550Z-9691c4`).

### Real-client check of wave 3 (2026-11-01, farm host, PoisonT's grid backpack at Britain's smithy)

| Shot (`work/player-client/PoisonT/shots/`) | Shows |
| --- | --- |
| `20261101-131010-heal-potion-reason.png` | Left click on a Lesser Heal potion in the grid backpack: "About" on top, then "Drink" greyed with "You are already at full health." The greyed entry is no longer lit on hover, so its text stays readable. |
| `20261101-131024-kindling-menu.png` | Kindling: "Light a fire" available, then "About". |
| `20261101-131037-kindling-lit.png` | Choosing it lit a campfire beside the character: the Kindling went from 5 to 4 and the stock camping messages showed. This is the first action carried out from a menu. |
| `20261101-131051-kindling-feed.png` | With the fire within a tile, the Kindling's menu now says "Feed the fire". |

## Wave 3b: tools, gear, magic and travel, resources and other (built 2026-11-01, on the owner's choice of all four groups)

The owner asked whether many more items should be covered. Three read-only surveys of the stock rules came first: gear, magic and travel, and resources and other. Everything below follows the stock rule and message, and runs the stock use of the item.

**Tools** (`WorldActions.Tools.cs`):

| Item | Action | Greyed, with the reason |
| --- | --- | --- |
| Crafting tool | The craft menu, opened straight away (T2A menus). Labels: Smith, Tailor, Tinker, Carpentry, Make bows and arrows, Make potions, Inscribe, Make a map | "This tool is worn out." / "You must be near an anvil and a forge to smith." / "Requires ingots." (cloth or leather, logs, reagents and an empty bottle, blank scrolls, a blank map) |
| Hatchet or axe | Chop a tree: the axe goes in the hands first, then the stock cursor | |
| Pickaxe, shovel | Mine | Worn out / "You can't mine while riding." |
| Fishing pole | Fish | "You can't fish while riding." |
| Knife, sword | Carve or cut kindling (the stock bladed-item cursor) | |
| Scissors, lockpick, key, blank key, key ring | Cut something / Pick a lock / Lock or unlock / Copy a key onto this blank | |

The cooking tools (skillet, rolling pin, flour sifter) are left out: they have no craft menu in this era, so their use does nothing.

**Gear** (`WorldActions.Gear.cs`):

| Item | Action | Greyed, with the reason |
| --- | --- | --- |
| Weapon, shield, armour, clothing, jewellery in the pack | Wield / Wear | "You are not strong enough to wear that: it needs N Strength." (Dexterity and Intelligence the same way) / "Only females can wear this." |
| Worn | Take off | |
| Torch, candle, lantern, lamp | Light / Put out | "It has burnt out." |
| Instrument | Play; Peacemaking; Provocation | "You must wait a moment before playing again." / "You must wait a few moments to use another skill." |
| Dye tub, dyes, hair dye | Dye an item / Fill a dye tub / Dye your hair | "You have no hair to dye." |

How it runs:
- Wearing does what a player does by hand: whatever is in the way goes into the pack, and is put back if the stock equip still refuses. A two-handed weapon empties both hands; a one-handed one keeps a shield or light.
- A torch goes into the hand before it is lit, since stock lighting would drop it at your feet when the hand is full.
- Discordance is left off: it came after this era.

**Magic and travel** (`WorldActions.Magic.cs`):

| Item | Action | Greyed, with the reason |
| --- | --- | --- |
| Spell scroll | Cast <spell> (with the stock "Add to spellbook" entry) | "You are already casting a spell." / "You cannot cast a spell while frozen." / "Not enough mana: Recall needs 11." |
| Spellbook | Open | "Put the spellbook straight in your backpack (not in a bag) to open it." |
| Recall rune | Recall; Open a gate; Rename (when marked) | "That rune is not yet marked." / "Requires a Recall scroll, or the Recall spell in your spellbook." / "Requires black pearl, bloodmoss and mandrake root." / mana / "You are a criminal and cannot escape so easily." / "You cannot flee during the heat of battle." / "You are carrying too much to travel by magic." |
| Runebook | Open | "This book needs time to recharge." |
| Wand | Use the wand (it goes in the hand first) | "This wand is out of charges." / "The wand is recharging." |

How it runs:
- The spellbook is used when it has the spell and the reagents; otherwise a scroll. The cast is `new RecallSpell(player, entry, null, scroll)` or `GateTravelSpell`, so the Magery roll, the travel rules and the shard's travel warning all still apply.
- Reagents are counted without taking any.

**Resources and other** (`WorldActions.Misc.cs`):

| Item | Action | Greyed, with the reason |
| --- | --- | --- |
| Ingots / cloth and leather / logs / shafts and feathers / reagents and bottles | The craft menu of the tool they go with, with the material chosen (logs: Carpentry and Make bows and arrows) | "Requires a smith's hammer or tongs." (a sewing kit, a carpentry tool, fletching tools, a mortar and pestle) / the anvil and forge / "Requires reagents." / "Requires an empty bottle." |
| Blank scroll / blank map | Inscribe / Make a map (the skill, no tool needed in the T2A menus) | |
| Bedroll | Unroll / Roll up / "Roll up and log out safely" (in a secure camp) | "Put the bedroll on the ground first." |
| Message in a bottle / SOS / fishing net | Open the bottle / Read the message / Cast the net | |
| House deed / addon deed | Place the house / Place it | "You already own a house, you may not place another!" |
| Training dummy / pickpocket dip / archery butte | Practise / Practise stealing / Shoot at it (+ Gather the arrows) | "You can't practise ranged weapons on this." / "You must practise with a bow or crossbow on this." / "You can't practise on this while riding." / "Stand 5 or 6 tiles away, straight in front of it." / "Your skill cannot improve any further by practising on this." |
| Food | Feed your pet (all N), the whole stack as a drag and drop would | "You have no pet near you." / "None of your pets near you eats this." |
| Treasure map | The stock Decode and Dig entries, now with reasons | "You need N Cartography to decode this map." / "Requires a shovel or pickaxe in your pack." |

Verification:
- Full shard suite, 1,867 pass (run `20261101T183422623Z-a87bd8`).
- A test makes sure no two actions share an id.

### Real-client check of wave 3b (2026-11-01, farm host, PoisonT's grid backpack)

| Shot (`work/player-client/PoisonT/shots/`) | Shows |
| --- | --- |
| `20261101-134139-w3b-cell3.png` | Dagger in the pack: "Carve or cut kindling", "Wield", "About". |
| `20261101-134151-w3b-wield.png` | Wield: the dagger is in hand (combat bar "held"), and the spellbook that held that hand went into the pack, as when swapping by hand. |
| `20261101-134205-w3b-book.png` | Spellbook in the pack: "Open", "About". |
| `20261101-134218-w3b-book-open.png` | Open: the spellbook's index opens. |

Not yet exercised live: crafting tools, magic travel, gear requirements, training objects and the other groups (the owner is testing).

## Wave 4: creatures (built 2026-11-01, on the owner's "Do wave 4")

A left click on a creature or a player opens its menu (the stock menu, after the double-click delay). The shard adjusts the menu through a new engine hook, `ContextMenuSystem.MobileEntriesHandler` (ModernUO `Projects/UOContent/Context Menus/ContextMenuSystem.cs`). It is called after the mobile's own entries, like the item hook. The code is in `WorldActions.Creatures.cs`, and there is no client change: the client already reads command 0xB2 by serial.

| Clicked | Actions | Greyed, with the reason |
| --- | --- | --- |
| A tamable creature (the stock Tame entry) | Tame | "That animal looks tame already." / "That creature can only be tamed by males." (or females) / "You have too many followers to tame that creature." / the pet-restriction refusal / "This animal has had too many owners and is too upset for you to tame." / "You must subdue this creature before you can tame it." / "You need N Animal Taming to tame this." / "Too far away. Stand within 2 tiles." / "You must wait a few moments to use another skill." |
| A creature that can never be tamed, or someone else's pet (not people, vendors or summons) | Tame, always greyed | "That creature cannot be tamed." / "That animal looks tame already." |
| Your own pet | Ride (mounts), Feed (all N), Heal with a bandage | "You can't do that while polymorphed." / "You may not ride at this time." / "Please dismount first." / "Too far away to ride. Stand next to it." / "This mount is too ill to ride." / "You carry no food it eats." / "Too far away. Stand within 2 tiles." / "Requires bandages." / "It is not hurt." / "Too far away. Stand next to them." |
| Another player | Heal with a bandage | "Requires bandages." / "They are not hurt." / "As a young player, you may not heal older players." / "Too far away. Stand next to them." |
| Yourself | Heal yourself, Dismount (when riding) | "Requires bandages." / "You are not hurt." |

The rules behind it:
- **The reasons follow the stock checks, in order.** Taming follows `AnimalTaming.InternalTarget.OnTarget`; the skill comes before range, and the skill timer is last. Riding follows `BaseMount.OnDoubleClick`, and bandaging follows `Bandage` and `BandageContext.BeginHeal`.
- **Each action runs the stock use.** The stock Tame entry still does the taming; the others go through the mount's double-click, `CheckFeed`, `Bandage.BandageTargetRequest` and `BaseMount.Dismount`. So every stock message still comes.
- **Feeding never offers a container or gold.** A goat's diet includes bags, and `CheckFeed` eats the whole stack.
- **Pack animals were already covered.** They keep their stock "Open backpack" entry.

Verification:
- Full shard suite, 1,882 pass (run `20261101T195513366Z-9b101e`).
- The engine hook tests (`ContextMenuShardHookTests`), 6 pass (run `20261101T195457479Z-396617`).

**Fix found in the real client (2026-11-01):** the horse's menu first showed Tame twice. One was the stock entry, left enabled; the other was the shard's greyed "cannot be tamed". The engine stores a stock entry number below 0x8000 as 3000000 + n, so the shard has to look for 3006130, not the 6130 that `TameEntry` passes. The wave 3b treasure-map reasons (Decode 6147, Dig 6148) had the same mistake and never applied; they now look for 3006147 and 3006148. A test pins the number (`TheStockTameEntryIsFoundByTheNumberTheEngineStores`). Full shard suite after the fix: 1,883 pass (run `20261101T195957248Z-9fe113`).

### Real-client check of wave 4 (2026-11-01, farm host, PoisonT at Britain's smithy; a horse added by staff and held in place)

| Shot (`work/player-client/PoisonT/shots/`) | Shows |
| --- | --- |
| `20261101-145924-w4-tame-menu.png` | Before the fix: Tame shown twice (see the fix above). |
| `20261101-150207-w4-tame-reason.png` | After the fix, Animal Taming 8.9: one greyed Tame, with "You need 29.1 Animal Taming to tame this." |
| `20261101-150220-w4-tame-ok.png` | Animal Taming set to 100 by staff: Tame enabled. |
| `20261101-150245-w4-tamed.png` | Tame clicked: the stock taming ran and the horse was tamed (stock speech and the shard's new-pet tip). |
| `20261101-150254-w4-pet-menu.png` | Own pet: the stock commands, then Ride, with Feed and Heal with a bandage greyed at the bottom. |
| `20261101-150305-w4-feed-reason.png` / `150309-w4-heal-reason.png` | "You carry no food it eats." / "Requires bandages." |
| `20261101-150331-w4-ride-self-menu.png` | Ride clicked: PoisonT is mounted. |
| `20261101-150344-w4-self-menu.png` | Own menu while riding: Dismount, with Heal yourself greyed. |
| `20261101-150355-w4-dismounted.png` | Dismount clicked: on foot, the horse beside. |

Cleanup:
- The horse was deleted.
- PoisonT's Animal Taming was set back to 8.9 base.

Not yet exercised live: Feed and Heal with real food and bandages, bandaging another player, and an untamable creature's greyed Tame.

## Pet friend entries explained

The owner asked why a horse offers "Add Friend". It is the stock pet command, the menu form of "<name> friend". A first try renamed the two entries in the client text; the owner said to revert that and give them a tooltip instead.

The stock labels stay. On your own pet's menu, the server now sends a tooltip for each entry with command 0xB2:
- Add Friend (3006110): "Choose another player who may also tell it to follow, stop and stay, and feed it. It stays yours." For a pack horse or pack llama, "and open its pack" is added.
- Remove Friend (3006099): "Choose one of its friends to take that back."

These are what a pet friend may do in the stock code: the friend orders (`BaseAI.IsFriendOrder`), feeding (`BaseCreature.CheckFeed`) and a pack animal's pack (`PackAnimal.CheckAccess`). Only the owner rides, releases or transfers the pet.

Before this, the client fork put a 0xB2 tooltip only on a greyed entry. It now puts one on any entry that has one (`PopupMenuGump.cs`). The test is `ThePetFriendEntriesSayWhatAFriendMayDo`.

Real-client check on the farm (shard DLL md5 55A48D0DCA7789FD33F20E5C28ECE61A, client cuo.dll md5 29F3875E51726F2C669CF8EC7D4992A5): `20261101-165526-friend-tip-menu.png` shows the stock labels back. `165535-friend-tip-add.png` and `165547-friend-tip-remove.png` show the two tooltips on hover. The test horse was deleted.

## Wave 5: everyday things (built 2026-11-01, on the owner's list)

The owner chose eight items from the gap survey: "fill for containers that hold liquid, chop for pole arms, wool/cotton/flax/yarn, moongates, docked boat (launch), bank check, shepherd's crook, cow (milk)". The code is in `WorldActions.Everyday.cs`. Each action runs the stock use, and the menu only says in advance what that use would refuse.

| Item | Menu | Greyed with |
| --- | --- | --- |
| An empty pitcher, mug, goblet or other fillable vessel in the pack | "Fill with water" when a trough, tub, barrel or bucket with water is within 2 tiles and in sight. "Fill with milk" when a cow that can be milked is that close. Either one fills the vessel at once (`BaseBeverage.Fill_OnTarget`). | "Fill": "Stand next to a trough, tub, barrel or bucket of water, or a cow." |
| A halberd, bardiche or other pole arm | "Chop a tree", the same as an axe: it goes into the hands first. A tree's own Chop wood now counts a pole arm as an axe (`FindAxe`, `IsChopper`). | The tree's existing reasons. "Requires an axe." keeps the owner's wording. |
| Wool, cotton or flax in the pack | "Spin on the wheel", with a free wheel picked first. | "Needs a spinning wheel within 3 tiles." / "That spinning wheel is being used." |
| Yarn or thread in the pack | "Weave on the loom". | "Needs a loom within 3 tiles." |
| A public moongate | "Travel", which opens the stock list of destinations. | In the stock order: "Criminals cannot use the moongate.", "You cannot use the moongate during a fight.", "You are too busy casting to use the moongate.", "Too far away. Stand next to the gate." |
| A Gate Travel gate | "Enter the gate", which goes through the stock confirmation. | "This moongate does not seem to go anywhere.", casting, too far. |
| A docked boat in the pack | "Launch the boat", which shows the stock placing cursor. | |
| A bank check | "Cash it (N gold)". | "Put it in your bank box first." Without account gold, a check is cashed from the bank box. With account gold, the reason is "Put it in your backpack first." |
| A shepherd's crook, carried or held | "Herd an animal", which shows the stock herding cursors. | |
| A cow (its own menu) | "Milk", which fills the first empty vessel in the pack. | In order: "Requires an empty pitcher, mug or goblet.", "This is someone else's cow.", "This cow has no milk left. Try again in a day.", "Too far away. Stand within 2 tiles." |

Notes:
- Milking a cow came with Mondain's Legacy (cliloc 1080xxx). Stock ModernUO offers it in every era, and the owner asked for it.
- The stock `Cow.TryMilk` does not stop when the cow is out of reach. The menu's reach check stands in for that.
- A boat deed was not on the owner's list, so it has no Place entry yet.

Tests: `APublicMoongateSaysWhyItCannotBeUsed`, `MilkingACowSaysWhyItCannotBeDone` and `ACowHasMilkAgainADayAfterItRanDry`. The WorldActions filter passes 122/122 (run `20261101T233225292Z-108ce7`).

### Real-client check of wave 5 (2026-11-01, farm host, PoisonT at Britain's smithy, z 30)

Run on the farm's shard DLL md5 4B4066534EEC645FF1C2BE0FC6E3CF87. Staff placed a water trough, a spinning wheel, a loom, a public moongate and a cow beside PoisonT, and put the hand items in the pack.

The first staging used `[go x y 0` and landed everything below this courtyard, whose floor is z 30. Fill then stayed greyed, because PoisonT had no line of sight to it. That was a staging mistake, not a bug: the props were deleted and placed again with `[go x y`. The scripts are `work/world-actions-w5/stage.py` and `restage.py`.

| Shot (`work/player-client/PoisonT/shots/`) | Shows |
| --- | --- |
| `20261101-191847-w5-wool.png` | Wool: "Spin on the wheel". Clicked, it spun into yarn ("You put the balls of yarn in your backpack"). |
| `20261101-191857-w5-crook.png` | Shepherd's crook: Wield, Herd an animal. |
| `20261101-192122-w5-fill-entry.png` | Before the fix to the staging: Fill greyed with "Stand next to a trough, tub, barrel or bucket of water, or a cow." |
| `20261101-192420-w5-fill-menu.png` | Empty pitcher near the trough and cow: Fill with water, Fill with milk. |
| `20261101-192432-w5-filled.png` | Fill with water clicked: "You fill the container with water", and the item is now a pitcher of water. |
| `20261101-192455-w5-milk-reason.png` | Cow with no empty vessel carried: Tame, and Milk greyed with "Requires an empty pitcher, mug or goblet." |
| `20261101-192520-w5-milked.png` | An empty mug added, then Milk clicked: "You fill the container with milk", and the mug is now a ceramic mug of milk. |
| `20261101-192535-w5-gate.png` | Public moongate next to PoisonT: Travel. Not clicked. |
| `20261101-192540-w5-halberd2.png` | Halberd: Chop a tree, then Wield. |
| `20261101-192556-w5-check-reason.png` | Bank check in the backpack: "Cash it (1,000 gold)" greyed with "Put it in your bank box first." |

Cleanup: the trough, wheel, loom, moongate and cow were deleted with `[Area delete where <type>`, one object each.

Not exercised live:
- Weave on the loom from yarn.
- Moongate Travel clicked, and a Gate Travel gate.
- Launch a docked boat. One can't be added directly; it only comes from dry-docking a boat.
- Cashing a check in the bank box.
- Herding through to an animal.
