from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import LibraryCard

User = get_user_model()


class AdminCardTests(TestCase):

    def setUp(self):
        self.admin_user = User.objects.create_superuser('boss', 'b@example.com', 'pass12345!')
        self.client.force_login(self.admin_user)

    def test_member_created_in_admin_gets_library_card(self):
        self.client.post(reverse('admin:accounts_user_add'), {
            'username': 'newmember',
            'password1': 'Str0ngPass!word',
            'password2': 'Str0ngPass!word',
            'role': 'MEMBER',
        })

        member = User.objects.get(username='newmember')
        self.assertTrue(LibraryCard.objects.filter(user=member).exists())

    def test_librarian_created_in_admin_gets_no_card(self):
        self.client.post(reverse('admin:accounts_user_add'), {
            'username': 'newlib',
            'password1': 'Str0ngPass!word',
            'password2': 'Str0ngPass!word',
            'role': 'LIBRARIAN',
        })

        self.assertFalse(LibraryCard.objects.filter(user__username='newlib').exists())

    def test_deactivate_and_activate_cards_actions(self):
        member = User.objects.create_user('m1', password='pass12345!')
        card = LibraryCard.objects.create(user=member)
        url = reverse('admin:accounts_librarycard_changelist')

        self.client.post(url, {'action': 'deactivate_cards', '_selected_action': [card.pk]})
        card.refresh_from_db()
        self.assertFalse(card.is_active)

        self.client.post(url, {'action': 'activate_cards', '_selected_action': [card.pk]})
        card.refresh_from_db()
        self.assertTrue(card.is_active)
