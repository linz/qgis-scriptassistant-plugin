# -*- coding: utf-8 -*-

"""Tests existance of the Script Assistant plugin. Created for the purpose of
testing Script Assistant plugin functionality.
"""

import os
import sys
import time
import unittest

from qgis.gui import QgsMessageBar
from qgis.utils import plugins, iface

from scriptassistant.plugin import ScriptAssistant

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

view_tests_during_execution = False


class QGISTest(unittest.TestCase):
    """Test the Script Assistant plugin."""

    def setUp(self):
        """Runs before each test."""
        self.scriptassistant = plugins.get("scriptassistant")

    def view(self, qt_object):
        if view_tests_during_execution:
            qt_object.repaint()
            time.sleep(1)
        else:
            pass

    def test_plugin(self):
        self.assertIsInstance(self.scriptassistant, ScriptAssistant)


def run_tests(view_tests=False):
    global view_tests_during_execution
    if view_tests:
        view_tests_during_execution = True
    else:
        view_tests_during_execution = False
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(QGISTest, "test"))
    result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
    if result.wasSuccessful():
        iface.messageBar().pushMessage(
            "All Tests Passed",
            "Testing was successful.",
            level=QgsMessageBar.SUCCESS,
        )
    else:
        iface.messageBar().pushMessage(
            "Test Failure",
            "Testing was not successful.",
            level=QgsMessageBar.CRITICAL,
        )
