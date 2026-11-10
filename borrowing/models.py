from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


def calculate_due_date():
    """
    Return a due date 14 days from today.
    """
    return timezone.localdate() + timedelta(days=14)


class BorrowRecord(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='borrow_records',
    )

    book = models.ForeignKey(
        'catalog.Book',
        on_delete=models.PROTECT,
        related_name='borrow_records',
    )

    borrowed_at = models.DateTimeField(
        auto_now_add=True,
    )

    due_date = models.DateField(
        default=calculate_due_date,
    )

    returned_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-borrowed_at']

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book'],
                condition=Q(returned_at__isnull=True),
                name='unique_active_borrow_per_user_book',
            ),
        ]

        indexes = [
            models.Index(fields=['user', 'returned_at']),
            models.Index(fields=['book', 'returned_at']),
            models.Index(fields=['due_date']),
        ]

    @property
    def is_returned(self):
        return self.returned_at is not None

    @property
    def is_overdue(self):
        return (
            not self.is_returned
            and self.due_date < timezone.localdate()
        )

    def __str__(self):
        return f'{self.user.username} - {self.book.title}'
