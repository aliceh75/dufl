import click
import contextlib
import os
import re
import time
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


def test_dufl_checkout_checks_the_given_root_file_out_to_its_absolute_location(cli_run, temp_folder, remote_git_path):
    # Create a file in the remote repo that will check out in the temp folder.
    file_in_temp_folder = os.path.join(temp_folder, 'path/to/the_file.txt')
    add_content_to_remote_git_repo(remote_git_path, {
        'root': {
            file_in_temp_folder: 'hello'
        }
    })

    # Create the dufl folder
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init', remote_git_path)
    cli_run('-r', dufl_root, 'pull')

    # Checkout and test
    assert not os.path.isfile(file_in_temp_folder)
    cli_run('-r', dufl_root, 'checkout', file_in_temp_folder)

    assert os.path.isfile(file_in_temp_folder)
    with open(file_in_temp_folder, 'r') as f:
        content = f.read()
    assert content == 'hello'


def test_dufl_checkout_checks_the_given_user_file_out_in_the_home_folder(cli_run, user_home, remote_git_path):
    # Create a file in the remote repo that will check out in the home folder.
    file_in_home_folder = os.path.join(user_home, 'path/to/the_file.txt')
    add_content_to_remote_git_repo(remote_git_path, {
        'home/path/to/the_file.txt': 'hello'
    })

    # Create the dufl folder
    dufl_root = os.path.join(user_home, '.dufl')
    cli_run('-r', dufl_root, 'init', remote_git_path)

    # Checkout and test
    assert not os.path.isfile(file_in_home_folder)
    cli_run('-r', dufl_root, 'checkout', file_in_home_folder)

    assert os.path.isfile(file_in_home_folder)
    with open(file_in_home_folder, 'r') as f:
        content = f.read()
    assert content == 'hello'


def test_dufl_checkout_does_not_overwrite_what_looks_like_a_changed_file(cli_run, temp_folder, remote_git_path):
    file_in_temp_folder = os.path.join(temp_folder, 'path/to/the_fiel.txt')
    add_content_to_remote_git_repo(remote_git_path, {
        'root': {
            file_in_temp_folder: 'hello'
        }
    })

    # Timestamps have 1 sec granularity, so wait a bit!
    time.sleep(1)

    os.makedirs(os.path.dirname(file_in_temp_folder))
    with open(file_in_temp_folder, 'w') as f:
        f.write('changed after the file was comitted')

    # Create the dufl folder
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init', remote_git_path)

    # Checkout and test
    r = cli_run('-r', dufl_root, 'checkout', file_in_temp_folder)

    assert 'It looks like you have local modifications' in r.output
    with open(file_in_temp_folder, 'r') as f:
        content = f.read()
    assert content == 'changed after the file was comitted'


def test_dufl_checkout_does_not_overwrite_what_looks_like_a_changed_file_even_if_date_is_earlier_than_date_in_repository(cli_run, temp_folder, remote_git_path):
    file_in_temp_folder = os.path.join(temp_folder, 'path/to/the_fiel.txt')

    add_content_to_remote_git_repo(remote_git_path, {
        'root': {
            file_in_temp_folder: 'the file, as it originally was'
        }
    })

    # Timestamps have 1 sec granularity, so wait a bit!
    time.sleep(1)

    os.makedirs(os.path.dirname(file_in_temp_folder))
    with open(file_in_temp_folder, 'w') as f:
        f.write('the file with some local changes')

    # Timestamps have 1 sec granularity, so wait a bit!
    time.sleep(1)

    add_content_to_remote_git_repo(remote_git_path, {
        'root': {
            file_in_temp_folder: 'a different upstream update'
        }
    })

    # Create the dufl folder
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init', remote_git_path)

    # Checkout and test
    r = cli_run('-r', dufl_root, 'checkout', file_in_temp_folder)

    assert 'It looks like you have local modifications' in r.output
    with open(file_in_temp_folder, 'r') as f:
        content = f.read()
    assert content == 'the file with some local changes'


