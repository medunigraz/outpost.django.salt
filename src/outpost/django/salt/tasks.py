import logging
import secrets
from datetime import timedelta

import requests
from celery.task import (
    PeriodicTask,
    Task,
)
from django.core.cache import cache

from .conf import settings

logger = logging.getLogger(__name__)


class RefreshPasswordTask(PeriodicTask):
    run_every = timedelta(minutes=10)

    def run(self, **kwargs):
        with cache.lock(settings.SALT_MANAGEMENT_KEY):
            new = secrets.token_hex()
            cache.set(
                settings.SALT_MANAGEMENT_KEY,
                new
            )
        return new

class RunCommandTask(Task):
    pass
