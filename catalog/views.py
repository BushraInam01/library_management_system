import re
import requests

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.urls import reverse_lazy
from django.views.generic import FormView, CreateView
from django.db.models import Q
from django.views.generic import ListView, DetailView
from reservations.models import Reservation
from borrowing.models import BorrowRecord

from accounts.models import User

from .forms import ISBNLookupForm, BookForm
from .models import Book


class LibrarianAccessMixin(
    LoginRequiredMixin,
    UserPassesTestMixin
):
    login_url = 'accounts:login'

    def test_func(self):
        user = self.request.user

        return (
            user.is_superuser
            or user.role == User.Role.LIBRARIAN
        )


class ISBNLookupView(LibrarianAccessMixin, FormView):
    template_name = 'catalog/isbn_lookup.html'
    form_class = ISBNLookupForm

    def form_valid(self, form):
        isbn = form.cleaned_data['isbn']

        cache_key = f'openlibrary_isbn_{isbn}'
        book_data = cache.get(cache_key)

        if book_data is None:
            try:
                url = f'https://openlibrary.org/isbn/{isbn}.json'

                response = requests.get(
                    url,
                    timeout=10,
                    headers={
                        'User-Agent': 'LibraryCatalogApp/1.0'
                    }
                )

                response.raise_for_status()
                api_data = response.json()

                authors = []

                for author in api_data.get('authors', [])[:3]:
                    author_key = author.get('key', '')
                    author_id = author_key.split('/')[-1]

                    if not author_id:
                        continue

                    author_url = (
                        f'https://openlibrary.org/authors/{author_id}.json'
                    )

                    try:
                        author_response = requests.get(
                            author_url,
                            timeout=10,
                            headers={
                                'User-Agent': 'LibraryCatalogApp/1.0'
                            }
                        )

                        author_response.raise_for_status()
                        author_data = author_response.json()

                        if author_data.get('name'):
                            authors.append(author_data['name'])

                    except (requests.RequestException, ValueError):
                        continue

                description = api_data.get('description', '')

                if isinstance(description, dict):
                    description = description.get('value', '')

                publish_date = api_data.get('publish_date', '')
                year_match = re.search(r'\b\d{4}\b', publish_date)

                publication_year = (
                    int(year_match.group())
                    if year_match else None
                )

                book_data = {
                    'title': api_data.get('title', ''),
                    'author': ', '.join(authors),
                    'isbn': isbn,
                    'publisher': ', '.join(
                        api_data.get('publishers', [])[:3]
                    ),
                    'publication_year': publication_year,
                    'description': description,
                }

                cache.set(
                    cache_key,
                    book_data,
                    timeout=60 * 60 * 24
                )

            except requests.RequestException:
                form.add_error(
                    None,
                    'Unable to connect to Open Library. Please try again.'
                )
                return self.form_invalid(form)

            except ValueError:
                form.add_error(
                    None,
                    'Invalid response received from Open Library.'
                )
                return self.form_invalid(form)

        if not book_data.get('title'):
            form.add_error(
                None,
                'No book information was found for this ISBN.'
            )
            return self.form_invalid(form)

        return self.render_to_response(
            self.get_context_data(
                form=form,
                book_data=book_data
            )
        )


class BookCreateView(LibrarianAccessMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'catalog/book_form.html'
    success_url = reverse_lazy('catalog:isbn_lookup')

    def get_initial(self):
        initial = super().get_initial()

        fields = [
            'title',
            'author',
            'isbn',
            'publisher',
            'publication_year',
            'description',
        ]

        for field in fields:
            value = self.request.GET.get(field)

            if value:
                initial[field] = value

        return initial

    def form_valid(self, form):
        messages.success(
            self.request,
            'Book has been added successfully to the catalog.'
        )

        return super().form_valid(form)



class BookListView(ListView):
    model = Book
    template_name = 'catalog/book_list.html'
    context_object_name = 'books'
    paginate_by = 10

    def get_queryset(self):
        queryset = Book.objects.all()

        search_query = self.request.GET.get('q', '').strip()

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(author__icontains=search_query) |
                Q(isbn__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        return context


class BookDetailView(DetailView):
    model = Book
    template_name = 'catalog/book_detail.html'
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        ready_reservation = False
        active_borrowing = False

        if user.is_authenticated and user.role == User.Role.MEMBER:

            ready_reservation = Reservation.objects.filter(
                user=user,
                book=self.object,
                status=Reservation.Status.READY
            ).exists()

            active_borrowing = BorrowRecord.objects.filter(
                user=user,
                book=self.object,
                returned_at__isnull=True
            ).exists()

        context['ready_reservation'] = ready_reservation
        context['active_borrowing'] = active_borrowing

        return context