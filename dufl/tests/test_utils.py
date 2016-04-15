from subprocess import CalledProcessError

from tutils import patch_utils, git, temp_folder
from ..utils import Git, GitError

#
# These tests don't require the git binary - they only
# ensure Git interacts with the binary as expected
#

def test_git_run_invokes_provided_git_binary():
    with patch_utils('check_call') as check_call:
        git = Git('/some/bin/git', '~/.dufl')
        check_call.return_value = 0
        git.run('pull')
        assert check_call.call_args[0][0][0] == '/some/bin/git'


def test_git_get_output_invokes_provided_git_binary():
    with patch_utils('check_output') as check_output:
        git = Git('/some/bin/git', '~/.dufl')
        git.get_output('pull')
        assert check_output.call_args[0][0][0] == '/some/bin/git'


def test_git_run_uses_provided_git_root():
    with patch_utils('check_call') as check_call:
        git = Git('/usr/bin/git', '/some/dufl/root')
        check_call.return_value = 0
        git.run('pull')
        assert check_call.call_args[0][0][1] == '-C'
        assert check_call.call_args[0][0][2] == '/some/dufl/root'


def test_git_get_output_uses_provided_git_root():
    with patch_utils('check_output') as check_output:
        git = Git('/usr/bin/git', '/some/dufl/root')
        git.get_output('pull')
        assert check_output.call_args[0][0][1] == '-C'
        assert check_output.call_args[0][0][2] == '/some/dufl/root'


def test_git_run_runs_expected_command():
    with patch_utils('check_call') as check_call:
        git = Git('/usr/bin/git', '~/.dufl')
        check_call.return_value = 0
        git.run('remote', 'add', 'origin', 'http://github.com/example/example.git')
        assert check_call.call_args[0][0][3:] == ['remote', 'add', 'origin', 'http://github.com/example/example.git']


def test_git_get_output_runs_expected_command():
    with patch_utils('check_output') as check_output:
        git = Git('/usr/bin/git', '~/.dufl')
        git.get_output('remote', 'add', 'origin', 'http://github.com/example/example.git')
        assert check_output.call_args[0][0][3:] == ['remote', 'add', 'origin', 'http://github.com/example/example.git']


def test_git_run_raises_on_status_failure():
    with patch_utils('check_call') as check_call:
        git = Git('/usr/bin/git', '~/.dufl')
        check_call.return_value = 1
        try:
            git.run('pull')
            assert False
        except GitError:
            assert True

def test_git_run_raises_on_exception_failure():
    with patch_utils('check_call') as check_call:
        git = Git('/usr/bin/git', '~/.dufl')
        check_call.side_effect = CalledProcessError(1, 1)
        try:
            git.run('pull')
            assert False
        except GitError:
            assert True

def test_git_get_output_raises_on_failure():
    with patch_utils('check_output') as check_output:
        git = Git('/usr/bin/git', '~/.dufl')
        check_output.side_effect = CalledProcessError(1, 1)
        try:
            git.get_output('pull')
            assert False
        except GitError:
            assert True


def test_git_get_output_returns_command_output():
    with patch_utils('check_output') as check_output:
        check_output.return_value = 'hello world'
        git = Git('/usr/bin/git', '~/.dufl')
        out = git.get_output('pull')
        assert out == 'hello world'


#
# These tests require the git binary, and ensure
# it works as expected.
#

def test_working_branch_returns_checkedout_branch(git):
    git.run('branch', 'somebranch')
    git.run('checkout', 'somebranch')
    assert git.working_branch() == 'somebranch'
    git.run('checkout', 'master')
    assert git.working_branch() == 'master'
