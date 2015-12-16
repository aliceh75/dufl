import click
import os
import re
import yaml

from subprocess import check_call


def dufl_debug(message, ctx):
    """ Output a debug message, along with an internal context dump """
    if ctx.obj['debug']:
        click.echo(message)
        click.echo('context[%s]' % ctx.obj['debug_context'])
        click.echo(yaml.dump(ctx.obj))
        click.echo('end[%s]' % ctx.obj['debug_context'])
        ctx.obj['debug_context'] = ctx.obj['debug_context'] + 1


def canonize_path(file_path):
    """ Canonize a path

    Return an absolute path if the path is not under
    the current user's home directory, and a path that
    starts with ~/ if the file is under the current
    user's home directory.

    Args:
        file_path (str): Path to cannonize

    Returns:
        str: The cannonized path
    """
    canon = os.path.abspath(file_path)
    home = os.path.expanduser('~')
    home = re.sub('\\/$', '', home) + '/'
    canon = re.sub('^' + re.escape(home), '~/', canon)
    return canon


class GitError(Exception):
    """ Exception raised on git failures """
    pass


class Git(object):
    """ Class used to run git commands

    Args:
        git (str): Path to git executable
        root (str): Git root folder to work from
    """
    def __init__(self, git, root):
        self.git = git
        self.root = root

    def run(self, *command):
        """ Run a git command

        Args:
            *command (array of str): List of parameters to pass to git
                executable.
        Raises:
            GitError
        """
        out = check_call([
            self.git, 
            '-C', self.root
        ] + list(command))
        if out != 0:
            raise GitError()
