from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from borrowing.models import BorrowRecord
from catalog.models import Book

from .models import Fine, FinePayment

User = get_user_model()


class MarkFinesPaidActionTests(TestCase):

    def setUp(self):
        self.admin_user = User.objects.create_superuser('boss', 'b@example.com', 'pass12345!')
        self.client.force_login(self.admin_user)
        member = User.objects.create_user('m', password='pass12345!')
        book = Book.objects.create(
            title='B', author='A', isbn='9780306406157',
            total_copies=1, available_copies=1,
        )
        record = BorrowRecord.objects.create(
            user=member, book=book,
            due_date=timezone.localdate() - timedelta(days=4),
        )
        self.fine = Fine.objects.create(
            borrow_record=record, overdue_days=4,
            rate_per_day=Decimal('50.00'), total_amount=Decimal('200.00'),
        )
        self.url = reverse('admin:fines_fine_changelist')

    def test_action_pays_outstanding_balance_once(self):
        FinePayment.objects.create(fine=self.fine, amount=Decimal('50.00'), received_by=self.admin_user)
        data = {'action': 'mark_fines_paid', '_selected_action': [self.fine.pk]}

        self.client.post(self.url, data)
        self.client.post(self.url, data)

        self.assertEqual(self.fine.outstanding_amount, Decimal('0.00'))
        self.assertEqual(self.fine.payment_status, 'PAID')
        self.assertEqual(self.fine.payments.count(), 2)
        self.assertEqual(self.fine.payments.latest('payment_date').amount, Decimal('150.00'))
