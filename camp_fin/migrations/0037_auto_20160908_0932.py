# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-08 15:32
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('camp_fin', '0036_auto_20160907_1318'),
    ]

    operations = [
        migrations.CreateModel(
            name='AddressType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.RenameField(
            model_name='address',
            old_name='zip_code',
            new_name='zipcode',
        ),
        migrations.AddField(
            model_name='address',
            name='country',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='address',
            name='county',
            field=models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='camp_fin.County'),
        ),
        migrations.AddField(
            model_name='address',
            name='date_added',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='address',
            name='from_file_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='address',
            name='olddb_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='address',
            field=models.ForeignKey(db_constraint=False, default=1, on_delete=django.db.models.deletion.CASCADE, to='camp_fin.Address'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contact',
            name='company_name',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='contact_type',
            field=models.ForeignKey(db_constraint=False, default=1, on_delete=django.db.models.deletion.CASCADE, to='camp_fin.ContactType'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contact',
            name='date_added',
            field=models.DateTimeField(default=datetime.datetime(2016, 9, 8, 15, 31, 47, 448736, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contact',
            name='email',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='entity',
            field=models.ForeignKey(db_constraint=False, default=1, on_delete=django.db.models.deletion.CASCADE, to='camp_fin.Entity'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contact',
            name='first_name',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='from_file_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='full_name',
            field=models.CharField(default='', max_length=500),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contact',
            name='last_name',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='memo',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='middle_name',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='olddb_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='phone',
            field=models.CharField(max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='prefix',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='status',
            field=models.ForeignKey(db_constraint=False, default=1, on_delete=django.db.models.deletion.CASCADE, to='camp_fin.Status'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contact',
            name='suffix',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='contacttype',
            name='description',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='address',
            name='state',
            field=models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='camp_fin.State'),
        ),
        migrations.AddField(
            model_name='address',
            name='address_type',
            field=models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='camp_fin.AddressType'),
        ),
    ]
