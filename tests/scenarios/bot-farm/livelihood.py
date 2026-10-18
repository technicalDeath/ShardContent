"""Fighters' livelihood (G13 + G10; Watcher item 2026-10-17; the Helper), behind the feature "livelihood".

Finding (live tree, 2026-10-17): looting, carving of animals, the sale of looted weapons/armour (r_sellgear) and of meat (r_sellmeat) already exist. What did not:
 * gems were looted only if the corpse held a name on a short list ("amethyst" and "star sapphire" were not on it) and then sat in the pack or the bank for ever:
   no rule sold them, and a Jeweler pays 25-100 gold for one (Amber 25, Citrine 25, Ruby 37, Tourmaline 47, Emerald 50, Sapphire 50, Amethyst 50, Star Sapphire 62, Diamond 100),
   several kills' worth of gold. r_sellloot sells gems (and jewellery) to the Jeweler the shared memory knows (else the gazetteer's), when their worth is 100 gold or more, or
   twenty minutes after the last sale of loot with some in the pack, or the fighter is down to its last 60 gold.
 * hunger has no effect in this server (Misc/FoodDecay.cs only counts it down), so no eating rule is built; carving other than animals only makes body parts and is left alone.
Event: loot_sold {items, gold}.
"""
import time

GEM_PRICE = {"star sapphire": 62, "amber": 25, "citrine": 25, "ruby": 37, "tourmaline": 47, "emerald": 50, "sapphire": 50, "amethyst": 50, "diamond": 100}
JEWELRY = ("ring", "necklace", "bracelet", "earring", "beads")
SELL_AT = 100


class LivelihoodMixin:
    def loot_for_sale(self):
        out = []
        for i in self.c.backpack:
            n = i.name.lower()
            if any(g in n for g in GEM_PRICE) and "ringmail" not in n:
                out.append(i)
        return out

    def loot_worth(self, items):
        total = 0
        for i in items:
            n = i.name.lower()
            price = next((p for g, p in GEM_PRICE.items() if g in n), 10)
            total += price * (i.amount or 1)
        return total

    def r_sellloot(self):
        if not self.feature("livelihood") or self.c.ghost or self.mobs(10):
            return False
        now = time.time()
        if now - self.facts.get("loot_sold_at", 0) < 300:
            return False
        items = self.loot_for_sale()
        if not items:
            return False
        worth = self.loot_worth(items)
        if worth < SELL_AT and self.c.gold >= 60 and not self.sale_due("loot_sold_at"):
            return False
        self.facts["loot_sold_at"] = now
        self.activity = "selling gems"
        words = sorted({self.gem_word(i) for i in items})
        shops = []
        for n in words:
            for p, xy, item in self.mem.vendor_buying(n):
                pt = tuple(int(v) for v in xy.split(","))
                if p > 0 and pt not in shops:
                    shops.append(pt)
        shops += [xy for xy in self.find_places(("jeweler",), n=2, per=1) if xy not in shops]
        gold0 = self.c.gold
        for xy in shops[:3]:
            left = self.loot_for_sale()
            if not left:
                break
            self.sell_items(xy, sorted({self.gem_word(i) for i in left}))
        earned = self.c.gold - gold0
        self.ev("loot_sold", items=[i.name for i in items][:8], gold=earned, worth=worth)
        self.dlog("choice", what="sell gems", why=f"{len(items)} items worth about {worth}, got {earned}")
        return True

    @staticmethod
    def gem_word(item):
        n = item.name.lower()
        return next((g for g in GEM_PRICE if g in n), n)
