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
                          Point3, AlphaTestAttrib, RenderAttrib, TexGenAttrib, TextureStage,
                          TransformState, TransparencyAttrib, Vec3, Vec4)
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
CAMERA_REACH = 1.8      # feet in front of the doorway at which the camera counts as through
ROOM_PICTURE_TONE = (0.80, 0.76, 0.72)

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
    # The real room takes over from the one that was built in advance,
    # in whatever view of it is up.
    entry = _shells.get(zoneId)
    if _view is not None and entry is not None and _view['room'] == entry[0]:
        _view['room'] = interior
        _showRoom(interior, bool(_view['inside']))
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
    if not handingOver:
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
        hidden.append(planeNp)
    _outside = (geom, hidden, stashed)
    if hidden:
        _startView(geom, hidden[0], room, 'room')


def leaveRoom():
    """Undo enterRoom.  The street itself is left to whoever comes next."""
    global _outside, _waitingLoader
    _waitingLoader = None
    if _outside is None:
        return
    geom, hidden, stashed = _outside
    _outside = None
    _stopView(leaving=True)
    # (the doorway's clip plane belongs to the view, which lets go of it
    # when the camera is out: _stopView)
    for coll in stashed:
        if not coll.isEmpty():
            coll.unstash()
    if not geom.isEmpty():
        geom.clearTag('postfx-outside')
        geom.show(ShadowCamera)
        if not handingOver:
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
    startApproach()
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
        owner.buildingInAdvance = True
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


def adopt(zoneId):
    """The server has made the room for this zone.  If it was built in
    advance, that very room is used: nothing is built twice, nothing
    changes on screen, and its lighting is already worked out.  Returns
    the room, or None."""
    global alignedZone
    entry = _shells.get(zoneId)
    if not Enabled or entry is None or entry[0].isEmpty():
        return None
    room = entry[0]
    if room.getParent() != base.render:
        room.wrtReparentTo(base.render)
    room.setName(ROOT_NAME)
    for coll in room.findAllMatches('**/+CollisionNode;+s'):
        coll.unstash()
    room.show()
    if _view is not None and _view['room'] == room:
        _showRoom(room, bool(_view['inside']))
    alignedZone = zoneId
    _adopted.add(zoneId)
    notify.info('room %s was ready behind its door' % zoneId)
    if _waitingLoader is not None:
        enterRoom(_waitingLoader)
    return room


def release(zoneId):
    """The server has taken the room away again: keep it for next time."""
    global alignedZone
    if alignedZone == zoneId:
        alignedZone = None
    if zoneId in _held:
        return      # the camera is still inside it (_stopView)
    _adopted.discard(zoneId)
    entry = _shells.get(zoneId)
    if entry is None or entry[0].isEmpty():
        return
    room = entry[0]
    room.setName('toon-interior-shell')
    room.show(ViewCameras | ShadowCamera | StreetBit)
    if not any(z == zoneId for z, _ in _doorways.values()):
        _storeShell(zoneId)


_adopted = set()


def _storeShell(zone):
    entry = _shells.get(zone)
    if zone in _adopted:
        return      # in use as the real room
    if entry is not None and not entry[0].isEmpty():
        for coll in entry[0].findAllMatches('**/+CollisionNode'):
            coll.stash()
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
        # The picture is solid.  Its alpha is whatever the room's own
        # textures left there, and would let the flat door painted on the
        # wall behind show through and flicker.
        panel.setTransparency(TransparencyAttrib.MNone, 100)
        panel.setAttrib(AlphaTestAttrib.make(RenderAttrib.MNone, 0), 100)
        # A picture of a lit place: it takes the day's light but no shadows.
        panel.setShaderInput('geomFlags', Vec4(0, 0, 1, 0), 100)
    return panels


