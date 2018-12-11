import pytest

from nycdbuddy import cli


def test_help_exits_without_error():
    with pytest.raises(SystemExit) as excinfo:
        cli.main(argv=['--help'])
    assert excinfo.value.code is None


def test_unrecognized_options_exit_with_error():
    with pytest.raises(SystemExit) as excinfo:
        cli.main(argv=['boogywoogy'])
    assert excinfo.value.code is not None
