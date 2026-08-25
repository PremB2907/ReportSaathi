import unittest
import json
import io
from PIL import Image

# Add root folder to sys path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.index import app
from app.utils.image_utils import preprocess_image
from app.services.safety_engine import (
    validate_and_sanitize_report,
    get_doctor_recommendations,
    generate_what_should_i_do,
    generate_doctor_questions
)
from app.services.doctor_finder import calculate_distance, get_mock_nearby_providers

class TestReportSaathi(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    # 1. Test image preprocessing validation
    def test_image_preprocessing_unsupported_format(self):
        with self.assertRaises(ValueError) as context:
            preprocess_image(b"fake data", "report.pdf")
        self.assertIn("Unsupported file type", str(context.exception))

    def test_image_preprocessing_corrupt_data(self):
        with self.assertRaises(ValueError) as context:
            preprocess_image(b"fake data corrupt", "report.png")
        self.assertIn("Could not open image file", str(context.exception))

    def test_image_preprocessing_success(self):
        # Create a tiny mock image in memory
        file_buffer = io.BytesIO()
        img = Image.new('RGB', (100, 100), color='white')
        img.save(file_buffer, format='PNG')
        img_bytes = file_buffer.getvalue()

        processed = preprocess_image(img_bytes, "report.png")
        self.assertIn("base64", processed)
        self.assertEqual(processed["mime_type"], "image/png")
        self.assertEqual(processed["width"], 100)
        self.assertEqual(processed["height"], 100)

    # 2. Test Geodistance calculation
    def test_geodistance_calculation(self):
        # Distance between Mumbai (19.0760, 72.8777) and Pune (18.5204, 73.8567)
        dist = calculate_distance(19.0760, 72.8777, 18.5204, 73.8567)
        self.assertGreater(dist, 100.0)
        self.assertLess(dist, 150.0)

    # 3. Test safety engine and validation rules
    def test_safety_engine_validation_structure(self):
        raw_report = {
            "patient": {"age": "45", "sex": "male"},
            "report_type": "CBC",
            "tests": [
                {
                    "name": "Hemoglobin",
                    "value": "10.2",
                    "unit": "g/dL",
                    "reference_range": "12.0-16.0",
                    "status": "discuss",
                    "confidence": 0.95
                }
            ],
            "overall_summary": {
                "status_level": "normal",
                "headline": "Normal Report"
            }
        }
        
        sanitized = validate_and_sanitize_report(raw_report)
        self.assertEqual(sanitized["patient"]["age"], 45) # converts string to int
        self.assertEqual(sanitized["patient"]["sex"], "male")
        # Test status escalation: since Hemoglobin is 'discuss', overall status is promoted to 'discuss'
        self.assertEqual(sanitized["overall_summary"]["status_level"], "discuss")
        self.assertTrue(len(sanitized["disclaimer"]) > 0)

    # 4. Test Doctor recommendation matcher
    def test_doctor_recommendations(self):
        # Thyroid checks map to Endocrinologist
        tests_thyroid = [
            {"name": "TSH (Thyroid)", "value": "12.5", "unit": "uIU/mL", "status": "discuss"}
        ]
        rec_thyroid = get_doctor_recommendations(tests_thyroid)
        self.assertIn("Endocrinologist", rec_thyroid["specialty"])

        # Kidney/Urine parameters map to Urologist/Nephrologist
        tests_renal = [
            {"name": "Urine Pus cells", "value": "25-30", "unit": "/hpf", "status": "discuss"}
        ]
        rec_renal = get_doctor_recommendations(tests_renal)
        self.assertIn("Urologist", rec_renal["specialty"])

        # Normal report maps to General Physician
        tests_normal = [
            {"name": "Hemoglobin", "value": "13.5", "unit": "g/dL", "status": "normal"}
        ]
        rec_normal = get_doctor_recommendations(tests_normal)
        self.assertEqual(rec_normal["specialty"], "General Physician / Family Doctor")

    # 5. Test dynamic "What Should I Do Now" action plan
    def test_action_plan_normal(self):
        report = {
            "overall_summary": {"status_level": "normal"},
            "tests": []
        }
        plan = generate_what_should_i_do(report, symptoms=[])
        self.assertIn("healthy lifestyle", plan["now"].lower())
        self.assertIn("no immediate doctor visit", plan["doctor"].lower())

    def test_action_plan_urgent(self):
        report = {
            "overall_summary": {"status_level": "urgent"},
            "tests": []
        }
        # Urgent status should trigger emergency warning prompt
        plan = generate_what_should_i_do(report, symptoms=["Fever", "Bleeding"])
        self.assertIn("emergency room", plan["dont_wait"].lower())
        self.assertIn("as soon as possible", plan["doctor"].lower())

    # 6. Test Doctor Consultation Questions
    def test_doctor_consultation_questions(self):
        tests = [
            {"name": "Platelet Count", "value": "80", "unit": "x10^3/uL", "status": "discuss"}
        ]
        questions = generate_doctor_questions(tests)
        self.assertTrue(len(questions) >= 3)
        self.assertIn("Platelet Count", questions[0])

    # 7. Test standard route responses
    def test_route_home(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_route_health(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")

    def test_route_config(self):
        response = self.app.get('/api/config')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("ai_configured", data)

    def test_route_test_real_disabled(self):
        with unittest.mock.patch.dict(os.environ, {"ADMIN_DIAGNOSTICS": "false"}):
            response = self.app.get('/api/ai/test-real')
            self.assertEqual(response.status_code, 403)

    def test_route_test_real_enabled_mock(self):
        # Patch the actual call to avoid hitting the live API during local tests
        with unittest.mock.patch.dict(os.environ, {"ADMIN_DIAGNOSTICS": "true"}):
            with unittest.mock.patch('app.services.ai.groq_provider.GroqProvider.check_health', return_value={"available": True}):
                with unittest.mock.patch('app.services.ai.groq_provider.GroqProvider.test_connection', return_value="hello"):
                    with unittest.mock.patch('app.services.ai.groq_provider.GroqProvider.analyze_report', return_value={
                        "tests": [],
                        "overall_summary": {"status_level": "normal", "headline": "Test", "bullets": []}
                    }):
                        response = self.app.get('/api/ai/test-real')
                        self.assertEqual(response.status_code, 200)
                        data = json.loads(response.data)
                        self.assertEqual(data["endpoint"], "ok")
                        self.assertEqual(data["groq_auth"], "ok")
                        self.assertEqual(data["groq_text"], "ok")
                        self.assertEqual(data["groq_vision"], "ok")
                        self.assertEqual(data["json_parsing"], "ok")
                        self.assertEqual(data["safety_validation"], "ok")

if __name__ == '__main__':
    unittest.main()
