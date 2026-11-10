from django.urls import path

from .views import (
    BorrowBookView,
    MyBorrowedBooksView,
    LibrarianBorrowedBooksView,
    ReturnBookView,
)


app_name = 'borrowing'

urlpatterns = [
    path('borrow/<int:pk>/', BorrowBookView.as_view(), name='borrow_book'),
    path('my-books/', MyBorrowedBooksView.as_view(), name='my_borrowed_books'),
    path('librarian/borrowed-books/', LibrarianBorrowedBooksView.as_view(), name='librarian_borrowed_books'),
    path('return/<int:pk>/', ReturnBookView.as_view(), name='return_book'),
]