"""Rooms that stand behind their own doors.

The game keeps every shop interior at the middle of an empty world: walk
through a door and the street is thrown away, the room is put up, and the
toon is moved to it behind a closed iris.  Here the room is built where it
belongs instead, behind the door of its own building, and the street
stays up around it.  Walking in moves nothing: the toon and the camera
keep the place and heading they had on the pavement.

    want-open-interiors   #t/#f (default #t)

What it does, piece by piece:

* place(): turns and moves a freshly built room so its door stands in the
  building's doorway, back to back with the street door.
* enterRoom() / leaveRoom(): called by the room's Place.  Puts the street
  back on screen while the toon is indoors, without its collisions (the
  backs of the buildings would otherwise wall the room in), without its
  shadows, and cut off at the doorway so nothing of it stands in the room.
"""

from panda3d.core import (BitMask32, ConfigVariableBool, LMatrix4, NodePath, Plane, PlaneNode,
                          Point3, TexGenAttrib, TextureStage, TransformState, Vec3, Vec4)
from direct.directnotify import DirectNotifyGlobal

notify = DirectNotifyGlobal.directNotify.newCategory('OpenInteriors')

Enabled = ConfigVariableBool('want-open-interiors', True).value

ROOT_NAME = 'toon-interior-root'
# The main camera and the effects' surface pass.
ViewCameras = BitMask32.bit(0) | BitMask32.bit(7)
ShadowCamera = BitMask32.bit(2)
# How far in front of the doorway the street begins to be drawn: past the
# wall of the building itself, short of its awning and sign.
FACADE_DEPTH = 0.35

# zone of the room now standing behind its door, or None
alignedZone = None
_outside = None          # (street geometry, [clip planes], [collisions stashed])
# True from entering a placed room until the toon is back on the street:
# the walk out is as seamless as the walk in.
cameFromRoom = False
_waitingLoader = None    # the place was entered before its room arrived


def doorTransform(dnaStore, block):
    """Where the street door of this block stands, as a TransformState."""
    try:
        posHpr = dnaStore.getDoorPosHprFromBlockNumber(int(block))
    except Exception:
        return None
    return TransformState.makePosHpr(posHpr.getPos(), posHpr.getHpr())


def place(interior, zoneId, block, dnaStore):
    """Stands a room behind the street door of its block.  Returns True
    if it could be placed."""
    global alignedZone
    alignedZone = None
    interior.setName(ROOT_NAME)
    if not Enabled or dnaStore is None:
        return False
    street = doorTransform(dnaStore, block)
    door = interior.find('**/door_origin;+s')
    if street is None or door.isEmpty():
        return False
    # The room's door, without the 0.8 scale the game gives it.
    inRoom = TransformState.makePosHpr(door.getPos(interior), door.getHpr(interior))
    # Back to back: the room's door looks into the room, the street door
    # into the building, so one is the other turned half round.
    turned = TransformState.makeHpr(Vec3(180, 0, 0))
    # door-in-room * room-in-world == turned * street-door-in-world
    world = street.compose(turned)
    room = world.compose(inRoom.getInverse())
    interior.setTransform(room)
    alignedZone = zoneId
    # The real room takes over from the one that was built in advance.
    _storeShell(zoneId)
    if _waitingLoader is not None:
        enterRoom(_waitingLoader)
    notify.info('room %s stands behind door %s' % (zoneId, block))
    return True


def isAligned(zoneId=None):
    return Enabled and alignedZone is not None and (zoneId is None or zoneId == alignedZone)


def roomRoot():
    return base.render.find(ROOT_NAME)


def enterRoom(loader):
    """The toon is in a room: bring the street back around it."""
    global _outside, cameFromRoom, _waitingLoader
    leaveRoom()
    cameFromRoom = False
    if not isAligned():
        # The room itself may arrive from the server a moment after the
        # toon does; place() comes back here when it has been stood up.
        _waitingLoader = loader if Enabled else None
        return
    _waitingLoader = None
    cameFromRoom = True
    geom = getattr(loader, 'geom', None)
    room = roomRoot()
    if geom is None or geom.isEmpty() or room.isEmpty():
        return
    geom.reparentTo(base.render)
    # A street is kept in sections that are put away as the toon moves
    # along it; the ones still fading out when the toon went indoors end
    # up put away for good.  Bring every section back.
    for section in geom.getStashedChildren():
        if section.getName().split(':')[0].isdigit():
            section.unstash()
            section.clearColorScale()
            section.clearTransparency()
    geom.setTag('postfx-outside', '1')
    geom.hide(ShadowCamera)
    stashed = []
    for coll in geom.findAllMatches('**/+CollisionNode'):
        coll.stash()
        stashed.append(coll)
    hidden = []
    # The room stands where the back of its building, the fence behind it
    # and the lawn beyond are.  The street is drawn only on the street
    # side of the doorway, which is all that can be seen through the door.
    door = room.find('**/door_origin')
    if not door.isEmpty():
        at = door.getPos(base.render)
        # The room's door looks into the room; the street is behind it.
        toStreet = base.render.getRelativeVector(door, Vec3(0, 1, 0))
        toStreet.setZ(0)
        toStreet.normalize()
        plane = PlaneNode('open-interior-clip', Plane(toStreet, at + toStreet * FACADE_DEPTH))
        planeNp = base.render.attachNewNode(plane)
        geom.setClipPlane(planeNp)
        hidden.append(planeNp)
    _outside = (geom, hidden, stashed)


