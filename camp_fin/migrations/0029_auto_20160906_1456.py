# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-06 20:56
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('camp_fin', '0028_auto_20160906_1230'),
    ]

    operations = [
        migrations.RenameField(
            model_name='loan',
            old_name='oldb_id',
            new_name='olddb_id',
        ),
    ]
