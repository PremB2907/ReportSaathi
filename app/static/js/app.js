// Core App Controller and UI Logic

let selectedFiles = [];
let selectedSymptoms = [];
let currentReport = null;
let olderReport = null;
let chatHistory = [];

// Drag and drop events
function onDragOver(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.add('dragover');
}

function onDragLeave(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.remove('dragover');
}

function onDrop(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.remove('dragover');
  if (e.dataTransfer.files) {
    addFiles(e.dataTransfer.files);
  }
}

function handleFileSelect(e) {
  if (e.target.files) {
    addFiles(e.target.files);
  }
}

function addFiles(filesList) {
  for (let i = 0; i < filesList.length; i++) {
    const file = filesList[i];
    // Check file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      alert(`File "${file.name}" is not supported. Please upload PNG, JPG, JPEG, or WEBP.`);
      continue;
    }
    // Check size limit (10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert(`File "${file.name}" exceeds 10MB.`);
      continue;
    }
    selectedFiles.push(file);
  }
  renderFilePreviews();
}

function renderFilePreviews() {
  const container = document.getElementById('file-preview-container');
  container.innerHTML = '';
  
  selectedFiles.forEach((file, index) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const div = document.createElement('div');
      div.style.position = 'relative';
      div.style.display = 'inline-block';
      div.style.border = '2px solid var(--black)';
      div.style.padding = '2px';
      div.style.backgroundColor = '#fff';
      
      const img = document.createElement('img');
      img.src = e.target.result;
      img.style.width = '70px';
      img.style.height = '70px';
      img.style.objectFit = 'cover';
      
      const deleteBtn = document.createElement('button');
      deleteBtn.innerHTML = 'X';
      deleteBtn.style.position = 'absolute';
      deleteBtn.style.top = '-5px';
      deleteBtn.style.right = '-5px';
      deleteBtn.style.backgroundColor = 'var(--red)';
      deleteBtn.style.color = '#fff';
      deleteBtn.style.border = '1px solid #111';
      deleteBtn.style.borderRadius = '50%';
      deleteBtn.style.width = '20px';
      deleteBtn.style.height = '20px';
      deleteBtn.style.fontSize = '10px';
      deleteBtn.style.cursor = 'pointer';
      deleteBtn.onclick = (event) => {
        event.stopPropagation();
        selectedFiles.splice(index, 1);
        renderFilePreviews();
      };
      
      div.appendChild(img);
      div.appendChild(deleteBtn);
      container.appendChild(div);
    };
    reader.readAsDataURL(file);
  });
}

// Symptom list togglers
function toggleSymptom(element) {
  const symptom = element.getAttribute('data-symptom');
  // Clear "None" if other symptoms selected
  const noneCard = document.getElementById('symptom-none');
  if (noneCard && noneCard.classList.contains('selected')) {
    noneCard.classList.remove('selected');
    selectedSymptoms = [];
  }

  element.classList.toggle('selected');
  if (element.classList.contains('selected')) {
    selectedSymptoms.push(symptom);
  } else {
    selectedSymptoms = selectedSymptoms.filter(s => s !== symptom);
  }
}

function clearSymptoms(element) {
  // Clear all other selections
  const cards = document.querySelectorAll('.symptom-card');
  cards.forEach(c => c.classList.remove('selected'));
  
  element.classList.add('selected');
  selectedSymptoms = ["No symptoms"];
}

// Submit medical report analysis
async function submitAnalysis() {
  if (selectedFiles.length === 0) {
    alert("Please upload at least one report image first.");
    return;
  }
  
  const formData = new FormData();
  selectedFiles.forEach(file => {
    formData.append('images[]', file);
  });
  
  buildAndSendAnalysis(formData, false);
}

// Submit demo analysis
function submitDemoAnalysis() {
  const formData = new FormData();
  buildAndSendAnalysis(formData, true);
}

