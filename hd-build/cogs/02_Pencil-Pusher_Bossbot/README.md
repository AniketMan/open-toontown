# 02_Pencil-Pusher_Bossbot HD build (suit B)

Reference sheets: `Documents/Codex/2026-11-12/new-chat/` (new-turnarounds is the measured one, 570 px = 5.0 units;
head-breakdowns and the blueprint sheets give the plate and jaw-cassette construction).

Run order, same as the Flunky (scripts hold scratchpad paths in `SP`; change it if the files move):

1. `extract_rig.py p pp_rig.json walk:0 walk:6 walk:12 neutral:20` (game Python, repo root, `PYTHONPATH=. venv/bin/python`).
2. `build.py` in Blender (it execs `hd_lib.py`, the helpers shared with the Flunky build).
3. `rig.py` in Blender. `run.py` does 2 + 3 and renders `check.py` views in a chosen pose.
4. `uv.py`, then `bake.py` (rest pose), then `dump_export.py` with `OUT` set.
5. `build_bam.py p pp_export.json 02_Pencil-Pusher_Bossbot shot.png`, then `test_swap.py shot.png p`.

Suit B joints, checked against the walk and neutral frames (not guessed from names):
upper arm `scale_jnt3_1` / `scale_jnt9_1`, forearm `jnt3_2` / `jnt9_2`, shoulder `shoulderL1/R1`, thigh
`scale_jnt1_1` / `scale_jnt2_1`, shin `jnt1_2` / `jnt2_2`, foot `to_legL/R` + `to_ballL/R`, pelvis `to_MAIN`.
Hand joints are named alike on both sides (`Lh_*` / `Rh_*`). `cons_Lwrist`, `Rsleeve_trans`, `Rforearm` exist on one side only and are unused.
Native size = game size / 0.633; rest pose is a T-pose with shoulders at z 4.96.
