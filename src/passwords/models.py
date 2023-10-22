from django.db import models


class Password(models.Model):

    user_id = models.PositiveBigIntegerField(
        verbose_name='ID пользователя'
    )
    password = models.CharField(
        max_length=255,
        verbose_name='Пароль'
    )
    site = models.URLField(
        verbose_name='Ссылка на сайт'
    )
    site_alias = models.CharField(
        max_length=255,
        verbose_name='Сокращенный сайт'
    )

    class Meta:
        verbose_name = 'Пароль'
        verbose_name_plural = 'Пароли'

    def __str__(self):
        return f'{self.user_id} - {self.site}'

