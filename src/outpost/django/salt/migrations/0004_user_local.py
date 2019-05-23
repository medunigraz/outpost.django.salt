# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-01-29 13:46
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("salt", "0003_publickey"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="local",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        )
    ]
