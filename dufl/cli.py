import click
import os
import shutil
import yaml

from .app import get_dufl_file_path
from .utils import dufl_debug, Git, GitError


@click.group('cli', invoke_without_command=True)
@click.pass_context
@click.version_option()
@click.option('-r', '--root', default=None, help='dufl root folder. Defaults to ~/.dufl - Note that if you don\'t use the default, you\'ll need to specify it for every command.')
@click.option('--debug/--no-debug', default=False, help='enable debug mode')
def cli(ctx, root, debug):
    """ General group containing all commands """
    if root is None:
        root = os.path.expanduser('~/.dufl')
    ctx.obj = {
        'dufl_root': root,
        'create_mode': 0766,
        'home_subdir': 'home',
        'slash_subdir': 'root',
        'settings_file': 'settings.yaml',
        'debug': debug,
        'debug_context': 0
    }
    settings_file = os.path.join(ctx.obj['dufl_root'], ctx.obj['settings_file'])
    if os.path.isfile(settings_file):
        try:
            with open(settings_file) as f:
                settings = dict(
                    settings.items() +
                    yaml.load(f.read()).items()
                )
        except Exception:
            click.echo("File %s appears to be corrupt. Delete or fix it, and try again." % settings_file)
            exit(1)
    dufl_debug('init', ctx)


@cli.command('init')
@click.pass_context
@click.argument('repository')
@click.option('--git', default='/usr/bin/git', help='git binary. This will be stored in the settings file.')
def init(ctx, repository, git):
    """ Initialize dufl for the current user """
    dufl_root = ctx.obj['dufl_root']
    if os.path.exists(dufl_root):
        click.echo('Folder %s already exists, cannot initialize.' % dufl_root)
        exit(1)

    try:
        click.echo('Creating %s...' % dufl_root)
        os.makedirs(dufl_root, ctx.obj['create_mode'])

        click.echo('Initializing git repository...')
        giti = Git(git, dufl_root)
        giti.run('init')
        giti.run('remote', 'add', 'origin', repository)

        click.echo('Looking for remote repository...')
        repo_exists = False
        try:
            giti.run('ls-remote', repository)
            repo_exists = True
        except GitError:
            pass

        if repo_exists:
            click.echo('Pull master branch of %s' % repository)
            giti.run('pull')
        else:
            click.echo('Creating new structure in %s' % dufl_root)
            os.makedirs(os.path.join(dufl_root, ctx.obj['home_subdir']), ctx.obj['create_mode'])
            os.makedirs(os.path.join(dufl_root, ctx.obj['slash_subdir']), ctx.obj['create_mode'])
            click.echo('Creating default settings file in %s' % dufl_root)
            with open(os.path.join(dufl_root, ctx.obj['settings_file']), 'w') as the_file:
                the_file.write(yaml.dump({
                    'git': git,
                }))
        click.echo('Done!')
    except Exception as e:
        click.echo(e)
        click.echo('Failed. To retry, you will need to clean up by deleting the folder %s' % dufl_root)
        exit(1)


@cli.command('add')
@click.pass_context
@click.argument('file_name')
@click.option('--message', '-m', default='Update.', help='Commit message')
def add(ctx, file_name, message):
    """ Add and commit a new file """
    dufl_root = ctx.obj['dufl_root']
    source = os.path.abspath(file_name)
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
    print 'hello'
    git.run('push')
