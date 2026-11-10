
from django.conf import settings
from django.db import models
from django.db.models import Q


class Reservation(models.Model):

    class Status(models.TextChoices):
        WAITING = 'WAITING', 'Waiting'
        READY = 'READY', 'Ready'
        FULFILLED = 'FULFILLED', 'Fulfilled'
        CANCELLED = 'CANCELLED', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations',
    )

    book = models.ForeignKey(
        'catalog.Book',
        on_delete=models.PROTECT,
        related_name='reservations',
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
    )

    reserved_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ['reserved_at', 'id']

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book'],
                condition=Q(
                    status__in=['WAITING', 'READY']
                ),
                name='unique_active_reservation_per_user_book',
            )
        ]

        indexes = [
            models.Index(
                fields=['book', 'status', 'reserved_at'],
                name='reservation_queue_idx',
            ),
            models.Index(
                fields=['user', 'status'],
                name='reservation_user_status_idx',
            ),
        ]

        verbose_name = 'Reservation'
        verbose_name_plural = 'Reservations'

    def __str__(self):
        return (
            f'{self.user.username} - '
            f'{self.book.title} ({self.status})'
        )

