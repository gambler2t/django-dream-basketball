import uuid
from datetime import datetime
from operator import attrgetter

import joblib
import pandas as pd
import requests
from bs4 import BeautifulSoup
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from yookassa import Configuration, Payment

from predict_baskeball_matches.settings import YOOKASSA_SECRET_KEY, YOOKASSA_ACCOUNT_ID

Configuration.account_id = YOOKASSA_ACCOUNT_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

from main.models import *

data = []
data_new = []
team_links = []
headers = {
    "User-Agent": "Mozilla/5.0"
}

header = [['id', 'Команда', 'М', 'В', 'П', '% побед', 'Заб', 'Проп', 'Рзн', 'Дома', 'В гостях', 'logo', 'logo_links']]

# Определение пути для сохранения модели
model_filename = 'logistic_regression_model.joblib'


def get_teams():
    url = 'https://www.sports.ru/vtb-league/table/'

    response = requests.get(url, headers=headers)
    html = response.text

    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table', class_='stat-table')
    first_table = True

    for table in tables:
        rows = table.find_all('tr')

        team_link = soup.find_all('a', class_='name')
        team_links.extend(team_link)

        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            data.append(cols)

        # print(len(data), data)

        if first_table:
            # удаление первого элемента из списка
            data.pop(0)
        else:
            data.pop(6)

        for i in range(0, len(data)):
            data[i].append(team_links[i]['href'])
            url = team_links[i]['href']
            print(url)
            response = requests.get(url, headers=headers)
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            logo = soup.find('div', class_='img-box').find('img')['src']
            data[i].append(logo)

        first_table = False

    data.insert(0, ['id', 'Команда', 'М', 'В', 'П', '% побед', 'Заб', 'Проп', 'Рзн', 'Дома', 'В гостях', 'logo',
                    'logo_links'])
    # data.pop(1)

    for i in range(0, len(data)):
        data[i] = data[i][:13]

    copy_data = data.copy()

    # print('team_links')
    # print(team_links)

    # for i in range(1, len(copy_data)):
    #     copy_data[i].pop()

    with open('vtb_league.csv', 'w') as file:
        for row in copy_data:
            file.write(','.join(row) + '\n')

    for link in team_links:
        # print(link['href'])
        if 'tags' in link['href']:
            tag_part = link['href'].split('tags')[1][1:-1]
            team_links[team_links.index(link)]['href'] = f"tags/{tag_part}"
        else:
            team_links[team_links.index(link)]['href'] = link['href'].split('/')[-2]

    for team_data in data[1:]:
        Teams.objects.get_or_create(
            name=team_data[1],
            games=team_data[2],
            wins=team_data[3],
            loses=team_data[4],
            win_percent=team_data[5],
            scored=team_data[6],
            missed=team_data[7],
            difference=team_data[8],
            home=team_data[9],
            away=team_data[10],
            logo=team_data[11],
            logo_links=team_data[12]
        )


def parse_matches():
    for team_link in team_links:

        url = 'https://www.sports.ru/basketball/club/' + team_link['href'] + '/calendar/'
        # url = team_link['href'] + '/calendar/'
        print(url)
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='stat-table')
        rows = table.find_all('tr')[1:]

        for row in rows:
            team_name = team_link.text

            date_col = row.find('td', class_='name-td alLeft bordR')
            date = date_col.text.strip()

            tournament_col = row.find_all('td')[1]
            tournament = tournament_col.text.strip()

            opponent_col = row.find_all('td')[2]
            opponent = opponent_col.text.strip()
            if 'Дома' in opponent:
                opponent = opponent.split('Дома')[0]
            elif 'В гостях' in opponent:
                opponent = opponent.split('В гостях')[0]

            home_away_col = row.find('td', class_='alRight padR20')
            home_away = home_away_col.text.strip()

            score_col = row.find('td', class_='score-td')
            score = score_col.text.strip()

            result = "not played"
            if row.find('a', class_='dot gr-dot'):
                result = "win"
            elif row.find('a', class_='dot rd-dot'):
                result = "lose"

            link = score_col.find('a')['href']
            if 'www.sports.ru' not in link:
                link = 'https://www.sports.ru' + link

            data.append([team_name, date, tournament, opponent,
                         home_away, score, result, link])

        data.pop()

    data.insert(0, ['Команда 1', 'Дата', 'Турнир', 'Команда 2', 'Место проведения', 'Счет', 'Результат', 'Ссылка',
                    'Время'])

    print('data:')
    print(data)
    for i in range(1, len(data)):
        if data[i][1] == 'перенесен':
            data[i][1] = '01.01.2025'
            data[i].append('')  # Добавляем пустое значение для времени, если матч перенесен
        else:
            try:
                temp = data[i][1].split('|')[1]
                print('temp: ', temp)
                data[i][1] = data[i][1].split('|')[0]
                data[i].append(temp)  # Добавляем время в список data
                print('time: ', data[i][-1])  # Используем индекс -1 для доступа к последнему элементу списка
            except:
                data[i].append('')  # Добавляем пустое значение для времени, если время отсутствует
                continue

    allmatches = []  # Создаем пустой список для хранения всех матчей
    MatchesForPredictions = []  # Создаем пустой список для хранения выигранных матчей

    for i in range(len(data) - 1, 0, -1):
        if data[i][6] != "not played":
            MatchesForPredictions.append(data[i])
        allmatches.append(data[i])

    data_new = data[:1] + data[17:]

    with open('data_matches.csv', 'w') as file:
        for row in data_new:
            file.write(','.join(row) + '\n')

    return allmatches, MatchesForPredictions  # Возвращаем оба списка


