from direct.actor import Actor
from otp.avatar import Avatar
from . import SuitDNA
from toontown.toonbase import ToontownGlobals
from panda3d.core import *
from panda3d.otp import *
from toontown.battle import SuitBattleGlobals
from direct.task.Task import Task
from toontown.battle import BattleProps
from toontown.toonbase import TTLocalizer
aSize = 6.06
bSize = 5.29
cSize = 4.14
SuitDialogArray = []
SkelSuitDialogArray = []
AllSuits = (('walk', 'walk'), ('run', 'walk'), ('neutral', 'neutral'))
AllSuitsMinigame = (('victory', 'victory'),
 ('flail', 'flailing'),
 ('tug-o-war', 'tug-o-war'),
 ('slip-backward', 'slip-backward'),
 ('slip-forward', 'slip-forward'))
AllSuitsTutorialBattle = (('lose', 'lose'), ('pie-small-react', 'pie-small'), ('squirt-small-react', 'squirt-small'))
AllSuitsBattle = (('drop-react', 'anvil-drop'),
 ('flatten', 'drop'),
 ('sidestep-left', 'sidestep-left'),
 ('sidestep-right', 'sidestep-right'),
 ('squirt-large-react', 'squirt-large'),
 ('landing', 'landing'),
 ('reach', 'walknreach'),
 ('rake-react', 'rake'),
 ('hypnotized', 'hypnotize'),
 ('soak', 'soak'))
SuitsCEOBattle = (('sit', 'sit'),
 ('sit-eat-in', 'sit-eat-in'),
 ('sit-eat-loop', 'sit-eat-loop'),
 ('sit-eat-out', 'sit-eat-out'),
 ('sit-angry', 'sit-angry'),
 ('sit-hungry-left', 'leftsit-hungry'),
 ('sit-hungry-right', 'rightsit-hungry'),
 ('sit-lose', 'sit-lose'),
 ('tray-walk', 'tray-walk'),
 ('tray-neutral', 'tray-neutral'),
 ('sit-lose', 'sit-lose'))
f = (('throw-paper', 'throw-paper', 3.5), ('phone', 'phone', 3.5), ('shredder', 'shredder', 3.5))
p = (('pencil-sharpener', 'pencil-sharpener', 5),
 ('pen-squirt', 'pen-squirt', 5),
 ('hold-eraser', 'hold-eraser', 5),
 ('finger-wag', 'finger-wag', 5),
 ('hold-pencil', 'hold-pencil', 5))
ym = (('throw-paper', 'throw-paper', 5),
 ('golf-club-swing', 'golf-club-swing', 5),
 ('magic3', 'magic3', 5),
 ('rubber-stamp', 'rubber-stamp', 5),
 ('smile', 'smile', 5))
mm = (('speak', 'speak', 5),
 ('effort', 'effort', 5),
 ('magic1', 'magic1', 5),
 ('pen-squirt', 'fountain-pen', 5),
 ('finger-wag', 'finger-wag', 5))
ds = (('magic1', 'magic1', 5),
 ('magic2', 'magic2', 5),
 ('throw-paper', 'throw-paper', 5),
 ('magic3', 'magic3', 5))
hh = (('pen-squirt', 'fountain-pen', 7),
 ('glower', 'glower', 5),
 ('throw-paper', 'throw-paper', 5),
 ('magic1', 'magic1', 5),
 ('roll-o-dex', 'roll-o-dex', 5))
cr = (('pickpocket', 'pickpocket', 5), ('throw-paper', 'throw-paper', 3.5), ('glower', 'glower', 5))
tbc = (('cigar-smoke', 'cigar-smoke', 8),
 ('glower', 'glower', 5),
 ('song-and-dance', 'song-and-dance', 8),
 ('golf-club-swing', 'golf-club-swing', 5))
cc = (('speak', 'speak', 5),
 ('glower', 'glower', 5),
 ('phone', 'phone', 3.5),
 ('finger-wag', 'finger-wag', 5))
tm = (('speak', 'speak', 5),
 ('throw-paper', 'throw-paper', 5),
 ('pickpocket', 'pickpocket', 5),
 ('roll-o-dex', 'roll-o-dex', 5),
 ('finger-wag', 'finger-wag', 5))
nd = (('pickpocket', 'pickpocket', 5),
 ('roll-o-dex', 'roll-o-dex', 5),
 ('magic3', 'magic3', 5),
 ('smile', 'smile', 5))
gh = (('speak', 'speak', 5), ('pen-squirt', 'fountain-pen', 5), ('rubber-stamp', 'rubber-stamp', 5))
ms = (('effort', 'effort', 5),
 ('throw-paper', 'throw-paper', 5),
 ('stomp', 'stomp', 5),
 ('quick-jump', 'jump', 6))
tf = (('phone', 'phone', 5),
 ('smile', 'smile', 5),
 ('throw-object', 'throw-object', 5),
 ('glower', 'glower', 5))
m = (('speak', 'speak', 5),
 ('magic2', 'magic2', 5),
 ('magic1', 'magic1', 5),
 ('golf-club-swing', 'golf-club-swing', 5))
mh = (('magic1', 'magic1', 5),
 ('smile', 'smile', 5),
 ('golf-club-swing', 'golf-club-swing', 5),
 ('song-and-dance', 'song-and-dance', 5))
sc = (('throw-paper', 'throw-paper', 3.5), ('watercooler', 'watercooler', 5), ('pickpocket', 'pickpocket', 5))
pp = (('throw-paper', 'throw-paper', 5), ('glower', 'glower', 5), ('finger-wag', 'fingerwag', 5))
tw = (('throw-paper', 'throw-paper', 3.5),
 ('glower', 'glower', 5),
 ('magic2', 'magic2', 5),
 ('finger-wag', 'finger-wag', 5))
bc = (('phone', 'phone', 5), ('hold-pencil', 'hold-pencil', 5))
nc = (('phone', 'phone', 5), ('throw-object', 'throw-object', 5))
mb = (('magic1', 'magic1', 5), ('throw-paper', 'throw-paper', 3.5))
ls = (('throw-paper', 'throw-paper', 5), ('throw-object', 'throw-object', 5), ('hold-pencil', 'hold-pencil', 5))
rb = (('glower', 'glower', 5), ('magic1', 'magic1', 5), ('golf-club-swing', 'golf-club-swing', 5))
bf = (('pickpocket', 'pickpocket', 5),
 ('rubber-stamp', 'rubber-stamp', 5),
 ('shredder', 'shredder', 3.5),
 ('watercooler', 'watercooler', 5))
b = (('effort', 'effort', 5),
 ('throw-paper', 'throw-paper', 5),
 ('throw-object', 'throw-object', 5),
 ('magic1', 'magic1', 5))
