# Swapping in a replacement enemy model

Instructions for replacing one robot enemy's body and head with a single
custom model, keeping the game's existing animations.  Written so that a
fresh session can do the job from this file alone.

## 1. How the game builds an enemy today

There is no model file per enemy.  `toontown/suit/Suit.py` assembles each
one when it appears:

1. `Suit.setDNA()` has one branch per enemy code (`dna.name`).  The branch
   sets `self.scale`, `self.handColor`, calls `generateBody()`, then
   `generateHead(piece)` once per head piece, then `setHeight()`.
2. `generateBody()` loads one of three shared rigged bodies,
   `phase_3.5/models/char/suit{A,B,C}-mod`, and binds that body's
   animation files (`suit{A,B,C}-<anim>` under `phase_3.5` .. `phase_12`;
   the list is built by `Suit.py` from `AllSuits`, `AllSuitsMinigame`,
   `AllSuitsTutorialBattle`, `AllSuitsBattle` and the per-enemy tables).
3. `generateHead()` finds the named piece in `suit{A,B,C}-heads` and
   instances it under the joint `joint_head`.
4. `setSuitClothes()` finds the mesh nodes `torso`, `arms`, `legs` and
   applies the department textures (`phase_3.5/maps/<dept>_blazer|sleeve|leg`),
   and colours the node `hands` with `self.handColor`.
5. It then looks up `joint_Lhold`, `joint_Rhold`, `joint_shadow`,
   `joint_nameTag`; `generateCorporateMedallion()` and
   `generateHealthBar()` attach to `joint_attachMeter`.
6. `self.getGeomNode().setScale(self.scale)` applies the per-enemy scale.

Body sizes (constants in `Suit.py`): `aSize = 6.06`, `bSize = 5.29`,
`cSize = 4.14` game units (feet).  `self.scale` is `<number> / <x>Size`,
so "Scale" below is the enemy's final body height before its head.

## 2. Slot table

The slot name is the file-name stem used for the turnaround sheets in
`open-toontown-hd/cog-turnarounds/`.  A replacement model for a slot is
named `<slot>_hd` (source `.blend`) and exported as `<slot>_hd.bam`.

| Slot | Code | Body | Head pieces | Scale | Height |
|---|---|---|---|---|---|
| `01_Flunky_Bossbot` | `f` | C | `flunky`, `glasses` | 4.0 | 4.88 |
| `02_Pencil-Pusher_Bossbot` | `p` | B | `pencilpusher` | 3.35 | 5.0 |
| `03_Yesman_Bossbot` | `ym` | A | `yesman` | 4.125 | 5.28 |
| `04_Micromanager_Bossbot` | `mm` | C | `micromanager` | 2.5 | 3.25 |
| `05_Downsizer_Bossbot` | `ds` | B | `beancounter` | 4.5 | 6.08 |
| `06_Head-Hunter_Bossbot` | `hh` | A | `headhunter` | 6.5 | 7.45 |
| `07_Corporate-Raider_Bossbot` | `cr` | C | `flunky` | 6.75 | 8.23 |
| `08_The-Big-Cheese_Bossbot` | `tbc` | A | `bigcheese` | 7.0 | 9.34 |
| `09_Bottom-Feeder_Lawbot` | `bf` | C | `tightwad` | 4.0 | 4.81 |
| `10_Bloodsucker_Lawbot` | `b` | B | `movershaker` | 4.375 | 6.17 |
| `11_Double-Talker_Lawbot` | `dt` | A | `twoface` | 4.25 | 5.63 |
| `12_Ambulance-Chaser_Lawbot` | `ac` | B | `ambulancechaser` | 4.35 | 6.39 |
| `13_Back-Stabber_Lawbot` | `bs` | A | `backstabber` | 4.5 | 6.71 |
| `14_Spin-Doctor_Lawbot` | `sd` | B | `telemarketer` | 5.65 | 7.9 |
| `15_Legal-Eagle_Lawbot` | `le` | A | `legaleagle` | 7.125 | 8.27 |
| `16_Big-Wig_Lawbot` | `bw` | A | `bigwig` | 7.0 | 8.69 |
| `17_Short-Change_Cashbot` | `sc` | C | `coldcaller` | 3.6 | 4.77 |
| `18_Penny-Pincher_Cashbot` | `pp` | A | `pennypincher` | 3.55 | 5.26 |
| `19_Tightwad_Cashbot` | `tw` | C | `tightwad` | 4.5 | 5.41 |
| `20_Bean-Counter_Cashbot` | `bc` | B | `beancounter` | 4.4 | 5.95 |
| `21_Number-Cruncher_Cashbot` | `nc` | A | `numbercruncher` | 5.25 | 7.22 |
| `22_Money-Bags_Cashbot` | `mb` | C | `moneybags` | 5.3 | 6.97 |
| `23_Loan-Shark_Cashbot` | `ls` | B | `loanshark` | 6.5 | 8.58 |
| `24_Robber-Baron_Cashbot` | `rb` | A | `yesman` | 7.0 | 8.95 |
| `25_Cold-Caller_Sellbot` | `cc` | C | `coldcaller` | 3.5 | 4.63 |
| `26_Telemarketer_Sellbot` | `tm` | B | `telemarketer` | 3.75 | 5.24 |
| `27_Name-Dropper_Sellbot` | `nd` | A | `numbercruncher` | 4.35 | 5.98 |
| `28_Glad-Hander_Sellbot` | `gh` | C | `gladhander` | 4.75 | 6.4 |
| `29_Mover-Shaker_Sellbot` | `ms` | B | `movershaker` | 4.75 | 6.7 |
| `30_Two-Face_Sellbot` | `tf` | A | `twoface` | 5.25 | 6.95 |
| `31_The-Mingler_Sellbot` | `m` | A | `twoface` | 5.75 | 7.61 |
| `32_Mr-Hollywood_Sellbot` | `mh` | A | `yesman` | 7.0 | 8.95 |

