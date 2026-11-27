
from django.urls import path

from .views import MeView, SignInView, SignUpView

urlpatterns = [
    path('signup/', SignUpView.as_view()),
    path('signin/', SignInView.as_view()),
    path('me/', MeView.as_view()),
]
