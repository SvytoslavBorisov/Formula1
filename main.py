import configparser
import os

import pyodbc
import sys
import functions

'''Библиотека FLASK'''
from flask import Flask, render_template, redirect, request, make_response, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
import requests

'''Классы для работы с формами для работы с пользователем'''
from forms.register import RegisterForm
from forms.login import LoginForm

from data.users import User

from api import users_api, racer_api, teams_api, countries_api, tracks_api
from data.db_connect import db_connect
from data import db_session

'''Запуск приложения FLASK'''
app = Flask(__name__)

'''Настройка приложения для того, чтобы можно было сохранять русские символы в json'''
app.config.update(
    JSON_AS_ASCII=False
)
CORS(app)
'''Инициализируем LoginManager'''
login_manager = LoginManager()
login_manager.init_app(app)

'''Соединение с Базой Данных'''
db_session.global_init("db/baseDate.sqlite")
app.register_blueprint(users_api.blueprint)
app.register_blueprint(racer_api.blueprint)
app.register_blueprint(teams_api.blueprint)
app.register_blueprint(countries_api.blueprint)
app.register_blueprint(tracks_api.blueprint)


'''Эта настройка защитит наше приложение от межсайтовой подделки запросов'''
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

'''Cоздаём объекта парсера. Читаем конфигурационный файл'''
config = configparser.ConfigParser()
config_play = configparser.ConfigParser()
config.read("config.ini", encoding='utf-8')

'''Функция для получения пользователя'''


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


'''Выход из аккаунта для пользователя'''


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/login', methods=['POST', 'GET'])
def login():

    session = db_session.create_session()

    if request.method == 'POST':           # 2
        user = session.query(User).filter(User.email == request.form['email']).first()  # 3

        if user.check_password(request.form['psw']):                                    # 4
            login_user(user)
            return redirect('/')

    return redirect('/')


@app.route('/register', methods=['POST', 'GET'])
def register():

    session = db_session.create_session()

    if request.method == 'POST':
        user = session.query(User).filter(User.email == request.form['email']).first()
        if user.check_password(request.form['password']):
            login_user(user)
            redirect('/')
    return redirect('/')


@app.route('/')
def main_page():
    db_connect('SELECT * FROM Racer')

    registerForm = RegisterForm()
    loginForm = LoginForm()

    return render_template('main_page.html', formLogin=loginForm, formRegister=registerForm)


@app.route('/career_racer_play')
def career_racer_play():
    db_connect('SELECT * FROM Racer')

    return render_template('career_racer_play.html')


@app.route('/career_racer_start')
def career_racer_start():

    if current_user.is_authenticated:
        nations = db_connect('SELECT * From Country')
        teams = db_connect('SELECT * From View_Team')
        teams1 = db_connect('SELECT * From Team')
        racers = []
        for x in teams1:
            t = db_connect(f'SELECT * From Racer WHERE team = {x[0]}')
            racers.append(t)
        tracks = db_connect('SELECT * From Track')

        print(racers)
        param = functions.fill_dict(
            title='F1 Manager',
            teams=teams,
            tracks=tracks,
            nations=nations,
            racers=racers)

        return render_template('career_racer_start.html', **param)

    return redirect('/')


@app.route('/career_team_start')
def career_team_start():

    if current_user.is_authenticated:
        nations = db_connect('SELECT * From Country')
        companies = db_connect('SELECT * From Company')

        param = functions.fill_dict(
            title='F1 Manager',
            nations=nations,
            companies=companies)

        return render_template('career_team_start.html', **param)

    return redirect('/')


@app.route('/database')
def database():
    if current_user.state == 'admin':
        racers = db_connect('SELECT * FROM View_Racer')
        teams = db_connect('SELECT * FROM View_Team')
        tracks = db_connect('SELECT * FROM View_Track')
        countries = db_connect('SELECT * FROM Country')
        print(teams)
        param = functions.fill_dict(
            title='',
            racers=racers,
            teams=teams,
            countries=countries,
            tracks=tracks)
        return render_template('database.html', **param)
    return redirect('/')


@app.route('/rating')
def rating():
    if current_user.state == 'admin':
        racers = db_connect('SELECT name, surname, nation, team, points FROM View_Racer ORDER BY points DESC;')
        teams = db_connect('SELECT title FROM View_Team')

        teams1 = db_connect('SELECT * From Team')
        points = []
        for i, x in enumerate(teams1):
            t = db_connect(f'SELECT points From Racer WHERE team = {x[0]}')
            points.append([teams[i], sum(x[0] for x in t)])
        points.sort(key=lambda x: -x[1])
        param = functions.fill_dict(
            title='',
            racers=racers,
            teams=teams,
            points=points)
        return render_template('rating.html', **param)
    return redirect('/')


@app.route('/racers')
def racers():
    racers = db_connect('SELECT * FROM View_Racer')
    teams = db_connect('SELECT * FROM Team')
    nations = db_connect('SELECT * FROM Country')
    tracks = db_connect('SELECT * FROM Track')
    maxs = db_connect('SELECT MAX(age), MAX(rating), MAX(salary), MAX(points) FROM Racer;')
    print('racers')
    param = functions.fill_dict(
        title='',
        racers=racers,
        teams=[list(x) for x in teams],
        nations=[list(x) for x in nations],
        tracks=[list(x) for x in tracks],
        maxs=maxs[0])
    return render_template('racers.html', **param)


@app.route('/teams')
def teams():
    racers = db_connect('SELECT * FROM View_Racer')
    nations = db_connect('SELECT * FROM Country')
    companies = db_connect('SELECT * FROM Company')
    maxs = db_connect('SELECT MAX(funs), MAX(budget) FROM Team;')

    param = functions.fill_dict(
        title='',
        racers=racers,
        nations=[list(x) for x in nations],
        companies=[list(x) for x in companies],
        maxs=maxs[0])
    return render_template('teams.html', **param)


