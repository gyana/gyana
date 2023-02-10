import logging

from honeybadger import honeybadger

# todo: understand behaviour of htmx for 500 in production


class TurboFrame500Mixin:
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as exc:
            honeybadger.notify(exc)
            logging.error(exc, exc_info=exc)
            return (
                self.get_turbo_frame()
                .template("components/frame_error.html", {"error": exc})
                .response(self.request)
            )
