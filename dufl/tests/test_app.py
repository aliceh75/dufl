import os
import yaml

from click.testing import CliRunner
from tutils import patch_app
from .. import defaults
from ..app import get_dufl_file_path, create_initial_context


def test_get_dufl_file_path_returns_path_within_dufl_root():
    with patch_app('os.path.expanduser') as expanduser:
        expanduser.return_value = '/home/someone'
        out = get_dufl_file_path('/some/where', {
            'dufl_root': '/my/dufl',
            'slash_subdir': 'root',
            'home_subdir': 'home'
        })
        assert out.startswith('/my/dufl/')


def test_get_dufl_file_path_returns_abs_path_within_dufl_slash_folder():
    with patch_app('os.path.expanduser') as expanduser:
        expanduser.return_value = '/home/someone'
        out = get_dufl_file_path('/some/where', {
            'dufl_root': '/my/dufl',
            'slash_subdir': 'root',
            'home_subdir': 'home'
        })
        assert out.startswith('/my/dufl/root/')


def test_get_dufl_file_path_returns_home_path_within_dufl_home_folder():
    with patch_app('os.path.expanduser') as expanduser:
        expanduser.return_value = '/home/someone'
        out = get_dufl_file_path('/home/someone/some/where', {
            'dufl_root': '/my/dufl',
            'slash_subdir': 'root',
            'home_subdir': 'home'
        })
        assert out.startswith('/my/dufl/home/')


def test_get_dufl_file_path_strips_home_folder_from_path():
    with patch_app('os.path.expanduser') as expanduser:
        expanduser.return_value = '/home/someone'
        out = get_dufl_file_path('/home/someone/some/where', {
            'dufl_root': '/my/dufl',
            'slash_subdir': 'root',
            'home_subdir': 'home'
        })
        assert out == '/my/dufl/home/some/where'


def test_get_dufl_file_path_adds_correct_abs_file_name():
    with patch_app('os.path.expanduser') as expanduser:
        expanduser.return_value = '/home/someone'
        out = get_dufl_file_path('/some/where', {
            'dufl_root': '/my/dufl',
            'slash_subdir': 'root',
            'home_subdir': 'home'
        })
        assert out == '/my/dufl/root/some/where'


def test_get_dufl_file_path_resolves_relative_paths():
    with patch_app('os.path.expanduser') as expanduser:
        expanduser.return_value = '/home/someone'
        out = get_dufl_file_path('/some/world/../where', {
            'dufl_root': '/my/dufl',
            'slash_subdir': 'root',
            'home_subdir': 'home'
        })
        assert out == '/my/dufl/root/some/where'


def test_create_initial_context_creates_expected_settings():
    with patch_app('os.path.isfile', 'os.path.expanduser') as (isfile, expanduser):
        isfile.return_value = False
        expanduser.return_value = '/some/where'
        context = create_initial_context(None)
        assert set(defaults.settings.keys() + [
            'dufl_root', 'create_mode', 'home_subdir', 
            'slash_subdir', 'settings_file']) == set(context.keys())


def test_create_initial_context_sets_default_root_in_homedir():
    with patch_app('os.path.isfile', 'os.path.expanduser') as (isfile, expanduser):
        isfile.return_value = False
        expanduser.return_value = '/some/where'
        context = create_initial_context(None)
        assert context['dufl_root'] == '/some/where'
        expanduser.assert_called_with('~/.dufl')


def test_create_initial_context_uses_provided_root():
    with patch_app('os.path.isfile') as isfile:
        isfile.return_value = False
        context = create_initial_context('/some/where/else')
        assert context['dufl_root'] == '/some/where/else'


def test_create_initial_context_expands_provided_root():
    with patch_app('os.path.isfile') as isfile:
        isfile.return_value = False
        context = create_initial_context('/some/where/../else')
        assert context['dufl_root'] == '/some/else'


def test_create_initial_context_merges_allowed_keys_from_settings_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        with open(os.path.join(here, 'settings.yaml'), 'w') as f:
            f.write(yaml.dump(dict(
                [(k, ':-)') for k in defaults.settings]
            )))
        context = create_initial_context(here)
        for key in defaults.settings:
            assert context[key] == ':-)'


def test_create_initial_context_does_not_merge_unknown_keys_from_settings_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        here = os.getcwd()
        with open(os.path.join(here, 'settings.yaml'), 'w') as f:
            f.write(yaml.dump(dict(
                defaults.settings.items() + {
                'dufl_root': '$$$',
                'create_mode': '$$$',
                'home_subdir': '$$$',
                'slash_subdir': '$$$',
                'settings_file': '$$$',
                'other_stuff': '$$$'
            }.items())))
        context = create_initial_context(here)
        assert 'other_stuff' not in context.keys()
        assert '$$$' not in [v for (k,v) in context.items()]
