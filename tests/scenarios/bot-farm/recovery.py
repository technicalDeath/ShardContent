"""Death recovery and stamina, the bot side (written into the bot-farm folder by patch_recovery.py). The server features are BotFarm QoL's, built 2026-10-16/17
and described in ShardContent/docs/Death-Recovery-Plan.md. Every reaction is driven by the server's own lines, read from the client's log (loopguard.guard_client
calls recovery_line for each [SYSTEM] line), and each is gated by a features.json switch, so nothing changes until the farm host runs the build with the
server flag on and the bot is in the cohort:
 corpse_timer    "Your corpse will turn to bones in N minutes, and the bones and everything in them will be gone 7 minutes after that.": the corpse run's
                 deadline becomes N + 7 minutes (less a minute), instead of the brain's 7-minute guess.
 ghost_hint      "A healer cannot see a ghost in peace mode...": war mode on, step out past 4 tiles of the healer, walk back in (r_dead's own 25 s routine stays
                 the fallback).
 blue_self_loot  one double-click on the own corpse takes everything back ("You quickly gather all of your belongings." / "You gather some of your
                 belongings. The rest remain on the corpse."); item-by-item only for what is left. Worn gear goes back on by itself; r_gear fixes the rest.
 killer_home     the monster that killed the bot walks home and ignores it for 2 minutes after the bot is alive again: during that window it is not a reason
                 to flee or avoid (mobs() leaves it out); every other monster counts as before.
 materializing   "You are materializing: monsters cannot see you...": the corpse run goes at once (no hit-point or threat or gold test: monsters cannot see
                 the bot and worn gear comes back), and the rules that would end it (potions, bandages, skills, spells, fights, looting other corpses,
                 vendors) wait until "You have fully materialized" (or 10 minutes). A refusal ("That will end your materializing...") is counted.
 stamina_relief  "You are too tired to run, but you can still walk...": walk (runmode never) for 45 s, and a flight does not ask to run meanwhile.
Not covered here: the corpse compass (the Tracking arrow, packet 0xBA): Navrey does not expose the arrow yet; the death spot stays the target.
Casters (CasterBot / mage_bot, patch_recovery_casters.py) get the same reactions through recovery_tail (their own client-log reader), the gate in mage_bot's
rule loop (an optional hook), and recovery_corpse_run (they had no corpse run at all; it runs only with blue_self_loot or materializing on).
"""
import re
import time

CORPSE_RX = re.compile(r"Your corpse will turn to bones in (\d+) minutes?")
GHOST_HINT = "A healer cannot see a ghost in peace mode"
SELF_ALL = "You quickly gather all of your belongings"
SELF_SOME = "You gather some of your belongings"
# materializing, renamed "Between Worlds" by the owner (2026-10-17); the old texts are kept so an older build still matches
MAT_START = ("You are Between Worlds", "You are materializing")
MAT_END = ("You are fully back in the world", "You have fully materialized")
MAT_REFUSE = "That will end your materializing"                 # the first build's line; now the server asks in a dialog (MAT_GUMP)
MAT_GUMP = "Between Worlds"                                      # "Come fully back?" OKAY = 1, CANCEL = 0: a recovering bot answers 0
CRIM_RX = re.compile(r"You will be a criminal for about (\d+)\s*(second|minute|hour)", re.I)   # criminalGhostNotice: the healer refused a criminal ghost
CRIM_END = "You are no longer a criminal"
TIRED = "You are too tired to run"
BONES_MIN = 7
MAT_MAX = 600
KILLER_WINDOW = 150
WALK_FOR = 45
# rules that would end materializing (a use of an item, a skill, a spell, an attack, lifting from another container, a vendor list); walking, doors, the
# own pack, bank and corpse, and equipping do not end it, so r_corpse, r_gear, r_bank, r_explore and the walks stay
MAT_BLOCK = ("r_fight", "r_hunt", "r_heal", "r_cure", "r_flee", "r_loot", "r_music", "r_resupply", "r_upgrade", "r_sell", "r_sellgear", "r_sellmeat",
             "r_restock", "r_retool", "r_craft", "r_fish", "r_mine", "r_dig", "r_chop", "r_tame", "r_lore", "r_practice", "r_book", "r_facility", "r_camp",
             "r_party", "r_party_heal", "r_buddy", "r_buddy_heal", "r_earn", "r_cut", "r_fletch", "r_smelt", "r_market", "r_avoid", "r_evade",
             "r_train", "r_rest", "r_carve", "r_sellmeat",                           # the casters' own (mage_bot / CasterBot)
             "r_bank", "r_lighten")                     # final rule: taking from the bank asks; only the own corpse, pack sorting and gear are free


