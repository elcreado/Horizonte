"""Límites de ventana fija compartidos por procesos mediante PostgreSQL."""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from rest_framework.throttling import UserRateThrottle

from .models import RateLimitBucket


class PersistentUserThrottle(UserRateThrottle):
    def allow_request(self, request, view):
        if self.rate is None:
            return True
        identity = (
            f"user:{request.user.pk}"
            if request.user.is_authenticated
            else f"ip:{self.get_ident(request)}"
        )
        key = salted_hmac(
            "horizonte.rate-limit", f"{self.scope}:{identity}", algorithm="sha256"
        ).hexdigest()
        now = timezone.now()
        with transaction.atomic():
            RateLimitBucket.objects.get_or_create(
                key=key, defaults={"expires_at": now + timedelta(seconds=self.duration)}
            )
            bucket = RateLimitBucket.objects.select_for_update().get(key=key)
            if bucket.expires_at <= now:
                bucket.requests = 0
                bucket.expires_at = now + timedelta(seconds=self.duration)
            self.remaining_wait = max(0, (bucket.expires_at - now).total_seconds())
            if bucket.requests >= self.num_requests:
                return False
            bucket.requests += 1
            bucket.save(update_fields=["requests", "expires_at"])
        return True

    def wait(self):
        return self.remaining_wait
