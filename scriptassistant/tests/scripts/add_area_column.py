##BQ31=vector
##BQ31_Updated=output vector

"""This processing script adds an area attribute to the input layer and
returns a new layer.
"""

from PyQt4.QtCore import QVariant
from qgis.core import QgsField, QgsFields, QgsVectorFileWriter, QGis, QgsFeature
import processing

layer = processing.getObject(BQ31)
output = BQ31_Updated

fields = QgsFields()
for field in layer.fields():
    fields.append(field)
fields.append(QgsField("area", QVariant.Double))

writer = QgsVectorFileWriter(
    output, None, fields, QGis.WKBLineString, layer.crs()
)

feats = layer.getFeatures()
for feat in feats:
    out_feat = QgsFeature()
    geom = feat.geometry()
    area = geom.area()
    attrs = feat.attributes()
    attrs.append(area)
    out_feat.setAttributes(attrs)
    out_feat.setGeometry(geom)
    writer.addFeature(out_feat)

del writer
