from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# wrapper for fivetran connector information returned from api
# https://fivetran.com/docs/rest-api/connectors#fields


@dataclass
class FivetranConnectorStatus:
    setup_state: str  # broken | incomplete | connected
    sync_state: str  # scheduled | syncing | paused | rescheduled
    update_state: str  # on_schedule | delayed
    is_historical_sync: bool
    tasks: List[Dict[str, str]]
    warnings: List[Dict[str, str]]

    @property
    def is_syncing(self):
        return self.is_historical_sync or self.sync_state == "syncing"


@dataclass
class FivetranConnector:
    id: str
    group_id: str
    service: str
    service_version: str
    schema: str
    paused: bool
    pause_after_trial: bool
    connected_by: str
    created_at: str
    succeeded_at: Optional[str]
    failed_at: Optional[str]
    sync_frequency: int
    schedule_type: str  # auto | manual
    status: FivetranConnectorStatus
    config: Dict[str, Any]
    daily_sync_time: Optional[int] = None  # only defined if sync_frequency = 1440
    source_sync_details: Dict[str, Any] = None  # only defined for certain connectors

    def __post_init__(self):
        self.status = FivetranConnectorStatus(**self.status)
        # timezone (UTC) information is parsed automatically
        if self.succeeded_at is not None:
            self.succeeded_at = datetime.strptime(
                self.succeeded_at, "%Y-%m-%dT%H:%M:%S.%f%z"
            )
        if self.failed_at is not None:
            self.failed_at = datetime.strptime(self.failed_at, "%Y-%m-%dT%H:%M:%S.%f%z")
