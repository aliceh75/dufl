import os
import yaml

from click.testing import CliRunner
from tutils import user_home, temp_folder
from .. import defaults
from ..app import get_dufl_file_path, create_initial_context


def test_get_dufl_file_path_returns_path_within_dufl_root(user_home):
    out = get_dufl_file_path('/some/where', {
        'dufl_root': '/my/dufl',
        'slash_subdir': 'root',
        'home_subdir': 'home'
    })
    assert out.startswith('/my/dufl/')


def test_get_dufl_file_path_returns_abs_path_within_dufl_slash_folder(user_home):
    out = get_dufl_file_path('/some/where', {
        'dufl_root': '/my/dufl',
        'slash_subdir': 'root',
        'home_subdir': 'home'
    })
    assert out.startswith('/my/dufl/root/')


def test_get_dufl_file_path_returns_home_path_within_dufl_home_folder(user_home):
    file_in_home = os.path.join(user_home, 'some/where')
    out = get_dufl_file_path(file_in_home, {
        'dufl_root': '/my/dufl',
        'slash_subdir': 'root',
        'home_subdir': 'home'
    })
    assert out.startswith('/my/dufl/home/')


def test_get_dufl_file_path_strips_home_folder_from_path(user_home):
    file_in_home = os.path.join(user_home, 'some/where')
    out = get_dufl_file_path(file_in_home, {
        'dufl_root': '/my/dufl',
        'slash_subdir': 'root',
        'home_subdir': 'home'
    })
    assert out == '/my/dufl/home/some/where'


def test_get_dufl_file_path_adds_correct_abs_file_name(user_home):
    out = get_dufl_file_path('/some/where', {
        'dufl_root': '/my/dufl',
        'slash_subdir': 'root',
        'home_subdir': 'home'
    })
    assert out == '/my/dufl/root/some/where'


def test_get_dufl_file_path_resolves_relative_paths(user_home):
    out = get_dufl_file_path('/some/world/../where', {
        'dufl_root': '/my/dufl',
        'slash_subdir': 'root',
        'home_subdir': 'home'
    })
    assert out == '/my/dufl/root/some/where'


def test_create_initial_context_creates_expected_settings(user_home):
    context = create_initial_context(None)
    assert set(defaults.settings.keys() + [
        'dufl_root', 'create_mode', 'home_subdir', 
        'slash_subdir', 'settings_file']) == set(context.keys())


def test_create_initial_context_sets_default_root_in_homedir(user_home):
    context = create_initial_context(None)
    assert context['dufl_root'] == os.path.join(user_home, '.dufl')


def test_create_initial_context_uses_provided_root(user_home, temp_folder):
    context = create_initial_context(temp_folder)
    assert context['dufl_root'] == temp_folder


def test_create_initial_context_expands_provided_root(user_home, temp_folder):
    context = create_initial_context(temp_folder + '/down/..')
    assert context['dufl_root'] == temp_folder


def test_create_initial_context_merges_allowed_keys_from_settings_file(user_home):
    os.makedirs(os.path.join(user_home, '.dufl'))
    with open(os.path.join(user_home, '.dufl/settings.yaml'), 'w') as f:
        f.write(yaml.dump(dict(
            [(k, ':-)') for k in defaults.settings]
        )))
    context = create_initial_context(None)
    for key in defaults.settings:
        assert context[key] == ':-)'


def test_create_initial_context_does_not_merge_unknown_keys_from_settings_file(user_home):
    os.makedirs(os.path.join(user_home, '.dufl'))
    with open(os.path.join(user_home, '.dufl/settings.yaml'), 'w') as f:
        f.write(yaml.dump(dict(
            defaults.settings.items() + {
            'dufl_root': '$$$',
            'create_mode': '$$$',
            'home_subdir': '$$$',
            'slash_subdir': '$$$',
            'settings_file': '$$$',
            'other_stuff': '$$$'
        }.items())))
    context = create_initial_context(None)
    assert 'other_stuff' not in context.keys()
    assert '$$$' not in [v for (k,v) in context.items()]
