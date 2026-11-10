from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class ReservationAdminTests(TestCase):

    def test_search_does_not_crash(self):
        admin_user = User.objects.create_superuser('boss', 'b@example.com', 'pass12345!')
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse('admin:reservations_reservation_changelist'), {'q': '978'}
        )

        self.assertEqual(response.status_code, 200)