def save_teams_data(data_new):
    for team_data in data_new[1:]:
        Teams.objects.get_or_create(
            name=team_data[1],
            defaults={
                'games': team_data[2],
                'wins': team_data[3],
                'loses': team_data[4],
                'win_percent': team_data[5],
                'scored': team_data[6],
                'missed': team_data[7],
                'difference': team_data[8],
                'home': team_data[9],
                'away': team_data[10],

            }
        )


def save_matches_data(data_new):
    # data_new в файл
    with open('data_matches2.csv', 'w') as file:
        for row in data_new:
            file.write(','.join(row) + '\n')
    for match_data in data_new:
        try:
            formatted_date = match_data[1]
            formatted_date = datetime.strptime(formatted_date, '%d.%m.%Y').strftime('%Y-%m-%d')
            # print(formatted_date)

            AllMatches.objects.get_or_create(
                name_team1=match_data[0],
                date=formatted_date,
                tournament=match_data[2],
                name_team2=match_data[3],
                place=match_data[4],
                score=match_data[5],
                result=match_data[6],
                link=match_data[7],
                time=match_data[8]  # Добавляем время
            )
        except:
            print('сохранение не удалось')


def save_predictions_data(data_new):
    for match_data in data_new:
        try:
            formatted_date = match_data[1]
            formatted_date = datetime.strptime(formatted_date, '%d.%m.%Y').strftime('%Y-%m-%d')

            MatchesForPredictions.objects.get_or_create(
                name_team1=match_data[0],
                date=formatted_date,
                tournament=match_data[2],
                name_team2=match_data[3],
                place=match_data[4],
                score=match_data[5],
                result=match_data[6],
                time=match_data[8]  # Добавляем время
            )
        except:
            print('сохранение не удалось')