Skeleton variants (`<slot>` 33-38) and waiters (39-40) reuse these codes
with `isSkelecog` / `isWaiter` set and are out of scope here.

## 3. What a replacement model must contain

Build one model per slot containing body and head together.

**Skeleton.**  Skin the mesh to the skeleton of the body the slot uses
(table above), with joint names and hierarchy unchanged and the same rest
pose.  The animations address joints by name; a renamed or missing joint
simply stops moving.  Get the skeleton by importing that body:

    bam2egg resources/phase_3.5/models/char/suitC-mod.bam -o suitC-mod.egg

then import the `.egg` into Blender (an egg importer add-on is needed) or
rebuild the armature from the joint trees in section 6.

**Required joints** (looked up by name in code): `joint_head`,
`joint_Lhold`, `joint_Rhold`, `joint_shadow`, `joint_nameTag`,
`joint_attachMeter`.  Keep them where the original has them relative to
the new mesh: `joint_nameTag` above the head, `joint_attachMeter` on the
chest, the two hold joints in the palms.

**Head.**  Weight the whole head 100% to `joint_head` (the originals are
rigid pieces hung on that joint), so head-turn animation still works.

**Mesh node names.**  If the model keeps separate nodes named `torso`,
`arms`, `legs`, `hands`, the game will overwrite their textures with the
department suit textures.  A custom-textured model should NOT use those
names; use e.g. `body_hd`, `head_hd`.  The loader in section 5 then skips
`setSuitClothes()`.

**Size and axes.**  Panda3D is Z-up.  Match the facing direction
of the imported body, which is the reference.  Model at the
body's native height (A 6.05, B 5.35, C 4.12 to the shoulders/neck joint,
measured on the original) so the per-enemy scale still gives the right
size.  Feet on Z = 0, centred on the origin.

**Budget.**  The originals are 635-830 vertices per body.  Many enemies
are on screen at once; keep a replacement to a few thousand triangles and
at most three bone weights per vertex, or provide LODs.

**Materials.**  Panda's default pipeline here is unlit and textured:
bake procedural Blender materials to an image texture (one atlas, 1024 or
2048) before export.  Put textures in `resources-hd/phase_3.5/maps/`.

## 4. Export

1. Apply all transforms; one armature; mesh parented with an Armature
   modifier; no shape keys unless needed.
