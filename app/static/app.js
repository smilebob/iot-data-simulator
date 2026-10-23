// Application Web Frontend - IoT Data Simulator

let state = {
  currentUser: null,
  devices: [],
  variables: [],
  broker: {},
  status: {},
  activeFilter: 'all',
  collapsedDevices: new Set(JSON.parse(localStorage.getItem("iot_sim_collapsed_devices") || "[]")),
  charts: {},
  chartData: {},
  editingVarId: null,
  editingDevId: null,
};

let ws = null;
let statusInterval = null;

// Initialisation au chargement de la page
document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  safeCreateIcons();
  const isAuthenticated = await checkAuthStatus();
  if (isAuthenticated) {
    await loadAllData();
    setupWebSocket();
    if (statusInterval) clearInterval(statusInterval);
    statusInterval = setInterval(refreshStatus, 3000);
  }
});

// Initialisation & Gestion du Thème (Clair / Sombre)
function initTheme() {
  const savedTheme = localStorage.getItem("iot_sim_theme") || "dark";
  applyTheme(savedTheme);
}

function applyTheme(theme) {
  const root = document.documentElement;
  const isDark = theme === "dark";

  if (isDark) {
    root.classList.add("dark");
    root.classList.remove("light");
  } else {
    root.classList.add("light");
    root.classList.remove("dark");
  }

  localStorage.setItem("iot_sim_theme", theme);
  updateThemeToggleUI(theme);
}

function toggleTheme() {
  const isDark = document.documentElement.classList.contains("dark");
  const newTheme = isDark ? "light" : "dark";
  applyTheme(newTheme);
}

function updateThemeToggleUI(theme) {
  const icon = document.getElementById("theme-icon");
  const label = document.getElementById("theme-text");
  if (!icon) return;

  if (theme === "light") {
    icon.setAttribute("data-lucide", "moon");
    icon.className = "w-4 h-4 text-indigo-500";
    if (label) label.textContent = "Sombre";
  } else {
    icon.setAttribute("data-lucide", "sun");
    icon.className = "w-4 h-4 text-amber-400";
    if (label) label.textContent = "Clair";
  }
  safeCreateIcons();
}

function safeCreateIcons() {
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    try {
      window.lucide.createIcons();
    } catch (e) {
      console.warn("Erreur chargement icônes Lucide:", e);
    }
  }
}

async function loadAllData() {
  try {
    const [devRes, varRes, brokerRes, statusRes] = await Promise.all([
      fetch("/api/devices"),
      fetch("/api/variables"),
      fetch("/api/broker"),
      fetch("/api/status")
    ]);

    if (devRes.status === 401 || varRes.status === 401 || brokerRes.status === 401 || statusRes.status === 401) {
      await checkAuthStatus();
      return;
    }

    if (!devRes.ok || !varRes.ok || !brokerRes.ok || !statusRes.ok) {
      console.error("Erreur HTTP lors du chargement des données API");
      return;
    }

    state.devices = await devRes.json();
    state.variables = await varRes.json();
    state.broker = await brokerRes.json();
    state.status = await statusRes.json();

    console.log(`Données chargées : ${state.devices.length} équipement(s), ${state.variables.length} variable(s)`);

    updateStatusUI();
    renderDeviceFilters();
    renderEquipmentGroups();
  } catch (err) {
    console.error("Erreur globale chargement données:", err);
  }
}

// Rafraîchissement périodique de l'état
async function refreshStatus() {
  try {
    const res = await fetch("/api/status");
    if (res.ok) {
      state.status = await res.json();
      updateStatusUI();
    }
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

  if (!dot || !text || !counter || !btnEngine || !textEngine) return;

  if (state.status.mqtt_connected) {
    dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50";
    text.textContent = `MQTT: Connecté (${state.broker.host || 'mosquitto'}:${state.broker.port || 1883})`;
  } else {
    dot.className = "w-2.5 h-2.5 rounded-full bg-[#E2001A] animate-pulse";
    text.textContent = state.status.mqtt_error ? `MQTT Erreur: ${state.status.mqtt_error}` : `MQTT Déconnecté`;
  }

  counter.textContent = state.status.messages_published || 0;

  if (state.status.version) {
    const verBadge = document.getElementById("app-version-badge");
    if (verBadge) {
      verBadge.textContent = state.status.version;
    }
  }

  if (state.status.engine_running) {
    btnEngine.className = "flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs px-4 py-2 rounded-lg transition shadow-md shadow-emerald-900/30";
    textEngine.textContent = "Simulation Active";
  } else {
    btnEngine.className = "flex items-center gap-2 bg-[#202531] hover:bg-[#2B3342] text-slate-300 font-medium text-xs px-4 py-2 rounded-lg transition border border-[#2B3342]";
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
      } else if (msg.type === "log") {
        handleLiveLog(msg.data);
      }
    } catch (e) {
      console.warn("Message WS non JSON:", event.data);
    }
  };

  ws.onclose = (e) => {
    if (e.code === 1008 || e.code === 4001 || !state.currentUser) {
      console.warn("WebSocket fermé : authentification requise.");
      return;
    }
    console.warn("WebSocket fermé. Reconnexion dans 2s...");
    setTimeout(() => {
      if (state.currentUser) setupWebSocket();
    }, 2000);
  };
}

// Mise à jour visuelle d'une variable lors de l'arrivée d'une valeur
function handleLiveTelemetry(data) {
  const { variable_id, value, timestamp, published, topic, anomaly } = data;
  
  if (published) {
    const counter = document.getElementById("published-counter");
    if (counter) {
      counter.textContent = parseInt(counter.textContent || 0) + 1;
    }
  }

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
  if (typeof value === "number" && state.charts && state.charts[variable_id]) {
    try {
      const chart = state.charts[variable_id];
      const dataPoints = state.chartData[variable_id] || [];
      dataPoints.push(value);
      if (dataPoints.length > 25) {
        dataPoints.shift();
      }
      chart.data.labels = dataPoints.map((_, i) => i);
      chart.data.datasets[0].data = dataPoints;
      chart.update("none");
    } catch (e) {
      console.debug("Erreur mise à jour sparkline:", e);
    }
  }
}

// Rendu des filtres d'équipements
function renderDeviceFilters() {
  const filterBar = document.getElementById("devices-filter-bar");
  const countSpan = document.getElementById("total-vars-count");
  if (!filterBar) return;
  if (countSpan) countSpan.textContent = state.variables.length;

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
  const allBtn = document.getElementById("filter-dev-all");
  if (allBtn) {
    allBtn.className = `filter-tab px-3 py-1.5 rounded-lg text-xs font-medium transition ${filter === 'all' ? 'active-filter-tab' : ''}`;
  }
  renderDeviceFilters();
  renderEquipmentGroups();
}

// Nettoyage sécurisé des instances Chart.js
function destroyAllCharts() {
  for (const varId in state.charts) {
    try {
      if (state.charts[varId]) {
        state.charts[varId].destroy();
      }
    } catch (e) {}
  }
  state.charts = {};
}

