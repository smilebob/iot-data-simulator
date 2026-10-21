// Application Web Frontend - IoT Data Simulator

let state = {
  devices: [],
  variables: [],
  broker: {},
  status: {},
  activeFilter: 'all',
  charts: {},
  chartData: {},
  editingVarId: null,
};

let ws = null;

// Initialisation au chargement de la page
document.addEventListener("DOMContentLoaded", async () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  await loadAllData();
  setupWebSocket();
  setInterval(refreshStatus, 3000);
});

async function loadAllData() {
  try {
    const [devRes, varRes, brokerRes, statusRes] = await Promise.all([
      fetch("/api/devices"),
      fetch("/api/variables"),
      fetch("/api/broker"),
      fetch("/api/status")
    ]);

    state.devices = await devRes.json();
    state.variables = await varRes.json();
    state.broker = await brokerRes.json();
    state.status = await statusRes.json();

    updateStatusUI();
    renderDeviceFilters();
    renderVariablesGrid();
  } catch (err) {
    console.error("Erreur chargement données:", err);
  }
}

// Rafraîchissement périodique de l'état
async function refreshStatus() {
  try {
    const res = await fetch("/api/status");
    state.status = await res.json();
    updateStatusUI();
  } catch (err) {
    console.warn("Erreur mise à jour statut:", err);
  }
}

function updateStatusUI() {
  const dot = document.getElementById("broker-status-dot");
  const text = document.getElementById("broker-status-text");
  const counter = document.getElementById("published-counter");
  const btnEngine = document.getElementById("btn-toggle-engine");
  const textEngine = document.getElementById("btn-engine-text");

  if (state.status.mqtt_connected) {
    dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50";
    text.textContent = `MQTT: Connecté (${state.broker.host}:${state.broker.port})`;
  } else {
    dot.className = "w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse";
    text.textContent = state.status.mqtt_error ? `MQTT Erreur: ${state.status.mqtt_error}` : `MQTT Déconnecté`;
  }

  counter.textContent = state.status.messages_published || 0;

  if (state.status.engine_running) {
    btnEngine.className = "flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs px-4 py-2 rounded-lg transition shadow-md shadow-emerald-900/30";
    textEngine.textContent = "Simulation Active";
  } else {
    btnEngine.className = "flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs px-4 py-2 rounded-lg transition border border-slate-700";
    textEngine.textContent = "Simulation Arrêtée";
  }
}

// Connexion WebSocket pour le streaming télémétrique en direct
function setupWebSocket() {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${proto}//${window.location.host}/ws/live`;
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log("WebSocket connecté");
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "telemetry") {
        handleLiveTelemetry(msg.data);
      }
    } catch (e) {
      console.warn("Message WS non JSON:", event.data);
    }
  };

  ws.onclose = () => {
    console.warn("WebSocket fermé. Reconnexion dans 2s...");
    setTimeout(setupWebSocket, 2000);
  };
}

// Mise à jour visuelle d'une variable lors de l'arrivée d'une valeur
function handleLiveTelemetry(data) {
  const { variable_id, value, timestamp, published, topic, anomaly } = data;
  
  // Incrémenter compteur visuel si publié
  if (published) {
    const counter = document.getElementById("published-counter");
    if (counter) {
      counter.textContent = parseInt(counter.textContent || 0) + 1;
    }
  }

  // Mettre à jour la valeur sur la carte
  const valEl = document.getElementById(`val-${variable_id}`);
  if (valEl) {
    valEl.textContent = value;
    valEl.classList.remove("flash-update");
    void valEl.offsetWidth; // Force re-flow CSS
    valEl.classList.add("flash-update");
  }

  const topicEl = document.getElementById(`topic-${variable_id}`);
  if (topicEl && topic) {
    topicEl.textContent = topic;
  }

  // Mettre à jour l'indicateur d'anomalie
  const anomBadge = document.getElementById(`anomaly-badge-${variable_id}`);
  if (anomBadge) {
    if (anomaly && anomaly !== "none") {
      anomBadge.textContent = `Anomalie: ${anomaly.toUpperCase()}`;
      anomBadge.className = "text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-700/60 animate-pulse";
    } else {
      anomBadge.textContent = "";
      anomBadge.className = "hidden";
    }
  }

  // Mettre à jour le graphique sparkline si présent et numérique
  if (typeof value === "number" && state.charts[variable_id]) {
    const chart = state.charts[variable_id];
    const dataPoints = state.chartData[variable_id];
    dataPoints.push(value);
    if (dataPoints.length > 25) {
      dataPoints.shift();
    }
    chart.data.labels = dataPoints.map((_, i) => i);
    chart.data.datasets[0].data = dataPoints;
    chart.update("none");
  }
}

