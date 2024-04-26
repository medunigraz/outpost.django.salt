from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _


class DefaultConfig(AppConfig):
    name = "outpost.django.salt"

    def ready(self):
        from .conf import settings

        if not settings.SALT_MANAGEMENT_PASSWORD:
            raise ImproperlyConfigured(
                _("No management password set for Salt API authentication")
            )
