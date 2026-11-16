# 10 Bloodsucker (Lawbot, suit B, code `b`)

Built 2026-11-14. Body is the Downsizer's coat (same suit B body) in navy with the Lawbot trim: purple piping, studded
lapels, yokes, hem, cuffs and trouser bands. It is laid out at the Downsizer's size and scaled by 4.375/4.5 at the end
of build.py. Head, shirt front and medallion are this cog's own.

- Regenerate the scripts: `python3 work/gen.py` (assembles build.py from ../05_Downsizer_Bossbot/build.py + work/head_part.py).
- In Blender: `run.py` `run(shots, prefix)`, then uv.py, bake.py, dump_export.py (OUT = b_export.json).
- Game: `build_bam.py b b_export.json 10_Bloodsucker_Lawbot shot.png`, `test_swap.py out.png b`, `../check_bams.py`,
  `../glow_test.py out.png b` (medallion with the health light off and on).

From the original turnaround (not only the new sheets): the shirt front has a zip, the bow tie is dotted, the hands
are white, the medallion is an upright gavel. The medallion comes from `../medallion.py` (shared by every cog): the
emblem and the ring round the face are dark metal in their own mesh, which `../add_meter.py` splits out as `hd_emblem`
so the game lights them.

Known rough spots: about 48k triangles; the hair is a plain swept-back block, less of a pompadour than the sheets;
plain lower coat (no pocket welts).
