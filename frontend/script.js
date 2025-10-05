const API_URL = "http://localhost:8000/api/city-data";

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

  init() {
    this.setupEventListeners();
    this.initLeafletMap();
    console.log("Global City Planner initialized - NO initial requests sent");
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

      // Always recreate Deck.gl instance for better reliability
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

    console.log("Initializing Deck.gl...");
    console.log("Cities data:", this.cities);

    const cityData = Object.values(this.cities).map((city) => ({
      position: [city.lng, city.lat],
      name: city.name,
      country: city.country,
      population: city.population,
      aqi: city.aqi,
      temp: city.temp,
    }));

    console.log("City data for Deck.gl:", cityData);

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

      console.log("Deck.gl initialized successfully");

      // Add a message to confirm
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

    // 3D Column Layer - AQI visualization
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

    // Hexagon Layer - Aggregated heatmap
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

    // Scatterplot Layer - City bubbles
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

    // Heatmap Layer - Temperature overlay
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

    // Arc Layer - Connections between cities
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

    // Screen Grid Layer - Density visualization
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

    // Contour Layer - Topographic style
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

    // Text Layer - City labels
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

    // Icon Layer - Weather icons
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
            if (d.temp < 10) return [100, 150, 255]; // Cold - blue
            if (d.temp < 20) return [150, 200, 255]; // Cool - light blue
            if (d.temp < 30) return [255, 200, 100]; // Warm - orange
            return [255, 100, 100]; // Hot - red
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
      console.log("Deck.gl instance not found, initializing...");
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

    console.log("Updating Deck.gl layers with", cityData.length, "cities");

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

    await this.sendToBackend(query);
  },

  setQuery(text) {
    document.getElementById("queryInput").value = text;
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

    // Auto-add points from AI (for "where is X" queries)
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

      // Zoom to the new point
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

      // Fit bounds to show all cities if multiple
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

    // If currently on deck.gl view and we just got new data, refresh it
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
};

document.addEventListener("DOMContentLoaded", () => app.init());
window.app = app;
