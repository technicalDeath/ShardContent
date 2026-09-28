from pathlib import Path
import sys,time
root=Path(sys.argv[1]).resolve();sys.path.insert(0,str(root/'Navrey'/'cli'))
from uo import Client

def open_client(role):
 d=(root/'work'/'alpha3-starter-economy-clients'/role).resolve()
 c=Client(state_file=str((d/'state2.json').resolve()),world_file=str((d/'world2.json').resolve()),cmd_file=str((d/'cmd2.txt').resolve()),log_file=str((d/'client2.log').resolve()))
 c.require_live()
 if not c.state.get('inGame') or time.time()*1000-c.state.get('updatedAtMs',0)>=5000: raise RuntimeError(f'{role} stale/out of game')
 return c
p1,p2=map(open_client,['player1','player2'])
char1=p1.state['charID']; char2=p2.state['charID']; vendor='0x0001C59C'; ordinary='0x40079ED6'; nested='0x40079F99'
assert p1.state.get('weight') < p1.state.get('maxWeight')

def no_trade(c, label):
 lines=c.call('trades',timeout=5)
 if not any('No secure-trade windows open' in x for x in lines): raise RuntimeError(f'{label}: expected no trade window, got {lines}')

def direct_trade(label, serial, amount=None):
 if not any(i.serial==serial for i in p1.backpack): raise RuntimeError(f'{label}: not in owner backpack before attempt')
 p1.drop(serial,char2,amount)
 if not p1.wait(lambda:any(i.serial==serial for i in p1.backpack),timeout=6,poll=.1): raise RuntimeError(f'{label}: did not remain/return to owner backpack')
 if any(i.serial==serial for i in p2.backpack): raise RuntimeError(f'{label}: appeared in recipient backpack')
 no_trade(p1,label)
 print(label+' direct_trade=PASS')
 time.sleep(1.2)

def direct_vendor(label, serial, amount=None):
 if not any(i.serial==serial for i in p1.backpack): raise RuntimeError(f'{label}: not in owner backpack before vendor attempt')
 p1.drop(serial,vendor,amount)
 if not p1.wait(lambda:any(i.serial==serial for i in p1.backpack),timeout=6,poll=.1): raise RuntimeError(f'{label}: did not remain/return to owner backpack')
 print(label+' direct_vendor=PASS')
 time.sleep(1.2)

for label,serial,amount in [
 ('StarterBag','0x40079ED0',None),
 ('StarterScissors','0x40079ED1',None),
 ('StarterIronIngot full stack','0x40079ED2',10),
 ('StarterTinkerTools','0x40079ED3',None),
 ('StarterKatana','0x40079ED4',None),
 ('marked BackpackWard','0x40079ED5',None),
]:
 direct_trade(label,serial,amount)

# An ordinary wrapper containing a bound starter ingot must fail before a trade opens.
assert any(i.serial==nested for i in p1.backpack)
p1.drop(nested,char2)
if not p1.wait(lambda:any(i.serial==nested for i in p1.backpack),timeout=6,poll=.1): raise RuntimeError('nested wrapper did not remain in owner backpack')
no_trade(p1,'nested bound contents')
print('ordinary wrapper with nested bound ingot secure_trade=PASS blocked')
time.sleep(1.2)

for label,serial,amount in [
 ('StarterBag','0x40079ED0',None),
 ('StarterScissors','0x40079ED1',None),
 ('StarterIronIngot full stack','0x40079ED2',10),
 ('StarterTinkerTools','0x40079ED3',None),
 ('StarterKatana','0x40079ED4',None),
 ('marked BackpackWard','0x40079ED5',None),
]:
 direct_vendor(label,serial,amount)

# Player-vendor intake must also reject an ordinary wrapper with bound contents.
p1.drop(nested,vendor)
if not p1.wait(lambda:any(i.serial==nested for i in p1.backpack),timeout=6,poll=.1): raise RuntimeError('nested wrapper did not remain in owner backpack after player-vendor attempt')
print('ordinary wrapper with nested bound ingot player_vendor=PASS blocked')
time.sleep(1.2)

# Ordinary output remains secure-trade eligible and settles on the recipient after both accepts.
p1.drop(ordinary,char2)
for _ in range(30):
 trade=p1.call('trades',timeout=5)
 if any('[TRADE]' in x for x in trade): break
 time.sleep(.1)
else: raise RuntimeError('ordinary Katana did not open a secure trade')
print('ordinary trade offer',trade)
p1.call('accepttrade',timeout=5); time.sleep(.2); p2.call('accepttrade',timeout=5)
if not p2.wait(lambda:any(i.serial==ordinary for i in p2.backpack),timeout=10,poll=.1): raise RuntimeError('ordinary Katana did not arrive after both clients accepted')
if any(i.serial==ordinary for i in p1.backpack): raise RuntimeError('ordinary Katana remained with seller after trade')
print('ordinary output secure_trade=PASS recipient received item')
time.sleep(1.2)

# Return it, then show ordinary output enters the owner-operated player vendor's stock.
p2.drop(ordinary,char1)
for _ in range(30):
 trade=p2.call('trades',timeout=5)
 if any('[TRADE]' in x for x in trade): break
 time.sleep(.1)
else: raise RuntimeError('ordinary Katana return trade did not open')
p2.call('accepttrade',timeout=5); time.sleep(.2); p1.call('accepttrade',timeout=5)
if not p1.wait(lambda:any(i.serial==ordinary for i in p1.backpack),timeout=10,poll=.1): raise RuntimeError('ordinary Katana did not return to seller')
time.sleep(1.2); p1.drop(ordinary,vendor)
if not p1.wait(lambda:not any(i.serial==ordinary for i in p1.backpack),timeout=8,poll=.1): raise RuntimeError('ordinary Katana did not leave owner backpack for player vendor')
print('ordinary output player_vendor intake delivered; server inventory check pending')
