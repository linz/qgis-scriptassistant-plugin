# -*- coding: utf-8 -*-

import os.path

from PyQt4 import uic
from PyQt4.QtGui import QDialog
from PyQt4.QtCore import pyqtSignal


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'configure_test_script_dialog.ui'))


class ConfigureTestScriptDialog(QDialog, FORM_CLASS):

    closingDialog = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(ConfigureTestScriptDialog, self).__init__(parent)
        self.setupUi(self)

    def closeEvent(self, event):
        self.closingDialog.emit()
        event.accept()