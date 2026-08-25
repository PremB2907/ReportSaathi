import re

def validate_and_sanitize_report(report):
    """
    Validates report data structure, normalizes status flags, and runs rules-based safety checks.
    """
    if not isinstance(report, dict):
        report = {}

    # Initialize default structure
    patient = report.get("patient", {})
    if not isinstance(patient, dict):
        patient = {}
    patient.setdefault("age", None)
    patient.setdefault("sex", None)
    if patient.get("age") is not None:
        try:
            patient["age"] = int(patient["age"])
        except (ValueError, TypeError):
            pass
    
    report["patient"] = patient
    report.setdefault("report_type", "General Lab Report")
    report.setdefault("unreadable_fields", [])
    
    tests = report.get("tests", [])
    if not isinstance(tests, list):
        tests = []
        
    sanitized_tests = []
    has_urgent = False
    has_discuss = False
    has_attention = False

    for t in tests:
        if not isinstance(t, dict):
            continue
        name = t.get("name", "Unknown Test")
        val = t.get("value", "")
        unit = t.get("unit", "")
        ref = t.get("reference_range", "N/A")
        status = str(t.get("status", "normal")).lower()
        confidence = t.get("confidence", 1.0)
        
        # Ensure status falls within designated choices
        if status not in ["normal", "attention", "discuss", "urgent"]:
            status = "normal"
            
        if status == "urgent":
            has_urgent = True
        elif status == "discuss":
            has_discuss = True
        elif status == "attention":
            has_attention = True
            
        simple_explanation = t.get("simple_explanation", "")
        if not simple_explanation:
            simple_explanation = f"This measures the levels of {name} in your body. It is printed as {val} {unit}."

        sanitized_tests.append({
            "name": name,
            "value": val,
            "unit": unit,
            "reference_range": ref,
            "status": status,
            "confidence": float(confidence),
            "simple_explanation": simple_explanation
        })
        
    report["tests"] = sanitized_tests

    # Enforce rules-based status escalation
    summary = report.get("overall_summary", {})
    if not isinstance(summary, dict):
        summary = {}
        
    current_status = summary.get("status_level", "normal").lower()
    
    # If any test parameters are urgent, elevate overall status
    if has_urgent:
        calculated_status = "urgent"
    elif has_discuss:
        calculated_status = "discuss"
    elif has_attention:
        calculated_status = "attention"
    else:
        calculated_status = "normal"
        
    # Keep the higher status between AI estimation and rules-based calculation
    status_order = ["normal", "attention", "discuss", "urgent"]
    if status_order.index(calculated_status) > status_order.index(current_status):
        summary["status_level"] = calculated_status

    summary.setdefault("status_level", calculated_status)
    summary.setdefault("headline", "Report Summary")
    summary.setdefault("bullets", ["Review results with your physician."])
    report["overall_summary"] = summary

    # Append absolute safety disclaimer
    report["disclaimer"] = (
        "ReportSaathi provides educational explanations based on AI reading of the uploaded document. "
        "It does NOT replace professional medical diagnosis, prescriptions, or clinical treatments. "
        "Always discuss your reports directly with a qualified doctor."
    )

    return report

