import os

from appconf import AppConf
from django.conf import settings


class SaltAppConf(AppConf):
    MANAGEMENT_URL = 'http://localhost'
    MANAGEMENT_USER = __package__
    MANAGEMENT_KEY = 'salt:management_password'
    MANAGEMENT_PERMISSIONS = ['.*']

    class Meta:
        prefix = 'salt'
