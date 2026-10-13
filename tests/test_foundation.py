import importlib
import importlib.util
import json
import sys
import tomllib
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_runtime_settings(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    assert importlib.util.find_spec("config") is not None, "Django runtime configuration is not implemented"
    assert (ROOT / "config" / "settings.py").is_file(), "Django settings are not implemented"
    monkeypatch.setenv("DJANGO_ENV", "test")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "synthetic-test-only-secret-not-valid-for-production")
    monkeypatch.setenv("POSTGRES_DB", "doctor_portal_test")
    monkeypatch.setenv("POSTGRES_USER", "doctor_portal_test")
    monkeypatch.setenv("POSTGRES_PASSWORD", "synthetic-test-only")
    monkeypatch.setenv("POSTGRES_HOST", "127.0.0.1")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.delitem(sys.modules, "config.settings", raising=False)
    return importlib.import_module("config.settings")


def test_runtime_uses_clinic_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = load_runtime_settings(monkeypatch)
    assert runtime.TIME_ZONE == "Asia/Kolkata"


def test_runtime_uses_aware_datetimes(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = load_runtime_settings(monkeypatch)
    assert runtime.USE_TZ is True


def test_runtime_uses_postgresql(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = load_runtime_settings(monkeypatch)
    assert runtime.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert runtime.DATABASES["default"]["NAME"] == "doctor_portal_test"


def test_openspec_is_pinned_locally_with_telemetry_disabled() -> None:
    manifest = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert manifest["private"] is True
    assert manifest["devDependencies"]["@fission-ai/openspec"] == "1.14.1"
    for name, command in manifest["scripts"].items():
        if name == "spec" or name.startswith("spec:"):
            assert command.startswith("OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1 openspec")


def test_python_formatters_follow_approved_preferences() -> None:
    with (ROOT / "pyproject.toml").open("rb") as source:
        manifest = tomllib.load(source)
    assert manifest["tool"]["black"]["line-length"] == 120
    assert manifest["tool"]["isort"]["profile"] == "black"
    assert manifest["tool"]["isort"]["line_length"] == 120


def test_missing_secret_is_not_replaced(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = load_runtime_settings(monkeypatch)
    from django.core.exceptions import ImproperlyConfigured

    monkeypatch.delenv("DJANGO_SECRET_KEY")
    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        runtime.environment_settings()


def test_missing_database_is_not_replaced(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = load_runtime_settings(monkeypatch)
    from django.core.exceptions import ImproperlyConfigured

    monkeypatch.delenv("POSTGRES_DB")
    with pytest.raises(ImproperlyConfigured, match="POSTGRES_DB"):
        runtime.environment_settings()


def test_production_checks_expose_missing_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    load_runtime_settings(monkeypatch)
    assert (ROOT / "config" / "checks.py").is_file(), "Production gates are not implemented"
    from config.checks import production_errors

    errors = production_errors(
        {
            "ENVIRONMENT": "production",
            "SECRET_KEY": "short",
            "DEBUG": True,
            "ALLOWED_HOSTS": [],
            "SECURE_SSL_REDIRECT": False,
            "SESSION_COOKIE_SECURE": False,
            "CSRF_COOKIE_SECURE": False,
            "PATIENT_OTP_PROVIDER": "",
            "LIVE_DATA_APPROVED": False,
        }
    )
    assert {error.id for error in errors} == {
        "portal.E001",
        "portal.E002",
        "portal.E003",
        "portal.E004",
        "portal.E005",
    }
