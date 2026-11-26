
from django.urls import path

from .views import ScanDetailView, ScanListCreateView

urlpatterns = [
    path('', ScanListCreateView.as_view()),
    path('<int:scan_id>/', ScanDetailView.as_view()),
]
