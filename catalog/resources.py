from import_export import resources

from .models import Book


class BookResource(resources.ModelResource):
    """CSV/Excel import and export for books, matched on ISBN.

    ``available_copies`` is deliberately not importable: it is managed by
    the borrow/return workflow. New books start with every copy available,
    and changing ``total_copies`` on an existing book shifts the available
    count by the same amount.
    """

    class Meta:
        model = Book
        import_id_fields = ('isbn',)
        fields = (
            'isbn',
            'title',
            'author',
            'publisher',
            'publication_year',
            'description',
            'total_copies',
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        if row.get('isbn'):
            row['isbn'] = (
                str(row['isbn']).replace('-', '').replace(' ', '').upper()
            )

    def before_save_instance(self, instance, row, **kwargs):
        if instance.total_copies is None or instance.total_copies < 1:
            raise ValueError('total_copies must be at least 1.')

        if instance.pk is None:
            instance.available_copies = instance.total_copies
            return

        previous_total = (
            Book.objects.filter(pk=instance.pk)
            .values_list('total_copies', flat=True)
            .get()
        )
        instance.available_copies = max(
            0,
            instance.available_copies + (instance.total_copies - previous_total),
        )
