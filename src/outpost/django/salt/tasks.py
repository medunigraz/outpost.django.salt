import logging
from datetime import timedelta

import requests
from celery.task import PeriodicTask, Task

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

class RunCommandTask(Task):
    pass
