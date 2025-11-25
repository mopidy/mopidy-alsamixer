from unittest import mock

from mopidy_alsamixer import Extension, mixer


def test_get_default_config():
    ext = Extension()

    config = ext.get_default_config()

    assert "[alsamixer]" in config
    assert "enabled = true" in config
    assert "device = default" in config
    assert "card =" in config
    assert "control = Master" in config

    schema = ext.get_config_schema()

    assert "device" in schema
    assert "card" in schema
    assert "control" in schema


def test_setup():
    ext = Extension()
    registry = mock.Mock()

    ext.setup(registry)

    registry.add.assert_called_once_with("mixer", mixer.AlsaMixer)
