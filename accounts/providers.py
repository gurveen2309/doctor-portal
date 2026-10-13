from typing import Protocol, runtime_checkable

from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


class Delivery(Protocol):
    def deliver(self, phone: str, code: str) -> None: ...


@runtime_checkable
class ProductionDelivery(Delivery, Protocol):
    def validate_configuration(self) -> None: ...


def provider_from_path(path: str) -> ProductionDelivery:
    if not path or path.startswith(("tests.", "test", "django.core.mail.backends.console")):
        raise ImproperlyConfigured("A real patient OTP delivery adapter must be configured.")
    try:
        instance = import_string(path)()
    except (ImportError, AttributeError) as error:
        raise ImproperlyConfigured("The patient OTP delivery adapter cannot be loaded.") from error
    if not isinstance(instance, ProductionDelivery):
        raise ImproperlyConfigured("The OTP adapter needs deliver and offline validate_configuration methods.")
    instance.validate_configuration()
    return instance
