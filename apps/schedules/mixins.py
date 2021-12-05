class ScheduleMixin:
    @property
    def _project(self):
        return (
            self.integration.project if hasattr(self, "integration") else self.project
        )

    @property
    def up_to_date(self):

        latest = self._project.latest_schedule

        just_failed = self.failed_at is not None and self.failed_at > latest
        just_succeeded = self.succeeded_at is not None and self.succeeded_at > latest

        return just_failed or just_succeeded

    def run_for_schedule(self):
        raise NotImplementedError

    @property
    def succeeded(self):
        return self.succeeded_at is not None and (
            self.failed_at is None or self.succeeded_at > self.failed_at
        )
