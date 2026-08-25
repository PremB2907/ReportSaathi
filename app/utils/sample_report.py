def get_sample_report_data(language="english"):
    """
    Returns synthetic, high-quality CBC and Urine analysis report data
    matching the guidelines. Pre-translated for instant loading in demo mode.
    """
    # Simple explanations based on target language
    explanations = {
        "english": {
            "Hemoglobin": "Think of this as the part of your blood that carries oxygen. When normal, your body gets enough energy.",
            "WBC": "These are your body's defense soldiers. They help fight off infections and illnesses.",
            "Platelets": "Think of these as band-aids in your blood. They stick together to stop bleeding when you get a cut.",
            "Pus cells": "These are defense cells that gather to fight germs. A small number is normal, but higher counts could indicate an infection.",
            "Epithelial cells": "These are normal cells shed from the lining of your urinary tract. A small number is typical.",
            "Protein": "This is a key building block. It should stay in your blood, not pass into your urine. 'Absent' is a good result.",
            "Sugar": "This is energy in your blood. It should not leak into your urine. 'Absent' is normal."
        },
        "hindi": {
            "Hemoglobin": "इसे अपने खून का वह हिस्सा समझें जो ऑक्सीजन ले जाता है। सामान्य होने पर शरीर में पूरी ऊर्जा रहती है।",
            "WBC": "ये आपके शरीर के रक्षक सैनिक हैं। वे संक्रमण और बीमारियों से लड़ने में मदद करते हैं।",
            "Platelets": "इन्हें अपने खून में 'बैंड-एड' समझें। चोट लगने पर खून रोकने के लिए ये आपस में चिपक जाते हैं।",
            "Pus cells": "ये वे कोशिकाएं हैं जो कीटाणुओं से लड़ने के लिए जमा होती हैं। कम संख्या सामान्य है, अधिक होने पर संक्रमण हो सकता है।",
            "Epithelial cells": "ये आपके मूत्र मार्ग की परत से निकलने वाली सामान्य कोशिकाएं हैं। कम संख्या में होना सामान्य बात है।",
            "Protein": "यह शरीर का मुख्य निर्माण खंड है। इसे आपके खून में रहना चाहिए, पेशाब में नहीं। 'Absent' होना अच्छा है।",
            "Sugar": "यह आपके खून की ऊर्जा है। इसे पेशाब में बाहर नहीं आना चाहिए। 'Absent' होना सामान्य है।"
        },
        "marathi": {
            "Hemoglobin": "याला तुमच्या रक्तातील प्राणवायू (ऑक्सिजन) वाहून नेणारा भाग समजा. हे प्रमाण व्यवस्थित असल्यास शरीराला पुरेशी ऊर्जा मिळते.",
            "WBC": "हे तुमच्या शरीराचे रक्षक सैनिक आहेत. ते विविध आजार आणि जंतूंशी लढण्यास मदत करतात.",
            "Platelets": "यांना तुमच्या रक्तातील नैसर्गिक मलमपट्टी (बँड-एड) समजा. जखम झाल्यास रक्त गोठवून रक्तप्रवाह थांबवण्यास हे मदत करतात.",
            "Pus cells": "या जंतूंशी लढण्यासाठी जमा झालेल्या पांढऱ्या पेशी आहेत. कमी प्रमाण सामान्य आहे, जास्त प्रमाण लघवीच्या संसर्गाचे लक्षण असू शकते.",
            "Epithelial cells": "या लघवीच्या मार्गातील सोलून निघणाऱ्या सामान्य पेशी आहेत. कमी प्रमाण असणे नेहमीचे आहे.",
            "Protein": "हा शरीराचा मुख्य घटक आहे. हा रक्तातच राहिला पाहिजे, लघवीमध्ये उतरू नये. 'Absent' असणे चांगले आहे.",
            "Sugar": "ही तुमच्या रक्तातील साखर आहे. ती लघवीवाटे बाहेर पडू नये. 'Absent' असणे सामान्य आहे."
        }
    }
    
    lang_exps = explanations.get(language.lower(), explanations["english"])
    
    overall_trans = {
        "english": {
            "headline": "🟢 MOST RESULTS LOOK WITHIN RANGE",
            "bullet1": "Blood counts look broadly within the laboratory ranges.",
            "bullet2": "Urine screening is largely unremarkable and clean.",
            "bullet3": "One or more findings (like minor pus cells) may need discussion depending on symptoms."
        },
        "hindi": {
            "headline": "🟢 अधिकांश परिणाम सामान्य सीमा में हैं",
            "bullet1": "ब्लड काउंट सामान्य तौर पर प्रयोगशाला की सामान्य सीमा के भीतर हैं।",
            "bullet2": "पेशाब की जांच मुख्य रूप से सामान्य और साफ है।",
            "bullet3": "कुछ रिपोर्ट (जैसे मामूली पस सेल्स) पर लक्षणों के आधार पर डॉक्टर से चर्चा की जा सकती है।"
        },
        "marathi": {
            "headline": "🟢 बहुतेक निकाल सामान्य मर्यादेत आहेत",
            "bullet1": "रक्ताचे प्रमाण सामान्यतः प्रयोगशाळेच्या मर्यादेत दिसते.",
            "bullet2": "लघवीची तपासणी मुख्यत्वे सामान्य आणि स्वच्छ आहे.",
            "bullet3": "लक्षणे असल्यास काही गोष्टींविषयी (जसे की थोडे पस सेल्स) डॉक्टरांशी चर्चा करावी."
        }
    }
    
    lang_overall = overall_trans.get(language.lower(), overall_trans["english"])

    return {
        "patient": {
            "age": 42,
            "sex": "female"
        },
        "report_type": "Complete Blood Count (CBC) + Urine Analysis",
        "tests": [
            {
                "name": "Hemoglobin",
                "value": "12.7",
                "unit": "g/dL",
                "reference_range": "12.5 - 16.0",
                "status": "normal",
                "confidence": 0.98,
                "simple_explanation": lang_exps["Hemoglobin"]
            },
            {
                "name": "WBC (White Blood Cells)",
                "value": "8710",
                "unit": "/cmm",
                "reference_range": "4000 - 11000",
                "status": "normal",
                "confidence": 0.99,
                "simple_explanation": lang_exps["WBC"]
            },
            {
                "name": "Platelets",
                "value": "314",
                "unit": "x10^3/uL",
                "reference_range": "150 - 450",
                "status": "normal",
                "confidence": 0.97,
                "simple_explanation": lang_exps["Platelets"]
            },
            {
                "name": "Urine Protein",
                "value": "Absent",
                "unit": "",
                "reference_range": "Absent",
                "status": "normal",
                "confidence": 0.99,
                "simple_explanation": lang_exps["Protein"]
            },
            {
                "name": "Urine Sugar",
                "value": "Absent",
                "unit": "",
                "reference_range": "Absent",
                "status": "normal",
                "confidence": 0.99,
                "simple_explanation": lang_exps["Sugar"]
            },
            {
                "name": "Urine Pus Cells",
                "value": "01-02",
                "unit": "/hpf",
                "reference_range": "00-05",
                "status": "normal",
                "confidence": 0.95,
                "simple_explanation": lang_exps["Pus cells"]
            },
            {
                "name": "Urine Epithelial Cells",
                "value": "01-02",
                "unit": "/hpf",
                "reference_range": "00-05",
                "status": "normal",
                "confidence": 0.95,
                "simple_explanation": lang_exps["Epithelial cells"]
            }
        ],
        "unreadable_fields": [],
        "overall_summary": {
            "status_level": "normal",
            "headline": lang_overall["headline"],
            "bullets": [
                lang_overall["bullet1"],
                lang_overall["bullet2"],
                lang_overall["bullet3"]
            ]
        }
    }