# TODO: We should have an analogous test where the repo itself didn't exist at the file's creation date
# (here is exists because remote_git_path fixture creates it for us)
def test_dufl_checkout_does_not_overwrite_what_looks_like_a_changed_file_even_if_date_is_earlier_than_creation_date_in_repository(cli_run, temp_folder, remote_git_path):
    file_in_temp_folder = os.path.join(temp_folder, 'path/to/the_fiel.txt')

    os.makedirs(os.path.dirname(file_in_temp_folder))
    with open(file_in_temp_folder, 'w') as f:
        f.write('the local file, predating the repo one')

    # Timestamps have 1 sec granularity, so wait a bit!
    time.sleep(1)

    add_content_to_remote_git_repo(remote_git_path, {
        'root': {
            file_in_temp_folder: 'the repo file, not the same as the local one'
        }
    })

    # Create the dufl folder
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init', remote_git_path)

    # Checkout and test
    r = cli_run('-r', dufl_root, 'checkout', file_in_temp_folder)

    assert 'It looks like you have local modifications' in r.output
    with open(file_in_temp_folder, 'r') as f:
        content = f.read()
    assert content == 'the local file, predating the repo one'


def test_dufl_checkout_overwrites_files_that_do_not_appear_to_have_been_changed(cli_run, temp_folder, remote_git_path):
    file_in_temp_folder = os.path.join(temp_folder, 'path/to/the_fiel.txt')
    add_content_to_remote_git_repo(remote_git_path, {
        'root': {
            file_in_temp_folder: 'the file as it was in the repo'
        }
    })

    # Timestamps have 1 sec granularity, so wait a bit!
    time.sleep(1)

    os.makedirs(os.path.dirname(file_in_temp_folder))
    with open(file_in_temp_folder, 'w') as f:
        f.write('the file as it was in the repo')

    # Timestamps have 1 sec granularity, so wait a bit!
    time.sleep(1)

    add_content_to_remote_git_repo(remote_git_path, {
        'root': {
            file_in_temp_folder: 'updated repo version'
        }
    })

    # Create the dufl folder.
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init', remote_git_path)

    # Checkout and test
    cli_run('-r', dufl_root, 'checkout', file_in_temp_folder)

    with open(file_in_temp_folder, 'r') as f:
        content = f.read()
    assert content == 'updated repo version'


def test_dufl_checkout_does_not_rely_on_reflog(cli_run, temp_folder, remote_git_path):
    """ Dufl checkout inspects the content of a file at a given date.
        One way to do this is to use the reflog with the
        git show branch@{date} syntax. However this is not good as the
        reflog does not contain all the commits. This test is there to ensure
        we don't switch to using reflog in the future!
    """
    file_in_temp_folder = os.path.join(temp_folder, 'path/to/the_fiel.txt')
    add_content_to_remote_git_repo(remote_git_path, {
        'root': {
            file_in_temp_folder: 'the file as it was in the repo'
        }
    })

    # Timestamps have 1 sec granularity, so wait a bit!
    time.sleep(1)

    os.makedirs(os.path.dirname(file_in_temp_folder))
    with open(file_in_temp_folder, 'w') as f:
        f.write('the file as it was in the repo')

    # Timestamps have 1 sec granularity, so wait a bit!
    time.sleep(1)

    add_content_to_remote_git_repo(remote_git_path, {
        'root': {
            file_in_temp_folder: 'updated repo version'
        }
    })

    # Create the dufl folder. As we are creating the repo
    # after the original commits, they will not show in
    # the reflog - so the checkout would fail if we used
    # the reflog
    dufl_root = os.path.join(temp_folder, '.dufl')
    cli_run('-r', dufl_root, 'init', remote_git_path)

    # Checkout and test
    cli_run('-r', dufl_root, 'checkout', file_in_temp_folder)

    with open(file_in_temp_folder, 'r') as f:
        content = f.read()
    assert content == 'updated repo version'
