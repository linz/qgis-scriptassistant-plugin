# -*- coding: utf-8 -*-

import os
import sys
import time
import unittest

from qgis.gui import QgsMessageBar
from qgis.utils import plugins, iface

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

view_tests_during_execution = False


class ScriptAssistantTest(unittest.TestCase):
    """Test the Script Assistant plugin."""

    @classmethod
    def setUpClass(cls):
        """Runs at TestCase init."""
        cls.scriptassistant = plugins.get("scriptassistant")

    # @classmethod
    # def tearDownClass(cls):
    #     """Runs at TestCase teardown."""
    #     cls.road_plugin.dockwidget.close()

    def setUp(self):
        """Runs before each test."""
        pass

    def view(self, qt_object):
        if view_tests_during_execution:
            qt_object.repaint()
            time.sleep(1)
        else:
            pass

    def test_settings(self):
        settings_dialog = self.scriptassistant.dlg_settings
        settings_dialog.show()
        self.view(settings_dialog)
        self.assertFalse(settings_dialog.btn_delete.isEnabled())
        settings_dialog.lne_script.setText(os.path.join(__location__, "testdata"))
        self.view(settings_dialog)
        settings_dialog.lne_test_data.setText(os.path.join(__location__, "testdata"))
        self.view(settings_dialog)
        self.assertTrue(settings_dialog.btn_save.isEnabled())
        settings_dialog.cmb_config.lineEdit().setText("Script Assistant")
        self.view(settings_dialog)
        settings_dialog.btn_save.clicked.emit(True)
        self.view(settings_dialog)
        settings_dialog.close()
        settings_dialog.show()
        self.view(settings_dialog)
        self.assertEquals(settings_dialog.cmb_config.lineEdit().text(), "Script Assistant")
        self.view(settings_dialog)
        settings_dialog.btn_delete.clicked.emit(True)
        self.view(settings_dialog)
        self.assertEquals(settings_dialog.cmb_config.lineEdit().text(), "")

    # def test_add_test_data(self):
    #     settings_dialog = self.scriptassistant.dlg_settings
    #     settings_dialog.lne_test.setText(os.path.join(__location__, 'testdata'))
    #     self.view(settings_dialog)
    #     self.scriptassistant.prepareTest('$ALL')
    #     self.view(settings_dialog)

    def tearDown(self):
        settings_dialog = self.scriptassistant.dlg_settings
        while settings_dialog.btn_delete.isEnabled():
            settings_dialog.btn_delete.clicked.emit(True)
        settings_dialog.lne_script.setText("")
        settings_dialog.lne_test.setText(__location__)
        settings_dialog.lne_test_data.setText("")
        self.view(settings_dialog)
        settings_dialog.close()


def run_tests(view_tests=False):
    global view_tests_during_execution
    if view_tests:
        view_tests_during_execution = True
    else:
        view_tests_during_execution = False
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(ScriptAssistantTest, "test"))
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
