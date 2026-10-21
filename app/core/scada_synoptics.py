"""
Générateur de Schémas Synoptiques SCADA Industriels (SVG / HMI ISA-101).
Fournit des représentations graphiques vectorielles authentiques, animées et adaptées aux règles
des métiers de l'Industrie, du Bâtiment (GTB/GTC), des Réseaux d'Infrastructures et des Villes Intelligentes.
"""

from typing import Dict, Any, List, Optional
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig

def get_scada_synoptic_html(device: DeviceConfig, variables: List[VariableConfig], preset_id: Optional[str] = None) -> str:
    """
    Retourne le code HTML/SVG complet du synoptique SCADA correspondant au cas d'usage métier.
    """
    dev_id = (preset_id or device.id or "").lower()
    dev_name = device.name or device.id
    token_str = device.token or "NON_RENSEIGNE"
    proto_str = device.protocol.value.upper() if hasattr(device.protocol, "value") else str(device.protocol).upper()

    var_map = {v.id.lower(): v for v in variables}

    # Recherche par correspondance de clés métier
    for key, builder in SYNOPTIC_BUILDERS.items():
        if key in dev_id:
            return builder(dev_name, token_str, proto_str, variables, var_map)

    # Synoptique générique SCADA process
    return build_generic_scada_synoptic(dev_name, token_str, proto_str, variables, var_map)


# =====================================================================
# STYLES CSS SCADA COMMONS (Animations industrielles, voyants, tags)
# =====================================================================
SCADA_CSS = """
<style>
  .scada-container {
    background: #0B0F17;
    border: 1px solid #1F2937;
    border-radius: 12px;
    padding: 16px;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: #E2E8F0;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  }
  .scada-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #1E293B;
    padding-bottom: 10px;
    margin-bottom: 12px;
  }
  .scada-title {
    font-size: 13px;
    font-weight: 700;
    color: #F8FAFC;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .scada-live-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #10B981;
    border-radius: 50%;
    box-shadow: 0 0 10px #10B981;
    animation: blink-live 1.5s infinite;
  }
  @keyframes blink-live {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.35; transform: scale(0.85); }
  }
  .scada-badge {
    background: #131B28;
    border: 1px solid #283548;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    color: #94A3B8;
  }
  .scada-badge strong { color: #38BDF8; }
  .scada-badge-token { color: #F59E0B; font-family: monospace; }
  
  .pipe-flow {
    stroke-dasharray: 8, 4;
    animation: pipe-anim 1.2s linear infinite;
  }
  .pipe-flow-fast {
    stroke-dasharray: 6, 3;
    animation: pipe-anim 0.6s linear infinite;
  }
  @keyframes pipe-anim {
    from { stroke-dashoffset: 24; }
    to { stroke-dashoffset: 0; }
  }
  
  .scada-rotor {
    transform-origin: center;
    animation: rotate-blade 2s linear infinite;
  }
  .scada-rotor-fast {
    transform-origin: center;
    animation: rotate-blade 0.7s linear infinite;
  }
  @keyframes rotate-blade {
    100% { transform: rotate(360deg); }
  }
</style>
"""

def scada_wrapper(title: str, token: str, proto: str, svg_content: str) -> str:
    return f"""{SCADA_CSS}
<div class="scada-container">
  <div class="scada-header">
    <div class="scada-title">
      <span class="scada-live-indicator"></span>
      {title}
    </div>
    <div style="display:flex; gap:10px; align-items:center;">
      <div class="scada-badge">Protocole: <strong>{proto}</strong></div>
      <div class="scada-badge">Token TB: <strong class="scada-badge-token">{token}</strong></div>
    </div>
  </div>
  {svg_content}
</div>
"""