async function buildAndSendAnalysis(formData, isDemo) {
  const errorCard = document.getElementById('error-card');
  const resultsDiv = document.getElementById('results-section');
  const loadingOverlay = document.getElementById('loading-overlay');
  
  errorCard.style.display = 'none';
  resultsDiv.style.display = 'none';
  loadingOverlay.style.display = 'flex';
  
  // Set language pref
  const selectedLanguage = localStorage.getItem('rs-lang') || 'english';
  formData.append('language', selectedLanguage);
  
  // Set symptoms
  formData.append('symptoms', JSON.stringify(selectedSymptoms));
  
  // Set demographic details
  const age = document.getElementById('patient-age').value;
  const sex = document.getElementById('patient-sex').value;
  formData.append('age', age);
  formData.append('sex', sex);
  
  if (isDemo) {
    formData.append('demo', 'true');
  }

  // Animation sequence for checklist
  const pipeline = [
    { id: 'pipe-1', duration: 400 },
    { id: 'pipe-2', duration: 800 },
    { id: 'pipe-3', duration: 1200 },
    { id: 'pipe-4', duration: 600 },
    { id: 'pipe-5', duration: 400 }
  ];

  let currentPipeIdx = 0;
  
  function advancePipeline() {
    if (currentPipeIdx < pipeline.length) {
      const p = pipeline[currentPipeIdx];
      const el = document.getElementById(p.id);
      if (el) {
        el.className = 'pipeline-item active';
      }
      if (currentPipeIdx > 0) {
        const prevEl = document.getElementById(pipeline[currentPipeIdx - 1].id);
        if (prevEl) prevEl.className = 'pipeline-item done';
      }
      currentPipeIdx++;
      setTimeout(advancePipeline, p.duration);
    }
  }
  
  advancePipeline();

  try {
    const data = await API.analyzeReport(formData);
    
    // complete pipeline instantly if fast
    pipeline.forEach(p => {
      const el = document.getElementById(p.id);
      if (el) el.className = 'pipeline-item done';
    });
    
    setTimeout(() => {
      loadingOverlay.style.display = 'none';
      renderDashboard(data);
    }, 500);
    
  } catch (err) {
    loadingOverlay.style.display = 'none';
    errorCard.style.display = 'block';
    
    if (err.message && err.message.includes("AI_UNAVAILABLE")) {
      errorCard.className = 'card btn-red';
      errorCard.innerHTML = `
        <h3 style="text-transform: uppercase; font-weight:800; font-size:1.4rem; margin-bottom:10px;">⚠️ AI IS TEMPORARILY UNAVAILABLE</h3>
        <p style="margin-bottom:15px; font-weight:600;">Your report has not been lost. Try again in a moment or use our demo mode.</p>
        <div style="display:flex; gap:10px;">
          <button id="btn-retry-upload" style="background:#fff; border:3px solid #000; padding:8px 16px; font-weight:800; cursor:pointer; box-shadow: 3px 3px 0 #000; text-transform:uppercase; color:#000;">Try Again</button>
          <button id="btn-demo-fallback" style="background:var(--yellow); border:3px solid #000; padding:8px 16px; font-weight:800; cursor:pointer; box-shadow: 3px 3px 0 #000; text-transform:uppercase; color:#000;">Use Demo Mode</button>
        </div>
      `;
      document.getElementById('btn-retry-upload').addEventListener('click', () => {
        errorCard.style.display = 'none';
        if (isDemo) {
          submitDemoAnalysis();
        } else {
          submitAnalysis();
        }
      });
      document.getElementById('btn-demo-fallback').addEventListener('click', () => {
        errorCard.style.display = 'none';
        submitDemoAnalysis();
      });
    } else {
      errorCard.className = 'card btn-red';
      errorCard.innerHTML = `
        <h3 style="text-transform: uppercase; font-weight:800; font-size:1.2rem; margin-bottom:10px;">⚠️ Something went wrong</h3>
        <p id="error-message" style="font-weight:600;">${err.message}</p>
      `;
    }
    console.error(err);
  }
}

