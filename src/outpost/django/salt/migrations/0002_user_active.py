# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-06-29 18:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("salt", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="user", name="active", field=models.BooleanField(default=True)
        )
    ]
