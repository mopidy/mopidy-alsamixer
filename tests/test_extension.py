from unittest import mock

from mopidy_alsamixer import Extension, mixer


def test_get_default_config():
    ext = Extension()

    config = ext.get_default_config()

    self.assertIn("[alsamixer]", config)
    self.assertIn("enabled = true", config)
    self.assertIn("device = default", config)
    self.assertIn("card =", config)
    self.assertIn("control = Master", config)

    schema = ext.get_config_schema()

    self.assertIn("device", schema)
    self.assertIn("card", schema)
    self.assertIn("control", schema)


def test_setup():
    ext = Extension()
    registry = mock.Mock()

    ext.setup(registry)

    registry.add.assert_called_once_with("mixer", mixer.AlsaMixer)