def get_doctor_recommendations(tests):
    """
    Analyzes parameters to suggest the correct doctor type with clinical reasoning.
    """
    specialties = set()
    justifications = []
    
    has_abnormal = False
    
    for t in tests:
        name = t["name"].lower()
        status = t["status"]
        
        # Check if the result is abnormal
        if status in ["discuss", "urgent"]:
            has_abnormal = True
            
            # Urine/Kidney markers
            if any(k in name for k in ["urine", "pus", "specific gravity", "protein", "epithelial", "casts", "cyst", "kidney", "creatinine", "urea", "egfr", "bun"]):
                specialties.add("Urologist / Nephrologist")
                justifications.append(f"Due to findings in your urine/kidney parameter: '{t['name']}' ({t['value']} {t['unit']}).")
                
            # Thyroid markers
            elif any(k in name for k in ["thyroid", "t3", "t4", "tsh"]):
                specialties.add("Endocrinologist")
                justifications.append(f"Due to thyroid levels: '{t['name']}' ({t['value']} {t['unit']}).")
                
            # Liver markers
            elif any(k in name for k in ["sgot", "sgpt", "bilirubin", "ast", "alt", "alp", "liver", "albumin"]):
                specialties.add("Gastroenterologist / Hepatologist")
                justifications.append(f"Due to liver enzymes or function parameters: '{t['name']}' ({t['value']} {t['unit']}).")
                
            # Blood count / Hematology markers
            elif any(k in name for k in ["hemoglobin", "platelet", "wbc", "rbc", "mcv", "mch", "mchc", "leukocyte", "hematocrit", "eosinophils", "neutrophils"]):
                specialties.add("Hematologist")
                justifications.append(f"Due to blood cell indices: '{t['name']}' ({t['value']} {t['unit']}).")
                
            # Lipid / Heart markers
            elif any(k in name for k in ["cholesterol", "lipid", "triglyceride", "hdl", "ldl"]):
                specialties.add("Cardiologist")
                justifications.append(f"Due to lipid profile markers: '{t['name']}' ({t['value']} {t['unit']}).")

    if not has_abnormal or not specialties:
        # Default recommendation
        return {
            "specialty": "General Physician / Family Doctor",
            "reason": "All parameters are within normal laboratory ranges, or represent general findings suitable for a primary care doctor."
        }
    
    # Join multiple findings
    return {
        "specialty": " & ".join(specialties),
        "reason": " ".join(justifications) + " A General Physician can also perform initial review and refer you."
    }

def generate_what_should_i_do(report, symptoms=None):
    """
    Returns 3 concrete cards: NOW, DOCTOR, DON'T WAIT.
    """
    status = report["overall_summary"]["status_level"]
    symptoms = symptoms or []
    
    # 1. NOW card
    if status == "normal":
        now_text = "Keep up your healthy lifestyle. Drink plenty of water and maintain a balanced diet."
    elif status == "attention":
        now_text = "Rest, stay hydrated, and monitor your symptoms. Avoid taking unprescribed supplements or self-medicating."
    else:
        now_text = "Organize your medical reports chronologically. Note down your recent diet or lifestyle habits to share with a physician."

    # 2. DOCTOR card
    if status == "normal":
        if symptoms:
            doctor_text = "Even though the report is normal, you are experiencing symptoms. You should schedule a routine visit with a General Physician."
        else:
            doctor_text = "No immediate doctor visit is indicated by this report alone. Discuss it at your next routine wellness checkup."
    elif status == "attention":
        doctor_text = "Schedule a consultation with your family doctor over the next few days to discuss these slight variations."
    elif status == "discuss":
        doctor_text = "Plan to see a General Physician or the recommended specialist this week. They will help investigate the root cause."
    else: # urgent
        doctor_text = "Arrange a medical consultation as soon as possible. Do not delay showing these findings to a medical practitioner."

    # 3. DON'T WAIT card
    # Emergency flags
    urgent_symptoms = ["Bleeding", "Pain", "Vomiting", "Fever"]
    matching_symptoms = [s for s in symptoms if s in urgent_symptoms]
    
    if status == "urgent" or len(matching_symptoms) >= 2:
        dont_wait_text = "If you feel severe pain, experience high fever (>102°F), persistent vomiting, active bleeding, or shortness of breath, go to the nearest emergency room immediately."
    else:
        dont_wait_text = "If you develop new or worsening symptoms like severe localized pain, burning sensation during urination, sudden weakness, or high fever, seek prompt medical care."

    return {
        "now": now_text,
        "doctor": doctor_text,
        "dont_wait": dont_wait_text
    }

