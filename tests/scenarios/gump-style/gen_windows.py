"""Writes the proposal windows as .gs scripts with the button kinds of Gump-Style-Guide.md section 3.2:  python gen_windows.py

One family of ovals told apart by colour: purple for a game action (chosen by the owner 2026-10-07), blue for a menu action, and the classic
green OKAY and red CANCEL for answering a question.
Files: ref, mockStatus, mockConfirm, mockBank, buttons.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

BLUE = {56: 62010, 88: 62012, 128: 62014, 176: 62016, 232: 62018}        # menu action, 21 px tall
PURPLE = {56: 62020, 88: 62022, 128: 62024, 176: 62026, 232: 62028}      # game action, purple, 21 px tall
CHOSEN = {22: 62030}      # the chosen one of a pick-one group: a purple 22 px oval, a picture
STONE = {22: 62040}       # the others in the group: a dull stone 22 px oval, a button


def oval(x, y, width, text, bid, family=BLUE):
    art = family[width]
    return [
        f"button {x} {y} {art} {art + 1} {bid}",
        f'html {x + 1} {y + 3} {width} 18 "{text}" color=#101010 align=center',
        f'html {x} {y + 2} {width} 18 "{text}" color=#FFFFFF align=center',
    ]


def pill(x, y, text, selected, bid, label_width=80, chosen_ink="#D9B8FF"):
    """One choice of a pick-one group, drawn like a standard radio button: a small empty oval with the label beside it.
    The chosen oval is purple (a picture, it does nothing); the others are dull stone buttons. The chosen label is lavender."""
    if selected:
        return [f"img {x} {y} {CHOSEN[22]}", f'html {x + 30} {y + 2} {label_width} 18 "{text}" color={chosen_ink}']
    return [f"button {x} {y} {STONE[22]} {STONE[22] + 1} {bid}", f'html {x + 30} {y + 2} {label_width} 18 "{text}" color=#BBBBBB']


def game_action(x, y, text, bid, size):
    """size: 's' a short word, 'm' a phrase, 'l' a sentence."""
    return oval(x, y, {"s": 88, "m": 128, "l": 176}[size], text, bid, PURPLE)


def okay_cancel(x_ok, x_cancel, y, ok_id=1, cancel_id=0):
    return [f"button {x_ok} {y} 2450 2451 {ok_id}", f"button {x_cancel} {y} 2453 2454 {cancel_id}"]


def write(name, lines):
    open(os.path.join(HERE, name + ".gs"), "w", encoding="utf-8").write("\n".join(lines) + "\n")


def frame(w, h, title, subtitle, title_color="#FFD060", pos="pos 20 40"):
    return [
        pos, f"bg 0 0 {w} {h} 9200", f"tile 10 10 {w - 20} {h - 20} 2624",
        f'html 20 16 {w - 40} 24 "{title}" color={title_color} size=5 align=center',
        f'html 20 46 {w - 40} 18 "{subtitle}" color=#BBBBBB align=center',
        f"tile 28 70 {w - 56} 4 2700",
    ]


def slate(lines, w, h, tile):
    return [l.replace(f"bg 0 0 {w} {h} 9200", f"bg 0 0 {w} {h} 9270") for l in lines if not l.startswith(f"tile 10 10 {tile}")]


def make_ref():
    ref = frame(640, 480, "Window title", "One line saying what this window is for")
    ref += [
        "img 34 82 5826", 'html 72 86 250 20 "Done: saved your choice." color=#8FE08F',
        "img 330 82 5830", 'html 368 86 250 20 "Danger: you are exposed." color=#FF7B7B',
        "img 34 116 2151", 'html 72 120 250 20 "Note: nothing to show yet." color=#8FD3FF',
        'html 34 156 280 20 "Section heading" color=#FFD060', "tile 34 178 280 3 96",
        'html 34 188 280 36 "Body text is near white, left aligned, about fifty characters a line." color=#F2F2F2',
        'html 34 226 280 18 "Secondary text, muted." color=#BBBBBB',
        'html 34 246 280 18 "Footnote or hint, dim." color=#999999',
        'html 34 266 280 18 "[Command" color=#8FD3FF', 'html 120 266 200 18 "Number 96.0" color=#FFD060',
        'html 34 296 280 20 "Skill" color=#BBBBBB', 'html 214 296 100 20 "Points" color=#BBBBBB align=right', "tile 34 316 280 3 96",
        'html 34 324 170 20 "Swordsmanship" color=#F2F2F2', 'html 214 324 100 20 "96.0" color=#F2F2F2 align=right', "tile 34 346 280 3 96",
        'html 34 354 170 20 "Anatomy" color=#F2F2F2', 'html 214 354 100 20 "88.5" color=#F2F2F2 align=right', "tile 34 376 280 3 96",
        'html 34 386 280 18 "<B><BASEFONT COLOR=#8FE08F>||||||||||||||||||||||||||||||||||||</BASEFONT><BASEFONT COLOR=#555555>||||||||||||||||||||||||||||||||</BASEFONT></B>" color=#FFFFFF',
        f'html 340 156 270 20 "Game action: purple oval" color=#FFD060', "tile 340 178 270 3 96",
    ]
    ref += game_action(340, 186, "Turn Criminal Intent on", 1, "l")
    ref += ['html 340 214 270 20 "Menu action: blue oval" color=#FFD060', "tile 340 236 270 3 96"]
    ref += oval(340, 246, 56, "Back", 2) + ['html 408 248 80 18 "Page 1 of 2" color=#BBBBBB align=center'] + oval(494, 246, 56, "Next", 3)
    ref += ['html 340 278 270 20 "Accept or decline: green and red ovals" color=#FFD060', "tile 340 300 270 3 96"]
    ref += okay_cancel(340, 410, 310, 4, 5)
    ref += [
        'html 340 340 270 20 "Choices" color=#FFD060', "tile 340 362 270 3 96",
        "check 340 370 210 211 1 1", 'html 368 372 240 20 "Ticked: ask me before I travel" color=#F2F2F2',
        "check 340 392 210 211 0 2", 'html 368 394 240 20 "Not ticked" color=#F2F2F2',
        "tile 28 418 584 4 2700",
        'html 34 436 340 20 "Type [Command to do this without the window." color=#999999',
    ]
    ref += oval(548, 432, 56, "Close", 0)
    return ref


def make_status():
    status = frame(480, 340, "Criminal Intent", "Whether other players may fight you")
    status += [
        "img 30 84 5826", 'html 70 88 380 22 "Intent is OFF: you are protected." color=#8FE08F',
        'html 30 126 420 120 "Other players cannot attack you unless you break the law or are already fighting them, except in a Hot Zone.<BR><BR>Criminal Intent does not make you a criminal: guards will not attack you, and you can still use Recall and gates, until you commit a criminal act such as stealing." color=#F2F2F2',
    ]
    status += game_action(30, 249, "Turn Criminal Intent on", 1, "l")
    status += ["tile 28 292 424 4 2700", 'html 34 306 300 20 "Type [Intent to do this without the window." color=#999999']
    status += oval(392, 300, 56, "Close", 0)
    return status


def make_bank():
    bank = frame(640, 500, "Skill Bank", "Skill points a Down skill gave up, saved so you can earn them back")
    bank += [
        "img 34 80 5826", 'html 72 86 540 20 "Done: Anatomy is now Locked, so its banked points are safe." color=#8FE08F',
        'html 34 124 300 20 "Banked  12.4 of 300.0 points" color=#F2F2F2',
        'html 34 146 300 18 "<B><BASEFONT COLOR=#FFD060>||||</BASEFONT><BASEFONT COLOR=#555555>||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||</BASEFONT></B>" color=#FFFFFF',
        'html 370 124 240 56 "Set a skill to Up and train it: every use brings back 0.2 from the bank." color=#BBBBBB',
        'html 34 184 170 18 "Skill" color=#BBBBBB', 'html 190 184 60 18 "Now" color=#BBBBBB align=right',
        'html 256 184 60 18 "Banked" color=#BBBBBB align=right', 'html 330 184 100 18 "Setting" color=#BBBBBB',
        'html 520 184 88 18 "Banked points" color=#BBBBBB align=center', "tile 28 204 584 3 96",
    ]
    rows = [("Swordsmanship", "96.0", "6.2", 0, 1), ("Anatomy", "88.5", "4.0", 1, 0), ("Evaluating Intelligence", "74.2", "2.2", 0, 1)]
    for i, (name, now, banked, locked, down) in enumerate(rows):
        y = 214 + i * 36
        bank += [
            f'html 34 {y} 160 20 "{name}" color=#F2F2F2', f'html 190 {y} 60 20 "{now}" color=#BBBBBB align=right',
            f'html 256 {y} 60 20 "{banked}" color=#FFD060 align=right',
        ]
        bank += pill(330, y - 4, "Locked", locked, 30 + i, 60) + pill(426, y - 4, "Down", down, 40 + i, 50)
        bank += game_action(520, y - 4, "Discard", 20 + i, "s")
        bank += [f"tile 28 {y + 26} 584 3 96"]
    bank += [
        'html 34 326 570 54 "Locked keeps a skill\'s banked points safe and stops it giving any up. Down lets it give points up when another skill gains, and banks them. Discard throws the banked points away for good." color=#999999',
        "tile 28 440 584 4 2700", 'html 34 456 300 20 "Type [SkillBank to open this window." color=#999999',
    ]
    bank += oval(292, 452, 56, "Back", 11) + ['html 356 456 96 20 "Page 1 of 2" color=#BBBBBB align=center'] + oval(460, 452, 56, "Next", 12)
    bank += oval(548, 452, 56, "Close", 0)
    return bank


# ---- the windows
ref = make_ref()
write("ref", ref)
write("mockStatus", make_status())
bank = make_bank()
write("mockBank", bank)

# ---- the Hot Zone confirm
confirm = frame(440, 300, "Hot Zone Warning", "Buccaneer's Den island is a PvP zone", "#FF7B7B")
confirm += [
    "img 30 84 5830",
    'html 70 84 350 56 "Danger: other players can attack you there, and your Backpack Ward and Loot Protection do not work in a Hot Zone." color=#FF7B7B',
    'html 30 150 380 40 "Recall will take you there. You can turn this warning off for good below, or later with [TravelWarning off." color=#F2F2F2',
    "check 30 200 210 211 0 1", 'html 62 202 340 20 "Do not warn me again when travelling" color=#BBBBBB',
    "tile 28 238 384 4 2700",
]
confirm += okay_cancel(130, 250, 252, 1, 0)
write("mockConfirm", confirm)

# ---- every kind of button
kinds = frame(640, 500, "Button kinds", "Every button is an oval; its colour says what it does")
kinds += ['html 34 84 570 20 "Purple: a game action, something that changes the game" color=#FFD060']
kinds += game_action(34, 108, "Turn Criminal Intent on", 1, "l") + game_action(250, 108, "Discard points", 2, "m")
kinds += game_action(394, 108, "Travel", 3, "s") + game_action(492, 108, "Discard", 4, "s")
kinds += ['html 34 148 570 20 "Blue: a menu action, moving around the windows (Close, Back, Next, window links)" color=#FFD060']
kinds += oval(34, 172, 56, "Close", 5) + oval(104, 172, 56, "Back", 6) + oval(174, 172, 56, "Next", 7)
kinds += oval(250, 172, 128, "How it works", 8) + oval(392, 172, 128, "Skill speeds", 9)
kinds += ['html 34 212 570 20 "Green and red: answering a question the window asked" color=#FFD060']
kinds += okay_cancel(34, 100, 236, 10, 11)
kinds += ['html 34 278 570 20 "In place" color=#FFD060']
kinds += ["bg 34 304 280 180 9200", "tile 44 314 260 160 2624", 'html 44 320 260 20 "Criminal Intent" color=#FFD060 align=center',
          "img 54 350 5826", 'html 90 354 200 20 "Intent is OFF" color=#8FE08F']
kinds += game_action(54, 392, "Turn Criminal Intent on", 12, "l")
kinds += ["tile 50 432 248 3 2700", 'html 54 444 150 18 "Type [Intent instead." color=#999999'] + oval(232, 440, 56, "Close", 0)
kinds += ["bg 330 304 290 180 9200", "tile 340 314 270 160 2624", 'html 340 320 270 20 "Leave the safe world?" color=#FFD060 align=center',
          'html 346 350 260 40 "Other players can attack you there." color=#FFFFFF', 'html 346 390 260 20 "Your Backpack Ward does not work there." color=#FFFFFF']
kinds += okay_cancel(366, 520, 440, 13, 14)
write("buttons", kinds)

# ---- the pick-one choice: small ovals with the label beside them
pick = frame(640, 500, "Pick-one choices", "A small oval with the label beside it, like a standard radio button")
pick += ['html 34 84 570 20 "Skill Bank: Locked or Down" color=#FFD060']
for i, (name, locked) in enumerate((("Swordsmanship", 0), ("Anatomy", 1))):
    y = 112 + i * 30
    pick += [f'html 34 {y + 2} 160 20 "{name}" color=#F2F2F2'] + pill(220, y, "Locked", locked, 10 + i, 60) + pill(330, y, "Down", not locked, 20 + i, 50)
pick += ['html 34 184 570 20 "The chosen label in white instead of lavender" color=#FFD060']
for i, (name, locked) in enumerate((("Swordsmanship", 0), ("Anatomy", 1))):
    y = 212 + i * 30
    pick += [f'html 34 {y + 2} 160 20 "{name}" color=#F2F2F2'] + pill(220, y, "Locked", locked, 30 + i, 60, "#FFFFFF") + pill(330, y, "Down", not locked, 40 + i, 50, "#FFFFFF")
pick += ['html 34 284 570 20 "Three choices (a skill lock: Up, Down, Locked) and a longer group" color=#FFD060']
pick += pill(34, 312, "Up", 0, 50, 40) + pill(140, 312, "Down", 1, 51, 50) + pill(250, 312, "Locked", 0, 52, 60)
pick += pill(34, 346, "Ask me before I travel", 1, 53, 220) + pill(34, 374, "Warn me only the first time", 0, 54, 220) + pill(34, 402, "Never warn me", 0, 55, 220)
pick += ["tile 28 440 584 4 2700", 'html 34 456 300 20 "Click the oval; the label is not a button." color=#999999']
pick += oval(548, 452, 56, "Close", 0)
write("radioPick", pick)
print("ok")