dt = (('rubber-stamp', 'rubber-stamp', 5),
 ('throw-paper', 'throw-paper', 5),
 ('speak', 'speak', 5),
 ('finger-wag', 'fingerwag', 5),
 ('throw-paper', 'throw-paper', 5))
ac = (('throw-object', 'throw-object', 5),
 ('roll-o-dex', 'roll-o-dex', 5),
 ('stomp', 'stomp', 5),
 ('phone', 'phone', 5),
 ('throw-paper', 'throw-paper', 5))
bs = (('magic1', 'magic1', 5), ('throw-paper', 'throw-paper', 5), ('finger-wag', 'fingerwag', 5))
sd = (('magic2', 'magic2', 5),
 ('quick-jump', 'jump', 6),
 ('stomp', 'stomp', 5),
 ('magic3', 'magic3', 5),
 ('hold-pencil', 'hold-pencil', 5),
 ('throw-paper', 'throw-paper', 5))
le = (('speak', 'speak', 5),
 ('throw-object', 'throw-object', 5),
 ('glower', 'glower', 5),
 ('throw-paper', 'throw-paper', 5))
bw = (('finger-wag', 'fingerwag', 5),
 ('cigar-smoke', 'cigar-smoke', 8),
 ('gavel', 'gavel', 8),
 ('magic1', 'magic1', 5),
 ('throw-object', 'throw-object', 5),
 ('throw-paper', 'throw-paper', 5))
if not ConfigVariableBool('want-new-cogs', 0).value:
    ModelDict = {'a': ('/models/char/suitA-', 4),
     'b': ('/models/char/suitB-', 4),
     'c': ('/models/char/suitC-', 3.5)}
    TutorialModelDict = {'a': ('/models/char/suitA-', 4),
     'b': ('/models/char/suitB-', 4),
     'c': ('/models/char/suitC-', 3.5)}
else:
    ModelDict = {'a': ('/models/char/tt_a_ene_cga_', 4),
     'b': ('/models/char/tt_a_ene_cgb_', 4),
     'c': ('/models/char/tt_a_ene_cgc_', 3.5)}
    TutorialModelDict = {'a': ('/models/char/tt_a_ene_cga_', 4),
     'b': ('/models/char/tt_a_ene_cgb_', 4),
     'c': ('/models/char/tt_a_ene_cgc_', 3.5)}
HeadModelDict = {'a': ('/models/char/suitA-', 4),
 'b': ('/models/char/suitB-', 4),
 'c': ('/models/char/suitC-', 3.5)}

# Replacement HD models (tools/ENEMY_MODEL_SWAP.md): one file per enemy, body and
# head together, skinned to the original body's skeleton so the existing
# animations drive it.  A slot is used only when its file is on the model path
# (resources-hd/phase_3.5/models/char/<slot>_hd.bam); otherwise the enemy is
# assembled from the shared body and head pieces as before.
HD_SLOTS = {'f': '01_Flunky_Bossbot', 'p': '02_Pencil-Pusher_Bossbot', 'ym': '03_Yesman_Bossbot',
 'mm': '04_Micromanager_Bossbot', 'ds': '05_Downsizer_Bossbot', 'hh': '06_Head-Hunter_Bossbot',
 'cr': '07_Corporate-Raider_Bossbot', 'tbc': '08_The-Big-Cheese_Bossbot',
 'bf': '09_Bottom-Feeder_Lawbot', 'b': '10_Bloodsucker_Lawbot', 'dt': '11_Double-Talker_Lawbot',
 'ac': '12_Ambulance-Chaser_Lawbot', 'bs': '13_Back-Stabber_Lawbot', 'sd': '14_Spin-Doctor_Lawbot',
 'le': '15_Legal-Eagle_Lawbot', 'bw': '16_Big-Wig_Lawbot',
 'sc': '17_Short-Change_Cashbot', 'pp': '18_Penny-Pincher_Cashbot', 'tw': '19_Tightwad_Cashbot',
 'bc': '20_Bean-Counter_Cashbot', 'nc': '21_Number-Cruncher_Cashbot', 'mb': '22_Money-Bags_Cashbot',
 'ls': '23_Loan-Shark_Cashbot', 'rb': '24_Robber-Baron_Cashbot',
 'cc': '25_Cold-Caller_Sellbot', 'tm': '26_Telemarketer_Sellbot', 'nd': '27_Name-Dropper_Sellbot',
 'gh': '28_Glad-Hander_Sellbot', 'ms': '29_Mover-Shaker_Sellbot', 'tf': '30_Two-Face_Sellbot',
 'm': '31_The-Mingler_Sellbot', 'mh': '32_Mr-Hollywood_Sellbot'}
_hdModelPaths = {}
_flatColorTextures = {}


def flatColorTexture(color):
    """A one-pixel texture of this colour."""
    key = (round(color[0], 3), round(color[1], 3), round(color[2], 3))
    if key not in _flatColorTextures:
        image = PNMImage(1, 1)
        image.fill(*key)
        tex = Texture('flat-%s-%s-%s' % key)
        tex.load(image)
        _flatColorTextures[key] = tex
    return _flatColorTextures[key]

# Where the glowing health emblem sits on an HD model's chest joint.
# Last frame of the defeat animation before its pieces fly apart (24 a second;
# the explosion is at 5.4 seconds).
HD_LOSE_LAST_FRAME = 134
HD_EMBLEM_POS_HPR_SCALE = (0.02, 0.05, 0.04, 180.0, 0.0, 0.0, 0.51, 0.51, 0.51)


def hdModelPath(dnaName):
    """Model path of this enemy's HD replacement, or None if there isn't one."""
    if not ConfigVariableBool('want-hd-suits', True).value:
        return None
    if dnaName not in _hdModelPaths:
        path = None
        slot = HD_SLOTS.get(dnaName)
        if slot:
            candidate = 'phase_3.5/models/char/%s_hd' % slot
            if VirtualFileSystem.getGlobalPtr().resolveFilename(Filename(candidate + '.bam'), getModelPath().getValue()):
                path = candidate
        _hdModelPaths[dnaName] = path
    return _hdModelPaths[dnaName]

def loadTutorialSuit():
    loader.loadModel('phase_3.5/models/char/suitC-mod').node()
    loadDialog(1)


def loadSuits(level):
    loadSuitModelsAndAnims(level, flag=1)
    loadDialog(level)


def unloadSuits(level):
    loadSuitModelsAndAnims(level, flag=0)
    unloadDialog(level)


