# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-17 13:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('satti', '0017_auto_20161117_1312'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatroom',
            name='image',
            field=models.ImageField(default='default.jpg', upload_to='/images/'),
        ),
        migrations.AlterField(
            model_name='chatuser',
            name='image',
            field=models.ImageField(default='default.jpg', upload_to='/images/'),
        ),
    ]
