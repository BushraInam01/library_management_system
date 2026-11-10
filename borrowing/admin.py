from django.contrib import admin

from .models import BorrowRecord


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
