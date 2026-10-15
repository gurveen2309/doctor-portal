from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection

from tests.test_otp import MemoryDelivery


@pytest.mark.django_db(transaction=True)
def test_one_otp_code_cannot_establish_two_sessions_concurrently() -> None:
    from accounts.services import request_otp, verify_otp

    assert connection.vendor == "postgresql"
    delivery = MemoryDelivery()
    challenge = request_otp("+919000000002", "127.0.0.1", delivery=delivery)
    code = delivery.codes[0][1]
    barrier = Barrier(2)

    def verify() -> str:
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                verify_otp(challenge.pk, code)
            except ValidationError:
                return "rejected"
            return "accepted"
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: verify(), range(2)))
    assert sorted(outcomes) == ["accepted", "rejected"]
