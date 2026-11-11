
from django.contrib import admin, messages

from .models import Reservation
from .services import cancel_reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'book',
        'status',
        'ready_until',
        'reserved_at',
        'updated_at',
    )

    list_filter = (
        'status',
        'reserved_at',
        'ready_until',
    )

    search_fields = (
        'user__username',
        'book__title',
        'book__isbn',
    )

    readonly_fields = (
        'user',
        'book',
        'status',
        'reserved_at',
        'ready_until',
        'updated_at',
    )

    ordering = (
        'reserved_at',
        'id',
    )

    list_per_page = 20

    actions = [
        'cancel_selected_reservations',
    ]

    def has_add_permission(self, request):
        # Reservations must be created through the member workflow.
        return False

    def has_delete_permission(self, request, obj=None):
        # Preserve reservation history.
        return False

    @admin.action(
        description='Cancel selected active reservations'
    )
    def cancel_selected_reservations(self, request, queryset):
        cancelled_count = 0
        skipped_count = 0

        for reservation in queryset:
            try:
                cancel_reservation(reservation)
                cancelled_count += 1

            except ValueError:
                skipped_count += 1

        if cancelled_count:
            self.message_user(
                request,
                f'{cancelled_count} reservation(s) cancelled successfully.',
                level=messages.SUCCESS,
            )

        if skipped_count:
            self.message_user(
                request,
                f'{skipped_count} reservation(s) skipped because they were not active.',
                level=messages.WARNING,
            )

        if not cancelled_count and not skipped_count:
            self.message_user(
                request,
                'No reservations were selected.',
                level=messages.INFO,
            )
