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


globals().update(environment_settings())
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
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
