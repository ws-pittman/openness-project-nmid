# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-06 20:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('camp_fin', '0029_auto_20160906_1456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loan',
            name='contact',
            field=models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='camp_fin.Contact'),
        ),
    ]
