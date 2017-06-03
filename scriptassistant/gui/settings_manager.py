# -*- coding: utf-8 -*-

from PyQt4.QtCore import QSettings
from qgis.core import QgsProject


def save_setting(setting_name, setting_value):
    """Save a setting to the project file and system."""
    proj = QgsProject.instance()
    proj.writeEntry('script_assistant', setting_name, setting_value)

    settings = QSettings()
    settings.setValue('script_assistant/{}'.format(setting_name), setting_value)


def load_setting(setting_name):
    """Load a setting from the project file or system."""
    proj = QgsProject.instance()
    setting = proj.readEntry('script_assistant', setting_name)[0]

    if not setting:
        settings = QSettings()
        setting = settings.value('script_assistant/{}'.format(setting_name))

    return setting
