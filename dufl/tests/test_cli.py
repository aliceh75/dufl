import click
import contextlib
import os
import re
import yaml

from click.testing import CliRunner
from contextlib import contextmanager
from mock import call
from tutils import (
    patch_cli, temp_folder, cli_run, remote_git_path,
    create_files_in_folder, add_content_to_remote_git_repo, user_home
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


def test_dufl_add_copies_file_not_in_home_to_dufl_root_subfolder(cli_run, temp_folder):
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init')

    file_names = create_files_in_folder(temp_folder, {
        'the/path/file.txt': 'hello'
    })

    cli_run('-r', dufl_root, 'add', file_names['the/path/file.txt'])

    assert os.path.isfile(os.path.join(
        dufl_root, 'root',
        re.sub('^/', '', file_names['the/path/file.txt'])
    ))


def test_dufl_add_copies_file_in_home_to_dufl_home_subfolder(cli_run, temp_folder, user_home):
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init')

    file_names = create_files_in_folder(user_home, {
        'the/path/file.txt': 'hello'
    })

    cli_run('-r', dufl_root, 'add', file_names['the/path/file.txt'])

    assert os.path.isfile(os.path.join(
        dufl_root, 'home', 'the/path/file.txt'
    ))


def test_dufl_add_adds_and_commits_file_to_git(cli_run, temp_folder):
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init')

    file_names = create_files_in_folder(temp_folder, {
        'the/path/file.txt': 'hello'
    })

    cli_run('-r', dufl_root, 'add', file_names['the/path/file.txt'])

    git = utils.Git('/usr/bin/git', dufl_root)
    files = git.get_output('ls-files')
    assert 'the/path/file.txt' in files


def test_dufl_add_does_not_add_file_whose_name_matches_security_rule(cli_run, temp_folder):
    dufl_root = os.path.join(temp_folder, '.dufl')

    # Initialise repo, and create a settings.yaml with custon suspicious_name expressions
    cli_run('-r', dufl_root, 'init')
    create_files_in_folder(dufl_root, {
        'settings.yaml': yaml.dump({
            'suspicious_names': {
                'file\.[^.]+$': 'refused on suspicious name'
            },
            'suspicious_content': {}
        })
    })

    # Create the suspicious file and try to add it
    file_names = create_files_in_folder(temp_folder, {
        'path/to/file.txt': 'hello'
    })
    r = cli_run('-r', dufl_root, 'add', file_names['path/to/file.txt'])

    assert r.exit_code != 0
    assert 'refused on suspicious name' in r.output
    assert not os.path.isfile(os.path.join(
        dufl_root, 'root',
        re.sub('^/', '', file_names['path/to/file.txt'])
    ))

def test_dufl_add_does_not_add_file_whose_content_matches_security_rule(cli_run, temp_folder):
    dufl_root = os.path.join(temp_folder, '.dufl')

    # Initialize repo, and create a settings.yaml with custom suspicous_content expressions
    cli_run('-r', dufl_root, 'init')
    create_files_in_folder(dufl_root, {
        'settings.yaml': yaml.dump({
            'suspicious_content': {
                'PRIVATE KEY': 'refused on suspicious content'
            },
            'suspicious_name': {}
        })
    })

    # Create the suspicious file and try to add it
    file_names = create_files_in_folder(temp_folder, {
        'path/to/file.txt': "hello\n here is a PRIVATE KEY ;)\n!"
    })
    r = cli_run('-r', dufl_root, 'add', file_names['path/to/file.txt'])

    assert r.exit_code != 0
    assert 'refused on suspicious content' in r.output
    assert not os.path.isfile(os.path.join(
        dufl_root, 'root',
        re.sub('^/', '', file_names['path/to/file.txt']
    )))

def test_dufl_add_uses_provided_commit_message(cli_run, temp_folder):
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init')

    file_names = create_files_in_folder(temp_folder, {
        'the/path/file.txt': 'hello'
    })

    cli_run('-r', dufl_root, 'add', file_names['the/path/file.txt'],
            '-m', 'Good job!')

    git = utils.Git('/usr/bin/git', dufl_root)
    logs = git.get_output('log')
    assert 'Good job!' in logs


def test_dufl_push_pushes_to_git(cli_run, temp_folder, remote_git_path):
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init', remote_git_path)

    # Create and commit file
    file_names = create_files_in_folder(temp_folder, {
        'the/path/file.txt': 'hello'
    })
    cli_run('-r', dufl_root, 'add', file_names['the/path/file.txt'])

    # Push
    cli_run('-r', dufl_root, 'push')

    # Now pull that remote repo somewhere else, and check the file is there.
    repo_clone = os.path.join(temp_folder, 'clone')
    os.makedirs(repo_clone)
    git = utils.Git('/usr/bin/git', repo_clone)
    git.run('init')
    git.run('remote', 'add', 'origin', remote_git_path)
    git.run('pull', 'origin', 'master')

    assert os.path.isfile(os.path.join(
        repo_clone, 'root',
        re.sub('^/+', '', file_names['the/path/file.txt'])
    ))
