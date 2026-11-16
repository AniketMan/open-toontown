# 04_Micromanager_Bossbot HD build (suit C, code `mm`, scale 2.5 / 4.14)

Same step order as `../03_Yesman_Bossbot/README.md`: extract_rig (`mm`), build, rig, uv, bake, dump_export, build_bam, test_swap.
`run.py` rebuilds and rigs in one call and renders check views (`check.py`).

Sheets read: all five (see `../REFERENCE_INDEX.md`). Measured sheet: new-turnaround, 447 px = 3.25 game units.
Where the sheets disagree: two of the five show ringed ear discs on the hair shell; three (including the measured
one) show none, so there are none.

New in this build
- The face is a prow (two flat cheek planes on a centre ridge, box behind), so the head is not a superellipse loft:
  `gauge_pt()` in build.py gives a point and normal on a section from half-width, front, back and cheek slope.
- Open mouth: the inner shell and the mouth bowl are built from the same columns of points (`core_col`), so the
  bowl is the shell behind the opening and there is no join. Lips are tubes on the rim.
- rig.py carries each vertex to the rest pose with the exact inverse of its own skin blend (`FROM_REST`), so the
  sheet pose gives back the modelled shape exactly. Suit C's coat joints follow the splayed legs; with the old
  per-joint average, blended jacket vertices moved up to 0.07 and swallowed a button.
- uv.py creates a UV layer for a mesh that has none (the head here is all grids and tubes).

Suit C joint map: see `../01_Flunky_Bossbot/README.md` and the comments in rig.py.
