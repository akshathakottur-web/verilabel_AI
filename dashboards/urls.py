from django.urls import path

from .views import (
    AdminHistoryView,
    AdminStatsView,
    CustomerScansView,
    InspectorBatchDetailView,
    InspectorBatchListView,
    InspectorListCreateView,
    ReviewScanView,
    RuleDetailView,
    RuleListCreateView,
)

urlpatterns = [
    path("admin/rules/", RuleListCreateView.as_view()),
    path("admin/rules/<str:rule_id>/", RuleDetailView.as_view()),
    path("admin/inspectors/", InspectorListCreateView.as_view()),
    path("admin/history/", AdminHistoryView.as_view()),
    path("admin/stats/", AdminStatsView.as_view()),
    path("inspector/batches/", InspectorBatchListView.as_view()),
    path("inspector/batches/<int:batch_id>/", InspectorBatchDetailView.as_view()),
    path("inspector/customer-scans/", CustomerScansView.as_view()),
    path("inspector/scans/<int:scan_id>/review/", ReviewScanView.as_view()),
]