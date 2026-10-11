"""lay.py NAME            lay work/cosmetics/layouts/NAME.json in the world (items appear as plain statics; the host is thrown away unsaved)
   lay.py clear          remove what the last lay created
   lay.py walkgrid X Y W H   dump the server's walkable floor and items for the rectangle to work/cosmetics/walkgrid.json
"""
import sys

import rig

if len(sys.argv) >= 6 and sys.argv[1] == "walkgrid":
    print(rig.walkgrid(*[int(v) for v in sys.argv[2:6]]))
elif len(sys.argv) == 2:
    rig.lay(sys.argv[1])
    print("laid", sys.argv[1])
else:
    print(__doc__)
