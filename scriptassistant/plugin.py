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
    QFileDialog)

from qgis.gui import QgsMessageBar
from qgis.core import QgsProject
from qgis.utils import plugins, iface, QGis
from processing.script.ScriptUtils import ScriptUtils

# Initialize Qt resources from file resources.py
import resources
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
        self.image_dir = os.path.join(__location__, 'images')

        # Initialise locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            __location__, 'i18n', 'ScriptAssistant_{}.qm'.format(locale)
        )
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Initialise plugin toolbar
        self.toolbar = self.iface.addToolBar(u'Script Assistant')
        self.toolbar.setObjectName(u'Script Assistant')

        self.reload_scripts_menu = QMenu(self.toolbar)
        self.test_script_menu = QMenu(self.toolbar)
        self.add_test_data_menu = QMenu(self.toolbar)

        self.test_script_menu.aboutToShow.connect(self.updateTestScriptMenu)

        self.actions = []

        # Initialise QGIS menu item
        self.menu = self.tr(u'&Script Assistant')

        # Initialise plugin dialogs
        self.dlg_settings = SettingsDialog()

        self.dlg_settings.btn_save.setEnabled(False)
        self.dlg_settings.btn_delete.setEnabled(False)

        self.dlg_settings.cmb_config.currentIndexChanged.connect(
            self.loadConfiguration)
        self.dlg_settings.btn_save.clicked.connect(
            self.saveConfiguration)
        self.dlg_settings.btn_delete.clicked.connect(
            self.deleteConfiguration)

        self.dlg_settings.btn_script.clicked.connect(partial(
            self.loadExistingDirectoryDialog, self.dlg_settings.lne_script))
        self.dlg_settings.btn_test_data.clicked.connect(partial(
            self.loadExistingDirectoryDialog, self.dlg_settings.lne_test_data))
        self.dlg_settings.btn_test.clicked.connect(partial(
            self.loadExistingDirectoryDialog, self.dlg_settings.lne_test))

        self.dlg_settings.lne_script.textChanged.connect(self.checkValidConfig)
        self.dlg_settings.lne_script.textEdited.connect(self.checkValidConfig)
        self.dlg_settings.lne_test.textChanged.connect(self.checkValidConfig)
        self.dlg_settings.lne_test.textEdited.connect(self.checkValidConfig)
        self.dlg_settings.lne_test_data.textChanged.connect(self.checkValidConfig)
        self.dlg_settings.lne_test_data.textEdited.connect(self.checkValidConfig)

        self.dlg_settings.chk_reload.stateChanged.connect(self.setReload)
        self.dlg_settings.chk_repaint.stateChanged.connect(self.setRepaint)

        self.dlg_settings.show()
        self.dlg_settings.lne_test.setText(os.path.join(__location__, 'tests'))
        self.dlg_settings.close()

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.
        """
        return QCoreApplication.translate('ScriptAssistant', message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.addReloadToolButton()
        self.addTestToolButton()
        self.addTestDataToolButton()
        self.addSettingsAction()

    def checkValidConfig(self):
        if os.path.isdir(self.dlg_settings.lne_script.text()) or \
                os.path.isdir(self.dlg_settings.lne_test_data.text()) or \
                os.path.isdir(self.dlg_settings.lne_test.text()):
            self.dlg_settings.btn_save.setEnabled(True)
        else:
            self.dlg_settings.btn_save.setEnabled(False)

    def addAction(self, icon_filename, text, callback):
        """Creates an action with an icon, assigned to a QToolButton menu."""
        icon_path = os.path.join(self.image_dir, icon_filename)
        icon = QIcon()
        icon.addFile(icon_path, QSize(8, 8))
        action = QAction(icon, text, self.toolbar)
        action.triggered.connect(callback)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        return action

    def createToolButton(self, tool_button_menu):
        """Creates an icon style menu."""
        tool_button = QToolButton()
        tool_button.setMenu(tool_button_menu)
        # The first action created is the default
        tool_button.setDefaultAction(tool_button_menu.actions()[0])
        tool_button.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolbar.addWidget(tool_button)
        return tool_button

    def updateTestScriptMenu(self):
        self.test_script_menu.clear()
        self.createTestScriptMenu()
        self.test_tool_button.setDefaultAction(self.test_script_action)

    def addReloadToolButton(self):
        """
        Creates the actions and tool button required for reloading scripts
        from a folder.
        """
        script_folder = self.loadSetting('script_folder')

        # Reload
        self.reload_scripts_action = self.addAction(
            'reload_scripts.png', 'Reload: {}'.format(script_folder), self.reloadScripts)
        self.reload_scripts_menu.addAction(self.reload_scripts_action)
        self.createToolButton(self.reload_scripts_menu)

        if not script_folder:
            self.reload_scripts_action.setEnabled(False)

    def createTestScriptMenu(self):
        test_folder = self.loadSetting('test_folder')

        if test_folder and test_folder not in sys.path:
            sys.path.append(test_folder)

        self.test_script_action = self.addAction(
            'test_scripts.png', 'Test: {}'.format(self.loadSetting('current_test')),
            partial(self.prepareTest, self.loadSetting('current_test'))
        )
        self.test_script_menu.addAction(self.test_script_action)
        self.test_all_action = self.addAction(
            'test_scripts.png', 'all in: {}'.format(test_folder),
            partial(self.prepareTest, '$ALL')
        )
        self.test_script_menu.addAction(self.test_all_action)

        if test_folder:
            test_file_names = [
                f[5:-3] for f in os.listdir(test_folder) if
                f.startswith('test_') and f.endswith('.py')
            ]
            for test_name in test_file_names:
                action = self.addAction(
                    'test_scripts.png', test_name,
                    partial(self.prepareTest, test_name)
                )
                self.test_script_menu.addAction(action)

            if not self.loadSetting('current_test') in test_file_names:
                self.saveSetting('current_test', '$ALL')
                self.test_script_action.setText('Test: all')

        if not test_folder:
            self.test_script_action.setEnabled(False)
            self.test_all_action.setEnabled(False)

    def addTestToolButton(self):
        """
        Creates the actions and tool button required for running tests
        within QGIS.
        """
        self.createTestScriptMenu()
        self.test_tool_button = self.createToolButton(self.test_script_menu)
        self.test_tool_button.setDefaultAction(self.test_script_action)

    def addTestDataToolButton(self):
        """
        Creates the actions and tool button required for adding test data.
        """

        test_data_folder = self.loadSetting('test_data_folder')

        # Reload
        self.add_test_data_action = self.addAction(
            'add_test_data.png', 'Add Test Data From: {}'.format(test_data_folder),
            self.addTestDataToMap
        )
        self.add_test_data_menu.addAction(self.add_test_data_action)
        self.createToolButton(self.add_test_data_menu)

        if not test_data_folder:
            self.add_test_data_action.setEnabled(False)

    def addSettingsAction(self):
        """
        Creates the actions and tool button required for running tests
        within QGIS.
        """
        self.settings_action = self.addAction(
            'settings.png', 'Open Script Assistant Settings',
            self.openSettingsDialog
        )
        self.toolbar.addAction(self.settings_action)

    @staticmethod
    def isProcessingScript(filename):
        """
        Find the first non-blank line of the python file and ensure that it
        contains ##something that looks like a processing script.
        """
        with open(filename) as lines:
            line = lines.readline()
            while line != '':
                if line.startswith('##'):
                    if line.startswith('## ') or line.startswith('###'):
                        return False
                    else:
                        return True
                else:
                    return False

    @pyqtSlot()
    def reloadScripts(self):
        """
        Copies and overwrites scripts from the configured folder to the
        QGIS scripts folder.
        """
        folder_dir = self.loadSetting('script_folder')
        if folder_dir:
            for filename in os.listdir(folder_dir):
                if filename.endswith('.py') and not filename.startswith('_'):
                    if self.isProcessingScript(os.path.join(folder_dir, filename)):
                        # QGIS 2.14 has ScriptUtils.scriptsFolder()
                        if QGis.QGIS_VERSION_INT < 21800:
                            copy(os.path.join(folder_dir, filename), ScriptUtils.scriptsFolder())
                        # QGIS 2.18 has ScriptUtils.scriptsFolders()[0]
                        elif QGis.QGIS_VERSION_INT >= 21800:
                            copy(os.path.join(folder_dir, filename), ScriptUtils.scriptsFolders()[0])
            plugins['processing'].toolbox.updateProvider('script')
        else:
            self.iface.messageBar().pushMessage(
                self.tr('No Script Folder Configured'),
                self.tr('Please configure script folder first.'),
                level=QgsMessageBar.CRITICAL,
            )

    @pyqtSlot()
    def setReload(self):
        if self.loadSetting('no_reload') == 'N':
            self.saveSetting('no_reload', 'Y')
        else:
            self.saveSetting('no_reload', 'N')

    @pyqtSlot()
    def setRepaint(self):
        if self.loadSetting('view_tests') == 'N':
            self.saveSetting('view_tests', 'Y')
        else:
            self.saveSetting('view_tests', 'N')

    @pyqtSlot()
    def openSettingsDialog(self):
        self.dlg_settings.show()

        config = self.loadConfiguration()
        config_names = []
        for i in config:
            config_names.append(config[i]['configuration'])
        if config_names:
            self.dlg_settings.btn_delete.setEnabled(True)
            self.dlg_settings.cmb_config.clear()
            self.dlg_settings.cmb_config.addItems(config_names)
        else:
            self.dlg_settings.btn_delete.setEnabled(False)

        if self.loadSetting('current_configuration'):
            index = self.dlg_settings.cmb_config.findText(
                self.loadSetting('current_configuration')
            )
            if index >= 0:
                self.dlg_settings.cmb_config.setCurrentIndex(index)
                for i in config:
                    if config[i]['configuration'] == self.loadSetting('current_configuration'):
                        self.dlg_settings.lne_script.setText(config[i]['script_folder'])
                        self.dlg_settings.lne_test_data.setText(config[i]['test_data_folder'])
                        self.dlg_settings.lne_test.setText(config[i]['test_folder'])
                        break

        result = self.dlg_settings.exec_()
        if result:
            script_folder = self.dlg_settings.lne_script.text()
            self.saveSetting('script_folder', script_folder)
            if os.path.exists(script_folder):
                self.reload_scripts_action.setEnabled(True)
            else:
                self.reload_scripts_action.setEnabled(False)
                if script_folder != '':
                    self.iface.messageBar().pushMessage(
                        self.tr('Invalid Script Folder Path'),
                        self.tr('The configured script folder is not a valid path.'),
                        level=QgsMessageBar.CRITICAL,
                    )

            test_folder = self.dlg_settings.lne_test.text()
            self.saveSetting('test_folder', test_folder)
            if os.path.exists(test_folder):
                self.test_script_action.setEnabled(True)
                self.test_all_action.setEnabled(True)
                if test_folder not in sys.path:
                    sys.path.append(test_folder)
                self.updateTestScriptMenu()
            else:
                self.test_script_action.setEnabled(False)
                self.test_all_action.setEnabled(False)
                self.add_test_data_action.setEnabled(False)
                if test_folder  != '':
                    self.iface.messageBar().pushMessage(
                        self.tr('Invalid Test Script Path'),
                        self.tr('The configured test script folder is not a valid path.'),
                        level=QgsMessageBar.CRITICAL,
                    )

            test_data_folder = self.dlg_settings.lne_test_data.text()
            self.saveSetting('test_data_folder', test_data_folder)
            if os.path.exists(test_data_folder):
                self.add_test_data_action.setEnabled(True)
            else:
                self.add_test_data_action.setEnabled(False)
                if test_data_folder != '':
                    self.iface.messageBar().pushMessage(
                        self.tr('Invalid Test Data Path'),
                        self.tr('The configured test data folder is not a valid path.'),
                        level=QgsMessageBar.CRITICAL,
                    )

            if self.dlg_settings.cmb_config.lineEdit().text():
                self.saveSetting(
                    'current_configuration',
                    self.dlg_settings.cmb_config.lineEdit().text()
                )

    def runTest(self, test_name):
        module = import_module('test_{0}'.format(test_name))
        # have to reload otherwise a QGIS restart is required after changes
        if self.loadSetting('no_reload') == 'Y':
            pass
        else:
            reload(module)
        run_tests = getattr(module, 'run_tests')
        if self.loadSetting('view_tests') == 'Y':
            run_tests(view_tests=True)
        else:
            run_tests()

    @pyqtSlot()
    def prepareTest(self, test_name):
        """Run configured test(s) in the QGIS Python Console."""
        self.openPythonConsole()
        # Probably not working
        self.saveSetting('current_test', test_name)
        if test_name:
            if test_name == '$ALL':
                test_folder = self.loadSetting('test_folder')
                test_file_names = [
                    f[5:-3] for f in os.listdir(test_folder) if
                    f.startswith('test_') and f.endswith('.py')
                ]
                for actual_test_name in test_file_names:
                    self.runTest(actual_test_name)
            else:
                self.runTest(test_name)
        else:
            # Ideally the button would be disabled, but that isn't possible
            # with QToolButton without odd workarounds
            self.iface.messageBar().pushMessage(
                self.tr('No Test Script Configured'),
                self.tr('Please configure a script to test first.'),
                level=QgsMessageBar.CRITICAL,
            )

    @pyqtSlot()
    def addTestDataToMap(self):
        """Something"""
        test_data_folder = self.loadSetting('test_data_folder')
        test_folder = self.loadSetting('test_folder')
        current_test = self.loadSetting('current_test')
        test_file = open(os.path.join(test_folder, 'test_{}.py'.format(current_test)), 'r')
        test_text = test_file.read()
        test_file.close()
        matches = re.findall(r'\/(.*).shp', test_text)
        for match in matches:
            iface.addVectorLayer(
                os.path.join(test_data_folder, '{}.shp'.format(match)),
                match, 'ogr'
            )

    @pyqtSlot()
    def loadExistingDirectoryDialog(self, line_edit):
        """Opens a file browser dialog to allow selection of a directory."""
        directory = QFileDialog.getExistingDirectory(
            QFileDialog(),
            self.tr('Select directory...'),
            line_edit.text()
        )
        if directory:
            line_edit.setText(directory)

    @staticmethod
    def openPythonConsole():
        """Ensures that the QGIS Python Console is visible to the user."""
        pythonConsole = iface.mainWindow().findChild(
            QDockWidget, 'PythonConsole'
        )
        # If Python Console hasn't been opened before in this QGIS session
        # then pythonConsole will be a None type variable
        try:
            if not pythonConsole.isVisible():
                pythonConsole.setVisible(True)
        except AttributeError:
            # This method causes the Python Dialog to close if it is open
            # so we only use it when we know that is is closed
            iface.actionShowPythonDialog().trigger()

    @pyqtSlot()
    def saveConfiguration(self):
        """Save configuration (overwrite if config name already exists)."""
        new_config = self.dlg_settings.cmb_config.lineEdit().text()

        # Save to project file
        self.saveSetting('configuration', new_config)
        self.dlg_settings.cmb_config.addItem(new_config)

        # Save to system
        settings = QSettings()
        # First get the current size of the config array in QSettings.
        size = settings.beginReadArray('script_assistant')
        # Check if the config already exists. If it does, overwrite it.
        for i in xrange(size):
            settings.setArrayIndex(i)
            if settings.value('configuration') == new_config:
                config_index = i
                break
        else:  # no break
            config_index = size
        settings.endArray()
        # Now create new entry / overwrite (depending on index value).
        settings.beginWriteArray('script_assistant')
        settings.setArrayIndex(config_index)
        settings.setValue('configuration', new_config)
        settings.setValue('script_folder', self.dlg_settings.lne_script.text())
        settings.setValue('test_data_folder', self.dlg_settings.lne_test_data.text())
        settings.setValue('test_folder', self.dlg_settings.lne_test.text())
        settings.endArray()

        if self.dlg_settings.cmb_config.count() > 0:
            self.dlg_settings.btn_delete.setEnabled(True)

    @pyqtSlot()
    def deleteConfiguration(self):
        """Remove configuration."""
        config = self.loadConfiguration()
        delete_config = self.dlg_settings.cmb_config.lineEdit().text()
        for i in config:
            if config[i]['configuration'] == delete_config:
                del_i = i
                break
        config.pop(del_i)

        self.dlg_settings.cmb_config.removeItem(self.dlg_settings.cmb_config.currentIndex())

        settings = QSettings()
        settings.beginGroup('script_assistant')
        settings.remove('')
        settings.endGroup()

        settings.beginWriteArray('script_assistant')
        for i, item in enumerate(config):
            settings.setArrayIndex(i)
            settings.setValue('configuration', config[item]['configuration'])
            settings.setValue('script_folder', config[item]['script_folder'])
            settings.setValue('test_data_folder', config[item]['test_data_folder'])
            settings.setValue('test_folder', config[item]['test_folder'])
        settings.endArray()

        if self.dlg_settings.cmb_config.count() == 0:
            self.dlg_settings.btn_delete.setEnabled(False)

    @staticmethod
    def loadConfiguration():
        settings = QSettings()
        size = settings.beginReadArray('script_assistant')
        config = {}
        for i in xrange(size):
            settings.setArrayIndex(i)
            config[i] = {
                'configuration': settings.value('configuration'),
                'script_folder': settings.value('script_folder'),
                'test_data_folder': settings.value('test_data_folder'),
                'test_folder': settings.value('test_folder')
            }
        settings.endArray()
        return config

    @staticmethod
    def saveSetting(setting_name, setting_value):
        """Save a setting to the project file and system."""
        proj = QgsProject.instance()
        proj.writeEntry('script_assistant', setting_name, setting_value)
        settings = QSettings()
        settings.setValue('script_assistant/{}'.format(setting_name), setting_value)

    @staticmethod
    def loadSetting(setting_name):
        """Load a setting from the project file or system."""
        proj = QgsProject.instance()
        setting = proj.readEntry('script_assistant', setting_name)[0]
        if not setting:
            settings = QSettings()
            setting = settings.value('script_assistant/{}'.format(setting_name))
        return setting

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&Script Assistant'), action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
