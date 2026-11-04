"""Riding (feature "ride"; owner 2026-11-04: "have bots use horses for long trips", "or other mounts"): a ladder fighter or caster whose next outings are
trips to other towns and dungeons buys a horse at an Animal Trainer and rides it, as a Renaissance player rode everywhere once they could afford one.

The engine's rules (ModernUO, pre-AOS; read 2026-11-04):
  buying     SBAnimalTrainer.cs:17 "a horse", 550 gold, 1 control slot; the animal arrives tame and its buyer's (BaseVendor.ProcessValidPurchase), beside
             the buyer, and is ridden from an adjacent tile by a double-click (BaseMount.OnDoubleClick: InRange 1, its master only). Navrey's `mount`
             clears war mode first (a double-click in war mode is an attack) and the state file's isMounted says whether it took.
  speed      Movement.cs: running 100 ms a tile mounted against 200 on foot (runMount / runFoot), so a rider outpaces even a Fast chaser (0.3 s) three to one.
             The rider's stamina is not spent by running mounted (StaminaSystem.ProcessMountMovement): the horse's own step count is, 3,840 running steps
             (BaseMount.StepsMax), regained at 1 a second.
  riding     No region forbids a mount (BaseRegion.MountsAllowed, none overridden); teleporters and moongates take a rider (Teleporter.cs, PublicMoongate.cs).
             Melee, bows, spells, bandages and potions all work mounted; a ridden horse is off the map, so nothing can hit it, and its loyalty does not
             fall while it is ridden (BaseCreature.LoyaltyTimer skips a ridden mount). Pre-AOS nothing knocks a rider off but death (Dismount is an
             AOS special move; no monster here throws a bola).
  death      MountItem.OnParentDeath: the horse is put down where its rider died, still its rider's pet. Left on the map it loses 10 loyalty an hour and goes
             wild at 0, about 10 hours from full.
Other mounts: a ridable llama and the desert and forest ostards ride as a horse does (1 slot); none is sold here (SBAnimalTrainer has the horse only), so a
bot rides one only when it already has it (a tamer's, say).

    r_ride      mounted: note where (the death spot, if it dies). Not mounted, its own mount in view: walk up and ride. Out of view since it died: go back for
                it while RIDE_LOST_S lasts. None, and the bot wants one (ride_wanted) and can pay HORSE_PRICE + RIDE_RESERVE: buy one and ride.
Events: ride_bought {price}, ride_mounted {mount}, ride_fetched {found}, ride_lost.
"""
from __future__ import annotations

import time

RIDE_NAMES = ("a horse", "a ridable llama", "a desert ostard", "a forest ostard", "a frenzied ostard")    # BaseMount kinds of the era (Horse.cs, RidableLlama.cs, *Ostard.cs)
HORSE_KEY = "=horse [live]"      # the shop line exactly: Navrey names a vendor's animal by its body ("Horse [live]", uo-buy-items); "Pack Horse [live]" is no mount.
                                 # "=a horse" matched nothing: BotWarAdvR stood at the Animal Trainer and bought none (2026-11-04 10:17)
HORSE_PRICE = 550                # SBAnimalTrainer.cs:17
RIDE_RESERVE = 500               # gold kept after the purchase: ladder.DUNGEON_WORTH, so a horse never holds back the dungeon trip it is for
MOUNT_RUN_S = 0.1                # Movement.cs runMount: seconds a tile mounted, running (casterpass.RUN_S on foot)
RIDE_LOST_S = 1800               # s out of view after a death: gone. The horse waits where the bot died; the corpse it goes back for lasts 10 minutes and its bones
                                 # 7 more (longerPlayerCorpses, corpseTimerNotice), so a bot that has not found it by then is not coming back for it
RIDE_TRY_GAP = 1800              # s between purchases tried at the stall (a sold-out stall, a line the shop did not show)
RIDE_SHORT_GAP = 300             # s before the next try when the bank walk did not bring the price: the walk was cut short (a fight, loot on the way), not the
                                 # stall's answer. BotHealAdvR's bank walk stopped for a deer and two slimes and the next try waited 30 min (2026-11-04 10:45)
FETCH_REACH = 300                # tiles: a horse farther off than this is not walked back for (packy.FETCH_REACH)
FETCH_GAP = 300                  # s between walks back for it


