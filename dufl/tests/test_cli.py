import click
import contextlib
import os
import re
import yaml

from click.testing import CliRunner
from contextlib import contextmanager
from mock import call
from tutils import (
    patch_cli, temp_folder, temp_folder_2, cli_run, remote_git_path,
    add_content_to_remote_git_repo, user_home
)

from .. import cli
from .. import defaults
from .. import utils


def test_dufl_init_exits_with_error_if_dufl_root_already_exists(cli_run, temp_folder):
    dufl_root = os.path.join(temp_folder, '.dufl')
    os.makedirs(dufl_root)

    r = cli_run('-r', dufl_root, 'init')

    assert r.exit_code != 0
    assert ('Folder %s already exists, cannot initialize.' % dufl_root) in r.output


def test_dufl_init_creates_dufl_root(cli_run, temp_folder):
    dufl_root = os.path.join(temp_folder, '.dufl')
    r = cli_run('-r', dufl_root, 'init')
    assert os.path.isdir(dufl_root)


def test_dufl_init_warns_user_if_no_remote_is_specified(cli_run, temp_folder):
    dufl_root = os.path.join(temp_folder, '.dufl')
    r = cli_run('-r', dufl_root, 'init')
    assert 'No remote specified' in r.output


def test_dufl_init_initializes_git_repo_in_new_dufl_root(cli_run, temp_folder):
    dufl_root = os.path.join(temp_folder, '.dufl')

    r = cli_run('-r', dufl_root, 'init')

    git = utils.Git('/usr/bin/git', dufl_root)
    try:
        git.run('status')
    except utils.GitError:
        assert False


def test_dufl_init_sets_git_repo_remote(cli_run, temp_folder, remote_git_path):
    dufl_root = os.path.join(temp_folder, '.dufl')

    r = cli_run('-r', dufl_root, 'init', remote_git_path)

    git = utils.Git('/usr/bin/git', dufl_root)
    remotes = git.get_output('remote', '-v')
    assert remote_git_path in remotes


def test_dufl_init_pulls_remote_if_present(cli_run, temp_folder, remote_git_path):
    dufl_root = os.path.join(temp_folder, '.dufl')
    add_content_to_remote_git_repo(remote_git_path, {
        'remote_file.txt': 'hello'
    })

    r = cli_run('-r', dufl_root, 'init', remote_git_path)

    assert os.path.isfile(os.path.join(dufl_root, 'remote_file.txt'))


def test_dufl_init_creates_skeleton_folders_when_then_is_no_remote_repository(cli_run, temp_folder):
    dufl_root = os.path.join(temp_folder, '.dufl')
    r = cli_run('-r', dufl_root, 'init')
    assert os.path.isdir(os.path.join(dufl_root, 'home'))
    assert os.path.isdir(os.path.join(dufl_root, 'root'))
    assert os.path.isfile(os.path.join(dufl_root, 'settings.yaml'))


def test_dufl_init_creates_skeleton_folders_when_remote_does_not_include_them(cli_run, temp_folder, remote_git_path):
    dufl_root = os.path.join(temp_folder, '.dufl')
    add_content_to_remote_git_repo(remote_git_path, {
        'remote_file.txt': 'hello'
    })

    r = cli_run('-r', dufl_root, 'init', remote_git_path)

    # Check we pulled
    assert os.path.isfile(os.path.join(dufl_root, 'remote_file.txt'))
    # And still created the skeletons
    assert os.path.isdir(os.path.join(dufl_root, 'home'))
    assert os.path.isdir(os.path.join(dufl_root, 'root'))
    assert os.path.isfile(os.path.join(dufl_root, 'settings.yaml'))


def test_dufl_init_creates_default_settings_file_when_remote_does_not_include_it(cli_run, temp_folder, remote_git_path):
    dufl_root = os.path.join(temp_folder, '.dufl')
    add_content_to_remote_git_repo(remote_git_path, {
        'remote_file.txt': 'hello'
    })


    r = cli_run('-r', dufl_root, 'init', remote_git_path)

    # Check we pulled
    assert os.path.isfile(os.path.join(dufl_root, 'remote_file.txt'))
    # Check we created the default settings.yaml
    with open(os.path.join(dufl_root, 'settings.yaml')) as f:
        settings = yaml.load(f.read())
    for key in defaults.settings:
        assert settings[key] == defaults.settings[key]


def test_dufl_init_does_not_overwrite_settings_file_pulled_from_remote(cli_run, temp_folder, remote_git_path):
    dufl_root = os.path.join(temp_folder, '.dufl')
    add_content_to_remote_git_repo(remote_git_path, {
        'settings.yaml': yaml.dump({
            'git': '/a/very/different/location'
        })
    })

    r = cli_run('-r', dufl_root, 'init', remote_git_path)

    with open(os.path.join(dufl_root, 'settings.yaml')) as f:
        settings = yaml.load(f.read())
    assert settings == {'git': '/a/very/different/location'}


def test_dufl_init_adds_and_commits_initial_settings_file(cli_run, temp_folder):
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init')

    git = utils.Git('/usr/bin/git', dufl_root)
    files = git.get_output('ls-files')
    assert 'settings.yaml' in files


