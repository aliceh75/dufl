import click
import os
import re
import shutil
import yaml

from datetime import datetime

from . import defaults
from .app import get_dufl_file_path, create_initial_context
from .app import SettingsBroken
from .utils import Git, GitError


@click.group('cli', invoke_without_command=True)
@click.pass_context
@click.version_option()
@click.option('-r', '--root', default=None, help='dufl root folder. Defaults to ~/.dufl - Note that if you don\'t use the default, you\'ll need to specify it for every command.')
def cli(ctx, root):
    """ General group containing all commands """
    try:
        ctx.obj = create_initial_context(root)
    except SettingsBroken as e:
        click.echo(
            'Failed to read the settings file: %s' % str(e),
            err=True
        )
        exit(1)


@cli.command('init')
@click.pass_context
@click.argument('repository', default='')
@click.option('--git', default='/usr/bin/git', help='git binary. This will be stored in the settings file.')
def init(ctx, repository, git):
    """ Initialize the dufl root folder (must not exist) - by default ~/.dufl """
    dufl_root = ctx.obj['dufl_root']
    if os.path.exists(dufl_root):
        click.echo(
            'Folder %s already exists, cannot initialize.' % dufl_root,
            err=True
        )
        exit(1)

    try:
        click.echo('Creating %s...' % dufl_root)
        os.makedirs(dufl_root, ctx.obj['create_mode'])

        click.echo('Initializing git repository...')
        giti = Git(git, dufl_root)
        giti.run('init')
        if repository != '':
            giti.run('remote', 'add', 'origin', repository)

            click.echo('Looking for remote repository...')
            repo_exists = False
            try:
                giti.run('ls-remote', repository)
                repo_exists = True
            except GitError:
                pass

            if repo_exists:
                click.echo('Pulling master branch of %s' % repository)
                giti.run('pull', 'origin', 'master')
        else:
            click.echo('No remote specified. You will need to add it manually when you have one.')

        if not os.path.exists(os.path.join(dufl_root, ctx.obj['home_subdir'])):
            click.echo('Creating home subfolder in %s' % dufl_root)
            os.makedirs(os.path.join(dufl_root, ctx.obj['home_subdir']), ctx.obj['create_mode'])
        if not os.path.exists(os.path.join(dufl_root, ctx.obj['slash_subdir'])):
            click.echo('Creating absolute subfolder in %s' % dufl_root)
            os.makedirs(os.path.join(dufl_root, ctx.obj['slash_subdir']), ctx.obj['create_mode'])

        if not os.path.exists(os.path.join(dufl_root, ctx.obj['settings_file'])):
            click.echo('Creating default settings file in %s' % dufl_root)
            with open(os.path.join(dufl_root, ctx.obj['settings_file']), 'w') as the_file:
                the_file.write(yaml.dump(dict(
                    defaults.settings.items() + {
                        'git': git
                    }.items()
                )))
            giti.run('add', os.path.join(dufl_root, ctx.obj['settings_file']))
            giti.run('commit', '-m', 'Initial settings file.')

        click.echo('Done!')
    except Exception as e:
        click.echo(e, err=True)
        click.echo(
            'Failed. To retry, you will need to clean up by deleting the folder %s' % dufl_root,
            err=True
        )
        exit(1)


@cli.command('add')
@click.pass_context
@click.argument('file_name')
@click.option('--message', '-m', default='Update.', help='Commit message')
def add(ctx, file_name, message):
    """ Add and commit a new file """
    dufl_root = ctx.obj['dufl_root']
    source = os.path.abspath(file_name)
    # Security checks!
    for expr, msg in ctx.obj['suspicious_names'].items():
        if re.search(expr, source):
            click.echo('Error! This file won\'t be added because %s' % msg, err=True)
            exit(1)
    if len(ctx.obj['suspicious_content']) > 0:
        with open(source) as f:
            data = f.read()
            for expr, msg in ctx.obj['suspicious_content'].items():
                if re.search(expr, data):
                    click.echo(
                        'Error! This file won\'t be added because %s' % msg,
                        err=True
                    )
                    exit(1)
    # Go ahead
    dest = get_dufl_file_path(source, ctx.obj)
    if not os.path.isdir(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))
    shutil.copyfile(source, dest)
    git = Git(ctx.obj.get('git', '/usr/bin/git'), dufl_root)
    git.run('add', dest)
    git.run('commit', '-m', message)


@cli.command('push')
@click.pass_context
def push(ctx):
    """ Push the git repo """
    dufl_root = ctx.obj['dufl_root']
    git = Git(ctx.obj.get('git', '/usr/bin/git'), dufl_root)
    git.run('push', 'origin', git.working_branch())


@cli.command('checkout')
@click.argument('file_name')
@click.pass_context
def checkout(ctx, file_name):
    """ Copy the given file from the repository to the local file system.

    This will attempt to identify local changes, but it's not foolproof,
    so make sure you know what you are doing.
    """
    dufl_root = ctx.obj['dufl_root']

    checked_out_file = os.path.abspath(file_name)
    dufl_file = get_dufl_file_path(checked_out_file, ctx.obj)

    if not os.path.exists(dufl_file):
        click.echo('The file you want to checkout does not exist. Maybe run dufl fetch first?', err=True)
        exit(1)

    if os.path.exists(checked_out_file):
        # Try our best to see if it's been modified
        git = Git(ctx.obj.get('git', '/usr/bin/git'), dufl_root)
        last_modified_ts = os.path.getmtime(checked_out_file)
        last_modified = datetime.fromtimestamp(
            last_modified_ts
        ).strftime('%Y-%m-%d %H:%M:%S')
        commit_at_date = re.sub('[^a-zA-Z0-9]', '', git.get_output(
            'rev-list', '-1',
            '--before=%s' % last_modified,
            git.working_branch()
        ))
        file_exists_at_commit = False
        if len(commit_at_date) > 0:
            file_exists_at_commit = git.test(
                'rev-parse', '--verify',
                '%s:%s' % (
                    commit_at_date,
                    os.path.relpath(dufl_file, dufl_root)
                )
            )
        # If there is no commit at date, or the file didnt' exist at the commit,
        # assume first version of the file ever.
        if not file_exists_at_commit:
            commit_at_date = re.sub('[^a-zA-Z0-9]', '', git.get_output(
                'log', '--diff-filter=A', '--pretty=format:\'%H\'',
                '--', os.path.relpath(dufl_file, dufl_root)
            ))
            if len(commit_at_date) == 0:
                click.echo('File %s exists, but does not seem to be in the git repository?' % dufl_file, err=True)
                exit(1)

        # Note: do not be tempted to use 'git show branch@{date}' syntax,
        # as that relies on the reflog which does not contain all commits.
        content_at_date = git.get_output(
            'show',
            '%s:%s' % (
                commit_at_date,
                os.path.relpath(dufl_file, dufl_root)
            )
        )
        with open(checked_out_file, 'r') as f:
            content_now = f.read()
        if content_at_date != content_now:
            click.echo('It looks like you have local modifications. Will exit for now.', err=True)
            exit(1)

    click.echo('Copying %s to %s...' % (dufl_file, checked_out_file))
    if not os.path.exists(os.path.dirname(checked_out_file)):
        os.makedirs(os.path.dirname(checked_out_file))
    shutil.copy(dufl_file, checked_out_file)