// Display Extracted Data to Dashboard
function renderDashboard(data) {
  currentReport = data;
  window.currentReport = data; // store globally for maps context
  
  // Reset chat & history
  chatHistory = [];
  document.getElementById('chat-messages-container').innerHTML = `
    <div class="chat-bubble chat-assistant">
      Hello! I can explain parameters from this report. Ask me anything.
    </div>
  `;

  // 1. Overall Status banner styling
  const banner = document.getElementById('status-banner-box');
  const headline = document.getElementById('overall-status-headline');
  const notice = document.getElementById('overall-status-notice');
  const level = data.overall_summary.status_level;
  
  banner.className = 'status-banner';
  if (level === 'attention') {
    banner.classList.add('banner-attention');
  } else if (level === 'discuss') {
    banner.classList.add('banner-discuss');
  } else if (level === 'urgent') {
    banner.classList.add('banner-urgent');
  }
  
  headline.textContent = data.overall_summary.headline;
  
  // Notice text based on status level
  if (level === 'normal') {
    notice.textContent = "Nothing in the uploaded report obviously indicates an emergency based on the values we could read.";
  } else if (level === 'attention') {
    notice.textContent = "A few results are slightly outside range. These are generally normal fluctuations but good to monitor.";
  } else if (level === 'discuss') {
    notice.textContent = "Some test parameters warrant a scheduled review with your family doctor.";
  } else {
    notice.textContent = "Please consult a healthcare professional promptly to review these high priority values.";
  }

  // 2. Big 3 Things To Know (Headline bullets)
  const bullets = data.overall_summary.bullets;
  let summaryNoticeText = "<h3>📌 3 BIG THINGS TO KNOW:</h3><ul style='padding-left:1.5rem; margin-top:0.5rem;'>";
  bullets.forEach(b => {
    summaryNoticeText += `<li style='margin-bottom:0.4rem; font-weight:800;'>${b}</li>`;
  });
  summaryNoticeText += "</ul>";
  
  // Replace summary details or append below disclaimer
  document.getElementById('disclaimer-text').parentNode.innerHTML = `
    <div style="font-weight:900; margin-bottom:0.75rem; text-decoration:underline;">🛡️ MEDICAL EDUCATION COMPANION:</div>
    <p>${data.disclaimer}</p>
    <div style="margin-top:1rem; border-top:1px dashed var(--black); padding-top:1rem;">
      ${summaryNoticeText}
    </div>
  `;

  // 3. Narrative Storyboard
  document.getElementById('story-headline-txt').textContent = data.parent_simplified.headline;
  const storyboardPanel = document.getElementById('storyboard-panel');
  storyboardPanel.innerHTML = '';
  
  data.visual_story.forEach(card => {
    let badgeClass = "badge-normal";
    if (card.status === 'attention') badgeClass = 'badge-attention';
    if (card.status === 'discuss') badgeClass = 'badge-discuss';
    if (card.status === 'urgent') badgeClass = 'badge-urgent';

    const cardHtml = `
      <div class="story-card">
        <div class="story-icon">${card.icon}</div>
        <h4 style="text-transform:uppercase; font-weight:900; margin-bottom:0.25rem;">${card.title}</h4>
        <span class="badge ${badgeClass}" style="margin-bottom:0.5rem;">${card.status}</span>
        <p style="font-size:0.9rem; font-weight:800; color:#444;">${card.desc}</p>
      </div>
    `;
    storyboardPanel.innerHTML += cardHtml;
  });

  // 4. Test Table / Parameter Row generation
  const tableBody = document.getElementById('tests-table-body');
  const mobileList = document.getElementById('tests-mobile-body');
  tableBody.innerHTML = '';
  mobileList.innerHTML = '';
  
  data.tests.forEach(t => {
    let badgeClass = "badge-normal";
    let statusLabel = "🟢 Normal";
    
    if (t.status === 'attention') {
      badgeClass = 'badge-attention';
      statusLabel = '🟡 Attention';
    } else if (t.status === 'discuss') {
      badgeClass = 'badge-discuss';
      statusLabel = '🔵 Discuss';
    } else if (t.status === 'urgent') {
      badgeClass = 'badge-urgent';
      statusLabel = '🔴 Urgent';
    }

    // Check confidence. If confidence is low, trigger alert warning indicator
    let warningIcon = "";
    if (t.confidence < 0.8) {
      warningIcon = `<span title="Low OCR confidence. Please review." style="cursor:help;">⚠️</span>`;
    }

    // Row layout for desktop
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="font-weight:800;">${warningIcon} ${t.name}</td>
      <td style="font-weight:900; font-size:1.1rem;">${t.value} <span style="font-size:0.8rem; font-weight:600;">${t.unit}</span></td>
      <td style="font-weight:800;">${t.reference_range}</td>
      <td><span class="badge ${badgeClass}">${statusLabel}</span></td>
      <td>
        <p style="font-size:0.9rem; font-weight:600; margin-bottom:0.5rem;">${t.simple_explanation}</p>
        <button class="btn btn-sm btn-yellow" onclick="speakSingleTest('${t.name}', '${t.value}', '${t.unit}', '${t.status}', '${t.simple_explanation.replace(/'/g, "\\'")}')">🔊 LISTEN</button>
      </td>
    `;
    tableBody.appendChild(tr);

    // Card layout for mobile screens
    const mobCard = `
      <div class="test-mobile-card">
        <div class="test-mobile-title">
          <span>${warningIcon} ${t.name}</span>
          <span class="badge ${badgeClass}">${statusLabel}</span>
        </div>
        <div class="test-mobile-row">
          <span>Your value:</span>
          <strong>${t.value} ${t.unit}</strong>
        </div>
        <div class="test-mobile-row">
          <span>Lab range:</span>
          <strong>${t.reference_range}</strong>
        </div>
        <p style="margin-top:0.5rem; font-size:0.9rem; font-weight:600; border-top:1px dashed #ddd; padding-top:0.5rem;">
          ${t.simple_explanation}
        </p>
        <div style="margin-top:0.5rem; text-align:right;">
          <button class="btn btn-sm btn-yellow" onclick="speakSingleTest('${t.name}', '${t.value}', '${t.unit}', '${t.status}', '${t.simple_explanation.replace(/'/g, "\\'")}')">🔊 LISTEN</button>
        </div>
      </div>
    `;
    mobileList.innerHTML += mobCard;
  });

  // 5. Emergency Warning Red screen validation
  const emergencyBox = document.getElementById('emergency-alert-box');
  if (level === 'urgent') {
    emergencyBox.style.display = 'block';
  } else {
    emergencyBox.style.display = 'none';
  }

  // 6. Action Plan cards
  document.getElementById('action-now-txt').textContent = data.action_plan.now;
  document.getElementById('action-doctor-txt').textContent = data.action_plan.doctor;
  document.getElementById('action-urgent-txt').textContent = data.action_plan.dont_wait;

  // 7. Doctor recommendation panels
  document.getElementById('recommend-specialty-txt').textContent = data.doctor_recommendation.specialty;
  document.getElementById('recommend-reason-txt').textContent = data.doctor_recommendation.reason;

  // Reset parents explain text box
  document.getElementById('parents-translation-box').style.display = 'none';

  // 8. Auto-speak overall summary if narrated
  // We'll give it a slight delay so layout shifts finish
  setTimeout(() => {
    narrateReportSummary(data);
  }, 1000);

  // Reveal results segment
  document.getElementById('results-section').style.display = 'block';
  
  // Scroll smoothly down to results
  document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}

// Speaks explanations for a single parameter row
function speakSingleTest(name, value, unit, status, explanation) {
  const lang = localStorage.getItem('rs-lang') || 'english';
  let speechText = "";
  let voiceLang = 'en-US';

  if (lang === 'hindi') {
    speechText = `${name} का परिणाम है ${value} ${unit}। स्थिति ${status} है। ${explanation}`;
    voiceLang = 'hi-IN';
  } else if (lang === 'marathi') {
    speechText = `${name} चे निकाल आहे ${value} ${unit}। स्थिती ${status} आहे। ${explanation}`;
    voiceLang = 'mr-IN';
  } else {
    speechText = `${name} result is ${value} ${unit}. The status is ${status}. ${explanation}`;
    voiceLang = 'en-US';
  }

  speakText(speechText, voiceLang);
}

// "Explain to parents" toggle action
function explainToParents() {
  const box = document.getElementById('parents-translation-box');
  const txt = document.getElementById('parents-translation-text');
  
  if (!currentReport) return;
  
  txt.innerHTML = `
    <strong>${currentReport.parent_simplified.headline}</strong>
    <ul style="padding-left:1.5rem; margin-top:0.75rem;">
      ${currentReport.parent_simplified.bullets.map(b => `<li style="margin-bottom:0.5rem;">${b}</li>`).join('')}
    </ul>
  `;
  
  box.style.display = 'block';
  box.scrollIntoView({ behavior: 'smooth' });
}

// Chat integration Q&A
async function sendChatMessage() {
  const inputEl = document.getElementById('chat-user-input');
  const msg = inputEl.value.trim();
  if (!msg || !currentReport) return;

  const chatContainer = document.getElementById('chat-messages-container');
  
  // Render user bubble
  chatContainer.innerHTML += `
    <div class="chat-bubble chat-user">${msg}</div>
  `;
  chatContainer.scrollTop = chatContainer.scrollHeight;
  inputEl.value = '';

  // loading state
  const typingBubble = document.createElement('div');
  typingBubble.className = 'chat-bubble chat-assistant';
  typingBubble.textContent = 'Thinking...';
  chatContainer.appendChild(typingBubble);

  try {
    const lang = localStorage.getItem('rs-lang') || 'english';
    const data = await API.askQuestion(currentReport, msg, chatHistory, lang);
    
    // Save history
    chatHistory.push({ role: 'user', content: msg });
    chatHistory.push({ role: 'assistant', content: data.answer });
    
    typingBubble.textContent = data.answer;
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Read response aloud
    const voiceLang = lang === 'hindi' ? 'hi-IN' : (lang === 'marathi' ? 'mr-IN' : 'en-US');
    speakText(data.answer, voiceLang);
    
  } catch (err) {
    typingBubble.textContent = "Error getting answer. Please check your setup.";
  }
}

// Consultation Summary Modal
function openConsultationSummary() {
  if (!currentReport) return;
  
  const modal = document.getElementById('summary-modal');
  modal.style.display = 'flex';
  
  // Fill patient details
  const age = document.getElementById('patient-age').value || currentReport.patient.age || 'Not specified';
  const sex = document.getElementById('patient-sex').value || currentReport.patient.sex || 'Not specified';
  
  document.getElementById('sheet-age').textContent = age;
  document.getElementById('sheet-sex').textContent = sex;
  document.getElementById('sheet-report-type').textContent = currentReport.report_type;

  // Fill Flagged parameters
  const flaggedContainer = document.getElementById('sheet-flagged-tests-list');
  flaggedContainer.innerHTML = '';
  
  const flagged = currentReport.tests.filter(t => t.status !== 'normal');
  if (flagged.length === 0) {
    flaggedContainer.innerHTML = "<p>All parameters read are within standard laboratory ranges.</p>";
  } else {
    flagged.forEach(t => {
      flaggedContainer.innerHTML += `
        <p style="margin-bottom:0.25rem;">
          ❌ <strong>${t.name}</strong>: ${t.value} ${t.unit} (Printed range: ${t.reference_range}) - Status: <span style="text-transform:uppercase;">${t.status}</span>
        </p>
      `;
    });
  }

  // Symptoms
  document.getElementById('sheet-symptoms-list').textContent = selectedSymptoms.length > 0 ? selectedSymptoms.join(', ') : 'None reported';

  // Questions
  const questionsUl = document.getElementById('sheet-questions-list');
  questionsUl.innerHTML = '';
  currentReport.suggested_questions.forEach(q => {
    questionsUl.innerHTML += `<li style="margin-bottom:0.25rem;">${q}</li>`;
  });
}

function closeConsultationSummary() {
  document.getElementById('summary-modal').style.display = 'none';
}

// Compare reports function
async function handleCompareFileSelect(event) {
  const file = event.target.files[0];
  if (!file || !currentReport) return;

  const resultsBox = document.getElementById('compare-results-box');
  resultsBox.innerHTML = "<p style='font-weight:800;'>⏳ Extracting older report data...</p>";
  resultsBox.style.display = 'block';

  // In demo mode or if Groq is missing, simulate a trend comparison
  const formData = new FormData();
  formData.append('images[]', file);
  formData.append('demo', !isAIConfigured() ? 'true' : 'false');
  
  try {
    const data = await API.analyzeReport(formData);
    olderReport = data;
    
    // Compare
    const compareData = await API.compareReports(currentReport, olderReport);
    
    let html = `
      <div style="font-weight:800; font-size:1rem; text-transform:uppercase; margin-bottom:0.5rem; border-bottom:2px solid var(--black); padding-bottom:0.25rem;">
        📊 COMPARISON RESULTS
      </div>
      <p style="font-size:0.85rem; font-weight:800; margin-bottom:0.75rem; color:#444;">${compareData.message}</p>
    `;
    
    if (compareData.comparisons.length === 0) {
      html += "<p style='font-size:0.9rem;'>No matching test parameters could be found to establish a comparison trend.</p>";
    } else {
      compareData.comparisons.forEach(c => {
        let trendColor = "var(--black)";
        if (c.trend.includes("Increased")) trendColor = "var(--red)";
        if (c.trend.includes("Decreased")) trendColor = "var(--blue)";
        
        html += `
          <div class="compare-row">
            <div>
              <strong style="text-transform:uppercase;">${c.name}</strong>
              <p style="font-size:0.8rem; color:#555;">${c.desc}</p>
            </div>
            <div style="text-align:right;">
              <span style="color:${trendColor}; font-weight:900; font-size:0.9rem;">${c.trend}</span>
            </div>
          </div>
        `;
      });
    }
    
    resultsBox.innerHTML = html;
    
  } catch (err) {
    resultsBox.innerHTML = `<p style="color:var(--red); font-weight:800;">⚠️ Comparison failed: ${err.message}</p>`;
  }
}

// global variable for configuration state check
let isAIConfiguredState = false;
function isAIConfigured() {
  return isAIConfiguredState;
}

// Fetch backend configurations on start
fetch('/api/config')
  .then(r => r.json())
  .then(data => {
    isAIConfiguredState = data.ai_configured;
  })
  .catch(err => console.log("Failed to fetch API configurations"));

// PWA Setup banner logic
let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  // Show PWA install banner
  document.getElementById('pwa-install-banner').style.display = 'flex';
});

function installPWA() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted PWA installation');
      }
      deferredPrompt = null;
      dismissPWAInstall();
    });
  }
}

function dismissPWAInstall() {
  document.getElementById('pwa-install-banner').style.display = 'none';
}

// UI Setup lang select binders
function selectLanguage(lang) {
  changeGlobalLanguage(lang);
}

async function shutdownLocalServer() {
  if (!confirm("Are you sure you want to stop the local server and free up port 5000?")) {
    return;
  }
  
  try {
    const resp = await fetch('/api/shutdown', { method: 'POST' });
    const data = await resp.json();
    if (data.success) {
      alert(data.message);
      document.body.innerHTML = `
        <div style="text-align:center; padding: 5rem; font-family:'Outfit',sans-serif; background-color:#F5F0E8; min-height:100vh;">
          <h1 style="font-size:3rem; margin-bottom:1.5rem; text-transform:uppercase;">🔌 SERVER STOPPED</h1>
          <p style="font-size:1.5rem; font-weight:800; border:4px solid #111; display:inline-block; padding:1.5rem; background:white; box-shadow:6px 6px 0px #111;">
            Port 5000 is now released. You can safely close this browser window.
          </p>
        </div>
      `;
    }
  } catch (err) {
    alert("Could not communicate with the server. It might already be stopped.");
  }
}