def doorwayOpened(door, inside=False):
    """A door is swinging open: show what is behind it through the
    doorway.  From the street that is the room built in advance; from
    inside a room (inside=True) it is the street."""
    if not Enabled:
        return
    if door.doId in _doorways:
        _closeDoorway(door.doId)      # left over from the last time through
    _refreshLighting()
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
    if shell.getParent() != base.render:
        shell.wrtReparentTo(base.render)
    shell.show()
    if not (_view is not None and _view['room'] == shell and _view['inside']):
        shell.hide(ViewCameras | ShadowCamera | StreetBit)     # only the doorway picture sees it
    # Its floor and walls are solid while the door stands open, so the
    # toon can step in before the server has handed it over.
    for coll in shell.findAllMatches('**/+CollisionNode;+s'):
        coll.unstash()
    leaf = door.findDoorNode('rightDoor', True)
    if leaf is not None and not leaf.isEmpty():
        _leaves[door.doId] = leaf
    panels = _picturePanels(door, portal)
    for panel, state in panels:
        # A room is lit by its lamps, dimmer and warmer than the day
        # outside; the picture of it is toned to match what the toon
        # will walk into.
        panel.setColor(ROOM_PICTURE_TONE[0], ROOM_PICTURE_TONE[1], ROOM_PICTURE_TONE[2], 1, 100)
    _doorways[door.doId] = (zone, panels)


def _refreshLighting():
    """Has the effects look at the scene again now, so a room's surfaces
    and lamps are worked out before it is seen rather than after."""
    fx = getattr(base, 'postFx', None)
    if fx is not None:
        fx._materialScanAt = 0.0
        fx._lamp = None


def doorwayClosed(door):
    _closeDoorway(door.doId)


_leaves = {}             # door doId -> the leaf that swings open
_leavesHidden = False


def _hideLeaves(hide):
    """The camera follows the toon through the doorway, and through the
    open leaf standing in it.  The leaf is left undrawn for that moment."""
    global _leavesHidden
    if hide == _leavesHidden:
        return
    _leavesHidden = hide
    for leaf in _leaves.values():
        if not leaf.isEmpty():
            if hide:
                leaf.hide(ViewCameras)
            else:
                leaf.show(ViewCameras)


def _closeDoorway(doId):
    leaf = _leaves.pop(doId, None)
    if leaf is not None and not leaf.isEmpty():
        leaf.show(ViewCameras)
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


# ---------------------------------------------------------------------------
# Which side of the doorway the camera is on decides what is drawn.
#
# While the toon is in a room the street is still up.  With the camera out
# on the street (it trails the toon by a few feet) the building keeps its
# front and the room shows only through the doorway.  Once the camera is
# through, the room is drawn itself and the street is cut off at the
# doorway.  At the moment of crossing the two views are the same.

viewOutdoors = None      # True/False while a doorway is in play; PostFX lights by it
_view = None             # {'geom', 'plane', 'room', 'inside', 'owner'}


def _startView(geom, planeNp, room, owner):
    global _view
    _stopView()
    _view = {'geom': geom, 'plane': planeNp, 'room': room, 'inside': None, 'owner': owner}
    taskMgr.add(_viewTask, 'open-interiors-view', sort=46)
    _viewTask(None)


def _stopView(leaving=False):
    global _view, viewOutdoors
    taskMgr.remove('open-interiors-view')
    v = _view
    _view = None
    _hideLeaves(False)
    if v is None:
        viewOutdoors = None
        _setCameraCollisions(True)
        return
    geom, planeNp = v['geom'], v['plane']

    def finish():
        global viewOutdoors
        viewOutdoors = None
        if not geom.isEmpty():
            if not planeNp.isEmpty():
                geom.clearClipPlane(planeNp)
            geom.show(ShadowCamera)
        if not planeNp.isEmpty():
            planeNp.removeNode()
        _setCameraCollisions(True)
        for zone in list(_held):
            _held.discard(zone)
            release(zone)

    # Walking out, the camera is still in the room when the toon is handed
    # back to the street.  Until it has come out too, the room stays up
    # around it, the street stays cut off at the doorway, and the camera
    # is left free to follow.
    if leaving and handingOver and v['inside'] and not planeNp.isEmpty():
        plane = Plane(planeNp.node().getPlane())
        until = globalClock.getFrameTime() + 3.0
        if v['room'] is not None and not v['room'].isEmpty() and alignedZone is not None:
            _held.add(alignedZone)

        def comeOut(task):
            if globalClock.getFrameTime() > until or plane.distToPlane(base.cam.getPos(base.render)) > CAMERA_REACH:
                finish()
                return task.done
            _setCameraCollisions(False)
            return task.cont
        taskMgr.remove('open-interiors-camera-out')
        taskMgr.add(comeOut, 'open-interiors-camera-out', sort=46)
    else:
        finish()


