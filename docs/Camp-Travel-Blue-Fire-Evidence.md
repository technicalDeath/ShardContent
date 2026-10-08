# Camp travel: the blue fire (evidence and readiness)

Status: **built and verified 2026-10-08; ACTIVATED, committed, pushed and deployed 2026-10-08** on the owner's "2796 frostbite. Activate, commit, push, deploy". The plan and the owner's sign-off are in `Camp-Travel-Blue-Fire-Proposal.md` (all seven recommendations approved on 2026-10-08). The flag **`campTravelBlueFire` is on** and the flame is client hue **2796 (Frostbite)**, the owner's pick from the sheet (section 5).

## 1. What was built

| Where | Change |
| --- | --- |
| `ShardRulesConfiguration.cs` | Flag `campTravelBlueFire` (on since 2026-10-08; requires `campingTravel`), and `campTravel.fireHue` (a client hue, 1 to 3000, shipped 2796) |
| `CampTravelService.BlueFire.cs` (new) | The rule `Classify`, the claim kept per lighter, the once-a-second pass that gives every fire its class (oldest first), the hue and the single-click name, and the change notices |
| `CampTravelService.cs` | The service is `partial`; the camp list shows only travel fires (so one camp for each lighter); the refusal `NotTravelFire`; the notices now depend on what the fire is; the guide page has the blue wording; `[CampStatus` says "blue travel fire" or "ordinary" |
| `WelcomeGuide.cs` | The Camp travel page gets the blue wording when the flag is on |
| `shard-rules.json` | `campTravelBlueFire: false`, `campTravel.fireHue: 1265` |
| Test tooling | `TestOnlyProbe` verbs `[TestOnlyFires` (a grid of fires in candidate hues, `flat` finds open ground); `CampTravelProbe` verb `age` and fire hue, name and class in its report; `camp_travel_blue_fire_live.py`, `blue_fire_realclient.py` |

No ModernUO change: the hue and the name are public `Item` properties, set from the camp-travel poll that already ran every second.

## 2. The rules as built

- A fire a player lights becomes their **travel fire** (blue, named "<name>'s travel campfire", on the list) when the lighter's Camping can take at least one traveler (50 with the shipped numbers) and they hold no travel fire. Otherwise it is an **ordinary** campfire, unchanged from stock.
- **First lit keeps it.** The claim holds while the fire burns or dims, and is released when it is embers or gone, or when the lighter's Camping falls below 50. The next fire the lighter has burning (oldest first) then takes it; a fire relit from embers while another holds the claim is ordinary.
- Arrivals are still counted over each fire's own whole life, so one travel fire at a time is what stops a lighter's places being multiplied. A full blue fire stays blue until it burns out.
- `[CampTravel` lists only travel fires of party members, so at most one entry per party member. Travelling to an ordinary fire is refused ("That is an ordinary campfire. Only a blue travel fire can be travelled to."), after the embers and not-in-party refusals.
- A fire can show orange for up to a second after it is lit, until the first pass.
- With the flag off none of this runs and the behaviour is the shipped one.

## 3. Verification

**Unit tests** (`CampTravelBlueFireTests`, plus the existing camp-travel, guide and configuration tests): the class table (capacity, embers, who holds the claim), the first fire keeping the claim, embers releasing it, the refusal and its order, every notice for every class, the stock notices word for word with the flag off, the change notices, the guide page with and without the flag, the shipped file (flag off, hue in range), the validator (needs `campingTravel`; a hue outside 1 to 3000 is refused). Full suites on the final tree (run `20261008T140128995Z-408e4c`): Shard 1025 passed (993 before, 32 new), UOContent 1369 passed with 2 skipped, 0 failed.

**Live, disposable host, Navrey (three players in a party, `camp_travel_blue_fire_live.py blue`): ALL PASS, run 2026-10-08.**

| Case | Result |
| --- | --- |
| B1 | Flag off: one lighter's two fires are both travel fires, unhued and unnamed, and the lighter appears twice in the camp list (the old rule) |
| B2 | Flag switched on with two fires already burning: the older is blue (hue, name "CtLight's travel campfire"), the newer is ordinary; the list shows one camp |
| B3 | Travelling to the blue fire works, and the arrival is counted on that fire only |
| B4 | The blue fire aged to embers: it loses hue and name, the other burning fire takes the claim and burns blue; the lighter is told both ("Your travel fire is down to embers..." and "Your campfire burns blue.") |
| B5 | The embers fed back to life while the other fire holds the claim come back ordinary, with no blue notice |
| B6 | Camping 45: no fire is blue, and the lighter is told why; Camping 65: the oldest burning fire is blue again, and the lighter is told |
| B7 | A second lighter has a blue fire of their own (named for them), the first is unaffected, and the list shows one camp for each |
| B8 | The real path, lighting with Kindling: the first fire burns blue, with the notice and "You can have one travel fire at a time."; a second fire lit elsewhere is ordinary, with "This is an ordinary campfire. Your travel fire is still burning near ..." |
| B9 | Fires put out: the lighter is told "The next fire you light will burn blue.", and the next fire does |
| B10 | Camping 45: the fire is ordinary, the lighter is told what it takes, and the list says no camp is burning |

