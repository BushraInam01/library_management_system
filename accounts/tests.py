
from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from borrowing.models import BorrowRecord
from catalog.models import Book


User = get_user_model()


class SuperuserRoleTests(TestCase):

    def test_superuser_automatically_gets_librarian_role(self):
        superuser = User.objects.create_superuser(
            username='test_superuser',
            email='superuser@example.com',
            password='StrongPass123!',
        )

        self.assertTrue(superuser.is_superuser)

        self.assertEqual(
            superuser.role,
            User.Role.LIBRARIAN,
        )

    def test_superuser_role_is_preserved_with_update_fields(self):
        superuser = User.objects.create_superuser(
            username='update_superuser',
            email='update@example.com',
            password='StrongPass123!',
        )

        # Simulate an attempt to save another role.
        superuser.role = User.Role.MEMBER
        superuser.first_name = 'Updated'

        superuser.save(update_fields=['first_name'])

        superuser.refresh_from_db()

        self.assertEqual(
            superuser.role,
            User.Role.LIBRARIAN,
        )


class MemberDeletionProtectionTests(TestCase):

    def test_member_with_borrowing_history_cannot_be_deleted(self):
        member = User.objects.create_user(
            username='protected_member',
            password='StrongPass123!',
        )

        book = Book.objects.create(
            title='Protected Book',
            author='Test Author',
            isbn='9780306406157',
            total_copies=2,
            available_copies=1,
        )

        borrow_record = BorrowRecord.objects.create(
            user=member,
            book=book,
        )

        with self.assertRaises(ProtectedError):
            member.delete()

        # Member and borrowing history must remain in database.
        self.assertTrue(
            User.objects.filter(pk=member.pk).exists()
        )

        self.assertTrue(
            BorrowRecord.objects.filter(
                pk=borrow_record.pk
            ).exists()
        )