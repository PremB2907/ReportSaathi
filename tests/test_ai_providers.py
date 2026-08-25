import unittest
from unittest.mock import MagicMock, patch
import requests
from app.services.ai.base_provider import BaseAIProvider
from app.services.ai.provider_manager import ProviderManager
from app.services.ai.demo_provider import DemoProvider
from app.services.ai.groq_provider import GroqProvider

class MockHealthyProvider(BaseAIProvider):
    def check_health(self):
        return {"available": True, "reason": "active"}
    def analyze_report(self, images, language="english", symptoms=None, patient_context=None):
        return {"tests": [{"name": "Mock Test", "value": "12", "status": "normal"}]}
    def ask_report(self, report_data, question, history=None, language="english"):
        return "Mock Answer"
    def test_connection(self):
        return "Hello"

class MockFailingProvider(BaseAIProvider):
    def check_health(self):
        return {"available": True, "reason": "active"}
    def analyze_report(self, images, language="english", symptoms=None, patient_context=None):
        raise requests.exceptions.Timeout("Connection timed out")
    def ask_report(self, report_data, question, history=None, language="english"):
        raise requests.exceptions.HTTPError("429 Too Many Requests")
    def test_connection(self):
        raise ValueError("Auth Error")

class TestAIProviders(unittest.TestCase):
    def setUp(self):
        # Configure env variables for testing
        self.manager = ProviderManager()

    def test_error_categorization(self):
        # Timeout
        cat, status = self.manager._categorize_error(requests.exceptions.Timeout("timeout"))
        self.assertEqual(cat, "TIMEOUT")
        self.assertEqual(status, 504)

        # Connection Error
        cat, status = self.manager._categorize_error(requests.exceptions.ConnectionError("conn"))
        self.assertEqual(cat, "PROVIDER_UNAVAILABLE")
        self.assertEqual(status, 503)

        # HTTP 429
        resp = requests.Response()
        resp.status_code = 429
        cat, status = self.manager._categorize_error(requests.exceptions.HTTPError(response=resp))
        self.assertEqual(cat, "RATE_LIMIT")
        self.assertEqual(status, 429)

        # HTTP 401
        resp.status_code = 401
        cat, status = self.manager._categorize_error(requests.exceptions.HTTPError(response=resp))
        self.assertEqual(cat, "AUTHENTICATION_ERROR")
        self.assertEqual(status, 401)

    def test_fallback_sequence(self):
        # Inject failing provider followed by healthy provider
        failing = MockFailingProvider()
        healthy = MockHealthyProvider()
        self.manager.providers["groq"] = failing
        self.manager.providers["gemini"] = healthy
        self.manager.order = ["groq", "gemini"]

        # If groq fails with timeout, it should fall back to gemini and succeed
        res = self.manager.analyze_report(images=[])
        self.assertEqual(res["tests"][0]["name"], "Mock Test")

    def test_demo_provider_extraction(self):
        demo = DemoProvider()
        res = demo.analyze_report(images=[], language="english")
        self.assertEqual(res["overall_summary"]["headline"], "DEMO DATA — NOT A REAL PATIENT")
        self.assertGreater(len(res["tests"]), 0)

if __name__ == '__main__':
    unittest.main()
