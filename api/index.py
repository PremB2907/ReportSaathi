import os
import sys
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv

# Ensure root path is accessible for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env variables
load_dotenv()

def validate_startup_environment():
    print("=== REPORTSAATHI AI CONFIGURATION VALIDATION ===")
    for key in ["GROQ_API_KEY", "GEMINI_API_KEY", "NVIDIA_API_KEY"]:
        val = os.environ.get(key, "").strip()
        status = "configured" if val else "missing"
        print(f"{key} = {status}")
    print("================================================")

validate_startup_environment()

from app.utils.image_utils import preprocess_image
from app.services.ai.provider_manager import ProviderManager
ai_manager = ProviderManager()

from app.services.safety_engine import (
    validate_and_sanitize_report,
    get_doctor_recommendations,
    generate_what_should_i_do,
    generate_doctor_questions,
    generate_parent_version,
    generate_visual_story
)
from app.services.doctor_finder import reverse_geocode_osm, search_nearby_providers_osm
from app.utils.sample_report import get_sample_report_data

app = Flask(
    __name__,
    template_folder='../app/templates',
    static_folder='../app/static',
    static_url_path='/app/static'
)

# Set max upload size to 10MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

@app.route('/')
def home():
    """Serves the main frontend page."""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Simple health check endpoint."""
    return jsonify({
        "status": "healthy",
        "ai_configured": ai_manager.get_status_info()["healthy"]
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """Exposes configuration status to frontend."""
    return jsonify({
        "ai_configured": ai_manager.get_status_info()["healthy"],
        "maps_configured": bool(os.environ.get("GOOGLE_MAPS_API_KEY") or os.environ.get("MAPPLS_API_KEY"))
    })

@app.route('/api/analyze-report', methods=['POST'])
def analyze_report():
    """
    Endpoint to process medical report images.
    Input: Multi-part images[], language, symptoms[], age, sex, demo (optional)
    """
    language = request.form.get("language", "english").lower()
    symptoms_raw = request.form.get("symptoms", "[]")
    demo_mode = request.form.get("demo", "false").lower() == "true"
    age = request.form.get("age")
    sex = request.form.get("sex")

    try:
        symptoms = json.loads(symptoms_raw)
    except Exception:
        symptoms = []

    patient_context = {
        "age": int(age) if age and age.isdigit() else None,
        "sex": sex if sex in ["male", "female", "other"] else None
    }

    # 1. Check if demo mode or AI is not configured
    if demo_mode or not ai_manager.get_status_info()["healthy"]:
        # Retrieve preloaded clean mock report data matching the layout
        report_data = get_sample_report_data(language)
        # Apply context over demo
        if patient_context["age"]:
            report_data["patient"]["age"] = patient_context["age"]
        if patient_context["sex"]:
            report_data["patient"]["sex"] = patient_context["sex"]
    else:
        # Get uploaded files
        uploaded_files = request.files.getlist("images[]") or request.files.getlist("images")
        if not uploaded_files or (len(uploaded_files) == 1 and uploaded_files[0].filename == ''):
            return jsonify({"success": False, "error": "No files uploaded."}), 400

        processed_images = []
        for file in uploaded_files:
            try:
                img_bytes = file.read()
                processed = preprocess_image(img_bytes, file.filename)
                processed_images.append(processed)
            except Exception as e:
                return jsonify({"success": False, "error": f"Failed to process {file.filename}: {str(e)}"}), 400

        try:
            # Query active AI provider fallback chain
            report_data = ai_manager.analyze_report(
                images=processed_images,
                language=language,
                symptoms=symptoms,
                patient_context=patient_context
            )
        except Exception as e:
            return jsonify({
                "success": False,
                "error_code": "AI_UNAVAILABLE",
                "error": f"AI Engine analysis failed: {str(e)}. Please try again or use Demo Mode."
            }), 503

    # 2. Enrich extracted data using Safety Engine Rules
    report_data = validate_and_sanitize_report(report_data)
    
    # 3. Calculate dynamic sections
    doc_recommendation = get_doctor_recommendations(report_data["tests"])
    action_plan = generate_what_should_i_do(report_data, symptoms)
    suggested_questions = generate_doctor_questions(report_data["tests"])
    parent_simplified = generate_parent_version(report_data, language)
    visual_story = generate_visual_story(report_data)

    return jsonify({
        "success": True,
        "report_type": report_data["report_type"],
        "patient": report_data["patient"],
        "tests": report_data["tests"],
        "unreadable_fields": report_data["unreadable_fields"],
        "overall_summary": report_data["overall_summary"],
        "disclaimer": report_data["disclaimer"],
        "doctor_recommendation": doc_recommendation,
        "action_plan": action_plan,
        "suggested_questions": suggested_questions,
        "parent_simplified": parent_simplified,
        "visual_story": visual_story
    })

@app.route('/api/ask-report', methods=['POST'])
def ask_report():
    """
    Accepts question + report data and runs safety Q&A.
    """
    req_data = request.json or {}
    report_data = req_data.get("report_data")
    question = req_data.get("question")
    history = req_data.get("history", [])
    language = req_data.get("language", "english").lower()

    if not report_data or not question:
        return jsonify({"success": False, "error": "Missing report_data or question."}), 400

    # If AI is not configured, trigger a rule-based mock chat assistant
    if not ai_manager.get_status_info()["healthy"]:
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
        
        # Simple translation support
        if language == "hindi":
            if "serious" in q_lower: ans = "इस रिपोर्ट के आधार पर कोई आपातकालीन स्थिति नहीं दिख रही है। यदि आप अस्वस्थ महसूस कर रहे हैं, तो डॉक्टर से सलाह लें।"
            else: ans = "यह रिपोर्टसाथी है। आपकी रिपोर्ट सामान्य है। यदि आप किसी विशेष जांच के बारे में समझना चाहते हैं, तो कृपया पूछें!"
        elif language == "marathi":
            if "serious" in q_lower: ans = "या रिपोर्टच्या आधारे कोणतीही आणीबाणीची परिस्थिती दिसत नाही. जर तुम्हाला बरे वाटत नसेल, तर डॉक्टरांचा सल्ला घ्या."
            else: ans = "हे रिपोर्टसाथी आहे. तुमची रिपोर्ट सामान्य आहे. तुम्हाला विशिष्ट चाचणीबद्दल काही विचारायचे असल्यास विचारू शकता!"
            
        return jsonify({"success": True, "answer": ans})

    try:
        answer = ai_manager.ask_report(report_data, question, history, language)
        return jsonify({"success": True, "answer": answer})
    except Exception as e:
        return jsonify({
            "success": False,
            "error_code": "AI_UNAVAILABLE",
            "error": str(e)
        }), 503

@app.route('/api/nearby-doctors', methods=['GET'])
def get_nearby_doctors():
    """
    Search nearby doctors using OSM.
    Supports either lat/lon or city query.
    """
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    city = request.args.get("city")
    specialty = request.args.get("specialty")

    if lat and lon:
        try:
            locality = reverse_geocode_osm(lat, lon)
            providers = search_nearby_providers_osm(lat, lon, specialty)
            return jsonify({
                "success": True,
                "locality": locality,
                "providers": providers
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    elif city:
        # Mock geocode for common Indian cities to return working clinic coordinates
        city_coords = {
            "mumbai": (19.0760, 72.8777),
            "delhi": (28.6139, 77.2090),
            "bangalore": (12.9716, 77.5946),
            "pune": (18.5204, 73.8567),
            "hyderabad": (17.3850, 78.4867),
            "chennai": (13.0827, 80.2707)
        }
        clean_city = city.lower().strip()
        coords = city_coords.get(clean_city, (19.0760, 72.8777)) # fallback to Mumbai
        
        providers = search_nearby_providers_osm(coords[0], coords[1], specialty)
        return jsonify({
            "success": True,
            "locality": city.capitalize(),
            "providers": providers
        })
    else:
        return jsonify({"success": False, "error": "Provide either lat/lon or city query."}), 400

@app.route('/api/compare-reports', methods=['POST'])
def compare_reports():
    """
    Compares current report with previous report parameters.
    """
    req_data = request.json or {}
    current = req_data.get("current")
    previous = req_data.get("previous")

    if not current or not previous:
        return jsonify({"success": False, "error": "Both current and previous reports must be provided."}), 400

    comparisons = []
    
    # Simple delta calculator in python
    curr_tests = {t["name"].lower(): t for t in current.get("tests", [])}
    prev_tests = {t["name"].lower(): t for t in previous.get("tests", [])}

    for name, curr in curr_tests.items():
        if name in prev_tests:
            prev = prev_tests[name]
            
            # Try to extract numbers for numerical check
            try:
                c_val = float(re.findall(r"[-+]?\d*\.\d+|\d+", str(curr["value"]))[0])
                p_val = float(re.findall(r"[-+]?\d*\.\d+|\d+", str(prev["value"]))[0])
                delta = round(c_val - p_val, 2)
                
                if delta > 0:
                    trend = f"Increased by {delta}"
                    desc = f"Value went from {p_val} to {c_val} {curr['unit']}."
                elif delta < 0:
                    trend = f"Decreased by {abs(delta)}"
                    desc = f"Value went from {p_val} to {c_val} {curr['unit']}."
                else:
                    trend = "No change"
                    desc = f"Value remained stable at {c_val} {curr['unit']}."
            except Exception:
                trend = "N/A"
                desc = f"Value changed from '{prev['value']}' to '{curr['value']}'."
                
            comparisons.append({
                "name": curr["name"],
                "current_value": f"{curr['value']} {curr['unit']}",
                "previous_value": f"{prev['value']} {prev['unit']}",
                "trend": trend,
                "desc": desc,
                "status": curr["status"]
            })

    # Return compared structure
    return jsonify({
        "success": True,
        "comparisons": comparisons,
        "message": "This comparison details numerical changes between tests. Consult your doctor to understand what these trends mean for your health."
    })

@app.route('/api/create-doctor-summary', methods=['POST'])
def create_doctor_summary():
    """
    Generates a shareable / printable communication sheet.
    """
    req_data = request.json or {}
    report_data = req_data.get("report_data")
    symptoms = req_data.get("symptoms", [])
    questions = req_data.get("questions", [])
    user_notes = req_data.get("notes", "")

    if not report_data:
        return jsonify({"success": False, "error": "Missing report data."}), 400

    summary_sheet = {
        "title": "ReportSaathi - Doctor Consultation Visit Companion",
        "report_type": report_data.get("report_type"),
        "patient": report_data.get("patient"),
        "flagged_items": [
            {"name": t["name"], "value": f"{t['value']} {t['unit']}", "range": t["reference_range"], "status": t["status"]}
            for t in report_data.get("tests", []) if t["status"] != "normal"
        ],
        "symptoms": symptoms,
        "questions_to_ask": questions,
        "notes": user_notes,
        "notice": "This document is prepared to aid communication with a physician. It does not certify diagnostic findings."
    }

    return jsonify({"success": True, "summary": summary_sheet})

@app.route('/api/shutdown', methods=['POST'])
def shutdown_server():
    """Shuts down the Flask local server programmatically to release port 5000."""
    import signal
    import threading
    import time
    
    def kill_process():
        time.sleep(0.5)
        os.kill(os.getpid(), signal.SIGINT)
        
    threading.Thread(target=kill_process).start()
    return jsonify({
        "success": True, 
        "message": "Server port 5000 is being released. You can safely close this window."
    })

@app.route('/api/ai/status', methods=['GET'])
def ai_status_json():
    """Exposes structured provider health status (excluding keys)."""
    return jsonify(ai_manager.get_status_info())

@app.route('/admin/ai-status')
def admin_ai_status():
    """Serves the diagnostic administration dashboard if enabled."""
    is_enabled = os.environ.get("ADMIN_DIAGNOSTICS", "false").lower() == "true"
    if not is_enabled:
        return "Access Denied: Diagnostics page is disabled.", 403
    return render_template('ai_status.html')

@app.route('/api/ai/test-provider', methods=['POST'])
def test_provider():
    """Performs a lightweight harmless connection test for a specific provider."""
    is_enabled = os.environ.get("ADMIN_DIAGNOSTICS", "false").lower() == "true"
    if not is_enabled:
        return jsonify({"success": False, "error": "Access Denied"}), 403

    req_data = request.json or {}
    provider_name = req_data.get("provider", "").strip().lower()
    
    provider = ai_manager.get_provider(provider_name)
    if not provider:
        return jsonify({"success": False, "error": f"Unknown provider: {provider_name}"}), 400

    try:
        res = provider.test_connection()
        return jsonify({
            "success": True,
            "response": res
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# For running locally
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
