from pathlib import Path
import sys,time
root=Path(sys.argv[1]).resolve();sys.path.insert(0,str(root/'Navrey'/'cli'))
from uo import Client

def open_client(role):
 d=(root/'work'/'alpha3-starter-economy-clients'/role).resolve()
 c=Client(state_file=str((d/'state2.json').resolve()),world_file=str((d/'world2.json').resolve()),cmd_file=str((d/'cmd2.txt').resolve()),log_file=str((d/'client2.log').resolve()))
 c.require_live()
 return c

p1=open_client('player1')
ordinary='0x40079ED6'
if not any(i.serial==ordinary for i in p1.backpack):
 vendor_bags=[c for c in p1.world.get('containers',[]) if c.get('name')=='backpack' and c.get('serial')!='0x40079EA6']
 if not vendor_bags: raise RuntimeError('owner vendor stock backpack is not visible')
 p1.call('container '+vendor_bags[0]['serial'],timeout=8)
 time.sleep(.4)
 p1.call('get '+ordinary,timeout=8)
 if not p1.wait(lambda:any(i.serial==ordinary for i in p1.backpack),timeout=8,poll=.1):
  raise RuntimeError('ordinary Katana was not retrieved from player-vendor stock')
print('ordinary player-vendor withdrawal=PASS; owner backpack contains '+ordinary)
