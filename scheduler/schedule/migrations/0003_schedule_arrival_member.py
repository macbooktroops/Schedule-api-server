# Generated by Django 2.1.7 on 2019-06-20 13:19

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('schedule', '0002_holiday'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='arrival_member',
            field=models.ManyToManyField(related_name='schedule_arrival_member', to=settings.AUTH_USER_MODEL),
        ),
    ]
