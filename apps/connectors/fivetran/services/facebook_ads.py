from itertools import chain

FIELDS = [
    "account_id",
    "account_name",
    "action_values",
    "actions",
    "ad_id",
    "ad_name",
    "adset_id",
    "adset_name",
    "buying_type",
    "campaign_id",
    "campaign_name",
    "canvas_avg_view_percent",
    "canvas_avg_view_time",
    "clicks",
    "cost_per_10_sec_video_view",
    "cost_per_action_type",
    "cost_per_inline_link_click",
    "cost_per_inline_post_engagement",
    "cost_per_outbound_click",
    "cost_per_unique_action_type",
    "cost_per_unique_click",
    "cost_per_unique_inline_link_click",
    "cost_per_unique_outbound_click",
    "cpc",
    "cpm",
    "cpp",
    "ctr",
    "frequency",
    "gender_targeting",
    "impressions",
    "inline_link_click_ctr",
    "inline_link_clicks",
    "inline_post_engagement",
    "labels",
    "location",
    "mobile_app_purchase_roas",
    "objective",
    "outbound_clicks",
    "outbound_clicks_ctr",
    "reach",
    "relevance_score",
    "social_spend",
    "spend",
    "unique_actions",
    "unique_clicks",
    "unique_ctr",
    "unique_inline_link_click_ctr",
    "unique_inline_link_clicks",
    "unique_link_clicks_ctr",
    "unique_outbound_clicks",
    "unique_outbound_clicks_ctr",
    "video_10_sec_watched_actions",
    "video_30_sec_watched_actions",
    "video_avg_percent_watched_actions",
    "video_avg_time_watched_actions",
    "video_p100_watched_actions",
    "video_p25_watched_actions",
    "video_p50_watched_actions",
    "video_p75_watched_actions",
    "video_p95_watched_actions",
    "website_ctr",
    "website_purchase_roas",
    "purchase_roas",
    "conversion_rate_ranking",
    "conversion_values",
    "conversions",
    "cost_per_conversion",
    "cost_per_estimated_ad_recallers",
    "cost_per_thruplay",
    "engagement_rate_ranking",
    "estimated_ad_recall_rate",
    "estimated_ad_recallers",
    "full_view_impressions",
    "full_view_reach",
    "instant_experience_clicks_to_open",
    "instant_experience_clicks_to_start",
    "instant_experience_outbound_clicks",
    "quality_ranking",
    "video_play_actions",
    "video_play_curve_actions",
    "video_thruplay_watched_actions",
]

BREAKDOWNS = [
    "ad_format_asset",
    "age",
    "body_asset",
    "call_to_action_asset",
    "country",
    "description_asset",
    "dma",
    "gender",
    "frequency_value",
    "hourly_stats_aggregated_by_advertiser_time_zone",
    "hourly_stats_aggregated_by_audience_time_zone",
    "image_asset",
    "impression_device",
    "link_url_asset",
    "place_page_id",
    "device_platform",
    "product_id",
    "publisher_platform",
    "platform_position",
    "region",
    "title_asset",
    "video_asset",
]

ACTION_BREAKDOWNS = [
    "action_carousel_card_id",
    "action_carousel_card_name",
    "action_canvas_component_name",
    "action_destination",
    "action_device",
    "action_reaction",
    "action_target_id",
    "action_type",
    "action_video_sound",
    "action_video_type;",
]

PREBUILT_REPORTS = [
    "ACTION_CANVAS_COMPONENT",
    "ACTION_CAROUSEL_CARD",
    "ACTION_CONVERSION_DEVICE",
    "ACTION_PRODUCT_ID",
    "ACTION_REACTIONS",
    "ACTION_VIDEO_SOUND",
    "ACTION_VIDEO_VIEW_TYPE",
    "BASIC_AD",
    "BASIC_AD_SET",
    "BASIC_ALL_LEVELS",
    "BASIC_CAMPAIGN",
    "DELIVERY_PLACEMENT",
    "DELIVERY_PLACEMENT_AND_DEVICE",
    "DELIVERY_PLATFORM",
    "DELIVERY_PLATFORM_AND_DEVICE",
    "DELIVERY_PURCHASE_ROAS",
    "DEMOGRAPHICS_AGE",
    "DEMOGRAPHICS_AGE_AND_GENDER",
    "DEMOGRAPHICS_COUNTRY",
    "DEMOGRAPHICS_DMA_REGION",
    "DEMOGRAPHICS_GENDER",
    "DEMOGRAPHICS_REGION",
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


SECONDARY_TABLES = [
    "actions",
    "action_values",
    "inline_link_clicks",
    "outbound_clicks",
    "website_purchase_roas",
    "mobile_app_purchase_roas",
    "purchase_roas",
]

BASIC_REPORTS = {
    "BASIC_AD_PERFORMANCE": {
        "name": "Ad performance by day",
        "description": "CPC, CPM, CPP, CTR",
        "config": {
            "table_name": "basic_ads_performance",
            "fields": ["ad_id", "ad_name", "cpc", "cpm", "cpp", "ctr"],
            "breakdowns": [],
            "action_breakdowns": [],
            "aggregation": "Day",
            "action_report_time": "impression",
            "click_attribution_window": "DAY_7",
            "view_attribution_window": "DAY_1",
            "use_unified_attribution_setting": True,
        },
    },
    "BASIC_ADSET_PERFORMANCE": {
        "name": "Ad Set performance by day",
        "description": "CPC, CPM, CPP, CTR",
        "config": {
            "table_name": "basic_adset_performance",
            "fields": ["adset_id", "adset_name", "cpc", "cpm", "cpp", "ctr"],
            "breakdowns": [],
            "action_breakdowns": [],
            "aggregation": "Day",
            "action_report_time": "impression",
            "click_attribution_window": "DAY_7",
            "view_attribution_window": "DAY_1",
            "use_unified_attribution_setting": True,
        },
    },
    "BASIC_CAMPAIGN_PERFORMANCE": {
        "name": "Campaign performance by day",
        "description": "CPC, CPM, CPP, CTR",
        "config": {
            "table_name": "basic_campaign_performance",
            "fields": ["campaign_id", "campaign_name", "cpc", "cpm", "cpp", "ctr"],
            "breakdowns": [],
            "action_breakdowns": [],
            "aggregation": "Day",
            "action_report_time": "impression",
            "click_attribution_window": "DAY_7",
            "view_attribution_window": "DAY_1",
            "use_unified_attribution_setting": True,
        },
    },
}

BASIC_REPORTS_CHOICES = [
    (k, f'{v["name"]}: {v["description"]}') for k, v in BASIC_REPORTS.items()
]


def _get_table_ids_for_report(name):
    return [name] + [
        f"{name}_{secondary_table}" for secondary_table in SECONDARY_TABLES
    ]


def get_enabled_table_ids_for_facebook_ads(enabled_tables):
    table_ids = [
        _get_table_ids_for_report(table.name_in_destination) for table in enabled_tables
    ]
    return set(chain.from_iterable(table_ids))
