from .models import InviteNotification


def unread_notifications(request):
    if request.user.is_authenticated:
        unread_notification_count = InviteNotification.objects.filter(user=request.user, is_readed=False).count()
        return {'unread_notification_count': unread_notification_count}
    else:
        return {}
