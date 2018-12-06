# -*- coding: utf-8 -*-

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsField,
                       QgsFields,
                       QgsFeature,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink)
import processing


class ExampleProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    This processing script adds an area attribute to the input layer and
    returns a new layer.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExampleProcessingAlgorithm()

    def name(self):
        """
        Returns the algorithm name
        """
        return 'addareacolumn'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Add Area Column')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to
        """
        return self.tr('scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'scripts'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr("Example algorithm short description")

    def initAlgorithm(self, config=None):
        """
        Inputs and output of the algorithm
        """

        # Add the input vector features source. It must be of vector type.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('BQ31'),
                [QgsProcessing.TypeVector]
            )
        )

        # Add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('BQ31_Updated')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. 
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        # Add area field
        fields=QgsFields()
        for field in source.fields():
            fields.append(field)
        fields.append(QgsField("area", QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            source.wkbType(),
            source.sourceCrs()
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        features = source.getFeatures()
        source.fields().append(QgsField("area", QVariant.Double))

        for feat in features:
            out_feat = QgsFeature()
            geom = feat.geometry()
            area = geom.area()
            attrs = feat.attributes()
            attrs.append(area)
            out_feat.setAttributes(attrs)
            out_feat.setGeometry(feat.geometry())
            sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}

