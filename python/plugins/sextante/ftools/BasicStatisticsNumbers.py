import os.path
import math

from PyQt4 import QtGui
from PyQt4.QtCore import *

from qgis.core import *

from sextante.core.GeoAlgorithm import GeoAlgorithm
from sextante.core.QGisLayers import QGisLayers

from sextante.parameters.ParameterVector import ParameterVector
from sextante.parameters.ParameterTableField import ParameterTableField
from sextante.parameters.ParameterBoolean import ParameterBoolean

from sextante.outputs.OutputHTML import OutputHTML
from sextante.outputs.OutputNumber import OutputNumber

from sextante.ftools import FToolsUtils as utils

class BasicStatisticsNumbers(GeoAlgorithm):

    INPUT_LAYER = "INPUT_LAYER"
    FIELD_NAME = "FIELD_NAME"
    USE_SELECTION = "USE_SELECTION"
    OUTPUT_HTML_FILE = "OUTPUT_HTML_FILE"

    CV = "CV"
    MIN = "MIN"
    MAX = "MAX"
    SUM = "SUM"
    MEAN = "MEAN"
    COUNT = "COUNT"
    RANGE = "RANGE"
    MEDIAN = "MEDIAN"
    UNIQUE = "UNIQUE"
    STD_DEV = "STD_DEV"

    def getIcon(self):
        return QtGui.QIcon(os.path.dirname(__file__) + "/icons/basic_statistics.png")

    def defineCharacteristics(self):
        self.name = "Basic statistics for numeric fields"
        self.group = "Analysis tools"

        self.addParameter(ParameterVector(self.INPUT_LAYER, "Input vector layer", ParameterVector.VECTOR_TYPE_ANY, False))
        self.addParameter(ParameterTableField(self.FIELD_NAME, "Field to calculate statistics on", self.INPUT_LAYER, ParameterTableField.DATA_TYPE_NUMBER))
        self.addParameter(ParameterBoolean(self.USE_SELECTION, "Use selection", False))

        self.addOutput(OutputHTML(self.OUTPUT_HTML_FILE, "Statistics for numeric field"))

        self.addOutput(OutputNumber(self.CV, "Coefficient of Variation"))
        self.addOutput(OutputNumber(self.MIN, "Minimum value"))
        self.addOutput(OutputNumber(self.MAX, "Maximum value"))
        self.addOutput(OutputNumber(self.SUM, "Sum"))
        self.addOutput(OutputNumber(self.MEAN, "Mean value"))
        self.addOutput(OutputNumber(self.COUNT, "Count"))
        self.addOutput(OutputNumber(self.RANGE, "Range"))
        self.addOutput(OutputNumber(self.MEDIAN, "Median"))
        self.addOutput(OutputNumber(self.UNIQUE, "Number of unique values"))
        self.addOutput(OutputNumber(self.STD_DEV, "Standard deviation"))

    def processAlgorithm(self, progress):
        layer = QGisLayers.getObjectFromUri(self.getParameterValue(self.INPUT_LAYER))
        fieldName = self.getParameterValue(self.FIELD_NAME)
        useSelection = self.getParameterValue(self.USE_SELECTION)

        outputFile = self.getOutputValue(self.OUTPUT_HTML_FILE)

        index = layer.fieldNameIndex(fieldName)
        layer.select([index], QgsRectangle(), False)

        count = 0
        rValue = 0
        cvValue = 0
        minValue = 0
        maxValue = 0
        sumValue = 0
        meanValue = 0
        medianValue = 0
        stdDevValue = 0
        uniqueValue = 0

        isFirst = True
        values = []

        if useSelection:
            selection = layer.selectedFeatures()
            count = layer.selectedFeatureCount()
            total = 100.0 / float(count)
            current = 0

            for f in selection:
                value = float(f.attributeMap()[index].toDouble()[0])

                if isFirst:
                    minValue = value
                    maxValue = value
                    isFirst = False
                else:
                    if value < minValue:
                        minValue = value
                    if value > maxValue:
                        maxValue = value

                values.append(value)
                sumValue += value

                current += 1
                progress.setPercentage(int(current * total))
        else:
            count = layer.featureCount()
            total = 100.0 / float(count)
            current = 0

            ft = QgsFeature()
            while layer.nextFeature(ft):
                value = float(ft.attributeMap()[index].toDouble()[0])

                if isFirst:
                    minValue = value
                    maxValue = value
                    isFirst = False
                else:
                    if value < minValue:
                        minValue = value
                    if value > maxValue:
                        maxValue = value

                values.append( value )
                sumValue += value

                current += 1
                progress.setPercentage(int(current * total))

        # calculate additional values
        rValue = maxValue - minValue
        uniqueValue = utils.getUniqueValuesCount(layer, index, useSelection)

        if count > 0:
          meanValue = sumValue / count
          if meanValue != 0.00:
            for v in values:
              stdDevValue += ((v - meanValue) * (v - meanValue))
            stdDevValue = math.sqrt(stdDevValue / count)
            cvValue = stdDevValue / meanValue

        if count > 1:
          tmp = values
          tmp.sort()
          # calculate median
          if (count % 2) == 0:
            medianValue = 0.5 * (tmp[(count - 1) / 2] + tmp[count / 2])
          else:
            medianValue = tmp[(count + 1) / 2 - 1]

        data = []
        data.append("Count: " + unicode(count))
        data.append("Unique values: " + unicode(uniqueValue))
        data.append("Minimum value: " + unicode(minValue))
        data.append("Maximum value: " + unicode(maxValue))
        data.append("Range: " + unicode(rValue))
        data.append("Sum: " + unicode(sumValue))
        data.append("Mean value: " + unicode(meanValue))
        data.append("Median value: " + unicode(medianValue))
        data.append("Standard deviation: " + unicode(stdDevValue))
        data.append("Coefficient of Variation: " + unicode(cvValue))

        self.createHTML(outputFile, data)

        self.setOutputValue(self.COUNT, count)
        self.setOutputValue(self.UNIQUE, uniqueValue)
        self.setOutputValue(self.MIN, minValue)
        self.setOutputValue(self.MAX, maxValue)
        self.setOutputValue(self.RANGE, rValue)
        self.setOutputValue(self.SUM, sumValue)
        self.setOutputValue(self.MEAN, meanValue)
        self.setOutputValue(self.MEDIAN, medianValue)
        self.setOutputValue(self.STD_DEV, stdDevValue)
        self.setOutputValue(self.CV, cvValue)

    def createHTML(self, outputFile, algData):
        f = open(outputFile, "w")
        for s in algData:
            f.write("<p>" + str(s) + "</p>")
        f.close()