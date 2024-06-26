# Generated by Django 4.2.8 on 2024-05-04 10:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_invitenotification_created_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamFiles',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(blank=True, null=True, upload_to='files/')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.customteam')),
            ],
            options={
                'verbose_name': 'Файл команды',
                'verbose_name_plural': 'Файлы команды',
            },
        ),
    ]
