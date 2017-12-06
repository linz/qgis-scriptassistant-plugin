# -*- coding: utf-8 -*-

import coverage
import os
import sys
import re
import unittest
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
        self.test_actions = []
        self.test_script_action = None

        # Initialise QGIS menu item
        self.menu = self.tr(u"&Script Assistant")

        # Initialise plugin dialog
        self.dlg_settings = SettingsDialog()

        self.test_cases = []
        self.test_modules = []
        self.aggregated_test_result = None

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
                gui.settings_manager.save_setting("no_reload", "N")
                gui.settings_manager.save_setting("current_test", "$ALL")

                settings.beginWriteArray("script_assistant")
                settings.setArrayIndex(0)
                settings.setValue("configuration", "Script Assistant")
                settings.setValue("script_folder", "")
                settings.setValue("test_data_folder", "")
                settings.setValue("test_folder", os.path.join(__location__, "tests"))
                settings.setValue("no_reload", "N")
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

    def add_action(self, icon_filename, text, callback, test=False):
        """Creates an action with an icon, assigned to a QToolButton menu."""
        icon_path = os.path.join(self.image_dir, icon_filename)
        icon = QIcon()
        icon.addFile(icon_path, QSize(8, 8))
        action = QAction(icon, text, self.toolbar)
        action.triggered.connect(callback)
        if test is False:
            self.iface.addPluginToMenu(self.menu, action)
            self.actions.append(action)
        else:
            self.test_actions.append(action)
        return action

    def create_tool_button(self, tool_button_menu):
        """Creates an icon style menu."""
        tool_button = QToolButton()
        tool_button.setMenu(tool_button_menu)
        # The first action created is the default
        try:
            tool_button.setDefaultAction(tool_button_menu.actions()[0])
        except IndexError:
            pass
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
        user_script_dir = os.path.join(
            QgsApplication.qgisSettingsDirPath(), "processing", "scripts"
        )

        if folder_dir:
            for filename in os.listdir(folder_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    if self.is_processing_script(os.path.join(folder_dir, filename)):
                        copy(os.path.join(folder_dir, filename), user_script_dir)
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

        # Coverage
        print test_folder

        cov = coverage.Coverage(
            omit="{}/test_*.py".format(test_folder),
            include="~/dev/plugins/qgis-roads-plugin/roads/*.py",)
        print cov
        cov.start()

        if test_folder:
            if not os.path.isdir(test_folder):
                self.iface.messageBar().pushMessage(
                    self.tr("Invalid Test Folder"),
                    self.tr("Please reconfigure the test folder."),
                    level=QgsMessageBar.CRITICAL,
                )

        self.test_actions = []
        if self.test_script_action:
            self.iface.removePluginMenu(self.tr(u"&Script Assistant"), self.test_script_action)

        self.test_script_action = self.add_action(
            "test_scripts.png", "Test: {}".format(gui.settings_manager.load_setting("current_test")),
            partial(self.prepare_test, gui.settings_manager.load_setting("current_test"), cov=cov)
        )
        self.test_script_menu.addAction(self.test_script_action)
        self.test_all_action = self.add_action(
            "test_scripts.png", "all in: {}".format(test_folder),
            partial(self.prepare_test, "$ALL", cov=cov), True
        )
        self.test_script_menu.addAction(self.test_all_action)

        if os.path.isdir(test_folder):
            self.test_cases = []
            self.test_modules = []
            self.update_unique_test_modules(test_folder)

            for test_module_name in self.test_modules:
                action = self.add_action(
                    "test_scripts.png", test_module_name,
                    partial(self.prepare_test, test_module_name, cov=cov), True
                )
                self.test_script_menu.addAction(action)

            if not gui.settings_manager.load_setting("current_test") in self.test_modules:
                gui.settings_manager.save_setting("current_test", "$ALL")
                self.test_script_action.setText("Test: all")

        if not test_folder or not os.path.isdir(test_folder):
            self.test_script_action.setEnabled(False)
            self.test_all_action.setEnabled(False)

    def update_unique_test_modules(self, test_folder):
        """
        Loops through all TestCase instances in a test folder to find
        unique test modules
        """
        tests = unittest.TestLoader().discover(test_folder, pattern="test_*.py")
        self.update_all_test_cases(tests)

        all_test_modules = []
        for t in self.test_cases:
            all_test_modules.append(type(t).__module__)
        unique_test_modules = list(set(all_test_modules))
        self.test_modules = unique_test_modules
        self.test_modules.sort()

    def update_all_test_cases(self, test_suite):
        """
        Loops through the test suites discovered using unittest.TestLoader().discover()
        to find all individual TestCase instances and return them in a list
        """
        for test_or_suite in test_suite:
            if unittest.suite._isnotsuite(test_or_suite):
                # confirmed test
                self.test_cases.append(test_or_suite)
            else:
                # confirmed suite
                self.update_all_test_cases(test_or_suite)

    @pyqtSlot()
    def prepare_test(self, test_name, cov=None):
        """Open the QGIS Python Console. Handle testing all tests."""
        self.open_python_console()

        self.update_test_script_menu()

        if test_name:
            self.aggregated_test_result = unittest.TestResult()

            gui.settings_manager.save_setting("current_test", test_name)
            if test_name == "$ALL":
                self.add_test_data_action.setEnabled(False)
                test_folder = gui.settings_manager.load_setting("test_folder")
                self.update_unique_test_modules(test_folder)

                for test_module_name in self.test_modules:
                    result = self.run_test(test_module_name)
                    self.prepare_result(result)
            else:
                if not self.add_test_data_action.isEnabled():
                    test_data_folder = gui.settings_manager.load_setting("test_data_folder")
                    if os.path.isdir(test_data_folder):
                        self.add_test_data_action.setEnabled(True)
                result = self.run_test(test_name)
                self.prepare_result(result)
            self.print_aggregated_result()
            if cov:
                data = cov.get_data()
                print data
                print dir(data)
                print data.lines("~/dev/plugins/qgis-roads-plugin/roads/tasks/controller.py")
                print cov.analysis2("~/dev/plugins/qgis-roads-plugin/roads/tasks/controller.py")
                cov.stop()
                cov.save()
                print cov.report()

        else:
            # Ideally the button would be disabled, but that isn't possible
            # with QToolButton without odd workarounds
            self.iface.messageBar().pushMessage(
                self.tr("No Test Script Configured"),
                self.tr("Please configure a script to test first."),
                level=QgsMessageBar.CRITICAL,
            )

    def prepare_result(self, result):
        """Extend aggregated TestResult"""
        if result:
            self.aggregated_test_result.errors.extend(result.errors)
            self.aggregated_test_result.failures.extend(result.failures)
            self.aggregated_test_result.expectedFailures.extend(
                result.expectedFailures)
            self.aggregated_test_result.unexpectedSuccesses.extend(
                result.unexpectedSuccesses)
            self.aggregated_test_result.skipped.extend(result.skipped)
            self.aggregated_test_result.testsRun += result.testsRun
        else:
            self.iface.messageBar().pushMessage(
                self.tr("No Test Summary"),
                self.tr("Test summary could not be provided to output as the run_tests method does not return a result."),
                level=QgsMessageBar.WARNING,
            )

    def print_aggregated_result(self):
        """Print a summary of all tests to the QGIS Python Console"""
        if self.aggregated_test_result.testsRun:
            print ""
            if self.aggregated_test_result.errors:
                print "ERRORS:\n"
                for error in self.aggregated_test_result.errors:
                    print error[0]
                    print "-" * len(error[0].__str__())
                    print "{0}\n".format(error[1])
            if self.aggregated_test_result.failures:
                print "FAILURES:\n"
                for failure in self.aggregated_test_result.failures:
                    print failure[0]
                    print "-" * len(failure[0].__str__())
                    print "{0}\n".format(failure[1])
            if self.aggregated_test_result.unexpectedSuccesses:
                print "UNEXPECTED SUCCESSES:\n"
                for unexpected in self.aggregated_test_result.unexpectedSuccesses:
                    print unexpected
                print ""
            if self.aggregated_test_result.skipped:
                print "SKIPPED:\n"
                for skip in self.aggregated_test_result.skipped:
                    print "{0} - {1}".format(skip[0], skip[1])
                print ""

            successes = self.aggregated_test_result.testsRun - (
                len(self.aggregated_test_result.errors) +
                len(self.aggregated_test_result.failures) +
                len(self.aggregated_test_result.expectedFailures) +
                len(self.aggregated_test_result.unexpectedSuccesses) +
                len(self.aggregated_test_result.skipped)
            )

            self.print_table_row(
                "Successes", successes)
            self.print_table_row(
                "Errors", len(self.aggregated_test_result.errors))
            self.print_table_row(
                "Failures", len(self.aggregated_test_result.failures))
            self.print_table_row(
                "Expected Failures", len(self.aggregated_test_result.expectedFailures))
            self.print_table_row(
                "Unexpected Successes", len(self.aggregated_test_result.unexpectedSuccesses))
            self.print_table_row(
                "Skipped", len(self.aggregated_test_result.skipped))

            print """+===========================+============+
| Total                     |       {total: >{fill}} |
+---------------------------+------------+
            """.format(
                total=self.aggregated_test_result.testsRun,
                fill='4'
            )

        else:
            print "\nNo tests were run.\n"

    @staticmethod
    def print_table_row(result_type, count):
        if count:
            print """+---------------------------+------------+
| {result_type: <{text_fill}} | {count: >{count_fill}} |""".format(
                result_type=result_type,
                text_fill='25',
                count=count,
                count_fill='10'
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
        module = import_module(test_name)
        # have to reload otherwise a QGIS restart is required after changes
        if gui.settings_manager.load_setting("no_reload") == "Y":
            pass
        else:
            reload(module)
        suite = unittest.TestLoader().loadTestsFromModule(module)
        result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
        return result

    @pyqtSlot()
    def add_test_data_to_map(self):
        """Adds test data referred to in the test script to the map. Must
        be .shp (shapefile).
        """
        test_data_folder = gui.settings_manager.load_setting("test_data_folder")
        test_folder = gui.settings_manager.load_setting("test_folder")
        current_test = gui.settings_manager.load_setting("current_test")
        if current_test == "$ALL":
            self.iface.messageBar().pushMessage(
                self.tr("Select a Single Test"),
                self.tr("Cannot add test data for all tests."),
                level=QgsMessageBar.WARNING,
            )
            return
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
        self.dlg_settings.populate_config_combo()

        if gui.settings_manager.load_setting("current_configuration"):
            self.dlg_settings.show_last_configuration()
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

            self.save_settings()

    def save_settings(self):
        """Save current settings to Project file and config."""
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
            gui.settings_manager.save_setting("current_test", "$ALL")
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

        if self.dlg_settings.cmb_config.lineEdit().text():
            gui.settings_manager.save_setting(
                "current_configuration",
                self.dlg_settings.cmb_config.lineEdit().text()
            )

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u"&Script Assistant"), action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
