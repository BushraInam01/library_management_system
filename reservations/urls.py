
from django.urls import path

from .views import (
    CreateReservationView,
    MyReservationsView,
    CancelReservationView,
    LibrarianReservationsView,
)

app_name = 'reservations'

urlpatterns = [
    path('reserve/<int:book_id>/', CreateReservationView.as_view(), name='create'),
    path('my-reservations/', MyReservationsView.as_view(), name='my_reservations'),
    path('cancel/<int:pk>/', CancelReservationView.as_view(), name='cancel'),
    path('manage/', LibrarianReservationsView.as_view(), name='manage'),
]

