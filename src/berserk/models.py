from django.db import models


class TableLink(models.Model):

    user_id = models.PositiveBigIntegerField(
        unique=True,
        verbose_name='ID пользователя'
    )
    link = models.URLField(
        verbose_name='Ссылка на таблицу'
    )

    class Meta:
        verbose_name = 'Ссылка на таблицу'
        verbose_name_plural = 'Ссылки на таблицы'