def leaveRoom():
    """Undo enterRoom.  The street itself is left to whoever comes next."""
    global _outside, _waitingLoader
    _waitingLoader = None
    if _outside is None:
        return
    geom, hidden, stashed = _outside
    _outside = None
    for planeNp in hidden:
        if not geom.isEmpty():
            geom.clearClipPlane(planeNp)
        planeNp.removeNode()
    for coll in stashed:
        if not coll.isEmpty():
            coll.unstash()
    if not geom.isEmpty():
        geom.clearTag('postfx-outside')
        geom.show(ShadowCamera)
        geom.reparentTo(base.hidden)


# ---------------------------------------------------------------------------
# Rooms built in advance, and the view of them through an open door.
#
# When a street or playground comes up, the room of every shop on it is
# built too (one a frame, so nothing stalls) and kept aside.  When a street
# door opens, its room is stood behind it and drawn, from the player's own
# camera, into a picture that is laid over the black panel the game puts in
# an open doorway: the room is seen through the door before the toon steps
# in.  The building's front has no real hole in it, so this picture is the
# doorway.

PortalBit = BitMask32.bit(9)     # the camera that draws a room for a street doorway
StreetBit = BitMask32.bit(10)    # the camera that draws the street for a room's doorway
_shells = {}                     # room zone -> (room, the object that built it)
_shellLoader = None
_shellStore = NodePath('open-interior-shells')
_pending = []
_portals = {}                    # camera bit -> (buffer, camera)
_doorways = {}                   # door doId -> (room zone, [(panel, state)])


def interiorZone(branchZone, block):
    return branchZone - branchZone % 100 + 500 + int(block)


def prebuild(loader, branchZone):
    """Called when a street or playground comes up: build its rooms."""
    global _shellLoader, _pending
    if not Enabled or _shellLoader is loader:
        return
    clearShells()
    _shellLoader = loader
    geom = getattr(loader, 'geom', None)
    dnaStore = base.cr.playGame.dnaStore
    if geom is None or dnaStore is None:
        return
    geom.hide(PortalBit | StreetBit)
    _pending = []
    for i in range(dnaStore.getNumBlockNumbers()):
        block = dnaStore.getBlockNumberAt(i)
        kind = dnaStore.getBlockBuildingType(block)
        # Headquarters and the kart shop have rooms of their own kind,
        # with more than one door; every other shop is built here.
        if kind in ('hq', 'kartshop') or doorTransform(dnaStore, block) is None:
            continue
        _pending.append((interiorZone(branchZone, block), block, kind))
    taskMgr.remove('open-interiors-prebuild')
    if _pending:
        taskMgr.add(_prebuildTask, 'open-interiors-prebuild')


def _prebuildTask(task):
    if not _pending:
        notify.info('%d rooms built in advance' % len(_shells))
        return task.done
    zone, block, kind = _pending.pop(0)
    if zone not in _shells and zone != alignedZone:
        _buildShell(zone, block, kind)
    return task.cont


def _buildShell(zone, block, kind):
    global alignedZone
    from toontown.building import DistributedGagshopInterior, DistributedPetshopInterior, DistributedToonInterior
    cls = {'gagshop': DistributedGagshopInterior.DistributedGagshopInterior,
           'petshop': DistributedPetshopInterior.DistributedPetshopInterior}.get(
               kind, DistributedToonInterior.DistributedToonInterior)
    keep = alignedZone
    try:
        owner = cls(base.cr)
        owner.zoneId = zone
        owner.block = block
        owner.savedBy = None
        owner.setup()
    except Exception as e:
        notify.warning('could not build room %s in advance: %r' % (zone, e))
        alignedZone = keep
        stray = base.render.find(ROOT_NAME) if keep is None else NodePath()
        if not stray.isEmpty():
            stray.removeNode()
        return
    placed = alignedZone == zone
    alignedZone = keep
    shell = owner.interior
    shell.setName('toon-interior-shell')
    if not placed:
        shell.removeNode()
        return
    for coll in shell.findAllMatches('**/+CollisionNode'):
        coll.stash()
    shell.wrtReparentTo(_shellStore)
    _shells[zone] = (shell, owner)


