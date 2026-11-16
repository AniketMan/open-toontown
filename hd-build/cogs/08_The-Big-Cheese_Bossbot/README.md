# 08_The-Big-Cheese_Bossbot HD build (suit A, code `tbc`, scale 7.0 / 6.06)

Runs in place. Sheets read: all five; measured sheet: new-turnaround, 578 px = 9.4 game units.
Two of the five sheets show ringed ear discs; three (including the measured one) do not, so he has none.
Body: the Head Hunter's coat and limbs. The coat is laid out at the Head Hunter's size and scaled by `BODY_S` (1.106,
from hem and shoulder heights on this sheet) at the end of build.py; limbs are native suit A.
Head: a triangular slab (superellipse power 8). The cheese holes are a boolean cut applied inside build.py while
shell and cutter are together -- the rig moves the shell, so a live modifier cuts nothing. After the cut every shell
vertex is put back in the `joint_head` group. Expression: deep-set eyes under heavy slanted lid plates, dark rims,
thick low brows (the user rejected round open eyes as not scary, 2026-11-14).
