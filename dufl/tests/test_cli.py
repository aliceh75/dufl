import click
import re
import yaml

from click.testing import CliRunner
from mock import patch

from .. import cli

class NoInternalContext(Exception):
    pass


def _get_internal_context(out, n):
    """ Return the nth internal context dump of a command invoked with --debug """
    matches = re.search(
        '^context\\[%s\\](.+)^end\\[%s\\]' % (n, n), 
        out, 
        re.MULTILINE|re.DOTALL
    )
    try:
        return yaml.load(matches.group(1).strip())
    except AttributeError:
        raise NoInternalContext()


def test_debug_output_can_be_parsed():
    runner = CliRunner()
    r = runner.invoke(
        cli.cli, ['--debug']
    )
    ctx_obj = _get_internal_context(r.output, 0)
    assert True


def test_debug_output_is_not_empty():
    runner = CliRunner()
    r = runner.invoke(
        cli.cli, ['--debug']
    )
    ctx_obj = _get_internal_context(r.output, 0)
    assert len(ctx_obj.keys()) > 0


def test_debug_mode_set_on_context():
    runner = CliRunner()
    r = runner.invoke(
        cli.cli, ['--debug']
    )
    ctx_obj = _get_internal_context(r.output, 0)
    assert ctx_obj['debug'] is True


def test_provided_dufl_root_added_to_context():
    runner = CliRunner()
    r = runner.invoke(
        cli.cli, ['-r', '/some/where', '--debug']
    )
    ctx_obj = _get_internal_context(r.output, 0)
    assert ctx_obj['dufl_root'] == '/some/where'


def test_default_dufl_root_is_in_current_user_home_dir():
    runner = CliRunner()
    with patch(cli.__name__ + '.os.path.expanduser') as e:
        e.return_value = 'expanded-path'
        r = runner.invoke(
            cli.cli, ['--debug']
        )
        assert e.call_args[0][0] == '~/.dufl'

    ctx_obj = _get_internal_context(r.output, 0)
    assert ctx_obj['dufl_root'] == 'expanded-path'


def test_default_dufl_root_is_expanded():
    runner = CliRunner()
    with patch(cli.__name__ + '.os.path.expanduser') as e:
        e.return_value = 'expanded-path'
        r = runner.invoke(
            cli.cli, ['--debug']
        )

    ctx_obj = _get_internal_context(r.output, 0)
    assert ctx_obj['dufl_root'] == 'expanded-path'

