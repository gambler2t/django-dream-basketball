# Generated by Django 4.2.8 on 2024-05-04 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0018_subscriptions_active_until_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscriptions',
            name='term',
            field=models.IntegerField(default=30),
        ),
    ]
