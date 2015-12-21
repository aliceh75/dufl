import click
import contextlib
import os
import re
import yaml

from click.testing import CliRunner
from mock import patch, call

from .. import cli
from .. import utils


class NoInternalContext(Exception):
    pass


def _get_internal_context(out, n):
    """ Return the nth internal context dump of a command invoked with --debug """
    matches = re.search(
        'context\\[%s\\](.+)^end\\[%s\\]' % (n, n),
        out,
        re.MULTILINE|re.DOTALL
    )
    try:
        return yaml.load(matches.group(1).strip())
    except AttributeError:
        raise NoInternalContext()


@contextlib.contextmanager
def _mock_git(remote_exists=True):
    """ Context manager used to mock the git utility """
    def _git_run_side_effect(*args, **kwargs):
        if not remote_exists and args[0] == 'ls-remote':
            raise utils.GitError()
    with patch(cli.__name__ + '.Git') as Git:
        git = Git.return_value
        git.Git = Git
        git.run.side_effect = _git_run_side_effect
        yield git


def _prepare_empty_dufl_folder(dufl_root):
    """ Prepares a (mock) empty dufl folder at the given path """
    os.makedirs(dufl_root)
    os.makedirs(os.path.join(dufl_root, 'root'))
    os.makedirs(os.path.join(dufl_root, 'home'))


def test_debug_output_can_be_parsed():
    runner = CliRunner()
    r = runner.invoke(
        cli.cli, ['--debug']
    )
    ctx_obj = _get_internal_context(r.output, 0)
    assert True


def test_debug_output_is_not_empty():
    runner = CliRunner()
    r = runner.invoke(
        cli.cli, ['--debug']
    )
    ctx_obj = _get_internal_context(r.output, 0)
    assert len(ctx_obj.keys()) > 0


def test_debug_mode_set_on_context():
    runner = CliRunner()
    r = runner.invoke(
        cli.cli, ['--debug']
    )
    ctx_obj = _get_internal_context(r.output, 0)
    assert ctx_obj['debug'] is True


def test_provided_dufl_root_path_added_to_context():
    runner = CliRunner()
    r = runner.invoke(
        cli.cli, ['-r', '/some/where', '--debug']
    )
    ctx_obj = _get_internal_context(r.output, 0)
    assert ctx_obj['dufl_root'] == '/some/where'


def test_default_dufl_root_path_is_in_current_user_home_dir():
    runner = CliRunner()
    with patch(cli.__name__ + '.os.path.expanduser') as e:
        e.return_value = 'expanded-path'
        r = runner.invoke(
            cli.cli, ['--debug']
        )
        assert e.call_args[0][0] == '~/.dufl'

    ctx_obj = _get_internal_context(r.output, 0)
    assert ctx_obj['dufl_root'] == 'expanded-path'


def test_default_dufl_root_path_is_expanded():
    runner = CliRunner()
    with patch(cli.__name__ + '.os.path.expanduser') as e:
        e.return_value = 'expanded-path'
        r = runner.invoke(
            cli.cli, ['--debug']
        )

    ctx_obj = _get_internal_context(r.output, 0)
    assert ctx_obj['dufl_root'] == 'expanded-path'


def test_dufl_init_exits_with_error_if_dufl_root_already_exists():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        os.makedirs(dufl_root)
        with _mock_git() as git:
            r = runner.invoke(
                cli.cli, [
                    '-r', dufl_root,
                    'init', 'https://git.example.com/example.git'
                ]
            )
    assert r.exit_code == 1
    assert ('Folder %s already exists, cannot initialize.' % dufl_root) in r.output


def test_dufl_init_creates_dufl_root():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        with _mock_git() as git:
            r = runner.invoke(
                cli.cli, [
                    '-r', dufl_root,
                    'init', 'https://git.example.com/example.git'
                ]
            )
        assert os.path.isdir(dufl_root)


def test_dufl_init_initializes_git_repo_in_new_dufl_root():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        with _mock_git() as git:
            r = runner.invoke(
                cli.cli, [
                    '-r', dufl_root,
                    'init', 'https://git.example.com/example.git'
                ]
            )
            git.run.assert_any_call('init')
            git.Git.assert_any_call('/usr/bin/git', dufl_root)


def test_dufl_init_sets_git_repo_remote():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        with _mock_git() as git:
            r = runner.invoke(
                cli.cli, [
                    '-r', dufl_root,
                    'init', 'https://git.example.com/example.git'
                ]
            )
            git.run.assert_any_call('remote', 'add', 'origin', 'https://git.example.com/example.git')


