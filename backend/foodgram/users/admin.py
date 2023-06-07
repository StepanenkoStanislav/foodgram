from django.contrib import admin

from users.models import AuthUser


@admin.register(AuthUser)
class AuthUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'last_login', 'date_joined')
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
