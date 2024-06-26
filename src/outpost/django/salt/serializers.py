import logging

# import gpg
from rest_framework import serializers

from . import models
from .conf import settings

logger = logging.getLogger(__name__)


# class PGPFileField(serializers.Field):
#     def to_representation(self, value):
#         with gpg.Context(armor=True) as c:
#             imp = c.key_import(settings.SALT_PUBLIC_KEY.encode("ascii"))
#             if not isinstance(imp, gpg.results.ImportResult):
#                 logger.error("Could not import Saltstack public GPG key.")
#                 return
#             keys = [c.get_key(k.fpr) for k in imp.imports]
#             crypt, result, _ = c.encrypt(
#                 value.read(), keys, sign=False, always_trust=True
#             )
#         return crypt


class PublicKeySerializer(serializers.ModelSerializer):
    fingerprint = serializers.CharField(read_only=True)

    class Meta:
        model = models.PublicKey
        fields = ("fingerprint", "key", "openssh")


class GroupSerializer(serializers.ModelSerializer):
    gid = serializers.IntegerField(source="pk")

    class Meta:
        model = models.Group
        fields = ("gid", "name")


class SystemUserActiveFilterListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        return super().to_representation(data.filter(user__active=True))


class SystemUserSerializer(serializers.ModelSerializer):
    uid = serializers.IntegerField(source="user.pk")
    username = serializers.CharField(source="user.person.username")
    displayname = serializers.CharField(source="user.displayname")
    homedir = serializers.SerializerMethodField()
    groups = GroupSerializer(many=True)
    public_keys = PublicKeySerializer(source="user.publickey_set.all", many=True)
    directories = serializers.SerializerMethodField()

    class Meta:
        model = models.SystemUser
        list_serializer_class = SystemUserActiveFilterListSerializer
        fields = (
            "uid",
            "username",
            "displayname",
            "homedir",
            "shell",
            "groups",
            "sudo",
            "public_keys",
            "directories",
        )

    def get_homedir(self, o):
        return o.system.home_template.format(username=o.user.person.username)

    def get_directories(self, o):
        for d in o.system.userdirectory_set.all():
            yield {
                "path": d.template.replace("{username}", o.user.person.username),
                "permissions": d.permissions,
            }


class SystemFileSerializer(serializers.ModelSerializer):
    path = serializers.CharField(read_only=True)
    owner = serializers.CharField(source="file.user.username", read_only=True)
    permissions = serializers.CharField(source="file.permissions", read_only=True)
    source = serializers.FileField(source="file.content", use_url=False, read_only=True)
    # content = PGPFileField(source='file.content', read_only=True)
    sha256 = serializers.CharField(source="file.sha256", read_only=True)
    mimetype = serializers.CharField(source="file.mimetype", read_only=True)

    class Meta:
        model = models.SystemFile
        fields = ("path", "owner", "permissions", "source", "sha256", "mimetype")


class SystemSerializer(serializers.ModelSerializer):
    users = SystemUserSerializer(source="systemuser_set", many=True)
    groups = GroupSerializer(source="group_set", many=True)
    files = SystemFileSerializer(source="systemfile_set", many=True)

    class Meta:
        model = models.System
        fields = ("name", "users", "groups", "files")


class HostSerializer(serializers.ModelSerializer):
    system = SystemSerializer()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.update(self.Meta.extensions)

    class Meta:
        model = models.Host
        fields = ("name", "system")
        extensions = dict()


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.File
        fields = ("path", "systems", "permissions")
