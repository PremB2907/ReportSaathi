// Theme and Accessibility Manager

function setAccessibilityFont(scale) {
  // Reset all classes
  document.body.classList.remove('font-large', 'font-xlarge');
  
  // Reset button active classes
  document.getElementById('font-btn-normal').classList.remove('active');
  document.getElementById('font-btn-large').classList.remove('active');
  document.getElementById('font-btn-xlarge').classList.remove('active');
  
  if (scale === 'large') {
    document.body.classList.add('font-large');
    document.getElementById('font-btn-large').classList.add('active');
  } else if (scale === 'xlarge') {
    document.body.classList.add('font-xlarge');
    document.getElementById('font-btn-xlarge').classList.add('active');
  } else {
    document.getElementById('font-btn-normal').classList.add('active');
  }
  
  localStorage.setItem('rs-font-scale', scale);
}

function toggleReducedMotion() {
  const btn = document.getElementById('motion-btn');
  const isReduced = btn.classList.toggle('active');
  
  if (isReduced) {
    btn.textContent = 'ON';
    document.body.classList.add('reduced-motion');
    // Inject style to disable transitions/animations
    let styleTag = document.getElementById('reduced-motion-styles');
    if (!styleTag) {
      styleTag = document.createElement('style');
      styleTag.id = 'reduced-motion-styles';
      styleTag.innerHTML = `
        *, *:before, *:after {
          animation-delay: -1ms !important;
          animation-duration: 1ms !important;
          animation-iteration-count: 1 !important;
          background-attachment: initial !important;
          scroll-behavior: auto !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
        }
      `;
      document.head.appendChild(styleTag);
    }
  } else {
    btn.textContent = 'OFF';
    document.body.classList.remove('reduced-motion');
    const styleTag = document.getElementById('reduced-motion-styles');
    if (styleTag) styleTag.remove();
  }
  
  localStorage.setItem('rs-reduced-motion', isReduced ? 'true' : 'false');
}

function changeGlobalLanguage(lang) {
  localStorage.setItem('rs-lang', lang);
  
  // Sync header selector if it exists
  const headerSelector = document.getElementById('header-lang-selector');
  if (headerSelector) {
    headerSelector.value = lang;
  }
  
  // Sync uploader language buttons
  const buttons = document.querySelectorAll('.btn-lang');
  buttons.forEach(btn => {
    btn.classList.remove('btn-yellow');
    if (btn.id === `lang-${lang}`) {
      btn.classList.add('btn-yellow');
    }
  });
  
  console.log(`Global language configured to: ${lang}`);
}

// Load saved preferences on init
document.addEventListener('DOMContentLoaded', () => {
  const savedFont = localStorage.getItem('rs-font-scale') || 'normal';
  setAccessibilityFont(savedFont);
  
  const savedMotion = localStorage.getItem('rs-reduced-motion') === 'true';
  if (savedMotion) {
    toggleReducedMotion();
  }
  
  const savedLang = localStorage.getItem('rs-lang') || 'english';
  changeGlobalLanguage(savedLang);
});