// Rendu des filtres d'équipements
function renderDeviceFilters() {
  const filterBar = document.getElementById("devices-filter-bar");
  const countSpan = document.getElementById("total-vars-count");
  countSpan.textContent = state.variables.length;

  // Supprimer les anciens boutons d'équipements
  const oldBtns = filterBar.querySelectorAll(".dev-filter-btn");
  oldBtns.forEach(b => b.remove());

  state.devices.forEach(dev => {
    const devVars = state.variables.filter(v => v.device_id === dev.id);
    const btn = document.createElement("button");
    btn.className = `dev-filter-btn filter-tab px-3 py-1.5 rounded-lg text-xs font-medium transition ${state.activeFilter === dev.id ? 'active-filter-tab' : ''}`;
    btn.innerHTML = `${escapeHtml(dev.name)} <span class="opacity-75">(${devVars.length})</span>`;
    btn.onclick = () => selectDeviceFilter(dev.id);
    filterBar.appendChild(btn);
  });
}

function selectDeviceFilter(filter) {
  state.activeFilter = filter;
  document.getElementById("filter-dev-all").className = `filter-tab px-3 py-1.5 rounded-lg text-xs font-medium transition ${filter === 'all' ? 'active-filter-tab' : ''}`;
  renderDeviceFilters();
  renderVariablesGrid();
}

// Rendu de la grille des variables
function renderVariablesGrid() {
  const grid = document.getElementById("variables-grid");
  const emptyState = document.getElementById("empty-state");
  grid.innerHTML = "";

  const filtered = state.variables.filter(v => state.activeFilter === "all" || v.device_id === state.activeFilter);

  if (filtered.length === 0) {
    emptyState.classList.remove("hidden");
    return;
  }
  emptyState.classList.add("hidden");

  filtered.forEach(variable => {
    const dev = state.devices.find(d => d.id === variable.device_id) || { name: variable.device_id, platform: "generic" };
    const card = document.createElement("div");
    card.className = "bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col justify-between hover:border-slate-700 transition space-y-4";
    card.id = `card-${variable.id}`;

    const initialVal = variable.current_value !== null && variable.current_value !== undefined ? variable.current_value : "--";

    card.innerHTML = `
      <div>
        <!-- En-tête de la carte -->
        <div class="flex items-start justify-between gap-2">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-slate-100">${escapeHtml(variable.name)}</span>
              <span class="text-[10px] font-mono text-slate-400">(${escapeHtml(variable.id)})</span>
            </div>
            <div class="flex items-center gap-1.5 mt-1">
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                ${escapeHtml(dev.name)}
              </span>
              <span class="text-[10px] px-2 py-0.5 rounded-full ${variable.var_type === 'telemetry' ? 'bg-cyan-950 text-cyan-400 border border-cyan-800/60' : 'bg-purple-950 text-purple-400 border border-purple-800/60'}">
                ${variable.var_type === 'telemetry' ? 'Télémétrie' : 'Attribut/Contrôle'}
              </span>
              <span id="anomaly-badge-${variable.id}" class="hidden"></span>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <button onclick="editVariable('${variable.id}')" title="Modifier" class="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition">
              <i data-lucide="edit-2" class="w-4 h-4"></i>
            </button>
            <button onclick="deleteVariable('${variable.id}')" title="Supprimer" class="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition">
              <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>
          </div>
        </div>

        <!-- Valeur courante & Unité -->
        <div class="mt-4 flex items-baseline justify-between">
          <div class="flex items-baseline gap-2">
            <span id="val-${variable.id}" class="text-3xl font-extrabold tracking-tight font-mono text-white">
              ${initialVal}
            </span>
            <span class="text-sm font-semibold text-cyan-400">${escapeHtml(variable.unit || '')}</span>
          </div>
          <span class="text-[10px] text-slate-500 font-mono">
            ${variable.sim_mode.toUpperCase()} &bull; ${variable.publish_interval}s
          </span>
        </div>

        <!-- Topic MQTT actif -->
        <div class="mt-2 text-[11px] font-mono text-slate-400 bg-slate-950/70 px-2.5 py-1.5 rounded-lg border border-slate-800 flex items-center justify-between">
          <span class="truncate flex items-center gap-1.5" title="${escapeHtml(variable.topic)}">
            <i data-lucide="corner-down-right" class="w-3.5 h-3.5 text-slate-500"></i>
            <span id="topic-${variable.id}">${escapeHtml(variable.topic || 'v1/devices/me/telemetry')}</span>
          </span>
        </div>

        <!-- Sparkline Canvas si numérique -->
        ${variable.data_type === 'float' || variable.data_type === 'integer' ? `
          <div class="mt-3 h-14 w-full">
            <canvas id="chart-${variable.id}"></canvas>
          </div>
        ` : ''}
      </div>

      <!-- Actions de démo ThingsBoard (Anomalies & Forçage) -->
      <div class="pt-3 border-t border-slate-800 space-y-2">
        <div class="flex items-center justify-between text-[11px] text-slate-400">
          <span>Injecteur d'Anomalie :</span>
          <div class="flex items-center gap-1">
            <button onclick="injectAnomaly('${variable.id}', 'spike')" title="Pic anormal (+50)" class="px-2 py-0.5 rounded bg-amber-950/80 hover:bg-amber-900 text-amber-300 border border-amber-800/60 font-medium">💥 Pic</button>
            <button onclick="injectAnomaly('${variable.id}', 'drift')" title="Dérive progressive" class="px-2 py-0.5 rounded bg-orange-950/80 hover:bg-orange-900 text-orange-300 border border-orange-800/60 font-medium">📈 Dérive</button>
            <button onclick="injectAnomaly('${variable.id}', 'freeze')" title="Geler la valeur" class="px-2 py-0.5 rounded bg-blue-950/80 hover:bg-blue-900 text-blue-300 border border-blue-800/60 font-medium">❄️ Gel</button>
            <button onclick="injectAnomaly('${variable.id}', 'timeout')" title="Coupure de com (Timeout ThingsBoard)" class="px-2 py-0.5 rounded bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-800/60 font-medium">🔇 Timeout</button>
            <button onclick="injectAnomaly('${variable.id}', 'none')" title="Rétablir signal normal" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium">🔄</button>
          </div>
        </div>

        <!-- Forçage Manuel -->
        <div class="flex items-center gap-2 pt-1">
          <label class="flex items-center gap-1.5 text-[11px] text-slate-400 cursor-pointer">
            <input type="checkbox" onchange="toggleManualOverride('${variable.id}', this.checked)" ${variable.manual_override ? 'checked' : ''} class="rounded border-slate-700 text-cyan-500 text-xs">
            <span>Forcer :</span>
          </label>
          <input type="text" id="manual-input-${variable.id}" value="${variable.manual_value || ''}" placeholder="valeur..." onchange="updateManualValue('${variable.id}', this.value)" class="flex-1 bg-slate-950 border border-slate-700 rounded px-2 py-0.5 text-xs text-white">
        </div>
      </div>
    `;

    grid.appendChild(card);

    // Initialisation du mini graphique Chart.js
    if (variable.data_type === 'float' || variable.data_type === 'integer') {
      initSparkline(variable.id);
    }
  });

  if (window.lucide) {
    lucide.createIcons();
  }
}