def loadSuitModelsAndAnims(level, flag = 0):
    for key in list(ModelDict.keys()):
        model, phase = ModelDict[key]
        if ConfigVariableBool('want-new-cogs', 0).value:
            headModel, headPhase = HeadModelDict[key]
        else:
            headModel, headPhase = ModelDict[key]
        if flag:
            if ConfigVariableBool('want-new-cogs', 0).value:
                filepath = 'phase_3.5' + model + 'zero'
                if cogExists(model + 'zero.bam'):
                    loader.loadModel(filepath).node()
            else:
                loader.loadModel('phase_3.5' + model + 'mod').node()
            loader.loadModel('phase_' + str(headPhase) + headModel + 'heads').node()
        else:
            if ConfigVariableBool('want-new-cogs', 0).value:
                filepath = 'phase_3.5' + model + 'zero'
                if cogExists(model + 'zero.bam'):
                    loader.unloadModel(filepath)
            else:
                loader.unloadModel('phase_3.5' + model + 'mod')
            loader.unloadModel('phase_' + str(headPhase) + headModel + 'heads')


def cogExists(filePrefix):
    searchPath = DSearchPath()
    if __debug__:
        searchPath.appendDirectory(Filename('resources/phase_3.5'))
    filePrefix = filePrefix.strip('/')
    pfile = Filename(filePrefix)
    found = vfs.resolveFilename(pfile, searchPath)
    if not found:
        return False
    return True


def loadSuitAnims(suit, flag = 1):
    if suit in SuitDNA.suitHeadTypes:
        try:
            animList = eval(suit)
        except NameError:
            animList = ()

    else:
        print('Invalid suit name: ', suit)
        return -1
    for anim in animList:
        phase = 'phase_' + str(anim[2])
        filePrefix = ModelDict[bodyType][0]
        animName = filePrefix + anim[1]
        if flag:
            loader.loadModel(animName).node()
        else:
            loader.unloadModel(animName)


def loadDialog(level):
    global SuitDialogArray
    if len(SuitDialogArray) > 0:
        return
    else:
        loadPath = 'phase_3.5/audio/dial/'
        SuitDialogFiles = ['COG_VO_grunt',
         'COG_VO_murmur',
         'COG_VO_statement',
         'COG_VO_question']
        for file in SuitDialogFiles:
            SuitDialogArray.append(base.loader.loadSfx(loadPath + file + '.ogg'))

        SuitDialogArray.append(SuitDialogArray[2])
        SuitDialogArray.append(SuitDialogArray[2])


def loadSkelDialog():
    global SkelSuitDialogArray
    if len(SkelSuitDialogArray) > 0:
        return
    else:
        grunt = loader.loadSfx('phase_5/audio/sfx/Skel_COG_VO_grunt.ogg')
        murmur = loader.loadSfx('phase_5/audio/sfx/Skel_COG_VO_murmur.ogg')
        statement = loader.loadSfx('phase_5/audio/sfx/Skel_COG_VO_statement.ogg')
        question = loader.loadSfx('phase_5/audio/sfx/Skel_COG_VO_question.ogg')
        SkelSuitDialogArray = [grunt,
         murmur,
         statement,
         question,
         statement,
         statement]


def unloadDialog(level):
    global SuitDialogArray
    SuitDialogArray = []


def unloadSkelDialog():
    global SkelSuitDialogArray
    SkelSuitDialogArray = []


def attachSuitHead(node, suitName):
    suitIndex = SuitDNA.suitHeadTypes.index(suitName)
    suitDNA = SuitDNA.SuitDNA()
    suitDNA.newSuit(suitName)
    suit = Suit()
    suit.setDNA(suitDNA)
    headParts = suit.getHeadParts()
    head = node.attachNewNode('head')
    for part in headParts:
        copyPart = part.copyTo(head)
        copyPart.setDepthTest(1)
        copyPart.setDepthWrite(1)

    suit.delete()
    suit = None
    p1 = Point3()
    p2 = Point3()
    head.calcTightBounds(p1, p2)
    d = p2 - p1
    biggest = max(d[0], d[2])
    column = suitIndex % SuitDNA.suitsPerDept
    s = (0.2 + column / 100.0) / biggest
    pos = -0.14 + (SuitDNA.suitsPerDept - column - 1) / 135.0
    head.setPosHprScale(0, 0, pos, 180, 0, 0, s, s, s)
    return head


