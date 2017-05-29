# -*- coding: utf-8 -*-

import os
import sys
import unittest

from PyQt4.QtCore import Qt, QModelIndex
from PyQt4.QtGui import QKeyEvent, QItemSelectionModel, QKeySequence
from qgis.core import QgsFeatureRequest, QgsGeometry
from qgis.utils import plugins

from scriptassistant.plugin import ScriptAssistant

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


class QGISTest(unittest.TestCase):
    """Test the Script Assistant plugin."""

    def setUp(self):
        """Runs before each test."""
        self.scriptassistant = plugins.get('scriptassistant')

    def test_plugin(self):
        self.assertIsInstance(self.scriptassistant, ScriptAssistant)


def run_tests():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(QGISTest, 'test'))
    unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
