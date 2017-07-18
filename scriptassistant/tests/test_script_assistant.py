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


class ScriptAssistantSettingsTest(unittest.TestCase):
    """Test the Script Assistant plugin."""

    @classmethod
    def setUpClass(cls):
        """Runs at TestCase init."""
        cls.scriptassistant = plugins.get("scriptassistant")
        cls.dlg = cls.scriptassistant.dlg_settings

    @classmethod
    def tearDownClass(cls):
        """Runs at TestCase teardown."""
        pass

    def setUp(self):
        """Runs before each test."""
        self.dlg.show()
        self.scriptassistant.populate_config_combo()
        self.scriptassistant.show_last_configuration()
        self.view(self.dlg)

    def tearDown(self):
        """Runs after each test."""
        self.dlg.close()
        self.view(self.dlg)
        pass

    def view(self, qt_object):
        if view_tests_during_execution:
            qt_object.repaint()
            time.sleep(1)
        else:
            pass

    def test_correct_script_assistant_test_settings(self):
        self.assertEqual(self.dlg.cmb_config.lineEdit().text(), "Script Assistant")
        self.assertFalse(self.dlg.btn_save.isEnabled())
        self.assertTrue(self.dlg.btn_delete.isEnabled())
        self.assertEqual(self.dlg.lne_script.text(), "")
        self.assertEqual(self.dlg.lne_test.text(), __location__)
        self.assertEqual(self.dlg.lne_test_data.text(), "")
        self.assertFalse(self.dlg.chk_reload.isChecked())

    def test_deleting_settings(self):
        count = self.dlg.cmb_config.count()
        self.dlg.btn_delete.clicked.emit(True)
        self.view(self.dlg)
        if count == 1:
            self.assertTrue(self.dlg.btn_save.isEnabled())
            self.assertFalse(self.dlg.btn_delete.isEnabled())
            self.assertEqual(self.dlg.lne_script.text(), "")
            self.assertEqual(self.dlg.lne_test.text(), "")
            self.assertEqual(self.dlg.lne_test_data.text(), "")
            self.assertFalse(self.dlg.chk_reload.isChecked())
            self.assertFalse(self.dlg.chk_repaint.isChecked())
            self.assertIn("*", self.dlg.windowTitle())
        else:
            self.assertEqual(count - 1, self.dlg.cmb_config.count())
        self.dlg.cmb_config.lineEdit().setText("Script Assistant")
        self.dlg.lne_script.setText("")
        self.dlg.lne_test.setText(__location__)
        self.dlg.lne_test_data.setText("")
        self.dlg.chk_reload.setChecked(False)
        self.dlg.chk_repaint.setChecked(True)
        self.dlg.btn_save.clicked.emit(True)
        self.view(self.dlg)

    def test_adding_new_settings(self):
        self.dlg.cmb_config.lineEdit().setText("Script Assistant Test")
        self.view(self.dlg)
        self.assertIn("*", self.dlg.windowTitle())
        self.dlg.lne_test_data.setText(os.path.join(__location__, "testdata"))
        self.assertTrue(self.dlg.btn_save.isEnabled())
        self.view(self.dlg)
        self.dlg.btn_save.clicked.emit(True)
        self.assertEqual(self.dlg.cmb_config.lineEdit().text(), "Script Assistant Test")
        self.assertEqual(self.dlg.lne_test_data.text(), os.path.join(__location__, "testdata"))
        self.assertFalse(self.dlg.btn_save.isEnabled())
        self.assertTrue(self.dlg.btn_delete.isEnabled())
        self.dlg.btn_delete.clicked.emit(True)
        self.dlg.cmb_config.setCurrentIndex(self.dlg.cmb_config.findText("Script Assistant"))
        self.view(self.dlg)


def run_tests(view_tests=False):
    global view_tests_during_execution
    if view_tests:
        view_tests_during_execution = True
    else:
        view_tests_during_execution = False
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(ScriptAssistantSettingsTest, "test"))
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