def test_dufl_init_pulls_remote_if_present():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        with _mock_git() as git:
            r = runner.invoke(
                cli.cli, [
                    '-r', dufl_root,
                    'init', 'https://git.example.com/example.git'
                ]
            )
            git.run.assert_any_call('init')
            git.run.assert_any_call('ls-remote', 'https://git.example.com/example.git')
            git.run.assert_any_call('pull')


def test_dufl_init_creates_skeleton_if_no_remote():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        with _mock_git(remote_exists=False) as git:
            r = runner.invoke(
                cli.cli, [
                    '-r', dufl_root,
                    'init', 'https://git.example.com/example.git'
                ]
            )
            assert call('pull') not in git.run.call_args_list
        assert os.path.isdir(os.path.join(dufl_root, 'home'))
        assert os.path.isdir(os.path.join(dufl_root, 'root'))
        assert os.path.isfile(os.path.join(dufl_root, 'settings.yaml'))


def test_dufl_init_creates_settings_file_with_git_option():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        with _mock_git(remote_exists=False) as git:
            r = runner.invoke(
                cli.cli, [
                    '-r', dufl_root,
                    'init', 'https://git.example.com/example.git'
                ]
            )

        with open(os.path.join(dufl_root, 'settings.yaml')) as f:
            settings = yaml.load(f.read())
        assert settings == {'git': '/usr/bin/git'}


def test_dufl_add_copies_file_to_dufl_root_subfolder():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        _prepare_empty_dufl_folder(dufl_root)
        file_to_add = os.path.join(here, 'one', 'two', 'three.txt')
        os.makedirs(os.path.dirname(file_to_add))
        with open(file_to_add, 'w') as f:
            f.write('hello world')
        with _mock_git(remote_exists=False) as git:
            r = runner.invoke(
                cli.cli, [
                    '-r', dufl_root,
                    'add', file_to_add
                ]
            )
            assert os.path.isfile(os.path.join(
                dufl_root, 'root',
                re.sub('^\\/', '', file_to_add)
            ))


def test_dufl_add_invokes_get_dufl_file_path():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        _prepare_empty_dufl_folder(dufl_root)
        file_to_add = os.path.join(here, 'one', 'two', 'three.txt')
        os.makedirs(os.path.dirname(file_to_add))
        with open(file_to_add, 'w') as f:
            f.write('hello world')
        with _mock_git(remote_exists=False) as git:
            with patch(cli.__name__ + '.get_dufl_file_path') as get_dufl_file_path:
                get_dufl_file_path.return_value = os.path.join(dufl_root, 'home/four.txt')
                r = runner.invoke(
                    cli.cli, [
                        '-r', dufl_root,
                        'add', file_to_add
                    ]
                )
            assert os.path.isfile(os.path.join(dufl_root, 'home', 'four.txt'))


def test_dufl_add_adds_and_commits_file_to_git():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        _prepare_empty_dufl_folder(dufl_root)
        file_to_add = os.path.join(here, 'one', 'two', 'three.txt')
        os.makedirs(os.path.dirname(file_to_add))
        with open(os.path.join(here, file_to_add), 'w') as f:
            f.write('hello world')
        with _mock_git(remote_exists=False) as git:
            add_call = call('add', os.path.join(
                dufl_root, 'root',
                re.sub('^\\/', '', file_to_add)
            ))
            commit_call = call('commit', '-m', 'Update.')
            r = runner.invoke(
                cli.cli, [
                    '-r', dufl_root,
                    'add', file_to_add
                ]
            )
            assert add_call in git.run.call_args_list
            assert commit_call in git.run.call_args_list


def test_dufl_add_uses_provided_commit_message():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        _prepare_empty_dufl_folder(dufl_root)
        file_to_add = os.path.join(here, 'one', 'two', 'three.txt')
        os.makedirs(os.path.dirname(file_to_add))
        with open(os.path.join(here, file_to_add), 'w') as f:
            f.write('hello world')
        with _mock_git(remote_exists=False) as git:
            commit_call = call('commit', '-m', 'Good job!')
            r = runner.invoke(
                cli.cli, [
                    '-r', dufl_root,
                    'add', file_to_add,
                    '-m', 'Good job!'
                ]
            )
            assert commit_call in git.run.call_args_list

def test_dufl_push_pushes_to_git():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        _prepare_empty_dufl_folder(dufl_root)
        file_to_add = os.path.join(here, 'one', 'two', 'three.txt')
        os.makedirs(os.path.dirname(file_to_add))
        with open(os.path.join(here, file_to_add), 'w') as f:
            f.write('hello world')
        with _mock_git() as git:
            push_call = call('push')
            r = runner.invoke(
                cli.cli, [
                    '-r', dufl_root,
                    'push'
                ]
            )
            assert push_call in git.run.call_args_list
