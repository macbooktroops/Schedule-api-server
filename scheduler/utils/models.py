from django.db import models


class TimestampedModel(models.Model):
    created_datetime = models.DateTimeField(
        verbose_name='생성일시',
        auto_now_add=True,
    )
    updated_datetime = models.DateTimeField(
        verbose_name='수정일시',
        auto_now=True,
    )

    class Meta:
        abstract = True