function initSparkline(varId) {
  const ctx = document.getElementById(`chart-${varId}`);
  if (!ctx) return;

  state.chartData[varId] = state.chartData[varId] || [0];

  state.charts[varId] = new Chart(ctx, {
    type: "line",
    data: {
      labels: state.chartData[varId].map((_, i) => i),
      datasets: [{
        data: state.chartData[varId],
        borderColor: "#06b6d4",
        borderWidth: 2,
        tension: 0.35,
        pointRadius: 0,
        fill: true,
        backgroundColor: "rgba(6, 182, 212, 0.08)",
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: {
        x: { display: false },
        y: { display: false }
      },
      animation: false
    }
  });
}

// Contrôle Global de la Simulation
async function toggleEngine() {
  const endpoint = state.status.engine_running ? "/api/simulation/stop" : "/api/simulation/start";
  await fetch(endpoint, { method: "POST" });
  await refreshStatus();
}

// Injection d'Anomalie
async function injectAnomaly(varId, anomalyType) {
  await fetch(`/api/variables/${varId}/anomaly`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ anomaly: anomalyType, magnitude: 50.0 })
  });
}

// Forçage Manuel
async function toggleManualOverride(varId, enabled) {
  const val = document.getElementById(`manual-input-${varId}`).value;
  await fetch(`/api/variables/${varId}/override`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ manual_override: enabled, manual_value: val })
  });
  const v = state.variables.find(item => item.id === varId);
  if (v) v.manual_override = enabled;
}

async function updateManualValue(varId, val) {
  await fetch(`/api/variables/${varId}/override`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ manual_override: true, manual_value: val })
  });
  const v = state.variables.find(item => item.id === varId);
  if (v) {
    v.manual_override = true;
    v.manual_value = val;
  }
}

