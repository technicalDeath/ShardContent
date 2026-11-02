"""The bot-to-bot market deal as a py_trees behaviour tree (owner 2026-10-19: "Do it here" for the watcher's py_trees pilot, board item P12; feature "trade_tree").
The utility layer still decides WHAT to trade (market.py: offers, wants, matching, booking); this tree only EXECUTES a booked deal, one tick per brain tick.

Why (run 2026-10-18 22:12 - 2026-10-19 07:15): 749 deals failed and 23 completed. Read from the code and the events:
  * a failed deal was failed again every tick: mkt_fail recorded "fail" but did not refresh the shared memory, so deal_for kept returning the stale "agreed" deal
    (42 identical "seller has no stack of 21 iron ingot" in a row);
  * "buyer short of gold" (404): the buyer dropped gold from the FIRST gold pile in its pack, which can be smaller than the price while the pack holds enough;
  * a seller whose piles did not merge on the first try failed at once, every tick after;
  * neither side looked at the other: a deal the partner had given up kept one side waiting at the bank for the whole seven minutes.

The tree (root ticks once per brain tick; the deal state lives in facts["deals"][id], so a restarted brain resumes: every step checks before it acts):

    deal [Sequence, re-checked every tick]
      still agreed           condition: the shared memory says the deal is agreed, it is younger than DEAL_LIFE - 20 s, and the partner has not failed it
      steps [Sequence, resumes the running step]
        ready                seller: one pile holds the quantity (piles are merged onto the largest, up to MERGE_TRIES ticks);
                             buyer: the pack holds the price (gold fetched from the bank once when short; gold piles merged so one pile pays)
        at the meeting spot  walk to the deal's meeting spot (the bank spot)
        partner here         the other trader within 3 tiles
        window open          the secure-trade window with the partner (the seller drops the agreed quantity on the buyer, again every DROP_EVERY s)
        settled              both boxes right and accepted: the buyer puts the gold in from one pile; each accepts once the other box holds the agreed goods/gold;
                             SUCCESS when the window closes
        verified             counts: the seller's gold up by the price, the buyer's item count up by the quantity
A SUCCESS records "done" and the trade event; a FAILURE records "fail" ONCE (with the step and the reason), refreshes the shared memory, and the deal id is kept
in facts["deals_over"] so a stale "agreed" copy is never worked again. Events as before: trade {...}, deal_failed {id, with, item, why, role, step}.
"""
import time

import py_trees
from py_trees.common import Status

DEAL_LIFE = 420
MERGE_TRIES = 3
DROP_EVERY = 10
WALK_TIMEOUT = 6


