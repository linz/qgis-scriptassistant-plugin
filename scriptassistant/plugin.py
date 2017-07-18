# -*- coding: utf-8 -*-

import os
import sys
import re
from importlib import import_module
from shutil import copy
from functools import partial

from PyQt4.QtCore import (pyqtSlot, QSize, QSettings, QTranslator, qVersion,
                          QCoreApplication)
from PyQt4.QtGui import (QAction, QIcon, QMenu, QToolButton, QDockWidget,
                         QMessageBox, QPushButton)

from qgis.core import QgsApplication
from qgis.gui import QgsMessageBar
from qgis.utils import plugins, QGis
from processing.script.ScriptUtils import ScriptUtils

import gui.settings_manager
from gui.settings_dialog import SettingsDialog

# Get the path for the parent directory of this file.
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


class ScriptAssistant:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor."""
        self.iface = iface
        self.plugin_dir = __location__
        self.image_dir = os.path.join(__location__, "images")

        # Initialise locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            __location__, "i18n", "ScriptAssistant_{}.qm".format(locale)
        )
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            if qVersion() > "4.3.3":
                QCoreApplication.installTranslator(self.translator)

        # Initialise plugin toolbar
        self.toolbar = self.iface.addToolBar(u"Script Assistant")
        self.toolbar.setObjectName(u"Script Assistant")

        self.test_script_menu = QMenu(self.toolbar)
        self.test_script_menu.aboutToShow.connect(self.update_test_script_menu)

        self.actions = []

        # Initialise QGIS menu item
        self.menu = self.tr(u"&Script Assistant")

        # Initialise plugin dialog
        self.dlg_settings = SettingsDialog()

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.
        """
        return QCoreApplication.translate("ScriptAssistant", message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        settings = QSettings(
            os.path.join(QgsApplication.qgisSettingsDirPath(), "scriptassistant", "config.ini"),
            QSettings.IniFormat,
        )
        config_size = settings.value("script_assistant/size")
        if config_size is None:
            if gui.settings_manager.load_setting("current_configuration"):
                pass
            else:
                gui.settings_manager.save_setting("current_configuration", "Script Assistant")
                gui.settings_manager.save_setting("script_folder", "")
                gui.settings_manager.save_setting("test_folder", os.path.join(__location__, "tests"))
                gui.settings_manager.save_setting("test_data_folder", "")
                gui.settings_manager.save_setting("view_tests", "Y")
                gui.settings_manager.save_setting("no_reload", "N")
                gui.settings_manager.save_setting("current_test", "$ALL")

                settings.beginWriteArray("script_assistant")
                settings.setArrayIndex(0)
                settings.setValue("configuration", "Script Assistant")
                settings.setValue("script_folder", "")
                settings.setValue("test_data_folder", "")
                settings.setValue("test_folder", os.path.join(__location__, "tests"))
                settings.setValue("no_reload", "N")
                settings.setValue("view_tests", "Y")
                settings.endArray()

        self.create_reload_action()
        self.create_test_tool_button()
        self.create_add_test_data_action()
        self.create_settings_action()

    def create_reload_action(self):
        """
        Creates the actions and tool button required for reloading scripts
        from a folder.
        """
        script_folder = gui.settings_manager.load_setting("script_folder")

        # Reload
        self.reload_scripts_action = self.add_action(
            "reload_scripts.png", "Reload: {}".format(script_folder), self.reload_scripts)
        self.toolbar.addAction(self.reload_scripts_action)

        if not script_folder:
            self.reload_scripts_action.setEnabled(False)
        elif not os.path.isdir(script_folder):
            self.reload_scripts_action.setEnabled(False)
            self.iface.messageBar().pushMessage(
                self.tr("Invalid Script Folder"),
                self.tr("Please re-configure the script folder."),
                level=QgsMessageBar.CRITICAL,
            )

    def create_test_tool_button(self):
        """
        Creates the actions and tool button required for running tests
        within QGIS.
        """
        self.create_test_script_menu()
        self.test_tool_button = self.create_tool_button(self.test_script_menu)
        self.test_tool_button.setDefaultAction(self.test_script_action)

    def create_add_test_data_action(self):
        """
        Creates the actions and tool button required for adding test data.
        """

        test_data_folder = gui.settings_manager.load_setting("test_data_folder")

        # Reload
        self.add_test_data_action = self.add_action(
            "add_test_data.png", "Add Test Data From: {}".format(test_data_folder),
            self.add_test_data_to_map
        )
        self.toolbar.addAction(self.add_test_data_action)

        if not test_data_folder:
            self.add_test_data_action.setEnabled(False)
        elif not os.path.isdir(test_data_folder):
            self.add_test_data_action.setEnabled(False)
            self.iface.messageBar().pushMessage(
                self.tr("Invalid Test Data Folder"),
                self.tr("Please re-configure the test data folder."),
                level=QgsMessageBar.CRITICAL,
            )
        elif gui.settings_manager.load_setting("current_test") == "$ALL":
            self.add_test_data_action.setEnabled(False)

    def create_settings_action(self):
        """
        Creates the actions and tool button required for running tests
        within QGIS.
        """
        self.settings_action = self.add_action(
            "settings.png", "Open Script Assistant Settings",
            self.open_settings_dialog
        )
        self.toolbar.addAction(self.settings_action)

    def add_action(self, icon_filename, text, callback):
        """Creates an action with an icon, assigned to a QToolButton menu."""
        icon_path = os.path.join(self.image_dir, icon_filename)
        icon = QIcon()
        icon.addFile(icon_path, QSize(8, 8))
        action = QAction(icon, text, self.toolbar)
        action.triggered.connect(callback)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        return action

    def create_tool_button(self, tool_button_menu):
        """Creates an icon style menu."""
        tool_button = QToolButton()
        tool_button.setMenu(tool_button_menu)
        # The first action created is the default
        tool_button.setDefaultAction(tool_button_menu.actions()[0])
        tool_button.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolbar.addWidget(tool_button)
        return tool_button

    @pyqtSlot()
    def reload_scripts(self):
        """
        Copies and overwrites scripts from the configured folder to the
        QGIS scripts folder.
        """
        folder_dir = gui.settings_manager.load_setting("script_folder")
        if folder_dir:
            for filename in os.listdir(folder_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    if self.is_processing_script(os.path.join(folder_dir, filename)):
                        # QGIS 2.14 has ScriptUtils.scriptsFolder()
                        if QGis.QGIS_VERSION_INT < 21800:
                            copy(os.path.join(folder_dir, filename), ScriptUtils.scriptsFolder())
                        # QGIS 2.18 has ScriptUtils.scriptsFolders()[0]
                        elif QGis.QGIS_VERSION_INT >= 21800:
                            copy(os.path.join(folder_dir, filename), ScriptUtils.scriptsFolders()[0])
            plugins["processing"].toolbox.updateProvider("script")
        else:
            self.iface.messageBar().pushMessage(
                self.tr("No Script Folder Configured"),
                self.tr("Please configure script folder first."),
                level=QgsMessageBar.CRITICAL,
            )

    @staticmethod
    def is_processing_script(filename):
        """
        Find the first non-blank line of the python file and ensure that it
        contains ##formatting that looks like a processing script.
        """
        with open(filename) as lines:
            line = lines.readline()
            while line != "":
                if line.startswith("##"):
                    if line.startswith("## ") or line.startswith("###"):
                        return False
                    else:
                        return True
                else:
                    return False

    def update_test_script_menu(self):
        """
        """
        self.test_script_menu.clear()
        self.create_test_script_menu()
        self.test_tool_button.setDefaultAction(self.test_script_action)

    def create_test_script_menu(self):
        """
        """
        test_folder = gui.settings_manager.load_setting("test_folder")

        if test_folder:
            if not os.path.isdir(test_folder):
                self.iface.messageBar().pushMessage(
                    self.tr("Invalid Test Folder"),
                    self.tr("Please reconfigure the test folder."),
                    level=QgsMessageBar.CRITICAL,
                )
            else:
                if test_folder not in sys.path:
                    sys.path.append(test_folder)

        self.test_script_action = self.add_action(
            "test_scripts.png", "Test: {}".format(gui.settings_manager.load_setting("current_test")),
            partial(self.prepare_test, gui.settings_manager.load_setting("current_test"))
        )
        self.test_script_menu.addAction(self.test_script_action)
        self.test_all_action = self.add_action(
            "test_scripts.png", "all in: {}".format(test_folder),
            partial(self.prepare_test, "$ALL")
        )
        self.test_script_menu.addAction(self.test_all_action)

        if test_folder:
            test_file_names = [
                f[5:-3] for f in os.listdir(test_folder) if
                f.startswith("test_") and f.endswith(".py")
            ]
            for test_name in test_file_names:
                action = self.add_action(
                    "test_scripts.png", test_name,
                    partial(self.prepare_test, test_name)
                )
                self.test_script_menu.addAction(action)

            if not gui.settings_manager.load_setting("current_test") in test_file_names:
                gui.settings_manager.save_setting("current_test", "$ALL")
                self.test_script_action.setText("Test: all")

        if not test_folder or not os.path.isdir(test_folder):
            self.test_script_action.setEnabled(False)
            self.test_all_action.setEnabled(False)

    @pyqtSlot()
    def prepare_test(self, test_name):
        """Open the QGIS Python Console. Handle testing all tests."""
        self.open_python_console()
        gui.settings_manager.save_setting("current_test", test_name)
        self.update_test_script_menu()
        if test_name:
            if test_name == "$ALL":
                self.add_test_data_action.setEnabled(False)
                test_folder = gui.settings_manager.load_setting("test_folder")
                test_file_names = [
                    f[5:-3] for f in os.listdir(test_folder) if
                    f.startswith("test_") and f.endswith(".py")
                ]
                for actual_test_name in test_file_names:
                    self.run_test(actual_test_name)
            else:
                if not self.add_test_data_action.isEnabled():
                    test_data_folder = gui.settings_manager.load_setting("test_data_folder")
                    if os.path.isdir(test_data_folder):
                        self.add_test_data_action.setEnabled(True)
                self.run_test(test_name)
        else:
            # Ideally the button would be disabled, but that isn't possible
            # with QToolButton without odd workarounds
            self.iface.messageBar().pushMessage(
                self.tr("No Test Script Configured"),
                self.tr("Please configure a script to test first."),
                level=QgsMessageBar.CRITICAL,
            )

    def open_python_console(self):
        """Ensures that the QGIS Python Console is visible to the user."""
        pythonConsole = self.iface.mainWindow().findChild(
            QDockWidget, "PythonConsole"
        )
        # If Python Console hasn't been opened before in this QGIS session
        # then pythonConsole will be a None type variable
        if pythonConsole is not None:
            if not pythonConsole.isVisible():
                pythonConsole.setVisible(True)
        else:
            # This method causes the Python Dialog to close if it is open
            # so we only use it when we know that is is closed
            self.iface.actionShowPythonDialog().trigger()

    def run_test(self, test_name):
        """Import test scripts, run using run_tests method.

        Optionally reload and view depending on settings.
        """
        module = import_module("test_{0}".format(test_name))
        # have to reload otherwise a QGIS restart is required after changes
        if gui.settings_manager.load_setting("no_reload") == "Y":
            pass
        else:
            reload(module)
        run_tests = getattr(module, "run_tests")
        if gui.settings_manager.load_setting("view_tests") == "Y":
            try:
                run_tests(view_tests=True)
            except TypeError:
                self.iface.messageBar().pushMessage(
                    self.tr("Could Not Repaint Widgets"),
                    self.tr("Tests configured to repaint widgets, but test script doesn't support this."),
                    level=QgsMessageBar.INFO,
                )
                run_tests()
        else:
            run_tests()

    @pyqtSlot()
    def add_test_data_to_map(self):
        """Adds test data referred to in the test script to the map. Must
        be .shp (shapefile).
        """
        test_data_folder = gui.settings_manager.load_setting("test_data_folder")
        test_folder = gui.settings_manager.load_setting("test_folder")
        current_test = gui.settings_manager.load_setting("current_test")
        test_file = open(os.path.join(test_folder, "test_{}.py".format(current_test)), "r")
        test_text = test_file.read()
        test_file.close()
        matches = re.findall(r"\/(.*).shp", test_text)
        for match in matches:
            self.iface.addVectorLayer(
                os.path.join(test_data_folder, "{}.shp".format(match)),
                match, "ogr"
            )

    @pyqtSlot()
    def open_settings_dialog(self):
        """Open the settings dialog and show the current configuration."""
        self.dlg_settings.show()

        self.populate_config_combo()

        if gui.settings_manager.load_setting("current_configuration"):
            self.show_last_configuration()

            self.dlg_settings.check_changes()

        result = self.dlg_settings.exec_()

        # On close
        if result or not result:

            # An asterisk in the window title indicates an unsaved configuration.
            if "*" in self.dlg_settings.windowTitle():
                msg_confirm = QMessageBox()
                msg_confirm.setWindowTitle("Save")
                msg_confirm.setText("Would you like to save this configuration?")
                msg_confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_confirm.setDefaultButton(QMessageBox.Yes)
                msg_result = msg_confirm.exec_()
                if msg_result == QMessageBox.Yes:
                    self.dlg_settings.save_configuration()
                else:
                    msg_inform = QMessageBox()
                    msg_inform.setWindowTitle("Info")
                    msg_inform.setText("The configured settings will be used "
                                       "for the current session, but will not "
                                       "be saved for future sessions.")
                    msg_inform.addButton(QPushButton("OK"), QMessageBox.AcceptRole)
                    msg_inform.exec_()

            script_folder = self.dlg_settings.lne_script.text()
            gui.settings_manager.save_setting("script_folder", script_folder)
            if os.path.exists(script_folder):
                self.reload_scripts_action.setText("Reload: {}".format(script_folder))
                self.reload_scripts_action.setEnabled(True)
            else:
                self.reload_scripts_action.setText("Invalid Script Folder Path")
                self.reload_scripts_action.setEnabled(False)
                if script_folder != "":
                    self.iface.messageBar().pushMessage(
                        self.tr("Invalid Script Folder Path"),
                        self.tr("The configured script folder is not a valid path."),
                        level=QgsMessageBar.CRITICAL,
                    )

            test_folder = self.dlg_settings.lne_test.text()
            gui.settings_manager.save_setting("test_folder", test_folder)
            if os.path.exists(test_folder):
                self.test_script_action.setEnabled(True)
                self.test_all_action.setEnabled(True)
                if test_folder not in sys.path:
                    sys.path.append(test_folder)
                self.update_test_script_menu()
            else:
                self.test_script_action.setText("Invalid Test Script Path")
                self.test_script_action.setEnabled(False)
                self.test_all_action.setEnabled(False)
                self.add_test_data_action.setEnabled(False)
                if test_folder != "":
                    self.iface.messageBar().pushMessage(
                        self.tr("Invalid Test Script Path"),
                        self.tr("The configured test script folder is not a valid path."),
                        level=QgsMessageBar.CRITICAL,
                    )

            test_data_folder = self.dlg_settings.lne_test_data.text()
            gui.settings_manager.save_setting("test_data_folder", test_data_folder)
            if os.path.exists(test_data_folder):
                self.add_test_data_action.setText("Add Test Data From: {}".format(test_data_folder))
                self.add_test_data_action.setEnabled(True)
            else:
                self.add_test_data_action.setText("Invalid Test Data Path")
                self.add_test_data_action.setEnabled(False)
                if test_data_folder != "":
                    self.iface.messageBar().pushMessage(
                        self.tr("Invalid Test Data Path"),
                        self.tr("The configured test data folder is not a valid path."),
                        level=QgsMessageBar.CRITICAL,
                    )

            if self.dlg_settings.chk_reload.isChecked():
                gui.settings_manager.save_setting("no_reload", "Y")
            else:
                gui.settings_manager.save_setting("no_reload", "N")

            if self.dlg_settings.chk_repaint.isChecked():
                gui.settings_manager.save_setting("view_tests", "Y")
            else:
                gui.settings_manager.save_setting("view_tests", "N")

            if self.dlg_settings.cmb_config.lineEdit().text():
                gui.settings_manager.save_setting(
                    "current_configuration",
                    self.dlg_settings.cmb_config.lineEdit().text()
                )

    def populate_config_combo(self):
        """Populates the list of configurations from settings."""
        config = self.dlg_settings.load_configuration()
        config_names = []
        for i in config:
            config_names.append(config[i]["configuration"])
        if config_names:
            self.dlg_settings.btn_delete.setEnabled(True)
            self.dlg_settings.cmb_config.clear()
            self.dlg_settings.cmb_config.addItems(config_names)
        else:
            self.dlg_settings.btn_delete.setEnabled(False)

    def show_last_configuration(self):
        """Show last configuration used."""
        index = self.dlg_settings.cmb_config.findText(
            gui.settings_manager.load_setting("current_configuration")
        )
        if index >= 0:
            self.dlg_settings.cmb_config.setCurrentIndex(index)
        else:
            # Current configuration does not exist in saved configurations
            # e.g. Project File created on a different machine
            self.dlg_settings.cmb_config.lineEdit().setText(
                gui.settings_manager.load_setting("current_configuration")
            )
        self.dlg_settings.lne_script.setText(
            gui.settings_manager.load_setting("script_folder")
        )
        self.dlg_settings.lne_test_data.setText(
            gui.settings_manager.load_setting("test_data_folder")
        )
        self.dlg_settings.lne_test.setText(
            gui.settings_manager.load_setting("test_folder")
        )
        if gui.settings_manager.load_setting("no_reload") == "Y":
            self.dlg_settings.chk_reload.setChecked(True)
        elif gui.settings_manager.load_setting("no_reload") == "N":
            self.dlg_settings.chk_reload.setChecked(False)
        if gui.settings_manager.load_setting("view_tests") == "Y":
            self.dlg_settings.chk_repaint.setChecked(True)
        elif gui.settings_manager.load_setting("view_tests") == "N":
            self.dlg_settings.chk_repaint.setChecked(False)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u"&Script Assistant"), action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
