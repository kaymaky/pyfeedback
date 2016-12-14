# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-14 01:50
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('feedback', '0019_merge_20161209_1404'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='log',
            name='verursacher',
        ),
        migrations.AddField(
            model_name='log',
            name='scanner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scanner', to='feedback.BarcodeScanner'),
        ),
        migrations.AddField(
            model_name='log',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='log',
            name='interface',
            field=models.CharField(choices=[('fe', 'Frontend'), ('bs', 'Barcodescanner'), ('ad', 'Admin')], max_length=2),
        ),
        migrations.AlterField(
            model_name='log',
            name='veranstaltung',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='veranstaltung', to='feedback.Veranstaltung'),
        ),
    ]