from django.db import models
from django.contrib.auth.models import AbstractUser


class AuthUser(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Логин',
        help_text='Введите логин',
    )
    password = models.CharField(
        max_length=128,
        verbose_name='Пароль',
        help_text='Введите пароль'
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Почта',
        help_text='Введите почту',
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
        help_text='Введите имя',
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
        help_text='Введите фамилию',
    )

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'password']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username[:30]