def test_dufl_add_copies_file_not_in_home_to_dufl_root_subfolder(cli_run, temp_folder, temp_folder_2):
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init')

    file_to_add = os.path.join(temp_folder_2, 'the', 'path', 'file.txt')
    os.makedirs(os.path.dirname(file_to_add))
    with open(file_to_add, 'w') as f:
        f.write('hello')

    cli_run('-r', dufl_root, 'add', file_to_add)

    assert os.path.isfile(os.path.join(
        dufl_root, 'root',
        re.sub('^/', '', file_to_add)
    ))


def test_dufl_add_copies_file_in_home_to_dufl_home_subfolder(cli_run, temp_folder, user_home):
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init')

    file_to_add = os.path.join(user_home, 'the', 'path', 'file.txt')
    os.makedirs(os.path.dirname(file_to_add))
    with open(file_to_add, 'w') as f:
        f.write('hello')

    cli_run('-r', dufl_root, 'add', file_to_add)

    assert os.path.isfile(os.path.join(
        dufl_root, 'home', 'the', 'path', 'file.txt'
    ))


def test_dufl_add_adds_and_commits_file_to_git(cli_run, temp_folder, temp_folder_2):
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init')

    file_to_add = os.path.join(temp_folder_2, 'the', 'path', 'file.txt')
    os.makedirs(os.path.dirname(file_to_add))
    with open(file_to_add, 'w') as f:
        f.write('hello')

    cli_run('-r', dufl_root, 'add', file_to_add)

    git = utils.Git('/usr/bin/git', dufl_root)
    files = git.get_output('ls-files')
    assert 'the/path/file.txt' in files


#def test_dufl_add_does_not_add_file_whose_name_matches_security_rule():
#    runner = CliRunner()
#    with runner.isolated_filesystem():
#        here = os.getcwd()
#        dufl_root = os.path.join(here, '.dufl')
#        _prepare_empty_dufl_folder(dufl_root)
#        file_to_add = os.path.join(here, 'one', 'two', 'three.txt')
#        os.makedirs(os.path.dirname(file_to_add))
#        with open(file_to_add, 'w') as f:
#            f.write('hello world')
#        with open(os.path.join(dufl_root, 'settings.yaml'), 'w') as f:
#            f.write(yaml.dump({
#                'suspicious_names': {
#                    'three\.[^.]+$': 'no by name!'
#                },
#                'suspicious_content': {}
#            }))
#        with _mock_git(remote_exists=False) as git:
#            r = runner.invoke(
#                cli.cli, [
#                    '-r', dufl_root,
#                    'add', file_to_add
#                ]
#            )
#            assert r.exit_code != 0
#            assert 'no by name!' in r.output
#            assert not os.path.isfile(os.path.join(
#                dufl_root, 'root',
#                re.sub('^/', '', file_to_add)
#            ))
#
#def test_dufl_add_does_not_add_file_whose_content_matches_security_rule():
#    runner = CliRunner()
#    with runner.isolated_filesystem():
#        here = os.getcwd()
#        dufl_root = os.path.join(here, '.dufl')
#        _prepare_empty_dufl_folder(dufl_root)
#        file_to_add = os.path.join(here, 'one', 'two', 'three.txt')
#        os.makedirs(os.path.dirname(file_to_add))
#        with open(file_to_add, 'w') as f:
#            f.write("hello\n here is a PRIVATE KEY ;)\n!")
#        with open(os.path.join(dufl_root, 'settings.yaml'), 'w') as f:
#            f.write(yaml.dump({
#                'suspicious_names': {},
#                'suspicious_content': {
#                    'PRIVATE KEY': 'no by content!'
#                }
#            }))
#        with _mock_git(remote_exists=False) as git:
#            r = runner.invoke(
#                cli.cli, [
#                    '-r', dufl_root,
#                    'add', file_to_add
#                ]
#            )
#            assert r.exit_code != 0
#            assert 'no by content!' in r.output
#            assert not os.path.isfile(os.path.join(
#                dufl_root, 'root',
#                re.sub('^/', '', file_to_add)
#            ))
#
#def test_dufl_add_uses_provided_commit_message():
#    runner = CliRunner()
#    with runner.isolated_filesystem():
#        here = os.getcwd()
#        dufl_root = os.path.join(here, '.dufl')
#        _prepare_empty_dufl_folder(dufl_root)
#        file_to_add = os.path.join(here, 'one', 'two', 'three.txt')
#        os.makedirs(os.path.dirname(file_to_add))
#        with open(os.path.join(here, file_to_add), 'w') as f:
#            f.write('hello world')
#        with _mock_git(remote_exists=False) as git:
#            commit_call = call('commit', '-m', 'Good job!')
#            r = runner.invoke(
#                cli.cli, [
#                    '-r', dufl_root,
#                    'add', file_to_add,
#                    '-m', 'Good job!'
#                ]
#            )
#            assert commit_call in git.run.call_args_list
#
#def test_dufl_push_pushes_to_git():
#    runner = CliRunner()
#    with runner.isolated_filesystem():
#        here = os.getcwd()
#        dufl_root = os.path.join(here, '.dufl')
#        _prepare_empty_dufl_folder(dufl_root)
#        file_to_add = os.path.join(here, 'one', 'two', 'three.txt')
#        os.makedirs(os.path.dirname(file_to_add))
#        with open(os.path.join(here, file_to_add), 'w') as f:
#            f.write('hello world')
#        with _mock_git() as git:
#            push_call = call('push')
#            r = runner.invoke(
#                cli.cli, [
#                    '-r', dufl_root,
#                    'push'
#                ]
#            )
#            assert push_call in git.run.call_args_list