// Gestion des Modales & Formulaires
function openVariableModal(varToEdit = null) {
  state.editingVarId = varToEdit ? varToEdit.id : null;
  document.getElementById("var-is-edit").value = varToEdit ? "true" : "false";
  document.getElementById("modal-variable-title").innerHTML = varToEdit ?
    `<i data-lucide="edit-2" class="w-5 h-5 text-cyan-400"></i> Modifier la Variable` :
    `<i data-lucide="sliders" class="w-5 h-5 text-cyan-400"></i> Nouvelle Variable`;

  // Remplir le select d'équipements
  const devSelect = document.getElementById("var-device-id");
  devSelect.innerHTML = "";
  state.devices.forEach(d => {
    const opt = document.createElement("option");
    opt.value = d.id;
    opt.textContent = `${d.name} (${d.platform})`;
    devSelect.appendChild(opt);
  });

  if (varToEdit) {
    document.getElementById("var-id").value = varToEdit.id;
    document.getElementById("var-id").disabled = true;
    document.getElementById("var-name").value = varToEdit.name;
    document.getElementById("var-device-id").value = varToEdit.device_id;
    document.getElementById("var-data-type").value = varToEdit.data_type;
    document.getElementById("var-type").value = varToEdit.var_type;
    document.getElementById("var-unit").value = varToEdit.unit || "";
    document.getElementById("var-interval").value = varToEdit.publish_interval;
    document.getElementById("var-topic").value = varToEdit.topic || "";
    document.getElementById("var-sim-mode").value = varToEdit.sim_mode;

    // Paramètres math
    document.getElementById("math-min").value = varToEdit.math_config.min_val;
    document.getElementById("math-max").value = varToEdit.math_config.max_val;
    document.getElementById("math-period").value = varToEdit.math_config.period;
    document.getElementById("math-noise").value = varToEdit.math_config.noise_percent;
    document.getElementById("math-constant").value = varToEdit.math_config.constant_val;

    // Tableau de points
    renderPointsTable(varToEdit.points_config ? varToEdit.points_config.points : []);
  } else {
    document.getElementById("var-id").value = "";
    document.getElementById("var-id").disabled = false;
    document.getElementById("var-name").value = "";
    document.getElementById("var-unit").value = "";
    document.getElementById("var-topic").value = "";
    document.getElementById("var-interval").value = "3.0";
    document.getElementById("var-sim-mode").value = "sine";
    renderPointsTable([]);
  }

  toggleSimModeSections();
  openModal("modal-variable");
}

function toggleSimModeSections() {
  const mode = document.getElementById("var-sim-mode").value;
  const mathSec = document.getElementById("section-math-params");
  const pointsSec = document.getElementById("section-points-params");
  const constWrap = document.getElementById("constant-val-wrapper");

  if (mode === "points_table") {
    mathSec.classList.add("hidden");
    pointsSec.classList.remove("hidden");
  } else {
    mathSec.classList.remove("hidden");
    pointsSec.classList.add("hidden");
    if (mode === "constant") {
      constWrap.classList.remove("hidden");
    } else {
      constWrap.classList.add("hidden");
    }
  }
}

function renderPointsTable(points) {
  const tbody = document.getElementById("points-table-body");
  tbody.innerHTML = "";
  if (!points || points.length === 0) {
    addPointRow(0, 0);
    return;
  }
  points.forEach(p => addPointRow(p.offset_seconds, p.value));
}

function addPointRow(offset = 0, val = 0) {
  const tbody = document.getElementById("points-table-body");
  const tr = document.createElement("tr");
  tr.className = "hover:bg-slate-900/60";
  tr.innerHTML = `
    <td class="p-2"><input type="number" step="any" value="${offset}" class="point-offset w-24 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-100"></td>
    <td class="p-2"><input type="text" value="${val}" class="point-value w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-100"></td>
    <td class="p-2 text-right"><button type="button" onclick="this.closest('tr').remove()" class="text-rose-400 hover:text-rose-300"><i data-lucide="trash" class="w-4 h-4"></i></button></td>
  `;
  tbody.appendChild(tr);
  if (window.lucide) lucide.createIcons();
}

