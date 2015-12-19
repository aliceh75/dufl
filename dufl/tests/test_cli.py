import click
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


def test_provided_dufl_root_added_to_context():
    runner = CliRunner()
    r = runner.invoke(
        cli.cli, ['-r', '/some/where', '--debug']
    )
    ctx_obj = _get_internal_context(r.output, 0)
    assert ctx_obj['dufl_root'] == '/some/where'


def test_default_dufl_root_is_in_current_user_home_dir():
    runner = CliRunner()
    with patch(cli.__name__ + '.os.path.expanduser') as e:
        e.return_value = 'expanded-path'
        r = runner.invoke(
            cli.cli, ['--debug']
        )
        assert e.call_args[0][0] == '~/.dufl'

    ctx_obj = _get_internal_context(r.output, 0)
    assert ctx_obj['dufl_root'] == 'expanded-path'


def test_default_dufl_root_is_expanded():
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
        r = runner.invoke(
            cli.cli, [
                '-r', dufl_root,
                'init', 'https://git.example.com/example.git'
            ]
        )
        assert os.path.isdir(os.path.join(dufl_root, '.git'))


def test_dufl_init_sets_git_repo_remote():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        r = runner.invoke(
            cli.cli, [
                '-r', dufl_root,
                'init', 'https://git.example.com/example.git'
            ]
        )
        git = utils.Git('/usr/bin/git', dufl_root)
        out = git.get_output('remote', '-v')
        # FIXME: If different git version has different output, this will fail.
        assert re.match(
            'origin\s+https://git\.example\.com/example\.git',
            out,
            re.MULTILINE
        )


def test_dufl_init_pulls_remote_if_present():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        dufl_root = os.path.join(here, '.dufl')
        with patch(cli.__name__ + '.Git') as Git:
            git = Git.return_value
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
        with patch(cli.__name__ + '.Git') as Git:
            def raise_on_ls_remote(*args, **kwargs):
                if args[0] == 'ls-remote':
                    raise utils.GitError()
            git = Git.return_value
            git.run.side_effect = raise_on_ls_remote
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
        with patch(cli.__name__ + '.Git') as Git:
            def raise_on_ls_remote(*args, **kwargs):
                if args[0] == 'ls-remote':
                    raise utils.GitError()
            git = Git.return_value
            git.run.side_effect = raise_on_ls_remote
            r = runner.invoke(
                cli.cli, [
                    '-r', dufl_root,
                    'init', 'https://git.example.com/example.git'
                ]
            )

        with open(os.path.join(dufl_root, 'settings.yaml')) as f:
            settings = yaml.load(f.read())
        assert settings == {'git': '/usr/bin/git'}
