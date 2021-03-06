# Generated by Django 4.0.2 on 2022-02-26 05:54

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserConsent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('consent_start', models.DateTimeField()),
                ('consent_end', models.DateTimeField()),
                ('customer_id', models.CharField(max_length=24)),
                ('fi_date_range_from', models.DateTimeField()),
                ('fi_date_range_to', models.DateTimeField()),
            ],
        ),
    ]
