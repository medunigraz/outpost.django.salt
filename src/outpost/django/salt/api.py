from collections import defaultdict

from django.contrib.auth import authenticate, login
from django.core.cache import cache
from rest_framework import exceptions, permissions, viewsets
from rest_framework.response import Response

from outpost.django.api.permissions import ExtendedDjangoModelPermissions

from . import models, serializers
from .conf import settings


class HostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Host.objects.all()
    serializer_class = serializers.HostSerializer
    permission_classes = (permissions.IsAuthenticated, ExtendedDjangoModelPermissions)


class AuthenticateViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    def create(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if username == settings.SALT_MANAGEMENT_USER:
            if password == settings.SALT_MANAGEMENT_PASSWORD:
                return Response(settings.SALT_MANAGEMENT_PERMISSIONS)
            else:
                raise exceptions.AuthenticationFailed()
        user = authenticate(request, username=username, password=password)
        if not user:
            raise exceptions.AuthenticationFailed()
        perms = defaultdict(list)
        for p in models.Permission.objects.filter(user=user):
            for h in p.system.host_set.all():
                perms[h.name].append(p.function)
        eauth = perms.get(None, [])
        eauth.extend([{k: v} for k, v in perms.items() if k])
        return Response(eauth)
