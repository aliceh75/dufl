from contextlib import contextmanager
from mock import patch

from .. import app
from ..app import get_dufl_file_path


@contextmanager
def _patch_app(name):
    """ Helper context manager to patch methods in the app library """
    with patch(app.__name__ + '.' + name) as p:
        yield p


def test_get_dufl_file_path_returns_path_within_dufl_root():
    with _patch_app('os.path.expanduser') as expanduser:
        expanduser.return_value = '/home/someone'
        out = get_dufl_file_path('/some/where', {
            'dufl_root': '/my/dufl',
            'slash_subdir': 'root',
            'home_subdir': 'home'
        })
        assert out.startswith('/my/dufl/')


def test_get_dufl_file_path_returns_abs_path_within_dufl_slash_folder():
    with _patch_app('os.path.expanduser') as expanduser:
        expanduser.return_value = '/home/someone'
        out = get_dufl_file_path('/some/where', {
            'dufl_root': '/my/dufl',
            'slash_subdir': 'root',
            'home_subdir': 'home'
        })
        assert out.startswith('/my/dufl/root/')


def test_get_dufl_file_path_returns_home_path_within_dufl_home_folder():
    with _patch_app('os.path.expanduser') as expanduser:
        expanduser.return_value = '/home/someone'
        out = get_dufl_file_path('/home/someone/some/where', {
            'dufl_root': '/my/dufl',
            'slash_subdir': 'root',
            'home_subdir': 'home'
        })
        assert out.startswith('/my/dufl/home/')


def test_get_dufl_file_path_strips_home_folder_from_path():
    with _patch_app('os.path.expanduser') as expanduser:
        expanduser.return_value = '/home/someone'
        out = get_dufl_file_path('/home/someone/some/where', {
            'dufl_root': '/my/dufl',
            'slash_subdir': 'root',
            'home_subdir': 'home'
        })
        assert out == '/my/dufl/home/some/where'


def test_get_dufl_file_path_adds_correct_abs_file_name():
    with _patch_app('os.path.expanduser') as expanduser:
        expanduser.return_value = '/home/someone'
        out = get_dufl_file_path('/some/where', {
            'dufl_root': '/my/dufl',
            'slash_subdir': 'root',
            'home_subdir': 'home'
        })
        assert out == '/my/dufl/root/some/where'


def test_get_dufl_file_path_resolves_relative_paths():
    with _patch_app('os.path.expanduser') as expanduser:
        expanduser.return_value = '/home/someone'
        out = get_dufl_file_path('/some/world/../where', {
            'dufl_root': '/my/dufl',
            'slash_subdir': 'root',
            'home_subdir': 'home'
        })
        assert out == '/my/dufl/root/some/where'
