from panda3d.core import ConfigVariableBool
from panda3d.core import BitMask32, NodePath, Point3, VBase3, Vec3
from panda3d.otp import Nametag, NametagGroup

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.ClockDelta import globalClockDelta
from direct.distributed.DistributedObject import DistributedObject
from direct.fsm.ClassicFSM import ClassicFSM
from direct.fsm.State import State
from direct.interval.IntervalGlobal import (
    ActorInterval,
    Func,
    HprInterval,
    LerpHprInterval,
    LerpPosHprInterval,
    LerpPosInterval,
    Parallel,
    PosHprInterval,
    Sequence,
    SoundInterval,
    Wait
)

from direct.showbase.MessengerGlobal import messenger
from direct.task.TaskManagerGlobal import taskMgr

from toontown.building import DoorTypes
from toontown.building import FADoorCodes
from toontown.distributed.DelayDeletable import DelayDeletable
from toontown.distributed.DelayDelete import DelayDelete, cleanupDelayDeletes
from toontown.hood import ZoneUtil
from toontown.suit.Suit import Suit
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toontowngui import TTDialog
from toontown.toontowngui.TeaserPanel import TeaserPanel
from toontown.toonbase import FrameHold


# Walk through doors without the iris wipe: the picture of the toon in the
# doorway is held while the street is swapped for the room (or the room for
# the street), the toon arrives in the pose it left in, and the held
# picture dissolves into the new place.  See FrameHold.
QuickDoors = ConfigVariableBool('want-quick-doors', True).value
# How far through the doorway the toon is when the places are swapped,
# and how far behind it the camera sits.
DoorSwapDepth = 2.0
DoorCamBack = 8.0
# The main camera and the effects' surface pass; shadows are left alone.
ViewCameras = BitMask32.bit(0) | BitMask32.bit(7)

