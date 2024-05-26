# Generated by Django 4.2.8 on 2024-05-08 05:12

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0022_matchchat'),
    ]

    operations = [
        migrations.AddField(
            model_name='allmatches',
            name='time',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='matchesforpredictions',
            name='time',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='matchchat',
            unique_together={('match', 'user', 'message', 'timestamp')},
        ),
    ]