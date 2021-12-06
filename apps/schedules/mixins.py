class ScheduleMixin:
    @property
    def _schedule(self):
        return (
            self.integration if hasattr(self, "integration") else self
        ).project.schedule

    @property
    def up_to_date(self):

        latest = self._schedule.latest_schedule

        just_failed = self.failed_at is not None and self.failed_at > latest
        just_succeeded = self.succeeded_at is not None and self.succeeded_at > latest

        return just_failed or just_succeeded

    @property
    def schedule_status(self):

        if self.succeeded_at is None:
            return "incomplete"
        if self.is_scheduled is None:
            return "paused"
        if self.failed_at is not None and self.failed_at > self.succeeded_at:
            return "broken"

        return "active"
