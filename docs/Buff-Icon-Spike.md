# Buff-icon spike (Tier 1 item F)

**Superseded 2026-10-07 by `Buff-Icons-Era-Text.md`:** the stock-text problem found below is fixed by a data table and a narrow hook, the missing UOR effects and the shard's own states now have icons, and the "ID:" line and the hidden buff window are fixed in the client. What follows is the spike as it was.

Owner authorized 2026-10-07: a disposable-host test only, no flag, nothing shipped. Question: can the shard's own states (Knocked Out, criminal timer, Intent, Ward, Faint Memories ready) be shown as buff icons in this client, with the shard's own text?

## What was done

Disposable host `qol` (deleted afterwards) with the stock setting `buffIcons.enable` set to `True` in that host's `modernuo.json` only. A test-only probe verb (`TestOnlyBuff`, in `tests/scenarios/alpha3-tools/TestOnlyProbe.cs`) added six buffs to a new character, who was then logged in through the real ClassicUO client. Screenshots were taken of the buff window and of three tooltips (`work/player-client/Vista/shots/`, scratch).

## Findings

| Question | Answer |
| --- | --- |
| Do buff icons show in this client with no extra feature bit? | **Yes.** Six icons appeared as soon as the buff window was opened |
| Is the stock art usable for our states? | **Mostly.** Knockout shows a "KO" glyph, a clear fit for Knocked Out. CriminalStatus (red), Warding, Perfection, HeatOfBattleStatus (red fighter) and Honored (green figure) all drew. Which one best stands for Intent, a Ward or "free points ready" is a taste call; none is perfect |
| Can the shard put its own text on an icon? | **Yes.** Buff title cliloc 1042971 with the text as the argument displayed "Knocked Out" and the other texts as typed (the client title-cases them) |
| Can an icon carry a description? | **Yes, with a caveat.** With description cliloc 1070722 the same argument text appears twice (title and description); with description `0` there is a title only |
| Does a countdown work? | **Yes.** "Time left: 00:00:42" ran down live; a buff with no duration shows no countdown |
| Does the client add anything of its own? | A line "ID: <icon name>" under every buff's text (`BuffGump.cs:316,336` in the fork). It is cosmetic and removable with the item C client change |
| Does the buff window open by itself? | **No.** It opens from the orb button at the top-left of the Character Status window (or the ToggleBuffIconGump macro). Showing it by default needs client code (item C) |
| What does turning the setting on do besides our icons? | It also lights every stock UOR buff icon (Bless, Curse, Hide, Paralyze and the rest), a design decision for the owner |

## Conclusion

Feasible and cheap for the server side: one `BuffInfo` per state, re-added at login (buffs are not saved), using the Knockout, CriminalStatus, Warding, HeatOfBattleStatus and Perfection or Honored icons with the shard's own title text. The criminal timer needs the `Mobile.CriminalChanged` hook already planned for item B so the icon starts and ends with the flag. Two client changes belong with item C: open the buff window by default and drop the "ID:" line. The owner decides whether the stock buff icons come on with it.

Not tested in the spike: the art of every icon at game size beside a real fight, behaviour on death (non-retained buffs are removed on death), and how many icons fit before the bar gets crowded.

## Stock effects (owner question 2026-10-07: "does the buff bar work with standard effects like Bless, Curse?")

Disposable host `qol`, `buffIcons.enable` True, a test mage (`TestOnlyMage`: Magery 100, a full spellbook, reagents) casting through the engine's normal path (`TestOnlyCast` starts the stock spell, the client gets the real target cursor, the click targets self), seen in the real client.

| Spell | What showed |
| --- | --- |
| Bless | Icon (green hand), tooltip "Bless: +11% Strength, +11% Dexterity, +11% Intelligence", "Time left" counting down (1:22). Stats rose by 11 each |
| Curse | Red icon, tooltip "Curse: -17% Strength, Dexterity, Intelligence; -10 To Max Fire, Cold, Poison and Energy Resistance", countdown |
| Strength | Icon, tooltip "+11% Strength", countdown |
| Protection | **No icon.** On this shard Protection is the targeted UOR form; stock registers its icon only in the AoS toggle (`ProtectionSpell.Toggle`) |

So the bar works with the stock effects, but the **tooltip text is AoS-era and does not match this shard's rules**: it says percent where the effect is a flat number of points (Bless is +11 points: `SpellHelper.GetOffset` is `1 + Magery * 0.1` outside AoS), and Curse's "-17%" comes from the AoS scalar while the flat offset the code applies is the same 11 (by the code; not measured on its own). The max-resistance lines are real engine code (`PlayerMobile.GetMaxResistance`) but resistances barely matter in UOR. Other stock buffs registered in the code (Clumsy, Feeblemind, Weaken, Agility, Cunning, Night Sight, Reactive Armor, Magic Reflect, Incognito, Invisibility, Hiding, Meditation, Paralyze) were not cast; they use the same path. Turning the setting on lights all of them. If the owner wants the bar, the shard should supply its own text for the stock icons (a hook before `AddBuff` that swaps the clilocs for shard text) rather than show the AoS wording. The client also still prints "ID: <name>" under every tooltip (item C).
