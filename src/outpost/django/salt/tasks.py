import logging
import secrets
from datetime import timedelta

import requests
from celery.task import PeriodicTask, Task
from django.core.cache import cache

from .conf import settings
from .models import User, Person, Student

logger = logging.getLogger(__name__)


class CleanUsersTask(PeriodicTask):
    run_every = timedelta(minutes=5)

    def run(self, **kwargs):
        for u in User.objects.all():
            try:
                u.person
            except (Person.DoesNotExist, Student.DoesNotExist) as e:
                logger.warn(f"Removing {u._meta.label} with PK {u.pk} because of {e}")
                u.delete()


class RefreshPasswordTask(PeriodicTask):
    run_every = timedelta(minutes=10)

    def run(self, **kwargs):
        with cache.lock(settings.SALT_MANAGEMENT_KEY):
            new = secrets.token_hex()
            cache.set(settings.SALT_MANAGEMENT_KEY, new)
        return new


class RunCommandTask(Task):
    pass
