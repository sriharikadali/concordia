# Generated by Django 2.0.7 on 2018-07-27 20:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("concordia", "0007_pageinuse")]

    operations = [
        migrations.AlterField(
            model_name="pageinuse",
            name="created_on",
            field=models.DateTimeField(editable=False),
        ),
        migrations.AlterField(
            model_name="pageinuse", name="updated_on", field=models.DateTimeField()
        ),
    ]