class RecoveryMixin:
    _self_loot = None

    # ---- state ----------------------------------------------------------------------------------------------------------------------------------

    def materializing(self):
        return self.feature("materializing") and time.time() < self.facts.get("mat_until", 0)

    def criminal_wait(self):
        """A criminal ghost the healer refused: wait out the time the server stated (criminal_ghost), instead of walking in and out."""
        return self.feature("criminal_ghost") and time.time() < self.facts.get("crim_wait_until", 0)

    def recovery_skip(self, rule):
        """True for a rule that must wait while the bot is materializing."""
        return rule in MAT_BLOCK and self.materializing() and not (hasattr(self, "bw_released") and self.bw_released())

    def killer_spared(self, m):
        """The monster that killed this bot, during the 2 minutes it ignores the bot after its resurrection (killer_home)."""
        k = self.facts.get("killer")
        if not k or not self.feature("killer_home") or time.time() > self.facts.get("killer_until", 0):
            return False
        n = (m.name or "").lower()
        kn = k["name"].lower()
        mk = getattr(self, "mkey", None)
        return bool(n) and (kn == n or kn.startswith(n + " ") or (mk is not None and mk(m) == kn))     # casters record the killer's key ("troll")

    # ---- the server's lines --------------------------------------------------------------------------------------------------------------------------

    def bw_credit(self, how):
        """The open Between Worlds record learns at once what the corpse gave back, so an end line in the same read cannot write \"no corpse taken\"."""
        b = self.facts.get("bw")
        if b and not b.get("how"):
            b["how"] = how

    def recovery_line(self, text):
        now = time.time()
        m = CORPSE_RX.search(text)
        if m and self.feature("corpse_timer"):
            deadline = now + (int(m.group(1)) + BONES_MIN) * 60 - 60
            c = self.facts.get("corpse")
            if c and abs(now - c.get("t", 0)) < 180:
                c["deadline"] = deadline
            else:
                self.facts["corpse_deadline"] = [now, deadline]       # the corpse record is written a moment later (r_dead)
            self.dlog("ev", ev="corpse_timer", minutes=int(m.group(1)))
            return
        if GHOST_HINT in text and self.feature("ghost_hint"):
            self.facts["ghost_hint_at"] = now
            return
        if SELF_ALL in text:
            self._self_loot = ("all", now)
            self.bw_credit("all")
            return
        if SELF_SOME in text:
            self._self_loot = ("some", now)
            self.bw_credit("some")
            return
        m = CRIM_RX.search(text)
        if m and self.feature("criminal_ghost"):
            secs = int(m.group(1)) * {"second": 1, "minute": 60, "hour": 3600}[m.group(2).lower()]
            self.facts["crim_wait_until"] = now + secs + 5
            self.dlog("ev", ev="criminal_ghost_wait", secs=secs)
            return
        if CRIM_END in text and self.facts.get("crim_wait_until"):
            self.facts.pop("crim_wait_until", None)
            self.dlog("ev", ev="criminal_ghost_clear")
            return
        if any(s in text for s in MAT_START) and self.feature("materializing"):
            self.facts["mat_until"] = now + MAT_MAX
            self.facts["mat_from"] = now
            self.dlog("ev", ev="materializing")
            if hasattr(self, "bw_start"):
                self.bw_start(now)                                    # what the window is for (bw.py)
            return
        if any(s in text for s in MAT_END) and self.facts.get("mat_until"):
            self.facts.pop("mat_until", None)
            self.dlog("ev", ev="materialized", secs=round(now - self.facts.pop("mat_from", now)), refused=self.facts.get("mat_refused_n", 0))
            self.facts["mat_refused_n"] = 0
            if hasattr(self, "bw_end"):
                self.bw_end(now)
            return
        if MAT_REFUSE in text:
            self.facts["mat_refused_n"] = self.facts.get("mat_refused_n", 0) + 1
            self.dlog("ev", ev="materialize_refused", rule=getattr(self, "current_rule", None), n=self.facts["mat_refused_n"])
            return
        if "too fatigued to move" in text:
            self.facts["fatigued_at"] = now                    # overweight: the run loop sheds weight (BotBase.drop_excess)
            return
        if TIRED in text and self.feature("stamina_relief"):
            self.facts["walk_until"] = now + WALK_FOR
            if self.facts.get("runmode") != "never":
                self.set_runmode("never")
            self.dlog("ev", ev="too_tired", hp=self.c.hp, stam=getattr(self.c, "stam", None))

    # ---- vitals and the death timeline, for the watcher's reads (no switch: logging only) ------------------------------------------------------

    def vitals(self):
        """{stam, max_stam, stam_min10, hp_min10}: now, and the lowest of the last 10 s (death events and flight episodes carry them)."""
        st = getattr(self.c, "state", {}) or {}
        ring = [v for v in self.__dict__.get("_vitals", []) if time.time() - v[0] <= 10]
        last = self.__dict__.get("_vitals") or [None]
        last = last[-1]                                       # the last LIVING tick (a death event is written on the ghost tick)
        return {"stam": last[2] if last else st.get("stamina"), "max_stam": st.get("maxStam"),
                "stam_min10": min((v[2] for v in ring if v[2] is not None), default=last[2] if last else st.get("stamina")),
                "hp_min10": min((v[1] for v in ring if v[1] is not None), default=last[1] if last else st.get("hits")),
                "hp": last[1] if last else st.get("hits")}

    def vitals_tick(self, now):
        st = getattr(self.c, "state", {}) or {}
        ring = self.__dict__.setdefault("_vitals", [])
        if not getattr(self.c, "ghost", False) and (st.get("hits") or 0) > 0:
            ring.append((now, st.get("hits"), st.get("stamina")))     # living ticks only (the watcher: deaths read 0/0)
        while len(ring) > 1 and now - ring[0][0] > 12:
            ring.pop(0)                                       # never the last living tick: a long fight tick outlasts 12 s (patch_vitals_keep_last.py)
        rule = getattr(self, "last_rule", None)
        if rule == "r_flee" and self.__dict__.get("_prev_rule") != "r_flee" and now - self.facts.get("flee_ev_at", 0) > 20:
            self.facts["flee_ev_at"] = now
            self.dlog("ev", ev="flee", **self.vitals())              # a flight episode starts
        self.__dict__["_prev_rule"] = rule
        ghost = bool(self.c.ghost)
        was = self.__dict__.get("_was_ghost")
        if was is None:
            self.__dict__["_was_ghost"] = ghost
            return
        if ghost and not was:
            self.facts["died_at"] = now
        if was and not ghost:
            offer = now - self.facts.get("offer_at", 0) < 120
            self.dlog("ev", ev="resurrected", secs_dead=round(now - self.facts.get("died_at", now)), by="offer" if offer else "other")
            self.facts["res_seen_at"] = now
        self.__dict__["_was_ghost"] = ghost
        if self.facts.get("res_seen_at") and not ghost:
            if any((i.layer or "") in ("OneHanded", "TwoHanded") for i in self.c.equipped):
                self.dlog("ev", ev="rearmed", secs=round(now - self.facts.pop("res_seen_at")))
            elif now - self.facts["res_seen_at"] > 1800:
                self.facts.pop("res_seen_at", None)

    def recovery_tick(self):
        """Once per tick: the stamina walk ends, materializing times out, and the killer's window opens when the bot is alive again."""
        now = time.time()
        try:
            self.vitals_tick(now)
        except Exception:
            pass
        if hasattr(self, "bw_tick"):
            try:
                self.bw_tick(now)
            except Exception as e:
                self.log(f"bw: {type(e).__name__}: {e}")
        if self.materializing():
            find = getattr(self, "find_gump", None)
            serial = find(MAT_GUMP) if find else None
            if serial:
                # an action the brain did not mean to end it with: CANCEL keeps the bot Between Worlds; counted as before
                self.c.call(f"gumpresponse 0 gump:{serial}", timeout=6)
                self.facts["mat_refused_n"] = self.facts.get("mat_refused_n", 0) + 1
                self.dlog("ev", ev="materialize_refused", rule=getattr(self, "last_rule", None), n=self.facts["mat_refused_n"], how="dialog")
        if self.facts.get("runmode") == "never" and now > self.facts.get("walk_until", 0):
            self.set_runmode("auto")
        if self.facts.get("mat_until") and now > self.facts["mat_until"]:
            self.facts.pop("mat_until", None)
        k = self.facts.get("killer")
        if k and not self.c.ghost and not self.facts.get("killer_until"):
            self.facts["killer_until"] = now + KILLER_WINDOW            # its 2 minutes start when it first sees the bot alive again
        if k and self.c.ghost:
            self.facts.pop("killer_until", None)
        if k and now - k.get("t", now) > 1800:
            self.facts.pop("killer", None)
            self.facts.pop("killer_until", None)

    def corpse_deadline(self, info):
        """The corpse run's deadline: the server's own timer (corpse_timer) when it told us, else the old 7-minute guess."""
        p = self.facts.get("corpse_deadline")
        if p and "deadline" not in info and abs(p[0] - info.get("t", 0)) < 180:
            info["deadline"] = p[1]
            self.facts.pop("corpse_deadline", None)
        return info.get("deadline", info["t"] + 420)

    def self_loot_result(self, since):
        """After a double-click on the own corpse: "all", "some" or None (the server's line, read from the client log)."""
        try:
            reader = getattr(self, "guard_client", None) or self.recovery_tail
            reader()
        except Exception:
            pass
        r = self._self_loot
        how = r[0] if r and r[1] >= since else None
        if how == "all" and hasattr(self, "bw_looted") and self.facts.get("bw"):
            self.bw_looted(how)                                    # everything back: leave the corpse area (bw.py)
        return how

    # ---- casters: their own log reader and corpse run (CasterBot has no loop guard and no corpse rule) -------------------------------------------

    def recovery_tail(self):
        """Read the new [SYSTEM] lines of this bot's client log and hand them to recovery_line (BotBase gets them from loopguard.guard_client)."""
        import os
        root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
        path = os.path.join(root, "work", "navrey-sessions", self.name, "cuolog")
        try:
            size = os.path.getsize(path)
        except OSError:
            return
        pos = self.__dict__.get("_rec_pos")
        if pos is None or size < pos:
            self.__dict__["_rec_pos"] = size
            return
        if size == pos:
            return
        with open(path, "rb") as f:
            f.seek(pos)
            data = f.read(min(size - pos, 1_000_000))
            self.__dict__["_rec_pos"] = f.tell()
        for raw in data.decode("utf-8", "replace").splitlines():
            if "[NEAR] on damage:" in raw:
                try:
                    import deathsrc
                    deathsrc.near_feed(self, raw)                # who stood by when the caster was hit (patch_near_killer.py)
                except Exception:
                    pass
                continue
            i = raw.find("[SYSTEM] ")
            if i >= 0:
                try:
                    self.recovery_line(raw[i + 9:].strip())
                except Exception:
                    pass

    def recovery_corpse_run(self):
        """A caster's corpse run, only with blue_self_loot or materializing on: walk to the death spot, double-click the own corpse (one double-click takes
        everything back for a blue player), and take what is left item by item."""
        if not (self.feature("blue_self_loot") or self.feature("materializing")):
            return False
        info = self.facts.get("corpse")
        if not info or self.c.ghost or (info.get("tries", 0) >= 1 and not (hasattr(self, "bw_corpse_go") and self.bw_corpse_go() and not self.facts.get("far"))):
            return False
        if time.time() > self.corpse_deadline(info):
            self.facts.pop("corpse", None)
            return False
        if not self.materializing() and (self.hp_pct() < 60 or self.dangers(8)):
            return False
        info["tries"] = info.get("tries", 0) + 1
        x, y = info["xy"]
        self.activity = "going back for my corpse"
        res = self.far_goto((x, y), "corpse", 90, value=300) if hasattr(self, "far_goto") else self.c.goto(x, y).wait(timeout=90)
        if str(res).startswith(("moving", "interrupted")):
            info["tries"] = 0                                         # a far walk under way (r_far goes on with it): try again when there
            return True
        me = (self.name or "").lower()
        corpses = [i for i in self.c.containers(within=8) if "corpse" in (i.name or "").lower() and (me in (i.name or "").lower() or not (i.name or "").lower().startswith(("a ", "an ")))]
        if not corpses and hasattr(self, "ground_items"):
            try:                                          # turned to bones: not a container in the tile data, so containers() leaves it out
                corpses = [i for i in self.ground_items(8) if any(w in (i.name or "").lower() for w in ("bone", "remains", "corpse"))]
            except Exception:
                corpses = []
            if not corpses and info.get("serial"):
                from types import SimpleNamespace as _NS
                corpses = [_NS(serial=info["serial"], name="my corpse (kept serial)", x=x, y=y)]   # bones keep the corpse's serial
            if corpses:
                self.log(f"the corpse at {x},{y} has turned to bones ({corpses[0].name}): opening them")
        if not corpses:
            self.log(f"no corpse at {x},{y}: rotted away or not found")
            self.facts.pop("corpse", None)
            return True
        corpse = min(corpses, key=lambda i: max(abs(i.x - x), abs(i.y - y)))
        if max(abs(self.c.x - corpse.x), abs(self.c.y - corpse.y)) > 1:
            self.c.gotoexact(corpse.x, corpse.y).wait(timeout=8)
        used_at = time.time()
        self.c.events.drain()
        self.c.use(corpse.serial)
        time.sleep(1.5)
        how = self.self_loot_result(used_at) if self.feature("blue_self_loot") else None
        if how:
            self.dlog("ev", ev="self_loot", how=how, secs=round(time.time() - self.facts.get("mat_from", time.time())))
        if how != "all":
            try:
                for it in self.c.container(corpse.serial, timeout=5):
                    self.c.get_item(it.serial, it.amount if (it.amount or 0) > 1 else None)
                    time.sleep(1.2)
            except Exception as e:
                self.log(f"corpse run: {type(e).__name__}: {e}")
        if hasattr(self, "bw_looted") and self.facts.get("bw"):
            self.bw_looted(how or "item by item")                          # the Between Worlds record: the corpse was taken (bw.py)
        self.log(f"corpse run done ({how or 'item by item'})")
        self.facts.pop("corpse", None)
        return True
