import json

from django.db import models

with open("apps/web/functions.json", "r") as file:
    FUNCTIONS = json.load(file)

NODE_CONFIG = {
    "input": {
        "displayName": "Get data",
        "icon": "fa-file",
        "description": "Select a table from an Integration or previous Workflow",
        "section": "Input/Output",
        "explanation": "Select the data sources you want to transform in your workflow. They can come from results from other workflows or integrations.",
    },
    "output": {
        "displayName": "Save data",
        "icon": "fa-save",
        "description": "Save result as a new table",
        "section": "Input/Output",
        "explanation": "Make the results of your workflow available for other workflows or use them in dashboards by connecting the appropriate nodes with a Save data node.",
    },
    "select": {
        "displayName": "Select columns",
        "icon": "fa-mouse-pointer",
        "description": "Select columns from the table",
        "section": "Table manipulations",
        "explanation": "Use the select columns node to choose a subset of columns from the input table.",
    },
    "join": {
        "displayName": "Join",
        "icon": "fa-link",
        "description": "Combine rows from two tables based on a common column",
        "section": "Table manipulations",
        "explanation": "Use the join node to merge together two tables that share a common column (e.g. an internal id or email address)",
    },
    "aggregation": {
        "displayName": "Group and Aggregate",
        "icon": "fa-object-group",
        "description": "Aggregate values by grouping columns",
        "section": "Table manipulations",
        "explanation": "Use the group and aggregate node to generate summary statistics for groups of rows.",
    },
    "union": {
        "displayName": "Union",
        "icon": "fa-plus-square",
        "description": "Combine two or more tables on top of each other",
        "section": "Table manipulations",
        "explanation": "Use the union node to stack data from multiple input nodes with the same schema.",
    },
    "except": {
        "displayName": "Except",
        "icon": "fa-minus-square",
        "description": "Remove rows that exist in a second table",
        "section": "Table manipulations",
        "explanation": "Use the except node to remove rows that exist in a second table.",
    },
    "sort": {
        "displayName": "Sort",
        "icon": "fa-sort-numeric-up",
        "description": "Sort rows by the values of the specified columns",
        "section": "Table manipulations",
        "explanation": "Use the sort node to sort the rows based on column values.",
    },
    "limit": {
        "displayName": "Limit",
        "icon": "fa-sliders-h-square",
        "description": "Keep a set number of of rows",
        "section": "Table manipulations",
        "explanation": "Use the limit node to choose a fixed number of rows.",
    },
    "filter": {
        "displayName": "Filter",
        "icon": "fa-filter",
        "description": "Filter rows by specified criteria",
        "section": "Table manipulations",
        "explanation": "Use the filter node to filter rows from the input node by a condition.",
    },
    "edit": {
        "displayName": "Edit",
        "icon": "fa-edit",
        "description": "Change a columns value",
        "section": "Column manipulations",
        "explanation": "Use the edit node to transform columns using pre-defined functions",
    },
    "add": {
        "displayName": "Add",
        "icon": "fa-plus",
        "description": "Add new columns to the table",
        "section": "Column manipulations",
        "explanation": "Use the add node to create new columns using pre-built functions.",
    },
    "rename": {
        "displayName": "Rename",
        "icon": "fa-keyboard",
        "description": "Rename columns",
        "section": "Column manipulations",
        "explanation": "Use the rename node to rename the columns from the input node.",
    },
    "text": {
        "displayName": "Text",
        "icon": "fa-text",
        "description": "Annotate your workflow",
        "section": "Annotation",
        "explanation": "",
    },
    "formula": {
        "displayName": "Formula",
        "icon": "fa-function",
        "description": "Add a new column using a formula",
        "section": "Column manipulations",
        "explanation": "Use the formula node to create new columns using spreadsheet-like formulas.",
    },
    "distinct": {
        "displayName": "Distinct",
        "icon": "fa-fingerprint",
        "description": "Select unqiue values from selected columns",
        "section": "Table manipulations",
        "explanation": "Use the distinct node to remove duplicate rows.",
    },
    "pivot": {
        "displayName": "Pivot",
        "icon": "fa-redo-alt",
        "description": "Pivot your table",
        "section": "Table manipulations",
        "explanation": "Use the pivot node to summarise the relationship between two columns.",
    },
    "unpivot": {
        "displayName": "Unpivot",
        "icon": "fa-undo-alt",
        "description": "Unpivot your table",
        "section": "Table manipulations",
        "explanation": "Use the unpivot node to reverse data that is pivoted.",
    },
    "intersect": {
        "displayName": "Intersect",
        "icon": "fa-intersection",
        "description": "Find the common rows between tables",
        "section": "Table manipulations",
        "explanation": "Use the intersect node to only include rows that appear in all the input nodes.",
    },
    "window": {
        "displayName": "Window and Calculate",
        "icon": "fa-window-frame",
        "description": "Calculate analytics over groups without aggregating",
        "section": "Column manipulations",
        "explanation": "Use the window and calculate node to calculate a metric for each row, by looking at other rows in the chosen window.",
    },
    "convert": {
        "displayName": "Convert",
        "icon": "fa-transporter-3",
        "description": "Convert the data types of columns",
        "section": "Column manipulations",
        "explanation": "Use the convert node to change the data type of columns",
    },
}


