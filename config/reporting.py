import logging
from collections.abc import ItemsView
from types import FrameType
from typing import Any

from django.http import HttpRequest
from django.views.debug import ExceptionReporter, SafeExceptionReporterFilter


class PrivateReportFilter(SafeExceptionReporterFilter):
    def get_post_parameters(self, request: HttpRequest | None) -> dict[str, str]:
        return {}

    def get_safe_request_meta(self, request: HttpRequest | None) -> dict[str, str]:
        return {}

    def get_safe_cookies(self, request: HttpRequest | None) -> dict[str, str]:
        return {}

    def get_traceback_frame_variables(self, request: HttpRequest | None, tb_frame: FrameType) -> ItemsView[str, Any]:
        return {name: self.cleansed_substitute for name in tb_frame.f_locals}.items()


class PrivateExceptionReporter(ExceptionReporter):
    def get_traceback_data(self) -> dict[str, Any]:
        data = super().get_traceback_data()
        data.update(
            exception_value="Details withheld to protect authentication and clinical data.",
            exception_notes="",
            unicode_hint="",
            user_str="[withheld]",
            request=None,
            request_GET_items=[],
            request_FILES_items=[],
            request_insecure_uri="[withheld]",
            template_info=None,
            template_does_not_exist=False,
            postmortem=None,
        )
        for frame in data["frames"]:
            frame["exc_cause"] = None
            frame["exc_cause_explicit"] = False
        return data


class RedactedApplicationError(Exception):
    pass


class PrivateLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if getattr(record, "_portal_redacted", False):
            return True
        record._portal_redacted = True
        record.msg = "Application event: %s, HTTP status %s"
        record.args = (record.levelname, getattr(record, "status_code", "unavailable"))
        if record.exc_info:
            exc_type, _, traceback = record.exc_info
            error = RedactedApplicationError(f"{exc_type.__name__ if exc_type else 'Exception'}: details withheld")
            record.exc_info = (RedactedApplicationError, error, traceback)
        record.exc_text = None
        record.stack_info = None
        return True
