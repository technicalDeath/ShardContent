from pathlib import Path
import re,sys,time

root=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(root/'Navrey'/'cli'))
from uo import Client,Event

def open_client(role):
    d=(root/'work'/'alpha3-starter-economy-clients'/role).resolve()
    c=Client(state_file=str(d/'state2.json'),world_file=str(d/'world2.json'),cmd_file=str(d/'cmd2.txt'),log_file=str(d/'client2.log'))
    c.require_live()
    if not c.state.get('inGame') or time.time()*1000-c.state.get('updatedAtMs',0)>=5000:
        raise RuntimeError(f'{role} has no fresh in-game state')
    return c,d

def wait_for_text(client,kind,text,timeout=5):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        event=client.wait_for(kind,timeout=min(.5,deadline-time.monotonic()),poll=.05)
        if event and text.lower() in event.text.lower():
            return event.text
    return None

admin,admin_dir=open_client('admin')
p1,p1_dir=open_client('player1')
p2,p2_dir=open_client('player2')
if p1.state['charID']==p2.state['charID']:
    raise RuntimeError('paired clients resolved to the same character')
admin_log=admin_dir/'client2.log'
reuse=len(sys.argv)>2 and sys.argv[2]=='reuse'
start=0 if reuse else len(admin_log.read_text(errors='replace').splitlines())
owner=p1.state['charID']
if not reuse:
    admin.call(f'say [StarterEconomyProbe transfers {owner}',timeout=6)
deadline=time.time()+8
targets={}
vendor=None
while time.time()<deadline:
    lines=admin_log.read_text(errors='replace').splitlines()[start:]
    for line in lines:
        target=re.search(r'Starter economy transfer target: ([A-Za-z0-9_]+)=0x([0-9A-Fa-f]+);',line)
        if target:
            targets[target.group(1)]='0x'+target.group(2)
        match=re.search(r'Starter economy transfer matrix ready: count=(\d+); vendor=0x([0-9A-Fa-f]+); owner=',line)
        if match:
            if int(match.group(1))!=41:
                raise RuntimeError(f'probe reported {match.group(1)} transfer fixtures, expected 41')
            vendor='0x'+match.group(2)
    if len(targets)==41 and vendor:
        break
    time.sleep(.1)
if len(targets)!=41 or not vendor:
    raise RuntimeError(f'incomplete server fixture report: {len(targets)} classes, vendor={vendor}')
if not p1.wait(lambda:all(any(i.serial==s for i in p1.backpack) for s in targets.values()),timeout=8,poll=.1):
    raise RuntimeError('one or more transfer fixtures did not reach P1 backpack')
if p1.state.get('charPosX')!=p2.state.get('charPosX') or p1.state.get('charPosY')!=p2.state.get('charPosY'):
    raise RuntimeError('paired characters are not colocated for secure trade')

for label,serial in targets.items():
    if not any(i.serial==serial for i in p1.backpack):
        raise RuntimeError(f'{label}: absent from owner backpack before secure trade')
    p1.events.drain()
    p1.drop(serial,p2.state['charID'])
    refusal=wait_for_text(p1,Event.SYSTEM,'You cannot trade an item that contains nontransferable items.',timeout=.25)
    if not p1.wait(lambda:any(i.serial==serial for i in p1.backpack) and not any(i.serial==serial for i in p2.backpack),timeout=5,poll=.1):
        raise RuntimeError(f'{label}: secure-trade attempt changed the owner/recipient inventory')
    trade=p1.call('trades',timeout=5)
    if not any('No secure-trade windows open' in line for line in trade):
        raise RuntimeError(f'{label}: secure-trade window opened: {trade}')
    trade_observation='message and state' if refusal else 'state; no refusal narration observed'

    p1.events.drain()
    p1.drop(serial,vendor)
    vendor_refusal=wait_for_text(p1,Event.SPEECH,'I cannot accept an item that contains nontransferable items.',timeout=.25)
    if not p1.wait(lambda:any(i.serial==serial for i in p1.backpack) and not any(i.serial==serial for i in p2.backpack),timeout=5,poll=.1):
        raise RuntimeError(f'{label}: player-vendor attempt changed the owner/recipient inventory')
    vendor_observation='message and state' if vendor_refusal else 'state; no refusal narration observed'
    print(f'{label}: secure trade={trade_observation}; player-vendor intake={vendor_observation}')

verify_start=len(admin_log.read_text(errors='replace').splitlines())
admin.call(f'say [StarterEconomyProbe verify {owner}',timeout=8)
deadline=time.time()+8
verification={}
while time.time()<deadline:
    for line in admin_log.read_text(errors='replace').splitlines()[verify_start:]:
        for label,serial in targets.items():
            if f'{serial}: ' in line:
                verification[label]=line
    if len(verification)==41:
        break
    time.sleep(.1)
if len(verification)!=41:
    raise RuntimeError(f'server verification returned {len(verification)}/41 item records')
for label,line in verification.items():
    if 'ownerBackpack=True' not in line or 'vendorStock=False' not in line or 'inTrade=False' not in line:
        raise RuntimeError(f'{label}: server invariant failed: {line}')
print('41 bound implementations: server confirms every item remained in P1 backpack, outside trade and vendor stock')
