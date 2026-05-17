import json
import threading
import unittest
from http.client import HTTPConnection

from web_app.server import MarketingAgentHTTPServer


class WebAppIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.server = MarketingAgentHTTPServer(("127.0.0.1", 0))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.host, self.port = self.server.server_address

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection(self.host, self.port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response.status, response.getheaders(), payload

    def test_index_html_is_served(self):
        status, headers, payload = self.request("GET", "/")

        self.assertEqual(status, 200)
        self.assertIn(b"Monetization plan builder", payload)
        self.assertTrue(dict(headers)["Content-Type"].startswith("text/html"))

    def test_marketing_plan_api_returns_plan_json(self):
        request_body = json.dumps(
            {
                "software_source": "https://github.com/acme/revenue-dashboard",
                "user_interventions": [
                    {
                        "stage_name": "Market Research",
                        "feedback": "Prioritize finance teams with budget authority.",
                    }
                ],
            }
        )

        status, headers, payload = self.request(
            "POST",
            "/api/marketing-plan",
            body=request_body,
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(status, 200)
        self.assertEqual(dict(headers)["Content-Type"], "application/json")
        data = json.loads(payload)
        plan = data["marketing_plan"]
        self.assertEqual(plan["software_source"]["product_name"], "Revenue Dashboard")
        self.assertEqual(
            [stage["name"] for stage in plan["generation_stages"]],
            ["Market Research", "Campaign Orchestration", "Content Generation"],
        )
        self.assertIn("Prioritize finance teams", plan["editable_markdown"])

    def test_marketing_plan_api_returns_400_for_invalid_source(self):
        request_body = json.dumps({"software_source": "not a valid url"})

        status, headers, payload = self.request(
            "POST",
            "/api/marketing-plan",
            body=request_body,
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(status, 400)
        self.assertEqual(dict(headers)["Content-Type"], "application/json")
        data = json.loads(payload)
        self.assertIn("SoftwareSource", data["error"])
        self.assertNotIn("Traceback", data["error"])

    def test_marketing_plan_api_returns_400_for_malformed_json(self):
        status, headers, payload = self.request(
            "POST",
            "/api/marketing-plan",
            body="{",
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(status, 400)
        self.assertEqual(dict(headers)["Content-Type"], "application/json")
        self.assertEqual(json.loads(payload)["error"], "Request body must be valid JSON.")


if __name__ == "__main__":
    unittest.main()
