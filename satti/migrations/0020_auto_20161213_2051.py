# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-13 20:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('satti', '0019_auto_20161122_1625'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatuser',
            name='profile_text',
            field=models.CharField(default="This is my profile text. Isn't it fun?", max_length=200),
        ),
    ]
