"""Splits holdable.tsv into the five item-writing areas. Run: python make_assignments.py"""
from pathlib import Path
import collections

HERE = Path(__file__).parent
rows = [l.rstrip("\n").split("\t") for l in (HERE / "holdable.tsv").read_text(encoding="utf-8").splitlines()]

W_BASES = {"BaseWeapon", "BaseQuiver"}
A_BASES = {"BaseArmor", "BaseClothing", "BaseJewel", "BaseTalisman", "BaseSuit", "BasePaintedMask", "ElvenGlasses", "BaseFormTalisman"}
T_BASES = {"BaseTool", "FishingPole", "BaseContainer", "Container", "Bag", "Backpack", "BaseBook", "SpellScroll", "Spellbook", "SpecialScroll", "MapItem",
           "BaseBOD", "BulkOrderBook", "Bandage", "BaseInstrument", "DyeTub", "BaseLight", "BaseEquipableLight", "BaseHarvestTool", "BaseBulletinBoard", "Clock"}
R_BASES = {"BaseOre", "BaseIngot", "BaseGranite", "Log", "Board", "BaseHides", "BaseLeather", "BaseScales", "BaseClothMaterial", "Food", "CookableFood",
           "BaseBeverage", "BaseFish", "BaseMagicFish", "BaseReagent", "BasePotion", "FarmableCrop", "Amber", "Wool", "BaseCraftmansSatchel_none"}

W_NAMES = {"Arrow", "Bolt", "CrossbowBolts"}
T_NAMES = {"Key", "KeyRing", "Lockpick", "Lockpicks", "Scissors", "Anvil", "Forge", "Bedroll", "Runebook", "RecallRune", "Sextant", "Spyglass", "ToolKit", "Rope",
           "Hourglass", "BlankScroll", "PenAndInk", "Dyes", "HairDye", "DisguiseKit", "TaxidermyKit", "WeaponEngravingTool", "Campfire", "Cauldron", "Globe",
           "Knife", "Fork", "Spoon", "KnifeLeft", "KnifeRight", "ForkLeft", "ForkRight", "SpoonLeft", "SpoonRight", "PotionKeg", "PlayingCards", "PlayingCards2",
           "Cards", "Cards2", "Cards3", "Cards4", "Dices", "Chessmen", "Chessmen2", "Chessmen3", "Checkers", "Checkers2", "GamblingStone", "SOS", "MessageInABottle",
           "Easel", "Dressform", "PaintsAndBrush", "Fukiya", "FukiyaDarts"}
R_NAMES = {"Cloth", "Cotton", "Flax", "UncutCloth", "BoltOfCloth", "Feather", "Shaft", "Bone", "Coal", "Sand", "Glass", "Silver", "Gold", "Beeswax", "Dough",
           "SweetDough", "SackFlour", "SackOfSugar", "Vanilla", "CocoaButter", "CocoaLiquor", "CocoaPulp", "Springs", "Axle", "AxleGears", "Gears", "Hinge", "Beads",
           "CopperWire", "GoldWire", "IronWire", "SilverWire", "Kindling", "Eggshells", "Fish", "BigFish", "Scales", "Plate", "Bottle", "GlassBottle", "EmptyVial",
           "ClockParts", "ClockFrame", "ClockworkAssembly", "SextantParts", "BarrelHoops", "BarrelLid", "BarrelStaves", "BarrelTap", "UnfinishedBarrel", "Vines",
           "Amethyst", "Citrine", "Diamond", "Emerald", "Ruby", "Sapphire", "StarSapphire", "Tourmaline", "Turquoise", "EcruCitrine", "BlueDiamond", "DarkSapphire",
           "FireRuby", "PerfectEmerald", "WhitePearl", "BrilliantAmber", "DriedHerbs", "DriedOnions", "WheatSheaf", "SheafOfHay", "Shell", "MeltedWax", "OilCloth",
           "OilFlask", "EmptyOilFlask", "JarHoney", "Acid", "Blood", "Web", "Dirt", "FertileDirt", "ForgedMetal", "Seed", "PowderOfTemperament", "PowderOfTranslocation",
           "Muculent", "TribalBerry", "OrangePetals", "RedLeaves", "WoodDebris", "WoodenBowl", "EmptyWoodenBowl", "EmptyWoodenTub", "EmptyPewterBowl", "EmptyPewterTub",
           "Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg", "RibCage", "BonePile", "DemonSkull", "HydraScale", "Eggshells", "EggBomb", "Firebomb", "SmokeBomb"}

areas = collections.defaultdict(list)
for name, ns, chain in rows:
    parts = set(chain.split(">")) if chain else set()
    parts.add(name)
    if parts & W_BASES or name in W_NAMES:
        area = "W"
    elif parts & A_BASES:
        area = "A"
    elif parts & T_BASES or name in T_NAMES:
        area = "T"
    elif parts & R_BASES or name in R_NAMES:
        area = "R"
    else:
        area = "M"
    areas[area].append((name, ns, chain))

out = HERE / "assign"
out.mkdir(exist_ok=True)
for area, items in sorted(areas.items()):
    (out / f"{area}.tsv").write_text("\n".join("\t".join(r) for r in sorted(items)) + "\n", encoding="utf-8")
    print(area, len(items))
