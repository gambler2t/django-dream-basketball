from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('matches/', views.matches, name='matches'),
    path('login/', views.login_view, name='login_view'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('match/<int:match_id>/', views.match, name='match'),
    path('past_matches/', views.past_matches, name='past_matches'),
    path('chototo/', views.chototo, name='chototo'),
    path('custom_teams/', views.custom_teams, name='custom_teams'),
    path('create_custom_team/', views.create_custom_team, name='create_custom_team'),
    path('team_detail/<int:team_id>/', views.team_detail, name='team_detail'),
    path('team_invite/<int:team_id>/', views.team_invite, name='team_invite'),
    # path('team_invite/<int:team_id>/', views.team_invite, name='team_invite'),
    path('invite_player/<int:team_id>/<int:user_id>/', views.invite_player, name='invite_player'),
    path('profile/<int:user_id>/', views.profile, name='profile'),
    path('mark_notification_read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('delete_notification/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('process_invite/<int:notification_id>/', views.process_invite, name='process_invite'),
    path('delete_player/<int:team_id>/<int:player_id>/', views.delete_player, name='delete_player'),
    path('inside_info/<int:team_id>/', views.inside_info, name='inside_info'),
    path('create_inside_files/<int:team_id>/', views.create_inside_files, name='create_inside_files'),
    # path('delete_file/<int:file_id>/', views.delete_file, name='delete_file'),
    path('buy_subscription/', views.buy_subscription, name='buy_subscription'),
    path('get_new_chat_messages/<int:match_id>/', views.get_new_chat_messages, name='get_new_chat_messages'),
    path('send_chat_message/<int:match_id>/', views.send_chat_message, name='send_chat_message'),
    path('team_remove/<int:team_id>/', views.team_remove, name='team_remove'),
]
