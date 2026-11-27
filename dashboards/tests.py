from django.core.management import call_command
from rest_framework.test import APITestCase

from accounts.models import User


class AdminRulesApiTests(APITestCase):
    def setUp(self):
        call_command("seed_rules")
        self.admin = User.objects.create_user(
            username="admin_test", password="pass12345",
            name="Admin Test", role="admin",
        )
        self.customer = User.objects.create_user(
            username="customer_test", password="pass12345",
            name="Customer Test", role="customer",
        )

    def test_customer_gets_403_on_rules(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get("/api/admin/rules/")
        self.assertEqual(response.status_code, 403)

    def test_admin_gets_200_and_all_rules(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/rules/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 11)

    def test_admin_can_change_a_rule_weight(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            "/api/admin/rules/R01/", {"weight": 3}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["weight"], 3)

    def test_admin_can_create_and_list_inspector(self):
        self.client.force_authenticate(user=self.admin)
        created = self.client.post(
            "/api/admin/inspectors/",
            {"user_id": "inspector_test", "name": "Inspector Test", "password": "inspect123"},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        listing = self.client.get("/api/admin/inspectors/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data), 1)