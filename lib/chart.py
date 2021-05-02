import json
from typing import Any

import pandas as pd

from lib.fusioncharts import FusionCharts

DEFAULT_WIDTH = "100%"
DEFAULT_HEIGHT = "400"


def to_chart(df: pd.DataFrame, name: str, config: Any) -> FusionCharts:

    """Render a chart from a table."""

    dataSource = {
        "chart": {"theme": "fusion", **json.loads(config)},
        "data": df.to_dict(orient="records"),
    }

    return FusionCharts(
        "column2d",
        name,
        DEFAULT_WIDTH,
        DEFAULT_HEIGHT,
        f"{name}-container",
        "json",
        dataSource,
    )
