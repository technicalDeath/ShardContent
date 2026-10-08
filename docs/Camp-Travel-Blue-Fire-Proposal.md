# Camp travel: the blue fire (design proposal)

Status: **signed off by the owner on 2026-10-08 ("I agree with your proposal and recommendations"): all seven recommendations in section 8 stand (first fire keeps the blue; a full blue fire stays blue; no put-out or move action; ordinary fires hidden from the list; blue visible to everyone; a new flag, off at deploy; the colour chosen by the owner after the spike). Built and verified the same day (evidence: `Camp-Travel-Blue-Fire-Evidence.md`); activated on 2026-10-08 with the owner's chosen hue 2796 (Frostbite).** Origin: the owner's question "how does camp travel work if a player lights more than one fire?" and the idea that **a fire with travel enabled should burn blue, and a player can have only one blue fire at a time.**

## 1. How it works today with more than one fire

Read from `CampTravelService.cs`, `CampingService.cs` and the stock `Kindling.cs`/`Campfire.cs`.

- **Lighting.** Using Kindling lights a new fire on a tile next to you, unless a fire is already within one tile of you, in which case the Kindling feeds that fire instead (anyone's). Nothing limits how many fires a player has: each costs 1 Kindling and a Camping roll (chance = your Camping, at least 50%, as a percentage), so a player with five Kindling can have up to five fires, standing two or more tiles apart.
- **Every fire is its own travel camp.** A fire remembers its lighter, and a separate count of **arrivals**. A fire takes as many travelers as its lighter's Camping allows, **counted over that one fire's whole life**: 1 place at Camping 50, one more for each 10 points, 6 at 100, none below 50.
- **So fires multiply capacity.** A lighter with Camping 100 and three fires has three camps of six places: 18 arrivals. The only cost is 1 Kindling a fire.
- **The list.** `[CampTravel` lists every burning fire lit by a *party member* (not your own) on your map, nearest first, **at most 8 entries**. One lighter with three fires appears three times ("Rowan's camp: ready" x3) and can crowd the list.
- **Per traveler, not per fire.** The traveler pays 2 Kindling and has a 30-minute cooldown on their account, whichever fire they use.
- **Looks.** Every fire looks the same (orange), whether or not anyone can travel to it. A fire lit by someone under Camping 50 looks like any other, and only the list says "needs more Camping".
- **Life.** A fire burns `100 s + 2 s x Camping` (200 s at 50, 300 s at 100, the last third dim), then glows as embers for `60 s + 1.2 s x Camping` (120 s at 50, 180 s at 100). Feeding resets it, and embers can be relit. Fires are never saved.

The design contract did not discuss several fires; this is how it fell out.

## 2. The proposal

**A travel fire is a campfire that party members can travel to. It burns blue, and each player can have only one at a time.** Every other fire is an ordinary campfire: same stock behavior as today (secure camp, Bedroll, feeding), orange, not on the travel list.

### Rules

| # | Rule | Today |
| --- | --- | --- |
| 1 | A fire a player lights becomes their **travel fire** (blue) if travel is on, the lighter's Camping is **50 or more** (it can take at least one traveler), and they do not already have a burning travel fire. | Every fire is a travel camp if the lighter has Camping 50. |
| 2 | **First lit keeps it.** While a player's travel fire is burning, any other fire they light is ordinary (orange). They are told so. | No limit. |
| 3 | The travel fire **keeps its claim while burning or dimming**. When it goes to embers or is gone, the claim is free, and the next fire they light (or a relit ember fire, if the claim is still free) can be blue. | n/a |
| 4 | A fire lit under Camping 50 is ordinary, and the lighter is told why ("Camping 50 or more lets party members travel to your fire"). If their skill reaches 50 while it burns, it turns blue (if the claim is free). | Looks the same; refused at travel time. |
| 5 | **Arrivals stay counted per fire for its whole life**, as built. With one travel fire at a time, a lighter's capacity is one fire's: 6 at most. A full fire stays blue until it burns out (the list says "full"); letting it die and lighting again is the reset. | Lighting more fires resets it. |
| 6 | `[CampTravel` lists **only travel fires** of party members, so **at most one entry per party member**. Travelling to an ordinary fire (for instance, one picked from an old list) is refused with "That is an ordinary campfire; only a blue fire can be travelled to." | All fires. |
| 7 | Everyone sees a blue fire, in or out of the party. Blue is in Hot Zones too (the list keeps its [HOT ZONE] tag). Feeding by anyone keeps the fire and its colour. | n/a |
| 8 | Colour is **not the only signal** (the style guide's rule): single-clicking a travel fire reads "Rowan's travel campfire" instead of "campfire". | "campfire" |

### What the lighter hears (draft text for review)

- Lit and claimed: "Your campfire burns blue. Party members can travel to it with [CampTravel. You can have one travel fire at a time."
- Lit while one is burning: "This is an ordinary campfire. Your travel fire is still burning near <place>."
- Under Camping 50: "This is an ordinary campfire. Party members can travel to a fire only when its lighter has Camping 50 or more."
- Claim freed (embers or gone): the existing "burning low / embers / out" notices, plus "Your next campfire will burn blue." once.

The guide's Camp travel page gets the matching sentence ("A fire that party members can travel to burns blue; you can have one at a time"), and the README camp travel line too.

## 3. Design check

**Vision.** Camp travel is a small convenience that already ties travelers to a party and a place. This keeps that, and tightens it: one camp per person makes "go to Rowan's camp" a single known place, which concentrates the party instead of scattering it over several fires. Blue fires are visible to everyone, so a blue fire in a Hot Zone or on a road is an emergent encounter (a PK can see where a party is gathering, and arrivals land within two tiles of it). That is the classic sandbox, not griefing, and the Hot Zone warning already covers going in.

**Seven constraints.** (1) No power creep: it removes a way to stack capacity. (2) Thieves and encounters kept; blue is a visible beacon. (3) It draws a party to one spot. (4) Camping, party play and travel stay linked, with no new gate. (5) Works for a lone lighter and one party member. (6) No role gated behind another: anyone with Camping 50 and Kindling lights a blue fire. (7) Party members make a lighter's fire useful, as now.

**Stock first.** Stock lets anyone light any number of fires, and stock has no camp travel; the limit is shard-owned, applied only to the *travel* property, so stock Kindling, feeding and secure-camp behavior are untouched.

## 4. What is not decided by the code: the colour

- The campfire sprite (the burning and dimming art) can take a **hue**; the **light** it throws cannot change colour (the client has one warm light), so only the flames turn blue, not the glow around them.
- The embers art is left unhued.
- **Spike before building (no code, about ten minutes):** on a disposable host, hue a fire with the staff commands in a real client, photograph about a dozen blues on a real fire by day and by night, and you pick one. If the client ignores the hue on the animated art, the fallback is a different fire graphic (for example the large "fire pit" art) for travel fires, and I would come back with that before building.

## 5. Work breakdown (ShardContent only; no ModernUO change)

1. **Claim table and rule**, free of game objects so it is testable: `TravelFire.Decide(lighterCamping, hasClaim, fireState)` and the claim kept per lighter (in memory, like the fire records; fires are not saved).
2. **`CampTravelService.Poll`** (already runs every second over `Campfire.Active`): set the hue and the name, release and take claims, send the notices. A fire may show orange for up to one second after lighting.
3. **`[CampTravel` list** shows travel fires only; a new refusal `NotTravelFire` for the retry path; `[CampStatus` shows each fire's colour and claim.
4. **Config:** a flag `featureFlags.campTravelBlueFire` (see section 7), validated like the other camp flags (requires `campingTravel`), and a `campTravel.fireHue` number.
5. **Text:** the notices above, the guide page, the README line, and `GuideParagraphs` rewritten from the rules in force.
6. **Tests:** the decision table (first claim, second fire, embers release, relit with the claim taken, skill 49 to 50, flag off, deleted lighter), the list filter, the refusal text, the guide text.

## 6. Verification

- **Unit:** the table above, plus the list shows one entry per lighter.
- **Live, disposable host, Navrey (two players in a party):** light two fires, check the first is blue (item hue) and the second orange; the list has one entry; travel to the blue one works and an ordinary one is refused; let the blue one go to embers and light another (blue); feed embers back while the claim is taken (stays orange); lighter at Camping 49 (orange) then 50 (blue); flag off (every fire as today).
- **Real client, shown to you:** a blue and an orange fire side by side by day and by night, the single-click names, the lighter's messages, the list, the refusal, and the guide page.
- A restart is needed only for the deploy itself; nothing is saved by this change.

## 7. Activation

A new flag, **`campTravelBlueFire`, off when deployed**, so you can see it on the dev host before it counts. With it off, every fire is a travel camp exactly as today. It only changes a feature you already turned on, so I would ask for your explicit "activate" as with the others. If you would rather have no flag, it can ride on `campingTravel` (already on), which means it is live at the next deploy.

## 8. Open questions (recommendation first)

1. **Which fire holds the blue when a player lights a second?** Recommended: **the first one keeps it** (rule 2), so a party always knows where the camp is and capacity is not reset by relighting. Alternative: the newest takes it and the old fire turns orange ("my camp moves with me"), which is friendlier to someone who lit in the wrong place but brings back the capacity stacking, since each new blue fire has fresh places.
2. **A full blue fire:** stays blue until it burns out (recommended; the cap is the point), or turns orange and frees the claim (which brings stacking back).
3. **Move or put out your own travel fire:** not in this item (recommended). The fire lasts five minutes at most without feeding; a "put out" or "move my camp" action can follow if it proves annoying.
4. **Ordinary fires on the list:** hidden (recommended). Alternative: shown dimmed, "ordinary fire".
5. **Visible to everyone, not only the party:** recommended (it is just the colour of a fire). Alternative: nothing; a per-viewer colour would need a client change.
6. **A flag or no flag** (section 7): recommended a flag, off at deploy.
7. **Colour:** after the spike.

## 9. Out of scope / deferred

A put-out or move action; the persistent fire, camp stall and hearth after house zoning (already planned for later); changing capacity, cooldown or Kindling costs (unchanged); a coloured glow (the client cannot); changing who may light a fire (everyone, as now).

## 10. Risks

- **Existing habits.** Camp travel has only been on, in the dev host, since 2026-10-07, so there is little to unlearn; the flag still gives a clean switch-over.
- **Orange for up to a second** after lighting (the once-a-second poll); cosmetic. An engine hook could remove it but is not worth one.
- **The spike could show the hue is ignored** on the animated art (the fallback in section 4).
- **A wrongly placed fire cannot be moved for up to about five minutes** (open question 3).
