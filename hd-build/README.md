# HD cog and toon build sources

A mirror of the working folder `../open-toontown-hd` (which is not a git repository), refreshed with
`tools/sync_hd_build.sh`.

- `cogs/` — one folder per cog (01 Flunky to 14 Spin Doctor) with its Blender build scripts, notes and final
  previews, plus the shared pieces (`medallion.py`, `add_meter.py`, `check_bams.py`, `glow_test.py`).
- `toons/` — the single toon Blender project `toons_hd.blend` and its scripts; the duck head is the only piece
  started and is not finished.

Not mirrored: `work/` scratch renders, baked textures, export dumps, Blender backups, the per-cog `.blend` files, the
original game models and the reference sheets. The scripts regenerate the first three; the rest stay in the working
folder. The scripts still use absolute paths into the working folder, so they run from there, not from this copy.
