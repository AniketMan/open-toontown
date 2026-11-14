"""Holds the last drawn frame on screen while one place is swapped for
another, then dissolves it into the new place.

Walking through a door replaces the street with a room: the street is torn
down, the server is asked for the room, and the room is built.  The game
used to close an iris over that.  Instead the picture of the toon in the
doorway is kept up for those few frames, the toon and camera arrive in the
room in the same pose they left the street in, and the held picture
dissolves into the live room.

    FrameHold.hold()          keep showing the current frame
    FrameHold.release(0.3)    dissolve into whatever is drawn now
"""

from panda3d.core import CardMaker, NodePath, TransparencyAttrib, Texture
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import Sequence, LerpColorScaleInterval, Func

notify = DirectNotifyGlobal.directNotify.newCategory('FrameHold')

# Never leave a held frame up longer than this, whatever went wrong.
MAX_HOLD = 4.0

_card = None
_fade = None


def isHeld():
    return _card is not None


def hold():
    """Freezes the picture.  Safe to call twice."""
    global _card
    if _card is not None:
        return
    win = base.win
    if win is None:
        return
    tex = win.getScreenshot()
    if tex is None:
        notify.warning('no screenshot; nothing held')
        return
    tex.setMinfilter(Texture.FTLinear)
    tex.setMagfilter(Texture.FTLinear)
    cm = CardMaker('frame-hold')
    cm.setFrameFullscreenQuad()
    card = NodePath(cm.generate())
    card.setTexture(tex)
    card.setTransparency(TransparencyAttrib.MAlpha)
    card.setDepthTest(False)
    card.setDepthWrite(False)
    card.setLightOff(1)
    card.setFogOff(1)
    # Over everything, the black screen of the place change included.
    card.setBin('gui-popup', 10000)
    card.reparentTo(base.render2d)
    _card = card
    taskMgr.remove('frame-hold-timeout')
    taskMgr.doMethodLater(MAX_HOLD, _timeout, 'frame-hold-timeout')


def _timeout(task):
    notify.warning('held frame timed out')
    release(0.3)
    return task.done


def release(duration=0.3):
    """Dissolves the held picture into the live one."""
    global _card, _fade
    taskMgr.remove('frame-hold-timeout')
    if _card is None:
        return
    card = _card
    _card = None
    if _fade is not None:
        _fade.finish()
        _fade = None
    if duration <= 0:
        card.removeNode()
        return

    def done():
        global _fade
        card.removeNode()
        _fade = None

    _fade = Sequence(LerpColorScaleInterval(card, duration, (1, 1, 1, 0), startColorScale=(1, 1, 1, 1),
                                            blendType='easeInOut'),
                     Func(done), name='frame-hold-release')
    _fade.start()
