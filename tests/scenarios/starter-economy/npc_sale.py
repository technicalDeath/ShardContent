from pathlib import Path
import re,sys,time

root=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(root/'Navrey'/'cli'))
from uo import Client

def open_client(role):
    d=(root/'work'/'alpha3-starter-economy-clients'/role).resolve()
    c=Client(state_file=str(d/'state2.json'),world_file=str(d/'world2.json'),cmd_file=str(d/'cmd2.txt'),log_file=str(d/'client2.log'))
    c.require_live()
    if not c.state.get('inGame') or time.time()*1000-c.state.get('updatedAtMs',0)>=5000:
        raise RuntimeError(f'{role} has no fresh in-game state')
    return c,d

admin,admin_dir=open_client('admin')
player,player_dir=open_client('player1')
admin_log=admin_dir/'client2.log'
player_log=player_dir/'client2.log'
if player.state.get('charName')!='StarterSalvage':
    raise RuntimeError('ordinary test character is not StarterSalvage')
owner=player.state['charID']
before_gold=player.state['gold']
admin_start=len(admin_log.read_text(errors='replace').splitlines())
admin.call(f'say [StarterEconomyProbe npc {owner}',timeout=6)
deadline=time.time()+6
fixture=None
while time.time()<deadline:
    fixture=next((line for line in reversed(admin_log.read_text(errors='replace').splitlines()[admin_start:]) if 'Starter economy NPC targets:' in line),None)
    if fixture:
        break
    time.sleep(.1)
if not fixture:
    raise RuntimeError('server did not report NPC-sale fixture serials')
serials={key:'0x'+re.search(rf'{key}=(?:0x)?([0-9A-Fa-f]+)',fixture).group(1) for key in ('bound','ordinary','vendor')}
if not player.wait(lambda:all(any(i.serial==s for i in player.backpack) for s in (serials['bound'],serials['ordinary'])),timeout=6,poll=.1):
    raise RuntimeError('sale fixtures did not appear in the ordinary backpack')
location=re.search(r'location=\((\d+),\s*(\d+),',fixture)
px,py=int(location.group(1)),int(location.group(2))
if not player.wait(lambda:player.state['charPosX']==px and player.state['charPosY']==py,timeout=6,poll=.1):
    raise RuntimeError('player did not reach the spawned test Blacksmith')

player_start=len(player_log.read_text(errors='replace').splitlines())
player.call('say vendor sell',timeout=6)
deadline=time.time()+6
while time.time()<deadline and not any('[SHOP] Sell list from' in line for line in player_log.read_text(errors='replace').splitlines()[player_start:]):
    time.sleep(.1)
if not any('[SHOP] Sell list from' in line for line in player_log.read_text(errors='replace').splitlines()[player_start:]):
    raise RuntimeError('Blacksmith did not send a live NPC sell list')
listing=player.call('selllist',timeout=6)
print('NPC sell list',listing)
listing_text='\n'.join(listing)
if serials['bound'] in listing_text:
    raise RuntimeError('bound StarterIronIngot appeared in the NPC sell list')
if serials['ordinary'] not in listing_text:
    raise RuntimeError('ordinary IronIngot control was absent from the NPC sell list')
player.call(f"sell {serials['ordinary']} 2",timeout=6)
if not player.wait(lambda:player.state['gold']>before_gold and not any(i.serial==serials['ordinary'] for i in player.backpack),timeout=6,poll=.1):
    raise RuntimeError('ordinary ingots were listed but did not complete the NPC transaction')
if not any(i.serial==serials['bound'] for i in player.backpack):
    raise RuntimeError('bound StarterIronIngot left the ordinary backpack')
print('NPC sale=PASS; bound StarterIronIngot omitted and retained, ordinary IronIngot sold and gold increased')
