from functools import wraps

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse


def _get_decorated_function(view_func, permission_test_function):
    @wraps(view_func)
    def _inner(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return HttpResponseRedirect(
                "{}?next={}".format(reverse("account_login"), request.path)
            )

        if permission_test_function(user, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        else:
            # treat not having access to a team like a 404 to avoid accidentally leaking information
            return render(request, "404.html", status=404)

    return _inner


def login_and_permission_to_access(permission_test_function):
    def decorator(view_func):
        return _get_decorated_function(view_func, permission_test_function)

    return decorator
