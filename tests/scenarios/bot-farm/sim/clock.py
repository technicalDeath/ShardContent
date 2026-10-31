"""Virtual time for the simulator: the brains call time.time() and time.sleep() everywhere, so the simulator replaces both in the `time` module.

Every bot runs in its own thread, but only one thread runs at a time: a thread that calls time.sleep(d) hands the baton back to the scheduler, which
advances the world to the earliest wake-up, hands the baton to that thread, and waits until it sleeps again. Deterministic, no races, and ten simulated
hours of fifty bots take minutes: a sleep costs a thread switch, not the wait.

    clock = VirtualClock(start_epoch)
    clock.install()                          # patches time.time, time.monotonic, time.sleep for every thread of this process
    actor = clock.spawn(fn, name)            # a thread that runs fn() under the clock
    clock.run(until, on_advance=world.step)  # the scheduler loop; on_advance(dt) is called before time moves

A thread that is not a registered actor (the main thread, a C thread) gets a real sleep of 0 and the virtual time.
"""
from __future__ import annotations

import heapq
import threading
import time as _time

_real_time, _real_monotonic, _real_sleep = _time.time, _time.monotonic, _time.sleep


class Actor:
    __slots__ = ("name", "thread", "wake", "yielded", "done", "seq", "clock")

    def __init__(self, clock, name):
        self.clock = clock
        self.name = name
        self.thread = None
        self.wake = threading.Event()        # set by the scheduler: run
        self.yielded = threading.Event()     # set by the actor: I sleep (or finished)
        self.done = False
        self.seq = 0


class VirtualClock:
    def __init__(self, start: float):
        self.now = float(start)
        self.heap = []                       # (wake time, seq, actor)
        self.seq = 0
        self.local = threading.local()
        self.actors = []
        self.installed = False
        self.switches = 0

    # ---- the time module -------------------------------------------------------------------------------------------------------------------------

    # a state read costs the real client 0.07 ms; charging every clock read a little means a loop that only reads state and time (no command, no sleep)
    # still reaches its deadline instead of spinning for ever in zero time
    READ_COST = 0.0002

    def time(self):
        if getattr(self.local, "actor", None) is not None:
            self.now += self.READ_COST
        return self.now

    def monotonic(self):
        return self.time()

    def sleep(self, d):
        actor = getattr(self.local, "actor", None)
        if actor is None:
            return _real_sleep(0)              # not a simulated thread: nothing to wait for
        self.seq += 1
        heapq.heappush(self.heap, (self.now + max(float(d), 0.001), self.seq, actor))
        actor.yielded.set()
        actor.wake.wait()
        actor.wake.clear()

    def install(self):
        if not self.installed:
            _time.time, _time.monotonic, _time.sleep = self.time, self.monotonic, self.sleep
            self.installed = True

    def uninstall(self):
        if self.installed:
            _time.time, _time.monotonic, _time.sleep = _real_time, _real_monotonic, _real_sleep
            self.installed = False

    # ---- actors ---------------------------------------------------------------------------------------------------------------------------------

    def spawn(self, fn, name, start_in=0.0):
        actor = Actor(self, name)

        def body():
            self.local.actor = actor
            actor.wake.wait()
            actor.wake.clear()
            try:
                fn()
            finally:
                actor.done = True
                actor.yielded.set()

        actor.thread = threading.Thread(target=body, name=name, daemon=True)
        self.actors.append(actor)
        self.seq += 1
        heapq.heappush(self.heap, (self.now + start_in, self.seq, actor))
        actor.thread.start()
        return actor

    def run(self, until: float, on_advance=None, step=1.0, on_wake=None):
        """The scheduler: until the clock reaches `until` or every actor is done. on_advance(dt) runs for every world step (at most `step` seconds)."""
        while self.heap and self.now < until:
            wake, _, actor = heapq.heappop(self.heap)
            if actor.done:
                continue
            wake = min(wake, until)
            while self.now < wake:
                dt = min(step, wake - self.now)
                if on_advance is not None:
                    on_advance(dt)
                self.now += dt
            self.switches += 1
            actor.yielded.clear()
            actor.wake.set()
            actor.yielded.wait()
            if on_wake is not None:
                on_wake(actor)
        return self.now


def real_time():
    return _real_time()
