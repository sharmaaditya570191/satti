# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-25 00:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('satti', '0029_auto_20161222_1304'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatroom',
            name='banned',
            field=models.ManyToManyField(related_name='banned_in', to='satti.ChatUser'),
        ),
    ]
