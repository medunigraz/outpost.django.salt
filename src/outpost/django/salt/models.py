import logging
from base64 import b64encode
from hashlib import sha256

import asyncssh
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel

from outpost.django.base.decorators import signal_connect
from outpost.django.base.validators import PublicKeyValidator
from outpost.django.campusonline.models import Person, Student

from .tasks import RunCommandTask


logger = logging.getLogger(__name__)


class PublicKey(models.Model):
    user = models.ForeignKey("User")
    name = models.CharField(max_length=128)
    key = models.TextField(validators=(PublicKeyValidator(),))

    def __str__(self):
        return self.name

    @property
    def fingerprint(self):
        k = asyncssh.import_public_key(self.key)
        d = sha256(k.get_ssh_public_key()).digest()
        f = b64encode(d).replace(b"=", b"").decode("utf-8")
        return "SHA256:{}".format(f)

    @property
    def openssh(self):
        k = asyncssh.import_public_key(self.key)
        return k.export_public_key()

    @property
    def comment(self):
        k = asyncssh.import_public_key(self.key)
        return k.get_comment()

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kwargs):
        for system in instance.user.systems.all():
            for host in system.host_set.all():
                logger.debug(f"Scheduling public key sync task for {host}")
                task = RunCommandTask().delay(
                    tgt_type="compound",
                    tgt=f"G@host:{host.name}",
                    fun="state.apply",
                    arg=["outpost.users"],
                )
                logger.debug(f"Scheduled public key sync for {host} as {task.id}")


post_save.connect(PublicKey.post_save, sender=PublicKey)


class System(models.Model):
    name = models.CharField(max_length=128)
    home_template = models.CharField(max_length=256, default="/home/{username}")
    same_group_id = models.BooleanField(default=True)
    same_group_name = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kwargs):
        for host in instance.host_set.all():
            task = RunCommandTask().delay(
                tgt_type="compound",
                tgt=f"G@host:{host.name}",
                fun="state.apply",
                arg=[],
            )
            logger.debug(f"Scheduled host state sync for {host} as {task.id}")


post_save.connect(System.post_save, sender=System)


class Host(models.Model):
    name = models.CharField(primary_key=True, max_length=64)
    system = models.ForeignKey("System", blank=True, null=True)

    class Meta:
        permissions = (("view_host", _("View host")),)

    def __str__(self):
        return self.name

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kwargs):
        if not created:
            return
        task = RunCommandTask().delay(
            tgt_type="compound",
            tgt=f"G@host:{instance.name}",
            fun="state.apply",
            arg=[],
        )
        logger.debug(f"Scheduled host sync for {instance} as {task.id}")


post_save.connect(Host.post_save, sender=Host)


class SystemUser(models.Model):
    system = models.ForeignKey("System")
    user = models.ForeignKey("User")
    shell = models.CharField(max_length=256, default="/bin/bash")
    groups = models.ManyToManyField("Group", blank=True)
    sudo = models.BooleanField(default=False)

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kwargs):
        for group in instance.groups.all():
            if group not in instance.system.group_set.all():
                instance.system.group_set.add(group)
        for host in instance.system.host_set.all():
            task = RunCommandTask().delay(
                tgt_type="compound",
                tgt=f"G@host:{instance.name}",
                fun="state.apply",
                arg=["outpost"],
            )
            logger.debug(f"Scheduled user sync for {host} as {task.id}")

    def __str__(self):
        return f"{self.user.person.username}@{self.system} (self.user)"


post_save.connect(SystemUser.post_save, sender=SystemUser)


class User(PolymorphicModel):
    systems = models.ManyToManyField("System", through="SystemUser", blank=True)
    local = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)

    class Meta:
        ordering = ("pk",)

    @property
    def username(self):
        return self.person.username

    @property
    def displayname(self):
        return f"{self.person.first_name} {self.person.last_name}"

    @property
    def email(self):
        return self.person.email

    def __str__(self):
        return f"{self.person} ({self.username}:{self.pk})"

    @classmethod
    def update(cls, sender, request, user, **kwargs):
        username = getattr(user, user.USERNAME_FIELD)
        try:
            person = cls.campusonline.objects.get(username=username)
        except cls.campusonline.DoesNotExist:
            return
        defaults = {"person": person, "local": user}
        suser, created = cls.objects.get_or_create(
            person__username=username, defaults=defaults
        )
        if not created:
            if suser.local != user:
                suser.local = user
                suser.save()


class StaffUser(User):
    campusonline = Person
    person = models.OneToOneField("campusonline.Person", db_constraint=False)


class StudentUser(User):
    campusonline = Student
    person = models.OneToOneField("campusonline.Student", db_constraint=False)


user_logged_in.connect(StaffUser.update)
user_logged_in.connect(StudentUser.update)


class Group(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=31, unique=True)
    systems = models.ManyToManyField("System", blank=True)

    class Meta:
        ordering = ("pk",)

    def __str__(self):
        return f"{self.name} ({self.pk})"

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kwargs):
        for system in instance.systems.all():
            for host in system.host_set.all():
                task = RunCommandTask().delay(
                    tgt_type="compound",
                    tgt=f"G@host:{host.name}",
                    fun="state.apply",
                    arg=["outpost.groups"],
                )
                logger.debug(f"Scheduled group sync for {host} as {task.id}")


post_save.connect(Group.post_save, sender=Group)


class Permission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    system = models.ForeignKey("System", blank=True, null=True)
    function = models.CharField(max_length=256, default=".*")

    def __str__(self):
        if not self.system:
            return f"{self.user}: {self.function}"
        return f"{self.user}@{self.system}: {self.function}"
