from django.contrib import admin
from reversion.admin import VersionAdmin

from . import models


class PublicKeyInline(admin.TabularInline):
    model = models.PublicKey


class SystemUserInline(admin.TabularInline):
    model = models.SystemUser


@admin.register(models.System)
class SystemAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    inlines = (SystemUserInline,)


@admin.register(models.Host)
class HostAdmin(admin.ModelAdmin):
    list_filter = ("system",)
    search_fields = ("name",)


@admin.register(models.StaffUser)
class StaffUserAdmin(admin.ModelAdmin):
    inlines = (SystemUserInline, PublicKeyInline)
    list_display = ("pk", "username", "person")
    list_filter = ("systems",)
    search_fields = ("person__username", "person__first_name", "person__last_name")


@admin.register(models.StudentUser)
class StudentUserAdmin(admin.ModelAdmin):
    inlines = (SystemUserInline, PublicKeyInline)
    list_display = ("pk", "username", "person")
    list_filter = ("systems",)
    search_fields = ("person__username", "person__first_name", "person__last_name")


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Permission)
class PermissionAdmin(admin.ModelAdmin):
    pass


class SystemFileInline(admin.TabularInline):
    model = models.File.systems.through


@admin.register(models.File)
class FileAdmin(VersionAdmin):
    list_display = ("pk", "path", "permissions", "sha256")
    list_filter = ("user",)
    search_fields = ("path",)
    readonly_fields = ("sha256", "mimetype")
    inlines = (SystemFileInline,)


@admin.register(models.Job)
class JobAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Result)
class ResultAdmin(admin.ModelAdmin):
    date_hierarchy = "modified"
    list_filter = ("success", "function")
    list_display = ("pk", "target", "function", "success", "modified")
