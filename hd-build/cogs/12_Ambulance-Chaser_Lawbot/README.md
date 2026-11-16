# 12 Ambulance Chaser (Lawbot, suit B, code `ac`)

Built 2026-11-14. All five sheets and the original agree on this cog. Body: the Bloodsucker's build (itself the
Downsizer's suit B coat in Lawbot trim) with lilac hands and white shirt cuffs. Head (work/head_part.py): a tall
lilac slab, the grin cut straight into the face shell as two round lobes of teeth with the chin rising to a point
between them (no plate edge round the mouth), thick black brows, half-shut brown eyes, long nose, black hair shell
with sideburns, white top hat with a red cross.

- `python3 work/gen.py` regenerates the scripts from ../10_Bloodsucker_Lawbot/build.py + work/head_part.py.
- `python3 work/cmp.py <prefix>` puts the sheet's views over the renders at the same scale (work/cmp_heads.png,
  work/cmp_body.png); do this before showing anything.
- Blender: run.py, uv.py, bake.py, dump_export.py (OUT = ac_export.json). Game: build_bam.py ac ..., test_swap.py,
  ../check_bams.py, ../glow_test.py.

Known differences from the sheet: head and hat are upright (the sheet's side view leans them back a little); ears are
ringed discs, not sculpted ears; the hair is a straight shell, not swept; hands are smaller and arms hang wider than
drawn (skeleton); medallion shows the upright gavel used on every Lawbot, not the sheet's crossed pair.
