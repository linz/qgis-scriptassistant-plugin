# -*- coding: utf-8 -*-

import os


from qgis.PyQt.QtCore import QSettings
from qgis.core import QgsProject, QgsApplication




def save_setting(setting_name, setting_value):
    """Save a setting to the project file and system."""
    proj = QgsProject.instance()
    proj.writeEntry("script_assistant", setting_name, setting_value)

    settings = QSettings(
        os.path.join(QgsApplication.qgisSettingsDirPath(), "scriptassistant", "config.ini"),
        QSettings.IniFormat,
    )
    settings.setValue("last_script_assistant/{}".format(setting_name), setting_value)


def load_setting(setting_name):
    """Load a setting from the project file or system."""
    proj = QgsProject.instance()
    setting = proj.readEntry("script_assistant", setting_name)[0]

    if not setting:
        settings = QSettings(
            os.path.join(QgsApplication.qgisSettingsDirPath(), "scriptassistant", "config.ini"),
            QSettings.IniFormat,
        )
        setting = settings.value("last_script_assistant/{}".format(setting_name))

    return setting
