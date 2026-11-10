from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import MemberRegistrationForm
from .models import LibraryCard, User


class MemberRegistrationView(FormView):
    template_name = 'accounts/register.html'
    form_class = MemberRegistrationForm
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        with transaction.atomic():
            user = form.save()
            LibraryCard.objects.create(user=user)

        messages.success(
            self.request,
            'Your account and library card have been created successfully. Please log in.'
        )
        return super().form_valid(form)


class MemberLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class MemberLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')


class DashboardRedirectView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        user = request.user

        if user.is_superuser:
            return redirect('admin:index')

        if user.role == User.Role.LIBRARIAN:
            return redirect('accounts:librarian_dashboard')

        return redirect('accounts:member_dashboard')


class MemberDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect('admin:index')

            if request.user.role != User.Role.MEMBER:
                return HttpResponseForbidden(
                    'You are not authorized to access the Member Dashboard.'
                )

        return super().dispatch(request, *args, **kwargs)


class LibrarianDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/librarian_dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect('admin:index')

            if request.user.role != User.Role.LIBRARIAN:
                return HttpResponseForbidden(
                    'You are not authorized to access the Librarian Dashboard.'
                )

        return super().dispatch(request, *args, **kwargs)