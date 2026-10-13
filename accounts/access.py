from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

from accounts.models import Account


def request_actor(request: HttpRequest) -> Account:
    if not isinstance(request.user, Account) or not request.user.is_active:
        raise PermissionDenied("Sign-in is required.")
    return request.user
