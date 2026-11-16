# 13 Back Stabber (Lawbot, suit A, code `bs`; objects are prefixed BK_)

Built 2026-11-14. Body: the suit A Lawbot build from ../11_Double-Talker_Lawbot (the Head Hunter's coat in navy, with
studded yokes and shoulder caps), at K = 4.5/6.06. Head (work/head_part.py): a tall violet cone, back upright and
front sloping to the point; the frown is a slot cut into the face shell (no plate edge), jaw swelling below it; small
glaring eyes under dark brow strokes; the thin arch of the jaw panel; a red fin up the back forming the tip; a small
bolt on each side (two sheets draw big ear discs, the new turnaround and the original none).

- `python3 work/gen.py` regenerates the scripts; `python3 work/cmp.py <prefix>` makes the same-scale sheet comparison.
- Blender: run.py, uv.py, bake.py, dump_export.py (OUT = bs_export.json). Game: build_bam.py bs ..., test_swap.py,
  ../check_bams.py, ../glow_test.py.

Known differences from the sheet: the cone bulges a little where the sheet's sides are straight; the fin is rounded
at the back where the sheet's is cut flat; the frown is thinner than drawn; arms hang wider and hands are smaller
than drawn (skeleton); about 47k triangles.
