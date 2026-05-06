const DEFAULT_MAP_CENTER = [-31.9505, 115.8605];
const DEFAULT_MAP_ZOOM = 12;

function createBaseMap(elementId) {
  const map = L.map(elementId).setView(DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  return map;
}

function formatCoordinate(value) {
  return Number(value).toFixed(5);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function initActivityLocationMap() {
  const mapElement = document.getElementById("activityMap");
  if (!mapElement) {
    return;
  }

  const toggleLocationMapButton = document.getElementById("toggleLocationMap");
  const activityLocationPanel = document.getElementById("activityLocationPanel");
  const latitudeInput = document.getElementById("latitude");
  const longitudeInput = document.getElementById("longitude");
  const locationStatus = document.getElementById("locationStatus");
  const useCurrentLocationButton = document.getElementById("useCurrentLocation");
  const clearLocationButton = document.getElementById("clearLocation");
  let map = null;
  let marker = null;

  function ensureMap() {
    if (!map) {
      map = createBaseMap("activityMap");
      map.on("click", (event) => {
        setSelectedLocation(event.latlng.lat, event.latlng.lng);
      });
    }

    setTimeout(() => {
      map.invalidateSize();
    }, 0);

    return map;
  }

  function setSelectedLocation(latitude, longitude) {
    latitudeInput.value = latitude;
    longitudeInput.value = longitude;

    if (marker) {
      marker.setLatLng([latitude, longitude]);
    } else {
      marker = L.marker([latitude, longitude]).addTo(map);
    }

    locationStatus.textContent = `Selected location: ${formatCoordinate(latitude)}, ${formatCoordinate(longitude)}`;
  }

  function clearSelectedLocation() {
    latitudeInput.value = "";
    longitudeInput.value = "";
    locationStatus.textContent = "No location selected.";

    if (marker) {
      marker.remove();
      marker = null;
    }
  }

  function showLocationPanel() {
    activityLocationPanel.hidden = false;
    toggleLocationMapButton.textContent = "Hide activity location";
    ensureMap();
  }

  function hideLocationPanel() {
    activityLocationPanel.hidden = true;
    toggleLocationMapButton.textContent = latitudeInput.value ? "Edit activity location" : "Add activity location";
  }

  toggleLocationMapButton.addEventListener("click", () => {
    if (activityLocationPanel.hidden) {
      showLocationPanel();
    } else {
      hideLocationPanel();
    }
  });

  useCurrentLocationButton.addEventListener("click", () => {
    if (!navigator.geolocation) {
      locationStatus.textContent = "Geolocation is not supported by this browser.";
      return;
    }

    locationStatus.textContent = "Getting your current location...";
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;
        const activityMap = ensureMap();
        activityMap.setView([latitude, longitude], 15);
        setSelectedLocation(latitude, longitude);
      },
      () => {
        locationStatus.textContent = "Unable to access your location. You can still click the map manually.";
      }
    );
  });

  clearLocationButton.addEventListener("click", () => {
    clearSelectedLocation();
    toggleLocationMapButton.textContent = "Add activity location";
  });
}

function initHistoryLocationMap() {
  const mapElement = document.getElementById("historyMap");
  if (!mapElement) {
    return;
  }

  const mapPanel = document.getElementById("locationMapPanel");
  const mapStatus = document.getElementById("historyMapStatus");
  const locations = window.historyLocations || [];
  let map = null;
  let marker = null;

  function ensureHistoryMap() {
    if (!map) {
      map = createBaseMap("historyMap");
    }

    setTimeout(() => {
      map.invalidateSize();
    }, 0);

    return map;
  }

  function showSessionLocation(session) {
    const latitude = Number(session.latitude);
    const longitude = Number(session.longitude);

    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
      return;
    }

    mapPanel.hidden = false;
    const historyMap = ensureHistoryMap();

    if (marker) {
      marker.remove();
    }

    marker = L.marker([latitude, longitude]).addTo(historyMap);
    marker.bindPopup(`
      <strong>${escapeHtml(session.date)}</strong><br>
      Calories: ${escapeHtml(session.total_calories)} kcal<br>
      Weight: ${escapeHtml(session.current_weight)} kg<br>
      Notes: ${escapeHtml(session.notes || "-")}
    `).openPopup();

    historyMap.setView([latitude, longitude], 15);
    mapStatus.textContent = `Showing location for session on ${session.date}.`;
    mapPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  document.querySelectorAll(".check-location-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const sessionId = Number(button.dataset.sessionId);
      const session = locations.find((item) => Number(item.id) === sessionId);

      if (session) {
        showSessionLocation(session);
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initActivityLocationMap();
  initHistoryLocationMap();
});
