# Проект Foodgram

## Описание проекта
 На этом сервисе пользователи могут публиковать рецепты, 
 подписываться на публикации других пользователей, добавлять 
 понравившиеся рецепты в список «Избранное», а перед походом в магазин 
 скачивать сводный список продуктов, необходимых для приготовления одного 
 или нескольких выбранных блюд.

### Адрес

http://foodgram.myftp.biz/

### Пользователи

Админ
```python
Логин - admin@mail.com
Пароль - admin
```

Для остальных пользователей пароль "123accaunt"


## Установка
В директории foodgram-project-react/infra необходимо создать файл .env (пример находится в foodgram-project-react/infra/example.env), где необходимо указать:
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
# В директории foodgram-project-react/infra
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

Описание [ендпоинтов API](http://foodgram.myftp.biz/api/docs/redoc.html)

## Технологии

В проекте используются следующие технологии:
- Python 3.7
- Django 3.2
- DjangoRestFramework 3.12.4