**Regression, flag off, `camp_travel_live.py camp`** (the original travel, refusals, capacity, cooldown and notices): ALL PASS, 98 checks (run 2026-10-08, flag off, the shipped build). The flag-off behaviour is the shipped behaviour.

**Real client** (`blue_fire_realclient.py lighter|traveler`, two real ClassicUO clients on the disposable host; six pictures sent to the owner, which look right):

| Picture | What it shows |
| --- | --- |
| 1 | The first fire lit with Kindling burns blue, and the lighter reads "Your campfire burns blue. Once it has burned for 8 seconds, party members can travel to it with [CampTravel (your Camping skill gives 6 places). You can have one travel fire at a time." |
| 2 | A second fire lit elsewhere is orange, and the lighter reads "This is an ordinary campfire. Your travel fire is still burning near <place>." (the place is the town, a Hot Zone name or sextant coordinates, as in the camp list) |
| 3 | Both fires at night (light level 12): the blue flame reads as blue-green in the dark, the orange fire is brighter |
| 4 | Single click on the blue fire: "CtLight's travel campfire" |
| 5 | The camp list with two lighters, one of whom has two fires burning: one camp for each |
| 6 | The guide's Camp travel page with the blue wording |

Two things the pictures showed while being taken, neither a defect in the feature: a character left dead by an earlier scenario sees a grey world with no fires (the script now resurrects first), and the shipped numbers are not the test numbers (secure after 8 seconds and the 120-second fire are the test host's).

## 4. Player text for review

New or changed, with the flag on (each sentence is built from the numbers in force):

- Lit and claimed: "Your campfire burns blue. Once it has burned for 30 seconds, party members can travel to it with [CampTravel (your Camping skill gives N places). You can have one travel fire at a time."
- Lit, but a travel fire is burning: "This is an ordinary campfire. Your travel fire is still burning near <place>."
- Lit under Camping 50: the shipped sentence ("Your campfire is lit. Party members can travel to your camps with [CampTravel once your Camping skill is 50 or higher.").
- Blue gained later (Camping rose, or the claim passed): "Your campfire burns blue. Party members can travel to it with [CampTravel. You can have one travel fire at a time."
- Blue lost to a drop in Camping: "Your campfire no longer burns blue: party members can travel to a fire only when its lighter has Camping 50 or more."
- Travel fire in embers: "Your travel fire is down to embers. Feed it with Kindling to relight it, or the next fire you light will burn blue." (An ordinary fire's embers: the shipped "Use Kindling beside it to relight it.")
- A travel fire burned out: "Your campfire has burned out. ... The next fire you light will burn blue."
- Single click on a travel fire: "<name>'s travel campfire".
- Refusal: "That is an ordinary campfire. Only a blue travel fire can be travelled to."
- Guide, Camp travel page, first paragraph: "Use [CampTravel to travel to a campfire that burns blue, lit by a member of your party. A fire burns blue when its lighter has Camping 50 or more, and each player can have one blue fire at a time: the first fire they light keeps it until it burns down to embers. A blue fire is secure once it has burned for 30 seconds and is not down to embers."

**README at activation** (the deployed README describes the deployed behaviour, so this waits for the flag): in the Camp travel line, replace "lists the secure campfires lit by members of your party" with "lists the blue campfires lit by members of your party (a fire burns blue when its lighter has Camping 50 or more, and each player can have one blue fire at a time: the first fire they light keeps it until it burns down to embers)".

## 5. The colour

The spike (2026-10-08, real client) showed the hue recolours the flames, but **a hued flame is dimmer than the stock fire at night** and shifts in colour; the glow it throws stays warm. Sixteen candidates, by day and at real night (light level 12), are in `work/blue-fire/shots/sheet-closeup.png`. **The owner chose 2796 (Frostbite):** an icy light blue by day, which reads as a pale green-yellow at night (it was recommended-against only in that respect; 1265 sky blue and 1266 cyan were the steadier-at-night alternatives). It is one number in `campTravel.fireHue`, so changing it is a config edit and a restart.

## 6. Named limits

- Only the flames can be blue; the light the fire throws is the client's one warm light.
- A fire may show orange for up to one second after it is lit.
- A wrongly placed travel fire cannot be moved or put out by its lighter (deferred, owner-approved): it lasts at most a few minutes without feeding.
- A full blue fire stays blue until it burns out; the lighter's next blue fire has to wait for that.

## 7. Shipping

Activated on the owner's explicit "activate" (2026-10-08): `campTravelBlueFire` is `true` and `fireHue` 2796 in `shard-rules.json`, the README Camp travel line says blue fires, and the guide page carries the blue wording. Deployed with `Deploy-Alpha1Baseline.ps1` (no ModernUO change, no client change, no save-format change, no snapshot needed).
