# 11 Double Talker (Lawbot, suit A, code `dt`)

Built 2026-11-14. Body is the Head Hunter's coat (same suit A body) in navy with the Lawbot trim, laid out at his
size and scaled by 4.25/6.5 at the end of build.py; collar and shirt band are lowered because the chin sits low.

Head (work/head_part.py), rebuilt 2026-11-14 after the first version was rejected: a faceted two-tier block, a diamond
in plan. A hood of four flat planes flares from a small crown to a wide belt; a narrower jaw block sits under it.
Each hood plane has one eye, each jaw plane half a mouth; the two planes on his left are the sad face, the two on
his right the angry one. `P(tier, plane, u, v)` gives a point on a plane; `ridge()` makes brows and lips as folds.
preview_vs_sheet_head.png and preview_vs_sheet_body.png put the sheet over the model at the same scale.

From the original: zip down the shirt, dotted bow tie, lilac hands, upright gavel medallion (../medallion.py).

- `python3 work/gen.py` regenerates build.py/rig.py/check.py from ../06_Head-Hunter_Bossbot + work/head_part.py.
- Blender: run.py `run(shots, prefix)`, uv.py, bake.py, dump_export.py (OUT = dt_export.json).
- Game: build_bam.py dt dt_export.json 11_Double-Talker_Lawbot shot.png; test_swap.py; ../check_bams.py; ../glow_test.py.

Known differences from the sheet: the body is the Head Hunter's, so the shoulders are boxier and the arms hang wider
than drawn (the arm spread comes from the game's skeleton); hands are smaller than drawn; the face planes are flat
where the sheet's are softly sculpted; about 50k triangles.
