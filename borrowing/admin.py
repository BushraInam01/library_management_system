import logging

from django.conf import settings
from django.contrib import admin, messages
from django.core.mail import send_mail
from django.utils import timezone

from .models import BorrowRecord

logger = logging.getLogger(__name__)


@admin.action(description='Send overdue reminder emails to selected members')
def send_overdue_reminders(modeladmin, request, queryset):
    today = timezone.localdate()
    overdue = queryset.filter(
        returned_at__isnull=True,
        due_date__lt=today,
    ).select_related('user', 'book')

    sent = skipped = failed = 0

    for record in overdue:
        if not record.user.email:
            skipped += 1
            continue

        days_late = (today - record.due_date).days

        try:
            send_mail(
                subject=f'Library: "{record.book.title}" is overdue',
                message=(
                    f'Hello {record.user.get_full_name() or record.user.username},\n\n'
                    f'"{record.book.title}" was due on {record.due_date} '
                    f'and is now {days_late} day(s) overdue.\n'
                    'Please return it as soon as possible to avoid further fines.\n'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[record.user.email],
            )
            sent += 1
        except Exception:
            logger.exception('Overdue reminder failed for record %s', record.pk)
            failed += 1

    modeladmin.message_user(
        request,
        f'{sent} reminder(s) sent, {skipped} skipped (no email), {failed} failed.',
        messages.SUCCESS if not failed else messages.WARNING,
    )


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'book',
        'borrowed_at',
        'due_date',
        'returned_at',
        'is_returned',
        'is_overdue',
    )

    list_filter = (
        'due_date',
        'returned_at',
        'borrowed_at',
    )

    search_fields = (
        'user__username',
        'user__email',
        'book__title',
        'book__isbn',
    )

    readonly_fields = (
        'borrowed_at',
        'returned_at',
    )

    ordering = ('-borrowed_at',)

    actions = [send_overdue_reminders]