# =====================================================================
# 1. INDUSTRIE : COMPRESSEUR D'AIR
# =====================================================================
def build_synoptic_compressor(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    svg = """
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#0F141E; border-radius:8px; border:1px solid #1C2433;">
    <!-- Filtre aspiration -->
    <rect x="30" y="90" width="60" height="70" rx="6" fill="#1E293B" stroke="#475569" stroke-width="2"/>
    <text x="60" y="125" fill="#94A3B8" font-size="10" text-anchor="middle" font-weight="bold">FILTRE G4</text>
    <path d="M 90 125 L 180 125" fill="none" stroke="#38BDF8" stroke-width="6" class="pipe-flow"/>

    <!-- Bloc Vis Bi-Étagé -->
    <rect x="180" y="60" width="130" height="130" rx="10" fill="#182030" stroke="#E2001A" stroke-width="2.5"/>
    <circle cx="245" cy="125" r="45" fill="#111827" stroke="#E2001A" stroke-width="1.5"/>
    <g transform="translate(245, 125)">
      <path class="scada-rotor" d="M -30 -5 C -15 -25 15 -25 30 -5 C 15 25 -15 25 -30 -5 Z" fill="#E2001A" opacity="0.85"/>
      <circle cx="0" cy="0" r="10" fill="#F8FAFC"/>
    </g>
    <text x="245" y="45" fill="#F1F5F9" font-size="11" text-anchor="middle" font-weight="bold">BLOC VIS BI-ÉTAGÉ</text>
    <!-- Moteur 75kW -->
    <rect x="210" y="200" width="70" height="45" rx="4" fill="#1E293B" stroke="#38BDF8" stroke-width="1.5"/>
    <text x="245" y="227" fill="#38BDF8" font-size="9" text-anchor="middle" font-weight="bold">MOTEUR 75kW</text>

    <!-- Tuyauterie huile/air -->
    <path d="M 310 125 L 410 125" fill="none" stroke="#F59E0B" stroke-width="6" class="pipe-flow-fast"/>

    <!-- Séparateur Huile/Air -->
    <rect x="410" y="75" width="85" height="100" rx="8" fill="#1E293B" stroke="#F59E0B" stroke-width="2"/>
    <text x="452" y="105" fill="#F59E0B" font-size="10" text-anchor="middle" font-weight="bold">SÉPARATEUR</text>
    <rect x="420" y="145" width="65" height="20" rx="3" fill="#D97706" opacity="0.6"/>

    <!-- Cuve Tampon 1000L -->
    <path d="M 495 125 L 590 125" fill="none" stroke="#10B981" stroke-width="6" class="pipe-flow"/>
    <rect x="590" y="50" width="110" height="150" rx="20" fill="#1E293B" stroke="#38BDF8" stroke-width="2.5"/>
    <text x="645" y="80" fill="#38BDF8" font-size="11" text-anchor="middle" font-weight="bold">RÉSERVOIR AIR</text>
    <text x="645" y="95" fill="#64748B" font-size="9" text-anchor="middle">Capacité: 1000L</text>
    <line x1="645" y1="110" x2="645" y2="175" stroke="#10B981" stroke-width="6" stroke-linecap="round"/>

    <!-- Sortie Réseau -->
    <path d="M 700 125 L 860 125" fill="none" stroke="#10B981" stroke-width="6" class="pipe-flow"/>
    <polygon points="860,120 875,125 860,130" fill="#10B981"/>
    <text x="900" y="129" fill="#10B981" font-size="11" font-weight="bold">USINE</text>

    <!-- Callouts SCADA -->
    <g transform="translate(680, 40)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#38BDF8" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">PRESSION RÉSEAU</text>
      <text x="10" y="31" fill="#38BDF8" font-size="13" font-weight="bold" font-family="monospace">${pression_reseau:1} bar</text>
    </g>
    <g transform="translate(385, 190)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#F59E0B" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">TEMPÉRATURE HUILE</text>
      <text x="10" y="31" fill="#F59E0B" font-size="13" font-weight="bold" font-family="monospace">${temperature_huile:1} °C</text>
    </g>
  </svg>
    """
    return scada_wrapper(f"Synoptique P&ID SCADA : {name}", token, proto, svg)

# =====================================================================
# 2. INDUSTRIE : CHAUDIÈRE VAPEUR (P&ID)
# =====================================================================
def build_synoptic_steam_boiler(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    svg = """
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#0F141E; border-radius:8px; border:1px solid #1C2433;">
    <!-- Bâche alimentaire (Eau) -->
    <rect x="40" y="80" width="90" height="110" rx="10" fill="#1E293B" stroke="#0284C7" stroke-width="2"/>
    <text x="85" y="105" fill="#38BDF8" font-size="10" text-anchor="middle" font-weight="bold">BÂCHE ALIM.</text>
    <rect x="45" y="130" width="80" height="55" rx="4" fill="#0284C7" opacity="0.4"/>
    
    <!-- Pompe alimentaire HP -->
    <path d="M 130 150 L 190 150" fill="none" stroke="#38BDF8" stroke-width="5" class="pipe-flow"/>
    <circle cx="210" cy="150" r="20" fill="#1E293B" stroke="#10B981" stroke-width="2"/>
    <text x="210" y="185" fill="#10B981" font-size="9" text-anchor="middle">POMPE HP</text>

    <!-- Corps de Chaudière Tubulaire -->
    <path d="M 230 150 L 310 150" fill="none" stroke="#38BDF8" stroke-width="5" class="pipe-flow"/>
    <rect x="310" y="45" width="280" height="160" rx="20" fill="#182030" stroke="#EF4444" stroke-width="2.5"/>
    <text x="450" y="75" fill="#F8FAFC" font-size="13" text-anchor="middle" font-weight="bold">CORPS DE CHAUDIÈRE INDUSTRIELLE</text>

    <!-- Brûleur Gaz Modulant -->
    <rect x="250" y="80" width="60" height="60" rx="6" fill="#B91C1C" stroke="#EF4444" stroke-width="1.5"/>
    <polygon points="310,95 360,110 310,125" fill="#F59E0B" opacity="0.8"/>
    <text x="280" y="155" fill="#F87171" font-size="9" text-anchor="middle" font-weight="bold">BRÛLEUR</text>

    <!-- Niveau d'Eau Chaudière -->
    <rect x="330" y="130" width="240" height="60" rx="6" fill="#0284C7" opacity="0.3"/>
    <!-- Ciel de Vapeur HP -->
    <rect x="330" y="85" width="240" height="40" fill="#CBD5E1" opacity="0.15"/>
    <text x="450" y="110" fill="#E2E8F0" font-size="11" text-anchor="middle" font-weight="bold">CIEL VAPEUR HP (12.5 bar)</text>

    <!-- Départ Collecteur Vapeur -->
    <path d="M 450 45 L 450 15 L 750 15 L 750 80" fill="none" stroke="#E2E8F0" stroke-width="6" class="pipe-flow"/>
    <rect x="700" y="80" width="100" height="90" rx="8" fill="#1E293B" stroke="#94A3B8" stroke-width="2"/>
    <text x="750" y="115" fill="#F8FAFC" font-size="10" text-anchor="middle" font-weight="bold">BARILLET</text>
    <text x="750" y="130" fill="#94A3B8" font-size="9" text-anchor="middle">Vapeur Usine</text>

    <!-- Callouts SCADA -->
    <g transform="translate(620, 185)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#EF4444" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">PRESSION VAPEUR</text>
      <text x="10" y="31" fill="#EF4444" font-size="13" font-weight="bold" font-family="monospace">${pression_vapeur:1} bar</text>
    </g>
    <g transform="translate(420, 210)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#F59E0B" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">TEMP. FOYER / FUMÉES</text>
      <text x="10" y="31" fill="#F59E0B" font-size="13" font-weight="bold" font-family="monospace">${temperature_foyer:0} °C</text>
    </g>
  </svg>
    """
    return scada_wrapper(f"Synoptique Thermique SCADA : {name}", token, proto, svg)

# =====================================================================
# 3. INDUSTRIE : GROUPE FROID / CHILLER
# =====================================================================
def build_synoptic_chiller(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    svg = """
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#0F141E; border-radius:8px; border:1px solid #1C2433;">
    <!-- Boucle Frigorifique fermée -->
    <rect x="180" y="60" width="380" height="140" rx="16" fill="#16202E" stroke="#0284C7" stroke-width="2"/>
    <text x="370" y="90" fill="#38BDF8" font-size="12" text-anchor="middle" font-weight="bold">CHILLER INDUSTRIEL (R134a)</text>

    <!-- Évaporateur (Eau glacée) -->
    <rect x="195" y="110" width="90" height="70" rx="8" fill="#0C4A6E" stroke="#38BDF8" stroke-width="1.5"/>
    <text x="240" y="140" fill="#38BDF8" font-size="10" text-anchor="middle" font-weight="bold">ÉVAPORATEUR</text>
    <text x="240" y="155" fill="#E0F2FE" font-size="9" text-anchor="middle">7°C / 12°C</text>

    <!-- Compresseur à vis -->
    <circle cx="370" cy="145" r="30" fill="#1E293B" stroke="#E2001A" stroke-width="2"/>
    <g transform="translate(370,145)" class="scada-rotor">
      <path d="M -16 -4 C -8 -12 8 -12 16 -4 C 8 12 -8 12 -16 -4 Z" fill="#E2001A"/>
    </g>
    <text x="370" y="190" fill="#E2001A" font-size="9" text-anchor="middle" font-weight="bold">COMPRESSEUR</text>

    <!-- Condenseur Aéroréfrigérant -->
    <rect x="455" y="110" width="90" height="70" rx="8" fill="#7F1D1D" stroke="#EF4444" stroke-width="1.5"/>
    <text x="500" y="140" fill="#F87171" font-size="10" text-anchor="middle" font-weight="bold">CONDENSEUR</text>

    <!-- Circuit Eau Glacée Départ/Retour Usine -->
    <path d="M 50 120 L 195 120" fill="none" stroke="#38BDF8" stroke-width="6" class="pipe-flow"/>
    <text x="120" y="110" fill="#38BDF8" font-size="10">RETOUR USINE (12°C)</text>
    <path d="M 195 160 L 50 160" fill="none" stroke="#0284C7" stroke-width="6" class="pipe-flow-fast"/>
    <text x="120" y="180" fill="#0284C7" font-size="10">DÉPART EAU GLACÉE (7°C)</text>

    <!-- Callouts SCADA -->
    <g transform="translate(680, 50)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#38BDF8" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">TEMP. EAU GLACÉE</text>
      <text x="10" y="31" fill="#38BDF8" font-size="13" font-weight="bold" font-family="monospace">${temperature_eau_depart:1} °C</text>
    </g>
    <g transform="translate(680, 110)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#10B981" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">COP INSTANTANÉ</text>
      <text x="10" y="31" fill="#10B981" font-size="13" font-weight="bold" font-family="monospace">${cop:2}</text>
    </g>
  </svg>
    """
    return scada_wrapper(f"Synoptique Frigorifique SCADA : {name}", token, proto, svg)

# =====================================================================
# 4. BÂTIMENT : CENTRALE DE TRAITEMENT D'AIR (CTA / GTB)
# =====================================================================
def build_synoptic_cta(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    svg = """
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#0F141E; border-radius:8px; border:1px solid #1C2433;">
    <rect x="60" y="35" width="830" height="190" rx="12" fill="#131A26" stroke="#334155" stroke-width="2.5"/>
    <line x1="60" y1="130" x2="890" y2="130" stroke="#1E293B" stroke-width="2" stroke-dasharray="4,4"/>

    <!-- Voie Soufflage -->
    <text x="80" y="60" fill="#38BDF8" font-size="11" font-weight="bold">VOIE SOUFFLAGE AIR NEUF</text>
    <rect x="110" y="70" width="30" height="45" fill="#1E293B" stroke="#38BDF8" stroke-width="1.5"/>
    <text x="125" y="97" fill="#94A3B8" font-size="8" text-anchor="middle">REG.</text>

    <rect x="180" y="65" width="25" height="55" fill="#334155" stroke="#94A3B8" stroke-width="1.5"/>
    <text x="192" y="97" fill="#CBD5E1" font-size="8" text-anchor="middle">F7</text>

    <rect x="250" y="65" width="40" height="55" rx="4" fill="#0C4A6E" stroke="#0284C7" stroke-width="1.5"/>
    <text x="270" y="97" fill="#38BDF8" font-size="8" text-anchor="middle">FROID</text>

    <rect x="330" y="65" width="40" height="55" rx="4" fill="#7F1D1D" stroke="#DC2626" stroke-width="1.5"/>
    <text x="350" y="97" fill="#F87171" font-size="8" text-anchor="middle">CHAUD</text>

    <!-- Ventilateur EC -->
    <g transform="translate(460, 92)">
      <circle cx="0" cy="0" r="28" fill="#1E293B" stroke="#10B981" stroke-width="2"/>
      <g class="scada-rotor">
        <path d="M -18 -5 C -8 -15 8 -15 18 -5 C 8 15 -8 15 -18 -5 Z" fill="#10B981"/>
      </g>
      <circle cx="0" cy="0" r="6" fill="#F8FAFC"/>
      <text x="0" y="40" fill="#10B981" font-size="8" text-anchor="middle">PLUG-FAN EC</text>
    </g>

    <!-- Soufflage vers bâtiment -->
    <path d="M 495 92 L 780 92" fill="none" stroke="#38BDF8" stroke-width="7" class="pipe-flow"/>
    <text x="825" y="96" fill="#38BDF8" font-size="10" font-weight="bold">BÂTIMENT</text>

    <!-- Voie Reprise -->
    <text x="80" y="155" fill="#94A3B8" font-size="11" font-weight="bold">VOIE REPRISE EXTRACTION</text>
    <path d="M 780 180 L 495 180" fill="none" stroke="#94A3B8" stroke-width="6" class="pipe-flow"/>

    <!-- Callouts SCADA -->
    <g transform="translate(680, 40)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#38BDF8" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">TEMP. SOUFFLAGE</text>
      <text x="10" y="31" fill="#38BDF8" font-size="13" font-weight="bold" font-family="monospace">${temperature_soufflage:1} °C</text>
    </g>
    <g transform="translate(680, 110)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#10B981" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">DÉBIT SOUFFLAGE</text>
      <text x="10" y="31" fill="#10B981" font-size="13" font-weight="bold" font-family="monospace">${debit_air_soufflage:0} m³/h</text>
    </g>
  </svg>
    """
    return scada_wrapper(f"Synoptique Aéraulique GTB : {name}", token, proto, svg)

# =====================================================================
# 5. BÂTIMENT : TGBT & SCHÉMA UNIFILAIRE (SLD)
# =====================================================================
def build_synoptic_tgbt(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    svg = """
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#0F141E; border-radius:8px; border:1px solid #1C2433;">
    <line x1="50" y1="50" x2="250" y2="50" stroke="#E2001A" stroke-width="5"/>
    <text x="50" y="35" fill="#E2001A" font-size="11" font-weight="bold">ARRIVÉE HTA / BT (400V TRIPHASÉ)</text>

    <!-- Disjoncteur Général Masterpact -->
    <g transform="translate(300, 50)">
      <rect x="-18" y="-18" width="36" height="36" fill="#1E293B" stroke="#10B981" stroke-width="2"/>
      <line x1="-10" y1="-10" x2="10" y2="10" stroke="#10B981" stroke-width="3"/>
      <line x1="-10" y1="10" x2="10" y2="-10" stroke="#10B981" stroke-width="3"/>
      <text x="0" y="30" fill="#10B981" font-size="9" text-anchor="middle" font-weight="bold">DISJONCTEUR DGBT</text>
    </g>

    <!-- Jeu de Barres Général Cuivre -->
    <line x1="420" y1="35" x2="420" y2="230" stroke="#F59E0B" stroke-width="6"/>
    <text x="435" y="35" fill="#F59E0B" font-size="11" font-weight="bold">JEU DE BARRES TGBT 1600A</text>

    <!-- Départs Force, CVC, Éclairage -->
    <g transform="translate(420, 75)">
      <line x1="0" y1="0" x2="120" y2="0" stroke="#38BDF8" stroke-width="3"/>
      <text x="130" y="4" fill="#94A3B8" font-size="10">Départ CVC & Pompes (250A)</text>
    </g>
    <g transform="translate(420, 135)">
      <line x1="0" y1="0" x2="120" y2="0" stroke="#38BDF8" stroke-width="3"/>
      <text x="130" y="4" fill="#94A3B8" font-size="10">Départ Informatique / Onduleur (160A)</text>
    </g>
    <g transform="translate(420, 195)">
      <line x1="0" y1="0" x2="120" y2="0" stroke="#38BDF8" stroke-width="3"/>
      <text x="130" y="4" fill="#94A3B8" font-size="10">Départ Éclairage DALI (63A)</text>
    </g>

    <!-- Callouts Électriques -->
    <g transform="translate(680, 50)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#38BDF8" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">PUISSANCE ACTIVE</text>
      <text x="10" y="31" fill="#38BDF8" font-size="13" font-weight="bold" font-family="monospace">${puissance_active_totale:1} kW</text>
    </g>
    <g transform="translate(680, 110)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#10B981" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">COS PHI (FACTEUR)</text>
      <text x="10" y="31" fill="#10B981" font-size="13" font-weight="bold" font-family="monospace">${facteur_puissance:2}</text>
    </g>
  </svg>
    """
    return scada_wrapper(f"Schéma Unifilaire SCADA : {name}", token, proto, svg)

# =====================================================================
# 6. INFRASTRUCTURE : PARC SOLAIRE PHOTOVOLTAÏQUE
# =====================================================================
def build_synoptic_solar_pv(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    svg = """
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#0F141E; border-radius:8px; border:1px solid #1C2433;">
    <g transform="translate(80, 45)">
      <circle cx="0" cy="0" r="20" fill="#F59E0B" opacity="0.9"/>
      <text x="0" y="38" fill="#F59E0B" font-size="9" text-anchor="middle">PYRANOMÈTRE</text>
    </g>

    <g transform="translate(170, 60)">
      <polygon points="0,60 25,10 115,10 90,60" fill="#1E293B" stroke="#38BDF8" stroke-width="2"/>
      <polygon points="105,60 130,10 220,10 195,60" fill="#1E293B" stroke="#38BDF8" stroke-width="2"/>
      <text x="110" y="85" fill="#94A3B8" font-size="10" text-anchor="middle">CHAMP SOLAIRE 500kWc</text>
    </g>

    <path d="M 380 95 L 480 95" fill="none" stroke="#F59E0B" stroke-width="5" stroke-dasharray="6,3"/>
    <text x="430" y="85" fill="#F59E0B" font-size="9" text-anchor="middle">DC 820V</text>

    <!-- Onduleur Central -->
    <g transform="translate(540, 95)">
      <rect x="-45" y="-50" width="90" height="100" rx="8" fill="#1E293B" stroke="#10B981" stroke-width="2.5"/>
      <text x="-20" y="-12" fill="#F59E0B" font-size="12" font-weight="bold">DC</text>
      <text x="12" y="22" fill="#38BDF8" font-size="12" font-weight="bold">AC</text>
      <text x="0" y="65" fill="#10B981" font-size="9" text-anchor="middle" font-weight="bold">ONDULEUR MPPT</text>
    </g>

    <path d="M 585 95 L 750 95" fill="none" stroke="#38BDF8" stroke-width="5" class="pipe-flow"/>
    <text x="810" y="100" fill="#38BDF8" font-size="11" font-weight="bold">INJECTION RÉSEAU</text>

    <!-- Callouts SCADA -->
    <g transform="translate(480, 180)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#38BDF8" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">PUISSANCE INJECTÉE</text>
      <text x="10" y="31" fill="#38BDF8" font-size="13" font-weight="bold" font-family="monospace">${puissance_active_ac:1} kW</text>
    </g>
    <g transform="translate(680, 180)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#10B981" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">ÉNERGIE PRODUITE</text>
      <text x="10" y="31" fill="#10B981" font-size="13" font-weight="bold" font-family="monospace">${energie_active_totale:1} kWh</text>
    </g>
  </svg>
    """
    return scada_wrapper(f"Supervision Solaire SCADA : {name}", token, proto, svg)

# =====================================================================
# 7. INFRASTRUCTURE : POSTE DE RELEVAGE EAUX USÉES (ASSAINISSEMENT)
# =====================================================================
def build_synoptic_water_pump(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    svg = """
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#0F141E; border-radius:8px; border:1px solid #1C2433;">
    <!-- Fosse Humide Béton -->
    <rect x="80" y="40" width="350" height="180" rx="10" fill="#131B26" stroke="#475569" stroke-width="3"/>
    <text x="255" y="70" fill="#94A3B8" font-size="11" text-anchor="middle" font-weight="bold">FOSSE DE RELEVAGE BÉTON (EAUX USÉES)</text>

    <!-- Effluent / Niveau liquide -->
    <rect x="85" y="110" width="340" height="105" rx="6" fill="#065F46" opacity="0.45"/>
    <!-- Sonde Ultrason Niveau -->
    <g transform="translate(200, 40)">
      <rect x="-15" y="0" width="30" height="20" fill="#F59E0B"/>
      <path d="M 0 20 L -15 50 M 0 20 L 15 50" stroke="#F59E0B" stroke-width="1.5" stroke-dasharray="3,3"/>
      <text x="0" y="-8" fill="#F59E0B" font-size="8" text-anchor="middle">SONDE ULTRASON</text>
    </g>

    <!-- Pompes Submersibles P1 et P2 -->
    <g transform="translate(160, 165)">
      <rect x="-20" y="-30" width="40" height="40" rx="6" fill="#1E293B" stroke="#10B981" stroke-width="2"/>
      <text x="0" y="-8" fill="#10B981" font-size="9" text-anchor="middle" font-weight="bold">POMPE 1</text>
    </g>
    <g transform="translate(320, 165)">
      <rect x="-20" y="-30" width="40" height="40" rx="6" fill="#1E293B" stroke="#64748B" stroke-width="2"/>
      <text x="0" y="-8" fill="#94A3B8" font-size="9" text-anchor="middle" font-weight="bold">POMPE 2 (SECOURS)</text>
    </g>

    <!-- Conduite de Refoulement PEHD -->
    <path d="M 160 135 L 160 90 L 580 90" fill="none" stroke="#10B981" stroke-width="6" class="pipe-flow-fast"/>
    <text x="640" y="95" fill="#10B981" font-size="11" font-weight="bold">REFOULEMENT STEP</text>

    <!-- Callouts SCADA -->
    <g transform="translate(680, 50)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#38BDF8" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">NIVEAU BACHE</text>
      <text x="10" y="31" fill="#38BDF8" font-size="13" font-weight="bold" font-family="monospace">${niveau_bache_m:2} m</text>
    </g>
    <g transform="translate(680, 110)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#10B981" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">DÉBIT REFOULEMENT</text>
      <text x="10" y="31" fill="#10B981" font-size="13" font-weight="bold" font-family="monospace">${debit_instantane_m3h:1} m³/h</text>
    </g>
  </svg>
    """
    return scada_wrapper(f"Synoptique Assainissement SCADA : {name}", token, proto, svg)

# =====================================================================
# 8. VILLE INTELLIGENTE : ÉCLAIRAGE PUBLIC CONNECTÉ
# =====================================================================
def build_synoptic_city_lighting(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    svg = """
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#0F141E; border-radius:8px; border:1px solid #1C2433;">
    <!-- Armoire de Commande Rue -->
    <rect x="80" y="60" width="120" height="140" rx="8" fill="#1E293B" stroke="#F59E0B" stroke-width="2"/>
    <text x="140" y="90" fill="#F59E0B" font-size="10" text-anchor="middle" font-weight="bold">ARMOIRE ÉCLAIRAGE</text>
    <text x="140" y="110" fill="#94A3B8" font-size="9" text-anchor="middle">Horloge Astro</text>

    <!-- Candélabres LED sur voirie -->
    <g transform="translate(320, 80)">
      <line x1="0" y1="120" x2="0" y2="0" stroke="#64748B" stroke-width="4"/>
      <path d="M 0 0 Q 15 -10 30 -5" fill="none" stroke="#64748B" stroke-width="3"/>
      <polygon points="25,-5 35,-5 30,5" fill="#FBBF24"/>
      <!-- Faisceau lumineux -->
      <polygon points="20,5 40,5 60,80 0,80" fill="#FBBF24" opacity="0.15"/>
    </g>

    <g transform="translate(520, 80)">
      <line x1="0" y1="120" x2="0" y2="0" stroke="#64748B" stroke-width="4"/>
      <path d="M 0 0 Q 15 -10 30 -5" fill="none" stroke="#64748B" stroke-width="3"/>
      <polygon points="25,-5 35,-5 30,5" fill="#FBBF24"/>
      <polygon points="20,5 40,5 60,80 0,80" fill="#FBBF24" opacity="0.15"/>
    </g>

    <!-- Ligne d'alimentation souterraine -->
    <line x1="200" y1="180" x2="650" y2="180" stroke="#F59E0B" stroke-width="4" stroke-dasharray="6,3"/>

    <!-- Callouts SCADA -->
    <g transform="translate(680, 50)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#F59E0B" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">PUISSANCE ACTIVE</text>
      <text x="10" y="31" fill="#F59E0B" font-size="13" font-weight="bold" font-family="monospace">${puissance_active_kw:1} kW</text>
    </g>
    <g transform="translate(680, 110)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#10B981" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">TAUX DE GRADATION</text>
      <text x="10" y="31" fill="#10B981" font-size="13" font-weight="bold" font-family="monospace">${taux_gradation_pct:0} %</text>
    </g>
  </svg>
    """
    return scada_wrapper(f"Synoptique Smart Lighting SCADA : {name}", token, proto, svg)

# =====================================================================
# 9. VILLE / TÉLÉCOMS : SHELTER TÉLÉCOMS & FIBRE (N+1)
# =====================================================================
def build_synoptic_telecom(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    svg = """
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#0F141E; border-radius:8px; border:1px solid #1C2433;">
    <!-- Enceinte Shelter Sécurisé -->
    <rect x="70" y="40" width="550" height="180" rx="10" fill="#131B26" stroke="#0284C7" stroke-width="2.5"/>
    <text x="180" y="65" fill="#38BDF8" font-size="11" font-weight="bold">SHELTER TÉLÉCOMS / POP FIBRE</text>

    <!-- Baies Serveurs / Switchs 19 pouces -->
    <rect x="110" y="80" width="65" height="120" rx="4" fill="#1E293B" stroke="#94A3B8" stroke-width="1.5"/>
    <line x1="115" y1="100" x2="170" y2="100" stroke="#38BDF8" stroke-width="2"/>
    <line x1="115" y1="120" x2="170" y2="120" stroke="#38BDF8" stroke-width="2"/>
    <text x="142" y="190" fill="#94A3B8" font-size="8" text-anchor="middle">BAIE ROUTEURS</text>

    <rect x="200" y="80" width="65" height="120" rx="4" fill="#1E293B" stroke="#94A3B8" stroke-width="1.5"/>
    <line x1="205" y1="100" x2="260" y2="100" stroke="#10B981" stroke-width="2"/>
    <text x="232" y="190" fill="#94A3B8" font-size="8" text-anchor="middle">BAIE OLT FIBRE</text>

    <!-- Onduleur UPS Double Conversion -->
    <rect x="290" y="80" width="70" height="120" rx="4" fill="#1E293B" stroke="#F59E0B" stroke-width="1.5"/>
    <text x="325" y="130" fill="#F59E0B" font-size="9" text-anchor="middle" font-weight="bold">UPS 40kVA</text>
    <text x="325" y="145" fill="#F59E0B" font-size="8" text-anchor="middle">BATTERIES</text>

    <!-- Climatisation Redondante N+1 -->
    <rect x="400" y="80" width="80" height="120" rx="4" fill="#0C4A6E" stroke="#38BDF8" stroke-width="1.5"/>
    <text x="440" y="130" fill="#38BDF8" font-size="9" text-anchor="middle" font-weight="bold">CLIM PRECISION</text>
    <text x="440" y="145" fill="#38BDF8" font-size="8" text-anchor="middle">N+1 REDONDANT</text>

    <!-- Callouts SCADA -->
    <g transform="translate(680, 50)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#38BDF8" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">TEMP. SALLE (CONSIGNE)</text>
      <text x="10" y="31" fill="#38BDF8" font-size="13" font-weight="bold" font-family="monospace">${temperature_baie:1} °C</text>
    </g>
    <g transform="translate(680, 110)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#10B981" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">CHARGE ONDULEUR</text>
      <text x="10" y="31" fill="#10B981" font-size="13" font-weight="bold" font-family="monospace">${charge_ups_pct:0} %</text>
    </g>
  </svg>
    """
    return scada_wrapper(f"Supervision Shelter Télécoms SCADA : {name}", token, proto, svg)

# =====================================================================
# 10. VILLES INTELLIGENTES : COMPTAGE TRAFIC, MOBILITÉS & RADAR
# =====================================================================
def build_synoptic_city_traffic(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    svg = """
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#0F141E; border-radius:8px; border:1px solid #1C2433;">
    <!-- Voie Routière Principale (Asphalte sombre) -->
    <rect x="50" y="70" width="600" height="150" rx="8" fill="#141A23" stroke="#2B3342" stroke-width="2"/>

    <!-- Voie Cyclable & Mobilités Douces (Bande verte normée) -->
    <rect x="50" y="70" width="600" height="35" rx="4" fill="#064E3B" opacity="0.45" stroke="#10B981" stroke-width="1"/>
    <text x="70" y="92" fill="#34D399" font-size="10" font-weight="bold">VOIE CYCLABLE & TROTTINETTES (BIKE LANE)</text>
    <line x1="50" y1="105" x2="650" y2="105" stroke="#10B981" stroke-width="2"/>

    <!-- Ligne médiane blanche discontinue animée pour flux VL -->
    <line x1="50" y1="160" x2="650" y2="160" stroke="#F8FAFC" stroke-width="3" stroke-dasharray="14,10" class="pipe-flow"/>
    <text x="70" y="140" fill="#94A3B8" font-size="10">VOIE VL 1 (AMONT)</text>
    <text x="70" y="195" fill="#94A3B8" font-size="10">VOIE VL 2 (AVAL / BUS)</text>

    <!-- Boucles à Induction Magnétiques au sol -->
    <rect x="220" y="115" width="45" height="35" rx="3" fill="#1E293B" stroke="#38BDF8" stroke-width="1.5" stroke-dasharray="3,2"/>
    <rect x="220" y="170" width="45" height="35" rx="3" fill="#1E293B" stroke="#38BDF8" stroke-width="1.5" stroke-dasharray="3,2"/>
    <text x="242" y="136" fill="#38BDF8" font-size="8" text-anchor="middle">BOUCLE 1</text>
    <text x="242" y="191" fill="#38BDF8" font-size="8" text-anchor="middle">BOUCLE 2</text>

    <!-- Portique Radar Doppler & Caméra IA -->
    <line x1="380" y1="50" x2="380" y2="230" stroke="#64748B" stroke-width="4"/>
    <line x1="375" y1="50" x2="480" y2="50" stroke="#64748B" stroke-width="4"/>
    <rect x="420" y="40" width="45" height="20" rx="4" fill="#E2001A" stroke="#FFFFFF" stroke-width="1.5"/>
    <text x="442" y="54" fill="#FFFFFF" font-size="8" text-anchor="middle" font-weight="bold">RADAR</text>
    <polygon points="430,62 455,62 490,135 395,135" fill="#38BDF8" opacity="0.15"/>

    <!-- Feu Tricolore de Régulation Urbaine -->
    <g transform="translate(560, 40)">
      <rect width="26" height="65" rx="6" fill="#0B0F17" stroke="#475569" stroke-width="2"/>
      <circle cx="13" cy="14" r="6" fill="#EF4444" opacity="0.3"/>
      <circle cx="13" cy="32" r="6" fill="#F59E0B" opacity="0.3"/>
      <circle cx="13" cy="50" r="6" fill="#10B981" opacity="1" class="scada-live-indicator"/>
    </g>

    <!-- Armoire Régulateur de Carrefour (Contrôleur) -->
    <rect x="580" y="170" width="55" height="45" rx="4" fill="#1E293B" stroke="#FBBF24" stroke-width="1.5"/>
    <text x="607" y="195" fill="#FBBF24" font-size="8" text-anchor="middle" font-weight="bold">RÉGULATEUR</text>
    <text x="607" y="206" fill="#94A3B8" font-size="7" text-anchor="middle">PRIORITÉ BUS</text>

    <!-- Callouts SCADA Temps Réel -->
    <g transform="translate(680, 45)">
      <rect width="230" height="42" rx="6" fill="#141A24" stroke="#38BDF8" stroke-width="1.5"/>
      <text x="12" y="18" fill="#94A3B8" font-size="9">COMPTAGE VÉHICULES LÉGERS</text>
      <text x="12" y="34" fill="#38BDF8" font-size="14" font-weight="bold" font-family="monospace">DÉBIT : ${debit_vehicules:0} véh/h</text>
    </g>

    <g transform="translate(680, 97)">
      <rect width="230" height="42" rx="6" fill="#141A24" stroke="#10B981" stroke-width="1.5"/>
      <text x="12" y="18" fill="#94A3B8" font-size="9">PASSAGES VÉLOS & MOBILITÉS</text>
      <text x="12" y="34" fill="#10B981" font-size="14" font-weight="bold" font-family="monospace">FLUX : ${debit_cyclistes:0} vélos/h</text>
    </g>

    <g transform="translate(680, 149)">
      <rect width="230" height="42" rx="6" fill="#141A24" stroke="#F59E0B" stroke-width="1.5"/>
      <text x="12" y="18" fill="#94A3B8" font-size="9">VITESSE MOYENNE DOPPLER</text>
      <text x="12" y="34" fill="#F59E0B" font-size="14" font-weight="bold" font-family="monospace">RADAR : ${vitesse_moyenne_kmh:1} km/h</text>
    </g>

    <g transform="translate(680, 201)">
      <rect width="230" height="42" rx="6" fill="#141A24" stroke="#10B981" stroke-width="1.5"/>
      <text x="12" y="18" fill="#94A3B8" font-size="9">ÉTAT DE CONGESTION & TRAFIC</text>
      <text x="12" y="34" fill="#10B981" font-size="13" font-weight="bold" font-family="monospace">ALERTE CONGESTION : ${alerte_congestion}</text>
    </g>
  </svg>
    """
    return scada_wrapper(f"Supervision Trafic & Mobilités SCADA : {name}", token, proto, svg)

# =====================================================================
# 11. SYNOPTIQUE SCADA UNIVERSEL AVEC PYRAMIDE CIM / PROCESS MIMIC
# =====================================================================
def build_generic_scada_synoptic(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    svg = """
  <svg viewBox="0 0 950 250" style="width:100%; height:auto; background:#0F141E; border-radius:8px; border:1px solid #1C2433;">
    <!-- Réacteur Process -->
    <rect x="100" y="40" width="180" height="160" rx="16" fill="#161F2E" stroke="#38BDF8" stroke-width="2"/>
    <text x="190" y="70" fill="#38BDF8" font-size="12" text-anchor="middle" font-weight="bold">UNITÉ DE PROCESS</text>
    <rect x="105" y="110" width="170" height="85" rx="8" fill="#0284C7" opacity="0.35"/>

    <!-- Alimentation -->
    <path d="M 20 100 L 100 100" fill="none" stroke="#10B981" stroke-width="6" class="pipe-flow"/>
    <text x="50" y="90" fill="#10B981" font-size="9">ALIMENTATION</text>

    <!-- Pompe centrifuge -->
    <path d="M 280 150 L 400 150" fill="none" stroke="#38BDF8" stroke-width="6" class="pipe-flow"/>
    <circle cx="430" cy="150" r="28" fill="#1E293B" stroke="#E2001A" stroke-width="2"/>
    <g transform="translate(430, 150)" class="scada-rotor-fast">
      <path d="M -18 -5 C -8 -15 8 -15 18 -5 C 8 15 -8 15 -18 -5 Z" fill="#E2001A"/>
    </g>
    <text x="430" y="195" fill="#E2001A" font-size="9" text-anchor="middle" font-weight="bold">POMPE PROCESS</text>

    <!-- Échangeur / Refroidisseur -->
    <path d="M 460 150 L 620 150" fill="none" stroke="#38BDF8" stroke-width="6" class="pipe-flow-fast"/>
    <rect x="620" y="90" width="120" height="110" rx="10" fill="#1A2234" stroke="#F59E0B" stroke-width="2"/>
    <text x="680" y="125" fill="#F59E0B" font-size="11" text-anchor="middle" font-weight="bold">ÉCHANGEUR</text>
    <text x="680" y="145" fill="#94A3B8" font-size="9" text-anchor="middle">Régulation PID</text>

    <!-- Distribution Usine -->
    <path d="M 740 150 L 880 150" fill="none" stroke="#10B981" stroke-width="6" class="pipe-flow"/>
    <polygon points="880,145 895,150 880,155" fill="#10B981"/>
    <text x="830" y="140" fill="#10B981" font-size="10" font-weight="bold">DISTRIBUTION</text>

    <!-- Callouts SCADA -->
    <g transform="translate(480, 45)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#38BDF8" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">PROCESS | RÉGULATION</text>
      <text x="10" y="31" fill="#38BDF8" font-size="12" font-weight="bold" font-family="monospace">${valeur:1}</text>
    </g>
    <g transform="translate(740, 45)">
      <rect width="145" height="38" rx="6" fill="#141A24" stroke="#10B981" stroke-width="1.5"/>
      <text x="10" y="16" fill="#94A3B8" font-size="9">BOUCLE | SÉCURITÉ</text>
      <text x="10" y="31" fill="#10B981" font-size="12" font-weight="bold" font-family="monospace">ACTIVE</text>
    </g>
  </svg>
    """
    return scada_wrapper(f"Synoptique SCADA Process : {name}", token, proto, svg)

# Table de dispatch des synoptiques par préfixe de modèle
SYNOPTIC_BUILDERS = {
    "ind_compressor": build_synoptic_compressor,
    "compressor": build_synoptic_compressor,
    "boiler": build_synoptic_steam_boiler,
    "chaudiere": build_synoptic_steam_boiler,
    "steam": build_synoptic_steam_boiler,
    "chiller": build_synoptic_chiller,
    "cold": build_synoptic_chiller,
    "froid": build_synoptic_chiller,
    "cta": build_synoptic_cta,
    "cleanroom": build_synoptic_cta,
    "tgbt": build_synoptic_tgbt,
    "transfo": build_synoptic_tgbt,
    "bess": build_synoptic_tgbt,
    "solar": build_synoptic_solar_pv,
    "pv": build_synoptic_solar_pv,
    "wind": build_synoptic_solar_pv,
    "water": build_synoptic_water_pump,
    "pump": build_synoptic_water_pump,
    "lighting": build_synoptic_city_lighting,
    "eclairage": build_synoptic_city_lighting,
    "telecom": build_synoptic_telecom,
    "shelter": build_synoptic_telecom,
    "traffic": build_synoptic_city_traffic,
    "city_traffic": build_synoptic_city_traffic,
    "mobilite": build_synoptic_city_traffic,
}
