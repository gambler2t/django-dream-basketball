# Generated by Django 5.0 on 2023-12-06 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_teams_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='teams',
            name='logo_links',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
