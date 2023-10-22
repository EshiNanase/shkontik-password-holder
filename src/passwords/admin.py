from django.contrib import admin
from django.contrib.auth.models import Group, User
from .models import Password

admin.site.unregister(Group)
admin.site.unregister(User)


@admin.register(Password)
class PasswordAdmin(admin.ModelAdmin):

    class Meta:
        model = Password

