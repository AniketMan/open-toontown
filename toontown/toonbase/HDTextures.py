"""
Optional HD texture pack.

tools/upscale_textures.py writes 4x upscaled copies of the game's textures
into resources-hd/, mirroring the layout of resources/.  That folder is laid
over resources/ in Panda's virtual file system, so every model picks up the
HD version of a texture when one exists and the original when it doesn't.
Nothing in resources/ is modified.

Config:
  want-hd-textures  #t/#f   use the pack if it is present (default #t)
  hd-texture-path   resources-hd
"""
import os
from panda3d.core import (ConfigVariableBool, ConfigVariableString, Filename,
                          VirtualFileSystem, loadPrcFileData)


def enable():
    """Call once, after the config is loaded and before any model is."""
    if not ConfigVariableBool('want-hd-textures', True).value:
        return False
    path = ConfigVariableString('hd-texture-path', 'resources-hd').value
    if not os.path.isdir(path):
        return False
    # Keep the extra detail when a surface is seen at an angle, and don't
    # let Panda shrink the larger images.
    loadPrcFileData('hd-textures', 'texture-anisotropic-degree 8\nmax-texture-dimension -1')
    # Models refer to their textures relative to their own folder, so a
    # search-path entry alone would be bypassed.  Overlaying the pack on top
    # of resources/ in the virtual file system covers every lookup: files
    # the pack has are read from it, everything else falls through.
    base = ConfigVariableString('hd-texture-base', 'resources').value
    vfs = VirtualFileSystem.getGlobalPtr()
    return vfs.mount(Filename.fromOsSpecific(os.path.abspath(path)),
                     Filename.fromOsSpecific(os.path.abspath(base)), 0)
