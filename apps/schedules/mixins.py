from enum import Enum


class ScheduleStatus(Enum):
    PAUSED = "paused"
    INCOMPLETE = "incomplete"
    BROKEN = "broken"
    ACTIVE = "active"


class RunStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"


class ScheduleMixin:
    @property
    def _schedule(self):
        return (
            self.integration if hasattr(self, "integration") else self
        ).project.schedule

    @property
    def up_to_date(self):

        latest = self._schedule.run_started_at

        if latest is None:
            return True

        just_failed = self.failed_at and self.failed_at > latest
        just_succeeded = self.succeeded_at and self.succeeded_at > latest

        return just_failed or just_succeeded

    @property
    def run_status(self):

        run_started_at = self._schedule.run_started_at

        if run_started_at is None:
            return RunStatus.DONE.value

        just_failed = self.failed_at and self.failed_at > run_started_at
        just_succeeded = self.succeeded_at and self.succeeded_at > run_started_at

        if just_failed or just_succeeded:
            return RunStatus.DONE.value

        if (
            hasattr(self, "fivetran_sync_started")
            and self.fivetran_sync_started
            and self.fivetran_sync_started > run_started_at
        ):
            return RunStatus.RUNNING.value

        return RunStatus.PENDING.value

    @property
    def schedule_status(self):

        if self.succeeded_at is None:
            return ScheduleStatus.INCOMPLETE.value
        if not self.is_scheduled:
            return ScheduleStatus.PAUSED.value
        if self.failed_at is not None and self.failed_at > self.succeeded_at:
            return ScheduleStatus.BROKEN.value
        return ScheduleStatus.ACTIVE.value
