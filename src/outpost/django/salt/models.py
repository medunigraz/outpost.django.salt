# import os
# import gpg
import hashlib
import logging
from base64 import b64encode
from hashlib import sha256
from io import BytesIO
from pathlib import PurePath
from tempfile import NamedTemporaryFile

import asyncssh
import django
import magic
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import (
    ImproperlyConfigured,
    ValidationError,
)
from django.core.files import File as DjangoFile
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import (
    post_save,
    pre_save,
)
from django.utils.translation import gettext_lazy as _
from outpost.django.base.decorators import signal_connect
from outpost.django.base.utils import Uuid4Upload
from outpost.django.base.validators import (
    NormalizedPathValidator,
    PublicKeyValidator,
    RelativePathValidator,
)
from outpost.django.campusonline.models import (
    External,
    Person,
    Student,
)
from polymorphic.models import PolymorphicModel

from .conf import settings
from .tasks import CommandTasks

logger = logging.getLogger(__name__)


class File(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    path = models.CharField(
        max_length=512,
        validators=(
            NormalizedPathValidator(),
            RelativePathValidator(),
        ),
    )
    content = models.FileField(
        upload_to=Uuid4Upload, storage=settings.SALT_FILE_STORAGE
    )
    systems = models.ManyToManyField("System", through="SystemFile", blank=True)
    sha256 = models.CharField(max_length=64)
    permissions = models.CharField(
        max_length=4,
        default="0640",
        validators=(
            RegexValidator(r"^0?[0-7]{3}$", _("Not a valid POSIX permission.")),
        ),
    )
    mimetype = models.TextField()

    @classmethod
    def pre_save_handler(cls, sender, instance, raw, *args, **kwargs):
        if raw:
            return
        for system in instance.user.systems.all():
            home = PurePath(
                system.home_template.format(username=instance.user.username)
            )
            path = home.joinpath(PurePath(instance.path))
            if home.parts != path.parts[: len(home.parts)]:
                raise ValidationError(
                    f"Path does not fit in home directory {home} on {system}."
                )
        if not isinstance(instance.content.file, TemporaryUploadedFile):
            return
        hash = hashlib.sha256()
        b = bytearray(128 * 1024)
        mv = memoryview(b)
        for n in iter(lambda: instance.content.readinto(mv), 0):
            hash.update(mv[:n])
        instance.sha256 = hash.hexdigest()
        instance.content.seek(0)
        mimetype = magic.detect_from_fobj(instance.content)
        instance.mimetype = mimetype.mime_type
        # with gpg.Context(armor=True) as c:
        #    imp = c.key_import(settings.SALT_PUBLIC_KEY.encode('ascii'))
        #    if not isinstance(imp, gpg.results.ImportResult):
        #        logger.error('Could not import Saltstack public GPG key.')
        #        raise ImproperlyConfigured(_("Invalid Saltstack public PGP key."))
        #    keys = [c.get_key(k.fpr) for k in imp.imports]
        #    #import pudb; pu.db
        #    sink = NamedTemporaryFile(
        #        prefix=f"{__name__}.{__class__.__name__}.",
        #        suffix=".asc"
        #    )
        #    result, encryption, signature = c.encrypt(
        #        instance.content,
        #        keys,
        #        sign=False,
        #        always_trust=True,
        #        sink=sink
        #    )
        #    #os.unlink(instance.content.file.file.name)
        #    instance.content = DjangoFile(sink)

    @classmethod
    def post_save_handler(cls, sender, instance, raw, *args, **kwargs):
        if raw:
            return
        for system in instance.systems.all():
            for host in system.host_set.all():
                task = CommandTasks().run.delay(
                    tgt_type="compound",
                    tgt=f"G@host:{host.name}",
                    fun="state.apply",
                    arg=["outpost.files"],
                )
                logger.debug(f"Scheduled file sync for {host} as {task.id}")

    def __str__(self):
        return f"{self.user}: {self.path}"


pre_save.connect(File.pre_save_handler, sender=File)
post_save.connect(File.post_save_handler, sender=File)


class SystemFile(models.Model):
    system = models.ForeignKey("System", on_delete=models.CASCADE)
    file = models.ForeignKey("File", on_delete=models.CASCADE)

    @property
    def path(self) -> str:
        username = self.file.user.username
        home = PurePath(self.system.home_template.format(username=username))
        path = home.joinpath(PurePath(self.file.path))
        return str(path)

    @classmethod
    def post_save_handler(cls, sender, instance, raw, *args, **kwargs):
        if raw:
            return
        for host in instance.system.host_set.all():
            task = CommandTasks().run.delay(
                tgt_type="compound",
                tgt=f"G@host:{host.name}",
                fun="state.apply",
                arg=["outpost.files"],
            )
            logger.debug(f"Scheduled file sync for {host} as {task.id}")

    def __str__(self):
        return f"{self.system}: {self.path}"


post_save.connect(SystemFile.post_save_handler, sender=SystemFile)


class PublicKey(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    key = models.TextField(validators=(PublicKeyValidator(),))

    def __str__(self):
        return self.name

    @property
    def fingerprint(self):
        k = asyncssh.import_public_key(self.key)
        d = sha256(k.encode_ssh_public()).digest()
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
                task = CommandTasks().run.delay(
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

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kwargs):
        for host in instance.host_set.all():
            task = CommandTasks().run.delay(
                tgt_type="compound",
                tgt=f"G@host:{host.name}",
                fun="state.apply",
                arg=["outpost"],
            )
            logger.debug(f"Scheduled host state sync for {host} as {task.id}")


post_save.connect(System.post_save, sender=System)


class UserDirectory(models.Model):
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    template = models.TextField()
    permissions = models.CharField(max_length=4, default="0700")

    def __str__(self):
        return f"{self.system}: {self.template}"


class Host(models.Model):
    name = models.CharField(max_length=64, unique=True, db_index=True)
    system = models.ForeignKey(
        "System", blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        permissions = (
            (("view_host", _("View host")),) if django.VERSION < (2, 1) else tuple()
        )
        ordering = ("name",)

    def __str__(self):
        return self.name

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kwargs):
        if not created:
            return
        task = CommandTasks().run.delay(
            tgt_type="compound",
            tgt=f"G@host:{instance.name}",
            fun="state.apply",
            arg=["outpost"],
        )
        logger.debug(f"Scheduled host sync for {instance} as {task.id}")


post_save.connect(Host.post_save, sender=Host)


class SystemUser(models.Model):
    system = models.ForeignKey("System", on_delete=models.CASCADE)
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    shell = models.CharField(max_length=256, default="/bin/bash")
    groups = models.ManyToManyField("Group", blank=True)
    sudo = models.BooleanField(default=False)

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kwargs):
        for group in instance.groups.all():
            if group not in instance.system.group_set.all():
                instance.system.group_set.add(group)
        for host in instance.system.host_set.all():
            task = CommandTasks().run.delay(
                tgt_type="compound",
                tgt=f"G@host:{host.name}",
                fun="state.apply",
                arg=["outpost"],
            )
            logger.debug(f"Scheduled user sync for {host} as {task.id}")

    def __str__(self):
        return f"{self.user.person.username}@{self.system} (self.user)"


post_save.connect(SystemUser.post_save, sender=SystemUser)


class User(PolymorphicModel):
    systems = models.ManyToManyField("System", through="SystemUser", blank=True)
    local = models.ForeignKey(
        get_user_model(), blank=True, null=True, on_delete=models.SET_NULL
    )
    active = models.BooleanField(default=True)

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
    person = models.OneToOneField(
        "campusonline.Person", db_constraint=False, on_delete=models.DO_NOTHING
    )


class ExternalUser(User):
    campusonline = External
    person = models.OneToOneField(
        "campusonline.External", db_constraint=False, on_delete=models.DO_NOTHING
    )


class StudentUser(User):
    campusonline = Student
    person = models.OneToOneField(
        "campusonline.Student", db_constraint=False, on_delete=models.DO_NOTHING
    )


user_logged_in.connect(StaffUser.update)
user_logged_in.connect(ExternalUser.update)
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
                task = CommandTasks().run.delay(
                    tgt_type="compound",
                    tgt=f"G@host:{host.name}",
                    fun="state.apply",
                    arg=["outpost.groups"],
                )
                logger.debug(f"Scheduled group sync for {host} as {task.id}")


post_save.connect(Group.post_save, sender=Group)


class Permission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    system = models.ForeignKey(
        "System", blank=True, null=True, on_delete=models.SET_NULL
    )
    function = models.CharField(max_length=256, default=".*")

    def __str__(self):
        if not self.system:
            return f"{self.user}: {self.function}"
        return f"{self.user}@{self.system}: {self.function}"


class Job(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    data = JSONField()

    class Meta:
        managed = False
        db_table = "salt_job"

    def __str__(self):
        return self.id


class Result(models.Model):
    function = models.CharField(max_length=50)
    job = models.ForeignKey("Job", on_delete=models.CASCADE)
    result = JSONField()
    data = JSONField()
    target = models.CharField(max_length=255)
    success = models.BooleanField()
    modified = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "salt_result"
        ordering = ("-modified",)

    def __str__(self):
        return f"{self.target}: {self.function} @ {self.modified}"
