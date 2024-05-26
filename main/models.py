from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models


class Teams(models.Model):
    name = models.CharField(max_length=100)
    games = models.IntegerField()
    wins = models.IntegerField()
    loses = models.IntegerField()
    win_percent = models.FloatField()
    scored = models.FloatField()
    missed = models.FloatField()
    difference = models.FloatField()
    home = models.CharField(max_length=100)
    away = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='images/', blank=True, null=True)
    logo_links = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'


class AllMatches(models.Model):
    name_team1 = models.CharField(max_length=100)
    date = models.DateField()
    tournament = models.CharField(max_length=100)
    name_team2 = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    score = models.CharField(max_length=100)
    result = models.CharField(max_length=100)
    link = models.CharField(max_length=255, blank=True, null=True)
    time = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.name_team1 + ' - ' + self.name_team2

    class Meta:
        verbose_name = 'Матч'
        verbose_name_plural = 'Матчи'


class MatchesForPredictions(models.Model):
    name_team1 = models.CharField(max_length=100)
    date = models.DateField()
    tournament = models.CharField(max_length=100)
    name_team2 = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    score = models.CharField(max_length=100)
    result = models.CharField(max_length=100)
    time = models.CharField(max_length=100, null=True)

    def __str__(self):
        return f"{self.name_team1} - {self.name_team2}"

    class Meta:
        verbose_name = 'Прогноз на матч'
        verbose_name_plural = 'Прогнозы на матчи'


class CustomTeam(models.Model):
    name = models.CharField(max_length=100)
    games = models.IntegerField(null=True, blank=True)
    wins = models.IntegerField(null=True, blank=True)
    loses = models.IntegerField(null=True, blank=True)
    win_percent = models.FloatField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    captain = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    logo = models.ImageField(upload_to='images/', blank=True, null=True)
    logo_links = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.games != 0:
            self.win_percent = float(self.wins) / float(self.games) * 100
            super().save(*args, **kwargs)

        # добавляем пользователя в команду
        CustomTeamPlayers.objects.create(user=self.captain, team=self)

    class Meta:
        verbose_name = 'Пользовательская команда'
        verbose_name_plural = 'Пользовательские команды'


class CustomTeamPlayers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(CustomTeam, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name

    class Meta:
        verbose_name = 'Игрок'
        verbose_name_plural = 'Игроки'


class InviteNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(CustomTeam, on_delete=models.CASCADE)
    is_invited = models.BooleanField(default=False, verbose_name='Приглашение принято', null=True, blank=True)
    is_rejected = models.BooleanField(default=False, verbose_name='Приглашение отклонено', null=True, blank=True)
    is_readed = models.BooleanField(default=False, verbose_name='Прочитано', null=True, blank=True)
    notification_type = models.CharField(max_length=100, default='invite')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name

    class Meta:
        verbose_name = 'Уведомление о приглашении'
        verbose_name_plural = 'Уведомления о приглашениях'


class TeamFiles(models.Model):
    team = models.ForeignKey(CustomTeam, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='files/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    filename = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.team.name

    class Meta:
        verbose_name = 'Файл команды'
        verbose_name_plural = 'Файлы команды'


class Subscriptions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    term = models.IntegerField(default=30)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active_until = models.DateTimeField(null=True, blank=True)
    promo_period = models.BooleanField(default=False)
    term_promo = models.IntegerField(default=2)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name

    def save(self, *args, **kwargs):
        if self.is_active and self.active_until is None:
            self.active_until = self.created_at + timedelta(days=self.term)

        if self.promo_period:
            self.term = self.term_promo
            self.active_until = self.created_at + timedelta(days=self.term)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'


class MatchChat(models.Model):
    match = models.ForeignKey(AllMatches, on_delete=models.CASCADE, related_name='chat_messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        unique_together = ['match', 'user', 'message', 'timestamp']
