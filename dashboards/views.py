from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts import services as account_services
from accounts.permissions import IsAdminRole
from compliance import services as compliance_services


class RuleListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        return Response(compliance_services.list_rules())

    def post(self, request):
        try:
            rule = compliance_services.create_rule(request.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(rule, status=status.HTTP_201_CREATED)


class RuleDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def put(self, request, rule_id):
        try:
            rule = compliance_services.update_rule(rule_id, request.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(rule)


class InspectorListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        return Response(account_services.list_inspectors())

    def post(self, request):
        try:
            inspector = account_services.create_inspector(request.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(inspector, status=status.HTTP_201_CREATED)