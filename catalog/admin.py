from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Book
from .resources import BookResource


@admin.register(Book)
class BookAdmin(ImportExportModelAdmin):

    resource_classes = [BookResource]

    list_display = (
        'title',
        'author',
        'isbn',
        'publisher',
        'publication_year',
        'total_copies',
        'available_copies',
    )

    list_filter = (
        'publication_year',
        'publisher',
    )

    search_fields = (
        'title',
        'author',
        'isbn',
        'publisher',
    )

    ordering = ('title',)

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Book Information', {
            'fields': (
                'title',
                'author',
                'isbn',
                'publisher',
                'publication_year',
                'description',
            )
        }),
        ('Copies Information', {
            'fields': (
                'total_copies',
                'available_copies',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )
