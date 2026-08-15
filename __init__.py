"""Public compatibility facade for Bento Forge.

The Qt/Anki dialog implementation lives in :mod:`ui.factory_dialog`.  Keeping
these exports at the package root preserves the add-on entry points used by
Anki and existing integrations during the architecture transition.
"""

import os
import sys


_addon_root = os.path.dirname(os.path.abspath(__file__))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

from ui import factory_dialog as _factory_dialog

AnkiSmartFactory = _factory_dialog.AnkiSmartFactory
start_smart_factory = _factory_dialog.start_smart_factory

__all__ = ["AnkiSmartFactory", "start_smart_factory"]


def __getattr__(name):
    """Temporarily forward legacy module attributes to their UI owner."""
    return getattr(_factory_dialog, name)
