from django.http import HttpResponse
import json
from collections import OrderedDict
from io import StringIO
from enum import Enum

# Common base class for FC
class FusionCharts:

    baseTemplate = """
        <script type="text/javascript">
            FusionCharts.ready(function () {
                __TS__
                __FC__
            });
        </script>"""

    constructorTemplate = """new FusionCharts(__constructorOptions__);"""
    renderTemplate = """FusionCharts("__chartId__").render();"""
    eventTemplate = """FusionCharts("__chartId__").addEventListener("_fceventname_",_fceventbody_);"""
    timeSeriesObject = None

    # constructor
    def __init__(self, type, id, width, height, renderAt, dataFormat, dataSource): 
        self.eventOptions = OrderedDict()
        self.constructorOptions = {}  
        self.constructorOptions['type'] = type
        self.constructorOptions['id'] = id
        self.constructorOptions['width'] = width
        self.constructorOptions['height'] = height
        self.constructorOptions['renderAt'] = renderAt
        self.constructorOptions['dataFormat'] = dataFormat
        #dataSource = unicode(dataSource, errors='replace')
        if isinstance(dataSource, TimeSeries):
            self.timeSeriesObject = dataSource
            self.constructorOptions['dataSource'] = "__TS__"
        else:
            self.constructorOptions['dataSource'] = dataSource

    def addEvent(self, eventName, funcName):
        self.eventOptions[eventName] = funcName

    def addMessage(self, messageName, messageValue):
        self.constructorOptions[messageName] = messageValue

    # render the chart created
    # It prints a script and calls the FusionCharts javascript render method of created chart   
    def render(self):
        
        # Serialize constructorOptions to a JSON formatted
        self.readyJson = json.dumps(self.constructorOptions, ensure_ascii=False)

        if isinstance(self.timeSeriesObject, TimeSeries):
            self.readyJson = self.readyJson.replace("__TS__", self.timeSeriesObject.GetDataSource())

        # Create Fusioncharts constructor from template and insert JSON data in it
        self.readyJson = FusionCharts.constructorTemplate.replace('__constructorOptions__', self.readyJson)

        # Iterate and attach EventHandler from template
        for key, value in self.eventOptions.items():
            self.readyJson = self.readyJson + FusionCharts.eventTemplate.replace('__chartId__', self.constructorOptions['id'])
            self.readyJson = self.readyJson.replace("_fceventname_", key).replace("_fceventbody_", value)

        # FusionCharts Render method will create chart
        self.readyJson = self.readyJson + FusionCharts.renderTemplate.replace('__chartId__', self.constructorOptions['id'])
        self.readyJson = FusionCharts.baseTemplate.replace("__FC__", self.readyJson)

        if isinstance(self.timeSeriesObject, TimeSeries):
            self.readyJson = self.readyJson.replace("__TS__", self.timeSeriesObject.GetDataStore())
        else:
            self.readyJson = self.readyJson.replace("__TS__", "")

        self.readyJson = self.readyJson.replace('\\n', '')
        self.readyJson = self.readyJson.replace('\\t', '')

        if(self.constructorOptions['dataFormat'] == 'json'):
            self.readyJson = self.readyJson.replace('\\', '')
            self.readyJson = self.readyJson.replace('"{', "{")
            self.readyJson = self.readyJson.replace('}"', "}")

        return self.readyJson

# Common base class for TimeSeries
class TimeSeries:
    
    fusionTableObject = None
    attributes = None

    # constructor
    def __init__(self, fusionTable):
        self.attributes = []
        self.fusionTableObject = fusionTable

    def AddAttribute(self, Key, Value):
        self.attributes.append({ Key: Value})

    def GetDataSource(self):
        stringBuilder = StringBuilder()
        
        for dic in self.attributes:
            for key in dic:
                stringBuilder.AppendLine("{0}:{1},".format(key, dic[key]))

        stringBuilder.AppendLine("{0}:{1}".format("data", "fusionTable"))

        return "{{\n{0}\n}}".format(stringBuilder)
        
    def GetDataStore(self):
        return "{0}".format(self.fusionTableObject.GetDataTable())


# Common base class for FusionTable
class FusionTable:

    class OrderBy(Enum):
        ASC = 0
        DESC = 1
    
    class FilterType(Enum):
        Equals = 0
        Greater = 1
        GreaterEquals = 2
        Less = 3
        LessEquals = 4
        Between = 5
    
    stringBuilder = None

    # constructor
    def __init__(self, schema, data):
        self.stringBuilder = StringBuilder()
        self.stringBuilder.AppendLine("let schema = {0};".format(schema))
        self.stringBuilder.AppendLine("let data = {0};".format(data))
        self.stringBuilder.AppendLine("let fusionDataStore = new FusionCharts.DataStore();")
        self.stringBuilder.AppendLine("let fusionTable = fusionDataStore.createDataTable(data, schema);")

    def Select(self, *columnName):
        if len(columnName) > 0:
            columns = "'{0}'".format("', '".join(columnName))
            self.stringBuilder.AppendLine("fusionTable = fusionTable.query(FusionCharts.DataStore.Operators.select([" + columns + "]));")
    
    def Sort(self, columnName, columnOrderBy):
        orderby = "asc" if columnOrderBy == FusionTable.OrderBy.ASC else "desc"
        sortedData = "sort([{0}])".format("{{column: '{0}', order: '{1}'}}".format(columnName, orderby))
        self.stringBuilder.AppendLine("fusionTable = fusionTable.query({0});".format(sortedData))

    def CreateFilter(self, filterType, columnName, *values):
        fx = FusionTable.FilterType(filterType).name
        fx = fx[0].lower() + fx[1:]

        # empty list
        my_list = []
        for a in values:
            my_list.append(str(a))

        my_list.append(my_list[0])
    
        switcher = {
            FusionTable.FilterType.Equals: "FusionCharts.DataStore.Operators.{0}('{1}', '{2}')".format(fx, columnName, my_list[0]),
            FusionTable.FilterType.Between: "FusionCharts.DataStore.Operators.{0}('{1}', {2}, {3})".format(fx, columnName, my_list[0], my_list[1])
        }

        return switcher.get(filterType, "FusionCharts.DataStore.Operators.{0}('{1}', {2})".format(fx, columnName, my_list[0]))

    def ApplyFilter(self, filter):
        if len(filter) > 0:
            self.stringBuilder.AppendLine("fusionTable = fusionTable.query(" + filter + ");")

    def ApplyFilterByCondition(self, filter):
        if len(filter) > 0:
            self.stringBuilder.AppendLine("fusionTable = fusionTable.query(" + filter + ");")
    
    def Pipe(self, *filters):
        if len(filters) > 0:
            filter = "{0}".format(", ".join(filters))
            self.stringBuilder.AppendLine("fusionTable = fusionTable.query(FusionCharts.DataStore.Operators.pipe(" + filter + "));")

    def GetDataTable(self):
        return self.stringBuilder

class StringBuilder:
     _file_str = None

     def __init__(self):
         self._file_str = StringIO()

     def AppendLine(self, str):
         self._file_str.write(str + "\n")

     def __str__(self):
         return self._file_str.getvalue()