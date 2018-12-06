# -*- coding: utf-8 -*-

"""Tests the add_area_column.py user script. Created for the purpose of
testing Script Assistant plugin functionality.
"""

import os
import unittest
from shutil import copy

from qgis.core import (QgsApplication, 
                       QgsVectorLayer, 
                       QgsProcessingUtils, 
                       QgsProcessingContext,
                       QgsProject)
from qgis.utils import plugins, Qgis
from qgis.gui import QgisInterface

from PyQt5.QtTest import QTest

import processing
from processing.core.Processing import Processing
from processing import run
from processing.script import ScriptUtils

WAIT=500

class AddAreaColumnTest(unittest.TestCase):

    def setUp(self):
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

        copy(file_path, ScriptUtils.scriptsFolders()[0])

        # Add the basic providers including 'script'
        Processing.initialize()

        QgsApplication.processingRegistry().providerById('script').refreshAlgorithms()
        context = QgsProcessingContext()

        result = run("script:addareacolumn", 
                     {"INPUT": test_layer, 
                     "OUTPUT": 'memory:'},
                      context=context)#,
                     #context.addLayerToLoadOnCompletion(...))

        self.updated_layer=result['OUTPUT']
        # Only reason to add layer to map is to 
        # Provide feedaback to test executor 
        QgsProject.instance().addMapLayer(self.updated_layer)
        QTest.qWait(WAIT)

    def tearDown(self):
        if self.updated_layer:
            QgsProject.instance().removeMapLayer(self.updated_layer.id())

    def test_valid_output(self):
        """Ensure that an output layer has been created with expected rows."""
        self.assertEqual(self.updated_layer.featureCount(), 1)
        fields=[field.name() for field in self.updated_layer.fields()]
        self.assertIn('area',fields)