async function saveVariableForm(e) {
  e.preventDefault();
  const isEdit = document.getElementById("var-is-edit").value === "true";
  const simMode = document.getElementById("var-sim-mode").value;

  // Récupérer les points du tableau si actif
  const points = [];
  document.querySelectorAll("#points-table-body tr").forEach(tr => {
    const off = parseFloat(tr.querySelector(".point-offset")?.value || 0);
    const val = tr.querySelector(".point-value")?.value || 0;
    points.push({ offset_seconds: off, value: val });
  });

  const varPayload = {
    id: document.getElementById("var-id").value.trim(),
    name: document.getElementById("var-name").value.trim(),
    device_id: document.getElementById("var-device-id").value,
    var_type: document.getElementById("var-type").value,
    data_type: document.getElementById("var-data-type").value,
    unit: document.getElementById("var-unit").value.trim(),
    topic: document.getElementById("var-topic").value.trim(),
    publish_interval: parseFloat(document.getElementById("var-interval").value),
    sim_mode: simMode,
    math_config: {
      min_val: parseFloat(document.getElementById("math-min").value),
      max_val: parseFloat(document.getElementById("math-max").value),
      period: parseFloat(document.getElementById("math-period").value),
      noise_percent: parseFloat(document.getElementById("math-noise").value),
      constant_val: document.getElementById("math-constant").value,
    },
    points_config: {
      points: points,
      loop: document.getElementById("points-loop").checked,
      interpolate: document.getElementById("points-interpolate").checked,
      playback_speed: 1.0,
    },
    enabled: true,
  };

  await fetch("/api/variables", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(varPayload)
  });

  closeModal("modal-variable");
  await loadAllData();
}

function editVariable(varId) {
  const v = state.variables.find(item => item.id === varId);
  if (v) openVariableModal(v);
}

async function deleteVariable(varId) {
  if (confirm(`Confirmez-vous la suppression de la variable '${varId}' ?`)) {
    await fetch(`/api/variables/${varId}`, { method: "DELETE" });
    await loadAllData();
  }
}

// Modal Équipement (Device)
function openDeviceModal() {
  document.getElementById("dev-id").value = "";
  document.getElementById("dev-name").value = "";
  document.getElementById("dev-token").value = "";
  openModal("modal-device");
}

async function saveDeviceForm(e) {
  e.preventDefault();
  const devPayload = {
    id: document.getElementById("dev-id").value.trim(),
    name: document.getElementById("dev-name").value.trim(),
    platform: document.getElementById("dev-platform").value,
    token: document.getElementById("dev-token").value.trim() || null,
    enabled: true,
  };

  await fetch("/api/devices", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(devPayload)
  });

  closeModal("modal-device");
  await loadAllData();
}

// Modal Broker MQTT
function openBrokerModal() {
  document.getElementById("broker-host").value = state.broker.host || "mosquitto";
  document.getElementById("broker-port").value = state.broker.port || 1883;
  document.getElementById("broker-tls").checked = state.broker.use_tls || false;
  document.getElementById("broker-user").value = state.broker.username || "";
  document.getElementById("broker-pass").value = state.broker.password || "";
  openModal("modal-broker");
}

async function saveBrokerForm(e) {
  e.preventDefault();
  const brokerPayload = {
    host: document.getElementById("broker-host").value.trim(),
    port: parseInt(document.getElementById("broker-port").value),
    use_tls: document.getElementById("broker-tls").checked,
    username: document.getElementById("broker-user").value.trim() || null,
    password: document.getElementById("broker-pass").value.trim() || null,
  };

  await fetch("/api/broker", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(brokerPayload)
  });

  closeModal("modal-broker");
  await refreshStatus();
}

// Helpers Modales
function openModal(id) {
  document.getElementById(id).classList.remove("hidden");
  if (window.lucide) lucide.createIcons();
}

function closeModal(id) {
  document.getElementById(id).classList.add("hidden");
}

// Export / Import Scénario
async function exportScenario() {
  const res = await fetch("/api/scenario/export");
  const data = await res.json();
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `iot_scenario_${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
}

async function importScenario(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = async (e) => {
    try {
      const data = JSON.parse(e.target.result);
      await fetch("/api/scenario/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      alert("Scénario importé avec succès !");
      await loadAllData();
    } catch (err) {
      alert("Format de fichier JSON invalide");
    }
  };
  reader.readAsText(file);
}

// Upload CSV pour Points Table
async function uploadPointsCSV(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    const text = e.target.result;
    const lines = text.split("\n");
    const points = [];
    lines.forEach(line => {
      const parts = line.split(",");
      if (parts.length >= 2) {
        const off = parseFloat(parts[0].trim());
        const val = parts[1].trim();
        if (!isNaN(off)) {
          points.push({ offset_seconds: off, value: val });
        }
      }
    });
    if (points.length > 0) {
      renderPointsTable(points);
      alert(`${points.length} points chargés depuis le fichier CSV !`);
    } else {
      alert("Format CSV invalide. Attendu: offset_secondes,valeur");
    }
  };
  reader.readAsText(file);
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
