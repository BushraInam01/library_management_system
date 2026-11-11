
from import_export import resources

from .models import Book
from .services import adjust_book_copies


class BookResource(resources.ModelResource):
    """Import and export books using ISBN as the unique identifier."""

    class Meta:
        model = Book
        import_id_fields = ("isbn",)

        fields = (
            "isbn",
            "title",
            "author",
            "publisher",
            "publication_year",
            "description",
            "total_copies",
        )

        export_order = fields
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        """Normalize ISBN before matching an existing book."""

        if row.get("isbn"):
            row["isbn"] = (
                str(row["isbn"])
                .replace("-", "")
                .replace(" ", "")
                .upper()
            )

    def before_save_instance(self, instance, row, **kwargs):
        """Keep available copies consistent during CSV imports."""

        if (
            instance.total_copies is None
            or instance.total_copies < 1
        ):
            raise ValueError(
                "total_copies must be at least 1."
            )

        # New book: initially all copies are available.
        if instance.pk is None:
            instance.available_copies = instance.total_copies
            return

        # Existing book: use the central stock management service.
        updated_book = adjust_book_copies(
            instance,
            instance.total_copies,
        )

        instance.available_copies = updated_book.available_copies
