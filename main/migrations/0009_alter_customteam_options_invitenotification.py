# Generated by Django 4.2.8 on 2024-05-03 10:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0008_customteam_customteamplayers'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customteam',
            options={'verbose_name': 'Пользовательская команда', 'verbose_name_plural': 'Пользовательские команды'},
        ),
        migrations.CreateModel(
            name='InviteNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_invited', models.BooleanField(blank=True, default=False, null=True, verbose_name='Приглашение отправлено')),
                ('is_readed', models.BooleanField(blank=True, default=False, null=True, verbose_name='Прочитано')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.customteam')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Уведомление о приглашении',
                'verbose_name_plural': 'Уведомления о приглашениях',
            },
        ),
    ]