_held = set()            # rooms kept up until the camera has left them


def _showRoom(room, inside):
    if room is None or room.isEmpty():
        return
    if inside:
        room.show(ViewCameras | ShadowCamera)
    else:
        room.hide(ViewCameras | ShadowCamera | StreetBit)


def _viewTask(task):
    global viewOutdoors
    v = _view
    if v is None:
        return None if task is None else task.done
    if v['geom'].isEmpty() or v['plane'].isEmpty():
        return None if task is None else task.cont
    # A stride short of the wall the camera's near edge is already through
    # it, so the change is made there.
    camDist = v['plane'].node().getPlane().distToPlane(base.cam.getPos(base.render))
    inside = camDist < CAMERA_REACH
    _hideLeaves(-1.0 < camDist < 5.0)
    if inside != v['inside']:
        v['inside'] = inside
        viewOutdoors = not inside
        _refreshLighting()
        if inside:
            v['geom'].setClipPlane(v['plane'])
            v['geom'].hide(ShadowCamera)
            if v['owner'] == 'room':
                for doId in [d for d, e in _doorways.items() if e[0] is not None]:
                    _closeDoorway(doId)
        else:
            v['geom'].clearClipPlane(v['plane'])
            v['geom'].show(ShadowCamera)
        _showRoom(v['room'], inside)
    # The game's camera pulls itself in front of any wall between it and
    # the toon.  With the toon through the doorway and the camera not yet,
    # that wall is the front of the building, and the camera would leap
    # eleven feet forward in one frame.  While they are on different
    # sides (or the toon is in the doorway) the camera is left to follow
    # straight through.
    avatar = getattr(base, 'localAvatar', None)
    if avatar is not None and not avatar.isEmpty():
        toonInside = v['plane'].node().getPlane().distToPlane(avatar.getPos(base.render)) < 0
        _setCameraCollisions(toonInside == inside and not _inDoorway)
    return None if task is None else task.cont


_cameraCollides = True
_inDoorway = False


def _setCameraCollisions(on):
    global _cameraCollides
    avatar = getattr(base, 'localAvatar', None)
    if avatar is None or not getattr(avatar, '_smartCamEnabled', False):
        _cameraCollides = True
        return
    line = getattr(avatar, 'ccLineNodePath', None)
    sphere = getattr(avatar, 'ccSphereNodePath', None)
    if line is None or sphere is None or line.isEmpty() or sphere.isEmpty():
        return
    if on and not _cameraCollides:
        if not avatar.ccTrav.hasCollider(line):
            avatar.ccTrav.addCollider(line, avatar.camCollisionQueue)
        if not avatar.cTrav.hasCollider(sphere):
            avatar.cTrav.addCollider(sphere, avatar.camPusher)
    elif not on:
        if avatar.ccTrav.hasCollider(line):
            avatar.ccTrav.removeCollider(line)
        if avatar.cTrav.hasCollider(sphere):
            avatar.cTrav.removeCollider(sphere)
    _cameraCollides = on


# ---------------------------------------------------------------------------
# Walking through.
#
# The game takes the toon out of the player's hands at a door and plays a
# little walk.  Here the player keeps control.  Touching the door asks the
# server to open it, as always; then the player walks in.  The wall of the
# building does not stop the toon inside the open doorway, and when the
# toon is a step past the threshold the hand-over to the room (or back to
# the street) is made behind it.

DOOR_HALF_WIDTH = 0.7    # how far off the middle of the open leaf the toon may be
HAND_OVER_AT = 0.9       # feet past the threshold
DOORWAY_REACH = 4.2      # how far to either side of the open leaf the doorway is felt

walk = None              # the doorway being walked through
handingOver = False      # from crossing the threshold until arriving
walkedThrough = False    # set at the crossing; the arrival door clears it