2. Export to `.egg` (YABEE or a current Blender-to-egg exporter) or to
   glTF and convert with `gltf2bam` (`pip install panda3d-gltf` into
   `venv`).  Export the model only, no animation.
3. If via egg: `egg2bam -o <slot>_hd.bam <slot>_hd.egg`.
4. Place the result at `resources-hd/phase_3.5/models/char/<slot>_hd.bam`.
   `resources-hd/` is ahead of `resources/` on the model path when
   `want-hd-textures` is on, and is ignored by git.
5. Check it:  load with `Actor(path)`, compare
   `sorted(j.getName() for j in actor.getJoints())` against the original
   body's list, and bind one animation, e.g.
   `Actor(path, {'walk': 'phase_3.5/models/char/suitC-walk'})`.
   Any joint the animation cannot find is reported on the console.

## 5. Loader change (not written yet)

All in `toontown/suit/Suit.py`:

1. Add a table `HD_SLOTS = {'f': '01_Flunky_Bossbot', ...}` from the Slot
   and Code columns above, and a config switch `want-hd-suits` (default on).
2. Add a helper `hdModelPath(dnaName)` that returns
   `phase_3.5/models/char/<slot>_hd` if that file resolves on the model
   path (`VirtualFileSystem.getGlobalPtr().resolveFilename` with
   `getModelPath()`), else `None`.  Cache the answer per code.
3. In `generateBody()`: if not skeleton/waiter and `hdModelPath()` is set,
   `self.loadModel(thatPath)` instead of the shared body, set
   `self.hdModel = True`; the `self.loadAnims(animDict)` call is unchanged.
4. In `generateHead()`: return immediately when `self.hdModel`.
5. In `setSuitClothes()`: when `self.hdModel`, skip the texture and hand
   colour block but still run the joint lookups (`joint_Lhold` etc.).
6. `makeSkeleton()`, `makeWaiter()`, the lose/explode model
   (`suit{A,B,C}-lose-mod`, loaded in `getLoseActor()`), and the cog-suit
   disguise code in `toontown/toon/Toon.py` keep using the original parts.
   The defeat animation will therefore show the original body unless a
   `<slot>_hd_lose` variant is added the same way.
7. `preloadSuits()` style preloading can ignore the new files.

Test with the offscreen harness pattern used for the other graphics work
(`PYTHONPATH=. venv/bin/python script.py`, `window-type offscreen`):
create `Suit.Suit()`, `setDNA(SuitDNA.SuitDNA())` after `newSuit('<code>')`,
`loop('neutral')`, save a screenshot; then check in the game on a street.

## 6. Joint trees of the three bodies

Indentation is parent/child.  These are the names to preserve.

### Body A (`suitA-mod`)

```
<skeleton>
  suitA
    CONSlegL
      to_coatLBack
      to_coatLFront
    CONSlegR
      to_coatRBack
      to_coatRFront
    Lh_wrist
      Lh_1
        Lh_2
      Lh_arm
      Lh_index1
        Lh_index2
      Lh_thumb1
        Lh_thumb2
    Lshoulder_arm
      Lsleeve_trans
      jnt22_1
      scale_jnt24_1
    Luparm
    Rh_wrist
      Rh_1
        Rh_2
      Rh_arm
      Rh_index1
        Rh_index2
      Rh_thumb1
        Rh_thumb2
    Rsleeve_trans
    Ruparm
    jnt24_2
      Lforearm
    jnt27_2
      Rforearm
    jnt3_2
    jnt4_2
    joint_Lhold
    joint_Rhold
    joint_head
    joint_nameTag
    joint_shadow
    null7
      jnt28_1
    scale_jnt27_1
    scale_jnt3_1
    scale_jnt4_1
    to_LegL
      to_ballL
    to_MAIN
      to_body
        joint_attachMeter
        to_shoulder
          shoulderL1
          shoulderR1
          to_head
    to_coatL
    to_coatR
    to_legR
      to_ballR
```

### Body B (`suitB-mod`)

