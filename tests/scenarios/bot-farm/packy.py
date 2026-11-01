"""A miner's pack horse (feature "pack_animal"), as Renaissance miners worked the hills: the miner's own pack holds about 25-30 piles of ore, so a miner on
the western range walked about 240 tiles to the forge for every load (walking, smelting and selling were 30-45% of its hour, 2026-10-31). A pack horse's
pack holds 1,600 stones more (PackHorse.cs: StrongBackpack, DefaultMaxWeight 1600), about five loads.

The engine's rules, tested by hand on the farm host (2026-10-31, BotMinerAR): an Animal Trainer sells "a pack horse" for 631 gold (SBAnimalTrainer); the
bought horse is the buyer's own pet and follows on "all follow me"; an item dropped on it goes into its pack (PackHorse.OnDragDrop); a double-click opens
the pack (PackAnimal.TryPackOpen) and the owner may lift from it. Ore in the horse's pack cannot be smelted ("That is not accessible", BaseOre: RootParent is
a creature), so at the forge it comes back into the miner's own pack a load at a time.

    r_packy         buy one when there is none (gold and bank cover the price and PACK_RESERVE), keep it following; a horse not seen for PACK_LOST_S is
                    taken as lost, and another is not bought within PACK_BUY_GAP of that
    packy_load      the miner's own pack is heavy and the horse stands near: the ore goes onto the horse and digging goes on (r_sell calls it)
    packy_unload    at the forge after smelting: the next load of ore out of the horse's pack (smelt calls it again until the horse is empty)
Events: packy_bought {price}, packy_lost, packy_fetched {found}, packy_found {at}, packy_loaded {piles, stones}, packy_unloaded {piles, stones}.
"""
from __future__ import annotations

import re
import time

PACK_WORD = "pack horse"
PACK_PRICE_GUESS = 631          # SBAnimalTrainer / SBRancher: a pack horse, 631 gold
PACK_CAP = 1600                 # StrongBackpack.DefaultMaxWeight
PACK_FILL = 0.9                 # the horse is loaded to this share of PACK_CAP (its pack's own weight and rounding)
PACK_RESERVE = 300              # gold kept after the purchase (the bank trip and a set of tools)
PACK_LOST_S = 600               # not seen this long: gone (dead, or left behind)
PACK_BUY_GAP = 3600             # after a loss, the next horse waits this long
PACK_NEAR = 2                   # tiles: a drop onto the horse, as onto any mobile, needs it this near
FOLLOW_EVERY = 30               # s between "all follow me" when the horse lags
FETCH_AFTER = 45                # s out of view: walk back to where the horse was last seen. A following pet stands still once its master is beyond its
                                # perception (BaseAI.FollowTarget, RangePerception 16 for a pack horse), so a long walk leaves it behind
FETCH_REACH = 300               # tiles: farther than this, the walk back is not made
FETCH_GAP = 300                 # s between walks back for it
# leading it (feature "packy_lead"): pre-AOS a following pet has no speed cap (BaseCreature.FollowMoveSpeed 0 unless AOS), so a pack horse steps at its own
# 0.45 s ("Medium", npc-speeds.json activeMove) while a running player steps at 0.2 s and a walking one at 0.4 (movement.delay.runFoot / walkFoot): a running
# miner left it behind on every trip (2026-10-31). Leading, the miner walks, watches the horse every LEAD_SLICE s, and stops for it past LEAD_GAP tiles,
# well inside the 16 tiles past which it stands still
LEAD_GAP = 10
FOLLOW_RANGE = 16              # tiles: past this a following pet stands still (BaseAI.FollowTarget, RangePerception)
LOAD_GAP = 8.0                  # s between loads
LEAD_SLICE = 3.0
LEAD_WAIT = 25.0                # s to wait for it to catch up before going on without it (r_packy then walks back for it)
LEAD_MIN = 3                    # tiles: a shorter walk is not led. Was 12: a far walk goes in legs of 9-36 tiles, each its own goto, and every leg under 12 ran,
                                # so the horse was left behind on the long walks it was bought for (2026-11-01: 32 walks back for it in 3 h, nearly all after one)
BACK_WAIT = 8.0                 # s a horse walked back to is waited for after 'all come', before the bot walks right up to it
CALL_NEAR = 3                   # tiles: a horse farther off than this (but in view) is called before a led walk sets off


