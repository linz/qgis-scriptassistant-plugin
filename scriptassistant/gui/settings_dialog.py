# -*- coding: utf-8 -*-

import os.path
from functools import partial

from PyQt4 import uic
from PyQt4.QtGui import QDialog, QFileDialog
from PyQt4.QtCore import pyqtSignal, pyqtSlot, QSettings

import settings_manager

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'settings_dialog.ui'))


class SettingsDialog(QDialog, FORM_CLASS):

    closingDialog = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)

        self.btn_save.setEnabled(False)
        self.btn_delete.setEnabled(False)

        self.btn_save.clicked.connect(self.saveConfiguration)
        self.btn_delete.clicked.connect(self.deleteConfiguration)
        self.cmb_config.currentIndexChanged.connect(self.load_configuration)

        self.btn_script.clicked.connect(partial(
            self.load_existing_directory_dialog, self.lne_script))
        self.btn_test_data.clicked.connect(partial(
            self.load_existing_directory_dialog, self.lne_test_data))
        self.btn_test.clicked.connect(partial(
            self.load_existing_directory_dialog, self.lne_test))

        self.lne_script.textChanged.connect(self.check_valid_config)
        self.lne_script.textEdited.connect(self.check_valid_config)
        self.lne_test.textChanged.connect(self.check_valid_config)
        self.lne_test.textEdited.connect(self.check_valid_config)
        self.lne_test_data.textChanged.connect(self.check_valid_config)
        self.lne_test_data.textEdited.connect(self.check_valid_config)

        self.chk_reload.stateChanged.connect(self.set_reload)
        self.chk_repaint.stateChanged.connect(self.set_repaint)

    @pyqtSlot()
    def saveConfiguration(self):
        """Save configuration (overwrite if config name already exists)."""
        new_config = self.cmb_config.lineEdit().text()
        if self.chk_reload.isChecked():
            no_reload_value = 'Y'
        else:
            no_reload_value = 'N'
        if self.chk_repaint.isChecked():
            view_tests_value = 'Y'
        else:
            view_tests_value = 'N'

        # Save to project file
        settings_manager.save_setting('configuration', new_config)
        self.cmb_config.addItem(new_config)

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
        settings.setValue('script_folder', self.lne_script.text())
        settings.setValue('test_data_folder', self.lne_test_data.text())
        settings.setValue('test_folder', self.lne_test.text())
        settings.setValue('no_reload', no_reload_value)
        settings.setValue('view_tests', view_tests_value)
        settings.endArray()

        if self.cmb_config.count() > 0:
            self.btn_delete.setEnabled(True)

    @pyqtSlot()
    def deleteConfiguration(self):
        """Remove configuration."""
        config = self.load_configuration()
        delete_config = self.cmb_config.lineEdit().text()
        for i in config:
            if config[i]['configuration'] == delete_config:
                del_i = i
                break
        config.pop(del_i)

        self.cmb_config.removeItem(self.cmb_config.currentIndex())

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
            settings.setValue('no_reload', config[item]['no_reload'])
            settings.setValue('view_tests', config[item]['view_tests'])
        settings.endArray()

        if self.cmb_config.count() == 0:
            self.btn_delete.setEnabled(False)

    @staticmethod
    def load_configuration():
        """Load configuration."""
        settings = QSettings()
        size = settings.beginReadArray('script_assistant')
        config = {}
        for i in xrange(size):
            settings.setArrayIndex(i)
            config[i] = {
                'configuration': settings.value('configuration'),
                'script_folder': settings.value('script_folder'),
                'test_data_folder': settings.value('test_data_folder'),
                'test_folder': settings.value('test_folder'),
                'no_reload': settings.value('no_reload'),
                'view_tests': settings.value('view_tests'),
            }
        settings.endArray()
        return config

    @pyqtSlot()
    def load_existing_directory_dialog(self, line_edit):
        """Opens a file browser dialog to allow selection of a directory."""
        directory = QFileDialog.getExistingDirectory(
            QFileDialog(),
            self.tr('Select directory...'),
            line_edit.text()
        )
        if directory:
            line_edit.setText(directory)

    @pyqtSlot()
    def check_valid_config(self):
        if os.path.isdir(self.lne_script.text()) or \
                os.path.isdir(self.lne_test_data.text()) or \
                os.path.isdir(self.lne_test.text()):
            self.btn_save.setEnabled(True)
        else:
            self.btn_save.setEnabled(False)

    @pyqtSlot()
    def set_reload(self):
        if self.chk_reload.isChecked():
            settings_manager.save_setting('no_reload', 'Y')
        else:
            settings_manager.save_setting('no_reload', 'N')

    @pyqtSlot()
    def set_repaint(self):
        if self.chk_repaint.isChecked():
            settings_manager.save_setting('view_tests', 'Y')
        else:
            settings_manager.save_setting('view_tests', 'N')

    def closeEvent(self, event):
        self.closingDialog.emit()
        event.accept()