def train_model():
    matches = AllMatches.objects.all()
    teams = Teams.objects.all()

    data1 = teams
    data1 = pd.DataFrame(data1.values())

    data2 = matches
    data2 = pd.DataFrame(data2.values())

    combined_data = pd.merge(data1, data2, left_on='name', right_on='name_team1')
    combined_data = combined_data[combined_data['result'] != 'not played']

    # сохранение в csv
    combined_data.to_csv('combined_data.csv')

    le = LabelEncoder()
    combined_data['result'] = le.fit_transform(combined_data['result'])

    features = ['games', 'wins', 'loses', 'win_percent', 'scored', 'missed', 'difference']
    target = 'result'

    X = combined_data[features]
    y = combined_data[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LogisticRegression(max_iter=2000)
    model.fit(X_train, y_train)

    accuracy = accuracy_score(y_test, model.predict(X_test))
    print(f'Точность модели: {accuracy}')

    # Сохранение обученной модели в файл
    joblib.dump(model, model_filename)


def load_model():
    # Загрузка обученной модели из файла
    return joblib.load(model_filename)


def match(request, match_id):
    match = AllMatches.objects.get(id=match_id)
    team1 = Teams.objects.get(name=match.name_team1)
    team2 = Teams.objects.get(name=match.name_team2)

    try:
        # Попытка загрузить ранее обученную модель
        model = load_model()
    except FileNotFoundError:
        # Если файл не найден, обучаем модель и сохраняем ее
        train_model()
        model = load_model()

    teams = Teams.objects.all()

    data1 = teams
    data1 = pd.DataFrame(data1.values())

    matches = AllMatches.objects.all()
    data2 = pd.DataFrame(matches.values())

    combined_data = pd.merge(data1, data2, left_on='name', right_on='name_team1')

    le = LabelEncoder()
    combined_data['result'] = le.fit_transform(combined_data['result'])

    features = ['games', 'wins', 'loses', 'win_percent', 'scored', 'missed', 'difference']

    team1_data = combined_data[combined_data['name'] == team1.name]
    team2_data = combined_data[combined_data['name'] == team2.name]

    team1_data = team1_data[features]
    team2_data = team2_data[features]

    team1_proba = model.predict_proba(team1_data)
    team2_proba = model.predict_proba(team2_data)

    team1_win_probability = team1_proba[0][1]
    team2_win_probability = team2_proba[0][1]

    team1_odds = team1_win_probability / (1 - team1_win_probability)
    team2_odds = team2_win_probability / (1 - team2_win_probability)

    team1_percent = (team1_odds / (team1_odds + 1)) * 100
    team2_percent = (team2_odds / (team2_odds + 1)) * 100

    print(f'Команда {team1.name} победит с вероятностью {round(team1_percent, 2)}%')
    print(f'Команда {team2.name} победит с вероятностью {round(team2_percent, 2)}%')

    if team1_percent > team2_percent:
        result = "Победа команды " + team1.name
    elif team1_percent < team2_percent:
        result = "Победа команды " + team2.name
    else:
        result = "Ничья"

    # отбор последних 5 матчей команды 1
    team1_matches = AllMatches.objects.filter(name_team1=team1.name)
    team1_matches = team1_matches.exclude(result='not played')
    team1_matches = team1_matches.order_by('-date')
    team1_matches = team1_matches[:5]

    # отбор последних 5 матчей команды 2
    team2_matches = AllMatches.objects.filter(name_team1=team2.name)
    team2_matches = team2_matches.exclude(result='not played')
    team2_matches = team2_matches.order_by('-date')
    team2_matches = team2_matches[:5]

    response = requests.get(match.link, headers=headers)
    html_content = response.content

    soup = BeautifulSoup(html_content, 'html.parser')

    try:
        # Найдите все таблицы на странице
        tables = soup.find_all('table', class_='stat-table')

        # Переменная для хранения данных
        parsed_data_1 = []
        parsed_data_2 = []

        titles = soup.find_all('h3', class_='titleH3 bordered mB10')
        # print(titles[1].text)
        title1 = titles[1].text.split('.')[0]
        # print(titles[2].text)
        title2 = titles[2].text.split('.')[0]

        # Извлеките данные из каждой строки
        rows = tables[0].find_all('tr')
        for row in rows[2:]:  # Пропустите первую строку, так как это заголовки
            # Извлечение данных из ячеек
            cells = row.find_all(['td', 'th'])
            row_data = [cell.text.strip() for cell in cells]
            parsed_data_1.append(row_data)

        rows = tables[1].find_all('tr')
        for row in rows[2:]:  # Пропустите первую строку, так как это заголовки
            # Извлечение данных из ячеек
            cells = row.find_all(['td', 'th'])
            row_data = [cell.text.strip() for cell in cells]
            parsed_data_2.append(row_data)
    except:
        parsed_data_1 = []
        parsed_data_2 = []
        title1 = ''
        title2 = ''

    subscription = None

    if request.user.is_authenticated:
        user = request.user
        # ищем подписку
        try:
            subscription = Subscriptions.objects.get(user=user)
        except:
            pass
        if subscription is not None:
            if subscription.is_active or subscription.promo_period:
                subscription = True
            else:
                subscription = False
        else:
            subscription = False

    else:
        subscription = False

    match = AllMatches.objects.get(id=match_id)
    # если дата матча сегодня +- 1 день
    is_today = False
    chat_messages = None
    if match.date == datetime.now().date() or match.date == datetime.now().date() + timedelta(days=1):
        is_today = True

        chat_messages = MatchChat.objects.filter(match=match)

        if request.method == 'POST' and request.user.is_authenticated:
            # Обработка отправки нового сообщения
            message = request.POST.get('message')
            if message:
                MatchChat.objects.create(match=match, user=request.user, message=message)

    context = {
        'match': match,
        'team1': team1,
        'team2': team2,
        'result': result,
        'team1_percent': team1_percent,
        'team2_percent': team2_percent,
        'team1_matches': team1_matches,
        'team2_matches': team2_matches,
        'team1_players': parsed_data_1,
        'team2_players': parsed_data_2,
        'title1': title1,
        'title2': title2,
        'subscription': subscription,
    }

    if is_today:
        context['chat_messages'] = chat_messages
        context['is_today'] = is_today
    return render(request, 'match.html', context)


def update_data():
    Teams.objects.all().delete()
    AllMatches.objects.all().delete()
    MatchesForPredictions.objects.all().delete()
    get_teams()
    save_teams_data(data_new)
    all_matches, matches_for_predictions = parse_matches()
    save_matches_data(all_matches)
    save_predictions_data(matches_for_predictions)


def matches_future():
    matches = AllMatches.objects.all()

    print("matches", matches.values())

    # добавление лого команд
    for match in matches:
        try:
            team1 = Teams.objects.get(name=match.name_team1)
            team2 = Teams.objects.get(name=match.name_team2)
            match.logo1 = team1.logo_links
            match.logo2 = team2.logo_links
        # TODO: убрать потом этот блок
        except:
            continue

    # сортировка матчей по дате
    matches = sorted(matches, key=attrgetter('date'))

    # выбор матчей, которые еще не сыграны
    matches = [match for match in matches if match.result == 'not played']

    # удаление повторяющихся матчей, если есть матч с обратным порядком команд
    matches = [match for match in matches if match.name_team1 < match.name_team2]

    today_date = datetime.now().date()
    matches = [match for match in matches if match.date >= today_date]

    return matches


def matches(request):
    matches = matches_future()

    return render(request, 'matches.html', {'matches': matches})


def logout_view(request):
    logout(request)
    return redirect('index')


def index(request):
    try:
        notifications = InviteNotification.objects.filter(user=request.user)
        unread_notification_count = notifications.filter(is_readed=False).count()
    except:
        unread_notification_count = None
    return render(request, 'index.html', {'unread_notification_count': unread_notification_count})


def past_matches(request):
    matches = AllMatches.objects.all()

    # добавление лого команд
    for match in matches:
        team1 = Teams.objects.get(name=match.name_team1)
        team2 = Teams.objects.get(name=match.name_team2)
        match.logo1 = team1.logo_links
        match.logo2 = team2.logo_links

    # сортировка матчей по дате по убыванию
    matches = sorted(matches, key=attrgetter('date'), reverse=True)

    # выбор матчей, которые сыграны
    matches = [match for match in matches if match.result != 'not played']

    # удаление повторяющихся матчей, если есть матч с обратным порядком команд
    matches = [match for match in matches if match.name_team1 < match.name_team2]

    return render(request, 'past_matches.html', {'matches': matches})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['login']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
    else:
        return render(request, 'login.html')


def chototo(request):
    update_data()
    return redirect('index')


def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        name = request.POST['name']
        surname = request.POST['surname']
        email = request.POST['email']
        if password1 != password2:
            return render(request, 'signup.html', {'error': 'Пароли не совпадают'})
        else:
            # проверка на уникальность логина
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, password=password1, first_name=name,
                                                last_name=surname,
                                                email=email)
                login(request, user)
                return redirect('index')
            else:
                return render(request, 'signup.html', {'error': 'Пользователь с таким логином уже существует'})
    else:
        return render(request, 'signup.html')


