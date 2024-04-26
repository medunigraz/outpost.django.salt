import logging
from datetime import timedelta

import requests
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from purl import URL

from .conf import settings

logger = logging.getLogger(__name__)


class UserTasks:
    run_every = timedelta(minutes=5)

    @shared_task(bind=True, ignore_result=True, name=f"{__name__}.User:cleanup")
    def cleanup(task):
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


class CommandTasks:
    @shared_task(bind=True, ignore_result=True, name=f"{__name__}.Command:run")
    def run(task, **kwargs):
        session = requests.Session()
        session.headers.update({"Accept": "application/json"})
        url = URL(settings.SALT_MANAGEMENT_URL)
        kwargs.update(
            {
                "username": settings.SALT_MANAGEMENT_USER,
                "password": settings.SALT_MANAGEMENT_PASSWORD,
                "eauth": "rest",
                "client": "local_async",
            }
        )
        try:
            logger.debug(f"Posting task with data to Salt API: {kwargs}")
            result = session.post(url.add_path_segment("run").as_string(), json=kwargs)
            result.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to run task through Salt API: {e}")
            return
        logger.debug(f"Scheduled job through Salt API: {result.text}")
        return result.json()
