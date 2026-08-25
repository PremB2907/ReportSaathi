// Speech Synthesis and Recognition Manager

let currentUtterance = null;
let recognition = null;
let isSpeaking = false;

// 1. Text to Speech (TTS) Logic
function speakText(text, langCode = 'en-US') {
  if (!('speechSynthesis' in window)) {
    alert("Speech Synthesis is not supported in your browser.");
    return;
  }

  // Stop any active speech
  stopSpeaking();

  const utterance = new SpeechSynthesisUtterance(text);
  
  // Set voice based on preferred locale
  const voices = window.speechSynthesis.getVoices();
  let selectedVoice = null;

  if (langCode.startsWith('hi')) {
    selectedVoice = voices.find(v => v.lang.includes('hi-IN') || v.lang.includes('hi'));
    utterance.pitch = 1.0;
    utterance.rate = 0.9; // speak slightly slower for accessibility
  } else if (langCode.startsWith('mr')) {
    // If Marathi voice is not present, fall back to Hindi or general IN voice
    selectedVoice = voices.find(v => v.lang.includes('mr-IN') || v.lang.includes('mr'));
    if (!selectedVoice) {
      selectedVoice = voices.find(v => v.lang.includes('hi-IN') || v.lang.includes('hi'));
    }
    utterance.pitch = 1.0;
    utterance.rate = 0.9;
  } else {
    selectedVoice = voices.find(v => v.lang.includes('en-IN') || v.lang.includes('en-US') || v.lang.includes('en'));
    utterance.pitch = 1.0;
    utterance.rate = 0.95;
  }

  if (selectedVoice) {
    utterance.voice = selectedVoice;
  }
  utterance.lang = langCode;

  // Soundwave Animation Hook
  utterance.onstart = () => {
    isSpeaking = true;
    showGlobalVoiceWaves(true);
  };

  utterance.onend = utterance.onerror = () => {
    isSpeaking = false;
    showGlobalVoiceWaves(false);
  };

  currentUtterance = utterance;
  window.speechSynthesis.speak(utterance);
}

function stopSpeaking() {
  if ('speechSynthesis' in window && window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
  }
  isSpeaking = false;
  showGlobalVoiceWaves(false);
}

function showGlobalVoiceWaves(active) {
  // Toggle visual soundwave bars on active items
  const waves = document.querySelectorAll('.voice-wave');
  waves.forEach(w => {
    w.style.display = active ? 'flex' : 'none';
  });
}

function playDemoVoice() {
  const lang = localStorage.getItem('rs-lang') || 'english';
  let demoText = "";
  
  if (lang === 'hindi') {
    demoText = "नमस्ते। रिपोर्ट साथी में आपका स्वागत है। अपनी रिपोर्ट समझने के लिए एक फोटो अपलोड करें।";
    speakText(demoText, 'hi-IN');
  } else if (lang === 'marathi') {
    demoText = "नमस्कार. रिपोर्ट साथी मध्ये आपले स्वागत आहे. तुमची लॅब रिपोर्ट समजून घेण्यासाठी फोटो अपलोड करा.";
    speakText(demoText, 'mr-IN');
  } else {
    demoText = "Hello and welcome to Report Saathi. Take a photo of your medical report to get started.";
    speakText(demoText, 'en-US');
  }
}

// Speaks the full summary of the report
function narrateReportSummary(reportData) {
  const lang = localStorage.getItem('rs-lang') || 'english';
  const headline = reportData.overall_summary.headline;
  const bullets = reportData.overall_summary.bullets.join(". ");
  const doctor = reportData.doctor_recommendation.specialty;
  
  let speechText = "";
  let voiceLang = 'en-US';

  if (lang === 'hindi') {
    speechText = `आपकी रिपोर्ट का सारांश: ${headline}. मुख्य बातें: ${bullets}. सलाह: हम सुझाव देते हैं कि आप ${doctor} से संपर्क करें।`;
    voiceLang = 'hi-IN';
  } else if (lang === 'marathi') {
    speechText = `तुमच्या रिपोर्टचा सारांश: ${headline}. मुख्य गोष्टी: ${bullets}. सल्ला: आम्ही शिफारस करतो की तुम्ही ${doctor} चा सल्ला घ्यावा.`;
    voiceLang = 'mr-IN';
  } else {
    speechText = `Your report summary: ${headline}. Key findings: ${bullets}. We recommend consulting a ${doctor}.`;
    voiceLang = 'en-US';
  }

  speakText(speechText, voiceLang);
}

// 2. Speech to Text (STT) Logic
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.log("Speech recognition not supported in this browser.");
    return null;
  }
  
  const rec = new SpeechRecognition();
  rec.continuous = false;
  rec.interimResults = false;
  
  const lang = localStorage.getItem('rs-lang') || 'english';
  if (lang === 'hindi') rec.lang = 'hi-IN';
  else if (lang === 'marathi') rec.lang = 'mr-IN';
  else rec.lang = 'en-US';
  
  return rec;
}

function triggerVoiceInput() {
  const micBtn = document.getElementById('mic-chat-btn');
  const chatInput = document.getElementById('chat-user-input');
  
  if (!recognition) {
    recognition = initSpeechRecognition();
  }
  
  if (!recognition) {
    alert("Speech recognition is not supported on this browser. Please type your query.");
    return;
  }
  
  recognition.onstart = () => {
    micBtn.textContent = "🛑 LISTENING...";
    micBtn.classList.add('btn-red');
    chatInput.placeholder = "Listening to your voice... / बोला...";
  };
  
  recognition.onresult = (event) => {
    const textResult = event.results[0][0].transcript;
    chatInput.value = textResult;
  };
  
  recognition.onend = () => {
    micBtn.textContent = "🎙️ SPEAK";
    micBtn.classList.remove('btn-red');
    chatInput.placeholder = "Type question in English, Hindi, or Marathi...";
  };
  
  recognition.onerror = (e) => {
    console.error("Speech Recognition Error: ", e);
    micBtn.textContent = "🎙️ SPEAK";
    micBtn.classList.remove('btn-red');
  };
  
  recognition.start();
}

// Ensure voices are loaded
if ('speechSynthesis' in window) {
  window.speechSynthesis.onvoiceschanged = () => {
    console.log("Speech voices loaded.");
  };
}