def custom_teams(request):
    teams = CustomTeam.objects.all()
    # если пользователь авторизован
    if request.user.is_authenticated:
        user_teams = CustomTeamPlayers.objects.filter(user=request.user)
    else:
        user_teams = []
    # если user_teams не пустой, то команду пользотеля можно удалить из списка команд
    return render(request, 'custom_teams.html', {'teams': teams, 'user_teams': user_teams})


def create_custom_team(request):
    if request.method == 'POST':
        name = request.POST['name']
        games = request.POST['games']
        wins = request.POST['wins']
        loses = request.POST['loses']
        try:
            description = request.POST['description']
        except:
            description = None
        captain = request.user
        try:
            logo = request.FILES['logo']
        except:
            logo = None
        try:
            logo_links = request.POST['logo_links']
        except:
            logo_links = None

        # проверка, что команда с таким названием уже существует
        if not CustomTeam.objects.filter(name=name).exists():
            if CustomTeam.objects.filter(captain=captain).exists():
                # получение подписки пользователя
                subscription = Subscriptions.objects.get(user=captain)
                if subscription is not None:
                    print(subscription.is_active, subscription.promo_period)
                    if subscription.is_active or subscription.promo_period:
                        if CustomTeam.objects.filter(captain=captain).count() == 2:
                            return render(request, 'create_custom_team.html',
                                          {'error': 'Вы исчерпали лимит команд'})
                        else:
                            CustomTeam.objects.create(name=name, games=games, wins=wins, loses=loses,
                                                      description=description, captain=captain, logo=logo,
                                                      logo_links=logo_links)
                            return redirect('team_detail', CustomTeam.objects.get(name=name).id)
                return render(request, 'create_custom_team.html',
                              {'error': 'У вас уже есть команда. Для создания второй команды необходима подписка'})
            else:
                CustomTeam.objects.create(name=name, games=games, wins=wins, loses=loses,
                                          description=description, captain=captain, logo=logo, logo_links=logo_links)
            return redirect('team_detail', CustomTeam.objects.get(name=name).id)
        else:
            return render(request, 'create_custom_team.html',
                          {'error': 'Команда с таким названием уже существует'})
    else:
        return render(request, 'create_custom_team.html')