class Suit(Avatar.Avatar):
    healthColors = (Vec4(0, 1, 0, 1),
     Vec4(1, 1, 0, 1),
     Vec4(1, 0.5, 0, 1),
     Vec4(1, 0, 0, 1),
     Vec4(0.3, 0.3, 0.3, 1))
    healthGlowColors = (Vec4(0.25, 1, 0.25, 0.5),
     Vec4(1, 1, 0.25, 0.5),
     Vec4(1, 0.5, 0.25, 0.5),
     Vec4(1, 0.25, 0.25, 0.5),
     Vec4(0.3, 0.3, 0.3, 0))
    medallionColors = {'c': Vec4(0.863, 0.776, 0.769, 1.0),
     's': Vec4(0.843, 0.745, 0.745, 1.0),
     'l': Vec4(0.749, 0.776, 0.824, 1.0),
     'm': Vec4(0.749, 0.769, 0.749, 1.0)}

    def __init__(self):
        try:
            self.Suit_initialized
            return
        except:
            self.Suit_initialized = 1

        Avatar.Avatar.__init__(self)
        self.setFont(ToontownGlobals.getSuitFont())
        self.setPlayerType(NametagGroup.CCSuit)
        self.setPickable(1)
        self.leftHand = None
        self.rightHand = None
        self.shadowJoint = None
        self.nametagJoint = None
        self.headParts = []
        self.healthBar = None
        self.healthCondition = 0
        self.isDisguised = 0
        self.isWaiter = 0
        self.isRental = 0
        self.hdModel = False
        return

    def delete(self):
        try:
            self.Suit_deleted
        except:
            self.Suit_deleted = 1
            if self.leftHand:
                self.leftHand.removeNode()
                self.leftHand = None
            if self.rightHand:
                self.rightHand.removeNode()
                self.rightHand = None
            if self.shadowJoint:
                self.shadowJoint.removeNode()
                self.shadowJoint = None
            if self.nametagJoint:
                self.nametagJoint.removeNode()
                self.nametagJoint = None
            for part in self.headParts:
                part.removeNode()

            self.headParts = []
            self.removeHealthBar()
            Avatar.Avatar.delete(self)

        return

    def setHeight(self, height):
        Avatar.Avatar.setHeight(self, height)
        self.nametag3d.setPos(0, 0, height + 1.0)

    def getRadius(self):
        return 2

    def setDNAString(self, dnaString):
        self.dna = SuitDNA.SuitDNA()
        self.dna.makeFromNetString(dnaString)
        self.setDNA(self.dna)

    def setDNA(self, dna):
        if self.style:
            pass
        else:
            self.style = dna
            self.generateSuit()
            self.initializeDropShadow()
            self.initializeNametag3d()

    def generateSuit(self):
        dna = self.style
        self.headParts = []
        self.headColor = None
        self.headTexture = None
        self.loseActor = None
        self.isSkeleton = 0
        self.hdModel = False
        if dna.name == 'f':
            self.scale = 4.0 / cSize
            self.handColor = SuitDNA.corpPolyColor
            self.generateBody()
            self.generateHead('flunky')
            self.generateHead('glasses')
            self.setHeight(4.88)
        elif dna.name == 'p':
            self.scale = 3.35 / bSize
            self.handColor = SuitDNA.corpPolyColor
            self.generateBody()
            self.generateHead('pencilpusher')
            self.setHeight(5.0)
        elif dna.name == 'ym':
            self.scale = 4.125 / aSize
            self.handColor = SuitDNA.corpPolyColor
            self.generateBody()
            self.generateHead('yesman')
            self.setHeight(5.28)
        elif dna.name == 'mm':
            self.scale = 2.5 / cSize
            self.handColor = SuitDNA.corpPolyColor
            self.generateBody()
            self.generateHead('micromanager')
            self.setHeight(3.25)
        elif dna.name == 'ds':
            self.scale = 4.5 / bSize
            self.handColor = SuitDNA.corpPolyColor
            self.generateBody()
            self.generateHead('beancounter')
            self.setHeight(6.08)
        elif dna.name == 'hh':
            self.scale = 6.5 / aSize
            self.handColor = SuitDNA.corpPolyColor
            self.generateBody()
            self.generateHead('headhunter')
            self.setHeight(7.45)
        elif dna.name == 'cr':
            self.scale = 6.75 / cSize
            self.handColor = VBase4(0.85, 0.55, 0.55, 1.0)
            self.generateBody()
            self.headTexture = 'corporate-raider.jpg'
            self.generateHead('flunky')
            self.setHeight(8.23)
        elif dna.name == 'tbc':
            self.scale = 7.0 / aSize
            self.handColor = VBase4(0.75, 0.95, 0.75, 1.0)
            self.generateBody()
            self.generateHead('bigcheese')
            self.setHeight(9.34)
        elif dna.name == 'bf':
            self.scale = 4.0 / cSize
            self.handColor = SuitDNA.legalPolyColor
            self.generateBody()
            self.headTexture = 'bottom-feeder.jpg'
            self.generateHead('tightwad')
            self.setHeight(4.81)
        elif dna.name == 'b':
            self.scale = 4.375 / bSize
            self.handColor = VBase4(0.95, 0.95, 1.0, 1.0)
            self.generateBody()
            self.headTexture = 'blood-sucker.jpg'
            self.generateHead('movershaker')
            self.setHeight(6.17)
        elif dna.name == 'dt':
            self.scale = 4.25 / aSize
            self.handColor = SuitDNA.legalPolyColor
            self.generateBody()
            self.headTexture = 'double-talker.jpg'
            self.generateHead('twoface')
            self.setHeight(5.63)
        elif dna.name == 'ac':
            self.scale = 4.35 / bSize
            self.handColor = SuitDNA.legalPolyColor
            self.generateBody()
            self.generateHead('ambulancechaser')
            self.setHeight(6.39)
        elif dna.name == 'bs':
            self.scale = 4.5 / aSize
            self.handColor = SuitDNA.legalPolyColor
            self.generateBody()
            self.generateHead('backstabber')
            self.setHeight(6.71)
        elif dna.name == 'sd':
            self.scale = 5.65 / bSize
            self.handColor = VBase4(0.5, 0.8, 0.75, 1.0)
            self.generateBody()
            self.headTexture = 'spin-doctor.jpg'
            self.generateHead('telemarketer')
            self.setHeight(7.9)
        elif dna.name == 'le':
            self.scale = 7.125 / aSize
            self.handColor = VBase4(0.25, 0.25, 0.5, 1.0)
            self.generateBody()
            self.generateHead('legaleagle')
            self.setHeight(8.27)
        elif dna.name == 'bw':
            self.scale = 7.0 / aSize
            self.handColor = SuitDNA.legalPolyColor
            self.generateBody()
            self.generateHead('bigwig')
            self.setHeight(8.69)
        elif dna.name == 'sc':
            self.scale = 3.6 / cSize
            self.handColor = SuitDNA.moneyPolyColor
            self.generateBody()
            self.generateHead('coldcaller')
            self.setHeight(4.77)
        elif dna.name == 'pp':
            self.scale = 3.55 / aSize
            self.handColor = VBase4(1.0, 0.5, 0.6, 1.0)
            self.generateBody()
            self.generateHead('pennypincher')
            self.setHeight(5.26)
        elif dna.name == 'tw':
            self.scale = 4.5 / cSize
            self.handColor = SuitDNA.moneyPolyColor
            self.generateBody()
            self.generateHead('tightwad')
            self.setHeight(5.41)
        elif dna.name == 'bc':
            self.scale = 4.4 / bSize
            self.handColor = SuitDNA.moneyPolyColor
            self.generateBody()
            self.generateHead('beancounter')
            self.setHeight(5.95)
        elif dna.name == 'nc':
            self.scale = 5.25 / aSize
            self.handColor = SuitDNA.moneyPolyColor
            self.generateBody()
            self.generateHead('numbercruncher')
            self.setHeight(7.22)
        elif dna.name == 'mb':
            self.scale = 5.3 / cSize
            self.handColor = SuitDNA.moneyPolyColor
            self.generateBody()
            self.generateHead('moneybags')
            self.setHeight(6.97)
        elif dna.name == 'ls':
            self.scale = 6.5 / bSize
            self.handColor = VBase4(0.5, 0.85, 0.75, 1.0)
            self.generateBody()
            self.generateHead('loanshark')
            self.setHeight(8.58)
        elif dna.name == 'rb':
            self.scale = 7.0 / aSize
            self.handColor = SuitDNA.moneyPolyColor
            self.generateBody()
            self.headTexture = 'robber-baron.jpg'
            self.generateHead('yesman')
            self.setHeight(8.95)
        elif dna.name == 'cc':
            self.scale = 3.5 / cSize
            self.handColor = VBase4(0.55, 0.65, 1.0, 1.0)
            self.headColor = VBase4(0.25, 0.35, 1.0, 1.0)
            self.generateBody()
            self.generateHead('coldcaller')
            self.setHeight(4.63)
        elif dna.name == 'tm':
            self.scale = 3.75 / bSize
            self.handColor = SuitDNA.salesPolyColor
            self.generateBody()
            self.generateHead('telemarketer')
            self.setHeight(5.24)
        elif dna.name == 'nd':
            self.scale = 4.35 / aSize
            self.handColor = SuitDNA.salesPolyColor
            self.generateBody()
            self.headTexture = 'name-dropper.jpg'
            self.generateHead('numbercruncher')
            self.setHeight(5.98)
        elif dna.name == 'gh':
            self.scale = 4.75 / cSize
            self.handColor = SuitDNA.salesPolyColor
            self.generateBody()
            self.generateHead('gladhander')
            self.setHeight(6.4)
        elif dna.name == 'ms':
            self.scale = 4.75 / bSize
            self.handColor = SuitDNA.salesPolyColor
            self.generateBody()
            self.generateHead('movershaker')
            self.setHeight(6.7)
        elif dna.name == 'tf':
            self.scale = 5.25 / aSize
            self.handColor = SuitDNA.salesPolyColor
            self.generateBody()
            self.generateHead('twoface')
            self.setHeight(6.95)
        elif dna.name == 'm':
            self.scale = 5.75 / aSize
            self.handColor = SuitDNA.salesPolyColor
            self.generateBody()
            self.headTexture = 'mingler.jpg'
            self.generateHead('twoface')
            self.setHeight(7.61)
        elif dna.name == 'mh':
            self.scale = 7.0 / aSize
            self.handColor = SuitDNA.salesPolyColor
            self.generateBody()
            self.generateHead('yesman')
            self.setHeight(8.95)
        self.setName(SuitBattleGlobals.SuitAttributes[dna.name]['name'])
        self.getGeomNode().setScale(self.scale)
        self.generateHealthBar()
        self.generateCorporateMedallion()
        return

    def generateBody(self):
        animDict = self.generateAnimDict()
        filePrefix, bodyPhase = ModelDict[self.style.body]
        hdPath = hdModelPath(self.style.name)
        if hdPath:
            # body and head in one model, on the same skeleton: the animations below bind to it unchanged
            self.loadModel(hdPath)
            self.hdModel = True
        elif ConfigVariableBool('want-new-cogs', 0).value:
            if cogExists(filePrefix + 'zero.bam'):
                self.loadModel('phase_3.5' + filePrefix + 'zero')
            else:
                self.loadModel('phase_3.5' + filePrefix + 'mod')
        else:
            self.loadModel('phase_3.5' + filePrefix + 'mod')
        self.loadAnims(animDict)
        self.setSuitClothes()

    def generateAnimDict(self):
        animDict = {}
        filePrefix, bodyPhase = ModelDict[self.style.body]
        for anim in AllSuits:
            animDict[anim[0]] = 'phase_' + str(bodyPhase) + filePrefix + anim[1]

        for anim in AllSuitsMinigame:
            animDict[anim[0]] = 'phase_4' + filePrefix + anim[1]

        for anim in AllSuitsTutorialBattle:
            filePrefix, bodyPhase = TutorialModelDict[self.style.body]
            animDict[anim[0]] = 'phase_' + str(bodyPhase) + filePrefix + anim[1]

        for anim in AllSuitsBattle:
            animDict[anim[0]] = 'phase_5' + filePrefix + anim[1]

        if not ConfigVariableBool('want-new-cogs', 0).value:
            if self.style.body == 'a':
                animDict['neutral'] = 'phase_4/models/char/suitA-neutral'
                for anim in SuitsCEOBattle:
                    animDict[anim[0]] = 'phase_12/models/char/suitA-' + anim[1]

            elif self.style.body == 'b':
                animDict['neutral'] = 'phase_4/models/char/suitB-neutral'
                for anim in SuitsCEOBattle:
                    animDict[anim[0]] = 'phase_12/models/char/suitB-' + anim[1]

            elif self.style.body == 'c':
                animDict['neutral'] = 'phase_3.5/models/char/suitC-neutral'
                for anim in SuitsCEOBattle:
                    animDict[anim[0]] = 'phase_12/models/char/suitC-' + anim[1]

        try:
            animList = eval(self.style.name)
        except NameError:
            animList = ()

        for anim in animList:
            phase = 'phase_' + str(anim[2])
            animDict[anim[0]] = phase + filePrefix + anim[1]

        return animDict

    def initializeBodyCollisions(self, collIdStr):
        Avatar.Avatar.initializeBodyCollisions(self, collIdStr)
        if not self.ghostMode:
            self.collNode.setCollideMask(self.collNode.getIntoCollideMask() | ToontownGlobals.PieBitmask)

    def setSuitClothes(self, modelRoot = None):
        if not modelRoot:
            modelRoot = self
        dept = self.style.dept
        phase = 3.5
        if self.hdModel and modelRoot is self:
            # an HD model carries its own textures; it only needs the joints looked up
            self.leftHand = self.find('**/joint_Lhold')
            self.rightHand = self.find('**/joint_Rhold')
            self.shadowJoint = self.find('**/joint_shadow')
            self.nametagJoint = self.find('**/joint_nameTag')
            return

        def __doItTheOldWay__():
            torsoTex = loader.loadTexture('phase_%s/maps/%s_blazer.jpg' % (phase, dept))
            torsoTex.setMinfilter(Texture.FTLinearMipmapLinear)
            torsoTex.setMagfilter(Texture.FTLinear)
            legTex = loader.loadTexture('phase_%s/maps/%s_leg.jpg' % (phase, dept))
            legTex.setMinfilter(Texture.FTLinearMipmapLinear)
            legTex.setMagfilter(Texture.FTLinear)
            armTex = loader.loadTexture('phase_%s/maps/%s_sleeve.jpg' % (phase, dept))
            armTex.setMinfilter(Texture.FTLinearMipmapLinear)
            armTex.setMagfilter(Texture.FTLinear)
            modelRoot.find('**/torso').setTexture(torsoTex, 1)
            modelRoot.find('**/arms').setTexture(armTex, 1)
            modelRoot.find('**/legs').setTexture(legTex, 1)
            modelRoot.find('**/hands').setColor(self.handColor)
            self.leftHand = self.find('**/joint_Lhold')
            self.rightHand = self.find('**/joint_Rhold')
            self.shadowJoint = self.find('**/joint_shadow')
            self.nametagJoint = self.find('**/joint_nameTag')

        if ConfigVariableBool('want-new-cogs', 0).value:
            if dept == 'c':
                texType = 'bossbot'
            elif dept == 'm':
                texType = 'cashbot'
            elif dept == 'l':
                texType = 'lawbot'
            elif dept == 's':
                texType = 'sellbot'
            if self.find('**/body').isEmpty():
                __doItTheOldWay__()
            else:
                filepath = 'phase_3.5/maps/tt_t_ene_' + texType + '.jpg'
                if cogExists('/maps/tt_t_ene_' + texType + '.jpg'):
                    bodyTex = loader.loadTexture(filepath)
                    self.find('**/body').setTexture(bodyTex, 1)
                self.leftHand = self.find('**/def_joint_left_hold')
                self.rightHand = self.find('**/def_joint_right_hold')
                self.shadowJoint = self.find('**/def_shadow')
                self.nametagJoint = self.find('**/def_nameTag')
        else:
            __doItTheOldWay__()

    def makeWaiter(self, modelRoot = None):
        if not modelRoot:
            modelRoot = self
        self.isWaiter = 1
        if self.hdModel and modelRoot is self:
            return  # the HD model has no separate torso/arms/legs to re-dress
        torsoTex = loader.loadTexture('phase_3.5/maps/waiter_m_blazer.jpg')
        torsoTex.setMinfilter(Texture.FTLinearMipmapLinear)
        torsoTex.setMagfilter(Texture.FTLinear)
        legTex = loader.loadTexture('phase_3.5/maps/waiter_m_leg.jpg')
        legTex.setMinfilter(Texture.FTLinearMipmapLinear)
        legTex.setMagfilter(Texture.FTLinear)
        armTex = loader.loadTexture('phase_3.5/maps/waiter_m_sleeve.jpg')
        armTex.setMinfilter(Texture.FTLinearMipmapLinear)
        armTex.setMagfilter(Texture.FTLinear)
        modelRoot.find('**/torso').setTexture(torsoTex, 1)
        modelRoot.find('**/arms').setTexture(armTex, 1)
        modelRoot.find('**/legs').setTexture(legTex, 1)

    def makeRentalSuit(self, suitType, modelRoot = None):
        if not modelRoot:
            modelRoot = self.getGeomNode()
        if suitType == 's':
            torsoTex = loader.loadTexture('phase_3.5/maps/tt_t_ene_sellbotRental_blazer.jpg')
            legTex = loader.loadTexture('phase_3.5/maps/tt_t_ene_sellbotRental_leg.jpg')
            armTex = loader.loadTexture('phase_3.5/maps/tt_t_ene_sellbotRental_sleeve.jpg')
            handTex = loader.loadTexture('phase_3.5/maps/tt_t_ene_sellbotRental_hand.jpg')
        else:
            self.notify.warning('No rental suit for cog type %s' % suitType)
            return
        self.isRental = 1
        modelRoot.find('**/torso').setTexture(torsoTex, 1)
        modelRoot.find('**/arms').setTexture(armTex, 1)
        modelRoot.find('**/legs').setTexture(legTex, 1)
        modelRoot.find('**/hands').setTexture(handTex, 1)

    def generateHead(self, headType):
        if self.hdModel:
            # The head is part of the HD model.  Battle effects (the stun
            # stars of a pie hit, for one) still attach themselves to the
            # first head part, so give them an empty node on the head joint.
            joint = self.find('**/joint_head')
            anchor = (joint if not joint.isEmpty() else self).attachNewNode('hd-head-anchor')
            self.headParts.append(anchor)
            return
        if ConfigVariableBool('want-new-cogs', 0).value:
            filePrefix, phase = HeadModelDict[self.style.body]
        else:
            filePrefix, phase = ModelDict[self.style.body]
        headModel = loader.loadModel('phase_' + str(phase) + filePrefix + 'heads')
        headReferences = headModel.findAllMatches('**/' + headType)
        for i in range(0, headReferences.getNumPaths()):
            if ConfigVariableBool('want-new-cogs', 0).value:
                headPart = self.instance(headReferences.getPath(i), 'modelRoot', 'to_head')
                if not headPart:
                    headPart = self.instance(headReferences.getPath(i), 'modelRoot', 'joint_head')
            else:
                headPart = self.instance(headReferences.getPath(i), 'modelRoot', 'joint_head')
            if self.headTexture:
                headTex = loader.loadTexture('phase_' + str(phase) + '/maps/' + self.headTexture)
                headTex.setMinfilter(Texture.FTLinearMipmapLinear)
                headTex.setMagfilter(Texture.FTLinear)
                headPart.setTexture(headTex, 1)
            if self.headColor:
                headPart.setColor(self.headColor)
            self.headParts.append(headPart)

        headModel.removeNode()

    def generateCorporateTie(self, modelPath = None):
        if not modelPath:
            modelPath = self
        dept = self.style.dept
        tie = modelPath.find('**/tie')
        if tie.isEmpty():
            self.notify.warning('skelecog has no tie model!!!')
            return
        if dept == 'c':
            tieTex = loader.loadTexture('phase_5/maps/cog_robot_tie_boss.jpg')
        elif dept == 's':
            tieTex = loader.loadTexture('phase_5/maps/cog_robot_tie_sales.jpg')
        elif dept == 'l':
            tieTex = loader.loadTexture('phase_5/maps/cog_robot_tie_legal.jpg')
        elif dept == 'm':
            tieTex = loader.loadTexture('phase_5/maps/cog_robot_tie_money.jpg')
        tieTex.setMinfilter(Texture.FTLinearMipmapLinear)
        tieTex.setMagfilter(Texture.FTLinear)
        tie.setTexture(tieTex, 1)

    def generateCorporateMedallion(self):
        icons = loader.loadModel('phase_3/models/gui/cog_icons')
        dept = self.style.dept
        if ConfigVariableBool('want-new-cogs', 0).value:
            chestNull = self.find('**/def_joint_attachMeter')
            if chestNull.isEmpty():
                chestNull = self.find('**/joint_attachMeter')
        else:
            chestNull = self.find('**/joint_attachMeter')
        if dept == 'c':
            self.corpMedallion = icons.find('**/CorpIcon').copyTo(chestNull)
        elif dept == 's':
            self.corpMedallion = icons.find('**/SalesIcon').copyTo(chestNull)
        elif dept == 'l':
            self.corpMedallion = icons.find('**/LegalIcon').copyTo(chestNull)
        elif dept == 'm':
            self.corpMedallion = icons.find('**/MoneyIcon').copyTo(chestNull)
        self.corpMedallion.setPosHprScale(0.02, 0.05, 0.04, 180.0, 0.0, 0.0, 0.51, 0.51, 0.51)
        self.corpMedallion.setColor(self.medallionColors[dept])
        if self.hdModel:
            # the HD model wears its own medallion; keep the icon node (the avatar panel copies it) but out of the scene
            self.corpMedallion.stash()
        icons.removeNode()

    def generateHealthBar(self):
        self.removeHealthBar()
        self.hdEmblem = None
        if self.hdModel:
            # The health light of an HD model is its own department emblem,
            # lit up in the colour of its health while it is in a battle
            # (setHealthLight).  The node made here only carries the halo.
            emblem = self.find('**/hd_emblem')
            if not emblem.isEmpty():
                self.hdEmblem = emblem
                button = hidden.attachNewNode('hd-health-light')
            else:
                # An HD model without an emblem of its own gets the flat icon.
                icons = loader.loadModel('phase_3/models/gui/cog_icons')
                name = {'c': 'CorpIcon', 's': 'SalesIcon', 'l': 'LegalIcon', 'm': 'MoneyIcon'}[self.style.dept]
                button = icons.find('**/' + name).copyTo(hidden)
                icons.removeNode()
            # HD models mark where the light sits, on the face of their
            # medallion (hd_meter); older exports only have the chest joint.
            self.hdMeterSeat = self.find('**/hd_meter')
            if self.hdMeterSeat.isEmpty():
                button.setPosHprScale(*HD_EMBLEM_POS_HPR_SCALE)
        else:
            model = loader.loadModel('phase_3.5/models/gui/matching_game_gui')
            button = model.find('**/minnieCircle')
            button.setScale(3.0)
            button.setH(180.0)
        button.setColor(self.healthColors[0])
        # Its own light: not dimmed by shade or shadow (see PostFX).
        button.setTag('postfx-glow', '1')
        if ConfigVariableBool('want-new-cogs', 0).value:
            chestNull = self.find('**/def_joint_attachMeter')
            if chestNull.isEmpty():
                chestNull = self.find('**/joint_attachMeter')
        else:
            chestNull = self.find('**/joint_attachMeter')
        seat = getattr(self, 'hdMeterSeat', None) if self.hdModel else None
        seated = seat is not None and not seat.isEmpty()
        button.reparentTo(seat if seated else chestNull)
        self.healthBar = button
        glow = BattleProps.globalPropPool.getProp('glow')
        glow.reparentTo(self.healthBar)
        if self.hdModel:
            glow.setScale(0.55 if seated else 0.28 / HD_EMBLEM_POS_HPR_SCALE[-1])
            glow.setPos(0, 0.02, 0)
        else:
            glow.setScale(0.28)
            glow.setPos(-0.005, 0.01, 0.015)
        glow.setColor(self.healthGlowColors[0])
        if not self.hdModel:
            button.flattenLight()
        self.healthBarGlow = glow
        self.healthBar.hide()
        self.healthCondition = 0

    def reseatHealthBarForSkele(self):
        self.healthBar.setPos(0.0, 0.1, 0.0)

    def updateHealthBar(self, hp, forceUpdate = 0):
        if hp > self.currHP:
            hp = self.currHP
        self.currHP -= hp
        health = float(self.currHP) / float(self.maxHP)
        if health > 0.95:
            condition = 0
        elif health > 0.7:
            condition = 1
        elif health > 0.3:
            condition = 2
        elif health > 0.05:
            condition = 3
        elif health > 0.0:
            condition = 4
        else:
            condition = 5
        if self.healthCondition != condition or forceUpdate:
            if condition == 4:
                blinkTask = Task.loop(Task(self.__blinkRed), Task.pause(0.75), Task(self.__blinkGray), Task.pause(0.1))
                taskMgr.add(blinkTask, self.uniqueName('blink-task'))
            elif condition == 5:
                if self.healthCondition == 4:
                    taskMgr.remove(self.uniqueName('blink-task'))
                blinkTask = Task.loop(Task(self.__blinkRed), Task.pause(0.25), Task(self.__blinkGray), Task.pause(0.1))
                taskMgr.add(blinkTask, self.uniqueName('blink-task'))
            else:
                self.setHealthColor(self.healthColors[condition], self.healthGlowColors[condition])
            self.healthCondition = condition

    def setHealthColor(self, color, glowColor):
        self.healthColor = color
        self.healthBar.setColor(color, 1)
        self.healthBarGlow.setColor(glowColor, 1)
        if getattr(self, 'hdEmblem', None) is not None and getattr(self, 'healthLightOn', False):
            self.hdEmblem.setTexture(flatColorTexture(color), 1)

    def setHealthLight(self, on):
        """Lights an HD model's emblem in its health colour, or returns it
        to plain metal.  A lit emblem is its own light: it is not dimmed
        by shade or shadow (see the glow flag in PostFX)."""
        self.healthLightOn = on
        emblem = getattr(self, 'hdEmblem', None)
        if emblem is None or emblem.isEmpty():
            return
        if on:
            # Coloured with a one-pixel texture, not a flat colour: a flat
            # colour makes Panda rebuild the emblem's vertices without their
            # skinning, and it is left hanging in the rest pose in front of
            # the medallion while the body moves.
            if not hasattr(self, 'hdEmblemState'):
                self.hdEmblemState = emblem.getState()
            emblem.setTexture(flatColorTexture(getattr(self, 'healthColor', self.healthColors[0])), 1)
            emblem.setShaderInput('geomFlags', Vec4(0, 1, 0, 0), 100)
        elif hasattr(self, 'hdEmblemState'):
            emblem.setState(self.hdEmblemState)

    def __blinkRed(self, task):
        self.setHealthColor(self.healthColors[3], self.healthGlowColors[3])
        if self.healthCondition == 5:
            self.healthBar.setScale(1.17)
        return Task.done

    def __blinkGray(self, task):
        if not self.healthBar:
            return
        self.setHealthColor(self.healthColors[4], self.healthGlowColors[4])
        if self.healthCondition == 5:
            self.healthBar.setScale(1.0)
        return Task.done

    def removeHealthBar(self):
        if self.healthBar:
            self.healthBar.removeNode()
            self.healthBar = None
        if getattr(self, 'hdEmblem', None) is not None:
            self.setHealthLight(False)
        if self.healthCondition == 4 or self.healthCondition == 5:
            taskMgr.remove(self.uniqueName('blink-task'))
        self.healthCondition = 0
        return

    def getLoseActor(self):
        if ConfigVariableBool('want-new-cogs', 0).value:
            if self.find('**/body'):
                return self
        if self.loseActor == None:
            if self.hdModel and not self.isSkeleton:
                # The HD model plays its own defeat: the explosion animation
                # was made for a cut-down copy of the same skeleton, and
                # binds to this one by joint name.  Head and clothes are
                # part of the model.
                filePrefix, phase = TutorialModelDict[self.style.body]
                loseAnim = 'phase_' + str(phase) + filePrefix + 'lose'
                self.loseActor = Actor.Actor(hdModelPath(self.style.name))
                # The animation calls the skeleton's root by another name
                # (suitC_lose for suitC); it only binds if the names agree.
                skeleton = self.loseActor.getPartBundle('modelRoot').findChild('<skeleton>')
                if skeleton is not None and skeleton.getNumChildren() == 1:
                    root = skeleton.getChild(0)
                    if not root.getName().endswith('_lose'):
                        root.setName(root.getName() + '_lose')
                self.loseActor.loadAnims({'lose': loseAnim})
                self.followHips(self.loseActor, 'lose')
                if self.loseActor.find('**/joint_shadow').isEmpty():
                    self.loseActor.exposeJoint(None, 'modelRoot', 'joint_shadow')
            elif not self.isSkeleton:
                filePrefix, phase = TutorialModelDict[self.style.body]
                loseModel = 'phase_' + str(phase) + filePrefix + 'lose-mod'
                loseAnim = 'phase_' + str(phase) + filePrefix + 'lose'
                self.loseActor = Actor.Actor(loseModel, {'lose': loseAnim})
                loseNeck = self.loseActor.find('**/joint_head')
                for part in self.headParts:
                    part.instanceTo(loseNeck)

                if self.isWaiter:
                    self.makeWaiter(self.loseActor)
                else:
                    self.setSuitClothes(self.loseActor)
            else:
                loseModel = 'phase_5/models/char/cog' + self.style.body.upper() + '_robot-lose-mod'
                filePrefix, phase = TutorialModelDict[self.style.body]
                loseAnim = 'phase_' + str(phase) + filePrefix + 'lose'
                self.loseActor = Actor.Actor(loseModel, {'lose': loseAnim})
                self.generateCorporateTie(self.loseActor)
        self.loseActor.setScale(self.scale)
        self.loseActor.setPos(self.getPos())
        self.loseActor.setHpr(self.getHpr())
        shadowJoint = self.loseActor.find('**/joint_shadow')
        dropShadow = loader.loadModel('phase_3/models/props/drop_shadow')
        dropShadow.setScale(0.45)
        dropShadow.setColor(0.0, 0.0, 0.0, 0.5)
        dropShadow.reparentTo(shadowJoint)
        return self.loseActor

    def followHips(self, actor, animName):
        """The defeat animation was made for a skeleton without some of
        the joints an HD model's coat hangs from.  Left alone they stay
        where they stood while the body moves away, and the coat stretches
        out to them.  They are carried along rigidly with the hips."""
        bundle = actor.getPartBundle('modelRoot')
        skeleton = bundle.findChild('<skeleton>')
        control = actor.getAnimControl(animName)
        if skeleton is None or skeleton.getNumChildren() != 1 or control is None:
            return
        root = skeleton.getChild(0)
        animSkeleton = control.getAnim().findChild('<skeleton>')
        if animSkeleton is None or animSkeleton.getNumChildren() != 1:
            return
        animRoot = animSkeleton.getChild(0)
        driven = set(animRoot.getChild(i).getName() for i in range(animRoot.getNumChildren()))
        if 'to_MAIN' not in driven:
            return
        rest = {}
        for i in range(root.getNumChildren()):
            joint = root.getChild(i)
            if isinstance(joint, CharacterJoint):
                rest[joint.getName()] = LMatrix4(joint.getDefaultValue())
        hipsRest = LMatrix4()
        hipsRest.invertFrom(rest['to_MAIN'])
        followers = []
        for name, mat in rest.items():
            if name in driven or name.startswith('joint_'):
                continue
            node = actor.controlJoint(None, 'modelRoot', name)
            followers.append((node, mat * hipsRest))
        # Deeper joints the animation has no place for (it keeps the right
        # thumb under a joint HD models don't have) get bound to the wrong
        # channel and fly off; hold them in their rest pose instead.
        def paths(group, prefix, out):
            for i in range(group.getNumChildren()):
                child = group.getChild(i)
                out[child.getName()] = prefix
                paths(child, prefix + '/' + child.getName(), out)
            return out
        animPaths = paths(animRoot, '', {})

        def hold(joint, prefix, top):
            for i in range(joint.getNumChildren()):
                child = joint.getChild(i)
                name = child.getName()
                if not isinstance(child, CharacterJoint):
                    continue
                if not top and animPaths.get(name) != prefix:
                    actor.controlJoint(None, 'modelRoot', name).setMat(LMatrix4(child.getDefaultValue()))
                hold(child, prefix + '/' + name, False)
        hold(root, '', True)
        hips = actor.exposeJoint(None, 'modelRoot', 'to_MAIN')
        rootNode = actor.exposeJoint(None, 'modelRoot', root.getName())

        def follow(task):
            if actor.isEmpty() or hips.isEmpty():
                return task.done
            now = hips.getMat(rootNode)
            for node, offset in followers:
                node.setMat(offset * now)
            # From here the animation throws the pieces of the old model
            # apart, which would pull a one-piece model into sheets.  The
            # explosion goes off at this moment and covers the exit.
            flying = control.getFrame() >= HD_LOSE_LAST_FRAME
            if flying != actor.isHidden():
                if flying:
                    actor.hide()
                else:
                    actor.show()
            return task.cont

        self.followHipsTask = taskMgr.add(follow, self.uniqueName('hd-lose-follow') if hasattr(self, 'uniqueName') else 'hd-lose-follow-%d' % id(self), sort=30)

    def cleanupLoseActor(self):
        task = getattr(self, 'followHipsTask', None)
        if task is not None:
            taskMgr.remove(task)
            self.followHipsTask = None
        self.notify.debug('cleanupLoseActor()')
        if self.loseActor != None:
            self.notify.debug('cleanupLoseActor() - got one')
            self.loseActor.cleanup()
        self.loseActor = None
        return

    def makeSkeleton(self):
        model = 'phase_5/models/char/cog' + self.style.body.upper() + '_robot-zero'
        anims = self.generateAnimDict()
        anim = self.getCurrentAnim()
        dropShadow = self.dropShadow
        if not dropShadow.isEmpty():
            dropShadow.reparentTo(hidden)
        self.removePart('modelRoot')
        self.hdModel = False  # skeletons use the original robot model
        self.loadModel(model)
        self.loadAnims(anims)
        self.getGeomNode().setScale(self.scale * 1.0173)
        self.generateHealthBar()
        self.generateCorporateMedallion()
        self.generateCorporateTie()
        self.setHeight(self.height)
        parts = self.findAllMatches('**/pPlane*')
        for partNum in range(0, parts.getNumPaths()):
            bb = parts.getPath(partNum)
            bb.setTwoSided(1)

        self.setName(TTLocalizer.Skeleton)
        nameInfo = TTLocalizer.SuitBaseNameWithLevel % {'name': self._name,
         'dept': self.getStyleDept(),
         'level': self.getActualLevel()}
        self.setDisplayName(nameInfo)
        self.leftHand = self.find('**/joint_Lhold')
        self.rightHand = self.find('**/joint_Rhold')
        self.shadowJoint = self.find('**/joint_shadow')
        self.nametagNull = self.find('**/joint_nameTag')
        if not dropShadow.isEmpty():
            dropShadow.setScale(0.75)
            if not self.shadowJoint.isEmpty():
                dropShadow.reparentTo(self.shadowJoint)
        self.loop(anim)
        self.isSkeleton = 1

    def getHeadParts(self):
        return self.headParts

    def getRightHand(self):
        return self.rightHand

    def getLeftHand(self):
        return self.leftHand

    def getShadowJoint(self):
        return self.shadowJoint

    def getNametagJoints(self):
        return []

    def getDialogueArray(self):
        if self.isSkeleton:
            loadSkelDialog()
            return SkelSuitDialogArray
        else:
            return SuitDialogArray
