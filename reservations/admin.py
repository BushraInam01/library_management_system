
from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'book',
        'status',
        'reserved_at',
        'updated_at',
    )

    list_filter = (
        'status',
        'reserved_at',
    )

    search_fields = (
        'user__username',
        'book__title',
        'book__isbn',
    )

    readonly_fields = (
        'reserved_at',
        'updated_at',
    )

    ordering = (
        'reserved_at',
        'id',
    )

    list_per_page = 20

