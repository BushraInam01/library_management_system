
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from .models import Fine


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

    fine_rate = Decimal(str(settings.FINE_RATE_PER_DAY))

    total_amount = Decimal(overdue_days) * fine_rate

    fine, created = Fine.objects.get_or_create(
        borrow_record=borrow_record,
        defaults={
            'overdue_days': overdue_days,
            'rate_per_day': fine_rate,
            'total_amount': total_amount,
        }
    )

    return fine