class Ctx:
    """What every behaviour of one deal shares (the tree's blackboard, kept in a plain object: one brain per process, and the tests run many bots in one)."""

    def __init__(self, bot, d):
        self.bot, self.d = bot, d
        self.role = "seller" if d["seller"] == bot.name else "buyer"
        self.other = d["buyer"] if self.role == "seller" else d["seller"]
        self.qty, self.total, self.item = int(d.get("qty") or 1), int(d["price"]), d["item"]
        self.unit = d.get("unit") or (self.total // max(self.qty, 1))
        self.meet = tuple(d["meet"]) if d.get("meet") else tuple(bot.MEET)
        self.why, self.step = "", ""

    @property
    def st(self):
        """The deal's persisted state (facts are in BotBase.PERSIST): gold and count at the start, whether the window opened, the tries."""
        b = self.bot
        return b.facts.setdefault("deals", {}).setdefault(self.d["id"], {"gold0": b.c.gold, "n0": self.count(), "opened": False, "t0": time.time()})

    def count(self):
        b = self.bot
        if hasattr(b, "mkt_stacks"):
            try:
                return b.mkt_count(self.item)
            except KeyError:
                pass
        return sum((i.amount or 1) for i in b.c.backpack if i.name.lower() == self.item)

    def stacks(self):
        b = self.bot
        if self.d.get("serial"):
            return [i for i in b.c.backpack if str(i.serial) == str(self.d["serial"])]     # this very piece (a coloured one, colours.py)
        try:
            return b.mkt_stacks(self.item)
        except KeyError:
            return [i for i in b.c.backpack if i.name.lower() == self.item]

    def gold_piles(self):
        return sorted([i for i in self.bot.c.backpack if i.name.lower().startswith("gold coin")], key=lambda i: -(i.amount or 1))

    def window(self):
        tr = [t for t in self.bot.trades() if t["with"].startswith(self.other)]
        return tr[0] if tr else None

    def fail(self, step, why):
        self.step, self.why = step, why
        return Status.FAILURE


class Step(py_trees.behaviour.Behaviour):
    def __init__(self, name, ctx):
        super().__init__(name)
        self.ctx = ctx


class StillAgreed(Step):
    def update(self):
        c, b = self.ctx, self.ctx.bot
        try:
            b.mem.refresh()
            live = b.mem.state["world"]["market"]["deals"].get(c.d["id"], c.d)
        except Exception:
            live = c.d
        state = live.get("state", "agreed")
        if state == "done":
            return Status.SUCCESS                                   # the partner verified first: this side's own steps verify from its counts
        if state != "agreed":
            return c.fail(self.name, f"the {('buyer' if c.role == 'seller' else 'seller')} gave the deal up ({live.get('why') or state})")
        if time.time() - c.d["t"] > DEAL_LIFE - 20:
            return c.fail(self.name, f"{c.role} timed out ({'window opened' if c.st['opened'] else 'no window'})")
        return Status.SUCCESS


class Ready(Step):
    def update(self):
        c, b = self.ctx, self.ctx.bot
        st = c.st
        if c.st["opened"] or c.window():
            c.st["opened"] = True
            return Status.SUCCESS                                   # past this point already: a brain restarted mid-window, the goods are in the box
        if c.role == "seller":
            piles = c.stacks()
            if any((i.amount or 1) >= c.qty for i in piles):
                return Status.SUCCESS
            have = sum((i.amount or 1) for i in piles)
            if have < c.qty:
                b.mem.record("mkt", kind="unoffer", item=c.item)
                return c.fail(self.name, f"seller holds {have} {c.item}, the deal says {c.qty}")
            if st.get("merges", 0) >= MERGE_TRIES:
                return c.fail(self.name, f"seller's {c.item} stays in {len(piles)} piles after {MERGE_TRIES} merges ({[i.amount for i in piles][:5]})")
            piles.sort(key=lambda i: -(i.amount or 1))
            for extra in piles[1:]:
                b.c.drop(extra.serial, piles[0].serial, extra.amount or 1)
                time.sleep(0.7)
            st["merges"] = st.get("merges", 0) + 1
            b.log(f"trade tree: merged {len(piles)} piles of {c.item} (try {st['merges']})")
            return Status.RUNNING
        piles = c.gold_piles()
        carried = sum((i.amount or 1) for i in piles)
        if carried >= c.total and piles and (piles[0].amount or 1) >= c.total:
            return Status.SUCCESS
        if carried >= c.total:                                      # enough, but no single pile pays it: merge the piles onto the largest
            if st.get("gold_merges", 0) >= MERGE_TRIES:
                return Status.SUCCESS                               # settle drops from several piles
            for extra in piles[1:]:
                b.c.drop(extra.serial, piles[0].serial, extra.amount or 1)
                time.sleep(0.7)
            st["gold_merges"] = st.get("gold_merges", 0) + 1
            return Status.RUNNING
        bank = int(b.facts.get("bank_balance", 0) or 0)
        if bank >= c.total - carried and not st.get("banked"):
            st["banked"] = True
            b.activity = f"fetching {c.total - carried} gold for a trade with {c.other}"
            b.visit_bank("trade", withdraw=c.total - carried + 30, reserve=0)
            return Status.RUNNING
        return c.fail(self.name, f"buyer short: carried {carried}, bank {bank}, the deal says {c.total}")


class AtMeet(Step):
    def update(self):
        c, b = self.ctx, self.ctx.bot
        if max(abs(b.c.x - c.meet[0]), abs(b.c.y - c.meet[1])) <= 2:
            return Status.SUCCESS
        b.activity = f"walking to meet {c.other} to trade"
        b.c.goto(*c.meet).wait(timeout=WALK_TIMEOUT)
        return Status.RUNNING


class PartnerHere(Step):
    def update(self):
        c, b = self.ctx, self.ctx.bot
        if c.window() or any(m.name == c.other for m in b.c.mobiles(within=3)):
            return Status.SUCCESS
        b.activity = f"waiting for {c.other} at the bank"
        time.sleep(1.5)
        return Status.RUNNING


class WindowOpen(Step):
    def update(self):
        c, b = self.ctx, self.ctx.bot
        if c.window():
            c.st["opened"] = True
            return Status.SUCCESS
        if c.st["opened"]:
            return Status.SUCCESS                                   # opened and already closed: settled decides from the counts
        if c.role == "seller":
            them = next((m for m in b.c.mobiles(within=3) if m.name == c.other), None)
            pile = next((i for i in c.stacks() if (i.amount or 1) >= c.qty), None)
            if not pile:
                return c.fail(self.name, f"seller has no pile of {c.qty} {c.item} at the meeting")
            if them and time.time() - c.st.get("dropped_at", 0) >= DROP_EVERY:
                c.st["dropped_at"] = time.time()
                b.c.drop(pile.serial, them.serial, c.qty)
                time.sleep(2)
        else:
            time.sleep(1.5)
        return Status.RUNNING


class Settled(Step):
    def update(self):
        c, b = self.ctx, self.ctx.bot
        t = c.window()
        if not t:
            return Status.SUCCESS if c.st["opened"] else c.fail(self.name, "the window never opened")
        theirs = b.box_items(t["theirbox"])
        if c.role == "buyer":
            got = sum((i.amount or 1) for i in theirs if i.name.lower() == c.item)
            if got < c.qty:
                time.sleep(1.5)
                return Status.RUNNING
            mine_gold = sum((i.amount or 1) for i in b.box_items(t["mybox"]) if i.name.lower().startswith("gold"))
            if mine_gold < c.total:
                left = c.total - mine_gold
                piles = c.gold_piles()
                if sum((i.amount or 1) for i in piles) < left:
                    return c.fail(self.name, f"buyer short of gold in the window: {sum((i.amount or 1) for i in piles)} carried, {left} to put in")
                for p in piles:                                     # from as many piles as it takes (the old code used the first pile only)
                    n = min(left, p.amount or 1)
                    b.c.drop(p.serial, t["mybox"], n)
                    time.sleep(1.2)
                    left -= n
                    if left <= 0:
                        break
                return Status.RUNNING
            if not t["mine_ok"]:
                b.c.call(f"accepttrade {t['local']}", timeout=5)
        else:
            mine = sum((i.amount or 1) for i in b.box_items(t["mybox"]) if i.name.lower() == c.item)
            their_gold = sum((i.amount or 1) for i in theirs if i.name.lower().startswith("gold"))
            if mine != c.qty:
                return c.fail(self.name, f"my box holds {mine} {c.item}, the deal says {c.qty}")
            if their_gold >= c.total and not t["mine_ok"]:
                b.c.call(f"accepttrade {t['local']}", timeout=5)
        time.sleep(1.5)
        return Status.RUNNING


class Verified(Step):
    def update(self):
        c, b = self.ctx, self.ctx.bot
        st = c.st
        ok = (c.role == "seller" and b.c.gold >= st["gold0"] + c.total - 1) or (c.role == "buyer" and c.count() >= st["n0"] + c.qty)
        return Status.SUCCESS if ok else c.fail(self.name, f"{c.role}: the window closed without the goods")


def build(ctx):
    steps = py_trees.composites.Sequence("steps", memory=True, children=[
        Ready("ready", ctx), AtMeet("at the meeting spot", ctx), PartnerHere("partner here", ctx), WindowOpen("window open", ctx),
        Settled("settled", ctx), Verified("verified", ctx)])
    return py_trees.composites.Sequence("deal", memory=False, children=[StillAgreed("still agreed", ctx), steps])


def render(tree=None):
    """The tree as text (py_trees.display.unicode_tree), for the evidence."""
    if tree is None:
        tree = build(Ctx(type("B", (), {"name": "seller", "MEET": (0, 0), "facts": {}})(), {"id": "x", "seller": "seller", "buyer": "buyer", "item": "iron ingot", "price": 1}))
    return py_trees.display.unicode_tree(tree, show_status=False)


def tick(bot, d):
    """One tick of a deal as seller or buyer. Returns True while the deal owns the tick (also on the tick it ends); False for a deal already over here."""
    over = bot.facts.setdefault("deals_over", {})
    if d["id"] in over:
        return False                                                # a stale "agreed" copy of a deal this bot already finished or failed
    trees = bot.__dict__.setdefault("_trade_trees", {})
    entry = trees.get(d["id"])
    if entry is None:
        ctx = Ctx(bot, d)
        entry = trees[d["id"]] = (ctx, build(ctx))
    ctx, root = entry
    ctx.d = d
    _ = ctx.st                                                      # starting counts, before anything moves
    bot.activity = f"trading {ctx.qty} {ctx.item} with {ctx.other}"
    root.tick_once()
    if root.status == Status.RUNNING:
        return True
    now = time.time()
    if root.status == Status.SUCCESS:
        bot.mem.record("mkt", kind="done", id=d["id"], why="")
        bot.ev("trade", item=ctx.item, qty=ctx.qty, price=ctx.unit, total=ctx.total, role=ctx.role, tree=True, **{"with": ctx.other})
        bot.facts["trade_ok_at"] = now                   # (market.mkt_hold keeps holding while trades go through)
        bot.log(f"trade done (tree): {ctx.qty} {ctx.item} for {ctx.total} gold with {ctx.other}")
        bot.facts["deal_cool_until"] = now + getattr(bot, "COOL_OK", 300)
        if ctx.role == "buyer" and hasattr(bot, "wear_bought") and ctx.item not in __import__("market").ITEMS:
            bot.wear_bought(ctx.item)
    else:
        bot.mem.record("mkt", kind="fail", id=d["id"], why=ctx.why)
        bot.ev("deal_failed", id=d["id"], item=ctx.item, qty=ctx.qty, why=ctx.why, role=ctx.role, step=ctx.step, tree=True, **{"with": ctx.other})
        bot.log(f"trade {ctx.qty} {ctx.item} with {ctx.other} failed at '{ctx.step}': {ctx.why}")
        bot.facts["deal_cool_until"] = now + getattr(bot, "COOL_FAIL", 600)
        if ctx.st.get("opened") or ctx.step in ("window open", "settled"):
            bot.c.goto(bot.c.x + 8, bot.c.y + 8).wait(timeout=5)   # walk off: an open trade window closes when the traders part
    over[d["id"]] = now
    for k in [k for k, t in over.items() if now - t > 3600]:
        del over[k]
    bot.facts.get("deals", {}).pop(d["id"], None)
    trees.pop(d["id"], None)
    try:
        bot.mem.refresh(force=True)                                 # the failure is seen at once, here and by the partner (the old path re-failed every tick)
    except Exception:
        pass
    return True
