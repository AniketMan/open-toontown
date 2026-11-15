import sys, os, time, builtins
from panda3d.core import *
loadPrcFile('etc/Configrc.prc')
loadPrcFileData('', 'window-type offscreen\nwin-size 800 500\naudio-library-name null\ntoontown-auto-run 0\ninactivity-timeout 0\nwant-quick-doors %s\nnotify-level-FrameHold info\nnotify-level-OpenInteriors info\n' % os.environ.get('QUICK', '1'))
out = sys.argv[1]
from direct.showbase import ShowBase as SBM
_orig = SBM.ShowBase.openMainWindow
def _open(self, *a, **k):
    r = _orig(self, *a, **k)
    if getattr(self, 'mouseWatcherNode', None) is None:
        mw = MouseWatcher('watcher')
        self._fakeRoot = NodePath('fake'); self.mouseWatcher = self._fakeRoot.attachNewNode(mw)
        self.mouseWatcherNode = mw
        self.buttonThrowers = [self.mouseWatcher.attachNewNode(ButtonThrower('bt'))]
        self.timeButtonThrower = self.mouseWatcher.attachNewNode(ButtonThrower('tbt'))
        self.mouse2cam = self._fakeRoot.attachNewNode(Transform2SG('m2c'))
        self.aspect2d.node().setMouseWatcher(mw)
    return r
SBM.ShowBase.openMainWindow = _open
from direct.task.TaskManagerGlobal import taskMgr
from toontown.toonbase import FrameHold
from toontown.building import DoorTypes
FRAMES = []
import traceback
def spy(name):
    def hook(*a, **k):
        if S['rec']: print('SPY', name, a, ''.join(traceback.format_stack(limit=5)[:-1]).replace(chr(10), ' | ')[:700]); sys.stdout.flush()
        return ORIG[name](*a, **k)
    return hook
ORIG = {}
S = {'step': 'login', 't': 0, 'f': 0, 'rec': None, 'n': 0}
def log(*a):
    print('DRV %.2f' % globalClock.getRealTime(), *a); sys.stdout.flush()
def placeState():
    p = cr.playGame.getPlace() if getattr(cr, 'playGame', None) else None
    try: return p.__class__.__name__, p.fsm.getCurrentState().getName()
    except Exception: return (p.__class__.__name__ if p else None), None
def doors(kind):
    from toontown.building.DistributedDoor import DistributedDoor
    return [d for d in cr.doId2do.values() if isinstance(d, DistributedDoor) and d.doorType in kind]
