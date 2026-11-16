# 01_Flunky_Bossbot HD build

Run in this order (Blender scripts run through the Blender MCP or Blender's text editor):

1. `extract_rig.py` (game Python, from the open-toontown repo root):
   `PYTHONPATH=. venv/bin/python extract_rig.py f flunky_rig.json walk:0 walk:6 walk:12 neutral:20`
   Dumps the body's rest pose, the neutral pose the original was exported in, skin weights and test frames.
2. `build.py` (Blender): builds the model in the concept sheet's pose with procedural materials.
3. `rig.py` (Blender): armature in the body's rest pose at native size, weights (max 3 per vertex),
   joins everything into `body_hd` and `head_hd`. `apply_pose("sheet")`, `apply_pose("walk:6")`, `apply_pose(None)`.
4. `uv.py` (Blender): one atlas UV layout for the whole character.
5. `bake.py` (Blender): 2048 base colour + normal map into `open-toontown/resources-hd/phase_3.5/maps/`.

`check.py` renders check views; `compare.py` overlays them on the concept sheet.
Spec this follows: `open-toontown/tools/ENEMY_MODEL_SWAP.md`.

6. In Blender, dump the two meshes (rest pose, atlas UVs, normals, weights) to `flunky_export.json` (the block at the end of the save step).
7. `build_bam.py` (game Python, repo root): `PYTHONPATH=. venv/bin/python build_bam.py f flunky_export.json 01_Flunky_Bossbot shot.png`
   Loads `suitC-mod`, removes its meshes, hangs the HD meshes on the same joints, writes
   `resources-hd/phase_3.5/models/char/01_Flunky_Bossbot_hd.bam`, checks the joint list and binds walk/neutral.
8. `test_swap.py` (game Python): builds the enemy through `Suit.Suit` with and without `want-hd-suits` and screenshots both.

The loader change is in `open-toontown/toontown/suit/Suit.py` (`HD_SLOTS`, `hdModelPath`); it picks up any `<slot>_hd.bam` that exists.
Limbs are modelled in the body's rest pose (see the "limbs" section of build.py); the torso and head are modelled standing and carried to the rest pose by rig.py.