def beginWalk(door, inside):
    """The local toon touched this door.  Returns True if it can be
    walked through (its room was built in advance, or it is a room's own
    door); otherwise the game's own door sequence is used."""
    global walk
    if not Enabled or not ConfigVariableBool('want-walk-through-doors', True).value:
        return False
    endWalk()
    if inside:
        if not isAligned() or _outside is None:
            return False
        other = door.getDoorNodePath()
        if other is None or other.isEmpty():
            return False
        pos, hpr = other.getPos(base.render), other.getHpr(base.render)
        offset = door.doorX * other.getScale(base.render)[0]
    else:
        from toontown.hood import ZoneUtil
        zone = interiorZone(ZoneUtil.getBranchZone(door.zoneId), door.block)
        street = doorTransform(base.cr.playGame.dnaStore, door.block)
        if zone not in _shells or street is None:
            return False
        pos, hpr = street.getPos(), street.getHpr()
        offset = door.doorX
    frame = base.render.attachNewNode('open-interior-doorway')
    frame.setPosHpr(pos, hpr)
    if not inside and _shellLoader is not None and getattr(_shellLoader, 'geom', None) is not None:
        # If the camera gets through the doorway before the server has
        # handed the toon over, it must find the room there already.
        toStreet = base.render.getRelativeVector(frame, Vec3(0, -1, 0))
        toStreet.setZ(0)
        toStreet.normalize()
        planeNp = base.render.attachNewNode(PlaneNode('open-interior-clip', Plane(toStreet, Point3(pos) + toStreet * FACADE_DEPTH)))
        _startView(_shellLoader.geom, planeNp, _shells[zone][0], 'walk')
    walk = {'door': door, 'inside': inside, 'frame': frame, 'x': offset, 'done': False,
            'street': False}
    taskMgr.add(_walkTask, 'open-interiors-walk', sort=44)
    return True


def walkDone(door):
    return walk is not None and walk['door'] is door and walk['done']


def endWalk():
    global walk
    taskMgr.remove('open-interiors-walk')
    global _inDoorway
    _inDoorway = False
    if walk is not None:
        if not walk['frame'].isEmpty():
            walk['frame'].removeNode()
        walk = None
    if _view is not None and _view['owner'] == 'walk':
        _stopView()
    _setWalls(True)


_wallsOn = True


def _setWalls(on):
    """Turns the local toon's wall collisions on or off.  Checked against
    the traverser every time: the game adds the wall sphere back itself
    whenever the controls are switched on."""
    global _wallsOn
    avatar = getattr(base, 'localAvatar', None)
    walker = getattr(getattr(avatar, 'controlManager', None), 'currentControls', None)
    sphere = getattr(walker, 'cWallSphereNodePath', None)
    trav = getattr(walker, 'cTrav', None)
    pusher = getattr(walker, 'pusher', None)
    if sphere is None or sphere.isEmpty() or trav is None or pusher is None:
        _wallsOn = True
        return
    has = trav.hasCollider(sphere)
    if on and not has and (not _wallsOn) and getattr(walker, 'collisionsActive', 1):
        trav.addCollider(sphere, pusher)
    elif not on and has:
        trav.removeCollider(sphere)
    _wallsOn = on


def _doorIsOpen(door):
    # Open enough to go through: pushed open by the player a moment ago,
    # or held open by the server.
    try:
        if door.isSwungOpen():
            return True
        return door.fsm.getCurrentState().getName() == 'open'
    except Exception:
        return False


def _walkTask(task):
    global handingOver, walkedThrough
    w = walk
    avatar = getattr(base, 'localAvatar', None)
    if w is None or avatar is None or avatar.isEmpty() or w['frame'].isEmpty():
        endWalk()
        return task.done
    p = avatar.getPos(w['frame'])
    lateral = p[0] - w['x']
    passable = w['done'] or _doorIsOpen(w['door'])
    # Anywhere across the pair of doors counts: only one leaf opens, and
    # a toon heading for the other is eased across to it.
    global _inDoorway
    near = passable and abs(lateral) < DOORWAY_REACH and -3.5 < p[1] < 6.0
    _inDoorway = near
    _setWalls(not near)
    if near and -2.5 < p[1] < 2.5 and abs(lateral) > DOOR_HALF_WIDTH:
        want = max(-DOOR_HALF_WIDTH, min(DOOR_HALF_WIDTH, lateral))
        step = 14.0 * globalClock.getDt()
        moved = lateral + max(-step, min(step, want - lateral))
        avatar.setX(w['frame'], w['x'] + moved)
        if abs(moved) > DOOR_HALF_WIDTH + 0.6 and p[1] > -1.4:
            # not lined up yet: wait at the wall rather than pass through it
            avatar.setY(w['frame'], -1.4)
    if w['inside'] and _outside is not None:
        # Walking out: the street has to be solid under the toon before
        # it gets there.
        want = p[1] > -1.0
        if want != w['street']:
            w['street'] = want
            for coll in _outside[2]:
                if not coll.isEmpty():
                    if want:
                        coll.unstash()
                    else:
                        coll.stash()
    if near and not w['done'] and p[1] > HAND_OVER_AT:
        w['done'] = True
        handingOver = True
        walkedThrough = True
        notify.info('walked through door %s' % w['door'].doId)
        messenger.send('doorDoneEvent', [w['door'].getRequestStatus()])
        return task.cont
    if w['done'] and not handingOver and not near:
        endWalk()
        return task.done
    return task.cont


