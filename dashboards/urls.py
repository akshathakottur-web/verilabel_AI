from django.urls import path

from .views import (
    RuleListCreateView,
    RuleDetailView,
    InspectorListCreateView,
)

urlpatterns = [
    path("admin/rules/", RuleListCreateView.as_view()),
    path("admin/rules/<str:rule_id>/", RuleDetailView.as_view()),
    path("admin/inspectors/", InspectorListCreateView.as_view()),
]