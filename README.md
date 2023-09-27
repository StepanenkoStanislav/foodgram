# Проект Foodgram

## Описание проекта
 На этом сервисе пользователи могут публиковать рецепты, 
 подписываться на публикации других пользователей, добавлять 
 понравившиеся рецепты в список «Избранное», а перед походом в магазин 
 скачивать сводный список продуктов, необходимых для приготовления одного 
 или нескольких выбранных блюд.

Описание [ендпоинтов API](http://localhost/api/docs/redoc.html)


## Установка
В директории foodgram/infra необходимо создать файл .env (пример находится в foodgram/infra/example.env), где необходимо указать:
```python
DB_ENGINE=django.db.backends.postgresql - указываем, что работаем с postgresql
DB_NAME=foodgram_user - имя базы данных
POSTGRES_USER=foodgram_user - логин для подключения к базе данных
POSTGRES_PASSWORD=1234 - пароль для подключения к БД
DB_HOST=db - название сервиса (контейнера)
DB_PORT=5432 - порт для подключения к БД 
SECRET_KEY=secret_key - SECRET_KEY из settings.py
```

Запуск проекта
```python
# В директории foodgram/infra
docker-compose up --build
docker-compose exec backend python manage.py migrate
```

Создание суперпользователя
```python
docker-compose exec backend python manage.py createsuperuser
```

Собрать статические файлы
```python
docker-compose exec backend python manage.py collectstatic
```

Загрузить тестовые данные
```python
docker-compose cp ../data/data.json backend:/app/
docker-compose cp ../data/media backend:/app/
docker-compose exec backend python manage.py loaddata data.json
```

## Технологии

<div>
  <img src="https://github.com/devicons/devicon/blob/master/icons/python/python-original.svg" title="python" alt="python" width="40" height="40"/>&nbsp
  <img src="https://github.com/devicons/devicon/blob/master/icons/django/django-plain.svg" title="django" alt="django" width="40" height="40"/>&nbsp
  <img src="https://github.com/devicons/devicon/blob/master/icons/docker/docker-original.svg" title="docker" alt="docker" width="40" height="40"/>&nbsp
  <img src="https://github.com/devicons/devicon/blob/master/icons/postgresql/postgresql-original.svg" title="postgresql" alt="postgresql" width="40" height="40"/>&nbsp
</div>

В проекте используются следующие технологии:
- Python 3.7
- Django 3.2
- DjangoRestFramework 3.12.4
- Postgresql 13.0-alpine
- Docker 20.10.24

## Автор

[![Telegram Badge](https://img.shields.io/badge/StepanenkoStanislav-blue?logo=telegram&logoColor=white)](https://t.me/tme_zoom) [![Gmail Badge](https://img.shields.io/badge/-Gmail-red?style=flat&logo=Gmail&logoColor=white)](mailto:stepanenko.s.a.dev@gmail.com)
