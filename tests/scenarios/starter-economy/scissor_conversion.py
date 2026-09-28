from pathlib import Path
import re,sys,time
root=Path(sys.argv[1]).resolve();sys.path.insert(0,str(root/'Navrey'/'cli'))
from uo import Client

def open_client(role):
 d=(root/'work'/'alpha3-starter-economy-clients'/role).resolve()
 c=Client(state_file=str((d/'state2.json').resolve()),world_file=str((d/'world2.json').resolve()),cmd_file=str((d/'cmd2.txt').resolve()),log_file=str((d/'client2.log').resolve()))
 c.require_live()
 if not c.state.get('inGame') or time.time()*1000-c.state.get('updatedAtMs',0)>=5000: raise RuntimeError(f'{role} has no fresh in-game state')
 return c

admin,p1=open_client('admin'),open_client('player1')
admin_log=root/'work'/'alpha3-starter-economy-clients'/'admin'/'client2.log'
owner=p1.state['charID']
# Remove fixture items from earlier interrupted runs in this disposable world.
for old in ('0x4007A188','0x4007A189'):
 admin.call('say [StarterEconomyProbe delete '+old,timeout=6)
previous=next((line for line in reversed(admin_log.read_text(errors='replace').splitlines()) if 'Starter economy salvage targets:' in line),None)
if previous:
 for key in ('cloth','armor','ordinaryCloth','bag','scissors','tongs','nestedCloth','nestedArmor','nestedKatana','ordinaryKatana'):
  found=re.search(rf'{key}=(?:0x)?([0-9A-Fa-f]+)',previous)
  if found: admin.call('say [StarterEconomyProbe delete 0x'+found.group(1),timeout=6)
admin.call('say [StarterEconomyProbe salvage '+owner,timeout=6)
for _ in range(50):
 lines=admin_log.read_text(errors='replace').splitlines()
 fixture=next((line for line in reversed(lines) if 'Starter economy salvage targets:' in line),None)
 if fixture: break
 time.sleep(.1)
else: raise RuntimeError('server did not report seeded salvage targets')
serials={key:'0x'+re.search(rf'{key}=(?:0x)?([0-9A-Fa-f]+)',fixture).group(1) for key in ('cloth','armor','ordinaryCloth','bag','scissors','tongs','nestedCloth','nestedArmor','nestedKatana','ordinaryKatana')}
if not p1.wait(lambda:all(any(i.serial==s for i in p1.backpack) for s in (serials['cloth'],serials['armor'],serials['ordinaryCloth'],serials['bag'])),timeout=6,poll=.1): raise RuntimeError('server seeded direct salvage items but owner backpack snapshot did not update')
if not p1.wait(lambda:p1.state.get('charPosX')==1354 and p1.state.get('charPosY')==1778,timeout=6,poll=.1): raise RuntimeError('server did not place the salvage fixture at its disposable forge station')
scissors=serials['scissors']
for label,key in [('StarterCloth','cloth'),('StarterStuddedChest','armor')]:
 item=serials[key]
 before={i.serial for i in p1.backpack}
 if not p1.use_on(scissors,item,timeout=6): raise RuntimeError(f'{label}: no scissors target cursor')
 if not p1.wait(lambda:any(i.serial==item for i in p1.backpack),timeout=5,poll=.1): raise RuntimeError(f'{label} was consumed')
 if {i.serial for i in p1.backpack}-before: raise RuntimeError(f'{label} produced an output item')
 print(label+' direct scissors=PASS; item retained, no output')
 time.sleep(1.2)
# Ordinary cloth still converts through stock scissors, producing ordinary bandages.
ordinary=serials['ordinaryCloth'];before_bandages=sum(i.amount for i in p1.backpack if i.name.lower()=='clean bandage')
if not p1.use_on(scissors,ordinary,timeout=6): raise RuntimeError('ordinary cloth target cursor did not appear')
if not p1.wait(lambda:not any(i.serial==ordinary for i in p1.backpack) and sum(i.amount for i in p1.backpack if i.name.lower()=='clean bandage')>before_bandages,timeout=6,poll=.1):
 raise RuntimeError('ordinary cloth conversion control did not produce bandages')
