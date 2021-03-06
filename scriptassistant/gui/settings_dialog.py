# -*- coding: utf-8 -*-

import os
from functools import partial

from PyQt4 import uic
from PyQt4.QtGui import QDialog, QFileDialog
from PyQt4.QtCore import pyqtSignal, pyqtSlot, QSettings
from qgis.core import QgsApplication

import settings_manager

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), "settings_dialog.ui"))


class SettingsDialog(QDialog, FORM_CLASS):

    closingDialog = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)

        self.btn_save.setEnabled(False)
        self.btn_delete.setEnabled(False)

        self.btn_save.clicked.connect(self.save_configuration)
        self.btn_delete.clicked.connect(self.delete_configuration)
        self.cmb_config.currentIndexChanged.connect(self.show_configuration)

        self.btn_script.clicked.connect(partial(
            self.load_existing_directory_dialog, self.lne_script))
        self.btn_test_data.clicked.connect(partial(
            self.load_existing_directory_dialog, self.lne_test_data))
        self.btn_test.clicked.connect(partial(
            self.load_existing_directory_dialog, self.lne_test))

        self.lne_script.textChanged.connect(self.check_valid_config)
        self.lne_test.textChanged.connect(self.check_valid_config)
        self.lne_test_data.textChanged.connect(self.check_valid_config)

        self.cmb_config.lineEdit().textChanged.connect(self.check_changes)
        self.cmb_config.currentIndexChanged.connect(self.check_changes)
        self.chk_reload.stateChanged.connect(self.check_changes)

    @pyqtSlot()
    def save_configuration(self):
        """Save configuration (overwrite if config name already exists)."""
        new_config = self.cmb_config.lineEdit().text()

        if self.chk_reload.isChecked():
            no_reload_value = "Y"
        else:
            no_reload_value = "N"

        # Save to system
        settings = QSettings(
            os.path.join(QgsApplication.qgisSettingsDirPath(), "scriptassistant", "config.ini"),
            QSettings.IniFormat,
        )
        # First get the current size of the config array in QSettings.
        size = settings.beginReadArray("script_assistant")

        # Check if the config already exists. If it does, overwrite it.
        for i in xrange(size):
            settings.setArrayIndex(i)
            if settings.value("configuration") == new_config:
                config_index = i
                break
        else:  # no break
            config_index = size

        settings.endArray()
        # Now create new entry / overwrite (depending on index value).
        settings.beginWriteArray("script_assistant")
        settings.setArrayIndex(config_index)
        settings.setValue("configuration", new_config)
        settings.setValue("script_folder", self.lne_script.text())
        settings.setValue("test_data_folder", self.lne_test_data.text())
        settings.setValue("test_folder", self.lne_test.text())
        settings.setValue("no_reload", no_reload_value)
        settings.endArray()

        config_names = [self.cmb_config.itemText(i) for i in range(self.cmb_config.count())]
        if new_config not in config_names:
            self.cmb_config.addItem(new_config)

        self.setWindowTitle("Script Assistant Configuration")
        self.btn_save.setEnabled(False)

        if self.cmb_config.count() > 0:
            self.btn_delete.setEnabled(True)

    @pyqtSlot()
    def delete_configuration(self):
        """Remove configuration."""
        config = self.load_configuration()
        delete_config = self.cmb_config.lineEdit().text()
        for i in config:
            if config[i]["configuration"] == delete_config:
                config.pop(i)
                self.cmb_config.removeItem(self.cmb_config.currentIndex())
                break
        else:
            self.cmb_config.lineEdit().clear()

        settings = QSettings(
            os.path.join(QgsApplication.qgisSettingsDirPath(), "scriptassistant", "config.ini"),
            QSettings.IniFormat,
        )
        settings.beginGroup("script_assistant")
        settings.remove("")
        settings.endGroup()

        settings.beginWriteArray("script_assistant")
        for i, item in enumerate(config):
            settings.setArrayIndex(i)
            settings.setValue("configuration", config[item]["configuration"])
            settings.setValue("script_folder", config[item]["script_folder"])
            settings.setValue("test_data_folder", config[item]["test_data_folder"])
            settings.setValue("test_folder", config[item]["test_folder"])
            settings.setValue("no_reload", config[item]["no_reload"])
        settings.endArray()

        if self.cmb_config.count() == 0:
            self.btn_delete.setEnabled(False)
            self.lne_script.setText("")
            self.lne_test.setText("")
            self.lne_test_data.setText("")
            self.chk_reload.setChecked(False)
        else:
            self.show_configuration()

    @staticmethod
    def load_configuration():
        """Load configuration."""
        settings = QSettings(
            os.path.join(QgsApplication.qgisSettingsDirPath(), "scriptassistant", "config.ini"),
            QSettings.IniFormat,
        )
        size = settings.beginReadArray("script_assistant")
        config = {}
        for i in xrange(size):
            settings.setArrayIndex(i)
            config[i] = {
                "configuration": settings.value("configuration"),
                "script_folder": settings.value("script_folder"),
                "test_data_folder": settings.value("test_data_folder"),
                "test_folder": settings.value("test_folder"),
                "no_reload": settings.value("no_reload"),
            }
        settings.endArray()
        return config

    @pyqtSlot()
    def show_configuration(self):
        """Show saved configuration in settings dialog."""
        settings = QSettings(
            os.path.join(QgsApplication.qgisSettingsDirPath(), "scriptassistant", "config.ini"),
            QSettings.IniFormat,
        )
        settings.beginReadArray("script_assistant")
        settings.setArrayIndex(self.cmb_config.currentIndex())
        self.lne_script.setText(settings.value("script_folder"))
        self.lne_test.setText(settings.value("test_folder"))
        self.lne_test_data.setText(settings.value("test_data_folder"))
        if settings.value("no_reload") == "Y":
            self.chk_reload.setChecked(True)
        elif settings.value("no_reload") == "N":
            self.chk_reload.setChecked(False)
        settings.endArray()

    @pyqtSlot()
    def load_existing_directory_dialog(self, line_edit):
        """Opens a file browser dialog to allow selection of a directory."""
        directory = QFileDialog.getExistingDirectory(
            QFileDialog(),
            self.tr("Select directory..."),
            line_edit.text()
        )
        if directory:
            line_edit.setText(directory)

    @pyqtSlot()
    def check_valid_config(self):
        all_paths_are_valid = True
        if self.lne_script.text() and not os.path.isdir(self.lne_script.text()):
            self.lne_script.setStyleSheet("color: #FF6666")
            all_paths_are_valid = False
        else:
            self.lne_script.setStyleSheet("color: #000000")
        if self.lne_test_data.text() and not os.path.isdir(self.lne_test_data.text()):
            self.lne_test_data.setStyleSheet("color: #FF6666")
            all_paths_are_valid = False
        else:
            self.lne_test_data.setStyleSheet("color: #000000")
        if self.lne_test.text() and not os.path.isdir(self.lne_test.text()):
            self.lne_test.setStyleSheet("color: #FF6666")
            all_paths_are_valid = False
        else:
            self.lne_test.setStyleSheet("color: #000000")

        if all_paths_are_valid is True:
            self.check_changes()
        else:
            self.btn_save.setEnabled(False)

    @pyqtSlot()
    def check_changes(self):
        """Check if the user has changed any settings which are not saved."""
        if self.chk_reload.isChecked():
            no_reload_value = "Y"
        else:
            no_reload_value = "N"

        # Retrieve from system
        settings = QSettings(
            os.path.join(QgsApplication.qgisSettingsDirPath(), "scriptassistant", "config.ini"),
            QSettings.IniFormat,
        )

        # Check all entries against UI elements.
        settings.beginReadArray("script_assistant")
        settings.setArrayIndex(self.cmb_config.currentIndex())
        if self.cmb_config.lineEdit().text() == settings.value("configuration") and \
                self.lne_script.text() == settings.value("script_folder") and \
                self.lne_test.text() == settings.value("test_folder") and \
                self.lne_test_data.text() == settings.value("test_data_folder") and \
                no_reload_value == settings.value("no_reload"):
            self.btn_save.setEnabled(False)
            self.setWindowTitle("Script Assistant Configuration")
        else:
            self.btn_save.setEnabled(True)
            self.setWindowTitle("Script Assistant Configuration*")
        settings.endArray()

    def populate_config_combo(self):
        """Populates the list of configurations from settings."""
        config = self.load_configuration()
        config_names = []
        for i in config:
            config_names.append(config[i]["configuration"])
        if config_names:
            self.btn_delete.setEnabled(True)
            self.cmb_config.clear()
            self.cmb_config.addItems(config_names)
        else:
            self.btn_delete.setEnabled(False)

    def show_last_configuration(self):
        """Show last configuration used."""
        index = self.cmb_config.findText(
            settings_manager.load_setting("current_configuration")
        )
        if index >= 0:
            self.cmb_config.setCurrentIndex(index)
        else:
            # Current configuration does not exist in saved configurations
            # e.g. Project File created on a different machine
            self.cmb_config.lineEdit().setText(
                settings_manager.load_setting("current_configuration")
            )
        self.lne_script.setText(
            settings_manager.load_setting("script_folder")
        )
        self.lne_test_data.setText(
            settings_manager.load_setting("test_data_folder")
        )
        self.lne_test.setText(
            settings_manager.load_setting("test_folder")
        )
        if settings_manager.load_setting("no_reload") == "Y":
            self.chk_reload.setChecked(True)
        elif settings_manager.load_setting("no_reload") == "N":
            self.chk_reload.setChecked(False)

    def closeEvent(self, event):
        self.closingDialog.emit()
        event.accept()