def _storeShell(zone):
    entry = _shells.get(zone)
    if entry is not None and not entry[0].isEmpty():
        entry[0].wrtReparentTo(_shellStore)


def clearShells():
    global _shellLoader, _pending
    taskMgr.remove('open-interiors-prebuild')
    _pending = []
    for doId in list(_doorways.keys()):
        _closeDoorway(doId)
    for shell, owner in _shells.values():
        fish = getattr(owner, 'fish', None)
        if fish is not None:
            try:
                fish.stop()
                fish.cleanup()
            except Exception:
                pass
        if not shell.isEmpty():
            shell.removeNode()
    _shells.clear()
    _shellLoader = None


def _ensurePortal(bit):
    key = bit.getWord()
    if key in _portals:
        return _portals[key]
    buf = base.win.makeTextureBuffer('open-interior-portal-%d' % key,
                                     max(base.win.getXSize(), 64), max(base.win.getYSize(), 64))
    if buf is None:
        return None
    buf.setSort(-200)
    # Dark for a room; for the street, the colour of a clear sky, which
    # shows wherever the doorway looks past the scenery.
    buf.setClearColor(Vec4(0.45, 0.66, 0.95, 1) if bit == StreetBit else Vec4(0, 0, 0, 1))
    cam = base.makeCamera(buf, lens=base.camLens, mask=bit)
    cam.reparentTo(base.cam)
    cam.setPosHpr(0, 0, 0, 0, 0, 0)
    _portals[key] = (buf, cam)
    return _portals[key]


def _picturePanels(door, portal):
    """Lays the portal camera's picture over the black panels of an
    open doorway.  Returns [(panel, its state before)]."""
    buf, cam = portal
    panels = []
    stage = TextureStage.getDefault()
    for name in ('doorFrameHoleRight', 'doorFrameHoleLeft'):
        panel = door.findDoorNode(name, True)
        if panel is None or panel.isEmpty():
            continue
        panels.append((panel, panel.getState()))
        panel.setColor(1, 1, 1, 1, 100)
        panel.setTexGen(stage, TexGenAttrib.MWorldPosition)
        panel.setTexProjector(stage, base.render, cam)
        panel.setTexture(buf.getTexture(), 100)
        # A picture of a lit place: it takes the day's light but no shadows.
        panel.setShaderInput('geomFlags', Vec4(0, 0, 1, 0), 100)
    return panels


def doorwayOpened(door, inside=False):
    """A door is swinging open: show what is behind it through the
    doorway.  From the street that is the room built in advance; from
    inside a room (inside=True) it is the street."""
    if not Enabled or door.doId in _doorways:
        return
    if inside:
        room = roomRoot()
        if not isAligned() or room.isEmpty() or _outside is None:
            return
        portal = _ensurePortal(StreetBit)
        if portal is None:
            return
        room.hide(StreetBit)
        _outside[0].show(StreetBit)
        _doorways[door.doId] = (None, _picturePanels(door, portal))
        return
    from toontown.hood import ZoneUtil
    zone = interiorZone(ZoneUtil.getBranchZone(door.zoneId), door.block)
    entry = _shells.get(zone)
    if entry is None or entry[0].isEmpty():
        return
    portal = _ensurePortal(PortalBit)
    if portal is None:
        return
    shell = entry[0]
    shell.wrtReparentTo(base.render)
    shell.show()
    shell.hide(ViewCameras | ShadowCamera | StreetBit)     # only the doorway picture sees it
    _doorways[door.doId] = (zone, _picturePanels(door, portal))


def doorwayClosed(door):
    _closeDoorway(door.doId)


def _closeDoorway(doId):
    entry = _doorways.pop(doId, None)
    if entry is None:
        return
    zone, panels = entry
    for panel, state in panels:
        if not panel.isEmpty():
            hidden = panel.isHidden()
            panel.setState(state)
            panel.clearTexProjector()
            if hidden:
                panel.hide()
            else:
                panel.show()
    if zone is not None and not any(z == zone for z, _ in _doorways.values()):
        _storeShell(zone)
