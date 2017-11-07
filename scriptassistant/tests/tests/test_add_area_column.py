# -*- coding: utf-8 -*-

"""Tests the add_area_column.py user script. Created for the purpose of
testing Script Assistant plugin functionality.
"""

import os
import unittest
from shutil import copy

from qgis.core import QgsVectorLayer
from qgis.utils import plugins, QGis

import processing
from processing.core.Processing import Processing
from processing import runalg
from processing.script.ScriptUtils import ScriptUtils

# set global variables
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

test_dir = os.path.join(__location__, "testdata")
file_path = os.path.abspath(os.path.join(
    __location__, "..", "scripts", "add_area_column.py"))

# Set up test layers
test_layer = QgsVectorLayer(
    r"{}/BQ31.shp".format(test_dir), "BQ31", "ogr"
)
if not test_layer.isValid():
    raise ImportError("Reference Layer failed to load!")

# QGIS 2.14 has ScriptUtils.scriptsFolder()
if QGis.QGIS_VERSION_INT < 21800:
    copy(file_path, ScriptUtils.scriptsFolder())
# QGIS 2.18 has ScriptUtils.scriptsFolders()
elif QGis.QGIS_VERSION_INT >= 21800:
    copy(file_path, ScriptUtils.scriptsFolders()[0])
plugins["processing"].toolbox.updateProvider("script")

Processing.initialize()

# QGIS 2.14 has Processing.updateAlgsList()
if QGis.QGIS_VERSION_INT < 21800:
    Processing.updateAlgsList()
# QGIS 2.18 has algList.reloadProvider(("script")
elif QGis.QGIS_VERSION_INT >= 21800:
    from processing.core.alglist import algList
    algList.reloadProvider("script")

result = runalg(
    "script:addareacolumn",
    test_layer,
    None
)

output_layer = processing.getObject(result["BQ31_Updated"])


class AddAreaColumnTest(unittest.TestCase):

    def test_valid_output(self):
        """Ensure that an output layer has been created with expected rows."""
        self.assertEqual(output_layer.featureCount(), 1)
