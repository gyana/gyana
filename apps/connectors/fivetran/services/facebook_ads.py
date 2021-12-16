from itertools import chain

ACTION_FIELDS = [
    "inline_link_clicks",
    "outbound_clicks",
    "website_purchase_roas",
    "mobile_app_purchase_roas",
]

ACTION_VIDEO_FIELDS = [
    "video_thruplay_watched_actions",
    "video_30_sec_watched_actions",
    "video_p25_watched_actions",
    "video_p50_watched_actions",
    "video_p75_watched_actions",
    "video_p100_watched_actions",
    "video_avg_time_watched_actions",
]

COMMON_FIELDS = [
    "reach",
    "impressions",
    "frequency",
    "spend",
    "cpm",
    "cpc",
    "ctr",
    "inline_link_clicks",
    "actions",
    "cost_per_action_type",
]


PREBUILT_REPORTS = {
    "delivery_purchase_roas": {
        "fields": [],
        "breakdowns": [],
        "action_breakdowns": ACTION_FIELDS,
    }
}


def _get_table_ids_for_report(name):
    return [name] + [
        f"{name}_{field}"
        for field in (PREBUILT_REPORTS.get(name, {}).get("action_breakdowns", []))
    ]


def get_enabled_table_ids_for_facebook_ads(enabled_tables):
    table_ids = [
        _get_table_ids_for_report(table.name_in_destination) for table in enabled_tables
    ]
    return set(chain.from_iterable(table_ids))