# ---------------------------------------------------------------------------
# Doors open as the toon comes up to them.
#
# The game opens a door when the toon bumps into it, which means stopping
# against it first.  Here a shop door is asked to open while the toon is
# still a few strides off and heading for it, so it stands open by the
# time the toon gets there and nothing breaks its stride.

APPROACH_FAR = 8.5       # feet in front of the door at which it is asked to open
APPROACH_SIDE = 3.2      # feet to either side of the open leaf
_doorList = (0.0, [])


def startApproach():
    if Enabled and not taskMgr.hasTaskNamed('open-interiors-approach'):
        taskMgr.add(_approachTask, 'open-interiors-approach', sort=43)


def _doorPlace(door):
    """(position, heading, sideways offset of the open leaf) of a door."""
    cached = getattr(door, 'openInteriorPlace', None)
    if cached is not None:
        return cached
    from toontown.building import DoorTypes
    place = None
    if door.doorType == DoorTypes.EXT_STANDARD:
        street = doorTransform(base.cr.playGame.dnaStore, door.block)
        if street is not None:
            place = (Point3(street.getPos()), street.getHpr()[0], door.doorX)
    else:
        other = door.getDoorNodePath()
        if other is not None and not other.isEmpty():
            place = (other.getPos(base.render), other.getHpr(base.render)[0],
                     door.doorX * other.getScale(base.render)[0])
            if isAligned():
                door.openInteriorPlace = place
            return place
    door.openInteriorPlace = place
    return place


def _approachTask(task):
    global _doorList
    import math
    from direct.showbase.InputStateGlobal import inputState
    avatar = getattr(base, 'localAvatar', None)
    playGame = getattr(getattr(base, 'cr', None), 'playGame', None)
    if avatar is None or avatar.isEmpty() or playGame is None or walk is not None:
        return task.cont
    place = playGame.getPlace()
    try:
        walking = place.fsm.getCurrentState().getName() == 'walk'
    except Exception:
        walking = False
    if not walking or not inputState.isSet('forward'):
        return task.cont
    now = globalClock.getFrameTime()
    if now - _doorList[0] > 0.5:
        from toontown.building import DoorTypes
        from toontown.building.DistributedDoor import DistributedDoor
        doors = [d for d in base.cr.doId2do.values()
                 if isinstance(d, DistributedDoor) and d.doorType in (DoorTypes.EXT_STANDARD, DoorTypes.INT_STANDARD)]
        _doorList = (now, doors)
    pos = avatar.getPos(base.render)
    heading = math.radians(avatar.getH(base.render))
    fx, fy = -math.sin(heading), math.cos(heading)
    for door in _doorList[1]:
        if door.isEmpty() if hasattr(door, 'isEmpty') else False:
            continue
        try:
            state = door.fsm.getCurrentState().getName()
        except Exception:
            continue
        if state != 'closed' or getattr(door, 'walkThrough', False):
            continue
        where = _doorPlace(door)
        if where is None:
            continue
        at, h, offset = where
        if abs(pos[2] - at[2]) > 4.0:
            continue
        dh = math.radians(h)
        # the door's own axes: +y through the door, +x along the wall
        ax, ay = math.cos(dh), math.sin(dh)
        bx, by = -math.sin(dh), math.cos(dh)
        dx, dy = pos[0] - at[0], pos[1] - at[1]
        along, through = dx * ax + dy * ay, dx * bx + dy * by
        if not (-APPROACH_FAR < through < -0.5 and abs(along - offset) < APPROACH_SIDE):
            continue
        if fx * bx + fy * by < 0.6:
            continue        # not heading for it
        door.doorTrigger()
        break
    return task.cont
