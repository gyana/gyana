from honeybadger import honeybadger


class HoneybadgerUserContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            honeybadger.set_context(
                user_id=request.user.id, user_email=request.user.email
            )
        return self.get_response(request)
