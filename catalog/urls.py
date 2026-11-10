from django.urls import path

from .views import (
    ISBNLookupView,
    BookCreateView,
    BookListView,
    BookDetailView,
)

app_name = 'catalog'

urlpatterns = [
    path('', BookListView.as_view(), name='book_list'),
    path('isbn-lookup/', ISBNLookupView.as_view(), name='isbn_lookup'),
    path('books/add/', BookCreateView.as_view(), name='book_create'),
    path('books/<int:pk>/', BookDetailView.as_view(), name='book_detail'),
]