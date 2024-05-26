import requests
from bs4 import BeautifulSoup


def get_text_news(url):
    # создаем файл, в который будем записывать новости
    with open('news.txt', 'a') as file:
        response = requests.get(f'https://www.sports.ru' + url)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_text = soup.find('div', class_='news-item__content js-mediator-article').find_all('p')
        file.write('НОВОСТЬ: \n')
        for text in news_text:
            # print(text.text)
            file.write(text.text)

        file.write('\n')

    file.close()


def get_news():
    url = 'https://www.sports.ru/basketball/news/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    news = soup.find('div', class_='news').find('div', class_='short-news')
    date = news.find('b').text
    print(date)
    news_titles = news.find_all('p')
    for news_title in news_titles:
        print(news_title.find('span', class_='time').text,
              news_title.find('a').text + ' ' + news_title.find('a').get('href'))


def stat():
    # Задайте URL страницы
    url = "https://www.sports.ru/basketball/match/bk-nizhni-novgorod-vs-cmoki-minsk/"

    # Отправьте GET-запрос к странице
    response = requests.get(url)
    html_content = response.content

    # Используйте BeautifulSoup для парсинга HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Найдите все таблицы на странице
    tables = soup.find_all('table', class_='stat-table')

    # Проход по каждой таблице
    for table in tables:
        # Извлеките данные из каждой строки
        rows = table.find_all('tr')
        for row in rows:
            # Извлечение данных из ячеек
            cells = row.find_all(['td', 'th'])
            for cell in cells:
                print(cell.text.strip(), end='\t')
            print("\n")

        print("\n" + "=" * 50 + "\n")


def parse_table(url):
    # Отправьте GET-запрос к странице
    response = requests.get(url)
    html_content = response.content

    # Используйте BeautifulSoup для парсинга HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Найдите все таблицы на странице
    tables = soup.find_all('table', class_='stat-table')

    # Переменная для хранения данных
    parsed_data = []

    # Проход по каждой таблице
    for table in tables:
        # Извлеките данные из каждой строки
        rows = table.find_all('tr')
        for row in rows[1:]:  # Пропустите первую строку, так как это заголовки
            # Извлечение данных из ячеек
            cells = row.find_all(['td', 'th'])
            row_data = [cell.text.strip() for cell in cells]
            parsed_data.append(row_data)

    return parsed_data


def your_view():
    # URL страницы с таблицей
    url = "https://www.sports.ru/basketball/match/bk-nizhni-novgorod-vs-cmoki-minsk/"

    # Вызов функции парсинга
    parsed_data = parse_table(url)
    print(parsed_data)


your_view()