def team_detail(request, team_id):
    team = CustomTeam.objects.get(id=team_id)
    players = CustomTeamPlayers.objects.filter(team=team)
    is_player = False
    if request.user.is_authenticated:
        is_player = request.user in [player.user for player in players]
    return render(request, 'team_detail.html', {'team': team, 'players': players, 'is_player': is_player})


def invite_player(request, team_id, user_id):
    team = CustomTeam.objects.get(id=team_id)
    user = User.objects.get(id=user_id)
    # если пользователь уже в команде, то не добавляем его
    if CustomTeamPlayers.objects.filter(user=user, team=team).exists():
        return render(request, 'team_invite.html', {'team': team, 'error': 'Пользователь уже в команде'})
    # если у пользователя уже есть команда, то не добавляем его
    elif CustomTeam.objects.filter(captain=user).exists():
        return render(request, 'team_invite.html', {'team': team, 'error': 'Пользователь уже в другой команде'})
    elif InviteNotification.objects.filter(user=user, team=team).exists():
        return render(request, 'team_invite.html',
                      {'team': team, 'error': 'Пользователь уже получал приглашение в эту команду'})
    else:
        InviteNotification.objects.create(user=user, team=team, notification_type='invite')
    return render(request, 'team_invite.html', {'team': team, 'success': 'Приглашение отправлено'})


def team_invite(request, team_id):
    team = CustomTeam.objects.get(id=team_id)
    if request.method == 'POST':
        query = request.POST['userSearch']
        users = User.objects.filter(first_name__startswith=query)
        results = [{'id': user.id, 'name': user.get_full_name()} for user in users]
        return render(request, 'team_invite.html', {'team': team, 'results': results})
    return render(request, 'team_invite.html', {'team': team})


def profile(request, user_id):
    user = User.objects.get(id=user_id)
    notifications = InviteNotification.objects.filter(user=user)
    unread_notification_count = notifications.filter(is_readed=False).count()
    user_teams = CustomTeamPlayers.objects.filter(user=user)
    try:
        sub = Subscriptions.objects.get(user=user)[0]
    except:
        sub = None
    if request.user == user:
        subs = Subscriptions.objects.filter(user=user)
        if subs.exists():
            for sub in subs:
                current_date = timezone.now()
                if sub.active_until < current_date:
                    sub.delete()

                if sub.payment_id is not None and sub.promo_period is False and sub.is_active is False and sub.is_paid is False:
                    payment = Payment.find_one(sub.payment_id)
                    if payment.status == 'succeeded':
                        sub.is_active = True
                        sub.is_paid = True
                        sub.save()
                    else:
                        sub.is_active = False
                        sub.save()
    print(sub)
    context = {
        'user': user,
        'notifications': notifications,
        'unread_notification_count': unread_notification_count,
        'user_teams': user_teams,
        'sub': sub,
    }
    return render(request, 'profile.html', context)


