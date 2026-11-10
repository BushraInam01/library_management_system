from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import User


class LibrarianRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow only librarians and superusers."""

    login_url = 'accounts:login'

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.role == User.Role.LIBRARIAN
