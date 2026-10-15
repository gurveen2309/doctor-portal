from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AuditQuerySet(models.QuerySet["AuditEvent"]):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Audit events are append-only.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Audit events are append-only.")


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=64)
    record_type = models.CharField(max_length=64)
    record_id = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = AuditQuerySet.as_manager()

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ValidationError("Audit events are append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Audit events are append-only.")
