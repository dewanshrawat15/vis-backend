# Generated by Django 4.0.2 on 2022-02-26 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userconsent',
            name='consent_id',
            field=models.CharField(default=0, editable=False, max_length=72),
            preserve_default=False,
        ),
    ]
