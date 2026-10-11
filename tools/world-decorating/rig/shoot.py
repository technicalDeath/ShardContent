"""shoot.py OUT_DIR --site SITE.json [--only door,west]     one cropped real-client shot per camera spot of the site config ("cameraSpots")
   shoot.py OUT_DIR --spot name=x,y,z [--spot ...]       or explicit spots

Each spot teleports the camera character there (the client centres the view on it), waits for the world to draw, and saves OUT_DIR/<name>.png.
Look at every shot yourself before showing anything (skill player-client-shots).
"""
import json
import os
import sys

import rig


def main(a):
    if len(a) < 2:
        print(__doc__)
        return 2
    out = a[0]
    spots = {}
    if "--site" in a:
        spots.update(json.load(open(a[a.index("--site") + 1], encoding="utf-8"))["cameraSpots"])
    for i, v in enumerate(a):
        if v == "--spot":
            n, c = a[i + 1].split("=")
            spots[n] = [int(t) for t in c.split(",")]
    if "--only" in a:
        keep = a[a.index("--only") + 1].split(",")
        spots = {k: v for k, v in spots.items() if k in keep}
    for name, c in spots.items():
        rig.tp(*c)
        import time
        time.sleep(3)
        print("shot", rig.shot(name, out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