def generate_doctor_questions(tests):
    """
    Generates 3-5 useful, safe questions the patient can ask their doctor.
    """
    questions = [
        "Does the result of these tests require any immediate lifestyle adjustments or dietary modifications?",
        "Should we repeat this laboratory screening test after a specific period of time?",
        "Do the mild variations in my reports relate directly to the symptoms I have been experiencing?"
    ]
    
    abnormal_tests = [t["name"] for t in tests if t["status"] in ["discuss", "urgent"]]
    if abnormal_tests:
        questions.insert(0, f"What could be the primary cause behind the abnormal values of {', '.join(abnormal_tests[:2])}?")
        questions.append("Are there any secondary or confirmatory screenings I should undergo next?")
        
    return questions[:5]

def generate_parent_version(report, language="english"):
    """
    Converts findings into an ultra-simplified story or text suitable for elderly parents.
    Uses basic colloquial translations.
    """
    status = report["overall_summary"]["status_level"]
    
    translations = {
        "english": {
            "headline_normal": "Everything looks standard and safe! No need to worry.",
            "headline_attention": "There are minor differences, but nothing to panic about.",
            "headline_discuss": "A few points need a friendly check-in with your doctor.",
            "headline_urgent": "We should show this to a doctor right away to be safe.",
            "blood_label": "Blood Health",
            "urine_label": "Urine Cleanliness",
            "general_label": "Body Systems"
        },
        "hindi": {
            "headline_normal": "सब कुछ बिल्कुल सामान्य और ठीक है! चिंता की कोई बात नहीं है।",
            "headline_attention": "कुछ छोटी-मोटी चीज़ें सीमा से थोड़ी बाहर हैं, घबराने की ज़रूरत नहीं है।",
            "headline_discuss": "कुछ रिपोर्ट्स के लिए डॉक्टर से मिलकर सलाह लेना अच्छा रहेगा।",
            "headline_urgent": "हमें तुरंत डॉक्टर को दिखाना चाहिए ताकि कोई परेशानी न बढ़े।",
            "blood_label": "खून की सेहत",
            "urine_label": "पेशाब की जांच",
            "general_label": "शरीर के अंग"
        },
        "marathi": {
            "headline_normal": "सर्व काही पूर्णपणे सामान्य आणि ठीक आहे! काळजी करण्याची काहीच गरज नाही.",
            "headline_attention": "काही लहान-सहान गोष्टी मर्यादेबाहेर आहेत, घाबरून जाऊ नका.",
            "headline_discuss": "काही गोष्टींविषयी डॉक्टरांशी चर्चा करून सल्ला घेणे योग्य ठरेल.",
            "headline_urgent": "सुरक्षिततेसाठी आपण लगेच डॉक्टरांना ही रिपोर्ट दाखवली पाहिजे.",
            "blood_label": "रक्ताचे आरोग्य",
            "urine_label": "लघवीची तपासणी",
            "general_label": "शरीराची कार्यप्रणाली"
        }
    }
    
    lang_pack = translations.get(language.lower(), translations["english"])
    
    if status == "normal":
        story_headline = lang_pack["headline_normal"]
    elif status == "attention":
        story_headline = lang_pack["headline_attention"]
    elif status == "discuss":
        story_headline = lang_pack["headline_discuss"]
    else:
        story_headline = lang_pack["headline_urgent"]
        
    # Group tests in visual categories for elderly mapping
    categories = {"blood": [], "urine": [], "other": []}
    for t in report["tests"]:
        name = t["name"].lower()
        if any(k in name for k in ["hemoglobin", "platelet", "wbc", "rbc", "cbc", "mcv", "lymph", "neutro", "leuko"]):
            categories["blood"].append(t)
        elif any(k in name for k in ["urine", "pus", "specific gravity", "protein", "sugar", "bile", "epithelial"]):
            categories["urine"].append(t)
        else:
            categories["other"].append(t)
            
    story_bullets = []
    
    # Blood summarization
    if categories["blood"]:
        blood_abnormal = [t["name"] for t in categories["blood"] if t["status"] != "normal"]
        if not blood_abnormal:
            if language == "hindi":
                story_bullets.append("🩸 खून की सभी जांचें सामान्य सीमा में हैं।")
            elif language == "marathi":
                story_bullets.append("🩸 रक्ताच्या सर्व तपासण्या सामान्य मर्यादेत आहेत.")
            else:
                story_bullets.append("🩸 All blood indicators look completely healthy.")
        else:
            if language == "hindi":
                story_bullets.append(f"🩸 खून की रिपोर्ट में {', '.join(blood_abnormal[:2])} में थोड़ा बदलाव है।")
            elif language == "marathi":
                story_bullets.append(f"🩸 रक्ताच्या रिपोर्टमध्ये {', '.join(blood_abnormal[:2])} मध्ये थोडा बदल आहे.")
            else:
                story_bullets.append(f"🩸 Blood health shows minor variance in: {', '.join(blood_abnormal[:2])}.")
                
    # Urine summarization
    if categories["urine"]:
        urine_abnormal = [t["name"] for t in categories["urine"] if t["status"] != "normal"]
        if not urine_abnormal:
            if language == "hindi":
                story_bullets.append("💧 पेशाब की रिपोर्ट बिल्कुल साफ़ और सामान्य है।")
            elif language == "marathi":
                story_bullets.append("💧 लघवीची रिपोर्ट पूर्णपणे स्वच्छ आणि सामान्य आहे.")
            else:
                story_bullets.append("💧 Urine report is clean and within range.")
        else:
            if language == "hindi":
                story_bullets.append(f"💧 पेशाब की रिपोर्ट में {', '.join(urine_abnormal[:2])} की जांच करने की ज़रूरत है।")
            elif language == "marathi":
                story_bullets.append(f"💧 लघवीच्या रिपोर्टमध्ये {', '.join(urine_abnormal[:2])} कडे लक्ष देणे गरजेचे आहे.")
            else:
                story_bullets.append(f"💧 Urine report shows some variance in: {', '.join(urine_abnormal[:2])}.")
                
    return {
        "headline": story_headline,
        "bullets": story_bullets if story_bullets else [story_headline]
    }

