
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from import_export.admin import ImportExportModelAdmin

from borrowing.models import BorrowRecord
from reservations.models import Reservation

from .models import Book
from .resources import BookResource
from .services import adjust_book_copies
from .forms import normalize_and_validate_isbn


class BookAdminForm(forms.ModelForm):

    class Meta:
        model = Book
        fields = "__all__"

    def clean_isbn(self):
        isbn = self.cleaned_data["isbn"]
        return normalize_and_validate_isbn(isbn)

    def clean_total_copies(self):
        new_total = self.cleaned_data["total_copies"]

        if self.instance.pk:
            active_borrows = BorrowRecord.objects.filter(
                book=self.instance,
                returned_at__isnull=True,
            ).count()

            ready_reservations = Reservation.objects.filter(
                book=self.instance,
                status=Reservation.Status.READY,
            ).count()

            allocated = active_borrows + ready_reservations

            if new_total < allocated:
                raise ValidationError(
                    f"Cannot reduce total copies below {allocated}. "
                    "Some copies are currently borrowed or reserved."
                )

        return new_total


@admin.register(Book)
class BookAdmin(ImportExportModelAdmin):

    form = BookAdminForm
    resource_classes = [BookResource]

    list_display = (
        "title",
        "author",
        "isbn",
        "publisher",
        "publication_year",
        "total_copies",
        "available_copies",
    )

    list_filter = (
        "publication_year",
        "publisher",
    )

    search_fields = (
        "title",
        "author",
        "isbn",
        "publisher",
    )

    ordering = ("title",)

    readonly_fields = (
        "available_copies",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Book Information", {
            "fields": (
                "title",
                "author",
                "isbn",
                "publisher",
                "publication_year",
                "description",
            )
        }),
        ("Copies Information", {
            "fields": (
                "total_copies",
                "available_copies",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    def save_model(self, request, obj, form, change):

        if change:
            updated_book = adjust_book_copies(
                obj,
                obj.total_copies,
            )

            obj.available_copies = updated_book.available_copies

        else:
            obj.available_copies = obj.total_copies

        super().save_model(request, obj, form, change)
