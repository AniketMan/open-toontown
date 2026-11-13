"""
Render at the display's real pixel density on macOS Retina screens.

By default Panda3D opens a window whose size is in points and lets macOS
stretch the image 2x, which looks soft.  With dpi-aware on, window sizes are
in real pixels instead, so the window would come out half as large;
pixels() converts the size the player asked for so the window stays the same
size on screen, now with every pixel drawn.

Config:
  want-hidpi  #t/#f  (default #t)
"""
import sys
from panda3d.core import ConfigVariableBool, GraphicsPipeSelection, loadPrcFileData

_active = False
_zoom = None


def prepare():
    """Call before the window is opened."""
    global _active
    if sys.platform != 'darwin' or not ConfigVariableBool('want-hidpi', True).value:
        return False
    loadPrcFileData('hidpi', 'dpi-aware 1')
    _active = True
    return True


def zoom():
    """The display's pixel density (2.0 on Retina), or 1.0 when inactive."""
    global _zoom
    if not _active:
        return 1.0
    if _zoom is None:
        pipe = GraphicsPipeSelection.getGlobalPtr().makeDefaultPipe()
        _zoom = max(pipe.getDisplayZoom(), 1.0) if pipe is not None else 1.0
    return _zoom


def pixels(width, height):
    """Converts a window size chosen by the player into real pixels."""
    z = zoom()
    return int(round(width * z)), int(round(height * z))
