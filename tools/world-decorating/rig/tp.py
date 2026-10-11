"""tp.py X Y Z   move the camera character (see rig.tp for why the staff character visits it first)"""
import sys

import rig

if len(sys.argv) != 4:
    print(__doc__)
    sys.exit(2)
rig.tp(*[int(v) for v in sys.argv[1:4]])
print("camera at", sys.argv[1:4])
