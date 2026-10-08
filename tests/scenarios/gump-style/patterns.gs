# Patterns on the Stone frame: a confirm dialog (left) and a result banner plus empty state in a list window (right)
pos 10 20
# --- confirm dialog 380 x 250
bg 0 0 380 250 9200
tile 10 10 360 230 2624
html 20 16 340 26 "Leave the safe world?" color=#FFD060 size=5 align=center
tile 24 46 332 4 2700
html 30 62 320 110 "Recall will take you into Buccaneer's Den island, a Hot Zone: other players can attack you there, and your Backpack Ward does not protect you.<BR><BR>You will not be asked again if you tick the box." color=#F2F2F2
check 30 178 210 211 0 1
html 58 180 300 20 "Do not show this warning again" color=#BBBBBB
tile 24 206 332 4 2700
button 40 214 2443 2444 1
html 40 217 63 18 "Go" color=#101010 align=center style=1
button 276 214 2443 2444 0
html 276 217 63 18 "Stay" color=#101010 align=center style=1
# --- list window with banner and empty state 400 x 250, to the right
bg 400 0 400 250 9200
tile 410 10 380 230 2624
html 410 16 380 26 "Skill Bank" color=#FFD060 size=5 align=center
tile 424 46 352 4 2700
html 420 56 360 24 "Moved 1.2 points to Swordsmanship." color=#8FE08F style=1
html 420 84 360 20 "Skill" color=#BBBBBB
html 700 84 80 20 "Banked" color=#BBBBBB align=right
tile 424 104 352 4 2700
html 420 124 360 60 "Nothing is banked yet.<BR>Set a skill to Down and train another to bank points here." color=#999999 align=center
tile 424 206 352 4 2700
button 440 214 2443 2444 0
html 440 217 63 18 "Close" color=#101010 align=center style=1
