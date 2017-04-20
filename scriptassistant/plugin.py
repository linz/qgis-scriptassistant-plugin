# -*- coding: utf-8 -*-

import os
import sys
from importlib import import_module
from shutil import copy

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
from gui.script_folder import ConfigureScriptFolderDialog
from gui.test_script import ConfigureTestScriptDialog


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
        self.test_script_menu = QMenu(self.toolbar)
        self.reload_scripts_menu = QMenu(self.toolbar)
        self.actions = []

        # Initialise QGIS menu item
        self.menu = self.tr(u'&Script Assistant')

        # Initialise plugin dialogs
        self.dlg_test_script_config = ConfigureTestScriptDialog()
        self.dlg_script_folder_config = ConfigureScriptFolderDialog()

        self.dlg_script_folder_config.pushButton.clicked.connect(
            self.loadExistingDirectoryDialog)

        folder_dir = self.loadConfiguredScriptFolder()
        if not folder_dir:
            self.reload_scripts_action.setEnabled(False)
            self.test_scripts_action.setEnabled(False)
        else:
            if os.path.join(folder_dir, 'tests') not in sys.path:
                sys.path.append(os.path.join(folder_dir, 'tests'))

        last_script_tested = self.loadConfiguredTestScript()
        if not last_script_tested:
            self.test_scripts_action.setEnabled(False)

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.
        """
        return QCoreApplication.translate('ScriptAssistant', message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.addReloadToolButton()
        self.addTestToolButton()

    def addAction(self, icon_filename, text, callback, tool_button_menu):
        """Creates an action with an icon, assigned to a QToolButton menu."""
        icon_path = os.path.join(self.image_dir, icon_filename)
        icon = QIcon()
        icon.addFile(icon_path, QSize(8, 8))
        action = QAction(icon, text, self.toolbar)
        action.triggered.connect(callback)
        tool_button_menu.addAction(action)
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

    def addReloadToolButton(self):
        """
        Creates the actions and tool button required for reloading scripts
        from a folder.
        """

        # if status_tip is not None:
        #     action.setStatusTip(status_tip)
        # if whats_this is not None:
        #    action.setWhatsThis(whats_this)

        directory = self.loadConfiguredScriptFolder()

        # Reload
        self.reload_scripts_action = self.addAction(
            'reload_scripts.png', 'Reload: {}'.format(directory),
            self.reloadScripts, self.reload_scripts_menu)
        self.addAction(
            'configure_script_folder.png', self.tr('Choose a file directory'),
            self.openScriptFolderDialog, self.reload_scripts_menu)
        self.createToolButton(self.reload_scripts_menu)

    def addTestToolButton(self):
        """
        Creates the actions and tool button required for running tests
        within QGIS.
        """
        script = self.loadConfiguredTestScript()

        # Test
        self.test_scripts_action = self.addAction(
            'test_scripts.png', 'Test: {}'.format(script),
            self.runTest, self.test_script_menu)
        self.addAction(
            'configure_test_scripts.png', self.tr('Choose a script to test'),
            self.openTestScriptDialog, self.test_script_menu)
        self.createToolButton(self.test_script_menu)

    @pyqtSlot()
    def reloadScripts(self):
        """
        Copies and overwrites scripts from the configured folder to the
        QGIS scripts folder.
        """
        folder_dir = self.loadConfiguredScriptFolder()
        for filename in os.listdir(folder_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                # QGIS 2.14 has ScriptUtils.scriptsFolder()
                if QGis.QGIS_VERSION_INT < 21800:
                    copy(os.path.join(folder_dir, filename), ScriptUtils.scriptsFolder())
                # QGIS 2.18 has ScriptUtils.scriptsFolders()[0]
                elif QGis.QGIS_VERSION_INT >= 21800:
                    copy(os.path.join(folder_dir, filename), ScriptUtils.scriptsFolders()[0])
        plugins['processing'].toolbox.updateProvider('script')

    @pyqtSlot()
    def openScriptFolderDialog(self):
        """Opens a dialog that allows the script folder to be configured."""
        self.dlg_script_folder_config.show()
        lne = self.dlg_script_folder_config.lineEdit

        result = self.dlg_script_folder_config.exec_()
        if result:
            self.reload_scripts_action.setEnabled(True)
            self.reload_scripts_action.setText('Reload: {}'.format(lne.text()))
            self.saveConfiguredScriptFolder(lne.text())
            if os.path.join(lne.text(), 'tests') not in sys.path:
                sys.path.append(os.path.join(lne.text(), 'tests'))

    @pyqtSlot()
    def runTest(self):
        """Run configured test(s) in the QGIS Python Console."""
        self.openPythonConsole()
        script_name = self.loadConfiguredTestScript()
        if script_name == 'all':
            cmb = self.dlg_test_script_config.comboBox
            all_items = [cmb.itemText(i) for i in range(cmb.count())]
            for test_script_name in all_items:
                if test_script_name != 'all':
                    module = import_module('test_{0}'.format(test_script_name))
                    tests = getattr(module, 'run_tests')
                    tests()
        else:
            module = import_module('test_{0}'.format(script_name))
            tests = getattr(module, 'run_tests')
            tests()

    @pyqtSlot()
    def openTestScriptDialog(self):
        """Open a dialog that allows tests to be configured."""
        self.dlg_test_script_config.show()
        cmb = self.dlg_test_script_config.comboBox
        # Remove any previously added tests
        cmb.clear()
        cmb.addItem('all')

        if self.loadConfiguredScriptFolder():
            last_script_folder = self.loadConfiguredScriptFolder()
            test_file_names = [
                f[5:-3] for f in os.listdir(os.path.join(last_script_folder, 'tests')) if \
                f.startswith('test_') and f.endswith('.py')]
            cmb.addItems(test_file_names)
        else:
            self.iface.messageBar().pushMessage(
                self.tr('No Scripts in Settings'),
                self.tr('Please configure script folder first.'),
                level=QgsMessageBar.CRITICAL,
            )

        if self.loadConfiguredTestScript():
            indexOfLastScript = cmb.findText(self.loadConfiguredTestScript())
            cmb.setCurrentIndex(indexOfLastScript)

        result = self.dlg_test_script_config.exec_()
        if result:
            self.test_scripts_action.setEnabled(True)
            self.test_scripts_action.setText('Test: {}'.format(cmb.currentText()))
            self.saveConfiguredTestScript(cmb.currentText())

    @pyqtSlot()
    def loadExistingDirectoryDialog(self):
        """Opens a file browser dialog to allow selection of test directory."""
        directory = QFileDialog.getExistingDirectory(
            QFileDialog(),
            self.tr('Select script directory...')
        )
        self.dlg_script_folder_config.lineEdit.setText(directory)

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

    @staticmethod
    def loadConfiguredTestScript():
        """Load the most recently configured test script.

        Check the QGIS Project file first and then QSettings.
        """
        proj = QgsProject.instance()
        last_script_tested = proj.readEntry('script_assistant', 'last_script_tested')[0]
        if not last_script_tested:
            settings = QSettings()
            last_script_tested = settings.value('script_assistant/last_script_tested')
        return last_script_tested

    @staticmethod
    def saveConfiguredTestScript(last_script_tested):
        """Save the configured test script.

        The script name is saved with the QGIS Project file and in QSettings.
        """
        proj = QgsProject.instance()
        proj.writeEntry('script_assistant', 'last_script_tested', last_script_tested)
        settings = QSettings()
        settings.setValue('script_assistant/last_script_tested', last_script_tested)

    @staticmethod
    def loadConfiguredScriptFolder():
        """Load the most recently configured script folder.

        Check the QGIS Project file first and then QSettings.
        """
        proj = QgsProject.instance()
        last_script_folder = proj.readEntry('script_assistant', 'last_script_folder')[0]
        if not last_script_folder:
            settings = QSettings()
            last_script_folder = settings.value('script_assistant/last_script_folder')
        return last_script_folder

    @staticmethod
    def saveConfiguredScriptFolder(last_script_folder):
        """Save the configured script folder.

        The script folder is saved with the QGIS Project file and in QSettings.
        """
        proj = QgsProject.instance()
        proj.writeEntry('script_assistant', 'last_script_folder', last_script_folder)
        settings = QSettings()
        settings.setValue('script_assistant/last_script_folder', last_script_folder)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&Script Assistant'), action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
