
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum


def get_default_fine_rate():
    return settings.FINE_RATE_PER_DAY


class Fine(models.Model):

    borrow_record = models.OneToOneField(
        'borrowing.BorrowRecord',
        on_delete=models.CASCADE,
        related_name='fine',
    )

    overdue_days = models.PositiveIntegerField()

    rate_per_day = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=get_default_fine_rate,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Fine'
        verbose_name_plural = 'Fines'

    @property
    def amount_paid(self):
        total = self.payments.aggregate(
            total=Sum('amount')
        )['total']

        return total or Decimal('0.00')

    @property
    def outstanding_amount(self):
        return self.total_amount - self.amount_paid

    @property
    def payment_status(self):
        if self.outstanding_amount <= Decimal('0.00'):
            return 'PAID'

        if self.amount_paid > Decimal('0.00'):
            return 'PARTIALLY PAID'

        return 'UNPAID'

    def __str__(self):
        return (
            f'Fine for {self.borrow_record.user.username} - '
            f'{self.borrow_record.book.title}'
        )


class FinePayment(models.Model):

    fine = models.ForeignKey(
        Fine,
        on_delete=models.CASCADE,
        related_name='payments',
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='received_fine_payments',
    )

    payment_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Fine Payment'
        verbose_name_plural = 'Fine Payments'

    def __str__(self):
        return (
            f'Payment of Rs. {self.amount} '
            f'for Fine #{self.fine.pk}'
        )
