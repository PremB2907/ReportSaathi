// Backend API Client Integration Helper

const API = {
  async analyzeReport(formData) {
    const response = await fetch('/api/analyze-report', {
      method: 'POST',
      body: formData
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      const errPrefix = data.error_code ? `${data.error_code}: ` : "";
      throw new Error(errPrefix + (data.error || 'Server error occurred during analysis.'));
    }
    return data;
  },

  async askQuestion(reportData, question, history, language) {
    const response = await fetch('/api/ask-report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        report_data: reportData,
        question: question,
        history: history,
        language: language
      })
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.error || 'Failed to fetch answers.');
    }
    return data;
  },

  async compareReports(currentReport, previousReport) {
    const response = await fetch('/api/compare-reports', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        current: currentReport,
        previous: previousReport
      })
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.error || 'Comparison failed.');
    }
    return data;
  },

  async createDoctorSummary(reportData, symptoms, questions, notes) {
    const response = await fetch('/api/create-doctor-summary', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        report_data: reportData,
        symptoms: symptoms,
        questions: questions,
        notes: notes
      })
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.error || 'Could not compile doctor summary sheet.');
    }
    return data;
  }
};
