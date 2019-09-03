from rest_framework import serializers

from . import models


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


class SystemUserSerializer(serializers.ModelSerializer):
    uid = serializers.IntegerField(source="user.pk")
    username = serializers.CharField(source="user.person.username")
    displayname = serializers.CharField(source="user.displayname")
    homedir = serializers.SerializerMethodField()
    groups = GroupSerializer(many=True)
    public_keys = PublicKeySerializer(source="user.publickey_set.all", many=True)

    class Meta:
        model = models.SystemUser
        fields = (
            "uid",
            "username",
            "displayname",
            "homedir",
            "shell",
            "groups",
            "sudo",
            "public_keys",
        )

    def get_homedir(self, o):
        return o.system.home_template.format(username=o.user.person.username)


class SystemSerializer(serializers.ModelSerializer):
    users = SystemUserSerializer(source="systemuser_set", many=True)
    groups = GroupSerializer(source="group_set", many=True)

    class Meta:
        model = models.System
        fields = ("name", "users", "groups")


class HostSerializer(serializers.ModelSerializer):
    system = SystemSerializer()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.update(self.Meta.extensions)

    class Meta:
        model = models.Host
        fields = "__all__"
        extensions = dict()
