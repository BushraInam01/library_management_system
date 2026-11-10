from django.apps import AppConfig


class BorrowingConfig(AppConfig):
    name = 'borrowing'

    def ready(self):
        from . import signals  # noqa: F401
