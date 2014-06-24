from __future__ import unicode_literals

import unittest

import mock

from mopidy_alsamixer import Extension, mixer


class ExtensionTest(unittest.TestCase):

    def test_get_default_config(self):
        ext = Extension()

        config = ext.get_default_config()

        self.assertIn('[alsamixer]', config)
        self.assertIn('enabled = true', config)
        self.assertIn('card = 0', config)
        self.assertIn('control = Master', config)

    def test_get_config_schema(self):
        ext = Extension()

        schema = ext.get_config_schema()

        self.assertIn('card', schema)
        self.assertIn('control', schema)

    def test_setup(self):
        ext = Extension()
        registry = mock.Mock()

        ext.setup(registry)

        registry.add.assert_called_once_with('mixer', mixer.AlsaMixer)
