import os
import pytest
import tempfile
import re
import shutil

from click.testing import CliRunner
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


def _create_temp_folder(request, chdir=False):
    """ Create a temporary folder, and return it's path.

    This will add a finalizer to the fixture to ensure
    the folder is removed when the fixture goes out of
    scope.

    If chdir is true, set the current working directory
    to the temporary folder (and restore previous dir
    on clean up)

    Args:
        request: Fixture request object
        chdir (bool): True to change the current working
            directory to the created folder.
    Returns:
        str: Path to the temporary folder
    """
    temp_folder = tempfile.mkdtemp()
    if chdir:
        cwd = os.getcwd()
        os.chdir(temp_folder)
    def finalize():
        if chdir:
            os.chdir(cwd)
        try:
            shutil.rmtree(temp_folder)
        except (OSError, IOError):
            pass
    request.addfinalizer(finalize)
    return temp_folder


def _create_git_repo(request):
    """ Create a git repository, and return a Git object

    This will create a new git repository with a single
    file 'readme.txt' commited to the master branch.

    Args:
        request: Fixture request object
    Returns:
        Git: Git object
    """
    temp_folder = _create_temp_folder(request, chdir=False)
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


def create_files_in_folder(root, content):
    """ Create files with content in a given folder

    Args:
        root (str): The folder under which the files will be created
        content (dict): Dictionary of file name/path to file content
    Returns:
        dict: Dictionary of file name/path (as defined in the 'content'
            dict) to the absolute file name
    """
    result = {}
    for name, data in content.items():
        full_name = os.path.join(
            root,
            re.sub('^/+', '', name)
        )
        if not os.path.exists(os.path.dirname(full_name)):
            os.makedirs(os.path.dirname(full_name))
        with open(full_name, 'w') as f:
            f.write(data)
        result[name] = full_name
    return result


def add_content_to_remote_git_repo(remote, content):
    """ Add content to remote git repository

    Args:
        remote (str): Address of the remote repository
        content (dict): Dictionary of file name to file content
    """
    temp_folder = tempfile.mkdtemp()
    git = utils.Git('/usr/bin/git', temp_folder)
    git.run('init')
    git.run('remote', 'add', 'origin', remote)
    git.run('pull', 'origin', 'master')
    for name, data in content.items():
        repo_name = os.path.join(
            temp_folder,
            re.sub('^/+', '', name)
        )
        if not os.path.exists(os.path.dirname(repo_name)):
            os.makedirs(os.path.dirname(repo_name))
        with open(repo_name, 'w') as f:
            f.write(data)
        git.run('add', repo_name)
    git.run('commit', '-m', 'Added files to remote')
    git.run('push', 'origin', 'master')
    try:
        shutil.rmtree(temp_folder)
    except (OSError, IOError):
        pass


@pytest.fixture
def cli_run():
    """ Fixture to return a function used to invoke the cli commands

    This invokes Click's CliRunner, and returns a click.testing.Result
    object as per http://click.pocoo.org/5/api/#click.testing.Result
    which contains the following properties:

    - exc_info: traceback if an exception was raised
    - exception: exception if one was raised
    - exit_code: the exit code
    - output: the command output (as string)
    - output_bytes: the command output (as bytes)
    - runner: the runner object that was invoked

    Returns:
        click.testing.Result: The result
    """
    runner = CliRunner()
    def _run(*args):
        return runner.invoke(cli.cli, args)

    return _run


@pytest.fixture
def temp_folder(request):
    """ Fixture to create a temporary folder, and set the cwd to it.

    The path is provided as the fixture value, and the folder
    deleted when done.

    Based on click's isolated_filesystem, but works as a fixture
    rathen than a context manager.
    """
    return _create_temp_folder(request, chdir=True)


@pytest.fixture
def temp_folder_2(request):
    """ Fixture to create a temporary folder, and set the cwd to it.

    The path is provided as the fixture value, and the folder
    deleted when done.

    Based on click's isolated_filesystem, but works as a fixture
    rathen than a context manager.
    """
    return _create_temp_folder(request, chdir=True)


@pytest.fixture
def user_home(request):
    """ Fixture to fake a current user.

    An empty home folder is created. app.os.path.expanduser
    is patched to return the path to that. The fixture value
    is the path to the user home folder.
    """
    temp_folder = _create_temp_folder(request, chdir=False)

    patcher = patch(app.__name__ + '.os.path.expanduser')
    def finalize():
        patcher.stop()
    request.addfinalizer(finalize)

    def do_expand(value):
        expanded = re.sub('^~[^/]*', temp_folder, value)
        return expanded
    expand_user = patcher.start()
    expand_user.side_effect = do_expand
    return temp_folder


@pytest.fixture
def git(request):
    """ Fixture to provide an initialized git repository.

    This requires the Git binary to be in the path
    """
    return _create_git_repo(request)


@pytest.fixture
def remote_git_path(request):
    """ Fixture to provide a bare git repo to use as remote

    The fixture value is the path to the bare repo.

    Args:
        request: The fixture request
    Returns:
        str: The path to the bare repo
    """
    temp_folder = _create_temp_folder(request, chdir=False)
    git = utils.Git('/usr/bin/git', temp_folder)
    git.run('init', '--bare')

    # Ensure our remote repo has a master branch.
    git_2 = _create_git_repo(request)
    git_2.run('remote', 'add', 'origin', temp_folder)
    git_2.run('push', 'origin', 'master')

    return temp_folder
