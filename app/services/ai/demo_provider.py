import os
from app.services.ai.base_provider import BaseAIProvider
from app.utils.sample_report import get_sample_report_data

class DemoProvider(BaseAIProvider):
    """
    Demo provider returning synthetic test values labeled with demonstration warnings.
    """
    def __init__(self):
        self.enabled = os.environ.get("ENABLE_DEMO_PROVIDER", "true").lower() == "true"

    def check_health(self) -> dict:
        return {
            "available": self.enabled,
            "reason": "active" if self.enabled else "not_configured",
            "features": {"vision": True, "json": True}
        }

    def analyze_report(self, images, language="english", symptoms=None, patient_context=None) -> dict:
        data = get_sample_report_data(language)
        if patient_context:
            if patient_context.get("age") is not None:
                data["patient"]["age"] = patient_context["age"]
            if patient_context.get("sex") is not None:
                data["patient"]["sex"] = patient_context["sex"]
        
        # Override headline to clearly label it as synthetic data
        data["overall_summary"]["headline"] = "DEMO DATA — NOT A REAL PATIENT"
        return data

    def ask_report(self, report_data, question, history=None, language="english") -> str:
        q_lower = question.lower()
        if "serious" in q_lower or "danger" in q_lower:
            ans = "Based on this report alone, there is no immediate indication of an emergency. However, please consult a physician if you feel unwell."
        elif "next" in q_lower or "what should i do" in q_lower:
            ans = "You should schedule a consultation with your family doctor to discuss these results. In the meantime, rest well and stay hydrated."
        elif "abnormal" in q_lower or "wrong" in q_lower:
            ans = "All values parsed in this sample report are currently within their standard laboratory ranges."
        elif "doctor" in q_lower or "who should i see" in q_lower:
            ans = "A General Physician or Family Doctor is recommended for reviewing standard reports."
        else:
            ans = "This is ReportSaathi. Your report details look standard. Let me know if you would like me to explain any specific test parameter!"
            
        if language == "hindi":
            if "serious" in q_lower: 
                ans = "इस रिपोर्ट के आधार पर कोई आपातकालीन स्थिति नहीं दिख रही है। यदि आप अस्वस्थ महसूस कर रहे हैं, तो डॉक्टर से सलाह लें।"
            else: 
                ans = "यह रिपोर्टसाथी है। आपकी रिपोर्ट सामान्य है। यदि आप किसी विशेष जांच के बारे में समझना चाहते हैं, तो कृपया पूछें!"
        elif language == "marathi":
            if "serious" in q_lower: 
                ans = "या रिपोर्टच्या आधारे कोणतीही आणीबाणीची परिस्थिती दिसत नाही. जर तुम्हाला बरे वाटत नसेल, तर डॉक्टरांचा सल्ला घ्या."
            else: 
                ans = "हे रिपोर्टसाथी आहे. तुमची रिपोर्ट सामान्य आहे. तुम्हाला विशिष्ट चाचणीबद्दल काही विचारायचे असल्यास विचारू शकता!"
        return ans

    def test_connection(self) -> str:
        return "Hello from Demo Provider"
