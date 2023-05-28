from django.db import models


class Event(models.Model):

    user_id = models.PositiveBigIntegerField(
        verbose_name='ID пользователя'
    )
    at = models.DateTimeField(
        verbose_name='Когда'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    description = models.TextField(
        verbose_name='Описание'
    )

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    def __str__(self):
        return f'{self.user_id} - {self.title}'
