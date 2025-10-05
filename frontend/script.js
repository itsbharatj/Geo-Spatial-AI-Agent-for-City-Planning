const API_URL = "http://localhost:8000/api/city-data";
const REPORT_API_URL = "http://localhost:8000/plan";

const app = {
  mapView: "leaflet",
  messages: [],
  map: null,
  deckglInstance: null,
  cityMarkers: {},
  customMarkers: [],
  clickedPoints: [],
  charts: {},
  activeLayers: {
    column: true,
    hexagon: false,
    scatterplot: true,
    heatmap: false,
    arc: false,
    grid: false,
    contour: false,
    text: false,
    icon: false,
  },
  activeCharts: {
    temperature: true,
    aqi: true,
    population: false,
  },
  cities: {},
  highlightedCities: [],
  generatedMarkdown: "",
  currentMode: "chat", // "chat" or "report"

  init() {
    this.setupEventListeners();
    this.initLeafletMap();
    console.log("Global City Planner initialized");
  },

  setupEventListeners() {
    document.getElementById("sidebarToggle").addEventListener("click", () => {
      document.getElementById("sidebar").classList.toggle("collapsed");
    });

    document.querySelectorAll(".layer-toggle").forEach((toggle) => {
      toggle.addEventListener("change", (e) => {
        this.activeLayers[e.target.dataset.layer] = e.target.checked;
        if (this.deckglInstance) this.updateDeckGLLayers();
      });
    });

    document.querySelectorAll(".chart-toggle").forEach((toggle) => {
      toggle.addEventListener("change", (e) => {
        const chart = e.target.dataset.chart;
        this.activeCharts[chart] = e.target.checked;
        const container = document.getElementById(`${chart}ChartContainer`);
        if (container) {
          container.style.display = e.target.checked ? "block" : "none";
          if (e.target.checked && !this.charts[chart]) {
            this.renderChart(chart);
          }
        }
      });
    });
  },

  initLeafletMap() {
    if (this.map) this.map.remove();

    this.map = L.map("map").setView([20, 0], 2);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap",
      minZoom: 2,
      maxZoom: 18,
    }).addTo(this.map);

    this.map.on("click", (e) => this.handleMapClick(e));
  },

  handleMapClick(e) {
    const { lat, lng } = e.latlng;

    const clickMarker = L.marker([lat, lng], {
      icon: L.icon({
        iconUrl:
          "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
        shadowUrl:
          "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41],
      }),
    }).addTo(this.map);

    clickMarker
      .bindPopup(
        `
      <div style="color: #1f2937;">
        <b>Point ${this.clickedPoints.length + 1}</b><br>
        Lat: ${lat.toFixed(4)}<br>
        Lng: ${lng.toFixed(4)}
        <button onclick="app.removePoint(${this.clickedPoints.length})" style="margin-top:8px; background:#ef4444; color:white; padding:4px 8px; border-radius:4px; border:none; cursor:pointer;">
          Remove
        </button>
      </div>
    `,
      )
      .openPopup();

    this.clickedPoints.push({ lat, lng, marker: clickMarker });
    this.updateClickedPointsCount();
  },

  removePoint(index) {
    if (this.clickedPoints[index]) {
      this.map.removeLayer(this.clickedPoints[index].marker);
      this.clickedPoints.splice(index, 1);
      this.updateClickedPointsCount();
    }
  },

  updateClickedPointsCount() {
    document.getElementById("clickedPointsCount").textContent =
      this.clickedPoints.length;
  },

  toggleMapView(view) {
    this.mapView = view;
    document
      .querySelectorAll(".map-view-btn")
      .forEach((btn) => btn.classList.remove("active"));

    if (view === "leaflet") {
      document.getElementById("map").style.display = "block";
      document.getElementById("deckgl-container").style.display = "none";
      document.getElementById("leafletBtn").classList.add("active");
      if (this.map) setTimeout(() => this.map.invalidateSize(), 100);
    } else {
      document.getElementById("map").style.display = "none";
      document.getElementById("deckgl-container").style.display = "block";
      document.getElementById("deckglBtn").classList.add("active");

      if (this.deckglInstance) {
        this.deckglInstance.finalize();
        this.deckglInstance = null;
      }

      setTimeout(() => {
        this.initDeckGL();
      }, 100);
    }
  },

  initDeckGL() {
    const container = document.getElementById("deckgl-container");
    if (!container || typeof deck === "undefined") {
      console.error("Deck.gl not available");
      this.addMessage(
        "assistant",
        "Deck.gl library not loaded. Please refresh the page.",
      );
      return;
    }

    const cityData = Object.values(this.cities).map((city) => ({
      position: [city.lng, city.lat],
      name: city.name,
      country: city.country,
      population: city.population,
      aqi: city.aqi,
      temp: city.temp,
    }));

    try {
      this.deckglInstance = new deck.DeckGL({
        container: container,
        initialViewState: {
          longitude: 0,
          latitude: 20,
          zoom: 1.5,
          pitch: 45,
          bearing: 0,
          maxZoom: 16,
          minZoom: 0,
        },
        controller: true,
        layers: this.createDeckGLLayers(cityData),
        getTooltip: ({ object }) => this.getDeckGLTooltip(object),
      });

      if (cityData.length > 0) {
        this.addMessage(
          "assistant",
          `3D view loaded with ${cityData.length} cities visualized!`,
        );
      } else {
        this.addMessage(
          "assistant",
          "3D view active. Ask me about locations to see visualizations!",
        );
      }
    } catch (error) {
      console.error("Error initializing Deck.gl:", error);
      this.addMessage("assistant", `Error loading 3D view: ${error.message}`);
    }
  },

  createDeckGLLayers(cityData) {
    const layers = [];

    if (this.activeLayers.column && cityData.length > 0) {
      layers.push(
        new deck.ColumnLayer({
          id: "column-layer",
          data: cityData,
          diskResolution: 12,
          radius: 30000,
          extruded: true,
          pickable: true,
          elevationScale: 100,
          getPosition: (d) => d.position,
          getFillColor: (d) => this.getAQIColor(d.aqi),
          getLineColor: [255, 255, 255],
          getElevation: (d) => d.aqi,
          opacity: 0.8,
        }),
      );
    }

    if (this.activeLayers.hexagon && cityData.length > 0) {
      layers.push(
        new deck.HexagonLayer({
          id: "hexagon-layer",
          data: cityData,
          pickable: true,
          extruded: true,
          radius: 50000,
          elevationScale: 100,
          getPosition: (d) => d.position,
          getElevationWeight: (d) => d.aqi,
          elevationAggregation: "MAX",
          colorRange: [
            [255, 255, 204],
            [161, 218, 180],
            [65, 182, 196],
            [44, 127, 184],
            [37, 52, 148],
          ],
          opacity: 0.6,
        }),
      );
    }

    if (this.activeLayers.scatterplot && cityData.length > 0) {
      layers.push(
        new deck.ScatterplotLayer({
          id: "scatter-layer",
          data: cityData,
          pickable: true,
          opacity: 0.8,
          stroked: true,
          filled: true,
          radiusScale: 6,
          radiusMinPixels: 8,
          radiusMaxPixels: 100,
          lineWidthMinPixels: 2,
          getPosition: (d) => d.position,
          getRadius: (d) => Math.sqrt(d.population) / 10,
          getFillColor: (d) => this.getAQIColor(d.aqi),
          getLineColor: [255, 255, 255],
        }),
      );
    }

    if (this.activeLayers.heatmap && cityData.length > 0) {
      layers.push(
        new deck.HeatmapLayer({
          id: "heatmap-layer",
          data: cityData,
          getPosition: (d) => d.position,
          getWeight: (d) => d.temp,
          radiusPixels: 60,
          intensity: 1,
          threshold: 0.03,
          colorRange: [
            [0, 0, 255, 25],
            [0, 255, 255, 85],
            [0, 255, 0, 127],
            [255, 255, 0, 170],
            [255, 0, 0, 255],
          ],
        }),
      );
    }

    if (this.activeLayers.arc && cityData.length > 1) {
      const arcs = [];
      for (let i = 0; i < cityData.length - 1; i++) {
        arcs.push({
          source: cityData[i].position,
          target: cityData[i + 1].position,
          sourceColor: this.getAQIColor(cityData[i].aqi).slice(0, 3),
          targetColor: this.getAQIColor(cityData[i + 1].aqi).slice(0, 3),
        });
      }

      layers.push(
        new deck.ArcLayer({
          id: "arc-layer",
          data: arcs,
          pickable: true,
          getWidth: 3,
          getSourcePosition: (d) => d.source,
          getTargetPosition: (d) => d.target,
          getSourceColor: (d) => d.sourceColor,
          getTargetColor: (d) => d.targetColor,
          getHeight: 0.4,
        }),
      );
    }

    if (this.activeLayers.grid && cityData.length > 0) {
      layers.push(
        new deck.ScreenGridLayer({
          id: "screen-grid-layer",
          data: cityData,
          pickable: false,
          opacity: 0.8,
          cellSizePixels: 50,
          colorRange: [
            [255, 255, 178, 25],
            [254, 204, 92, 85],
            [253, 141, 60, 127],
            [240, 59, 32, 170],
            [189, 0, 38, 255],
          ],
          getPosition: (d) => d.position,
          getWeight: (d) => d.population / 1000000,
          gpuAggregation: true,
        }),
      );
    }

    if (this.activeLayers.contour && cityData.length > 0) {
      layers.push(
        new deck.ContourLayer({
          id: "contour-layer",
          data: cityData,
          cellSize: 100000,
          getPosition: (d) => d.position,
          getWeight: (d) => d.aqi,
          contours: [
            { threshold: 50, color: [0, 255, 0, 100] },
            { threshold: 100, color: [255, 255, 0, 100] },
            { threshold: 150, color: [255, 165, 0, 100] },
            { threshold: 200, color: [255, 0, 0, 100] },
          ],
          opacity: 0.5,
        }),
      );
    }

    if (this.activeLayers.text && cityData.length > 0) {
      layers.push(
        new deck.TextLayer({
          id: "text-layer",
          data: cityData,
          pickable: true,
          getPosition: (d) => d.position,
          getText: (d) => d.name,
          getSize: 16,
          getAngle: 0,
          getTextAnchor: "middle",
          getAlignmentBaseline: "bottom",
          getColor: [255, 255, 255, 255],
          getPixelOffset: [0, -40],
          fontFamily: "Arial, sans-serif",
          fontWeight: "bold",
          outlineWidth: 2,
          outlineColor: [0, 0, 0, 255],
        }),
      );
    }

    if (this.activeLayers.icon && cityData.length > 0) {
      const ICON_MAPPING = {
        marker: { x: 0, y: 0, width: 128, height: 128, mask: true },
      };

      layers.push(
        new deck.IconLayer({
          id: "icon-layer",
          data: cityData,
          pickable: true,
          iconAtlas:
            "https://raw.githubusercontent.com/visgl/deck.gl-data/master/website/icon-atlas.png",
          iconMapping: ICON_MAPPING,
          getIcon: (d) => "marker",
          sizeScale: 8,
          getPosition: (d) => d.position,
          getSize: (d) => 5,
          getColor: (d) => {
            if (d.temp < 10) return [100, 150, 255];
            if (d.temp < 20) return [150, 200, 255];
            if (d.temp < 30) return [255, 200, 100];
            return [255, 100, 100];
          },
        }),
      );
    }

    return layers;
  },

  getAQIColor(aqi) {
    if (aqi <= 50) return [0, 228, 0, 200];
    if (aqi <= 100) return [255, 255, 0, 200];
    if (aqi <= 150) return [255, 126, 0, 200];
    if (aqi <= 200) return [255, 0, 0, 200];
    return [143, 63, 151, 200];
  },

  getDeckGLTooltip(object) {
    if (object && object.name) {
      return {
        html: `<div style="background: rgba(0,0,0,0.9); padding: 12px; border-radius: 6px; color: white;">
          <b>${object.name}</b><br/>
          ${object.country ? object.country + "<br/>" : ""}
          Population: ${object.population.toLocaleString()}<br/>
          AQI: ${object.aqi} | Temp: ${object.temp}°C
        </div>`,
      };
    }
    return null;
  },

  updateDeckGLLayers() {
    if (!this.deckglInstance) {
      this.initDeckGL();
      return;
    }

    const cityData = Object.values(this.cities).map((city) => ({
      position: [city.lng, city.lat],
      name: city.name,
      country: city.country,
      population: city.population,
      aqi: city.aqi,
      temp: city.temp,
    }));

    try {
      this.deckglInstance.setProps({
        layers: this.createDeckGLLayers(cityData),
      });
    } catch (error) {
      console.error("Error updating Deck.gl layers:", error);
    }
  },

  renderChart(type) {
    const ctx = document.getElementById(`${type}Chart`)?.getContext("2d");
    if (!ctx) return;

    if (this.charts[type]) this.charts[type].destroy();

    if (type === "temperature" && this.temperatureData) {
      this.charts.temperature = new Chart(ctx, {
        type: "line",
        data: {
          labels: this.temperatureData.map((d) => d.time),
          datasets: [
            {
              label: "Temp (°C)",
              data: this.temperatureData.map((d) => d.temp),
              borderColor: "#ef4444",
              backgroundColor: "rgba(239, 68, 68, 0.1)",
              tension: 0.4,
            },
            {
              label: "Humidity (%)",
              data: this.temperatureData.map((d) => d.humidity),
              borderColor: "#3b82f6",
              backgroundColor: "rgba(59, 130, 246, 0.1)",
              tension: 0.4,
            },
          ],
        },
        options: this.getChartOptions(),
      });
    } else if (type === "aqi" && this.aqiData) {
      this.charts.aqi = new Chart(ctx, {
        type: "bar",
        data: {
          labels: this.aqiData.map((d) => d.location),
          datasets: [
            {
              label: "AQI",
              data: this.aqiData.map((d) => d.aqi),
              backgroundColor: "#8b5cf6",
            },
          ],
        },
        options: this.getChartOptions(),
      });
    } else if (type === "population") {
      this.charts.population = new Chart(ctx, {
        type: "bar",
        data: {
          labels: Object.values(this.cities).map((c) => c.name),
          datasets: [
            {
              label: "Population",
              data: Object.values(this.cities).map((c) => c.population),
              backgroundColor: "#10b981",
            },
          ],
        },
        options: { ...this.getChartOptions(), indexAxis: "y" },
      });
    }
  },

  getChartOptions() {
    return {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { labels: { color: "#e5e7eb", font: { size: 10 } } },
      },
      scales: {
        x: {
          ticks: { color: "#9ca3af", font: { size: 9 } },
          grid: { color: "#374151" },
        },
        y: {
          ticks: { color: "#9ca3af", font: { size: 9 } },
          grid: { color: "#374151" },
        },
      },
    };
  },

  async handleQuery() {
    const input = document.getElementById("queryInput");
    const query = input.value.trim();

    if (!query) return;

    this.addMessage("user", query);
    input.value = "";
    this.showLoading();

    // Route based on current mode
    if (this.currentMode === "report") {
      await this.generateReportFromChat(query);
    } else {
      await this.sendToBackend(query);
    }
  },

  toggleMode() {
    this.currentMode = this.currentMode === "chat" ? "report" : "chat";

    const modeLabel = document.getElementById("modeLabel");
    const modeDescription = document.getElementById("modeDescription");
    const modeHint = document.getElementById("modeHint");
    const modeToggle = document.getElementById("modeToggle");
    const chatExamples = document.getElementById("chatModeExamples");
    const reportExamples = document.getElementById("reportModeExamples");
    const queryInput = document.getElementById("queryInput");

    if (this.currentMode === "report") {
      // Switch to Report Mode
      modeLabel.innerHTML =
        '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg><span>Report Mode</span>';
      modeDescription.textContent = "Generate comprehensive markdown reports";
      modeHint.textContent =
        "Report Mode: Generates downloadable markdown reports";
      modeToggle.className =
        "flex gap-2 items-center py-1.5 px-3 text-xs font-semibold bg-green-600 rounded-lg transition-colors hover:bg-green-700";
      queryInput.placeholder =
        "Request a report (e.g., 'Compare Tokyo and London')";
      chatExamples.style.display = "none";
      reportExamples.style.display = "block";

      this.addMessage(
        "assistant",
        "Switched to Report Mode! Ask me to generate comprehensive reports about cities, regions, or comparisons. All responses will be downloadable markdown reports.",
      );
    } else {
      // Switch to Chat Mode
      modeLabel.innerHTML =
        '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg><span>Chat Mode</span>';
      modeDescription.textContent = "Interactive chat with map visualization";
      modeHint.textContent = "Chat Mode: Interactive queries with map updates";
      modeToggle.className =
        "flex gap-2 items-center py-1.5 px-3 text-xs font-semibold bg-blue-600 rounded-lg transition-colors hover:bg-blue-700";
      queryInput.placeholder = "Ask about marked locations...";
      chatExamples.style.display = "block";
      reportExamples.style.display = "none";

      this.addMessage(
        "assistant",
        "Switched to Chat Mode! Ask me about locations, weather, air quality, and I'll update the map with visualizations.",
      );
    }
  },

  async generateReportFromChat(query) {
    try {
      const response = await fetch(REPORT_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to generate report");
      }

      this.generatedMarkdown = await response.text();
      this.hideLoading();

      // Add report as a special message with download button
      this.addReportMessage(this.generatedMarkdown);
    } catch (error) {
      console.error("Error:", error);
      this.hideLoading();
      this.addMessage(
        "assistant",
        `Failed to generate report: ${error.message}. Make sure the backend is running.`,
      );
    }
  },

  addReportMessage(markdown) {
    const container = document.getElementById("messagesContainer");
    if (!container) return;

    const placeholder = container.querySelector(".text-center");
    if (placeholder) placeholder.remove();

    const messageDiv = document.createElement("div");
    messageDiv.className = "flex justify-start";

    const bubble = document.createElement("div");
    bubble.className = "max-w-full message-bubble message-assistant";
    bubble.innerHTML = `
      <div class="mb-3">
        <div class="flex gap-2 items-center mb-2">
          <svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          <span class="font-semibold text-green-400">Report Generated!</span>
        </div>
        <p class="mb-3 text-sm text-gray-300">Your markdown report is ready. Here's a preview:</p>
      </div>
      <div class="overflow-y-auto p-3 mb-3 max-h-48 bg-gray-800 rounded border border-gray-700">
        <pre class="font-mono text-xs text-gray-300 whitespace-pre-wrap">${this.escapeHtml(markdown.substring(0, 500))}${markdown.length > 500 ? "..." : ""}</pre>
      </div>
      <button onclick="app.downloadMarkdown()" class="flex gap-2 justify-center items-center py-2 px-4 w-full font-semibold text-white bg-blue-600 rounded-lg transition-colors hover:bg-blue-700">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        Download Report
      </button>
    `;

    messageDiv.appendChild(bubble);
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
  },

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  },

  setQuery(text) {
    document.getElementById("queryInput").value = text;
  },

  toggleMode() {
    this.currentMode = this.currentMode === "chat" ? "report" : "chat";

    const modeLabel = document.getElementById("modeLabel");
    const modeDescription = document.getElementById("modeDescription");
    const modeHint = document.getElementById("modeHint");
    const modeToggle = document.getElementById("modeToggle");
    const chatExamples = document.getElementById("chatModeExamples");
    const reportExamples = document.getElementById("reportModeExamples");
    const queryInput = document.getElementById("queryInput");

    if (this.currentMode === "report") {
      // Switch to Report Mode
      modeLabel.innerHTML =
        '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg><span>Report Mode</span>';
      modeDescription.textContent = "Generate comprehensive markdown reports";
      modeHint.textContent =
        "Report Mode: Generates downloadable markdown reports";
      modeToggle.className =
        "flex gap-2 items-center py-1.5 px-3 text-xs font-semibold bg-green-600 rounded-lg transition-colors hover:bg-green-700";
      queryInput.placeholder =
        "Request a report (e.g., 'Compare Tokyo and London')";
      chatExamples.style.display = "none";
      reportExamples.style.display = "block";

      this.addMessage(
        "assistant",
        "Switched to Report Mode! Ask me to generate comprehensive reports about cities, regions, or comparisons. All responses will be downloadable markdown reports.",
      );
    } else {
      // Switch to Chat Mode
      modeLabel.innerHTML =
        '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg><span>Chat Mode</span>';
      modeDescription.textContent = "Interactive chat with map visualization";
      modeHint.textContent = "Chat Mode: Interactive queries with map updates";
      modeToggle.className =
        "flex gap-2 items-center py-1.5 px-3 text-xs font-semibold bg-blue-600 rounded-lg transition-colors hover:bg-blue-700";
      queryInput.placeholder = "Ask about marked locations...";
      chatExamples.style.display = "block";
      reportExamples.style.display = "none";

      this.addMessage(
        "assistant",
        "Switched to Chat Mode! Ask me about locations, weather, air quality, and I'll update the map with visualizations.",
      );
    }
  },

  async sendToBackend(query) {
    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          context: {
            clickedPoints: this.clickedPoints.map((p) => ({
              lat: p.lat,
              lng: p.lng,
            })),
            mapView: this.mapView,
            activeLayers: this.activeLayers,
          },
        }),
      });

      const data = await response.json();
      this.handleBackendResponse(data);
    } catch (error) {
      console.error("Backend error:", error);
      this.hideLoading();
      this.addMessage(
        "assistant",
        "Connection error. Make sure FastAPI backend is running on http://localhost:8000",
      );
    }
  },

  handleBackendResponse(response) {
    this.hideLoading();

    if (response.autoAddPoints && response.autoAddPoints.length > 0) {
      response.autoAddPoints.forEach((point) => {
        const clickMarker = L.marker([point.lat, point.lng], {
          icon: L.icon({
            iconUrl:
              "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
            shadowUrl:
              "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41],
          }),
        }).addTo(this.map);

        clickMarker.bindPopup(`
          <div style="color: #1f2937;">
            <b>Location Point</b><br>
            Lat: ${point.lat.toFixed(4)}<br>
            Lng: ${point.lng.toFixed(4)}
          </div>
        `);

        this.clickedPoints.push({
          lat: point.lat,
          lng: point.lng,
          marker: clickMarker,
        });
      });
      this.updateClickedPointsCount();

      if (response.autoAddPoints.length === 1) {
        this.map.setView(
          [response.autoAddPoints[0].lat, response.autoAddPoints[0].lng],
          8,
        );
      }
    }

    if (response.cities) {
      this.cities = response.cities;
      this.highlightedCities = response.highlightCities || [];

      Object.keys(this.cityMarkers).forEach((key) => {
        this.map.removeLayer(this.cityMarkers[key]);
      });
      this.cityMarkers = {};

      Object.entries(this.cities).forEach(([key, city]) => {
        const isHighlighted = this.highlightedCities.includes(key);
        const marker = L.circleMarker([city.lat, city.lng], {
          radius: isHighlighted ? 10 : 8,
          fillColor: isHighlighted ? "#22c55e" : "#3b82f6",
          color: "#fff",
          weight: 2,
          opacity: 1,
          fillOpacity: isHighlighted ? 0.9 : 0.7,
          className: isHighlighted ? "highlight-marker" : "",
        }).addTo(this.map);

        marker.bindPopup(`
          <div style="color: #1f2937; min-width: 150px;">
            <b>${city.name}</b>${isHighlighted ? " ⭐" : ""}<br>
            ${city.country ? city.country + "<br>" : ""}
            Pop: ${city.population.toLocaleString()}<br>
            AQI: ${city.aqi} | Temp: ${city.temp}°C<br>
            ${city.weather || ""}
          </div>
        `);

        this.cityMarkers[key] = marker;
      });

      if (Object.keys(this.cities).length > 1) {
        const bounds = L.latLngBounds(
          Object.values(this.cities).map((c) => [c.lat, c.lng]),
        );
        this.map.fitBounds(bounds, { padding: [50, 50] });
      }
    }

    if (response.addMarkers) {
      response.addMarkers.forEach((markerData) => {
        const customMarker = L.marker([markerData.lat, markerData.lng], {
          icon: L.divIcon({
            className: "custom-marker",
            html: `<div style="background: ${markerData.color || "#8b5cf6"}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">${markerData.label}</div>`,
            iconSize: [null, null],
          }),
        }).addTo(this.map);
        this.customMarkers.push(customMarker);
      });
    }

    if (response.temperatureData) {
      this.temperatureData = response.temperatureData;
    }

    if (response.aqiData) {
      this.aqiData = response.aqiData;
    }

    if (response.response) {
      this.addMessage("assistant", response.response);
    }

    if (response.switchMapView) {
      this.toggleMapView(response.switchMapView);
    }

    if (response.enableLayers) {
      response.enableLayers.forEach((layer) => {
        this.activeLayers[layer] = true;
        const checkbox = document.querySelector(`[data-layer="${layer}"]`);
        if (checkbox) checkbox.checked = true;
      });
      if (this.deckglInstance) this.updateDeckGLLayers();
    }

    if (response.updateCharts) {
      response.updateCharts.forEach((chart) => {
        this.activeCharts[chart] = true;
        const checkbox = document.querySelector(`[data-chart="${chart}"]`);
        if (checkbox) checkbox.checked = true;
        const container = document.getElementById(`${chart}ChartContainer`);
        if (container) {
          container.style.display = "block";
          if (this.charts[chart]) this.charts[chart].destroy();
          this.renderChart(chart);
        }
      });
    }

    if (this.deckglInstance && Object.keys(this.cities).length > 0) {
      this.updateDeckGLLayers();
    }

    if (this.mapView === "deckgl" && Object.keys(this.cities).length > 0) {
      if (this.deckglInstance) {
        this.updateDeckGLLayers();
      } else {
        this.initDeckGL();
      }
    }
  },

  addMessage(role, content) {
    const container = document.getElementById("messagesContainer");
    if (!container) return;

    const placeholder = container.querySelector(".text-center");
    if (placeholder) placeholder.remove();

    const messageDiv = document.createElement("div");
    messageDiv.className = `flex message-enter ${role === "user" ? "justify-end" : "justify-start"}`;

    const bubble = document.createElement("div");
    bubble.className = `message-bubble message-${role}`;
    bubble.textContent = content;
    bubble.style.whiteSpace = "pre-line";

    messageDiv.appendChild(bubble);
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;

    this.messages.push({ role, content });
  },

  showLoading() {
    const container = document.getElementById("messagesContainer");
    if (!container) return;

    const loadingDiv = document.createElement("div");
    loadingDiv.id = "loadingIndicator";
    loadingDiv.className = "flex justify-start";
    loadingDiv.innerHTML = `
      <div class="flex gap-2 items-center p-2 text-sm bg-gray-800 rounded-lg">
        <div class="spinner"></div>
        <span class="text-gray-400">AI analyzing...</span>
      </div>
    `;
    container.appendChild(loadingDiv);
    container.scrollTop = container.scrollHeight;
  },

  hideLoading() {
    document.getElementById("loadingIndicator")?.remove();
  },

  clearPoints() {
    this.clickedPoints.forEach((p) => this.map.removeLayer(p.marker));
    this.clickedPoints = [];
    this.customMarkers.forEach((m) => this.map.removeLayer(m));
    this.customMarkers = [];
    this.updateClickedPointsCount();
    this.addMessage(
      "assistant",
      "All points cleared. Click on the map to mark new locations.",
    );
  },

  downloadMarkdown() {
    if (!this.generatedMarkdown) {
      this.addMessage("assistant", "No report available to download.");
      return;
    }

    const timestamp = new Date().toISOString().slice(0, 10);
    const filename = `report_${timestamp}.md`;

    const blob = new Blob([this.generatedMarkdown], {
      type: "text/markdown",
    });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    this.addMessage("assistant", `Report downloaded as ${filename}`);
  },
};

document.addEventListener("DOMContentLoaded", () => app.init());
window.app = app;
