# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-08 17:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0017_auto_20161208_1532'),
    ]

    operations = [
        migrations.AddField(
            model_name='importveranstaltung',
            name='is_attended_course',
            field=models.BooleanField(default=True),
        ),
    ]
