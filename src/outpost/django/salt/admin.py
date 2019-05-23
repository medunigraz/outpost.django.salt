from django.contrib import admin

from . import models


class PublicKeyInline(admin.TabularInline):
    model = models.PublicKey


class SystemUserInline(admin.TabularInline):
    model = models.SystemUser


@admin.register(models.System)
class SystemAdmin(admin.ModelAdmin):
    search_fields = (
        'name',
    )
    inlines = (
        SystemUserInline,
    )


@admin.register(models.Host)
class HostAdmin(admin.ModelAdmin):
    list_filter = (
        'system',
    )
    search_fields = (
        'name',
    )


@admin.register(models.StaffUser)
class StaffUserAdmin(admin.ModelAdmin):
    inlines = (
        SystemUserInline,
        PublicKeyInline,
    )
    list_display = (
        'pk',
        'username',
        'person',
    )
    list_filter = (
        'systems',
    )
    search_fields = (
        'person__username',
        'person__first_name',
        'person__last_name',
    )


@admin.register(models.StudentUser)
class StudentUserAdmin(admin.ModelAdmin):
    inlines = (
        SystemUserInline,
        PublicKeyInline,
    )
    list_display = (
        'pk',
        'username',
        'person',
    )
    list_filter = (
        'systems',
    )
    search_fields = (
        'person__username',
        'person__first_name',
        'person__last_name',
    )


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Permission)
class PermissionAdmin(admin.ModelAdmin):
    pass