class RideMixin:

    def ride_on(self):
        try:
            return bool(self.feature("ride"))
        except Exception:
            return False

    def run_s(self):
        """Seconds a tile this bot runs at: mounted or on foot (Movement.cs)."""
        try:
            return MOUNT_RUN_S if self.c.mounted else 0.2
        except Exception:
            return 0.2

    def ride_mobile(self, within=18):
        """Its own mount in view (isPet and a mount's name), nearest first, else None."""
        try:
            mine = [m for m in self.c.mobiles(within=within) if (getattr(m, "_d", None) or {}).get("isPet") and (m.name or "").lower() in RIDE_NAMES]
        except Exception:
            return None
        return min(mine, key=lambda m: m.distance) if mine else None

    def ride_wanted(self):
        """Buy a mount: a ladder bot past the outskirts rung, whose next outings are the long trips (towns, the dungeon)."""
        try:
            return bool(self.ladder_on() and self.ladder_state()["ok"].get("2"))
        except Exception:
            return False

    def ride_mount(self, m):
        """Walk up to the mount and ride it (Navrey `mount`: war mode off first). True when the bot now rides."""
        from uo.client import serial_of
        if (m.distance or 0) > 1:
            self.activity = f"walking to {m.name}"
            try:
                self.goto_near(int(m.x), int(m.y), 1).wait(timeout=20)
            except Exception as e:
                self.log(f"ride: the walk to the mount: {type(e).__name__}: {e}")
        try:
            self.c.call(f"mount {serial_of(m.serial)}", timeout=10)
        except Exception as e:
            self.log(f"ride: mount: {type(e).__name__}: {e}")
        for _ in range(10):
            if self.c.mounted:
                break
            time.sleep(0.3)
        now = time.time()
        if self.c.mounted:
            self.facts["ride"] = {"since": now, "seen": now, "xy": [int(self.c.x), int(self.c.y)], "kind": m.name}
            self.log(f"ride: riding {m.name}")
            self.ev("ride_mounted", mount=m.name)
            return True
        self.log(f"ride: could not ride {m.name} at {m.distance} tiles")
        return False

    def r_ride(self):
        if not self.ride_on() or self.c.ghost:
            return False
        now = time.time()
        rec = self.facts.get("ride")
        if self.c.mounted:
            if rec is None:
                rec = self.facts["ride"] = {"since": now}
            rec["seen"], rec["xy"] = now, [int(self.c.x), int(self.c.y)]
            return False
        if self.threats(8):
            return False                                  # the fight first
        m = self.ride_mobile()
        if m is not None:
            self.ride_mount(m)
            return True
        if rec and now - rec.get("seen", 0) < RIDE_LOST_S:
            xy = rec.get("xy")
            corpse = self.facts.get("corpse") or {}
            if corpse.get("xy") and float(corpse.get("t") or 0) >= float(rec.get("seen") or 0) - 60:
                xy = list(corpse["xy"])                   # it died riding: the horse was put down by its corpse (MountItem.OnParentDeath)
            if xy and now - rec.get("fetch_at", 0) > FETCH_GAP and max(abs(xy[0] - self.c.x), abs(xy[1] - self.c.y)) <= FETCH_REACH:
                rec["fetch_at"] = now
                self.activity = f"going back for the horse at {xy[0]},{xy[1]}"
                res = self.travel(xy[0], xy[1], near=6)
                m = self.ride_mobile()
                self.log(f"ride: went back for the mount at {xy[0]},{xy[1]} ({res}): {'found' if m is not None else 'not there'}")
                self.ev("ride_fetched", found=m is not None)
                if m is not None:
                    self.ride_mount(m)
                return True
            return False
        if rec:
            self.log(f"ride: the mount not seen for {int((now - rec.get('seen', now)) // 60)} min: lost")
            self.ev("ride_lost")
            self.facts.pop("ride", None)
        if not self.ride_wanted() or now - self.facts.get("ride_try_at", 0) < RIDE_TRY_GAP or not hasattr(self, "shop_at"):
            return False                                  # (a caster brain has no shop_at: it rides a mount it has, it buys none)
        st = self.c.state or {}
        if int(st.get("followers") or 0) + 1 > int(st.get("maxFollowers") or 5):
            return False                                  # no control slot free (Mobile.FollowersMax 5; a horse takes 1)
        funds = self.c.gold + max(0, self.facts.get("bank_balance", 0))
        if funds < HORSE_PRICE + RIDE_RESERVE:
            return False
        self.facts["ride_try_at"] = now
        self.activity = "buying a horse"
        if self.c.gold < HORSE_PRICE + 10 and self.facts.get("bank_balance", 0) > 0:
            self.visit_bank("horse", withdraw=min(self.facts["bank_balance"], HORSE_PRICE + 50))
        if self.c.gold < HORSE_PRICE:
            self.facts["ride_try_at"] = now - RIDE_TRY_GAP + RIDE_SHORT_GAP
            self.log(f"ride: the bank walk did not bring the price ({self.c.gold} gold): again in {RIDE_SHORT_GAP // 60} min")
            return True
        where = self.where1(("animal_trainer",), item="horse")
        if not where:
            self.log("ride: no Animal Trainer known")
            return True
        self.travel(where[0], where[1], near=4)
        m = self.ride_mobile(within=10)
        if m is None:
            got = self.shop_at(where, {HORSE_KEY: 1}, budget=max(self.c.gold - 5, 0))
            time.sleep(3)
            m = self.ride_mobile(within=10)
            if m is not None:
                self.log(f"ride: bought a horse ({got})")
                self.ev("ride_bought", price=HORSE_PRICE)
        if m is not None:
            self.ride_mount(m)
        return True
