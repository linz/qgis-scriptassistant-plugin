# -*- coding: utf-8 -*-

import os
import unittest

from qgis.core import QgsApplication
from qgis.utils import plugins

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
        self.dlg.populate_config_combo()
        self.dlg.show_last_configuration()

    def tearDown(self):
        """Runs after each test."""
        self.dlg.close()
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

    def test_adding_new_settings(self):
        self.dlg.cmb_config.lineEdit().setText("Script Assistant Test")
        self.assertIn("*", self.dlg.windowTitle())
        self.dlg.lne_test_data.setText(os.path.join(__location__, "tests", "testdata"))
        self.assertTrue(self.dlg.btn_save.isEnabled())
        self.dlg.btn_save.clicked.emit(True)
        self.assertEqual(self.dlg.cmb_config.lineEdit().text(), "Script Assistant Test")
        self.assertEqual(self.dlg.lne_test_data.text(), os.path.join(__location__, "tests", "testdata"))
        self.assertFalse(self.dlg.btn_save.isEnabled())
        self.assertTrue(self.dlg.btn_delete.isEnabled())
        self.dlg.btn_delete.clicked.emit(True)
        self.dlg.cmb_config.setCurrentIndex(self.dlg.cmb_config.findText("Script Assistant"))

    def test_running_script_test(self):
        self.dlg.lne_test.setText(os.path.join(__location__, "tests"))
        self.assertIn("*", self.dlg.windowTitle())
        self.dlg.btn_save.clicked.emit(True)
        self.assertNotIn("*", self.dlg.windowTitle())
        self.scriptassistant.save_settings()
        self.dlg.close()
        for action in self.scriptassistant.test_actions:
            if action.text() == "add_area_column":
                action.triggered.emit(True)
        self.dlg.show()
        self.dlg.populate_config_combo()
        self.dlg.show_last_configuration()
        self.dlg.lne_test.setText(__location__)
        self.dlg.lne_test_data.setText("")
        self.dlg.btn_save.clicked.emit(True)
        self.scriptassistant.save_settings()
        os.remove(
            os.path.join(
                QgsApplication.qgisSettingsDirPath(),
                "processing", "scripts", "add_area_column.py"
            )
        )
        plugins["processing"].toolbox.updateProvider("script")

    def test_running_plugin_test(self):
        self.dlg.lne_test.setText(os.path.join(__location__, "tests"))
        self.assertIn("*", self.dlg.windowTitle())
        self.dlg.btn_save.clicked.emit(True)
        self.assertNotIn("*", self.dlg.windowTitle())
        self.scriptassistant.save_settings()
        self.dlg.close()
        for action in self.scriptassistant.test_actions:
            if action.text() == "plugin":
                action.triggered.emit(True)
        self.dlg.show()
        self.dlg.populate_config_combo()
        self.dlg.show_last_configuration()
        self.dlg.lne_test.setText(__location__)
        self.dlg.lne_test_data.setText("")
        self.dlg.btn_save.clicked.emit(True)
        self.scriptassistant.save_settings()
