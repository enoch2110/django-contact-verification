# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-14 02:28
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contact_verification', '0002_auto_20161013_1504'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contacts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='contactverification',
            unique_together=set([]),
        ),
    ]
