from subprocess import check_call, check_output, CalledProcessError


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
        try:
            out = check_call([
                self.git,
                '-C', self.root
            ] + list(command))
            if out != 0:
                raise GitError()
        except CalledProcessError:
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
