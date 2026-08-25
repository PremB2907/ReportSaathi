// Location and Nearby Healthcare Finder Manager

let userCoordinates = null;

function requestLocationAccess() {
  if (!navigator.geolocation) {
    alert("Geolocation is not supported by your browser. Please search manually.");
    showManualLocationInput();
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      userCoordinates = {
        lat: position.coords.latitude,
        lon: position.coords.longitude
      };
      console.log("User coordinates fetched:", userCoordinates);
      fetchNearbyClinics(userCoordinates.lat, userCoordinates.lon);
    },
    (error) => {
      console.warn("Location permission denied or unavailable:", error.message);
      alert("Location permission not granted. You can enter your area manually.");
      showManualLocationInput();
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
  );
}

function showManualLocationInput() {
  const inputDiv = document.getElementById('manual-location-input');
  if (inputDiv) {
    inputDiv.style.display = 'block';
  }
}

function findDoctorsByCity() {
  const cityField = document.getElementById('city-input-field');
  const city = cityField.value.trim();
  
  if (!city) {
    alert("Please enter a valid city name.");
    return;
  }
  
  fetchNearbyClinics(null, null, city);
}

function fetchNearbyClinics(lat, lon, city = null) {
  const clinicsContainer = document.getElementById('nearby-clinics-list');
  clinicsContainer.innerHTML = "<p style='font-weight:800;'>⏳ Searching verified local providers...</p>";

  // Determine URL params
  let url = '/api/nearby-doctors?';
  if (lat && lon) {
    url += `lat=${lat}&lon=${lon}`;
  } else if (city) {
    url += `city=${encodeURIComponent(city)}`;
  } else {
    clinicsContainer.innerHTML = "<p style='color:var(--red); font-weight:800;'>⚠️ Search criteria missing.</p>";
    return;
  }

  // Add specialty context if available in current report
  if (window.currentReport && window.currentReport.doctor_recommendation) {
    const specialty = window.currentReport.doctor_recommendation.specialty;
    url += `&specialty=${encodeURIComponent(specialty)}`;
  }

  fetch(url)
    .then(resp => resp.json())
    .then(data => {
      if (data.success && data.providers && data.providers.length > 0) {
        renderNearbyClinics(data.providers, data.locality);
      } else {
        clinicsContainer.innerHTML = (
          "<p style='font-weight:800;'>⚠️ We couldn't find verified healthcare providers nearby.</p>" +
          "<p style='font-size:0.85rem;'>Try manual search with a larger city like Pune or Mumbai.</p>"
        );
      }
    })
    .catch(err => {
      console.error("Clinic search failure:", err);
      clinicsContainer.innerHTML = "<p style='color:var(--red); font-weight:800;'>⚠️ Something went wrong while listing providers.</p>";
    });
}

function renderNearbyClinics(providers, locality) {
  const clinicsContainer = document.getElementById('nearby-clinics-list');
  
  // Set locality text
  let headerHtml = `<div style='font-weight:900; font-size:1.1rem; text-transform:uppercase;'>📍 Showing Clinics in ${locality}</div>`;
  
  let cardsHtml = providers.map(p => {
    // Generate phone button if phone is present
    const phoneBtn = p.phone 
      ? `<a href="tel:${p.phone}" class="btn btn-sm btn-green" style="text-decoration:none;">📞 CALL: ${p.phone}</a>` 
      : "";
      
    // Generate website button if present
    const webBtn = p.website 
      ? `<a href="${p.website}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-blue" style="text-decoration:none;">🌐 WEBSITE</a>` 
      : "";

    // Doctor recommendation context match badge
    const matchedSpecialty = window.currentReport ? window.currentReport.doctor_recommendation.specialty : "General Physician";

    return `
      <div class="card" style="margin-bottom:0; box-shadow: 4px 4px 0px var(--black); padding: 1.25rem;">
        <div style="font-weight:900; font-size: 1.15rem; text-transform:uppercase; margin-bottom:0.25rem;">
          🏥 ${p.name}
        </div>
        <div style="font-size: 0.85rem; font-weight: 800; color: #555; text-transform:uppercase; margin-bottom: 0.5rem;">
          ${p.type} • ${p.specialty}
        </div>
        <p style="font-weight:800; font-size:0.95rem; margin-bottom:0.75rem;">
          📍 Address: ${p.address}<br>
          📏 Distance: <strong>${p.distance} km away</strong>
        </p>
        <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom: 0.75rem;">
          <a href="${p.directions_url}" target="_blank" rel="noopener" class="btn btn-sm btn-yellow" style="text-decoration:none;">🧭 DIRECTIONS</a>
          ${phoneBtn}
          ${webBtn}
        </div>
        <div style="border-top:1px dashed var(--black); padding-top:0.5rem; font-size:0.8rem; font-weight:800; color:#555;">
          Suggested because: "Your report recommends consultation with a ${matchedSpecialty}."
          <br>
          <span style="font-size:0.7rem; color:#888;">Source: ${p.source}</span>
        </div>
      </div>
    `;
  }).join('');
  
  clinicsContainer.innerHTML = headerHtml + cardsHtml;
}
