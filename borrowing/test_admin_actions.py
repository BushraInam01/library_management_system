from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Book

from .models import BorrowRecord

User = get_user_model()


class OverdueReminderActionTests(TestCase):

    def setUp(self):
        self.admin_user = User.objects.create_superuser('boss', 'b@example.com', 'pass12345!')
        self.client.force_login(self.admin_user)
        self.book = Book.objects.create(
            title='Late Book', author='A', isbn='9780306406157',
            total_copies=2, available_copies=2,
        )
        self.url = reverse('admin:borrowing_borrowrecord_changelist')

    def _record(self, username, email, days_until_due):
        user = User.objects.create_user(username, email=email, password='pass12345!')
        return BorrowRecord.objects.create(
            user=user, book=self.book,
            due_date=timezone.localdate() + timedelta(days=days_until_due),
        )

    def test_only_overdue_unreturned_loans_with_email_are_reminded(self):
        overdue = self._record('late', 'late@example.com', -3)
        on_time = self._record('ontime', 'ontime@example.com', 5)
        no_email = self._record('noemail', '', -2)
        mail.outbox.clear()

        self.client.post(self.url, {
            'action': 'send_overdue_reminders',
            '_selected_action': [overdue.pk, on_time.pk, no_email.pk],
        })

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['late@example.com'])
        self.assertIn('3 day(s) overdue', mail.outbox[0].body)
