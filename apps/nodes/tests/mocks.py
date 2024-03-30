from datetime import date

TABLE_NAME = "`project.dataset`.table"
POSITIVE_SCORE = +0.9
NEGATIVE_SCORE = -0.9

USAIN = "Usain Bolt"
SAKURA = "Sakura Yosozumi"
SENTIMENT_LOOKUP = {
    SAKURA: POSITIVE_SCORE,
    USAIN: NEGATIVE_SCORE,
}  # cache as creating mocks is expensive


INPUT_QUERY = f"SELECT\n  t0.*\nFROM {TABLE_NAME} AS t0"
DEFAULT_X_Y = {"x": 0, "y": 0}


INPUT_DATA = [
    {
        "id": 1,
        "athlete": USAIN,
        "birthday": date(year=1986, month=8, day=21),
    },
    {
        "id": 2,
        "athlete": SAKURA,
        "birthday": date(year=2002, month=3, day=15),
    },
]

DISTINCT_QUERY = "SELECT\n  t0.*\nFROM (\n  SELECT t1.`athlete` AS `text`\n  FROM (\n    SELECT DISTINCT t2.`athlete`\n    FROM `project.dataset.table` AS t2\n  ) t1\n) AS t0\nWHERE NOT t0.`text` IS NULL"
