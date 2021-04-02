from appconf import AppConf
from django.conf import settings


class SaltAppConf(AppConf):
    MANAGEMENT_URL = "http://localhost"
    MANAGEMENT_USER = __package__
    MANAGEMENT_PASSWORD = None
    MANAGEMENT_PERMISSIONS = [".*"]
    EVENTS_RETRY = 60
    PUBLIC_KEY = """
-----BEGIN PGP PUBLIC KEY BLOCK-----

-----END PGP PUBLIC KEY BLOCK-----
    """
    FILE_STORAGE = settings.DEFAULT_FILE_STORAGE

    class Meta:
        prefix = "salt"