@app.route('/tracks')
def tracks():
    racers = db_connect('SELECT * FROM View_Track')
    nations = db_connect('SELECT * FROM Country')
    companies = db_connect('SELECT * FROM Company')
    maxs = db_connect('SELECT MAX(length), MAX(turns) FROM Track;')
    mins = db_connect('SELECT MIN(length), MIN(turns) FROM Track;')

    param = functions.fill_dict(
        title='',
        racers=racers,
        nations=[list(x) for x in nations],
        companies=[list(x) for x in nations],
        maxs=maxs[0],
        mins=mins[0])

    return render_template('tracks.html', **param)


@app.route('/countries')
def countries():
    maxs = db_connect('SELECT MAX(id) FROM Country;')

    param = functions.fill_dict(
        title='',
        maxs=maxs[0])
    return render_template('countries.html', **param)


@app.route('/test')
def test():
    racers = db_connect('SELECT * FROM View_Racer')
    param = functions.fill_dict(
        title='',
        racers=racers)
    return render_template('test.html', **param)


@app.route('/global_search+<query_>')
def global_search(query_):
    results = db_connect(f"SELECT * FROM SearchTables('{query_}');")

    result_dict = {}
    print(results)
    for key, value in results:
        if key not in result_dict:
            result_dict[key] = [value]
        else:
            result_dict[key].append(value)
    for x, y in result_dict.items():
        print(x, y)
    return render_template('global_search.html', results=result_dict)


'''
    Отправка POST, PUT, GET, DELETE запросов для работы с пользователями с использованием ТОКЕНА.
    Вызов этих страниц происходит в коде html (js)
'''


'''
    Страница информации о пользователе.
    1. Проверка была ли начата игра текущим пользователем
    2. Если у текущего пользователя есть незаконченная игра, то он будет должен ее доиграть
    3. Подключение к базе данных
    4. В пути указывается никнейм пользователя, чей это профиль
    5. Получаем пользователя из БД, чей это профиль. Получаем все категории
    6. Создание форм для регистрации и авторизации пользователя, создания вопроса
    7. Заполнение формы для добавления вопроса
    8. Создание словаря для работы с переменными в html коде
        'title'            - Заголовок страницы
        'style'            - Названия файлов, в которых храняться стили для данной страницы
        'path_for_style'   - Путь к папке со стилями
        'style_for_mobile' - Путь к файлу с css стилями для мобильного устройства
        'user'             - Пользователь, чей это профиль
        'games'            - Игры пользователя, чей это профиль
        'procent_win'      - Процент побед
        'procent_def'      - Процент поражений
    9. Рендеринг
'''


@app.route('/user_info/<int:id_>')
def user_info(id_):

    session = db_session.create_session()
    user = session.query(User).filter(User.id == id_).first()

    if user:
        registerForm = RegisterForm()
        loginForm = LoginForm()

        param = functions.fill_dict(
            title='Профиль',
            user=user)

        return render_template('user_info.html', **param, formLogin=loginForm, formRegister=registerForm)
    return redirect('/')


@app.route('/edit_avatar/<int:id_>', methods=['POST'])
def edit_avatar(id_):

    if current_user.is_authenticated and current_user.id == id_:

        session = db_session.create_session()

        user = session.query(User).filter(User.id == current_user.id).first()

        if user:
            if user.avatar != '/static/img/users_avatars/no_photo.png':
                os.remove(user.avatar[1:])
            user.avatar = f'/static/img/users_avatars/{user.id}+{functions.get_time()}.png'
            with open(user.avatar[1:], 'wb') as f1:
                f1.write(request.files['edit_avatar'].read())

            session.commit()
        return redirect('/user_info/' + str(current_user.id))
    return redirect('/')


@app.route('/adminka/')
@login_required
def adminka():
    if current_user.is_authenticated and current_user.state == 'admin':  # 1

        param = functions.fill_dict(  # 2
            title='Админка')

        return render_template('adminka.html', **param)   # 3
    return redirect('/')


@app.route('/admin_users/')
@login_required
def admin_users():

    if current_user.is_authenticated and current_user.state == 'admin':  # 1

        session = db_session.create_session()

        users = session.query(User).all()
        param = functions.fill_dict(                                               # 2
            title='Редактировать пользователей',
            users=[{'id': x.id,
                    'nickname': x.nickname,
                    'email': x.email,
                    'rating': x.rating,
                    'start_date': x.start_date,
                    'state': config['ADMIN_STATE'][x.state],  # Перевод статуса в слова
                    'link_vk': x.link_vk,
                    'avatar': x.avatar} for x in users])
        return render_template('admin_users.html', **param)   # 3
    return redirect('/')


@app.route('/check_edit_or_show_users/<id_>', methods=['POST', 'PUT', 'GET', 'DELETE'])
def check_edit_or_show_users(id_):
    if current_user.is_authenticated and current_user.state == 'admin':
        if request.method == 'PUT':
            return requests.put(f'http://127.0.0.1:5000/api/put_user/' + id_, data=request.form, files=request.files).json()
        elif request.method == 'DELETE':
            return requests.delete(f'http://127.0.0.1:5000/api/delete_user/' + id_).json()
        elif request.method == 'GET':
            return requests.get(f'http://127.0.0.1:5000/api/users').json()
    if request.method == 'POST':
        return requests.post(f'http://127.0.0.1:5000/api/add_user', data=request.form, files=request.files).json()


# if __name__ == "__main__":
#    app.run(port=8080)

app.run()
