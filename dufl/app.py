import os
import re
import yaml

from yaml.scanner import ScannerError


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
    home = re.sub('/$', '', home)
    if file_path.startswith(home + '/'):
        return os.path.join(
            settings['dufl_root'],
            re.sub('^/', '', settings['home_subdir']),
            re.sub('^/', '', file_path[len(home):])
        )
    else:
        return os.path.join(
            settings['dufl_root'],
            re.sub('^/', '', settings['slash_subdir']),
            re.sub('^/', '', file_path)
        )


class SettingsBroken(Exception):
    """ Exception raised when the settings file can't be parsed"""
    pass


def create_initial_context(root):
    """ Create the context object used throughout the application

    Defaults are defined here, and the settings file in the
    given root is included here too.

    Args:
        root (str): Dufl root folder. If None, will default
            to ~/.dufl
    Returns:
        dict: The context
    Raises:
        SettingsBroken: When the settings file can't be opened
            or parsed.
    """
    if root is None:
        root = os.path.expanduser('~/.dufl')
    root = os.path.abspath(root)
    context = {
        'git': '/usr/bin/git',
        'dufl_root': root,
        'create_mode': 0766,
        'home_subdir': 'home',
        'slash_subdir': 'root',
        'settings_file': 'settings.yaml'
    }
    settings_file = os.path.join(
        context['dufl_root'], context['settings_file']
    )
    if os.path.isfile(settings_file):
        try:
            with open(settings_file) as f:
                settings = yaml.load(f.read())
        except IOError:
            raise SettingsBroken('Could not open settings file.')
        except ScannerError:
            raise SettingsBroken('Could not parse settings file.')
        allowed_settings = ['git']
        for setting_key in settings:
            if setting_key in allowed_settings:
                context[setting_key] = settings[setting_key]
    return context
