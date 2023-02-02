PLANS = {
    "free": {"name": "Free", "projects": 3, "rows_per_integration": 100_000},
    "pro": {
        "name": "Pro",
        "projects": -1,
        "custom_branding": True,
        "rows": 10_000_000,
        "credits": 10_000,
        "rows_per_integration": 10_000_000,
    },
    # todo: convert to agency plan
    "business": {
        "name": "Business",
        "projects": -1,
        "custom_branding": True,
        "sub_accounts": -1,
        "rows": 10_000_000,
        "credits": 100_000,
        "cnames": -1,
        "white_labeling": True,
    },
}
