from django.urls import path

from .views import FineListView, FinePaymentView

app_name = 'fines'

urlpatterns = [
    path('', FineListView.as_view(), name='fine_list'),
    path('<int:pk>/payment/', FinePaymentView.as_view(), name='record_payment'),
]