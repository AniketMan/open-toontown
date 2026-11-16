# 03_Yesman_Bossbot HD build (suit A)

Same run order as `02_Pencil-Pusher_Bossbot` (see its README); `run.py` rebuilds, rigs and renders check views.
Code `ym`, slot `03_Yesman_Bossbot`, scale 4.125 / 6.06.

Suit A joints, checked against the walk and neutral frames: upper arm `scale_jnt24_1` / `scale_jnt27_1`, forearm
`Lh_arm` / `Rh_arm`, shoulder `shoulderL1/R1` (on `to_shoulder`), thigh `scale_jnt3_1` / `scale_jnt4_1`, shin
`jnt3_2` / `jnt4_2`, foot `to_LegL` / `to_legR` (note the capital L) + `to_ballL/R`, pelvis `to_MAIN`.

Things suit A does that B and C did not:
- Its rest pose is not symmetric (shoulders x 1.67 / -1.61, hips 0.44 / -0.39, wrists 3.87 / -3.91) and its neutral
  pose leans. Limbs are built per side on each side's own joints (`to_right`, `HIP`).
- Right-side joints have mirrored (left-handed) axes. Never build a right joint's pose as X * left * X on the joint
  matrix; mirror the left joint's rest-to-pose MOVE and re-anchor it on the right joint's own rest position (rig.py).
- Preview poses apply `frame * bind^-1` to the bone's own frame, not an orthonormalised copy of the joint matrix.

Head plates: every seam is sampled at the same angles and heights on both of its sides, or slivers open between
plates on a curved head (`face_zs`, `chin_zs`, `BACK_Z`, `CROWN_TH` in build.py).
