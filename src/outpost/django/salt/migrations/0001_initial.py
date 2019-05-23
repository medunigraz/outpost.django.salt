# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-10-22 08:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [("campusonline", "0036_distributionlist_union")]

    operations = [
        migrations.CreateModel(
            name="Group",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=31)),
            ],
        ),
        migrations.CreateModel(
            name="Host",
            fields=[
                (
                    "name",
                    models.CharField(max_length=64, primary_key=True, serialize=False),
                )
            ],
            options={"permissions": (("view_host", "View host"),)},
        ),
        migrations.CreateModel(
            name="System",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=128)),
                (
                    "home_template",
                    models.CharField(default="/home/{username}", max_length=256),
                ),
                ("same_group_id", models.BooleanField(default=True)),
                ("same_group_name", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="SystemUser",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("shell", models.CharField(default="/bin/bash", max_length=256)),
                ("sudo", models.BooleanField(default=False)),
                ("groups", models.ManyToManyField(blank=True, to="salt.Group")),
                (
                    "system",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="salt.System"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "person",
                    models.OneToOneField(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="campusonline.Person",
                    ),
                ),
                (
                    "systems",
                    models.ManyToManyField(
                        blank=True, through="salt.SystemUser", to="salt.System"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="systemuser",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="salt.User"
            ),
        ),
        migrations.AddField(
            model_name="host",
            name="system",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="salt.System",
            ),
        ),
        migrations.AddField(
            model_name="group",
            name="systems",
            field=models.ManyToManyField(blank=True, to="salt.System"),
        ),
        migrations.RunSQL(
            "ALTER SEQUENCE salt_group_id_seq RESTART WITH 1000;",
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "ALTER SEQUENCE salt_user_id_seq RESTART WITH 2000;", migrations.RunSQL.noop
        ),
    ]
