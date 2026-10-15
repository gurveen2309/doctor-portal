import os
from pathlib import Path
from typing import Any

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"{name} must be configured explicitly")
    return value


def environment_settings() -> dict[str, Any]:
    environment = required("DJANGO_ENV")
    if environment not in {"development", "test", "production"}:
        raise ImproperlyConfigured("DJANGO_ENV must be development, test or production")
    production = environment == "production"
    return {
        "ENVIRONMENT": environment,
        "SECRET_KEY": required("DJANGO_SECRET_KEY"),
        "DEBUG": environment == "development",
        "ALLOWED_HOSTS": os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(","),
        "DATABASES": {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": required("POSTGRES_DB"),
                "USER": required("POSTGRES_USER"),
                "PASSWORD": required("POSTGRES_PASSWORD"),
                "HOST": required("POSTGRES_HOST"),
                "PORT": required("POSTGRES_PORT"),
            }
        },
        "SECURE_SSL_REDIRECT": production,
        "SESSION_COOKIE_SECURE": production,
        "CSRF_COOKIE_SECURE": production,
        "SECURE_HSTS_SECONDS": 31536000 if production else 0,
        "SECURE_HSTS_INCLUDE_SUBDOMAINS": production,
        "SECURE_HSTS_PRELOAD": production,
        "PATIENT_OTP_PROVIDER": os.environ.get("PATIENT_OTP_PROVIDER", ""),
        "LIVE_DATA_APPROVED": os.environ.get("LIVE_DATA_APPROVED") == "yes",
    }


_environment = environment_settings()
ENVIRONMENT: str = _environment["ENVIRONMENT"]
SECRET_KEY: str = _environment["SECRET_KEY"]
DEBUG: bool = _environment["DEBUG"]
ALLOWED_HOSTS: list[str] = _environment["ALLOWED_HOSTS"]
DATABASES: dict[str, Any] = _environment["DATABASES"]
SECURE_SSL_REDIRECT: bool = _environment["SECURE_SSL_REDIRECT"]
SESSION_COOKIE_SECURE: bool = _environment["SESSION_COOKIE_SECURE"]
CSRF_COOKIE_SECURE: bool = _environment["CSRF_COOKIE_SECURE"]
SECURE_HSTS_SECONDS: int = _environment["SECURE_HSTS_SECONDS"]
SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = _environment["SECURE_HSTS_INCLUDE_SUBDOMAINS"]
SECURE_HSTS_PRELOAD: bool = _environment["SECURE_HSTS_PRELOAD"]
PATIENT_OTP_PROVIDER: str = _environment["PATIENT_OTP_PROVIDER"]
LIVE_DATA_APPROVED: bool = _environment["LIVE_DATA_APPROVED"]
TIME_ZONE = "Asia/Kolkata"
USE_TZ = True
LANGUAGE_CODE = "en-in"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
INSTALLED_APPS = [
    "config.apps.RuntimeConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "accounts",
    "patients",
    "audit",
    "clinic",
    "intake",
    "appointments",
    "clinical",
    "operations",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
AUTH_USER_MODEL = "accounts.Account"
DEFAULT_EXCEPTION_REPORTER_FILTER = "config.reporting.PrivateReportFilter"
DEFAULT_EXCEPTION_REPORTER = "config.reporting.PrivateExceptionReporter"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "private_event": {"()": "config.reporting.PrivateLogFilter"},
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "filters": ["private_event"]},
        "mail_admins": {
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false", "private_event"],
        },
    },
    "loggers": {
        "django": {"handlers": ["console", "mail_admins"], "level": "INFO"},
        "django.request": {"filters": ["private_event"]},
        "django.server": {"handlers": ["console"], "filters": ["private_event"], "propagate": False},
    },
}
