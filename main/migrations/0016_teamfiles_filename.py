# Generated by Django 4.2.8 on 2024-05-04 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_teamfiles_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='teamfiles',
            name='filename',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]