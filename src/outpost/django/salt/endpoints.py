from . import api

v1 = [
    (r"salt/authenticate", api.AuthenticateViewSet, "salt-authenticate"),
    (r"salt/host", api.HostViewSet, "salt-host"),
    (r"salt/file", api.FileViewSet, "salt-file"),
    (r"salt/publickey", api.PublicKeyViewSet, "salt-publickey"),
]
