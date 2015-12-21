import click
import os
import re
import yaml

from subprocess import check_call, check_output, CalledProcessError


def dufl_debug(message, ctx):
    """ Output a debug message, along with an internal context dump """
    if ctx.obj['debug']:
        click.echo(message)
        click.echo('context[%s]' % ctx.obj['debug_context'])
        click.echo(yaml.dump(ctx.obj))
        click.echo('end[%s]' % ctx.obj['debug_context'])
        ctx.obj['debug_context'] = ctx.obj['debug_context'] + 1


def get_dufl_file_path(file_path, settings):
    """ Return the matching path of a file within the dufl folder

    Given a file path on the file system, return the corresponsing
    path in the dufl folder.

    Args:
        file_path (str): File system path
        settings (dict): Settings dictionary. Expected keys
            are dufl_root, home_subdir and slash_subdir.

    Returns:
        str: dufl path
    """
    file_path = os.path.abspath(file_path)
    home = os.path.expanduser('~')
    home = re.sub('\\/$', '', home)
    if file_path.startswith(home + '/'):
        return os.path.join(
            settings['dufl_root'],
            re.sub('^\\/', '', settings['home_subdir']),
            re.sub('^\\/', '', file_path[len(home):])
        )
    else:
        return os.path.join(
            settings['dufl_root'],
            re.sub('^\\/', '', settings['slash_subdir']),
            re.sub('^\\/', '', file_path)
        )


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
        """ Run a git command transparently

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

    def get_output(self, *command):
        """ Run a git command and return output

        Args:
            *command (array of str): List of parameters to pass to git
                executable.
        Returns:
            str: The output of the git command
        Raises:
            GitError
        """
        try:
            out = check_output([
                self.git,
                '-C', self.root
            ] + list(command))
        except CalledProcessError:
            raise GitError()
        return out
