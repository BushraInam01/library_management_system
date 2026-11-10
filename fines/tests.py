
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import Book
from borrowing.models import BorrowRecord
from .forms import FinePaymentForm
from .models import Fine, FinePayment
from .services import create_fine_for_return


User = get_user_model()


class FineServiceTests(TestCase):

    def setUp(self):
        self.member = User.objects.create_user(
            username='test_member',
            password='TestPassword123!',
        )

        self.book = Book.objects.create(
            title='Test Django Book',
            author='Test Author',
            isbn='9781234567890',
            total_copies=3,
            available_copies=3,
        )

    def create_borrow_record(self, due_date):
        return BorrowRecord.objects.create(
            user=self.member,
            book=self.book,
            due_date=due_date,
        )

    def make_returned_at(self, return_date):
        return timezone.make_aware(
            datetime.combine(return_date, time(12, 0)),
            timezone.get_current_timezone(),
        )

    def test_no_fine_when_returned_on_due_date(self):
        due_date = timezone.localdate()
        record = self.create_borrow_record(due_date)

        returned_at = self.make_returned_at(due_date)

        fine = create_fine_for_return(
            record,
            returned_at=returned_at,
        )

        self.assertIsNone(fine)
        self.assertEqual(Fine.objects.count(), 0)

    def test_no_fine_when_returned_before_due_date(self):
        due_date = timezone.localdate() + timedelta(days=2)
        record = self.create_borrow_record(due_date)

        return_date = due_date - timedelta(days=1)

        fine = create_fine_for_return(
            record,
            returned_at=self.make_returned_at(return_date),
        )

        self.assertIsNone(fine)
        self.assertEqual(Fine.objects.count(), 0)

    def test_fine_calculated_for_three_overdue_days(self):
        due_date = timezone.localdate() - timedelta(days=3)
        record = self.create_borrow_record(due_date)

        returned_at = self.make_returned_at(
            due_date + timedelta(days=3)
        )

        fine = create_fine_for_return(
            record,
            returned_at=returned_at,
        )

        self.assertIsNotNone(fine)
        self.assertEqual(fine.overdue_days, 3)
        self.assertEqual(fine.rate_per_day, Decimal('50.00'))
        self.assertEqual(fine.total_amount, Decimal('150.00'))

    def test_duplicate_fine_is_not_created(self):
        due_date = timezone.localdate() - timedelta(days=3)
        record = self.create_borrow_record(due_date)

        returned_at = self.make_returned_at(
            due_date + timedelta(days=3)
        )

        first_fine = create_fine_for_return(
            record,
            returned_at=returned_at,
        )

        second_fine = create_fine_for_return(
            record,
            returned_at=returned_at,
        )

        self.assertEqual(first_fine.pk, second_fine.pk)
        self.assertEqual(Fine.objects.count(), 1)


class FinePaymentTests(TestCase):

    def setUp(self):
        self.member = User.objects.create_user(
            username='payment_member',
            password='TestPassword123!',
        )

        self.librarian = User.objects.create_user(
            username='test_librarian',
            password='TestPassword123!',
            role=User.Role.LIBRARIAN,
        )

        self.book = Book.objects.create(
            title='Payment Test Book',
            author='Test Author',
            isbn='9781234567891',
            total_copies=2,
            available_copies=2,
        )

        self.borrow_record = BorrowRecord.objects.create(
            user=self.member,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=3),
        )

        self.fine = Fine.objects.create(
            borrow_record=self.borrow_record,
            overdue_days=3,
            rate_per_day=Decimal('50.00'),
            total_amount=Decimal('150.00'),
        )

    def test_partial_payment_calculation(self):
        FinePayment.objects.create(
            fine=self.fine,
            amount=Decimal('50.00'),
            received_by=self.librarian,
        )

        self.fine.refresh_from_db()

        self.assertEqual(
            self.fine.amount_paid,
            Decimal('50.00'),
        )

        self.assertEqual(
            self.fine.outstanding_amount,
            Decimal('100.00'),
        )

        self.assertEqual(
            self.fine.payment_status,
            'PARTIALLY PAID',
        )


    def test_overpayment_is_rejected(self):
        # First, receive Rs. 50 payment.
        FinePayment.objects.create(
            fine=self.fine,
            amount=Decimal('50.00'),
            received_by=self.librarian,
        )

        # Outstanding amount is now Rs. 100.
        # Try to submit Rs. 101.
        form = FinePaymentForm(
            data={'amount': '101.00'},
            fine=self.fine,
        )
    
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)


    def test_valid_partial_payment_form(self):
        form = FinePaymentForm(
            data={'amount': '50.00'},
            fine=self.fine,
        )

        self.assertTrue(form.is_valid())

    def test_full_payment_changes_status_to_paid(self):
        FinePayment.objects.create(
            fine=self.fine,
            amount=Decimal('150.00'),
            received_by=self.librarian,
        )

        self.fine.refresh_from_db()

        self.assertEqual(
            self.fine.amount_paid,
            Decimal('150.00'),
        )

        self.assertEqual(
            self.fine.outstanding_amount,
            Decimal('0.00'),
        )

        self.assertEqual(
            self.fine.payment_status,
            'PAID',
        )

