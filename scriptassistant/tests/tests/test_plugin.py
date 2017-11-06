# -*- coding: utf-8 -*-

"""Tests existance of the Script Assistant plugin. Created for the purpose of
testing Script Assistant plugin functionality.
"""

import os
import unittest

from qgis.utils import plugins

from scriptassistant.plugin import ScriptAssistant

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


class QGISTest(unittest.TestCase):
    """Test the Script Assistant plugin."""

    def setUp(self):
        """Runs before each test."""
        self.scriptassistant = plugins.get("scriptassistant")

    def test_plugin(self):
        self.assertIsInstance(self.scriptassistant, ScriptAssistant)