class WidgetKind(models.TextChoices):
    TEXT = "text", "Text"
    IMAGE = "image", "Image"
    METRIC = "metric", "Metric"
    TABLE = "table", "Table"
    # using fusioncharts name for database
    COLUMN = "mscolumn2d", "Column"
    STACKED_COLUMN = "stackedcolumn2d", "Stacked Column"
    BAR = "msbar2d", "Bar"
    STACKED_BAR = "stackedbar2d", "Stacked Bar"
    LINE = "msline", "Line"
    STACKED_LINE = "msline-stacked", "Stacked Line"
    PIE = "pie2d", "Pie"
    AREA = "msarea", "Area"
    DONUT = "doughnut2d", "Donut"
    SCATTER = "scatter", "Scatter"
    FUNNEL = "funnel", "Funnel"
    RADAR = "radar", "Radar"
    BUBBLE = "bubble", "Bubble"
    HEATMAP = "heatmap", "Heatmap"
    COMBO = "mscombidy2d", "Combination chart"
    IFRAME = "iframe", "iframe"
    GAUGE = "angulargauge", "Gauge"


class WidgetCategory(models.TextChoices):
    CONTENT = "content", "Content"
    SIMPLE = "simple", "Simple charts"
    ADVANCED = "advanced", "Advanced charts"
    COMBO = "combination", "Combination charts"


WIDGET_KIND_TO_WEB = {
    WidgetKind.TEXT.value: ("fa-text", WidgetCategory.CONTENT, "Text"),
    WidgetKind.IMAGE.value: ("fa-image", WidgetCategory.CONTENT, "Image"),
    WidgetKind.IFRAME.value: (
        "fa-browser",
        WidgetCategory.CONTENT,
        "URL Embed",
    ),
    WidgetKind.METRIC.value: ("fa-value-absolute", WidgetCategory.SIMPLE, "Metric"),
    WidgetKind.TABLE.value: ("fa-table", WidgetCategory.SIMPLE, "Table"),
    WidgetKind.COLUMN.value: ("fa-chart-bar", WidgetCategory.SIMPLE, "Column"),
    WidgetKind.STACKED_COLUMN.value: (
        "fa-chart-bar",
        WidgetCategory.ADVANCED,
        "Stacked Column",
    ),
    WidgetKind.BAR.value: ("fa-chart-bar", WidgetCategory.SIMPLE, "Bar"),
    WidgetKind.STACKED_BAR.value: (
        "fa-chart-bar",
        WidgetCategory.ADVANCED,
        "Stacked Bar",
    ),
    WidgetKind.LINE.value: ("fa-chart-line", WidgetCategory.SIMPLE, "Line"),
    WidgetKind.STACKED_LINE.value: (
        "fa-chart-line",
        WidgetCategory.ADVANCED,
        "Stacked Line",
    ),
    WidgetKind.PIE.value: ("fa-chart-pie", WidgetCategory.SIMPLE, "Pie"),
    WidgetKind.AREA.value: ("fa-chart-area", WidgetCategory.ADVANCED, "Area"),
    WidgetKind.DONUT.value: ("fa-dot-circle", WidgetCategory.SIMPLE, "Donut"),
    WidgetKind.SCATTER.value: (
        "fa-chart-scatter",
        WidgetCategory.ADVANCED,
        "Scatter",
    ),
    WidgetKind.FUNNEL.value: ("fa-filter", WidgetCategory.ADVANCED, "Funnel"),
    WidgetKind.RADAR.value: ("fa-radar", WidgetCategory.ADVANCED, "Radar"),
    WidgetKind.BUBBLE.value: ("fa-soap", WidgetCategory.ADVANCED, "Bubble"),
    WidgetKind.HEATMAP.value: ("fa-map", WidgetCategory.ADVANCED, "Heatmap"),
    WidgetKind.COMBO.value: (
        "fa-analytics",
        WidgetCategory.COMBO,
        "Combination chart",
    ),
    WidgetKind.GAUGE.value: ("fa-tachometer-fast", WidgetCategory.SIMPLE, "Gauge"),
}