def generate_visual_story(report):
    """
    Transforms the report parameters into an interactive simple storyboard.
    """
    storyboard = []
    
    # Card 1: Blood
    blood_status = "normal"
    blood_details = "Everything within standard levels."
    blood_tests = [t for t in report["tests"] if any(k in t["name"].lower() for k in ["hemo", "platelet", "wbc", "rbc", "cbc"])]
    if blood_tests:
        abnormal = [t for t in blood_tests if t["status"] != "normal"]
        if abnormal:
            blood_status = abnormal[0]["status"]
            blood_details = f"Noticed changes in: {', '.join([t['name'] for t in abnormal])}."
        storyboard.append({
            "icon": "🩸",
            "title": "Blood Health Check",
            "status": blood_status,
            "desc": blood_details
        })
        
    # Card 2: Urine/Kidney
    urine_status = "normal"
    urine_details = "No signs of sugar, proteins or blood."
    urine_tests = [t for t in report["tests"] if any(k in t["name"].lower() for k in ["urine", "pus", "specific gravity", "protein"])]
    if urine_tests:
        abnormal = [t for t in urine_tests if t["status"] != "normal"]
        if abnormal:
            urine_status = abnormal[0]["status"]
            urine_details = f"Noticed changes in: {', '.join([t['name'] for t in abnormal])}."
        storyboard.append({
            "icon": "💧",
            "title": "Urine Cleanliness",
            "status": urine_status,
            "desc": urine_details
        })

    # Card 3: Liver/Organs
    other_status = "normal"
    other_details = "Other parameters look stable."
    other_tests = [t for t in report["tests"] if not any(k in t["name"].lower() for k in ["hemo", "platelet", "wbc", "rbc", "cbc", "urine", "pus", "specific gravity", "protein"])]
    if other_tests:
        abnormal = [t for t in other_tests if t["status"] != "normal"]
        if abnormal:
            other_status = abnormal[0]["status"]
            other_details = f"Attention: {', '.join([t['name'] for t in abnormal[:2]])}."
        storyboard.append({
            "icon": "🩺",
            "title": "Organ & Metabolism",
            "status": other_status,
            "desc": other_details
        })
        
    return storyboard
