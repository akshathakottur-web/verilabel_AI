from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts import services as account_services
from accounts.permissions import IsAdminRole, IsInspectorOrAdmin
from compliance import services as compliance_services
from scans.models import Batch, Scan
from scans.permissions import can_view_scan
from scans.serializers import ScanSerializer
from scans.services import review_scan


def error(message, code=status.HTTP_400_BAD_REQUEST):
    return Response({"error": message}, status=code)


# ---------------------------------------------------------------- Admin: rules

class RuleListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        return Response(compliance_services.list_rules())

    def post(self, request):
        try:
            rule = compliance_services.create_rule(request.data)
        except ValueError as e:
            return error(str(e))
        return Response(rule, status=status.HTTP_201_CREATED)


class RuleDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def put(self, request, rule_id):
        try:
            rule = compliance_services.update_rule(rule_id, request.data)
        except ValueError as e:
            return error(str(e))
        return Response(rule)


# ------------------------------------------------------- Admin: inspector logins

class InspectorListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        return Response(account_services.list_inspectors())

    def post(self, request):
        try:
            inspector = account_services.create_inspector(request.data)
        except ValueError as e:
            return error(str(e))
        return Response(inspector, status=status.HTTP_201_CREATED)


# ------------------------------------------------------------ Admin: history

class AdminHistoryView(APIView):
    """Every scan, newest first. The page filters Reviewed / Not reviewed itself."""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        scans = Scan.objects.select_related("uploaded_by", "reviewed_by")
        return Response(ScanSerializer(scans, many=True).data)


# ------------------------------------------------------------ Admin: statistics

class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        scans = Scan.objects.all()

        total = scans.count()
        reviewed = scans.filter(review_status="reviewed").count()

        # "Checked" labels are the ones that have a score
        checked = scans.filter(score__isnull=False)
        average = checked.aggregate(avg=Avg("score"))["avg"]

        verdict_counts = {"COMPLIANT": 0, "PARTIAL": 0, "NON_COMPLIANT": 0}
        for row in checked.values("verdict").annotate(n=Count("id")):
            if row["verdict"] in verdict_counts:
                verdict_counts[row["verdict"]] = row["n"]

        status_counts = {}
        for row in scans.values("status").annotate(n=Count("id")):
            status_counts[row["status"]] = row["n"]

        since = timezone.now() - timedelta(days=13)
        per_day = (
            scans.filter(created_at__gte=since)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(n=Count("id"))
            .order_by("day")
        )
        scans_per_day = [{"date": str(r["day"]), "count": r["n"]} for r in per_day]

        top_products = list(
            scans.exclude(product_name="")
            .values("product_name")
            .annotate(count=Count("id"))
            .order_by("-count", "product_name")[:5]
        )

        # Most failed rules: counted here in Python, not inside the database JSON
        failures = {}
        for result in scans.filter(status="done").values_list("compliance_result", flat=True):
            for rule in (result or {}).get("rules", []):
                if rule.get("status") == "FAIL":
                    key = rule.get("rule_id")
                    entry = failures.setdefault(key, {"rule_id": key, "name": rule.get("name"), "failures": 0})
                    entry["failures"] += 1
        most_failed_rules = sorted(failures.values(), key=lambda r: -r["failures"])[:5]

        recent = scans.select_related("uploaded_by", "reviewed_by")[:10]

        return Response({
            "total_scanned": total,
            "reviewed": reviewed,
            "not_reviewed": total - reviewed,
            "checked": checked.count(),
            "average_score": round(average) if average is not None else None,
            "fully_compliant": verdict_counts["COMPLIANT"],
            "verdict_counts": verdict_counts,
            "status_counts": status_counts,
            "scans_per_day": scans_per_day,
            "top_products": top_products,
            "most_failed_rules": most_failed_rules,
            "recent_scans": ScanSerializer(recent, many=True).data,
        })


# ------------------------------------------------------------ Inspector: batches

def batch_counts():
    """The numbers shown for one batch, counted from plain database columns."""
    return dict(
        total=Count("scans"),
        done=Count("scans", filter=Q(scans__status="done")),
        in_progress=Count("scans", filter=Q(scans__status__in=["queued", "processing"])),
        failed=Count("scans", filter=Q(scans__status__in=["failed", "low_quality"])),
        compliant=Count("scans", filter=Q(scans__verdict="COMPLIANT")),
        partial=Count("scans", filter=Q(scans__verdict="PARTIAL")),
        non_compliant=Count("scans", filter=Q(scans__verdict="NON_COMPLIANT")),
        reviewed=Count("scans", filter=Q(scans__review_status="reviewed")),
    )


def batch_row(batch):
    return {
        "batch_id": batch.id,
        "created_at": batch.created_at,
        "created_by": {
            "user_id": batch.created_by.username,
            "name": batch.created_by.name,
        },
        "total": batch.total,
        "done": batch.done,
        "in_progress": batch.in_progress,
        "failed": batch.failed,
        "compliant": batch.compliant,
        "partial": batch.partial,
        "non_compliant": batch.non_compliant,
        "reviewed": batch.reviewed,
    }


def visible_batches(user):
    """An inspector sees their own batches. An admin sees all."""
    batches = Batch.objects.select_related("created_by")
    if user.role != "admin":
        batches = batches.filter(created_by=user)
    return batches.annotate(**batch_counts()).order_by("-created_at")


class InspectorBatchListView(APIView):
    permission_classes = [IsAuthenticated, IsInspectorOrAdmin]

    def get(self, request):
        return Response([batch_row(b) for b in visible_batches(request.user)])


class InspectorBatchDetailView(APIView):
    permission_classes = [IsAuthenticated, IsInspectorOrAdmin]

    def get(self, request, batch_id):
        batch = visible_batches(request.user).filter(id=batch_id).first()
        if batch is None:
            return error("Batch not found.", status.HTTP_404_NOT_FOUND)
        scans = batch.scans.select_related("uploaded_by", "reviewed_by")
        data = batch_row(batch)
        data["scans"] = ScanSerializer(scans, many=True).data
        return Response(data)


# --------------------------------------------- Inspector: customer scans, review

class CustomerScansView(APIView):
    """Finished customer scans, newest first. Optional ?review=pending or ?review=reviewed."""
    permission_classes = [IsAuthenticated, IsInspectorOrAdmin]

    def get(self, request):
        scans = Scan.objects.filter(
            uploaded_by__role="customer", status="done"
        ).select_related("uploaded_by", "reviewed_by")

        review = request.query_params.get("review")
        if review:
            if review not in ("pending", "reviewed"):
                return error('review must be "pending" or "reviewed".')
            scans = scans.filter(review_status=review)

        return Response(ScanSerializer(scans, many=True).data)


class ReviewScanView(APIView):
    permission_classes = [IsAuthenticated, IsInspectorOrAdmin]

    def post(self, request, scan_id):
        scan = (
            Scan.objects.select_related("uploaded_by", "reviewed_by")
            .filter(id=scan_id)
            .first()
        )
        if scan is None or not can_view_scan(request.user, scan):
            return error("Scan not found.", status.HTTP_404_NOT_FOUND)
        try:
            review_scan(scan, request.user, request.data.get("confirmation"))
        except ValueError as e:
            return error(str(e))
        return Response(ScanSerializer(scan).data)