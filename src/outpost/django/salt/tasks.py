import logging
from datetime import timedelta

import requests
from django.core.exceptions import ObjectDoesNotExist
from celery.task import PeriodicTask, Task
from purl import URL

from .conf import settings

logger = logging.getLogger(__name__)


class CleanUsersTask(PeriodicTask):
    run_every = timedelta(minutes=5)

    def run(self, **kwargs):
        from .models import User

        for u in User.objects.all():
            try:
                str(u.person)
            except ObjectDoesNotExist:
                if u.active:
                    logger.info(f"Deactivating {u._meta.label} with PK {u.pk}")
                    u.active = False
                    u.save()
            else:
                if not u.active:
                    logger.info(f"Reactivating {u._meta.label} with PK {u.pk}")
                    u.active = True
                    u.save()


class RunCommandTask(Task):
    def __init__(self, *args, **kwargs):
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def run(self, **kwargs):
        url = URL(settings.SALT_MANAGEMENT_URL)
        kwargs.update(
            {
                "username": settings.SALT_MANAGEMENT_USER,
                "password": settings.SALT_MANAGEMENT_PASSWORD,
                "eauth": "rest",
                "client": "local",
            }
        )
        try:
            logger.debug(f"Posting task with data to Salt API: {kwargs}")
            result = self.session.post(
                url.add_path_segment("run").as_string(), data=kwargs
            )
            result.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to run task through Salt API: {e}")
            return
        logger.debug(f"Scheduled job through Salt API: {result.text}")
        return result.json()