@login_required
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        notification = InviteNotification.objects.get(id=notification_id)
        notification.is_readed = True
        notification.save()
        return JsonResponse({'success': True})


def process_invite(request, notification_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        notification = InviteNotification.objects.get(id=notification_id)
        team = notification.team
        user = notification.user
        if action == 'accept':
            notification.is_invited = True
            CustomTeamPlayers.objects.create(user=user, team=team)
        elif action == 'decline':
            notification.is_rejected = True
        notification.save()
        return redirect('profile', user.id)
    return redirect('index')


def delete_notification(request, notification_id):
    if request.method == 'POST':
        notification = InviteNotification.objects.get(id=notification_id)
        notification.delete()
        return JsonResponse({'success': True})


def delete_player(request, team_id, player_id):
    if request.method == 'POST':
        player = CustomTeamPlayers.objects.get(id=player_id, team=team_id)
        player.delete()
        return JsonResponse({'success': True})


def inside_info(request, team_id):
    team_files = TeamFiles.objects.filter(team=team_id)
    return render(request, 'inside_info.html', {'team_files': team_files, 'team': team_id})


def create_inside_files(request, team_id):
    if request.method == 'POST':
        team = CustomTeam.objects.get(id=team_id)
        description = request.POST['description']
        file = None
        filename = None
        try:
            file = request.FILES['file']
            filename = file.name
        except:
            pass
        TeamFiles.objects.create(team=team, description=description, file=file, filename=filename)
        return redirect('inside_info', team_id)
    return render(request, 'create_inside_files.html', {'team': team_id})


@login_required
def buy_subscription(request):
    if request.method == 'POST':
        user = request.user
        subscription, created = Subscriptions.objects.get_or_create(user=user)

        if subscription.is_active:
            return render(request, 'buy_subscription.html', {'error': 'У вас уже есть активная подписка'})
        else:
            if 'buy' in request.POST and request.POST['buy'] == '':
                # Настройка ЮKassa
                Configuration.account_id = YOOKASSA_ACCOUNT_ID
                Configuration.secret_key = YOOKASSA_SECRET_KEY

                # Создание платежа в ЮKassa
                payment = Payment.create({
                    "amount": {
                        "value": str(900),
                        "currency": "RUB"
                    },
                    "confirmation": {
                        "type": "redirect",
                        "return_url": f"https://dreambasketball.fun"
                    },
                    "capture": True,
                    "description": f"Оплата подписки для пользователя {user.get_full_name()}"
                }, uuid.uuid4())

                subscription.payment_id = payment.id
                subscription.is_active = True
                subscription.is_paid = True
                subscription.active_until = timezone.now() + timedelta(days=subscription.term)
                subscription.save()

                return redirect(payment.confirmation.confirmation_url)
            elif 'promo' in request.POST and request.POST['promo'] == '':
                subscription.promo_period = True
                subscription.is_active = True
                subscription.active_until = timezone.now() + timedelta(days=subscription.term)
                subscription.save()
                return redirect('profile', user.id)

    return render(request, 'buy_subscription.html')


@login_required
def get_new_chat_messages(request, match_id):
    match = AllMatches.objects.get(id=match_id)
    last_message_id = request.GET.get('last_message_id', 0)
    new_messages = list(
        MatchChat.objects.filter(match=match, id__gt=last_message_id).values('id', 'user__username', 'message',
                                                                             'timestamp'))
    return JsonResponse({'messages': new_messages})


@login_required
def send_chat_message(request, match_id):
    if request.method == 'POST':
        match = AllMatches.objects.get(id=match_id)
        message = request.POST.get('message')
        if message:
            MatchChat.objects.create(match=match, user=request.user, message=message)
            return JsonResponse({'success': True})
    return JsonResponse({'success': False})


def team_remove(request, team_id):
    team = CustomTeam.objects.get(id=team_id)
    team.delete()
    return redirect('custom_teams')
