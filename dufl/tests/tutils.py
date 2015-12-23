from contextlib import contextmanager
from mock import patch

from .. import app
from .. import cli 
from .. import utils 


@contextmanager
def patch_app(*names):
    """ Helper context manager to patch methods in the app library 
   
    Args:
        *names: List of functions to patch in the app module
    Yields:
        Mock or list(Mock): Mock(s) representing the patched functions
    """
    with patch(app.__name__ + '.' + names[0]) as p:
        if len(names) > 1:
            with patch_app(*names[1:]) as patches:
                if not isinstance(patches, list):
                    patches = list([patches])
                yield list([p]) + patches
        else:
            yield p


@contextmanager
def patch_cli(*names):
    """ Helper context manager to patch methods in the cli module 
   
    Args:
        *names: List of functions to patch in the cli module
    Yields:
        Mock or list(Mock): Mock(s) representing the patched functions
    """
    with patch(cli.__name__ + '.' + names[0]) as p:
        if len(names) > 1:
            with patch_cli(*names[1:]) as patches:
                if not isinstance(patches, list):
                    patches = list([patches])
                yield list([p]) + patches
        else:
            yield p


@contextmanager
def patch_utils(*names):
    """ Helper context manager to patch methods in the utils module 
   
    Args:
        *names: List of functions to patch in the utils module
    Yields:
        Mock or list(Mock): Mock(s) representing the patched functions
    """
    with patch(utils.__name__ + '.' + names[0]) as p:
        if len(names) > 1:
            with patch_utils(*names[1:]) as patches:
                if not isinstance(patches, list):
                    patches = list([patches])
                yield list([p]) + patches
        else:
            yield p
