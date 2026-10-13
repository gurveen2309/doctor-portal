from django.db.models import Model

from accounts.models import Account
from audit.models import AuditEvent


def record(actor: Account, action: str, entity: Model) -> AuditEvent:
    return AuditEvent.objects.create(
        actor=actor, action=action, record_type=entity._meta.label_lower, record_id=str(entity.pk)
    )
