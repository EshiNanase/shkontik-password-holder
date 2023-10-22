from django.contrib import admin
from .models import TableLink


@admin.register(TableLink)
class TableLinkAdmin(admin.ModelAdmin):

    class Meta:
        model = TableLink
        