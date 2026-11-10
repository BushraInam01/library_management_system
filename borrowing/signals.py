import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BorrowRecord

logger = logging.getLogger(__name__)


def send_due_date_email(borrow_record_id):
    """Email the member their due date. Never lets a mail failure break borrowing."""
    record = (
        BorrowRecord.objects
        .select_related('user', 'book')
        .filter(pk=borrow_record_id)
        .first()
    )

    if record is None or not record.user.email:
        return

    try:
        send_mail(
            subject=f'Library: "{record.book.title}" is due on {record.due_date}',
            message=(
                f'Hello {record.user.get_full_name() or record.user.username},\n\n'
                f'You borrowed "{record.book.title}".\n'
                f'Please return it by {record.due_date:%A, %d %B %Y}.\n\n'
                'Overdue books are charged a daily fine.\n'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[record.user.email],
        )
    except Exception:
        logger.exception(
            'Could not send due-date email for borrow record %s',
            borrow_record_id,
        )


@receiver(post_save, sender=BorrowRecord)
def borrow_record_created(sender, instance, created, **kwargs):
    if created:
        # Send only after the borrowing transaction has committed.
        transaction.on_commit(lambda: send_due_date_email(instance.pk))
