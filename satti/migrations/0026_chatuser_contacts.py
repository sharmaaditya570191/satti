# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-21 00:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('satti', '0025_auto_20161216_1618'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatuser',
            name='contacts',
            field=models.ManyToManyField(blank=True, related_name='_chatuser_contacts_+', to='satti.ChatUser'),
        ),
    ]