print('ordinary Cloth scissors control=PASS')
time.sleep(1.2)
# The probe placed bound sources inside this test-only Salvage Bag because player drops reject them.
print('open bag',p1.call('use '+serials['bag'],timeout=6));time.sleep(.5)
contents=p1.call('container '+serials['bag'],timeout=6);print('salvage bag contents before',contents)
if serials['nestedCloth'] not in str(contents) or serials['nestedArmor'] not in str(contents): raise RuntimeError('server did not seed both bound sources inside the test Salvage Bag')
bandages_before_salvage=sum(i.amount for i in p1.backpack if i.name.lower()=='clean bandage')
cloth_before_salvage=sum(i.amount for i in p1.backpack if i.name.lower()=='cut cloth')
menu=p1.call('contextmenu '+serials['bag'],timeout=6);print('salvage menu',menu)
line=next((x for x in menu if 'Salvage Cloth' in x),None)
if line is None: raise RuntimeError('Salvage Cloth action missing from observed context menu')
match=re.search(r'\[entry (\d+)\]',line,re.I)
if not match: raise RuntimeError('could not parse observed Salvage Cloth menu index')
p1.call('contextpick '+serials['bag']+' '+match.group(1),timeout=6);time.sleep(.8)
if not p1.wait(lambda:sum(i.amount for i in p1.backpack if i.name.lower()=='cut cloth')>=cloth_before_salvage+2,timeout=6,poll=.1): raise RuntimeError('Salvage Bag did not return nested StarterCloth to the owner')
p1.call('use '+serials['bag'],timeout=6);time.sleep(.3)
post=p1.call('container '+serials['bag'],timeout=6);print('salvage bag contents after',post)
if serials['nestedArmor'] not in str(post): raise RuntimeError('Salvage Bag consumed or lost nested StarterStuddedChest')
if sum(i.amount for i in p1.backpack if i.name.lower()=='clean bandage')!=bandages_before_salvage: raise RuntimeError('Salvage Bag produced unrestricted bandages from bound cloth')
print('Salvage Bag bound cloth/armor=PASS; cloth returned/stacked as bound cloth, armor remained, no bandages')

# Ingot salvage must keep bound weapon/armor and still recover ordinary output.
if serials['nestedKatana'] not in str(post) or serials['ordinaryKatana'] not in str(post): raise RuntimeError('ingot salvage control items are not in the Salvage Bag')
ingots_before=sum(i.amount for i in p1.backpack if i.name.lower()=='iron ingot')
menu=p1.call('contextmenu '+serials['bag'],timeout=6);print('ingot salvage menu',menu)
line=next((x for x in menu if 'Salvage Ingots' in x),None)
if line is None: raise RuntimeError('Salvage Ingots action missing from observed context menu')
match=re.search(r'\[entry (\d+)\]',line,re.I)
if not match: raise RuntimeError('could not parse observed Salvage Ingots menu index')
p1.call('contextpick '+serials['bag']+' '+match.group(1),timeout=6);time.sleep(.8)
after_ingots=p1.call('container '+serials['bag'],timeout=6);print('salvage bag after ingot salvage',after_ingots)
if serials['nestedKatana'] not in str(after_ingots) or serials['nestedArmor'] not in str(after_ingots): raise RuntimeError('Salvage Bag consumed or lost bound metal equipment')
if serials['ordinaryKatana'] in str(after_ingots): raise RuntimeError('ordinary Katana control was not resmelted')
if not p1.wait(lambda:sum(i.amount for i in p1.backpack if i.name.lower()=='iron ingot')>=ingots_before+2,timeout=6,poll=.1): raise RuntimeError('ordinary Katana did not yield the expected ordinary ingot control')
print('Salvage Ingots bound equipment=PASS; bound items retained, ordinary Katana yielded ordinary ingots')
