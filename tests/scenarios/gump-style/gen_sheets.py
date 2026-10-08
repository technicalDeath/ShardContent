"""Generates gump scripts (.gs) for the sampler: python gen_sheets.py"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def write(name, lines):
    with open(os.path.join(HERE, name + ".gs"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def backgrounds(name, ids, cols=6, w=118, h=84, gap=8, title="Backgrounds (AddBackground, art id to id+8)"):
    rows = (len(ids) + cols - 1) // cols
    W = cols * (w + gap) + gap
    H = rows * (h + gap + 18) + gap + 30
    out = ["pos 20 20", f"tile 0 0 {W} {H} 2624", f'html 8 6 {W-16} 20 "{title}" color=#FFD060 size=4']
    for i, bid in enumerate(ids):
        c, r = i % cols, i // cols
        x = gap + c * (w + gap)
        y = 30 + r * (h + gap + 18)
        out.append(f"bg {x} {y} {w} {h} {bid}")
        out.append(f'html {x+10} {y+10} {w-20} 18 "{bid}" color=#FFFFFF size=3 style=1')
        out.append(f'html {x+10} {y+34} {w-20} 18 "Sample text" color=#BBBBBB')
        out.append(f'html {x+10} {y+52} {w-20} 18 "Gold heading" color=#FFD060')
    write(name, out)


def arts(name, ids, cols=8, cell=84, title="Art (AddImage at natural size)"):
    rows = (len(ids) + cols - 1) // cols
    W = cols * cell + 16
    H = rows * cell + 40
    out = ["pos 20 20", f"tile 0 0 {W} {H} 2624", f'html 8 6 {W-16} 20 "{title}" color=#FFD060 size=4']
    for i, aid in enumerate(ids):
        c, r = i % cols, i // cols
        x = 8 + c * cell
        y = 30 + r * cell
        out.append(f"img {x} {y+14} {aid}")
        out.append(f'html {x} {y} {cell} 14 "{aid}" color=#8FD3FF size=1')
    write(name, out)


if __name__ == "__main__":
    backgrounds("bg1", [9200, 9250, 9260, 9270, 9300, 9350, 9380, 9390, 9400, 9450, 9500, 9550,
                        5054, 2620, 2600, 2610, 3000, 3500, 5100, 2520, 2500, 30546, 40000, 30536])
    backgrounds("bg2", [9300, 9310, 9320, 9330, 9340, 9360, 9370, 9380, 9390, 9410, 9420, 9430,
                        9440, 9460, 9470, 9480, 9490, 9510, 9520, 9530, 9540, 9560, 9570, 9580])
    arts("arts_buttons1", list(range(4000, 4032)), title="Buttons 4000-4031")
    arts("arts_buttons2", list(range(2440, 2472)), title="Buttons 2440-2471")
    arts("arts_buttons3", [2084, 2085, 2086, 2087, 2088, 2089, 2151, 2152, 2153, 2154, 2360, 2361, 2362, 2363, 2460, 2461, 9721, 9722, 9723, 9724, 9725, 9726, 5200, 5201, 5202, 5203, 5204, 5205, 1209, 1210, 208, 209, 210, 211, 212, 213, 250, 251, 252, 253, 255, 256, 5826, 5827, 5828, 5829, 5830, 5831, 5832, 5833], title="Buttons and choices, assorted")
    arts("arts_misc1", list(range(5000, 5034)), title="5000-5033: tabs, borders, bars")
    arts("arts_misc2", [57, 58, 90, 91, 92, 93, 95, 96, 97, 98, 99, 2700, 2701, 2702, 2703, 2704, 2705, 2706, 2707, 2708, 2709, 2710, 2711, 2712, 1141, 1142, 1143, 1144, 1145, 1146, 1147, 1148], cols=8, title="Dividers, rules and ornaments")
