from contextlib import contextmanager
from mock import patch
from subprocess import CalledProcessError

from .. import utils
from ..utils import canonize_path, Git, GitError


@contextmanager
def _patch_utils(name):
    """ Helper context manager to patch methods in the utils library """
    with patch(utils.__name__ + '.' + name) as p:
        yield p


def test_canonize_path_returns_absolute_path_if_not_in_home_dir():
    out = canonize_path('/some/where')
    assert out == '/some/where'


def test_canonize_path_resolves_absolute_path():
    out = canonize_path('/some/where/else/../beautiful')
    assert out == '/some/where/beautiful'


def test_canonize_path_returns_relative_path_if_in_home_dir():
    with _patch_utils('os.path.expanduser') as expanduser:
        expanduser.return_value = '/home/user'
        out = canonize_path('/home/user/some/where')
    assert out == '~/some/where'


def test_canonize_path_strips_trailing_slash():
    out = canonize_path('/some/where/')
    assert out == '/some/where'


def test_git_run_invokes_provided_git_binary():
    with _patch_utils('check_call') as check_call:
        git = Git('/some/bin/git', '~/.dufl')
        check_call.return_value = 0
        git.run('pull')
        assert check_call.call_args[0][0][0] == '/some/bin/git'


def test_git_get_output_invokes_provided_git_binary():
    with _patch_utils('check_output') as check_output:
        git = Git('/some/bin/git', '~/.dufl')
        git.get_output('pull')
        assert check_output.call_args[0][0][0] == '/some/bin/git'


def test_git_run_uses_provided_git_root():
    with _patch_utils('check_call') as check_call:
        git = Git('/usr/bin/git', '/some/dufl/root')
        check_call.return_value = 0
        git.run('pull')
        assert check_call.call_args[0][0][1] == '-C'
        assert check_call.call_args[0][0][2] == '/some/dufl/root'


def test_git_get_output_uses_provided_git_root():
    with _patch_utils('check_output') as check_output:
        git = Git('/usr/bin/git', '/some/dufl/root')
        git.get_output('pull')
        assert check_output.call_args[0][0][1] == '-C'
        assert check_output.call_args[0][0][2] == '/some/dufl/root'


def test_git_run_runs_expected_command():
    with _patch_utils('check_call') as check_call:
        git = Git('/usr/bin/git', '~/.dufl')
        check_call.return_value = 0
        git.run('remote', 'add', 'origin', 'http://github.com/example/example.git')
        assert check_call.call_args[0][0][3:] == ['remote', 'add', 'origin', 'http://github.com/example/example.git']


def test_git_get_output_runs_expected_command():
    with _patch_utils('check_output') as check_output:
        git = Git('/usr/bin/git', '~/.dufl')
        git.get_output('remote', 'add', 'origin', 'http://github.com/example/example.git')
        assert check_output.call_args[0][0][3:] == ['remote', 'add', 'origin', 'http://github.com/example/example.git']


def test_git_run_raises_on_failure():
    with _patch_utils('check_call') as check_call:
        git = Git('/usr/bin/git', '~/.dufl')
        check_call.return_value = 1
        try:
            git.run('pull')
            assert False
        except GitError:
            assert True


def test_git_get_output_raises_on_failure():
    with _patch_utils('check_output') as check_output:
        git = Git('/usr/bin/git', '~/.dufl')
        check_output.side_effect = CalledProcessError(1, 1)
        try:
            git.get_output('pull')
            assert False
        except GitError:
            assert True


def test_git_get_output_returns_command_output():
    with _patch_utils('check_output') as check_output:
        check_output.return_value = 'hello world'
        git = Git('/usr/bin/git', '~/.dufl')
        out = git.get_output('pull')
        assert out == 'hello world'
