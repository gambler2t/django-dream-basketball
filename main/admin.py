from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(Teams)
admin.site.register(AllMatches)
admin.site.register(MatchesForPredictions)
admin.site.register(CustomTeam)
admin.site.register(InviteNotification)
admin.site.register(TeamFiles)
admin.site.register(Subscriptions)