class DistributedDoor(DistributedObject, DelayDeletable):
    notify = directNotify.newCategory('DistributedDoor')

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        self.openSfx = base.loader.loadSfx('phase_3.5/audio/sfx/Door_Open_1.ogg')
        self.closeSfx = base.loader.loadSfx('phase_3.5/audio/sfx/Door_Close_1.ogg')
        self.nametag = None
        self.fsm = ClassicFSM('DistributedDoor_right', [State('off', self.enterOff, self.exitOff, ['closing',
          'closed',
          'opening',
          'open']),
         State('closing', self.enterClosing, self.exitClosing, ['closed', 'opening']),
         State('closed', self.enterClosed, self.exitClosed, ['opening']),
         State('opening', self.enterOpening, self.exitOpening, ['open']),
         State('open', self.enterOpen, self.exitOpen, ['closing', 'open'])], 'off', 'off')
        self.fsm.enterInitialState()
        self.exitDoorFSM = ClassicFSM('DistributedDoor_left', [State('off', self.exitDoorEnterOff, self.exitDoorExitOff, ['closing',
          'closed',
          'opening',
          'open']),
         State('closing', self.exitDoorEnterClosing, self.exitDoorExitClosing, ['closed', 'opening']),
         State('closed', self.exitDoorEnterClosed, self.exitDoorExitClosed, ['opening']),
         State('opening', self.exitDoorEnterOpening, self.exitDoorExitOpening, ['open']),
         State('open', self.exitDoorEnterOpen, self.exitDoorExitOpen, ['closing', 'open'])], 'off', 'off')
        self.exitDoorFSM.enterInitialState()
        self.specialDoorTypes = {DoorTypes.EXT_HQ: 0,
         DoorTypes.EXT_COGHQ: 0,
         DoorTypes.INT_COGHQ: 0,
         DoorTypes.EXT_KS: 0,
         DoorTypes.INT_KS: 0}
        self.doorX = 1.5

    def generate(self):
        DistributedObject.generate(self)
        self.avatarTracks = []
        self.avatarExitTracks = []
        self.avatarIDList = []
        self.avatarExitIDList = []
        self.doorTrack = None
        self.doorExitTrack = None

    def disable(self):
        self.clearNametag()
        taskMgr.remove(self.checkIsDoorHitTaskName())
        self.ignore(self.getEnterTriggerEvent())
        self.ignore(self.getExitTriggerEvent())
        self.ignore('clearOutToonInterior')
        self.fsm.request('off')
        self.exitDoorFSM.request('off')
        if 'building' in self.__dict__:
            del self.building

        self.finishAllTracks()
        self.avatarIDList = []
        self.avatarExitIDList = []
        if hasattr(self, 'tempDoorNodePath'):
            self.tempDoorNodePath.removeNode()
            del self.tempDoorNodePath

        DistributedObject.disable(self)

    def delete(self):
        del self.fsm
        del self.exitDoorFSM
        del self.openSfx
        del self.closeSfx
        DistributedObject.delete(self)

    def wantsNametag(self):
        return not ZoneUtil.isInterior(self.zoneId)

    def setupNametag(self):
        if not self.wantsNametag():
            return

        if self.nametag == None:
            self.nametag = NametagGroup()
            self.nametag.setFont(ToontownGlobals.getBuildingNametagFont())
            if TTLocalizer.BuildingNametagShadow:
                self.nametag.setShadow(*TTLocalizer.BuildingNametagShadow)

            self.nametag.setContents(Nametag.CName)
            self.nametag.setColorCode(NametagGroup.CCToonBuilding)
            self.nametag.setActive(0)
            self.nametag.setAvatar(self.getDoorNodePath())
            self.nametag.setObjectCode(self.block)
            name = self.cr.playGame.dnaStore.getTitleFromBlockNumber(self.block)
            self.nametag.setName(name)
            self.nametag.manage(base.marginManager)

    def clearNametag(self):
        if self.nametag != None:
            self.nametag.unmanage(base.marginManager)
            self.nametag.setAvatar(NodePath())
            self.nametag = None

    def getTriggerName(self):
        if self.doorType == DoorTypes.INT_HQ or self.doorType in self.specialDoorTypes:
            return 'door_trigger_' + str(self.block) + '_' + str(self.doorIndex)
        else:
            return 'door_trigger_' + str(self.block)

    def getTriggerName_wip(self):
        name = 'door_trigger_%d' % (self.doId,)
        return name

    def getEnterTriggerEvent(self):
        return 'enter' + self.getTriggerName()

    def getExitTriggerEvent(self):
        return 'exit' + self.getTriggerName()

    def hideDoorParts(self):
        if self.doorType in self.specialDoorTypes:
            self.hideIfHasFlat(self.findDoorNode('rightDoor'))
            self.hideIfHasFlat(self.findDoorNode('leftDoor'))
            self.findDoorNode('doorFrameHoleRight').hide()
            self.findDoorNode('doorFrameHoleLeft').hide()

    def setTriggerName(self):
        if self.doorType in self.specialDoorTypes:
            building = self.getBuilding()
            doorTrigger = building.find('**/door_' + str(self.doorIndex) + '/**/door_trigger*')
            doorTrigger.node().setName(self.getTriggerName())

    def setTriggerName_wip(self):
        building = self.getBuilding()
        doorTrigger = building.find('**/door_%d/**/door_trigger_%d' % (self.doorIndex, self.block))
        if doorTrigger.isEmpty():
            doorTrigger = building.find('**/door_trigger_%d' % (self.block,))

        if doorTrigger.isEmpty():
            doorTrigger = building.find('**/door_%d/**/door_trigger_*' % (self.doorIndex,))

        if doorTrigger.isEmpty():
            doorTrigger = building.find('**/door_trigger_*')

        doorTrigger.node().setName(self.getTriggerName())

    def setZoneIdAndBlock(self, zoneId, block):
        self.zoneId = zoneId
        self.block = block

    def setDoorType(self, doorType):
        self.notify.debug('Door type = ' + str(doorType) + ' on door #' + str(self.doId))
        self.doorType = doorType

    def setDoorIndex(self, doorIndex):
        self.doorIndex = doorIndex

    def setSwing(self, flags):
        self.leftSwing = flags & 1 != 0
        self.rightSwing = flags & 2 != 0

    def setOtherZoneIdAndDoId(self, zoneId, distributedObjectID):
        self.otherZoneId = zoneId
        self.otherDoId = distributedObjectID

    def setState(self, state, timestamp):
        self.fsm.request(state, [globalClockDelta.localElapsedTime(timestamp)])

    def setExitDoorState(self, state, timestamp):
        self.exitDoorFSM.request(state, [globalClockDelta.localElapsedTime(timestamp)])

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        self.doPostAnnounceGenerate()

    def doPostAnnounceGenerate(self):
        if self.doorType == DoorTypes.INT_STANDARD:
            self.bHasFlat = True
        else:
            self.bHasFlat = not self.findDoorNode('door*flat', True).isEmpty()

        self.hideDoorParts()
        self.setTriggerName()
        self.accept(self.getEnterTriggerEvent(), self.doorTrigger)
        self.acceptOnce('clearOutToonInterior', self.doorTrigger)
        self.setupNametag()

    def getBuilding(self):
        if 'building' not in self.__dict__:
            if self.doorType == DoorTypes.INT_STANDARD:
                door = base.render.find('**/leftDoor;+s')
                self.building = door.getParent()
            elif self.doorType == DoorTypes.INT_HQ:
                door = base.render.find('**/door_0')
                self.building = door.getParent()
            elif self.doorType == DoorTypes.INT_KS:
                self.building = base.render.find('**/KartShop_Interior*')
            elif self.doorType == DoorTypes.EXT_STANDARD or self.doorType == DoorTypes.EXT_HQ or self.doorType == DoorTypes.EXT_KS:
                self.building = self.cr.playGame.hood.loader.geom.find('**/??' + str(self.block) + ':*_landmark_*_DNARoot;+s')
                if self.building.isEmpty():
                    self.building = self.cr.playGame.hood.loader.geom.find('**/??' + str(self.block) + ':animated_building_*_DNARoot;+s')
            elif self.doorType == DoorTypes.EXT_COGHQ or self.doorType == DoorTypes.INT_COGHQ:
                self.building = self.cr.playGame.hood.loader.geom
            else:
                self.notify.error('No such door type as ' + str(self.doorType))

        return self.building

    def getBuilding_wip(self):
        if 'building' not in self.__dict__:
            if 'block' in self.__dict__:
                self.building = self.cr.playGame.hood.loader.geom.find('**/??' + str(self.block) + ':*_landmark_*_DNARoot;+s')
            else:
                self.building = self.cr.playGame.hood.loader.geom
                print('---------------- door is interior -------')

        return self.building

    def readyToExit(self):
        if QuickDoors:
            self.arriveThroughDoor()
        else:
            base.transitions.fadeScreen(1.0)
        self.sendUpdate('requestExit')

    def arriveThroughDoor(self):
        """The new place is up and this is the door the local toon comes
        out of.  Rather than wait behind a black screen for the server to
        open the door, put the toon and camera where they were on the
        other side of it, already through the open door and walking, and
        dissolve the held picture of the old place into this."""
        avatar = base.localAvatar
        otherNP = self.getDoorNodePath()
        if otherNP is None or otherNP.isEmpty():
            base.transitions.noTransitions()
            FrameHold.release(0.3)
            return
        if hasattr(avatar, 'stopSmooth'):
            avatar.stopSmooth()
        avatar.setPosHpr(otherNP, -self.doorX, -DoorSwapDepth, ToontownGlobals.FloorOffset, 180, 0, 0)
        avatar.setParent(ToontownGlobals.SPRender)
        avatar.setAnimState('walk')
        base.camera.setPosHpr(otherNP, -self.doorX, DoorCamBack - DoorSwapDepth, avatar.getHeight(), 180, 0, 0)
        self.poseExitDoorOpen()
        self.hideBuildingShell()
        # Keep strolling in until the server lets the toon go.
        self.finishArrivalStroll()
        strollTo = base.render.getRelativePoint(otherNP, Point3(-self.doorX, -DoorSwapDepth - 3.0, ToontownGlobals.FloorOffset))
        self.arrivalStroll = LerpPosInterval(nodePath=avatar, duration=1.5, pos=strollTo, name='doorArrivalStroll-%d' % self.doId)
        self.arrivalStroll.start()
        self.arrivedEarly = True
        base.transitions.noTransitions()
        FrameHold.release(0.3)

    def hideBuildingShell(self):
        """Coming out onto the street the camera starts inside the
        building, behind the toon, where the insides of its walls fill
        the view.  The building is left undrawn (it still casts its
        shadow) until the camera is back outside."""
        if self.doorType not in (DoorTypes.EXT_STANDARD, DoorTypes.EXT_HQ, DoorTypes.EXT_ANIM_STANDARD):
            return
        self.showBuildingShell()
        building = self.getBuilding()
        if building is None or building.isEmpty():
            return
        building.hide(ViewCameras)
        self.hiddenShell = building

    def showBuildingShell(self, task=None):
        taskMgr.remove(self.uniqueName('showBuildingShell'))
        shell = getattr(self, 'hiddenShell', None)
        self.hiddenShell = None
        if shell is not None and not shell.isEmpty():
            shell.show(ViewCameras)

    def showBuildingShellSoon(self):
        if getattr(self, 'hiddenShell', None) is not None:
            taskMgr.doMethodLater(0.6, self.showBuildingShell, self.uniqueName('showBuildingShell'))

    def poseExitDoorOpen(self):
        """Shows the leaf the local toon comes out through standing open.
        The black panels that stand in for the dark inside of a doorway
        stay hidden: the camera arrives behind this door, looking through
        it at the toon, and they would black out the view."""
        leftDoor = self.findDoorNode('leftDoor', True)
        if leftDoor is None or leftDoor.isEmpty():
            return False
        for name in ('doorFrameHoleLeft', 'doorFrameHoleRight'):
            hole = self.findDoorNode(name, True)
            if hole is not None and not hole.isEmpty():
                hole.hide()
        leftDoor.show()
        leftDoor.setHpr(self.getDoorNodePath(), -100 if self.leftSwing else 100, 0, 0)
        return True

    def finishArrivalStroll(self):
        stroll = getattr(self, 'arrivalStroll', None)
        if stroll is not None:
            stroll.pause()
            self.arrivalStroll = None

    def avatarEnterDoorTrack(self, avatar, duration):
        trackName = 'avatarEnterDoor-%d-%d' % (self.doId, avatar.doId)
        track = Parallel(name=trackName)
        otherNP = self.getDoorNodePath()
        if hasattr(avatar, 'stopSmooth'):
            avatar.stopSmooth()

        if avatar.doId == base.localAvatar.doId:
            track.append(LerpPosHprInterval(nodePath=base.camera, other=avatar, duration=duration, pos=Point3(0, -8, avatar.getHeight()), hpr=VBase3(0, 0, 0), blendType='easeInOut'))

        finalPos = avatar.getParent().getRelativePoint(otherNP, Point3(self.doorX, 2, ToontownGlobals.FloorOffset))
        moveHere = Sequence(self.getAnimStateInterval(avatar, 'walk'), LerpPosInterval(nodePath=avatar, duration=duration, pos=finalPos, blendType='easeIn'))
        track.append(moveHere)
        if avatar.doId == base.localAvatar.doId:
            if QuickDoors:
                # Walk straight through.  The last frame of the toon in
                # the doorway stays up while the places are swapped.
                track.append(Sequence(Wait(duration), Func(FrameHold.hold), Func(avatar.b_setParent, ToontownGlobals.SPHidden)))
            else:
                track.append(Sequence(Wait(duration * 0.5), Func(base.transitions.irisOut, duration * 0.5), Wait(duration * 0.5), Func(avatar.b_setParent, ToontownGlobals.SPHidden)))

        track.delayDelete = DelayDelete(avatar, 'avatarEnterDoorTrack')
        return track

    def avatarEnqueueTrack(self, avatar, duration):
        if hasattr(avatar, 'stopSmooth'):
            avatar.stopSmooth()

        back = -5.0 - 2.0 * len(self.avatarIDList)
        if back < -9.0:
            back = -9.0

        offset = Point3(self.doorX, back, ToontownGlobals.FloorOffset)
        otherNP = self.getDoorNodePath()
        walkLike = ActorInterval(avatar, 'walk', startTime=1, duration=duration, endTime=0.0001)
        standHere = Sequence(LerpPosHprInterval(nodePath=avatar, other=otherNP, duration=duration, pos=offset, hpr=VBase3(0, 0, 0), blendType='easeInOut'), self.getAnimStateInterval(avatar, 'neutral'))
        trackName = 'avatarEnqueueDoor-%d-%d' % (self.doId, avatar.doId)
        track = Parallel(walkLike, standHere, name=trackName)
        track.delayDelete = DelayDelete(avatar, 'avatarEnqueueTrack')
        return track

    def getAnimStateInterval(self, avatar, animName):
        isSuit = isinstance(avatar, Suit)
        if isSuit:
            return Func(avatar.loop, animName, 0)
        else:
            return Func(avatar.setAnimState, animName)

    def isDoorHit(self):
        vec = base.localAvatar.getRelativeVector(self.currentDoorNp, self.currentDoorVec)
        netScale = self.currentDoorNp.getNetTransform().getScale()
        yToTest = vec.getY() / netScale[1]
        return yToTest < -0.5

    def enterDoor(self):
        if self.allowedToEnter():
            messenger.send('DistributedDoor_doorTrigger')
            self.sendUpdate('requestEnter')
        else:
            place = base.cr.playGame.getPlace()
            if place:
                place.fsm.request('stopped')

            self.dialog = TeaserPanel(pageName='otherHoods', doneFunc=self.handleOkTeaser)

    def handleOkTeaser(self):
        self.accept(self.getEnterTriggerEvent(), self.doorTrigger)
        self.dialog.destroy()
        del self.dialog
        place = base.cr.playGame.getPlace()
        if place:
            place.fsm.request('walk')

    def allowedToEnter(self, zoneId = None):
        allowed = False
        if hasattr(base, 'ttAccess') and base.ttAccess:
            if zoneId:
                allowed = base.ttAccess.canAccess(zoneId)
            else:
                allowed = base.ttAccess.canAccess()

        return allowed

    def checkIsDoorHitTaskName(self):
        return 'checkIsDoorHit' + self.getTriggerName()

    def checkIsDoorHitTask(self, task):
        if self.isDoorHit():
            self.ignore(self.checkIsDoorHitTaskName())
            self.ignore(self.getExitTriggerEvent())
            self.enterDoor()
            return task.done

        return task.cont

    def cancelCheckIsDoorHitTask(self, args):
        taskMgr.remove(self.checkIsDoorHitTaskName())
        del self.currentDoorNp
        del self.currentDoorVec
        self.ignore(self.getExitTriggerEvent())
        self.accept(self.getEnterTriggerEvent(), self.doorTrigger)

    def doorTrigger(self, args = None):
        self.ignore(self.getEnterTriggerEvent())
        if args == None:
            self.enterDoor()
        else:
            self.currentDoorNp = NodePath(args.getIntoNodePath())
            self.currentDoorVec = Vec3(args.getSurfaceNormal(self.currentDoorNp))
            if self.isDoorHit():
                self.enterDoor()
            else:
                self.accept(self.getExitTriggerEvent(), self.cancelCheckIsDoorHitTask)
                taskMgr.add(self.checkIsDoorHitTask, self.checkIsDoorHitTaskName())

    def avatarEnter(self, avatarID):
        avatar = self.cr.doId2do.get(avatarID, None)
        if avatar:
            avatar.setAnimState('neutral')
            track = self.avatarEnqueueTrack(avatar, 0.5)
            track.start()
            self.avatarTracks.append(track)
            self.avatarIDList.append(avatarID)

    def rejectEnter(self, reason):
        message = FADoorCodes.reasonDict[reason]
        if message:
            self.__faRejectEnter(message)
        else:
            self.__basicRejectEnter()

    def __basicRejectEnter(self):
        self.accept(self.getEnterTriggerEvent(), self.doorTrigger)
        if self.cr.playGame.getPlace():
            self.cr.playGame.getPlace().setState('walk')

    def __faRejectEnter(self, message):
        self.rejectDialog = TTDialog.TTGlobalDialog(message=message, doneEvent='doorRejectAck', style=TTDialog.Acknowledge)
        self.rejectDialog.show()
        self.rejectDialog.delayDelete = DelayDelete(self, '__faRejectEnter')
        event = 'clientCleanup'
        self.acceptOnce(event, self.__handleClientCleanup)
        base.cr.playGame.getPlace().setState('stopped')
        self.acceptOnce('doorRejectAck', self.__handleRejectAck)
        self.acceptOnce('stoppedAsleep', self.__handleFallAsleepDoor)

    def __handleClientCleanup(self):
        if hasattr(self, 'rejectDialog') and self.rejectDialog:
            self.rejectDialog.doneStatus = 'ok'

        self.__handleRejectAck()

    def __handleFallAsleepDoor(self):
        self.rejectDialog.doneStatus = 'ok'
        self.__handleRejectAck()

    def __handleRejectAck(self):
        self.ignore('doorRejectAck')
        self.ignore('stoppedAsleep')
        self.ignore('clientCleanup')
        doneStatus = self.rejectDialog.doneStatus
        if doneStatus != 'ok':
            self.notify.error('Unrecognized doneStatus: ' + str(doneStatus))

        self.__basicRejectEnter()
        self.rejectDialog.delayDelete.destroy()
        self.rejectDialog.cleanup()
        del self.rejectDialog

    def getDoorNodePath(self):
        if self.doorType == DoorTypes.INT_STANDARD:
            otherNP = base.render.find('**/door_origin')
        elif self.doorType == DoorTypes.EXT_STANDARD:
            if hasattr(self, 'tempDoorNodePath'):
                return self.tempDoorNodePath
            else:
                posHpr = self.cr.playGame.dnaStore.getDoorPosHprFromBlockNumber(self.block)
                otherNP = NodePath('doorOrigin')
                otherNP.setPos(posHpr.getPos())
                otherNP.setHpr(posHpr.getHpr())
                self.tempDoorNodePath = otherNP
        elif self.doorType in self.specialDoorTypes:
            building = self.getBuilding()
            otherNP = building.find('**/door_origin_' + str(self.doorIndex))
        elif self.doorType == DoorTypes.INT_HQ:
            otherNP = base.render.find('**/door_origin_' + str(self.doorIndex))
        else:
            self.notify.error('No such door type as ' + str(self.doorType))

        return otherNP

    def avatarExitTrack(self, avatar, duration):
        if hasattr(avatar, 'stopSmooth'):
            avatar.stopSmooth()

        otherNP = self.getDoorNodePath()
        trackName = 'avatarExitDoor-%d-%d' % (self.doId, avatar.doId)
        track = Sequence(name=trackName)
        track.append(self.getAnimStateInterval(avatar, 'walk'))
        quick = QuickDoors and avatar.doId == base.localAvatar.doId
        if quick and getattr(self, 'arrivedEarly', False):
            # Already through the door and walking (arriveThroughDoor):
            # just carry on to where the toon is let go.
            self.arrivedEarly = False
            finalPos = base.render.getRelativePoint(otherNP, Point3(-self.doorX, -6, ToontownGlobals.FloorOffset))
            track.append(Func(self.finishArrivalStroll))
            track.append(LerpPosInterval(nodePath=avatar, duration=0.4, pos=finalPos, blendType='easeOut'))
            track.append(Func(self.exitCompleted))
            track.append(Func(self.showBuildingShellSoon))
            if hasattr(avatar, 'startSmooth'):
                track.append(Func(avatar.startSmooth))
            track.delayDelete = DelayDelete(avatar, 'DistributedDoor.avatarExitTrack')
            return track
        # The toon went into the other side of this door facing in and
        # DoorSwapDepth through it, with the camera DoorCamBack behind.
        # It comes out of this side in the same place, so the held picture
        # and the live one line up.
        startY = -DoorSwapDepth if quick else 0
        track.append(PosHprInterval(avatar, Point3(-self.doorX, startY, ToontownGlobals.FloorOffset), VBase3(180 if quick else 179, 0, 0), other=otherNP))
        track.append(Func(avatar.setParent, ToontownGlobals.SPRender))
        if avatar.doId == base.localAvatar.doId:
            track.append(PosHprInterval(base.camera, VBase3(-self.doorX, startY + DoorCamBack if quick else 5, avatar.getHeight()), VBase3(180, 0, 0), other=otherNP))

        if avatar.doId == base.localAvatar.doId:
            finalPos = base.render.getRelativePoint(otherNP, Point3(-self.doorX, -6, ToontownGlobals.FloorOffset))
        else:
            finalPos = base.render.getRelativePoint(otherNP, Point3(-self.doorX, -3, ToontownGlobals.FloorOffset))

        if QuickDoors and avatar.doId == base.localAvatar.doId:
            # The new place is up: clear the black screen the place change
            # put behind the held picture, dissolve the picture into it,
            # and keep walking.
            track.append(Func(base.transitions.noTransitions))
            track.append(Func(FrameHold.release, 0.3))
            track.append(LerpPosInterval(nodePath=avatar, duration=min(duration, 0.6), pos=finalPos, blendType='easeOut'))
            track.append(Func(self.exitCompleted))
        else:
            track.append(LerpPosInterval(nodePath=avatar, duration=duration, pos=finalPos, blendType='easeInOut'))
            if avatar.doId == base.localAvatar.doId:
                track.append(Func(self.exitCompleted))
                track.append(Func(base.transitions.irisIn))

        if hasattr(avatar, 'startSmooth'):
            track.append(Func(avatar.startSmooth))

        track.delayDelete = DelayDelete(avatar, 'DistributedDoor.avatarExitTrack')
        return track

    def exitCompleted(self):
        base.localAvatar.setAnimState('neutral')
        place = self.cr.playGame.getPlace()
        if place:
            place.setState('walk')

        base.localAvatar.d_setParent(ToontownGlobals.SPRender)

    def avatarExit(self, avatarID):
        if avatarID in self.avatarIDList:
            self.avatarIDList.remove(avatarID)
            if avatarID == base.localAvatar.doId:
                self.exitCompleted()
        else:
            self.avatarExitIDList.append(avatarID)

    def finishDoorTrack(self):
        if self.doorTrack:
            self.doorTrack.finish()

        self.doorTrack = None

    def finishDoorExitTrack(self):
        if self.doorExitTrack:
            self.doorExitTrack.finish()

        self.doorExitTrack = None

    def finishAllTracks(self):
        self.finishDoorTrack()
        self.finishArrivalStroll()
        self.showBuildingShell()
        self.finishDoorExitTrack()
        for t in self.avatarTracks:
            t.finish()
            cleanupDelayDeletes(t)

        self.avatarTracks = []
        for t in self.avatarExitTracks:
            t.finish()
            cleanupDelayDeletes(t)

        self.avatarExitTracks = []

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def getRequestStatus(self):
        zoneId = self.otherZoneId
        request = {'loader': ZoneUtil.getBranchLoaderName(zoneId),
         'where': ZoneUtil.getToonWhereName(zoneId),
         'how': 'doorIn',
         'hoodId': ZoneUtil.getHoodId(zoneId),
         'zoneId': zoneId,
         'shardId': None,
         'avId': -1,
         'allowRedirect': 0,
         'doorDoId': self.otherDoId}
        return request

    def enterClosing(self, ts):
        doorFrameHoleRight = self.findDoorNode('doorFrameHoleRight')
        if doorFrameHoleRight.isEmpty():
            self.notify.warning('enterClosing(): did not find doorFrameHoleRight')
            return

        rightDoor = self.findDoorNode('rightDoor')
        if rightDoor.isEmpty():
            self.notify.warning('enterClosing(): did not find rightDoor')
            return

        otherNP = self.getDoorNodePath()
        trackName = 'doorClose-%d' % self.doId
        if self.rightSwing:
            h = 100
        else:
            h = -100

        self.finishDoorTrack()
        self.doorTrack = Sequence(LerpHprInterval(nodePath=rightDoor, duration=1.0, hpr=VBase3(0, 0, 0), startHpr=VBase3(h, 0, 0), other=otherNP, blendType='easeInOut'), Func(doorFrameHoleRight.hide), Func(self.hideIfHasFlat, rightDoor), SoundInterval(self.closeSfx, node=rightDoor), name=trackName)
        self.doorTrack.start(ts)
        if hasattr(self, 'done'):
            request = self.getRequestStatus()
            messenger.send('doorDoneEvent', [request])

    def exitClosing(self):
        pass

    def enterClosed(self, ts):
        pass

    def exitClosed(self):
        pass

    def enterOpening(self, ts):
        doorFrameHoleRight = self.findDoorNode('doorFrameHoleRight')
        if doorFrameHoleRight.isEmpty():
            self.notify.warning('enterOpening(): did not find doorFrameHoleRight')
            return

        rightDoor = self.findDoorNode('rightDoor')
        if rightDoor.isEmpty():
            self.notify.warning('enterOpening(): did not find rightDoor')
            return

        otherNP = self.getDoorNodePath()
        trackName = 'doorOpen-%d' % self.doId
        if self.rightSwing:
            h = 100
        else:
            h = -100

        self.finishDoorTrack()
        self.doorTrack = Parallel(SoundInterval(self.openSfx, node=rightDoor), Sequence(HprInterval(rightDoor, VBase3(0, 0, 0), other=otherNP), Wait(0.4), Func(rightDoor.show), Func(doorFrameHoleRight.show), LerpHprInterval(nodePath=rightDoor, duration=0.6, hpr=VBase3(h, 0, 0), startHpr=VBase3(0, 0, 0), other=otherNP, blendType='easeInOut')), name=trackName)
        self.doorTrack.start(ts)

    def exitOpening(self):
        pass

    def enterOpen(self, ts):
        for avatarID in self.avatarIDList:
            avatar = self.cr.doId2do.get(avatarID)
            if avatar:
                track = self.avatarEnterDoorTrack(avatar, 1.0)
                track.start(ts)
                self.avatarTracks.append(track)

            if avatarID == base.localAvatar.doId:
                self.done = 1

        self.avatarIDList = []

    def exitOpen(self):
        for track in self.avatarTracks:
            track.finish()
            cleanupDelayDeletes(track)

        self.avatarTracks = []

    def exitDoorEnterOff(self):
        pass

    def exitDoorExitOff(self):
        pass

    def exitDoorEnterClosing(self, ts):
        doorFrameHoleLeft = self.findDoorNode('doorFrameHoleLeft')
        if doorFrameHoleLeft.isEmpty():
            self.notify.warning('enterOpening(): did not find flatDoors')
            return

        if self.leftSwing:
            h = -100
        else:
            h = 100

        leftDoor = self.findDoorNode('leftDoor')
        if not leftDoor.isEmpty():
            otherNP = self.getDoorNodePath()
            trackName = 'doorExitTrack-%d' % self.doId
            self.finishDoorExitTrack()
            self.doorExitTrack = Sequence(LerpHprInterval(nodePath=leftDoor, duration=1.0, hpr=VBase3(0, 0, 0), startHpr=VBase3(h, 0, 0), other=otherNP, blendType='easeInOut'), Func(doorFrameHoleLeft.hide), Func(self.hideIfHasFlat, leftDoor), SoundInterval(self.closeSfx, node=leftDoor), name=trackName)
            self.doorExitTrack.start(ts)

    def exitDoorExitClosing(self):
        pass

    def exitDoorEnterClosed(self, ts):
        pass

    def exitDoorExitClosed(self):
        pass

    def exitDoorEnterOpening(self, ts):
        doorFrameHoleLeft = self.findDoorNode('doorFrameHoleLeft')
        if doorFrameHoleLeft.isEmpty():
            self.notify.warning('enterOpening(): did not find flatDoors')
            return

        leftDoor = self.findDoorNode('leftDoor')
        if self.leftSwing:
            h = -100
        else:
            h = 100

        if getattr(self, 'arrivedEarly', False) and self.poseExitDoorOpen():
            # The local toon is already walking out of this door, which
            # was shown open for it; don't swing it open again.
            self.finishDoorExitTrack()
            return

        if not leftDoor.isEmpty():
            otherNP = self.getDoorNodePath()
            trackName = 'doorDoorExitTrack-%d' % self.doId
            self.finishDoorExitTrack()
            self.doorExitTrack = Parallel(SoundInterval(self.openSfx, node=leftDoor), Sequence(Func(leftDoor.show), Func(doorFrameHoleLeft.show), LerpHprInterval(nodePath=leftDoor, duration=0.6, hpr=VBase3(h, 0, 0), startHpr=VBase3(0, 0, 0), other=otherNP, blendType='easeInOut')), name=trackName)
            self.doorExitTrack.start(ts)
        else:
            self.notify.warning('exitDoorEnterOpening(): did not find leftDoor')

    def exitDoorExitOpening(self):
        pass

    def exitDoorEnterOpen(self, ts):
        for avatarID in self.avatarExitIDList:
            avatar = self.cr.doId2do.get(avatarID)
            if avatar:
                track = self.avatarExitTrack(avatar, 0.2)
                track.start()
                self.avatarExitTracks.append(track)

        self.avatarExitIDList = []

    def exitDoorExitOpen(self):
        for track in self.avatarExitTracks:
            track.finish()
            cleanupDelayDeletes(track)

        self.avatarExitTracks = []

    def findDoorNode(self, string, allowEmpty = False):
        building = self.getBuilding()
        if not building:
            self.notify.warning('getBuilding() returned None, avoiding crash, remark 896029')
            foundNode = None
        else:
            foundNode = building.find('**/door_' + str(self.doorIndex) + '/**/' + string + '*;+s+i')
            if foundNode.isEmpty():
                foundNode = building.find('**/' + string + '*;+s+i')

        if allowEmpty:
            return foundNode

        return foundNode

    def hideIfHasFlat(self, node):
        if self.bHasFlat:
            node.hide()
