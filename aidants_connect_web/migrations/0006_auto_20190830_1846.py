# Generated by Django 2.2.4 on 2019-08-30 16:46

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("aidants_connect_web", "0005_auto_20190830_1837")]

    operations = [
        migrations.AlterField(
            model_name="connection",
            name="demarches",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.TextField(default="No démarche"), null=True, size=None
            ),
        )
    ]
