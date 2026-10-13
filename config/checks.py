from typing import Any

from django.conf import settings
from django.core.checks import Error, register


def production_errors(values: dict[str, Any]) -> list[Error]:
    if values["ENVIRONMENT"] != "production":
        return []
    errors = []
    if len(values["SECRET_KEY"]) < 50:
        errors.append(Error("Configure a production secret of at least 50 characters.", id="portal.E001"))
    if values["DEBUG"] or not values["ALLOWED_HOSTS"] or "*" in values["ALLOWED_HOSTS"]:
        errors.append(Error("Production needs debug disabled and explicit allowed hosts.", id="portal.E002"))
    if not all(values[key] for key in ("SECURE_SSL_REDIRECT", "SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE")):
        errors.append(Error("Production requires HTTPS and secure cookies.", id="portal.E003"))
    if not values["PATIENT_OTP_PROVIDER"]:
        errors.append(Error("A real patient OTP provider must be onboarded.", id="portal.E004"))
    if not values["LIVE_DATA_APPROVED"]:
        errors.append(Error("Live-data legal, privacy, practice and restore gates are not approved.", id="portal.E005"))
    return errors


@register()
def check_production(app_configs: Any, **kwargs: Any) -> list[Error]:
    keys = (
        "ENVIRONMENT",
        "SECRET_KEY",
        "DEBUG",
        "ALLOWED_HOSTS",
        "SECURE_SSL_REDIRECT",
        "SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE",
        "PATIENT_OTP_PROVIDER",
        "LIVE_DATA_APPROVED",
    )
    return production_errors({key: getattr(settings, key) for key in keys})
