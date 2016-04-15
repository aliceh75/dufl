import os
import pytest
import tempfile
import re
import shutil

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


@pytest.fixture
def temp_folder(request):
    """ Fixture to create a temporary folder, and set the cwd to it.

    The path is provided as the fixture value, and the folder
    deleted when done.

    Based on click's isolated_filesystem, but works as a fixture
    rathen than a context manager.
    """
    cwd = os.getcwd()
    temp_folder = tempfile.mkdtemp()
    os.chdir(temp_folder)
    def finalize():
        os.chdir(cwd)
        try:
            shutil.rmtree(temp_folder)
        except (OSError, IOError):
            pass
    request.addfinalizer(finalize)
    return temp_folder


@pytest.fixture
def user_home(request):
    """ Fixture to fake a current user.

    An empty home folder is created. app.os.path.expanduser
    is patched to return the path to that. The fixture value 
    is the path to the user home folder.
    """
    cwd = os.getcwd()
    temp_folder = tempfile.mkdtemp()
    patcher = patch(app.__name__ + '.os.path.expanduser')
    def finalize():
        # Ensure we're not in the folder
        os.chdir(cwd)
        try:
            shutil.rmtree(temp_folder)
        except (OSError, IOError):
            pass
        patcher.stop()
    def do_expand(value):
        expanded = re.sub('^~[^/]*', temp_folder, value)
        return expanded
    expand_user = patcher.start()
    expand_user.side_effect = do_expand
    request.addfinalizer(finalize)
    return temp_folder
    

@pytest.fixture
def git(temp_folder):
    """ Fixture to provide an initialized git repository.

    This requires the Git binary to be in the path
    """
    git = utils.Git('/usr/bin/git', temp_folder)
    git.run('init')

    # The repository doesn't have master branch until we commit
    # something, so create a file.
    readme = os.path.join(temp_folder, 'readme.txt')
    with open(readme, 'w') as f:
            f.write('hello world')
    git.run('add', readme)
    git.run('commit', '-m', 'readme')

    return git