class PackAnimalMixin:

    def packy_mobile(self, within=18):
        """The horse in view: the recorded serial, else a pack horse of this bot's own (isPet) to adopt (one bought before a brain restart)."""
        rec = self.facts.get("packy") or {}
        mine = [m for m in self.c.mobiles(within=within) if (getattr(m, "_d", None) or {}).get("isPet") and PACK_WORD in (m.name or "").lower()]
        m = next((x for x in mine if x.serial == rec.get("serial")), None) or (min(mine, key=lambda x: x.distance) if mine else None)
        if m is not None and m.serial != rec.get("serial"):
            self.facts["packy"] = {"serial": m.serial, "since": time.time(), "seen": time.time(), "load": rec.get("load", 0.0) if rec else 0.0}
        return m

    def r_packy(self):
        if not self.feature("pack_animal") or self.c.ghost or self.threats(8):
            return False
        now = time.time()
        m = self.packy_mobile()
        rec = self.facts.get("packy")
        if m is not None:
            rec["seen"], rec["xy"] = now, [m.x, m.y]
            if (m.distance > 4 or not rec.get("called")) and now - rec.get("called", 0) > FOLLOW_EVERY:
                rec["called"] = now
                self.c.say("all follow me")
            return False
        if rec and now - rec.get("seen", 0) < PACK_LOST_S:
            xy = rec.get("xy")
            if (xy and now - rec.get("seen", 0) > FETCH_AFTER and now - rec.get("fetch_at", 0) > FETCH_GAP
                    and max(abs(xy[0] - self.c.x), abs(xy[1] - self.c.y)) <= FETCH_REACH):
                rec["fetch_at"] = now
                self.activity = f"going back for the pack horse at {xy[0]},{xy[1]}"
                res = self.travel(xy[0], xy[1], near=6)
                m = self.packy_mobile()
                if m is not None:
                    rec["seen"], rec["called"] = time.time(), time.time()
                    self.c.say("all follow me")
                self.log(f"pack horse: went back for it at {xy[0]},{xy[1]} ({res}): {'found' if m is not None else 'not there'}")
                self.ev("packy_fetched", found=m is not None)
                return True
            return False                                  # out of view for now (a far walk, a corner)
        if rec:
            self.log(f"pack horse: not seen for {int((now - rec.get('seen', now)) // 60)} min: lost, with about {rec.get('load', 0):.0f} stones of ore")
            self.ev("packy_lost", load=round(rec.get("load", 0)))
            self.facts.pop("packy", None)
            self.facts["packy_lost_at"] = now
        if now - self.facts.get("packy_lost_at", 0) < PACK_BUY_GAP or now - self.facts.get("packy_try_at", 0) < 1800:
            return False
        prices = [p for p, xy, item, qty in self.mem.vendor_selling(PACK_WORD) if p > 0]
        price = min(prices) if prices else PACK_PRICE_GUESS
        funds = self.c.gold + max(0, self.facts.get("bank_balance", 0))
        if funds < price + PACK_RESERVE:
            return False
        self.facts["packy_try_at"] = now
        self.activity = "buying a pack horse"
        if self.c.gold < price + 10 and self.facts.get("bank_balance", 0) > 0:
            # the visit banks the purse down to its reserve before the withdrawal, so the whole price comes out (two miners came back with 473 and
            # 417 of the 631, 2026-10-31)
            self.visit_bank("pack horse", withdraw=min(self.facts["bank_balance"], price + 50))
        if self.c.gold < price:
            return True
        where = self.where1(("animal_trainer",), item=PACK_WORD)
        if where:
            self.travel(where[0], where[1], near=4)
            m = self.packy_mobile()
            if m is not None:
                # a horse of its own waits there (left behind at the stall, or bought before the record was lost): no second one is paid for
                self.facts["packy"]["seen"] = time.time()
                self.c.say("all follow me")
                self.log(f"pack horse: its own horse was at the Animal Trainer: taken back, not bought again")
                self.ev("packy_found", at=list(where))
                return True
        got = self.shop_at(where, {PACK_WORD: 1}, budget=max(self.c.gold - 5, 0))
        time.sleep(3)
        m = self.packy_mobile(within=10)
        if m is not None:
            self.facts["packy"]["load"] = 0.0
            self.c.say("all follow me")
            self.log(f"pack horse bought ({got}): it carries the ore between the hills and the forge")
            self.ev("packy_bought", price=price)
        return True

    def packy_load(self):
        """The ore in the miner's own pack onto the horse, while it has room. True when anything went on."""
        if not self.feature("pack_animal"):
            return False
        rec = self.facts.get("packy") or {}
        if time.time() - rec.get("loaded_at", 0) < LOAD_GAP:
            return False                                  # the client's weight and pack lag a moment behind a load: loaded again at once, BotMineAdvR
                                                          # logged "loaded 1 piles (0 stones)" 21 times in 60 s and the loop guard held r_sell back (2026-10-31)
        m = self.packy_mobile()
        if m is None or rec.get("load", 0) >= PACK_CAP * PACK_FILL:
            return False
        if m.distance > PACK_NEAR:
            self.c.goto(m.x, m.y).wait(timeout=15)
            m = self.packy_mobile()
            if m is None or m.distance > PACK_NEAR:
                return False
        moved, stones = 0, 0.0
        for p in sorted(self.ore_piles(), key=lambda i: bool(getattr(i, "hue", 0))):     # iron first: no shop buys coloured metal (bot_common.drop_excess)
            if rec.get("load", 0) >= PACK_CAP * PACK_FILL:
                break
            before = self.c.weight
            self.c.call(f"drop {p.serial} {m.serial}", timeout=8)
            time.sleep(0.8)
            if not any(i.serial == p.serial for i in self.c.backpack):
                w = max(0.0, float(before - self.c.weight))
                rec["load"] = rec.get("load", 0.0) + w
                stones += w
                moved += 1
        if moved:
            rec["loaded_at"] = time.time()
            self.facts["packy"] = rec
            self.log(f"pack horse: loaded {moved} piles of ore ({stones:.0f} stones; it carries about {rec['load']:.0f})")
            self.ev("packy_loaded", piles=moved, stones=round(stones))
        return moved > 0

    def packy_unload(self):
        """At the forge: the next load of ore out of the horse's pack into the miner's own, up to its CLEAR_SHARE of the weight limit. True when any came."""
        if not self.feature("pack_animal"):
            return False
        rec = self.facts.get("packy") or {}
        m = self.packy_mobile()
        if m is None or rec.get("load", 0) <= 0:
            return False
        if m.distance > PACK_NEAR:
            self.c.say("all follow me")
            self.c.goto(m.x, m.y).wait(timeout=15)
            m = self.packy_mobile()
            if m is None or m.distance > PACK_NEAR:
                return False
        self.c.events.drain()
        self.c.use(m.serial)
        pack = None
        end = time.time() + 4
        while time.time() < end and pack is None:
            time.sleep(0.5)
            for e in self.c.events.poll():
                mm = re.search(r"Opened (0x[0-9A-Fa-f]+)", e.text)
                if mm:
                    pack = mm.group(1)
        if pack is None:
            return False
        try:
            inside = [i for i in self.c.container(pack, timeout=6) if re.search(r"\bore\b", (i.name or "").lower())]
        except Exception:
            return False
        if not inside:
            rec["load"] = 0.0
            return False
        room = self.c.max_weight * self.CLEAR_SHARE - self.c.weight
        taken, stones = 0, 0.0
        for it in inside:
            if room <= 0:
                break
            before = self.c.weight
            self.c.get_item(it.serial, None)
            time.sleep(0.8)
            w = max(0.0, float(self.c.weight - before))
            room -= w
            stones += w
            taken += 1
        rec["load"] = max(0.0, rec.get("load", 0.0) - stones)
        self.facts["packy"] = rec
        if taken:
            self.log(f"pack horse: took out {taken} piles of ore ({stones:.0f} stones) to smelt")
            self.ev("packy_unloaded", piles=taken, stones=round(stones))
        return taken > 0

    # ---- leading the horse at its pace (feature "packy_lead"; called from BotBase._wrap_goto's wait) ------------------------------------------------------

    def packy_leading(self, x, y):
        """True when this walk should go at the horse's pace: the feature is on, the horse is in view and near, the walk is long, and the bot is not
        running for its life (a flight sprints, BotBase.sprint)."""
        if not (self.feature("pack_animal") and self.feature("packy_lead")) or self.c.ghost or self.__dict__.get("_packy_calling"):
            return False                                  # (the walk to the horse itself, while calling it in, is not led)
        if time.time() - self.facts.get("sprint_at", 0) < 15 or max(abs(x - self.c.x), abs(y - self.c.y)) < LEAD_MIN:
            return False
        m = self.packy_mobile()
        if m is None:
            return False
        if m.distance > CALL_NEAR:
            # a horse in view but not at heel (it stood still past its 16 tiles, or was left at the bank): called in before the walk sets off, so the walk
            # never starts with it out of its follow range (BotMineAdvR walked back for it at 1428,1691 four times in half an hour, 2026-10-31)
            self.packy_call_in(m)
        return True

    def packy_call_in(self, m, wait=None):
        """'all come', wait for it (at most wait s), then 'all follow me'; walk to it when it does not come (a pet past its perception does not hear
        the order move it: it stands still, BaseAI FollowTarget). True when it is at heel."""
        self.__dict__["_packy_calling"] = True
        try:
            return self._packy_call_in(m, LEAD_WAIT if wait is None else wait)
        finally:
            self.__dict__["_packy_calling"] = False

    def _packy_call_in(self, m, wait):
        self.c.say("all come")
        until = time.time() + wait
        while time.time() < until:
            time.sleep(1.0)
            m2 = self.packy_mobile()
            if m2 is not None and m2.distance <= CALL_NEAR:
                self.c.say("all follow me")
                return True
            if m2 is not None:
                m = m2
        try:
            self.c.goto(m.x, m.y).wait(timeout=60)
        except Exception:
            pass
        m2 = self.packy_mobile()
        self.c.say("all follow me")
        return m2 is not None and m2.distance <= CALL_NEAR

    def packy_back_for(self, m):
        """Once a walk: back to the horse and call it in (packy_call_in). True when it is at heel again."""
        self.__dict__["_packy_backed"] = True
        self.ev("packy_back", dist=m.distance)
        return self.packy_call_in(m, wait=BACK_WAIT)

    def packy_lead(self, walk_wait, restart, timeout):
        """Wait out a walk at the horse's pace: walking, not running; every LEAD_SLICE s a look back, and past LEAD_GAP tiles a stop until it catches up
        (at most LEAD_WAIT s), then the walk again. Returns the walk's result."""
        # the shard's petsKeepUp (feature "pets_keep_up" mirrors it): a following pet steps at the run-on-foot pace, so the miner may run; without it a
        # pack horse (0.45 s a step) falls behind even a walking player (0.4 s), and the miner walks
        self.set_runmode("auto" if self.feature("pets_keep_up") else "never")
        waits = 0
        self.__dict__["_packy_backed"] = False
        try:
            end = time.time() + timeout
            while True:
                left = end - time.time()
                if left <= 0:
                    return "timeout"
                res = walk_wait(min(LEAD_SLICE, left))
                if res != "timeout":
                    return res
                m = self.packy_mobile()
                if m is not None and m.distance <= LEAD_GAP:
                    continue
                self.c.call("stop", timeout=3)
                self.c.say("all follow me")
                caught = False
                until = time.time() + LEAD_WAIT
                while time.time() < until:
                    time.sleep(1.0)
                    m = self.packy_mobile()
                    if m is not None and m.distance <= 3:
                        caught = True
                        break
                waits += 1
                walk_wait = restart()
                if not caught:
                    # walked back to at once, while it is still near where it stopped (it stands still past 16 tiles and never follows again): going on
                    # without it left it for good (2026-10-31: 3-4 losses a horse in 3 h). Once a walk; then the walk goes on and r_packy fetches it later
                    self.ev("packy_behind", dist=m.distance if m is not None else None, at=[self.c.x, self.c.y])
                    back = m is not None and not self.__dict__.get("_packy_backed") and self.packy_back_for(m)
                    self.log(f"pack horse: it did not catch up ({m.distance if m is not None else 'out of'} tiles {'off' if m is not None else 'view'} "
                             f"at {self.c.x},{self.c.y}); {'walked back for it' if back else 'the walk goes on without it (it is walked back for)'}")
                    if back:
                        walk_wait = restart()
                        continue
                    self.set_runmode("auto")
                    return walk_wait(max(end - time.time(), 0.05))
        finally:
            if waits:
                self.ev("packy_led", waits=waits)
            self.set_runmode("auto")
