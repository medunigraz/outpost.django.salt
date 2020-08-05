# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-08-05 12:03
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("salt", "0003_auto_20200730_1627")]

    operations = [
        migrations.AlterField(
            model_name="host",
            name="system",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="salt.System",
            ),
        ),
        migrations.AlterField(
            model_name="permission",
            name="system",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="salt.System",
            ),
        ),
        migrations.AlterField(
            model_name="staffuser",
            name="person",
            field=models.OneToOneField(
                db_constraint=False,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="campusonline.Person",
            ),
        ),
        migrations.AlterField(
            model_name="studentuser",
            name="person",
            field=models.OneToOneField(
                db_constraint=False,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="campusonline.Student",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="local",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
