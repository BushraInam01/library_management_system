from decimal import Decimal

from django.utils import timezone

from .models import Fine


FINE_RATE_PER_DAY = Decimal('50.00')


def create_fine_for_return(borrow_record, returned_at=None):

    if returned_at is None:
        returned_at = timezone.now()

    return_date = timezone.localdate(returned_at)

    overdue_days = (
        return_date - borrow_record.due_date
    ).days

    # No fine if the book is returned on time.
    if overdue_days <= 0:
        return None

    total_amount = (
        Decimal(overdue_days) * FINE_RATE_PER_DAY
    )

    fine, created = Fine.objects.get_or_create(
        borrow_record=borrow_record,
        defaults={
            'overdue_days': overdue_days,
            'rate_per_day': FINE_RATE_PER_DAY,
            'total_amount': total_amount,
        }
    )

    return fine