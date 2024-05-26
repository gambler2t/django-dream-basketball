# Generated by Django 4.2.8 on 2024-05-04 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_subscriptions'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptions',
            name='active_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='subscriptions',
            name='promo_period',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='subscriptions',
            name='term',
            field=models.IntegerField(default=1),
        ),
    ]