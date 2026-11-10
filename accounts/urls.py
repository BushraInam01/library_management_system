from django.urls import path

from .views import (
    MemberRegistrationView,
    MemberLoginView,
    MemberLogoutView,
    DashboardRedirectView,
    MemberDashboardView,
    LibrarianDashboardView,
)

app_name = 'accounts'

urlpatterns = [
    path('register/', MemberRegistrationView.as_view(), name='register'),
    path('login/', MemberLoginView.as_view(), name='login'),
    path('logout/', MemberLogoutView.as_view(), name='logout'),

    path('dashboard/', DashboardRedirectView.as_view(), name='dashboard'),
    path('dashboard/member/', MemberDashboardView.as_view(), name='member_dashboard'),
    path('dashboard/librarian/', LibrarianDashboardView.as_view(), name='librarian_dashboard'),
]