```
<skeleton>
  suitB
    CONSlegL
      to_coatLBack
      to_coatLFront
    CONSlegR
      to_coatRBack
      to_coatRFront
    Lh_wrist
      Lh_1
        Lh_2
      Lh_arm
      Lh_index1
        Lh_index2
      Lh_thumb1
        Lh_thumb2
    Luparm
    Rh_wrist
      Rh_1
        Rh_2
      Rh_arm
      Rh_index1
        Rh_index2
      Rh_thumb1
        Rh_thumb2
    Rsleeve_trans
    Ruparm
    cons_Lwrist
    jnt1_2
    jnt2_2
    jnt3_2
    jnt4_1
    jnt8_1
    jnt9_2
      Rforearm
    joint_Lhold
    joint_Rhold
    joint_head
    joint_nameTag
    joint_shadow
    scale_jnt1_1
    scale_jnt2_1
    scale_jnt3_1
    scale_jnt9_1
    to_MAIN
      to_body1
        joint_attachMeter
        to_SHOULDER
          shoulderL1
          shoulderR1
          to_head
    to_coatl
    to_coatr
    to_legL
      to_ballL
    to_legR
      to_ballR
```

### Body C (`suitC-mod`)

```
<skeleton>
  suitC
    CONSlegL
      to_coatLBack
      to_coatLFront
    CONSlegR
      to_coatRBack
      to_coatRFront
    Lh_wrist
      Lh_1
        Lh_2
      Lh_arm
      Lh_index1
        Lh_index2
      Lh_thumb1
        Lh_thumb2
      LupVct
    Lshoulder_arm
      Lsleeve_trans
      null5
        jnt23_1
      scale_jnt26_1
    Luparm
    Rh_wrist
      Rh_5
        Rh_6
      Rh_arm
      Rh_index5
        Rh_index6
      Rh_thumb7
        Rh_thumb8
      RupVct
    Rshoulder_arm
      cons_Rwrist
        Rsleeve_trans
      null4
        jnt24_1
      scale_jnt27_1
    Ruparm
    jnt13_1
      jnt13_2
      to_coatr
    jnt14_1
      jnt14_2
      to_coatl
    jnt26_2
      Lforearm
    jnt27_2
      Rforearm
    joint_Lhold
    joint_Rhold
    joint_head
    joint_nameTag
    joint_shadow
    to_MAIN
      to_body1
        joint_attachMeter
        to_SHOULDER
          shoulderL1
          shoulderR1
          to_head
    to_legL
      to_ballL
    to_legR
      to_ballR
```

## 7. Animation files per body

Each is `suit<Body>-<name>.bam` under some `resources/phase_*/models/char/`.

- **A:** anvil-drop, awalk, cigar-smoke, drop, effort, fingerwag, flailing, fountain-pen, glower, golf-club-swing, hypnotize, landing, leftsit-hungry, lose, lured, magic1, magic2, magic3, neutral, phone, pickpocket, pie-small, rake, rightsit-hungry, roll-o-dex, rubber-stamp, sidestep-left, sidestep-right, sit, sit-angry, sit-eat-in, sit-eat-loop, sit-eat-out, sit-lose, slip-backward, slip-forward, smile, soak, song-and-dance, speak, squirt-large, squirt-small, throw-object, throw-paper, tray-neutral, tray-walk, tug-o-war, victory, walk, walknreach
- **B:** anvil-drop, drop, effort, finger-wag, flailing, hold-eraser, hold-pencil, hypnotize, jump, landing, lose, lured, magic1, magic2, magic3, neutral, pen-squirt, pencil-sharpener, phone, pickpocket, pie-small, rake, roll-o-dex, sidestep-left, sidestep-right, slip-backward, slip-forward, soak, speak, squirt-large, squirt-small, stomp, throw-object, throw-paper, tray-neutral, tray-walk, tug-o-war, victory, walk, walknreach
- **C:** anvil-drop, drop, effort, finger-wag, flailing, fountain-pen, glower, hypnotize, landing, leftsit-hungry, lose, lured, magic1, magic2, neutral, pencil-sharpener, phone, pickpocket, pie-small, rake, rightsit-hungry, rubber-stamp, shredder, sidestep-left, sidestep-right, sit, sit-angry, sit-eat-in, sit-eat-loop, sit-eat-out, sit-lose, slip-backward, slip-forward, soak, speak, squirt-large, squirt-small, throw-paper, tray-neutral, tray-walk, tug-o-war, victory, walk, walknreach, watercooler