def drive(task):
    global cr
    if not hasattr(builtins, 'base') or not getattr(base, 'cr', None) or not hasattr(base.cr, 'loginFSM'): return task.cont
    cr = base.cr
    now = globalClock.getRealTime(); S['f'] += 1
    if S['rec']:
        S['n'] += 1
        if now - S.get('last', 0) < 0.045: return_early = True
        else:
            return_early = False; S['last'] = now; S['k'] = S.get('k', 0) + 1
            fn = '%s/%s_%03d.png' % (out, S['rec'], S['k'])
            if False:
                im = PNMImage(); base.win.getScreenshot(im); FRAMES.append((fn, im))
                print('SHOT %s %03d t=%.3f held=%s place=%s' % (S['rec'], S['k'], now, FrameHold.isHeld(), placeState()))
        print('REC %s %03d t=%.3f dt=%.0fms held=%s place=%s' % (S['rec'], S['n'] - 1, now, globalClock.getDt() * 1000, FrameHold.isHeld(), placeState())); sys.stdout.flush()
    step = S['step']
    if step == 'login':
        if cr.loginFSM.getCurrentState().getName() == 'chooseAvatar' and getattr(cr, 'avChoice', None):
            av = [a for a in cr.avList if a.position == 1][0]
            log('choosing', av.name)
            cr.avChoice.exit()
            cr.loginFSM.request('waitForSetAvatarResponse', [av])
            S['step'] = 'spawn'
    elif step == 'spawn':
        if now - S['t'] > 5:
            S['t'] = now; log('waiting', cr.loginFSM.getCurrentState().getName(), cr.gameFSM.getCurrentState().getName(), placeState())
        if hasattr(base, 'localAvatar') and placeState()[1] == 'walk':
            log('in world', placeState(), base.localAvatar.getPos(render)); S['step'] = 'settle'; S['t'] = now
            for nm in ('irisIn', 'irisOut', 'fadeIn', 'fadeOut', 'fadeScreen'):
                ORIG[nm] = getattr(base.transitions, nm); setattr(base.transitions, nm, spy(nm))
    elif step == 'settle' and now - S['t'] > 3 and os.environ.get('HOOD') and not S.get('tp'):
        S['tp'] = 1; hood = int(os.environ['HOOD']); log('teleport', hood)
        cr.playGame.getPlace().requestTeleport(hood, int(os.environ.get('ZONE', hood)), None, -1)
        S['step'] = 'tpwait'; S['t'] = now
    elif step == 'tpwait':
        ps = placeState()
        if now - S['t'] > 4 and ps[1] == 'walk':
            log('arrived', ps); S['step'] = 'settle'; S['t'] = now
        elif now - S['t'] > 40: log('TIMEOUT tp', ps); S['step'] = 'quit'
    elif step == 'settle' and now - S['t'] > 4:
        ds = doors((DoorTypes.EXT_STANDARD, DoorTypes.EXT_HQ, DoorTypes.EXT_KS)); S['home'] = placeState()[0]
        ds = [d for d in ds if d.doorType == int(os.environ.get('DTYPE', d.doorType))]; d = ds[int(os.environ.get('DIDX', 0)) % len(ds)]; S['door'] = d; log('using', d.doorType, getattr(d, 'block', None))
        t = OI.doorTransform(cr.playGame.dnaStore, d.block)
        fr = render.attachNewNode('fr'); fr.setPosHpr(t.getPos(), t.getHpr())
        base.localAvatar.setPosHpr(fr, d.doorX, -9, 0, 0, 0, 0); fr.removeNode()
        S['step'] = 'approach'; S['t'] = now
    elif step == 'approach' and now - S['t'] > 1.5:
        S['rec'] = 'in'; S['n'] = 0; S['k'] = 0
        from direct.showbase.InputStateGlobal import inputState
        S['is'] = inputState
        log('walking forward'); inputState.set('forward', True); S['step'] = 'entering'; S['t'] = now
    elif step == 'entering':
        ps = placeState()
        if now - S.get('lg', 0) > 0.5:
            S['lg'] = now; d = S['door']
            fr = OI.walk['frame'] if OI.walk else None
            try: st = d.fsm.getCurrentState().getName()
            except Exception: st = '?'
            log('  ', ps, 'in door frame', [round(x, 1) for x in base.localAvatar.getPos(fr)] if fr else None, 'walk', OI.walk is not None, 'door', st, 'wt', getattr(d, 'walkThrough', None), 'walls', OI._wallsOn, 'handing', OI.handingOver)
        if ps[0] not in (None, S['home']) and ps[1] == 'walk' and not S.get('inside'):
            S['inside'] = now; log('inside walk after %.2fs' % (now - S['t']))
        if S.get('inside') and now - S['inside'] > 1.2 and not S.get('stopped'):
            S['stopped'] = 1; S['is'].set('forward', False); S['rec'] = None
            base.win.saveScreenshot(Filename(out + '/inside.png'))
        if S.get('inside') and now - S['inside'] > 3.0:
            base.localAvatar.setH(base.localAvatar.getH() + 180)
            S['rec'] = 'out'; S['n'] = 0; S['k'] = 0
            log('walking back out'); S['is'].set('forward', True); S['step'] = 'leaving'; S['t'] = now
        elif now - S['t'] > 9:
            log('TIMEOUT entering', ps); S['step'] = 'quit'
    elif step == 'leaving':
        ps = placeState()
        if now - S.get('lg', 0) > 0.5:
            S['lg'] = now; fr = OI.walk['frame'] if OI.walk else None
            log('  ', ps, 'in door frame', [round(x, 1) for x in base.localAvatar.getPos(fr)] if fr else [round(x, 1) for x in base.localAvatar.getPos(render)], 'walk', OI.walk is not None, 'walls', OI._wallsOn, 'handing', OI.handingOver)
        if ps[0] == S['home'] and ps[1] == 'walk' and not S.get('outside'):
            S['outside'] = now; log('outside walk after %.2fs' % (now - S['t']))
        if S.get('outside') and now - S['outside'] > 1.5 or now - S['t'] > 25:
            S['is'].set('forward', False)
            if not S.get('outside'): log('TIMEOUT leaving', ps)
            S['step'] = 'quit'
    elif step == 'quit':
        log('done')
        for fn, im in FRAMES: im.write(Filename(fn))
        os._exit(0)
    return task.cont
taskMgr.add(drive, 'drv', sort=100)
taskMgr.doMethodLater(140, lambda t: os._exit(3), 'bail')
# appended to the driver: report what OpenInteriors did
from toontown.building import OpenInteriors as OI
_p = OI.place
def place(interior, zoneId, block, dnaStore):
    r = _p(interior, zoneId, block, dnaStore)
    try: e = OI.doorTransform(dnaStore, block)
    except Exception as ex: e = repr(ex)
    print('OI place', zoneId, block, 'ok', r, 'door', interior.find('**/door_origin;+s'), 'street', e, 'room at', interior.getPos(), interior.getHpr()); sys.stdout.flush()
    return r
OI.place = place
_e = OI.enterRoom
def enterRoom(loader):
    _e(loader)
    print('OI enterRoom aligned', OI.isAligned(), 'outside', OI._outside is not None and (len(OI._outside[1]), len(OI._outside[2]))); sys.stdout.flush()
OI.enterRoom = enterRoom
from toontown.launcher.QuickLauncher import QuickLauncher
launcher = QuickLauncher()
