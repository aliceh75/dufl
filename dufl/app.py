import os
import re


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