// Rendu STRUCTURÉ : Regroupement CLAIR des variables par Équipement
function renderEquipmentGroups() {
  const container = document.getElementById("equipment-groups-container") || document.getElementById("variables-grid");
  const emptyState = document.getElementById("empty-state");
  if (!container) {
    console.error("Conteneur d'affichage introuvable dans le DOM");
    return;
  }

  // Nettoyage des graphiques existants
  destroyAllCharts();
  container.innerHTML = "";

  const visibleDevices = state.devices.filter(d => state.activeFilter === "all" || d.id === state.activeFilter);

  if (visibleDevices.length === 0) {
    if (emptyState) emptyState.classList.remove("hidden");
    return;
  }
  if (emptyState) emptyState.classList.add("hidden");

  visibleDevices.forEach(device => {
    const devVars = state.variables.filter(v => v.device_id === device.id);
    
    // Détermination du badge plateforme
    let platformBadgeHtml = "";
    if (device.platform === "thingsboard") {
      platformBadgeHtml = `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-red-950/80 text-red-300 border border-red-800/80 flex items-center gap-1">
        <i data-lucide="cloud" class="w-3 h-3 text-[#E2001A]"></i> ThingsBoard
      </span>`;
    } else if (device.platform === "homeassistant") {
      platformBadgeHtml = `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-950/80 text-blue-300 border border-blue-800/80 flex items-center gap-1">
        <i data-lucide="home" class="w-3 h-3 text-blue-400"></i> Home Assistant
      </span>`;
    } else if (device.platform === "datacake") {
      platformBadgeHtml = `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-800/80 flex items-center gap-1">
        <i data-lucide="database" class="w-3 h-3 text-amber-400"></i> Datacake
      </span>`;
    } else {
      platformBadgeHtml = `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-800 text-slate-300 border border-slate-700 flex items-center gap-1">
        <i data-lucide="radio" class="w-3 h-3 text-slate-400"></i> MQTT Standard
      </span>`;
    }

    // Détermination du badge protocole
    let protocolBadgeHtml = "";
    const proto = (device.protocol || "mqtt").toLowerCase();
    if (device.platform === "thingsboard") {
      if (proto === "http") {
        protocolBadgeHtml = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-700/70 flex items-center gap-1" title="Protocole: ThingsBoard HTTP REST v1 (Port 443 / Cloudflare OK)">
          <i data-lucide="globe" class="w-3 h-3 text-emerald-400"></i> HTTP
        </span>`;
      } else if (proto === "coap") {
        protocolBadgeHtml = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-950 text-purple-300 border border-purple-700/70 flex items-center gap-1" title="Protocole: ThingsBoard CoAP UDP (RFC 7252 / Port 5683)">
          <i data-lucide="zap" class="w-3 h-3 text-purple-400"></i> CoAP
        </span>`;
      } else {
        protocolBadgeHtml = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-950 text-sky-300 border border-sky-700/70 flex items-center gap-1" title="Protocole: Standard MQTT">
          <i data-lucide="radio" class="w-3 h-3 text-sky-400"></i> MQTT
        </span>`;
      }
    }

    // Détermination du badge cadence d'envoi
    let cadenceBadgeHtml = "";
    if (device.publish_interval != null && device.publish_interval > 0) {
      cadenceBadgeHtml = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950/70 text-amber-300 border border-amber-700/60 flex items-center gap-1" title="Cadence globale imposée : ${device.publish_interval}s sur toutes les grandeurs">
        <i data-lucide="timer" class="w-3 h-3 text-amber-400"></i> Cadence : ${device.publish_interval}s
      </span>`;
    } else {
      cadenceBadgeHtml = `<span class="px-2 py-0.5 rounded text-[10px] text-slate-400 bg-[#12151B] border border-[#2B3342] flex items-center gap-1" title="Cadences définies individuellement par grandeur">
        <i data-lucide="clock" class="w-3 h-3 text-slate-500"></i> Cadence variable
      </span>`;
    }

    const canOperate = state.currentUser && (state.currentUser.role === "admin" || state.currentUser.role === "operator");
    let devActionsHtml = "";
    if (canOperate) {
      devActionsHtml = `
        <div class="flex items-center gap-2 flex-wrap">
          <button onclick="downloadDeviceCsv('${device.id}')" title="Télécharger le fichier CSV d'importation ThingsBoard pour cet équipement" class="p-2 text-emerald-400 hover:text-white bg-[#202531] hover:bg-[#2B3342] rounded-lg transition border border-[#2B3342] flex items-center gap-1.5 text-xs font-medium">
            <i data-lucide="file-spreadsheet" class="w-3.5 h-3.5 text-emerald-400"></i>
            <span>CSV TB</span>
          </button>
          <button onclick="downloadDeviceDashboard('${device.id}')" title="Télécharger le tableau de bord ThingsBoard JSON préconfiguré pour cet équipement (avec token et grandeurs)" class="p-2 text-sky-400 hover:text-white bg-[#202531] hover:bg-[#2B3342] rounded-lg transition border border-[#2B3342] flex items-center gap-1.5 text-xs font-medium">
            <i data-lucide="layout-dashboard" class="w-3.5 h-3.5 text-sky-400"></i>
            <span>Dashboard TB</span>
          </button>
          <button onclick="openVariableModalForDevice('${device.id}')" class="flex items-center gap-1.5 btn-primary-red text-xs font-semibold px-3 py-1.5 rounded-lg transition shadow-md shadow-red-900/30">
            <i data-lucide="plus" class="w-3.5 h-3.5"></i>
            <span>Ajouter une Variable</span>
          </button>
          <button onclick="testDeviceById('${device.id}')" title="Tester la communication avec ThingsBoard" class="p-2 text-amber-300 hover:text-white bg-[#202531] hover:bg-[#2B3342] rounded-lg transition border border-[#2B3342] flex items-center gap-1 text-xs font-medium">
            <i data-lucide="activity" class="w-3.5 h-3.5 text-amber-400"></i>
            <span>Tester</span>
          </button>
          <button onclick="editDevice('${device.id}')" title="Modifier cet équipement" class="p-2 text-slate-300 hover:text-white bg-[#202531] hover:bg-[#2B3342] rounded-lg transition border border-[#2B3342] flex items-center gap-1 text-xs font-medium">
            <i data-lucide="edit-3" class="w-3.5 h-3.5 text-slate-400"></i>
            <span>Éditer</span>
          </button>
          <button onclick="deleteDevice('${device.id}')" title="Supprimer cet équipement" class="p-2 text-rose-400 hover:text-rose-300 hover:bg-rose-950/40 rounded-lg transition border border-[#2B3342] flex items-center gap-1 text-xs font-medium">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
            <span>Supprimer</span>
          </button>
        </div>
      `;
    } else {
      devActionsHtml = `
        <div class="flex items-center gap-2 flex-wrap">
          <button onclick="downloadDeviceCsv('${device.id}')" title="Télécharger le fichier CSV d'importation ThingsBoard pour cet équipement" class="p-2 text-emerald-400 hover:text-white bg-[#202531] hover:bg-[#2B3342] rounded-lg transition border border-[#2B3342] flex items-center gap-1.5 text-xs font-medium">
            <i data-lucide="file-spreadsheet" class="w-3.5 h-3.5 text-emerald-400"></i>
            <span>CSV TB</span>
          </button>
          <button onclick="downloadDeviceDashboard('${device.id}')" title="Télécharger le tableau de bord ThingsBoard JSON préconfiguré pour cet équipement" class="p-2 text-sky-400 hover:text-white bg-[#202531] hover:bg-[#2B3342] rounded-lg transition border border-[#2B3342] flex items-center gap-1.5 text-xs font-medium">
            <i data-lucide="layout-dashboard" class="w-3.5 h-3.5 text-sky-400"></i>
            <span>Dashboard TB</span>
          </button>
          <span class="text-[10px] text-slate-500 italic bg-[#12151B] px-2.5 py-1 rounded border border-[#2B3342] flex items-center gap-1">
            <i data-lucide="eye" class="w-3 h-3 text-slate-500"></i> Observateur (Lecture Seule)
          </span>
        </div>
      `;
    }

    const isCollapsed = state.collapsedDevices.has(device.id);

    // Bloc de Section d'Équipement
    const section = document.createElement("section");
    section.className = "device-group-card shadow-2xl overflow-hidden";
    section.id = `device-section-${device.id}`;

    section.innerHTML = `
      <!-- Ligne d'accentuation supérieure -->
      <div class="card-accent-line"></div>

      <!-- En-tête de l'Équipement (Accordéon cliquable) -->
      <div class="bg-[#181D26] px-6 py-4 flex flex-wrap items-center justify-between gap-4 border-b border-[#2B3342] cursor-pointer hover:bg-[#1C222D] transition select-none" onclick="toggleDeviceSection('${device.id}', event)">
        <div class="flex items-center gap-3">
          <button type="button" class="p-1.5 rounded-lg bg-[#202531] border border-[#2B3342] text-slate-300 hover:text-white transition" title="${isCollapsed ? 'Déplier' : 'Plier'} cet équipement">
            <i data-lucide="${isCollapsed ? 'chevron-right' : 'chevron-down'}" class="w-4 h-4 text-slate-300 device-chevron-${device.id}"></i>
          </button>
          <div class="p-2.5 bg-[#202531] border border-[#2B3342] rounded-xl text-white">
            <i data-lucide="cpu" class="w-5 h-5 text-[#E2001A]"></i>
          </div>
          <div>
            <div class="flex items-center gap-2 flex-wrap">
              <h2 class="text-base font-bold text-white tracking-tight">${escapeHtml(device.name)}</h2>
              <span class="text-xs font-mono text-slate-400">(${escapeHtml(device.id)})</span>
              <span class="device-collapsed-summary-${device.id} ${isCollapsed ? '' : 'hidden'} text-[11px] font-medium px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                Replié (${devVars.length} grandeur${devVars.length > 1 ? 's' : ''})
              </span>
            </div>
            <div class="flex items-center gap-2 mt-1 flex-wrap">
              ${platformBadgeHtml}
              ${protocolBadgeHtml}
              ${cadenceBadgeHtml}
              ${device.token ? `
                <span class="text-[11px] font-mono px-2 py-0.5 rounded bg-[#12151B] text-slate-300 border border-[#2B3342] flex items-center gap-1" title="Token: ${escapeHtml(device.token)}">
                  <i data-lucide="key" class="w-3 h-3 text-amber-400"></i> Token: &bull;&bull;&bull;&bull;&bull;&bull;
                </span>
              ` : ''}
              <span class="text-[11px] px-2 py-0.5 rounded bg-[#12151B] text-slate-300 border border-[#2B3342]">
                ${devVars.length} variable(s)
              </span>
            </div>
          </div>
        </div>

        <div onclick="event.stopPropagation()">
          ${devActionsHtml}
        </div>
      </div>

      <!-- Grille interne des variables de cet équipement -->
      <div id="vars-container-${device.id}" class="p-6 bg-[#12151B] ${isCollapsed ? 'hidden' : ''}">
        <div id="vars-grid-${device.id}" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"></div>
      </div>
    `;

    container.appendChild(section);

    const varsGrid = section.querySelector(`#vars-grid-${device.id}`);

    if (devVars.length === 0) {
      varsGrid.className = "text-center py-8 border border-dashed border-[#2B3342] rounded-xl p-4";
      varsGrid.innerHTML = `
        <p class="text-xs text-slate-400 mb-2">Aucune variable de télémétrie configurée pour cet équipement.</p>
        <button onclick="openVariableModalForDevice('${device.id}')" class="inline-flex items-center gap-1.5 btn-primary-red text-xs font-semibold px-3 py-1.5 rounded-lg transition">
          <i data-lucide="plus" class="w-3.5 h-3.5"></i> Ajouter une première variable
        </button>
      `;
    } else {
      devVars.forEach(variable => {
        try {
          const card = createVariableCard(variable, device);
          varsGrid.appendChild(card);
          if (variable.data_type === 'float' || variable.data_type === 'integer') {
            initSparkline(variable.id);
          }
        } catch (cardErr) {
          console.error(`Erreur création carte variable ${variable.id}:`, cardErr);
        }
      });
    }
  });

  safeCreateIcons();
}

// Création d'une carte de variable
function createVariableCard(variable, device) {
  const card = document.createElement("div");
  card.className = "bg-[#181D26] border border-[#2B3342] rounded-xl p-5 shadow-lg flex flex-col justify-between hover:border-slate-600 transition space-y-4";
  card.id = `card-${variable.id}`;

  const initialVal = variable.current_value !== null && variable.current_value !== undefined ? variable.current_value : "--";

  const canOperateVar = state.currentUser && (state.currentUser.role === "admin" || state.currentUser.role === "operator");
  const varActionsHtml = canOperateVar ? `
    <div class="flex items-center gap-1">
      <button onclick="editVariable('${variable.id}')" title="Modifier la variable" class="p-1.5 text-slate-400 hover:text-white hover:bg-[#202531] rounded-lg transition">
        <i data-lucide="edit-2" class="w-3.5 h-3.5"></i>
      </button>
      <button onclick="deleteVariable('${variable.id}')" title="Supprimer la variable" class="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-[#202531] rounded-lg transition">
        <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
      </button>
    </div>
  ` : '';

  const chaosActionsHtml = canOperateVar ? `
    <!-- Actions de démo ThingsBoard (Anomalies & Forçage) -->
    <div class="pt-3 border-t border-[#2B3342] space-y-2">
      <div class="flex items-center justify-between text-[11px] text-slate-400">
        <span class="font-medium text-slate-300">Chaos Button :</span>
        <div class="flex items-center gap-1">
          <button onclick="injectAnomaly('${variable.id}', 'spike')" title="Pic anormal (+50)" class="px-2 py-0.5 rounded bg-amber-950/80 hover:bg-amber-900 text-amber-300 border border-amber-800/60 font-semibold">💥 Pic</button>
          <button onclick="injectAnomaly('${variable.id}', 'drift')" title="Dérive progressive" class="px-2 py-0.5 rounded bg-orange-950/80 hover:bg-orange-900 text-orange-300 border border-orange-800/60 font-semibold">📈 Dérive</button>
          <button onclick="injectAnomaly('${variable.id}', 'freeze')" title="Geler la valeur" class="px-2 py-0.5 rounded bg-blue-950/80 hover:bg-blue-900 text-blue-300 border border-blue-800/60 font-semibold">❄️ Gel</button>
          <button onclick="injectAnomaly('${variable.id}', 'timeout')" title="Coupure réseau" class="px-2 py-0.5 rounded bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-800/60 font-semibold">🔇 Timeout</button>
          <button onclick="injectAnomaly('${variable.id}', 'none')" title="Rétablir signal normal" class="px-2 py-0.5 rounded bg-[#202531] hover:bg-[#2B3342] text-slate-300 font-semibold">🔄</button>
        </div>
      </div>

      <!-- Forçage Manuel -->
      <div class="flex items-center gap-2 pt-1">
        <label class="flex items-center gap-1.5 text-[11px] text-slate-300 cursor-pointer">
          <input type="checkbox" onchange="toggleManualOverride('${variable.id}', this.checked)" ${variable.manual_override ? 'checked' : ''} class="rounded border-[#2B3342] text-[#E2001A]">
          <span>Forcer :</span>
        </label>
        <input type="text" id="manual-input-${variable.id}" value="${variable.manual_value || ''}" placeholder="valeur..." onchange="updateManualValue('${variable.id}', this.value)" class="flex-1 bg-[#0F1218] border border-[#2B3342] rounded px-2 py-0.5 text-xs text-white">
      </div>
    </div>
  ` : `
    <div class="pt-2 border-t border-[#2B3342]/60 text-right">
      <span class="text-[10px] text-slate-500 italic">Affichage télémétrique en direct (Lecture seule)</span>
    </div>
  `;

  card.innerHTML = `
    <div>
      <!-- En-tête de la carte -->
      <div class="flex items-start justify-between gap-2">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-xs font-bold text-white">${escapeHtml(variable.name)}</span>
            <span class="text-[10px] font-mono text-slate-400">(${escapeHtml(variable.id)})</span>
          </div>
          <div class="flex items-center gap-1.5 mt-1">
            <span class="text-[10px] px-2 py-0.5 rounded-full ${variable.var_type === 'telemetry' ? 'bg-red-950/70 text-red-300 border border-red-800/60' : 'bg-purple-950/70 text-purple-300 border border-purple-800/60'}">
              ${variable.var_type === 'telemetry' ? 'Télémétrie' : 'Attribut / Contrôle'}
            </span>
            <span id="anomaly-badge-${variable.id}" class="hidden"></span>
          </div>
        </div>
        ${varActionsHtml}
      </div>

      <!-- Valeur courante & Unité -->
      <div class="mt-4 flex items-baseline justify-between">
        <div class="flex items-baseline gap-2">
          <span id="val-${variable.id}" class="text-3xl font-extrabold tracking-tight font-mono text-white">
            ${initialVal}
          </span>
          <span class="text-sm font-bold text-[#FF4D61]">${escapeHtml(variable.unit || '')}</span>
        </div>
        <div class="text-right">
          <span class="text-[10px] text-slate-400 font-mono block">
            ${variable.sim_mode === 'derived' ? '<span class="text-amber-400 font-bold" title="Formule: ' + escapeHtml(variable.derived_config?.formula || '') + '">ƒ(x) COUPLÉ</span>' : (variable.sim_mode === 'integrator' ? '<span class="text-emerald-400 font-bold" title="Source: ' + escapeHtml(variable.integrator_config?.source_variable_id || '') + '">∫ INTÉGRÉ</span>' : variable.sim_mode.toUpperCase())} &bull; ${variable.publish_interval}s
          </span>
          ${variable.sim_mode === 'derived' && variable.derived_config?.formula ? `<span class="text-[9px] text-amber-500/80 font-mono truncate max-w-[140px] block" title="${escapeHtml(variable.derived_config.formula)}">${escapeHtml(variable.derived_config.formula)}</span>` : ''}
          ${variable.sim_mode === 'integrator' && variable.integrator_config?.source_variable_id ? `<span class="text-[9px] text-emerald-500/80 font-mono truncate max-w-[140px] block" title="Source: ${escapeHtml(variable.integrator_config.source_variable_id)}">∫ ${escapeHtml(variable.integrator_config.source_variable_id)}</span>` : ''}
        </div>
      </div>

      <!-- Topic MQTT actif -->
      <div class="mt-2 text-[11px] font-mono text-slate-400 bg-[#0F1218] px-2.5 py-1.5 rounded-lg border border-[#2B3342] flex items-center justify-between">
        <span class="truncate flex items-center gap-1.5" title="${escapeHtml(variable.topic)}">
          <i data-lucide="corner-down-right" class="w-3.5 h-3.5 text-[#E2001A]"></i>
          <span id="topic-${variable.id}">${escapeHtml(variable.topic || 'v1/devices/me/telemetry')}</span>
        </span>
      </div>

      <!-- Sparkline Canvas -->
      ${variable.data_type === 'float' || variable.data_type === 'integer' ? `
        <div class="mt-3 h-14 w-full">
          <canvas id="chart-${variable.id}"></canvas>
        </div>
      ` : ''}
    </div>

    ${chaosActionsHtml}
  `;

  return card;
}

// Initialisation sparkline Chart.js sécurisée avec protection try/catch
function initSparkline(varId) {
  try {
    const ctx = document.getElementById(`chart-${varId}`);
    if (!ctx) return;

    if (typeof Chart === "undefined") {
      return; // Chart.js indisponible, pas de blocage du rendu
    }

    if (state.charts[varId]) {
      try {
        state.charts[varId].destroy();
      } catch (e) {}
      delete state.charts[varId];
    }

    state.chartData[varId] = state.chartData[varId] || [0];

    state.charts[varId] = new Chart(ctx, {
      type: "line",
      data: {
        labels: state.chartData[varId].map((_, i) => i),
        datasets: [{
          data: state.chartData[varId],
          borderColor: "#E2001A",
          borderWidth: 2,
          tension: 0.35,
          pointRadius: 0,
          fill: true,
          backgroundColor: "rgba(226, 0, 26, 0.12)",
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
  } catch (err) {
    console.warn(`Impossible d'initialiser le sparkline pour ${varId}:`, err);
  }
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
  const inputEl = document.getElementById(`manual-input-${varId}`);
  const val = inputEl ? inputEl.value : "";
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

// ==========================================
// GESTION DES ÉQUIPEMENTS (Création, Édition, Suppression)
// ==========================================

function openDeviceModal(devToEdit = null) {
  state.editingDevId = devToEdit ? devToEdit.id : null;
  const isEditEl = document.getElementById("dev-is-edit");
  if (isEditEl) isEditEl.value = devToEdit ? "true" : "false";
  
  const titleEl = document.getElementById("modal-device-title");
  if (titleEl) {
    titleEl.innerHTML = devToEdit ?
      `<i data-lucide="edit-3" class="w-5 h-5 text-[#E2001A]"></i> Modifier l'Équipement` :
      `<i data-lucide="cpu" class="w-5 h-5 text-[#E2001A]"></i> Nouvel Équipement`;
  }

  const idEl = document.getElementById("dev-id");
  const nameEl = document.getElementById("dev-name");
  const platformEl = document.getElementById("dev-platform");
  const protoEl = document.getElementById("dev-protocol");
  const tokenEl = document.getElementById("dev-token");
  const publishIntervalEl = document.getElementById("dev-publish-interval");
  const customHostEl = document.getElementById("dev-custom-host");
  const customPortEl = document.getElementById("dev-custom-port");
  const useTlsEl = document.getElementById("dev-use-tls");
  const enabledEl = document.getElementById("dev-enabled");

  if (devToEdit) {
    if (idEl) { idEl.value = devToEdit.id; idEl.disabled = true; }
    if (nameEl) nameEl.value = devToEdit.name;
    if (platformEl) platformEl.value = devToEdit.platform;
    if (protoEl) protoEl.value = devToEdit.protocol || "mqtt";
    if (tokenEl) tokenEl.value = devToEdit.token || "";
    if (publishIntervalEl) publishIntervalEl.value = devToEdit.publish_interval != null ? devToEdit.publish_interval : "";
    if (customHostEl) customHostEl.value = devToEdit.custom_host || "";
    if (customPortEl) customPortEl.value = devToEdit.custom_port || "";
    if (useTlsEl) useTlsEl.checked = devToEdit.use_tls === true;
    if (enabledEl) enabledEl.checked = devToEdit.enabled !== false;
  } else {
    if (idEl) { idEl.value = ""; idEl.disabled = false; }
    if (nameEl) nameEl.value = "";
    if (platformEl) platformEl.value = "thingsboard";
    if (protoEl) protoEl.value = "http"; // HTTP par défaut pour ThingsBoard (recommandé port 443 / Cloudflare)
    if (tokenEl) tokenEl.value = "";
    if (publishIntervalEl) publishIntervalEl.value = "";
    if (customHostEl) customHostEl.value = "";
    if (customPortEl) customPortEl.value = "";
    if (useTlsEl) useTlsEl.checked = true;
    if (enabledEl) enabledEl.checked = true;
  }

  onDevicePlatformChange();
  onDeviceProtocolChange();

  const testResultBox = document.getElementById("dev-test-result");
  if (testResultBox) {
    testResultBox.classList.add("hidden");
    testResultBox.innerHTML = "";
  }

  openModal("modal-device");
}

function onDevicePlatformChange() {
  const platform = document.getElementById("dev-platform").value;
  const protoContainer = document.getElementById("dev-protocol-container");
  if (protoContainer) {
    if (platform === "thingsboard") {
      protoContainer.classList.remove("hidden");
    } else {
      protoContainer.classList.add("hidden");
    }
  }
}

function onDeviceProtocolChange() {
  const proto = document.getElementById("dev-protocol") ? document.getElementById("dev-protocol").value : "mqtt";
  const hint = document.getElementById("dev-protocol-hint");
  const tlsEl = document.getElementById("dev-use-tls");
  if (proto === "http") {
    if (hint) hint.innerHTML = `<span class="text-emerald-400 font-semibold">Mode HTTP REST</span> : Envoi par requêtes HTTPS POST (port 443) directement vers l'API ThingsBoard (/api/v1/{token}/telemetry). <strong class="text-white">Idéal si votre ThingsBoard est derrière Cloudflare ou un reverse proxy bloquant le port 1883.</strong>`;
    if (tlsEl && !tlsEl.checked) tlsEl.checked = true;
  } else if (proto === "coap") {
    if (hint) hint.innerHTML = `<span class="text-purple-400 font-semibold">Mode CoAP UDP (RFC 7252)</span> : Trames légères sur port UDP 5683 sans overhead de session TCP.`;
  } else {
    if (hint) hint.innerHTML = `Mode MQTT standard : Session TCP persistante sur le broker (ports 1883, 8883 ou WebSockets).`;
  }
}

function toggleDeviceAdvancedNetwork() {
  const adv = document.getElementById("dev-network-advanced");
  const txt = document.getElementById("dev-advanced-toggle-text");
  if (adv) {
    adv.classList.toggle("hidden");
    if (txt) {
      txt.textContent = adv.classList.contains("hidden") ? "Afficher" : "Masquer";
    }
  }
}

async function testCurrentDeviceConfig() {
  const btn = document.getElementById("btn-test-dev");
  const label = document.getElementById("btn-test-dev-label");
  const resultBox = document.getElementById("dev-test-result");
  if (!resultBox) return;

  const customPortVal = document.getElementById("dev-custom-port").value;
  const payload = {
    id: document.getElementById("dev-id").value.trim() || "test_device",
    name: document.getElementById("dev-name").value.trim() || "Test",
    platform: document.getElementById("dev-platform").value,
    protocol: document.getElementById("dev-protocol") ? document.getElementById("dev-protocol").value : "mqtt",
    token: document.getElementById("dev-token").value.trim() || null,
    custom_host: document.getElementById("dev-custom-host").value.trim() || null,
    custom_port: customPortVal ? parseInt(customPortVal) : null,
    use_tls: document.getElementById("dev-use-tls").checked,
    enabled: true,
  };

  if (btn) btn.disabled = true;
  if (label) label.textContent = "Test en cours...";
  resultBox.classList.remove("hidden");
  resultBox.className = "p-2.5 rounded-lg text-xs border bg-[#12151B] border-[#2B3342] text-slate-300 flex items-center gap-2";
  resultBox.innerHTML = `<span class="animate-spin inline-block w-3.5 h-3.5 border-2 border-amber-400 border-t-transparent rounded-full"></span> <span>Test ${payload.protocol.toUpperCase()} vers ThingsBoard...</span>`;

  try {
    const res = await fetch("/api/devices/test-custom", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (btn) btn.disabled = false;
    if (label) label.textContent = "Tester la communication";

    let html = "";
    if (data.success) {
      resultBox.className = "p-2.5 rounded-lg text-xs border bg-emerald-950/40 border-emerald-700/60 text-emerald-200 space-y-1";
      html += `<div class="flex items-center gap-2 font-bold text-emerald-400">
        <i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i> Communication validée (${data.latency_ms || 0} ms)
      </div>`;
    } else {
      resultBox.className = "p-2.5 rounded-lg text-xs border bg-red-950/40 border-red-700/60 text-red-200 space-y-1";
      html += `<div class="flex items-center gap-2 font-bold text-[#E2001A]">
        <i data-lucide="alert-triangle" class="w-4 h-4 text-[#E2001A]"></i> Échec : ${escapeHtml(data.message || data.status_code || "Erreur de transmission")}
      </div>`;
    }

    if (data.recommendations && data.recommendations.length > 0) {
      html += `<ul class="list-disc list-inside text-[11px] text-slate-300 space-y-0.5 pt-1 border-t border-slate-700/50">
        ${data.recommendations.map(r => `<li>${escapeHtml(r)}</li>`).join("")}
      </ul>`;
    }

    resultBox.innerHTML = html;
    safeCreateIcons();
  } catch (err) {
    if (btn) btn.disabled = false;
    if (label) label.textContent = "Tester la communication";
    resultBox.className = "p-2.5 rounded-lg text-xs border bg-red-950/40 border-red-700/60 text-red-200";
    resultBox.innerHTML = `Erreur technique lors du test : ${escapeHtml(err.message)}`;
  }
}

async function testDeviceById(devId) {
  const dev = state.devices.find(d => d.id === devId);
  if (!dev) return;

  const btn = window.event?.currentTarget;
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full mr-1"></span><span>Test...</span>`;
  }

  try {
    const res = await fetch(`/api/devices/${devId}/test`, { method: "POST" });
    const data = await res.json();
    if (data.success) {
      alert(`✅ Communication validée pour "${dev.name}" !\n\nProtocole : ${(dev.protocol || 'mqtt').toUpperCase()}\nLatence : ${data.latency_ms || 0} ms\nStatut : ${data.message || data.status_code || 'OK'}`);
    } else {
      let recs = (data.recommendations || []).join("\n- ");
      alert(`❌ Échec de communication pour "${dev.name}"\n\nProtocole : ${(dev.protocol || 'mqtt').toUpperCase()}\nMessage : ${data.message || data.status_code || 'Inconnu'}\n\nRecommandations :\n- ${recs}`);
    }
  } catch (err) {
    alert(`Erreur technique : ${err.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<i data-lucide="activity" class="w-3.5 h-3.5 text-amber-400"></i><span>Tester</span>`;
      safeCreateIcons();
    }
  }
}

function editDevice(devId) {
  const dev = state.devices.find(d => d.id === devId);
  if (dev) {
    openDeviceModal(dev);
  }
}

async function deleteDevice(devId) {
  const dev = state.devices.find(d => d.id === devId);
  const name = dev ? dev.name : devId;
  const count = state.variables.filter(v => v.device_id === devId).length;

  const msg = `⚠️ Confirmez-vous la suppression de l'équipement "${name}" ?\n\nAttention : les ${count} variable(s) associées seront également supprimées.`;
  if (confirm(msg)) {
    await fetch(`/api/devices/${devId}`, { method: "DELETE" });
    if (state.activeFilter === devId) {
      state.activeFilter = "all";
    }
    await loadAllData();
  }
}

function downloadDeviceDashboard(deviceId) {
  window.location.href = `/api/devices/${encodeURIComponent(deviceId)}/thingsboard-dashboard`;
}

function downloadPresetDashboard(presetId) {
  window.location.href = `/api/presets/${encodeURIComponent(presetId)}/thingsboard-dashboard`;
}

// Sauvegarde de l'état des sections repliées dans localStorage
function saveCollapsedState() {
  try {
    localStorage.setItem("iot_sim_collapsed_devices", JSON.stringify([...state.collapsedDevices]));
  } catch (e) {
    console.warn("Erreur sauvegarde collapsedDevices dans localStorage:", e);
  }
}

// Basculer l'état plié/déplié d'un équipement
function toggleDeviceSection(deviceId, event) {
  if (event && event.target && event.target.closest("button, a, input, select, textarea")) {
    return;
  }
  if (state.collapsedDevices.has(deviceId)) {
    state.collapsedDevices.delete(deviceId);
  } else {
    state.collapsedDevices.add(deviceId);
  }
  saveCollapsedState();

  const section = document.getElementById(`device-section-${deviceId}`);
  if (section) {
    const isCollapsed = state.collapsedDevices.has(deviceId);
    const content = section.querySelector(`#vars-container-${deviceId}`);
    const chevron = section.querySelector(`.device-chevron-${deviceId}`);
    const summaryBadge = section.querySelector(`.device-collapsed-summary-${deviceId}`);

    if (content) {
      if (isCollapsed) {
        content.classList.add("hidden");
      } else {
        content.classList.remove("hidden");
      }
    }
    if (chevron) {
      chevron.setAttribute("data-lucide", isCollapsed ? "chevron-right" : "chevron-down");
    }
    if (summaryBadge) {
      if (isCollapsed) {
        summaryBadge.classList.remove("hidden");
      } else {
        summaryBadge.classList.add("hidden");
      }
    }
    safeCreateIcons();
  }
}

// Plier tous les équipements
function collapseAllDevices() {
  state.devices.forEach(d => state.collapsedDevices.add(d.id));
  saveCollapsedState();
  renderEquipmentGroups();
}

// Déplier tous les équipements
function expandAllDevices() {
  state.collapsedDevices.clear();
  saveCollapsedState();
  renderEquipmentGroups();
}

// Encodage Base64URL conforme RFC 7519
function base64UrlEncode(str) {
  return btoa(unescape(encodeURIComponent(str)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

// Générateur de token JWT ThingsBoard compatible (HS512 avec claims standard ThingsBoard)
function generateThingsBoardJwt(deviceId) {
  const dId = (deviceId && deviceId.trim()) ? deviceId.trim() : ("tb_dev_" + Math.random().toString(36).substring(2, 10));
  const header = {
    alg: "HS512",
    typ: "JWT"
  };
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    sub: dId,
    scopes: ["DEVICE"],
    userId: dId,
    enabled: true,
    isPublic: false,
    iss: "thingsboard.io",
    iat: now,
    exp: now + (10 * 365 * 86400) // Validité 10 ans
  };

  const encodedHeader = base64UrlEncode(JSON.stringify(header));
  const encodedPayload = base64UrlEncode(JSON.stringify(payload));
  // Signature factice HS512 (64 octets / 512 bits) encodée en base64url
  const randomBytes = new Uint8Array(64);
  (window.crypto || window.msCrypto).getRandomValues(randomBytes);
  const dummySignature = Array.from(randomBytes).map(b => String.fromCharCode(b)).join('');
  const encodedSignature = base64UrlEncode(dummySignature);

  return `${encodedHeader}.${encodedPayload}.${encodedSignature}`;
}

// Remplissage automatique du champ token avec le JWT ThingsBoard généré
function fillGeneratedJwtToken(targetInputId, deviceIdInputId) {
  const devIdEl = document.getElementById(deviceIdInputId);
  const targetEl = document.getElementById(targetInputId);
  if (!targetEl) return;
  const devId = devIdEl ? devIdEl.value : "";
  const token = generateThingsBoardJwt(devId);
  targetEl.value = token;

  // Feedback visuel élégant sur le champ modifié
  targetEl.classList.add("ring-2", "ring-emerald-500", "border-emerald-500");
  setTimeout(() => {
    targetEl.classList.remove("ring-2", "ring-emerald-500", "border-emerald-500");
  }, 1500);
}

// Échappement de valeur CSV avec encadrement guillemets
function escapeCsvValue(val) {
  if (val === null || val === undefined) return '""';
  const str = String(val).replace(/"/g, '""');
  return `"${str}"`;
}

// Téléchargement du fichier CSV d'import ThingsBoard pour un équipement donné
function downloadDeviceCsv(deviceId) {
  const device = state.devices.find(d => d.id === deviceId);
  if (!device) return;
  const header = "name,type,label,access_token";
  const row = [
    escapeCsvValue(device.name),
    escapeCsvValue("default"),
    escapeCsvValue(device.id),
    escapeCsvValue(device.token || "")
  ].join(",");

  const csvContent = header + "\r\n" + row + "\r\n";
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `tb_device_${device.id}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Téléchargement du fichier CSV d'import ThingsBoard pour l'ensemble des équipements
function exportAllDevicesCsv() {
  if (!state.devices || state.devices.length === 0) {
    alert("Aucun équipement à exporter.");
    return;
  }
  const header = "name,type,label,access_token";
  const rows = state.devices.map(device => [
    escapeCsvValue(device.name),
    escapeCsvValue("default"),
    escapeCsvValue(device.id),
    escapeCsvValue(device.token || "")
  ].join(","));

  const csvContent = [header, ...rows].join("\r\n") + "\r\n";
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `thingsboard_devices_all_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function saveDeviceForm(e) {
  e.preventDefault();
  const customPortVal = document.getElementById("dev-custom-port").value;
  const publishIntervalRaw = document.getElementById("dev-publish-interval") ? document.getElementById("dev-publish-interval").value.trim() : "";
  const devPayload = {
    id: document.getElementById("dev-id").value.trim(),
    name: document.getElementById("dev-name").value.trim(),
    platform: document.getElementById("dev-platform").value,
    protocol: document.getElementById("dev-protocol") ? document.getElementById("dev-protocol").value : "mqtt",
    token: document.getElementById("dev-token").value.trim() || null,
    custom_host: document.getElementById("dev-custom-host").value.trim() || null,
    custom_port: customPortVal ? parseInt(customPortVal) : null,
    use_tls: document.getElementById("dev-use-tls").checked,
    publish_interval: publishIntervalRaw ? parseFloat(publishIntervalRaw) : null,
    enabled: document.getElementById("dev-enabled").checked,
  };

  await fetch("/api/devices", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(devPayload)
  });

  closeModal("modal-device");
  await loadAllData();
}

// ==========================================
// GESTION DES VARIABLES
// ==========================================

function openVariableModalForDevice(deviceId) {
  openVariableModal(null, deviceId);
}

function openVariableModal(varToEdit = null, preselectedDeviceId = null) {
  state.editingVarId = varToEdit ? varToEdit.id : null;
  const isEditEl = document.getElementById("var-is-edit");
  if (isEditEl) isEditEl.value = varToEdit ? "true" : "false";

  const titleEl = document.getElementById("modal-variable-title");
  if (titleEl) {
    titleEl.innerHTML = varToEdit ?
      `<i data-lucide="edit-2" class="w-5 h-5 text-[#E2001A]"></i> Modifier la Variable` :
      `<i data-lucide="sliders" class="w-5 h-5 text-[#E2001A]"></i> Nouvelle Variable`;
  }

  const devSelect = document.getElementById("var-device-id");
  if (devSelect) {
    devSelect.innerHTML = "";
    state.devices.forEach(d => {
      const opt = document.createElement("option");
      opt.value = d.id;
      opt.textContent = `${d.name} (${d.platform})`;
      devSelect.appendChild(opt);
    });
  }

  const idEl = document.getElementById("var-id");
  const nameEl = document.getElementById("var-name");
  const unitEl = document.getElementById("var-unit");
  const topicEl = document.getElementById("var-topic");
  const intervalEl = document.getElementById("var-interval");
  const modeEl = document.getElementById("var-sim-mode");

  if (varToEdit) {
    if (idEl) { idEl.value = varToEdit.id; idEl.disabled = true; }
    if (nameEl) nameEl.value = varToEdit.name;
    if (devSelect) devSelect.value = varToEdit.device_id;
    document.getElementById("var-data-type").value = varToEdit.data_type;
    document.getElementById("var-type").value = varToEdit.var_type;
    if (unitEl) unitEl.value = varToEdit.unit || "";
    if (intervalEl) intervalEl.value = varToEdit.publish_interval;
    if (topicEl) topicEl.value = varToEdit.topic || "";
    if (modeEl) modeEl.value = varToEdit.sim_mode;

    document.getElementById("math-min").value = varToEdit.math_config.min_val;
    document.getElementById("math-max").value = varToEdit.math_config.max_val;
    document.getElementById("math-period").value = varToEdit.math_config.period;
    document.getElementById("math-noise").value = varToEdit.math_config.noise_percent;
    document.getElementById("math-constant").value = varToEdit.math_config.constant_val;

    const formulaInput = document.getElementById("derived-formula");
    if (formulaInput) formulaInput.value = varToEdit.derived_config?.formula || "";

    const intSourceSelect = document.getElementById("integrator-source-var");
    if (intSourceSelect && varToEdit.integrator_config?.source_variable_id) {
      intSourceSelect.value = varToEdit.integrator_config.source_variable_id;
    }
    const timeUnitSelect = document.getElementById("integrator-time-unit");
    if (timeUnitSelect) timeUnitSelect.value = varToEdit.integrator_config?.time_unit || "hour";
    const multInput = document.getElementById("integrator-multiplier");
    if (multInput) multInput.value = varToEdit.integrator_config?.multiplier ?? 1.0;
    const initValInput = document.getElementById("integrator-initial-val");
    if (initValInput) initValInput.value = varToEdit.integrator_config?.initial_value ?? 0.0;

    renderPointsTable(varToEdit.points_config ? varToEdit.points_config.points : []);
  } else {
    if (idEl) { idEl.value = ""; idEl.disabled = false; }
    if (nameEl) nameEl.value = "";
    if (devSelect && preselectedDeviceId) {
      devSelect.value = preselectedDeviceId;
    }
    if (unitEl) unitEl.value = "";
    if (topicEl) topicEl.value = "";
    
    // Cadence par défaut héritée de l'équipement si configurée, sinon 3.0s
    const activeDevId = (devSelect && devSelect.value) || preselectedDeviceId;
    const parentDev = state.devices.find(d => d.id === activeDevId);
    if (intervalEl) {
      intervalEl.value = (parentDev && parentDev.publish_interval != null && parentDev.publish_interval > 0)
        ? parentDev.publish_interval
        : "3.0";
    }
    if (modeEl) modeEl.value = "sine";

    const formulaInput = document.getElementById("derived-formula");
    if (formulaInput) formulaInput.value = "";
    const timeUnitSelect = document.getElementById("integrator-time-unit");
    if (timeUnitSelect) timeUnitSelect.value = "hour";
    const multInput = document.getElementById("integrator-multiplier");
    if (multInput) multInput.value = "1.0";
    const initValInput = document.getElementById("integrator-initial-val");
    if (initValInput) initValInput.value = "0.0";

    renderPointsTable([]);
  }

  // Peuplement des aides contextuelles pour formules et intégrateurs
  const targetDevId = varToEdit ? varToEdit.device_id : (devSelect ? devSelect.value : "");
  const devVars = state.variables.filter(v => v.device_id === targetDevId && (!varToEdit || v.id !== varToEdit.id));
  
  const chipsContainer = document.getElementById("derived-variables-chips");
  if (chipsContainer) {
    if (devVars.length === 0) {
      chipsContainer.innerHTML = '<span class="text-slate-500 text-[10px]">Aucune autre variable disponible sur cet équipement</span>';
    } else {
      chipsContainer.innerHTML = devVars.map(v => 
        `<button type="button" onclick="insertFormulaVariable('${escapeHtml(v.id)}')" class="px-2 py-0.5 rounded bg-[#181D26] hover:bg-[#2B3342] border border-[#2B3342] text-[10px] text-amber-300 font-mono transition" title="${escapeHtml(v.name)}">${escapeHtml(v.id)}</button>`
      ).join("");
    }
  }

  const intSourceSelect = document.getElementById("integrator-source-var");
  if (intSourceSelect) {
    intSourceSelect.innerHTML = "";
    devVars.forEach(v => {
      const opt = document.createElement("option");
      opt.value = v.id;
      opt.textContent = `${v.name} (${v.id})${v.unit ? ' [' + v.unit + ']' : ''}`;
      intSourceSelect.appendChild(opt);
    });
    if (varToEdit && varToEdit.integrator_config?.source_variable_id) {
      intSourceSelect.value = varToEdit.integrator_config.source_variable_id;
    }
  }

  toggleSimModeSections();
  openModal("modal-variable");
}

function toggleSimModeSections() {
  const mode = document.getElementById("var-sim-mode").value;
  const mathSec = document.getElementById("section-math-params");
  const pointsSec = document.getElementById("section-points-params");
  const derivedSec = document.getElementById("section-derived-params");
  const intSec = document.getElementById("section-integrator-params");
  const constWrap = document.getElementById("constant-val-wrapper");

  if (mathSec) mathSec.classList.add("hidden");
  if (pointsSec) pointsSec.classList.add("hidden");
  if (derivedSec) derivedSec.classList.add("hidden");
  if (intSec) intSec.classList.add("hidden");

  if (mode === "points_table") {
    if (pointsSec) pointsSec.classList.remove("hidden");
  } else if (mode === "derived") {
    if (derivedSec) derivedSec.classList.remove("hidden");
  } else if (mode === "integrator") {
    if (intSec) intSec.classList.remove("hidden");
  } else {
    if (mathSec) mathSec.classList.remove("hidden");
    if (mode === "constant") {
      if (constWrap) constWrap.classList.remove("hidden");
    } else {
      if (constWrap) constWrap.classList.add("hidden");
    }
  }
}

function insertFormulaVariable(varId) {
  const input = document.getElementById("derived-formula");
  if (!input) return;
  input.value = input.value ? `${input.value} * ${varId}` : varId;
  input.focus();
}

function renderPointsTable(points) {
  const tbody = document.getElementById("points-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";
  if (!points || points.length === 0) {
    addPointRow(0, 0);
    return;
  }
  points.forEach(p => addPointRow(p.offset_seconds, p.value));
}

function addPointRow(offset = 0, val = 0) {
  const tbody = document.getElementById("points-table-body");
  if (!tbody) return;
  const tr = document.createElement("tr");
  tr.className = "hover:bg-[#181D26]";
  tr.innerHTML = `
    <td class="p-2"><input type="number" step="any" value="${offset}" class="point-offset w-24 bg-[#181D26] border border-[#2B3342] rounded px-2 py-1 text-slate-100"></td>
    <td class="p-2"><input type="text" value="${val}" class="point-value w-full bg-[#181D26] border border-[#2B3342] rounded px-2 py-1 text-slate-100"></td>
    <td class="p-2 text-right"><button type="button" onclick="this.closest('tr').remove()" class="text-rose-400 hover:text-rose-300"><i data-lucide="trash" class="w-4 h-4"></i></button></td>
  `;
  tbody.appendChild(tr);
  safeCreateIcons();
}

async function saveVariableForm(e) {
  e.preventDefault();
  const simMode = document.getElementById("var-sim-mode").value;

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
    derived_config: {
      formula: document.getElementById("derived-formula") ? document.getElementById("derived-formula").value.trim() : "",
    },
    integrator_config: {
      source_variable_id: document.getElementById("integrator-source-var") ? document.getElementById("integrator-source-var").value : "",
      time_unit: document.getElementById("integrator-time-unit") ? document.getElementById("integrator-time-unit").value : "hour",
      multiplier: parseFloat(document.getElementById("integrator-multiplier")?.value) || 1.0,
      initial_value: parseFloat(document.getElementById("integrator-initial-val")?.value) || 0.0,
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

// Modal Broker MQTT
function openBrokerModal() {
  document.getElementById("broker-host").value = state.broker.host || "mosquitto";
  document.getElementById("broker-port").value = state.broker.port || 1883;
  
  const transportEl = document.getElementById("broker-transport");
  if (transportEl) transportEl.value = state.broker.transport || "tcp";
  
  const wsPathEl = document.getElementById("broker-ws-path");
  if (wsPathEl) wsPathEl.value = state.broker.ws_path || "/mqtt";
  
  document.getElementById("broker-tls").checked = state.broker.use_tls || false;
  document.getElementById("broker-user").value = state.broker.username || "";
  document.getElementById("broker-pass").value = state.broker.password || "";

  toggleTransportFields();

  const testResultBox = document.getElementById("broker-test-result");
  if (testResultBox) {
    testResultBox.classList.add("hidden");
    testResultBox.innerHTML = "";
  }

  openModal("modal-broker");
}

function toggleTransportFields() {
  const transportEl = document.getElementById("broker-transport");
  const wsContainer = document.getElementById("ws-path-container");
  if (transportEl && wsContainer) {
    if (transportEl.value === "websockets") {
      wsContainer.classList.remove("hidden");
    } else {
      wsContainer.classList.add("hidden");
    }
  }
}

async function saveBrokerForm(e) {
  e.preventDefault();
  const brokerPayload = {
    host: document.getElementById("broker-host").value.trim(),
    port: parseInt(document.getElementById("broker-port").value),
    transport: document.getElementById("broker-transport") ? document.getElementById("broker-transport").value : "tcp",
    ws_path: document.getElementById("broker-ws-path") ? document.getElementById("broker-ws-path").value.trim() : "/mqtt",
    use_tls: document.getElementById("broker-tls").checked,
    username: document.getElementById("broker-user").value.trim() || null,
    password: document.getElementById("broker-pass").value.trim() || null,
  };

  try {
    const res = await fetch("/api/broker", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(brokerPayload)
    });
    if (res.ok) {
      state.broker = await res.json();
    }
  } catch (err) {
    console.error("Erreur enregistrement broker:", err);
  }

  closeModal("modal-broker");
  await refreshStatus();
}

async function testBrokerConfig() {
  const btn = document.getElementById("btn-test-broker");
  const label = document.getElementById("btn-test-broker-label");
  const resultBox = document.getElementById("broker-test-result");
  if (!resultBox) return;

  const payload = {
    host: document.getElementById("broker-host").value.trim(),
    port: parseInt(document.getElementById("broker-port").value) || 1883,
    transport: document.getElementById("broker-transport") ? document.getElementById("broker-transport").value : "tcp",
    ws_path: document.getElementById("broker-ws-path") ? document.getElementById("broker-ws-path").value.trim() : "/mqtt",
    use_tls: document.getElementById("broker-tls").checked,
    username: document.getElementById("broker-user").value.trim() || null,
    password: document.getElementById("broker-pass").value.trim() || null,
  };

  if (btn) btn.disabled = true;
  if (label) label.textContent = "Test en cours...";
  resultBox.classList.remove("hidden");
  resultBox.className = "p-3 rounded-lg text-xs border bg-[#12151B] border-[#2B3342] text-slate-300 flex items-center gap-2";
  resultBox.innerHTML = `<span class="animate-spin inline-block w-3.5 h-3.5 border-2 border-amber-400 border-t-transparent rounded-full"></span> <span>Analyse de connectivité vers ${escapeHtml(payload.host)}:${payload.port}...</span>`;

  try {
    const res = await fetch("/api/broker/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (btn) btn.disabled = false;
    if (label) label.textContent = "Tester la connectivité";

    let html = "";
    if (data.success) {
      resultBox.className = "p-3 rounded-lg text-xs border bg-emerald-950/40 border-emerald-700/60 text-emerald-200 space-y-1.5";
      html += `<div class="flex items-center gap-2 font-bold text-emerald-400">
        <i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i> Connexion réussie (${data.latency_ms} ms)
      </div>`;
    } else {
      resultBox.className = "p-3 rounded-lg text-xs border bg-red-950/40 border-red-700/60 text-red-200 space-y-1.5";
      html += `<div class="flex items-center gap-2 font-bold text-[#E2001A]">
        <i data-lucide="alert-triangle" class="w-4 h-4 text-[#E2001A]"></i> Échec du test : ${escapeHtml(data.message)}
      </div>`;
    }

    if (data.details) {
      html += `<div class="text-[11px] text-slate-300 font-mono space-y-0.5 pt-1 border-t border-slate-700/50">`;
      if (data.details.resolved_ip) {
        html += `<div>IP résolue: <span class="text-white">${escapeHtml(data.details.resolved_ip)}</span></div>`;
      }
      if (data.details.is_cloudflare) {
        html += `<div class="text-amber-400 font-semibold flex items-center gap-1.5 mt-1">
          <i data-lucide="shield-alert" class="w-3.5 h-3.5 shrink-0 text-amber-400"></i>
          <span>Reverse Proxy Cloudflare CDN détecté ! Les flux TCP bruts (ports 1883/8883) sont généralement bloqués par le proxy CDN.</span>
        </div>`;
      }
      if (data.details.error) {
        html += `<div class="text-red-400">Détail technique: ${escapeHtml(data.details.error)}</div>`;
      }
      html += `</div>`;
    }

    if (data.recommendations && data.recommendations.length > 0) {
      html += `<div class="pt-1.5 border-t border-slate-700/50">
        <span class="font-semibold text-slate-200">Recommandations :</span>
        <ul class="list-disc list-inside text-[11px] text-slate-300 space-y-0.5 mt-1">
          ${data.recommendations.map(r => `<li>${escapeHtml(r)}</li>`).join("")}
        </ul>
      </div>`;
    }

    resultBox.innerHTML = html;
    safeCreateIcons();
  } catch (err) {
    if (btn) btn.disabled = false;
    if (label) label.textContent = "Tester la connectivité";
    resultBox.className = "p-3 rounded-lg text-xs border bg-red-950/40 border-red-700/60 text-red-200";
    resultBox.innerHTML = `<span class="font-bold">Erreur de communication :</span> Impossible d'exécuter le test (${escapeHtml(err.message)})`;
  }
}

// -------------------------------------------------------------
// Module Gestion Console de Logs & Diagnostics
// -------------------------------------------------------------
const logState = {
  logs: [],
  activeFilter: 'ALL',
  unreadErrors: 0,
};

function handleLiveLog(logEntry) {
  logState.logs.push(logEntry);
  if (logState.logs.length > 300) {
    logState.logs.shift();
  }

  if (logEntry.level === "ERROR") {
    logState.unreadErrors++;
    updateErrorBadge();
  }

  const modalLogs = document.getElementById("modal-logs");
  const terminal = document.getElementById("log-terminal");
  if (modalLogs && terminal && !modalLogs.classList.contains("hidden")) {
    if (logState.activeFilter === "ALL" || logEntry.level === logState.activeFilter) {
      if (terminal.querySelector(".italic")) {
        terminal.innerHTML = "";
      }
      const wrapper = document.createElement("div");
      wrapper.innerHTML = formatLogLineHtml(logEntry);
      terminal.appendChild(wrapper.firstElementChild);

      const autoscroll = document.getElementById("log-autoscroll");
      if (autoscroll && autoscroll.checked) {
        terminal.scrollTop = terminal.scrollHeight;
      }
      updateLogCountBadge();
    }
  }
}

function updateErrorBadge() {
  const badge = document.getElementById("log-error-badge");
  if (!badge) return;
  if (logState.unreadErrors > 0) {
    badge.textContent = logState.unreadErrors > 99 ? "99+" : logState.unreadErrors;
    badge.classList.remove("hidden");
  } else {
    badge.classList.add("hidden");
  }
}

function updateLogCountBadge() {
  const badge = document.getElementById("log-count-badge");
  if (badge) {
    badge.textContent = `${logState.logs.length} ligne(s)`;
  }
}

function formatLogLineHtml(log) {
  let levelClass = "text-slate-400 bg-slate-800 border-slate-700";
  if (log.level === "ERROR") {
    levelClass = "text-red-400 bg-red-950/80 border-red-700/60";
  } else if (log.level === "WARNING") {
    levelClass = "text-amber-400 bg-amber-950/80 border-amber-700/60";
  } else if (log.level === "INFO") {
    levelClass = "text-sky-400 bg-sky-950/80 border-sky-700/60";
  }

  const timeStr = log.timestamp ? (log.timestamp.includes("T") ? log.timestamp.split("T")[1].slice(0, 8) : log.timestamp) : "";

  return `<div class="flex items-start gap-2 py-0.5 hover:bg-white/5 rounded px-1 transition text-[11px] leading-relaxed">
    <span class="text-slate-500 font-mono shrink-0 select-none">${escapeHtml(timeStr)}</span>
    <span class="px-1.5 py-0.2 text-[10px] font-bold rounded border ${levelClass} shrink-0 select-none">${escapeHtml(log.level)}</span>
    <span class="text-slate-400 font-mono shrink-0 select-none">[${escapeHtml(log.name)}]</span>
    <span class="text-slate-200 break-all">${escapeHtml(log.message)}</span>
  </div>`;
}

function renderLogsTerminal() {
  const terminal = document.getElementById("log-terminal");
  if (!terminal) return;

  const filtered = logState.logs.filter(l => {
    if (logState.activeFilter === "ALL") return true;
    return l.level === logState.activeFilter;
  });

  if (filtered.length === 0) {
    terminal.innerHTML = `<div class="text-slate-500 italic text-[11px]">Aucun journal d'événement disponible pour ce filtre.</div>`;
    updateLogCountBadge();
    return;
  }

  terminal.innerHTML = filtered.map(l => formatLogLineHtml(l)).join("");
  updateLogCountBadge();

  const autoscroll = document.getElementById("log-autoscroll");
  if (autoscroll && autoscroll.checked) {
    terminal.scrollTop = terminal.scrollHeight;
  }
}

async function openLogsModal() {
  logState.unreadErrors = 0;
  updateErrorBadge();
  openModal("modal-logs");
  await fetchLogs();
}

async function fetchLogs() {
  try {
    const res = await fetch("/api/logs?limit=200");
    if (res.ok) {
      logState.logs = await res.json();
      renderLogsTerminal();
    }
  } catch (err) {
    console.error("Erreur récupération logs:", err);
  }
}

async function clearLogs() {
  try {
    await fetch("/api/logs", { method: "DELETE" });
    logState.logs = [];
    logState.unreadErrors = 0;
    updateErrorBadge();
    renderLogsTerminal();
  } catch (err) {
    console.error("Erreur suppression logs:", err);
  }
}

function setLogLevelFilter(level) {
  logState.activeFilter = level;
  ['ALL', 'INFO', 'WARNING', 'ERROR'].forEach(lvl => {
    const btn = document.getElementById(`log-filter-${lvl}`);
    if (btn) {
      if (lvl === level) {
        btn.className = "px-2 py-1 rounded text-[11px] font-semibold bg-[#202531] text-white";
      } else {
        btn.className = "px-2 py-1 rounded text-[11px] font-semibold text-slate-400 hover:text-white";
      }
    }
  });
  renderLogsTerminal();
}

function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("hidden");
  safeCreateIcons();
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("hidden");
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

// =============================================================
// MODULE GESTION DES UTILISATEURS & AUTHENTIFICATION (RBAC / CIS)
// =============================================================

async function checkAuthStatus() {
  try {
    const res = await fetch("/api/auth/me");
    if (res.ok) {
      state.currentUser = await res.json();
      updateUserSessionUI();
      closeModal("modal-login");
      return true;
    } else {
      state.currentUser = null;
      openModal("modal-login");
      return false;
    }
  } catch (err) {
    state.currentUser = null;
    openModal("modal-login");
    return false;
  }
}

function updateUserSessionUI() {
  if (!state.currentUser) return;
  const nameEl = document.getElementById("user-display-name");
  const roleEl = document.getElementById("user-display-role");
  const adminBtn = document.getElementById("btn-admin-users");
  const brokerBtn = document.getElementById("btn-broker-settings");
  const importLabel = document.getElementById("lbl-import-scenario");
  const newDevBtn = document.getElementById("btn-new-device");
  const catalogBtn = document.getElementById("btn-catalog");
  const engineBtn = document.getElementById("btn-toggle-engine");

  if (nameEl) nameEl.textContent = state.currentUser.full_name || state.currentUser.username;
  if (roleEl) {
    const r = (state.currentUser.role || "viewer").toUpperCase();
    roleEl.textContent = r;
    if (r === "ADMIN") {
      roleEl.className = "px-1.5 py-0.2 text-[10px] font-bold rounded bg-red-950 text-red-300 border border-red-800";
    } else if (r === "OPERATOR") {
      roleEl.className = "px-1.5 py-0.2 text-[10px] font-bold rounded bg-sky-950 text-sky-300 border border-sky-800";
    } else {
      roleEl.className = "px-1.5 py-0.2 text-[10px] font-bold rounded bg-slate-800 text-slate-300 border border-slate-700";
    }
  }

  const isAdmin = state.currentUser.role === "admin";
  const canOperate = state.currentUser.role === "admin" || state.currentUser.role === "operator";

  if (adminBtn) {
    if (isAdmin) adminBtn.classList.remove("hidden");
    else adminBtn.classList.add("hidden");
  }

  if (brokerBtn) {
    if (isAdmin) brokerBtn.classList.remove("hidden");
    else brokerBtn.classList.add("hidden");
  }

  if (importLabel) {
    if (canOperate) importLabel.classList.remove("hidden");
    else importLabel.classList.add("hidden");
  }

  if (newDevBtn) {
    if (canOperate) newDevBtn.classList.remove("hidden");
    else newDevBtn.classList.add("hidden");
  }

  if (catalogBtn) {
    if (canOperate) catalogBtn.classList.remove("hidden");
    else catalogBtn.classList.add("hidden");
  }

  if (engineBtn) {
    if (canOperate) {
      engineBtn.disabled = false;
      engineBtn.classList.remove("opacity-50", "cursor-not-allowed");
    } else {
      engineBtn.disabled = true;
      engineBtn.classList.add("opacity-50", "cursor-not-allowed");
      engineBtn.title = "Action réservée aux opérateurs et administrateurs";
    }
  }
}

async function submitLogin(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-login-submit");
  const label = document.getElementById("btn-login-label");
  const errBox = document.getElementById("login-error");

  const username = document.getElementById("login-username").value.trim();
  const password = document.getElementById("login-password").value;

  if (btn) btn.disabled = true;
  if (label) label.textContent = "Connexion en cours...";
  if (errBox) errBox.classList.add("hidden");

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    if (btn) btn.disabled = false;
    if (label) label.textContent = "Se Connecter";

    if (!res.ok) {
      if (errBox) {
        errBox.textContent = data.detail || "Identifiant ou mot de passe incorrect.";
        errBox.classList.remove("hidden");
      }
      return;
    }

    state.currentUser = data.user;
    updateUserSessionUI();
    closeModal("modal-login");

    // Chargement initial des données et ouverture du WebSocket
    await loadAllData();
    setupWebSocket();

    if (statusInterval) clearInterval(statusInterval);
    statusInterval = setInterval(refreshStatus, 3000);

    // Alerte si mot de passe par défaut
    if (data.user.must_change_password) {
      alert("⚠️ Sécurité : Vous utilisez le mot de passe initial par défaut. Veuillez le modifier via le menu de votre profil.");
    }
  } catch (err) {
    if (btn) btn.disabled = false;
    if (label) label.textContent = "Se Connecter";
    if (errBox) {
      errBox.textContent = `Erreur réseau : ${err.message}`;
      errBox.classList.remove("hidden");
    }
  }
}

async function logout() {
  if (confirm("Confirmez-vous votre déconnexion ?")) {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch (e) {
      console.warn("Erreur logout:", e);
    }
    if (ws) {
      ws.close();
      ws = null;
    }
    if (statusInterval) {
      clearInterval(statusInterval);
      statusInterval = null;
    }
    state.currentUser = null;
    openModal("modal-login");
  }
}

// -------------------------------------------------------------
// Gestion des Utilisateurs (Admin Only)
// -------------------------------------------------------------

async function openUsersModal() {
  openModal("modal-users");
  await fetchUsersList();
}

async function fetchUsersList() {
  const tbody = document.getElementById("users-table-body");
  const countEl = document.getElementById("users-count");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-slate-500 italic">Chargement des utilisateurs...</td></tr>`;

  try {
    const res = await fetch("/api/users");
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-red-400">Erreur lors de la récupération des utilisateurs.</td></tr>`;
      return;
    }

    const users = await res.json();
    if (countEl) countEl.textContent = users.length;

    if (users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-slate-500 italic">Aucun utilisateur trouvé.</td></tr>`;
      return;
    }

    tbody.innerHTML = users.map(u => {
      let roleBadge = "";
      if (u.role === "admin") {
        roleBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-950 text-red-300 border border-red-800">ADMIN</span>`;
      } else if (u.role === "operator") {
        roleBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-950 text-sky-300 border border-sky-800">OPERATOR</span>`;
      } else {
        roleBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">VIEWER</span>`;
      }

      const isSelf = state.currentUser && state.currentUser.username === u.username;
      const lastLoginStr = u.last_login ? u.last_login.replace("T", " ").slice(0, 19) : "Jamais";

      return `
        <tr class="hover:bg-white/5 transition">
          <td class="p-3 font-semibold text-white flex items-center gap-1.5">
            <i data-lucide="user" class="w-3.5 h-3.5 text-slate-500"></i>
            <span>${escapeHtml(u.username)}</span>
            ${isSelf ? '<span class="text-[9px] bg-slate-800 text-slate-400 px-1 rounded">vous</span>' : ''}
          </td>
          <td class="p-3 text-slate-300 font-sans">${escapeHtml(u.full_name)}</td>
          <td class="p-3">${roleBadge}</td>
          <td class="p-3 text-slate-400 text-[10px]">${escapeHtml(lastLoginStr)}</td>
          <td class="p-3 text-right space-x-1">
            <button onclick="openResetPasswordModal('${escapeHtml(u.username)}')" title="Réinitialiser le mot de passe" class="p-1.5 rounded bg-[#202531] hover:bg-[#2B3342] text-amber-300 transition inline-flex items-center">
              <i data-lucide="key" class="w-3.5 h-3.5"></i>
            </button>
            ${!isSelf ? `
              <button onclick="deleteUser('${escapeHtml(u.username)}')" title="Supprimer cet utilisateur" class="p-1.5 rounded bg-[#202531] hover:bg-rose-950/60 text-rose-400 transition inline-flex items-center">
                <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
              </button>
            ` : ''}
          </td>
        </tr>
      `;
    }).join("");

    safeCreateIcons();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-red-400">Erreur technique : ${escapeHtml(err.message)}</td></tr>`;
  }
}

function openCreateUserModal() {
  document.getElementById("create-username").value = "";
  document.getElementById("create-fullname").value = "";
  document.getElementById("create-role").value = "operator";
  document.getElementById("create-password").value = "";
  const errBox = document.getElementById("create-user-error");
  if (errBox) errBox.classList.add("hidden");
  openModal("modal-create-user");
}

async function submitCreateUser(e) {
  e.preventDefault();
  const errBox = document.getElementById("create-user-error");
  if (errBox) errBox.classList.add("hidden");

  const payload = {
    username: document.getElementById("create-username").value.trim().toLowerCase(),
    full_name: document.getElementById("create-fullname").value.trim(),
    role: document.getElementById("create-role").value,
    password: document.getElementById("create-password").value,
  };

  try {
    const res = await fetch("/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) {
      if (errBox) {
        errBox.textContent = data.detail || "Erreur de validation lors de la création.";
        errBox.classList.remove("hidden");
      }
      return;
    }

    closeModal("modal-create-user");
    await fetchUsersList();
    alert(`✅ Utilisateur "${payload.username}" créé avec succès !`);
  } catch (err) {
    if (errBox) {
      errBox.textContent = `Erreur réseau : ${err.message}`;
      errBox.classList.remove("hidden");
    }
  }
}

async function deleteUser(username) {
  if (confirm(`Confirmez-vous la suppression définitive du compte "${username}" ?`)) {
    try {
      const res = await fetch(`/api/users/${username}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) {
        alert(`❌ Erreur : ${data.detail || 'Impossible de supprimer cet utilisateur'}`);
        return;
      }
      await fetchUsersList();
    } catch (err) {
      alert(`Erreur technique : ${err.message}`);
    }
  }
}

function openResetPasswordModal(username) {
  document.getElementById("reset-target-username").value = username;
  document.getElementById("reset-target-display").textContent = username;
  document.getElementById("reset-new-password").value = "";
  const errBox = document.getElementById("reset-pw-error");
  if (errBox) errBox.classList.add("hidden");
  openModal("modal-reset-password");
}

async function submitResetPassword(e) {
  e.preventDefault();
  const username = document.getElementById("reset-target-username").value;
  const newPassword = document.getElementById("reset-new-password").value;
  const errBox = document.getElementById("reset-pw-error");

  try {
    const res = await fetch(`/api/users/${username}/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_password: newPassword })
    });
    const data = await res.json();
    if (!res.ok) {
      if (errBox) {
        errBox.textContent = data.detail || "Erreur lors de la réinitialisation.";
        errBox.classList.remove("hidden");
      }
      return;
    }
    closeModal("modal-reset-password");
    alert(`✅ Mot de passe réinitialisé pour "${username}".`);
  } catch (err) {
    if (errBox) {
      errBox.textContent = `Erreur : ${err.message}`;
      errBox.classList.remove("hidden");
    }
  }
}

function openChangePasswordModal() {
  document.getElementById("pw-current").value = "";
  document.getElementById("pw-new").value = "";
  document.getElementById("pw-confirm").value = "";
  const errBox = document.getElementById("change-pw-error");
  if (errBox) errBox.classList.add("hidden");
  openModal("modal-change-password");
}

async function submitChangePassword(e) {
  e.preventDefault();
  const currentPassword = document.getElementById("pw-current").value;
  const newPassword = document.getElementById("pw-new").value;
  const confirmPassword = document.getElementById("pw-confirm").value;
  const errBox = document.getElementById("change-pw-error");

  if (newPassword !== confirmPassword) {
    if (errBox) {
      errBox.textContent = "Le nouveau mot de passe et sa confirmation ne correspondent pas.";
      errBox.classList.remove("hidden");
    }
    return;
  }

  try {
    const res = await fetch("/api/auth/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
    });
    const data = await res.json();
    if (!res.ok) {
      if (errBox) {
        errBox.textContent = data.detail || "Erreur lors de la modification.";
        errBox.classList.remove("hidden");
      }
      return;
    }
    closeModal("modal-change-password");
    alert("✅ Votre mot de passe a été mis à jour avec succès !");
  } catch (err) {
    if (errBox) {
      errBox.textContent = `Erreur : ${err.message}`;
      errBox.classList.remove("hidden");
    }
  }
}

// =========================================================================
// CATALOGUE DE MODÈLES D'ÉQUIPEMENTS MÉTIERS (PRESETS)
// =========================================================================

let catalogPresets = [];
let currentCatalogCategory = "all";
let currentCatalogSearch = "";

async function openCatalogModal() {
  try {
    const res = await fetch("/api/presets/catalog");
    if (!res.ok) throw new Error("Impossible de charger le catalogue.");
    catalogPresets = await res.json();
    
    // Mise à jour des compteurs de catégories
    const elAll = document.getElementById("cat-count-all");
    const elInd = document.getElementById("cat-count-industry");
    const elBldg = document.getElementById("cat-count-building");
    const elInfra = document.getElementById("cat-count-infrastructure");
    const elCity = document.getElementById("cat-count-smart_city");
    const elCustom = document.getElementById("cat-count-custom");
    if (elAll) elAll.textContent = catalogPresets.length;
    if (elInd) elInd.textContent = catalogPresets.filter(p => p.category === 'industry').length;
    if (elBldg) elBldg.textContent = catalogPresets.filter(p => p.category === 'building').length;
    if (elInfra) elInfra.textContent = catalogPresets.filter(p => p.category === 'infrastructure').length;
    if (elCity) elCity.textContent = catalogPresets.filter(p => p.category === 'smart_city').length;
    if (elCustom) elCustom.textContent = catalogPresets.filter(p => p.is_custom).length;

    renderCatalogCards();
    openModal("modal-catalog");
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    alert("Erreur lors de la récupération des modèles : " + err.message);
  }
}

function filterCatalogCategory(category) {
  currentCatalogCategory = category;
  const tabs = [
    { id: "cat-tab-all", cat: "all" },
    { id: "cat-tab-industry", cat: "industry" },
    { id: "cat-tab-building", cat: "building" },
    { id: "cat-tab-infrastructure", cat: "infrastructure" },
    { id: "cat-tab-smart_city", cat: "smart_city" },
    { id: "cat-tab-custom", cat: "custom" }
  ];
  tabs.forEach(tab => {
    const el = document.getElementById(tab.id);
    if (!el) return;
    if (tab.cat === category) {
      el.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#E2001A] text-white transition";
    } else {
      el.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#12151B] text-slate-300 hover:text-white hover:bg-[#202531] border border-[#2B3342] transition";
    }
  });
  renderCatalogCards();
}

function onCatalogSearch(query) {
  currentCatalogSearch = (query || "").toLowerCase().trim();
  renderCatalogCards();
}

function renderCatalogCards() {
  const container = document.getElementById("catalog-presets-grid");
  if (!container) return;

  const filtered = catalogPresets.filter(p => {
    const matchCat = (currentCatalogCategory === "all") ||
      (currentCatalogCategory === "custom" ? p.is_custom : p.category === currentCatalogCategory);
    const matchSearch = !currentCatalogSearch ||
      p.name.toLowerCase().includes(currentCatalogSearch) ||
      p.description.toLowerCase().includes(currentCatalogSearch) ||
      p.category_label.toLowerCase().includes(currentCatalogSearch) ||
      p.variables.some(v => v.name.toLowerCase().includes(currentCatalogSearch) || v.id.toLowerCase().includes(currentCatalogSearch));
    return matchCat && matchSearch;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="col-span-full text-center py-12 text-slate-400">
        <i data-lucide="search-x" class="w-8 h-8 mx-auto mb-2 text-slate-500"></i>
        <p class="text-xs font-medium">Aucun modèle ne correspond à votre recherche.</p>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  container.innerHTML = filtered.map(p => {
    // Category color tag
    let catColor = "bg-slate-800 text-slate-300 border-slate-700";
    if (p.is_custom) catColor = "bg-emerald-950/70 text-emerald-300 border-emerald-800/60";
    else if (p.category === "industry") catColor = "bg-amber-950/70 text-amber-300 border-amber-800/60";
    else if (p.category === "building") catColor = "bg-sky-950/70 text-sky-300 border-sky-800/60";
    else if (p.category === "infrastructure") catColor = "bg-emerald-950/70 text-emerald-300 border-emerald-800/60";
    else if (p.category === "smart_city") catColor = "bg-purple-950/70 text-purple-300 border-purple-800/60";

    const customBadge = p.is_custom
      ? `<span class="inline-block text-[10px] font-semibold px-1.5 py-0.2 rounded border bg-emerald-950/70 text-emerald-300 border-emerald-800/60 ml-1">Custom</span>`
      : "";

    // Protocol badge
    const protoBadge = (p.default_protocol || "mqtt").toUpperCase();

    // Variables preview tags
    const varTags = p.variables.slice(0, 4).map(v => `
      <span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] bg-[#12151B] text-slate-300 border border-[#2B3342]">
        ${escapeHtml(v.name)} ${v.unit ? `<span class="text-slate-500 ml-0.5">(${escapeHtml(v.unit)})</span>` : ""}
      </span>
    `).join("");

    const moreVars = p.variables.length > 4 
      ? `<span class="text-[10px] text-slate-500 font-semibold self-center">+${p.variables.length - 4} autre(s)</span>`
      : "";

    return `
      <div class="bg-[#12151B] hover:bg-[#151922] border border-[#2B3342] hover:border-slate-600 rounded-xl p-4 flex flex-col justify-between transition group shadow-sm">
        <div class="space-y-3">
          <!-- En-tête de la carte -->
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center gap-2.5">
              <div class="w-9 h-9 rounded-lg bg-[#181D26] border border-[#2B3342] group-hover:border-slate-500 flex items-center justify-center text-[#E2001A] shrink-0">
                <i data-lucide="${p.icon || 'cpu'}" class="w-4 h-4"></i>
              </div>
              <div>
                <h4 class="text-xs font-bold text-white group-hover:text-red-400 transition leading-snug flex items-center gap-1">
                  <span>${escapeHtml(p.name)}</span>
                  ${customBadge}
                </h4>
                <span class="inline-block text-[10px] font-medium px-1.5 py-0.2 rounded border ${catColor} mt-0.5">
                  ${escapeHtml(p.category_label)}
                </span>
              </div>
            </div>
            <span class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono shrink-0">
              ${protoBadge}
            </span>
          </div>

          <!-- Description -->
          <p class="text-[11px] text-slate-400 leading-relaxed line-clamp-2">
            ${escapeHtml(p.description)}
          </p>

          <!-- Télémétries incluses -->
          <div>
            <span class="text-[10px] font-semibold text-slate-500 block mb-1">Grandeurs configurées (${p.variables.length}) :</span>
            <div class="flex flex-wrap gap-1">
              ${varTags}
              ${moreVars}
            </div>
          </div>
        </div>

        <!-- Boutons d'action -->
        <div class="pt-3.5 mt-3 border-t border-[#202531] flex items-center gap-1.5">
          <button onclick="downloadPresetDashboard('${p.id}')" title="Télécharger le modèle de Dashboard ThingsBoard (.json)" class="p-2 bg-[#181D26] hover:bg-[#202531] text-sky-400 hover:text-white border border-[#2B3342] rounded-lg transition text-xs flex items-center gap-1 shrink-0">
            <i data-lucide="layout-dashboard" class="w-3.5 h-3.5"></i>
          </button>
          <button onclick="exportSinglePreset('${p.id}')" title="Exporter ce cas d'usage complet (.json avec TB Dashboard, CSV, formule)" class="p-2 bg-[#181D26] hover:bg-[#202531] text-emerald-400 hover:text-white border border-[#2B3342] rounded-lg transition text-xs flex items-center gap-1 shrink-0">
            <i data-lucide="download" class="w-3.5 h-3.5"></i>
          </button>
          ${p.is_custom ? `
          <button onclick="deleteCustomPreset('${p.id}')" title="Supprimer ce modèle personnalisé" class="p-2 bg-[#181D26] hover:bg-rose-950/60 text-rose-400 hover:text-rose-200 border border-[#2B3342] hover:border-rose-800 rounded-lg transition text-xs flex items-center gap-1 shrink-0">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
          ` : ""}
          <button onclick="prepareInstantiatePreset('${p.id}')" class="flex-1 flex items-center justify-center gap-1.5 bg-[#1F2532] hover:bg-[#E2001A] text-slate-200 hover:text-white border border-[#2B3342] hover:border-red-600 text-xs font-semibold py-1.5 px-2.5 rounded-lg transition shadow-sm">
            <i data-lucide="plus" class="w-3.5 h-3.5"></i>
            <span>Utiliser</span>
          </button>
        </div>
      </div>
    `;
  }).join("");

  if (window.lucide) lucide.createIcons();
}

function prepareInstantiatePreset(presetId) {
  const preset = catalogPresets.find(p => p.id === presetId);
  if (!preset) return;

  closeModal("modal-catalog");

  const subtitle = document.getElementById("instantiate-modal-subtitle");
  if (subtitle) subtitle.textContent = `Modèle : ${preset.name} (${preset.category_label})`;

  document.getElementById("instantiate-preset-id").value = preset.id;
  document.getElementById("instantiate-name").value = preset.name;
  document.getElementById("instantiate-device-id").value = "";
  document.getElementById("instantiate-device-id").placeholder = `Ex: ${preset.id}_01`;
  document.getElementById("instantiate-protocol").value = preset.default_protocol || "http";
  const useTlsEl = document.getElementById("instantiate-use-tls");
  if (useTlsEl) useTlsEl.checked = true;
  document.getElementById("instantiate-token").value = "";
  const instantiateIntervalEl = document.getElementById("instantiate-publish-interval");
  if (instantiateIntervalEl) instantiateIntervalEl.value = "";

  const errBox = document.getElementById("instantiate-error");
  if (errBox) errBox.classList.add("hidden");

  // Rendu des badges de prévisualisation des variables
  const previewBox = document.getElementById("instantiate-vars-preview");
  if (previewBox) {
    previewBox.innerHTML = preset.variables.map(v => `
      <span class="px-2 py-1 rounded bg-[#181D26] text-slate-300 border border-[#2B3342] text-[10px] font-medium flex items-center gap-1">
        <span class="w-1.5 h-1.5 rounded-full ${v.var_type === 'telemetry' ? 'bg-emerald-400' : 'bg-sky-400'}"></span>
        ${escapeHtml(v.name)} ${v.unit ? `<span class="text-slate-500 font-mono">(${escapeHtml(v.unit)})</span>` : ''}
      </span>
    `).join("");
  }

  openModal("modal-instantiate-preset");
}

async function submitInstantiatePreset(e) {
  e.preventDefault();
  const presetId = document.getElementById("instantiate-preset-id").value;
  const name = document.getElementById("instantiate-name").value.trim();
  const deviceId = document.getElementById("instantiate-device-id").value.trim();
  const protocol = document.getElementById("instantiate-protocol").value;
  const useTls = document.getElementById("instantiate-use-tls") ? document.getElementById("instantiate-use-tls").checked : true;
  const token = document.getElementById("instantiate-token").value.trim();
  const publishIntervalRaw = document.getElementById("instantiate-publish-interval") ? document.getElementById("instantiate-publish-interval").value.trim() : "";
  const errBox = document.getElementById("instantiate-error");

  const payload = {
    preset_id: presetId,
    name: name || undefined,
    device_id: deviceId || undefined,
    protocol: protocol || undefined,
    token: token || undefined,
    use_tls: useTls,
    publish_interval: publishIntervalRaw ? parseFloat(publishIntervalRaw) : undefined
  };

  try {
    const res = await fetch("/api/presets/instantiate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      if (errBox) {
        errBox.textContent = data.detail || "Erreur lors de la création du modèle.";
        errBox.classList.remove("hidden");
      }
      return;
    }

    closeModal("modal-instantiate-preset");
    await loadAllData();
    let msg = `✅ L'équipement '${data.device.name}' et ses ${data.variables_count} variables ont été créés avec succès !`;
    if (data.validation) {
      if (data.validation.success) {
        msg += `\n\n🟢 Communication validée immédiatement : ${data.validation.message} (latence: ${data.validation.latency_ms || 0}ms)`;
      } else {
        msg += `\n\n⚠️ Test initial de communication : ${data.validation.message}`;
      }
    }
    msg += `\n\n💡 Astuce : Cliquez sur le bouton "Dashboard TB" de cet équipement pour télécharger son tableau de bord ThingsBoard préconfiguré (intégrant son Token et toutes ses grandeurs).`;
    alert(msg);
  } catch (err) {
    if (errBox) {
      errBox.textContent = `Erreur : ${err.message}`;
      errBox.classList.remove("hidden");
    }
  }
}

// --- Import / Export des Cas d'Usage Métier (Presets) ---

async function downloadFileFromApi(url, defaultFilename) {
  try {
    const res = await fetch(url);
    if (!res.ok) {
      let errText = "Erreur lors du téléchargement.";
      try {
        const errJson = await res.json();
        if (errJson.detail) errText = errJson.detail;
      } catch (e) {}
      alert(errText);
      return;
    }
    const blob = await res.blob();
    const disposition = res.headers.get("content-disposition") || "";
    let filename = defaultFilename;
    const match = disposition.match(/filename="?([^";]+)"?/i);
    if (match && match[1]) filename = match[1];

    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  } catch (err) {
    alert("Erreur réseau lors du téléchargement : " + err.message);
  }
}

function exportSinglePreset(presetId) {
  downloadFileFromApi(`/api/presets/${encodeURIComponent(presetId)}/export`, `preset_export_${presetId}.json`);
}

function exportAllPresets() {
  downloadFileFromApi("/api/presets/export/all", "presets_catalog_full_bundle.json");
}

async function handlePresetFileImport(event) {
  const input = event.target;
  if (!input.files || input.files.length === 0) return;
  const file = input.files[0];

  try {
    const text = await file.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch (e) {
      alert("Le fichier sélectionné n'est pas un document JSON valide.");
      input.value = "";
      return;
    }

    const res = await fetch("/api/presets/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    const result = await res.json();
    if (!res.ok) {
      alert("Échec de l'importation : " + (result.detail || "Erreur inconnue"));
      input.value = "";
      return;
    }

    alert(result.message || `${result.imported_count || 1} cas d'usage métier(s) importé(s) avec succès !`);
    input.value = "";
    // Recharger le catalogue pour rafraîchir les modèles et compteurs
    await openCatalogModal();
    // Basculer sur l'onglet personnalisés
    filterCatalogCategory("custom");
  } catch (err) {
    alert("Erreur lors de la lecture du fichier : " + err.message);
    input.value = "";
  }
}

async function deleteCustomPreset(presetId) {
  if (!confirm(`Êtes-vous sûr de vouloir supprimer le modèle personnalisé "${presetId}" ?`)) {
    return;
  }

  try {
    const res = await fetch(`/api/presets/${encodeURIComponent(presetId)}`, {
      method: "DELETE"
    });
    const result = await res.json();
    if (!res.ok) {
      alert("Impossible de supprimer le modèle : " + (result.detail || "Erreur"));
      return;
    }
    // Recharger le catalogue
    await openCatalogModal();
    filterCatalogCategory(currentCatalogCategory);
  } catch (err) {
    alert("Erreur lors de la suppression : " + err.message);
  }
}

