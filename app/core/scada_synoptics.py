"""
Générateur de Schémas Synoptiques SCADA Industriels (SVG / HMI ISA-101) - Thème Light Eiffage.
Fournit des représentations graphiques vectorielles authentiques, animées et adaptées aux règles
des métiers de l'Industrie, du Bâtiment (GTB/GTC), des Réseaux d'Infrastructures et des Villes Intelligentes.
Chacun des 32 cas d'usage dispose de son propre synoptique vectoriel dédié et cohérent.
"""

from typing import Dict, Any, List, Optional
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig

def get_clean_var_key(variable: VariableConfig) -> str:
    """Extrait la clé métrique sans le préfixe unique équipement interne du simulateur."""
    if variable.device_id and variable.id.startswith(f"{variable.device_id}_"):
        return variable.id[len(variable.device_id) + 1:]
    return variable.id

def get_scada_synoptic_html(device: DeviceConfig, variables: List[VariableConfig], preset_id: Optional[str] = None) -> str:
    """
    Retourne le code HTML/SVG complet du synoptique SCADA correspondant au cas d'usage métier.
    Garantit l'adéquation exacte entre l'équipement et son synoptique SCADA.
    """
    dev_id = (preset_id or device.id or "").lower()
    dev_name = device.name or device.id
    token_str = device.token or "NON_RENSEIGNE"
    proto_str = device.protocol.value.upper() if hasattr(device.protocol, "value") else str(device.protocol).upper()

    var_map = {get_clean_var_key(v): v for v in variables}

    # 1. Recherche par correspondance exacte d'identifiant de preset
    if dev_id in SYNOPTIC_BUILDERS:
        return SYNOPTIC_BUILDERS[dev_id](dev_name, token_str, proto_str, variables, var_map)

    # 2. Recherche par correspondance de clés métier (ordonnées de la plus longue à la plus courte)
    for key in sorted(SYNOPTIC_BUILDERS.keys(), key=len, reverse=True):
        if key in dev_id:
            return SYNOPTIC_BUILDERS[key](dev_name, token_str, proto_str, variables, var_map)

    # Synoptique de secours générique SCADA process
    return build_generic_scada_synoptic(dev_name, token_str, proto_str, variables, var_map)


# =====================================================================
# STYLES CSS SCADA COMMONS (Thème Light - Contraste WCAG AA & Accents)
# =====================================================================
SCADA_CSS = """
<style>
  .scada-container {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 12px;
    padding: 16px;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: #0F172A;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
  }
  .scada-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #E2E8F0;
    padding-bottom: 10px;
    margin-bottom: 12px;
  }
  .scada-title {
    font-size: 13px;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .scada-live-indicator {
    display: inline-block;
    width: 9px;
    height: 9px;
    background: #059669;
    border-radius: 50%;
    box-shadow: 0 0 8px #10B981;
    animation: blink-live 1.5s infinite;
  }
  @keyframes blink-live {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.35; transform: scale(0.85); }
  }
  .scada-badge {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    color: #475569;
  }
  .scada-badge strong { color: #0284C7; }
  .scada-badge-token { color: #D97706; font-family: monospace; font-weight: 700; }
  
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
    """Enveloppe le contenu SVG dans le conteneur SCADA Light normalisé."""
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

def make_callout(x: int, y: int, label: str, value_expr: str, accent: str = "#0284C7", width: int = 155, height: int = 40) -> str:
    """Génère un bloc indicateur de métrique SCADA haute lisibilité en thème Light."""
    return f"""
    <g transform="translate({x}, {y})">
      <rect width="{width}" height="{height}" rx="6" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
      <rect width="4" height="{height}" rx="2" fill="{accent}"/>
      <text x="12" y="15" fill="#475569" font-size="9" font-weight="600">{label}</text>
      <text x="12" y="32" fill="#0F172A" font-size="13" font-weight="bold" font-family="monospace">{value_expr}</text>
    </g>"""


# =====================================================================
# 1. INDUSTRIE (01_industrie) - 8 CAS D'USAGE DÉDIÉS
# =====================================================================

def build_synoptic_compressor(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Centrale d'Air Comprimé Industrielle."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Filtre aspiration -->
    <rect x="30" y="90" width="60" height="70" rx="6" fill="#E2E8F0" stroke="#475569" stroke-width="2"/>
    <text x="60" y="125" fill="#1E293B" font-size="10" text-anchor="middle" font-weight="bold">FILTRE G4</text>
    <path d="M 90 125 L 180 125" fill="none" stroke="#0284C7" stroke-width="6" class="pipe-flow"/>

    <!-- Bloc Vis Bi-Étagé -->
    <rect x="180" y="60" width="130" height="130" rx="10" fill="#F1F5F9" stroke="#E2001A" stroke-width="2.5"/>
    <circle cx="245" cy="125" r="45" fill="#FFFFFF" stroke="#E2001A" stroke-width="1.5"/>
    <g transform="translate(245, 125)">
      <path class="scada-rotor" d="M -30 -5 C -15 -25 15 -25 30 -5 C 15 25 -15 25 -30 -5 Z" fill="#E2001A" opacity="0.85"/>
      <circle cx="0" cy="0" r="10" fill="#0F172A"/>
    </g>
    <text x="245" y="45" fill="#0F172A" font-size="11" text-anchor="middle" font-weight="bold">BLOC VIS BI-ÉTAGÉ</text>
    <rect x="210" y="200" width="70" height="45" rx="4" fill="#E2E8F0" stroke="#0284C7" stroke-width="1.5"/>
    <text x="245" y="227" fill="#0284C7" font-size="9" text-anchor="middle" font-weight="bold">MOTEUR 75kW</text>

    <!-- Séparateur Huile/Air -->
    <path d="M 310 125 L 410 125" fill="none" stroke="#D97706" stroke-width="6" class="pipe-flow-fast"/>
    <rect x="410" y="75" width="85" height="100" rx="8" fill="#F1F5F9" stroke="#D97706" stroke-width="2"/>
    <text x="452" y="105" fill="#B45309" font-size="10" text-anchor="middle" font-weight="bold">SÉPARATEUR</text>
    <rect x="420" y="145" width="65" height="20" rx="3" fill="#FDE68A" stroke="#D97706" stroke-width="1"/>

    <!-- Cuve Tampon 1000L -->
    <path d="M 495 125 L 590 125" fill="none" stroke="#059669" stroke-width="6" class="pipe-flow"/>
    <rect x="590" y="50" width="110" height="150" rx="20" fill="#F1F5F9" stroke="#0284C7" stroke-width="2.5"/>
    <text x="645" y="80" fill="#0284C7" font-size="11" text-anchor="middle" font-weight="bold">RÉSERVOIR AIR</text>
    <text x="645" y="95" fill="#64748B" font-size="9" text-anchor="middle">Capacité: 1000L</text>
    <line x1="645" y1="110" x2="645" y2="175" stroke="#059669" stroke-width="6" stroke-linecap="round"/>

    <!-- Sortie Réseau Usine -->
    <path d="M 700 125 L 860 125" fill="none" stroke="#059669" stroke-width="6" class="pipe-flow"/>
    <polygon points="860,120 875,125 860,130" fill="#059669"/>
    <text x="895" y="129" fill="#059669" font-size="11" font-weight="bold">USINE</text>

    <!-- Callouts SCADA Light -->
    {make_callout(720, 35, "PRESSION RÉSEAU", "${pression_reseau:1} bar", "#0284C7")}
    {make_callout(720, 85, "TEMP. VIS HUILE", "${temp_vis_huile:1} °C", "#D97706")}
    {make_callout(720, 135, "DÉBIT D'AIR", "${debit_air:0} Nm³/h", "#059669")}
    {make_callout(720, 185, "PUISSANCE ACTIVE", "${puissance_active:1} kW", "#E2001A")}
  </svg>
    """
    return scada_wrapper(f"Synoptique P&ID SCADA : {name}", token, proto, svg)

def build_synoptic_spindle(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Broche d'Usinage Grande Vitesse & Moteur Électrique."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Bâti Machine Outil -->
    <rect x="50" y="40" width="620" height="180" rx="10" fill="#F1F5F9" stroke="#334155" stroke-width="2"/>
    <text x="70" y="65" fill="#334155" font-size="11" font-weight="bold">CARTOUCHE DE BROCHE D'USINAGE (HSK-63)</text>

    <!-- Corps de broche & Chemise de refroidissement -->
    <rect x="90" y="80" width="360" height="100" rx="6" fill="#E2E8F0" stroke="#475569" stroke-width="2"/>
    <rect x="90" y="85" width="360" height="15" fill="#BAE6FD" opacity="0.6"/>
    <rect x="90" y="160" width="360" height="15" fill="#BAE6FD" opacity="0.6"/>
    <text x="270" y="97" fill="#0369A1" font-size="9" text-anchor="middle">CHEMISE DE REFROIDISSEMENT LIQUIDE</text>

    <!-- Roulements Céramique Avant / Arrière -->
    <g transform="translate(140, 130)">
      <circle cx="0" cy="0" r="24" fill="#FFFFFF" stroke="#E2001A" stroke-width="2"/>
      <circle cx="0" cy="0" r="14" fill="#F1F5F9" stroke="#E2001A" stroke-width="1.5"/>
      <text x="0" y="38" fill="#E2001A" font-size="8" text-anchor="middle" font-weight="bold">PALIER AVANT</text>
    </g>
    <g transform="translate(390, 130)">
      <circle cx="0" cy="0" r="24" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
      <circle cx="0" cy="0" r="14" fill="#F1F5F9" stroke="#0284C7" stroke-width="1.5"/>
      <text x="0" y="38" fill="#0284C7" font-size="8" text-anchor="middle" font-weight="bold">PALIER ARRIÈRE</text>
    </g>

    <!-- Arbre Tournant Rotor -->
    <rect x="70" y="123" width="450" height="14" fill="#475569" stroke="#0F172A" stroke-width="1.5"/>
    <!-- Outil Fraise HSK -->
    <polygon points="50,115 70,123 70,137 50,145" fill="#E2001A"/>
    <text x="60" y="165" fill="#E2001A" font-size="8" text-anchor="middle" font-weight="bold">OUTIL HSK</text>

    <!-- Moteur Synchrone Intégré -->
    <rect x="200" y="105" width="140" height="50" rx="4" fill="#CBD5E1" stroke="#334155" stroke-width="1.5"/>
    <text x="270" y="134" fill="#0F172A" font-size="10" text-anchor="middle" font-weight="bold">STATOR 24kW</text>

    <!-- Capteur Accéléromètre Piézoélectrique (Vibrations) -->
    <g transform="translate(140, 65)">
      <rect x="-10" y="0" width="20" height="15" fill="#E2001A" rx="2"/>
      <line x1="0" y1="15" x2="0" y2="30" stroke="#E2001A" stroke-width="2"/>
      <text x="0" y="-4" fill="#E2001A" font-size="8" text-anchor="middle" font-weight="bold">VIBRATIONS RMS</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(710, 35, "VITESSE BROCHE", "${vitesse_rotation:0} RPM", "#0284C7")}
    {make_callout(710, 85, "VIBRATION PALIER", "${vibration_rms:2} mm/s", "#E2001A")}
    {make_callout(710, 135, "TEMP. PALIER", "${temp_palier:1} °C", "#D97706")}
    {make_callout(710, 185, "COURANT STATOR", "${courant_moteur:1} A", "#059669")}
  </svg>
    """
    return scada_wrapper(f"Synoptique Broche CNC SCADA : {name}", token, proto, svg)

def build_synoptic_chiller(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Groupe Froid Industriel / Chiller Eau Glacée."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Boucle Frigorifique fermée -->
    <rect x="180" y="60" width="380" height="140" rx="16" fill="#F1F5F9" stroke="#0284C7" stroke-width="2"/>
    <text x="370" y="90" fill="#0284C7" font-size="12" text-anchor="middle" font-weight="bold">CHILLER INDUSTRIEL (R134a)</text>

    <!-- Évaporateur (Eau glacée) -->
    <rect x="195" y="110" width="90" height="70" rx="8" fill="#E0F2FE" stroke="#0284C7" stroke-width="2"/>
    <text x="240" y="140" fill="#0369A1" font-size="10" text-anchor="middle" font-weight="bold">ÉVAPORATEUR</text>
    <text x="240" y="155" fill="#0284C7" font-size="9" text-anchor="middle">7°C / 12°C</text>

    <!-- Compresseur à vis -->
    <circle cx="370" cy="145" r="30" fill="#FFFFFF" stroke="#E2001A" stroke-width="2"/>
    <g transform="translate(370,145)" class="scada-rotor">
      <path d="M -16 -4 C -8 -12 8 -12 16 -4 C 8 12 -8 12 -16 -4 Z" fill="#E2001A"/>
    </g>
    <text x="370" y="190" fill="#E2001A" font-size="9" text-anchor="middle" font-weight="bold">COMPRESSEUR</text>

    <!-- Condenseur Aéroréfrigérant -->
    <rect x="455" y="110" width="90" height="70" rx="8" fill="#FEE2E2" stroke="#DC2626" stroke-width="2"/>
    <text x="500" y="140" fill="#B91C1C" font-size="10" text-anchor="middle" font-weight="bold">CONDENSEUR</text>

    <!-- Circuit Eau Glacée Départ/Retour Usine -->
    <path d="M 50 120 L 195 120" fill="none" stroke="#0284C7" stroke-width="6" class="pipe-flow"/>
    <text x="120" y="110" fill="#0369A1" font-size="10" font-weight="bold">RETOUR USINE (12°C)</text>
    <path d="M 195 160 L 50 160" fill="none" stroke="#0369A1" stroke-width="6" class="pipe-flow-fast"/>
    <text x="120" y="180" fill="#0284C7" font-size="10" font-weight="bold">DÉPART EAU GLACÉE (7°C)</text>

    <!-- Callouts SCADA Light -->
    {make_callout(680, 35, "TEMP. DÉPART EAU", "${temp_eau_depart:1} °C", "#0284C7", 200)}
    {make_callout(680, 85, "TEMP. RETOUR EAU", "${temp_eau_retour:1} °C", "#0369A1", 200)}
    {make_callout(680, 135, "PRESSION HP FRIGO", "${pression_hp:1} bar", "#DC2626", 200)}
    {make_callout(680, 185, "COP INSTANTANÉ", "${cop_instantane:2}", "#059669", 200)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Frigorifique SCADA : {name}", token, proto, svg)

def build_synoptic_conveyor(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Ligne de Convoyage Automatisé & Poste Robotique."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Châssis Convoyeur -->
    <rect x="50" y="120" width="580" height="40" rx="6" fill="#E2E8F0" stroke="#334155" stroke-width="2"/>
    <line x1="50" y1="140" x2="630" y2="140" stroke="#64748B" stroke-width="3" stroke-dasharray="12,6" class="pipe-flow"/>

    <!-- Rouleaux d'Entraînement -->
    <circle cx="80" cy="140" r="16" fill="#CBD5E1" stroke="#334155" stroke-width="2"/>
    <circle cx="340" cy="140" r="16" fill="#CBD5E1" stroke="#334155" stroke-width="2"/>
    <circle cx="600" cy="140" r="16" fill="#CBD5E1" stroke="#334155" stroke-width="2"/>

    <!-- Cartons / Pièces en transit -->
    <rect x="130" y="98" width="35" height="22" rx="3" fill="#D97706" stroke="#B45309" stroke-width="1.5"/>
    <rect x="230" y="98" width="35" height="22" rx="3" fill="#D97706" stroke="#B45309" stroke-width="1.5"/>
    <rect x="440" y="98" width="35" height="22" rx="3" fill="#059669" stroke="#047857" stroke-width="1.5"/>

    <!-- Cellule Photoélectrique & Bras Robotique Pick & Place -->
    <g transform="translate(340, 50)">
      <rect x="-15" y="0" width="30" height="20" rx="3" fill="#E2001A" stroke="#B91C1C" stroke-width="1"/>
      <line x1="0" y1="20" x2="0" y2="70" stroke="#E2001A" stroke-width="2" stroke-dasharray="4,2"/>
      <text x="0" y="-6" fill="#E2001A" font-size="8" text-anchor="middle" font-weight="bold">CELLULE DÉTECTION</text>
    </g>

    <!-- Moteur Réducteur d'Entraînement 5.5kW -->
    <rect x="580" y="170" width="70" height="45" rx="4" fill="#F1F5F9" stroke="#0284C7" stroke-width="2"/>
    <text x="615" y="195" fill="#0284C7" font-size="9" text-anchor="middle" font-weight="bold">MOTORÉDUCTEUR</text>
    <text x="615" y="207" fill="#64748B" font-size="8" text-anchor="middle">5.5 kW VFD</text>

    <!-- Callouts SCADA Light -->
    {make_callout(680, 40, "CADENCE PIÈCES", "${cadence_pieces:0} pcs/min", "#0284C7", 200)}
    {make_callout(680, 100, "VITESSE BANDE", "${vitesse_bande:2} m/s", "#D97706", 200)}
    {make_callout(680, 160, "RENDEMENT TRS (OEE)", "${taux_rendement_trs:1} %", "#059669", 200)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Convoyage Industriel SCADA : {name}", token, proto, svg)

def build_synoptic_cold_room(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Chambre Froide Négative Industrielle (-20°C)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Enceinte Frigorifique Isolée -->
    <rect x="60" y="40" width="560" height="180" rx="12" fill="#F1F5F9" stroke="#0284C7" stroke-width="3"/>
    <text x="80" y="65" fill="#0369A1" font-size="11" font-weight="bold">ENCEINTE ISOTHERME NÉGATIVE (-20°C / PANNEAUX PIR 150mm)</text>

    <!-- Porte Isotherme avec Contacteur -->
    <rect x="580" y="75" width="20" height="110" rx="2" fill="#E2E8F0" stroke="#E2001A" stroke-width="2"/>
    <text x="590" y="200" fill="#E2001A" font-size="8" text-anchor="middle" font-weight="bold">PORTE</text>

    <!-- Évaporateur Plafonnier avec Ventilateurs -->
    <rect x="100" y="70" width="220" height="60" rx="6" fill="#E0F2FE" stroke="#0284C7" stroke-width="2"/>
    <text x="210" y="95" fill="#0369A1" font-size="10" text-anchor="middle" font-weight="bold">ÉVAPORATEUR PLAFONNIER</text>
    <circle cx="140" cy="115" r="10" fill="#FFFFFF" stroke="#0284C7"/>
    <circle cx="210" cy="115" r="10" fill="#FFFFFF" stroke="#0284C7"/>
    <circle cx="280" cy="115" r="10" fill="#FFFFFF" stroke="#0284C7"/>

    <!-- Résistances de Dégivrage Électrique -->
    <line x1="110" y1="125" x2="310" y2="125" stroke="#D97706" stroke-width="3" stroke-dasharray="6,4"/>
    <text x="210" y="145" fill="#D97706" font-size="8" text-anchor="middle" font-weight="bold">RÉSISTANCES DÉGIVRAGE</text>

    <!-- Palettes de stockage produits surgelés -->
    <g transform="translate(140, 160)">
      <rect x="0" y="0" width="60" height="45" fill="#CBD5E1" stroke="#475569" stroke-width="1.5"/>
      <rect x="80" y="0" width="60" height="45" fill="#CBD5E1" stroke="#475569" stroke-width="1.5"/>
      <rect x="160" y="0" width="60" height="45" fill="#CBD5E1" stroke="#475569" stroke-width="1.5"/>
      <text x="150" y="30" fill="#334155" font-size="9" text-anchor="middle">STOCK SURGELÉ</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(670, 35, "TEMP. AMBIANTE", "${temp_chambre_froide:1} °C", "#0284C7", 220)}
    {make_callout(670, 85, "TEMP. ÉVAPORATEUR", "${temp_evaporateur:1} °C", "#0369A1", 220)}
    {make_callout(670, 135, "PUISSANCE GROUPE", "${puissance_groupe_kw:1} kW", "#D97706", 220)}
    {make_callout(670, 185, "STATUT SYSTÈME", "${statut_degivrage}", "#059669", 220)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Chambre Froide SCADA : {name}", token, proto, svg)

def build_synoptic_steam_boiler(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Chaudière Industrielle Vapeur (P&ID)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Bâche alimentaire (Eau) -->
    <rect x="40" y="80" width="90" height="110" rx="10" fill="#F1F5F9" stroke="#0284C7" stroke-width="2"/>
    <text x="85" y="105" fill="#0284C7" font-size="10" text-anchor="middle" font-weight="bold">BÂCHE ALIM.</text>
    <rect x="45" y="130" width="80" height="55" rx="4" fill="#BAE6FD" opacity="0.6"/>
    
    <!-- Pompe alimentaire HP -->
    <path d="M 130 150 L 190 150" fill="none" stroke="#0284C7" stroke-width="5" class="pipe-flow"/>
    <circle cx="210" cy="150" r="20" fill="#FFFFFF" stroke="#059669" stroke-width="2"/>
    <text x="210" y="185" fill="#059669" font-size="9" text-anchor="middle" font-weight="bold">POMPE HP</text>

    <!-- Corps de Chaudière Tubulaire -->
    <path d="M 230 150 L 310 150" fill="none" stroke="#0284C7" stroke-width="5" class="pipe-flow"/>
    <rect x="310" y="45" width="280" height="160" rx="20" fill="#F1F5F9" stroke="#DC2626" stroke-width="2.5"/>
    <text x="450" y="75" fill="#0F172A" font-size="13" text-anchor="middle" font-weight="bold">CHAUDIÈRE TUBE DE FUMÉES</text>

    <!-- Brûleur Gaz Modulant -->
    <rect x="250" y="80" width="60" height="60" rx="6" fill="#FEE2E2" stroke="#DC2626" stroke-width="1.5"/>
    <polygon points="310,95 360,110 310,125" fill="#F59E0B" opacity="0.8"/>
    <text x="280" y="155" fill="#DC2626" font-size="9" text-anchor="middle" font-weight="bold">BRÛLEUR</text>

    <!-- Niveau d'Eau Chaudière -->
    <rect x="330" y="130" width="240" height="60" rx="6" fill="#BAE6FD" opacity="0.6"/>
    <!-- Ciel de Vapeur HP -->
    <rect x="330" y="85" width="240" height="40" fill="#E2E8F0" opacity="0.5"/>
    <text x="450" y="110" fill="#334155" font-size="11" text-anchor="middle" font-weight="bold">CIEL VAPEUR HP</text>

    <!-- Départ Collecteur Vapeur Usine -->
    <path d="M 450 45 L 450 20 L 640 20 L 640 90" fill="none" stroke="#DC2626" stroke-width="6" class="pipe-flow-fast"/>
    <rect x="610" y="90" width="60" height="80" rx="6" fill="#F1F5F9" stroke="#475569" stroke-width="2"/>
    <text x="640" y="125" fill="#0F172A" font-size="9" text-anchor="middle" font-weight="bold">BARILLET</text>

    <!-- Callouts SCADA Light -->
    {make_callout(710, 25, "PRESSION VAPEUR", "${pression_vapeur_bar:1} bar", "#DC2626", 200)}
    {make_callout(710, 75, "DÉBIT VAPEUR", "${debit_vapeur_th:1} t/h", "#0284C7", 200)}
    {make_callout(710, 125, "TEMP. FUMÉES", "${temp_fumees:0} °C", "#D97706", 200)}
    {make_callout(710, 175, "RENDEMENT", "${rendement_combustion_pct:1} %", "#059669", 200)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Thermique SCADA : {name}", token, proto, svg)

def build_synoptic_cleanroom_cta(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Salle Blanche ISO & Centrale d'Air Stérile."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Enceinte Salle Blanche ISO 5 / 7 -->
    <rect x="50" y="35" width="580" height="190" rx="12" fill="#F1F5F9" stroke="#0284C7" stroke-width="2.5"/>
    <text x="75" y="60" fill="#0369A1" font-size="11" font-weight="bold">SALLE BLANCHE STÉRILE (ISO 14644-1 / SURPRESSION CONTRÔLÉE)</text>

    <!-- Plafond Soufflant Filtres HEPA H14 -->
    <rect x="90" y="75" width="400" height="30" rx="4" fill="#E2E8F0" stroke="#0284C7" stroke-width="1.5"/>
    <line x1="90" y1="90" x2="490" y2="90" stroke="#0284C7" stroke-width="2" stroke-dasharray="6,4"/>
    <text x="290" y="87" fill="#0369A1" font-size="9" text-anchor="middle" font-weight="bold">PLAFOND FILTRANT FLUX LAMINAIRE HEPA H14 (99.995%)</text>

    <!-- Flux descendant d'air stérile -->
    <path d="M 150 110 L 150 170" stroke="#0284C7" stroke-width="4" stroke-dasharray="6,4" class="pipe-flow"/>
    <path d="M 290 110 L 290 170" stroke="#0284C7" stroke-width="4" stroke-dasharray="6,4" class="pipe-flow"/>
    <path d="M 430 110 L 430 170" stroke="#0284C7" stroke-width="4" stroke-dasharray="6,4" class="pipe-flow"/>

    <!-- Sas Personnel / Matériel Airlock -->
    <rect x="520" y="80" width="80" height="110" rx="4" fill="#E2E8F0" stroke="#475569" stroke-width="1.5"/>
    <text x="560" y="130" fill="#334155" font-size="9" text-anchor="middle" font-weight="bold">SAS AIRLOCK</text>
    <text x="560" y="145" fill="#64748B" font-size="8" text-anchor="middle">Interverrouillé</text>

    <!-- Compteur Optique de Particules Laser -->
    <g transform="translate(290, 185)">
      <rect x="-20" y="-15" width="40" height="25" rx="3" fill="#FFFFFF" stroke="#E2001A" stroke-width="1.5"/>
      <text x="0" y="2" fill="#E2001A" font-size="8" text-anchor="middle" font-weight="bold">PARTICULES</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "SURPRESSION SALLE", "${surpression_salle_pa:1} Pa", "#0284C7", 230)}
    {make_callout(660, 75, "RENOUVELLEMENT", "${renouvellement_air_volh:1} vol/h", "#059669", 230)}
    {make_callout(660, 125, "COMPTAGE 0.5µm", "${comptage_particules_05:0} part/m³", "#E2001A", 230)}
    {make_callout(660, 175, "HUMIDITÉ ABSOLUE", "${humidite_absolue_gkg:1} g/kg", "#D97706", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Salle Blanche SCADA : {name}", token, proto, svg)

def build_synoptic_thermal_furnace(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Four Industriel de Traitement Thermique Multi-Zones."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Enceinte Réfractaire du Four -->
    <rect x="50" y="45" width="580" height="170" rx="12" fill="#F1F5F9" stroke="#DC2626" stroke-width="2.5"/>
    <text x="80" y="70" fill="#991B1B" font-size="11" font-weight="bold">FOUR DE TRAITEMENT THERMIQUE INDUSTRIEL (ATMOSPHÈRE CONTRÔLÉE)</text>

    <!-- Zone 1 : Préchauffage -->
    <rect x="80" y="90" width="150" height="100" rx="6" fill="#FEF3C7" stroke="#D97706" stroke-width="2"/>
    <text x="155" y="115" fill="#B45309" font-size="10" text-anchor="middle" font-weight="bold">ZONE 1 : PRÉCHAUFFE</text>
    <polygon points="155,140 140,170 170,170" fill="#D97706" opacity="0.7"/>

    <!-- Zone 2 : Maintien Haute Température (Austénitisation) -->
    <rect x="260" y="90" width="150" height="100" rx="6" fill="#FEE2E2" stroke="#DC2626" stroke-width="2"/>
    <text x="335" y="115" fill="#B91C1C" font-size="10" text-anchor="middle" font-weight="bold">ZONE 2 : HAUTE TEMP</text>
    <polygon points="335,140 320,170 350,170" fill="#DC2626" opacity="0.8"/>

    <!-- Zone 3 : Recuit / Homogénéisation -->
    <rect x="440" y="90" width="150" height="100" rx="6" fill="#FFEDD5" stroke="#EA580C" stroke-width="2"/>
    <text x="515" y="115" fill="#C2410C" font-size="10" text-anchor="middle" font-weight="bold">ZONE 3 : RECUIT</text>
    <polygon points="515,140 500,170 530,170" fill="#EA580C" opacity="0.7"/>

    <!-- Rampe de Gaz Brûleurs -->
    <path d="M 50 205 L 610 205" fill="none" stroke="#D97706" stroke-width="4" stroke-dasharray="8,4"/>
    <text x="330" y="225" fill="#D97706" font-size="9" text-anchor="middle" font-weight="bold">RAMPE GAZ GAZ NATUREL / BRÛLEURS MODULANTS</text>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "TEMP. ZONE 1", "${temp_zone_1:0} °C", "#D97706", 230)}
    {make_callout(660, 75, "TEMP. ZONE 2 (HP)", "${temp_zone_2:0} °C", "#DC2626", 230)}
    {make_callout(660, 125, "TEMP. ZONE 3", "${temp_zone_3:0} °C", "#EA580C", 230)}
    {make_callout(660, 175, "DÉBIT GAZ", "${debit_gaz_combustible:1} Nm³/h", "#059669", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Four Traitement Thermique SCADA : {name}", token, proto, svg)


# =====================================================================
# 2. BÂTIMENTS & TERTIAIRE (02_tertiaire) - 8 CAS D'USAGE DÉDIÉS
# =====================================================================

def build_synoptic_cta(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Centrale de Traitement d'Air (CTA GTB / GTC)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <rect x="60" y="35" width="580" height="190" rx="12" fill="#F1F5F9" stroke="#334155" stroke-width="2.5"/>
    <line x1="60" y1="130" x2="640" y2="130" stroke="#CBD5E1" stroke-width="2" stroke-dasharray="4,4"/>

    <!-- Voie Soufflage -->
    <text x="80" y="60" fill="#0284C7" font-size="11" font-weight="bold">VOIE SOUFFLAGE AIR NEUF</text>
    <rect x="100" y="70" width="30" height="45" fill="#E2E8F0" stroke="#0284C7" stroke-width="1.5"/>
    <text x="115" y="97" fill="#475569" font-size="8" text-anchor="middle">REG.</text>

    <rect x="160" y="65" width="25" height="55" fill="#CBD5E1" stroke="#64748B" stroke-width="1.5"/>
    <text x="172" y="97" fill="#0F172A" font-size="8" text-anchor="middle" font-weight="bold">F7</text>

    <rect x="220" y="65" width="40" height="55" rx="4" fill="#E0F2FE" stroke="#0284C7" stroke-width="1.5"/>
    <text x="240" y="97" fill="#0284C7" font-size="8" text-anchor="middle" font-weight="bold">FROID</text>

    <rect x="290" y="65" width="40" height="55" rx="4" fill="#FEE2E2" stroke="#DC2626" stroke-width="1.5"/>
    <text x="310" y="97" fill="#DC2626" font-size="8" text-anchor="middle" font-weight="bold">CHAUD</text>

    <!-- Ventilateur Soufflage Plug-Fan EC -->
    <g transform="translate(420, 92)">
      <circle cx="0" cy="0" r="28" fill="#FFFFFF" stroke="#059669" stroke-width="2"/>
      <g class="scada-rotor">
        <path d="M -18 -5 C -8 -15 8 -15 18 -5 C 8 15 -8 15 -18 -5 Z" fill="#059669"/>
      </g>
      <circle cx="0" cy="0" r="6" fill="#0F172A"/>
      <text x="0" y="40" fill="#059669" font-size="8" text-anchor="middle" font-weight="bold">PLUG-FAN EC</text>
    </g>

    <!-- Soufflage vers bâtiment -->
    <path d="M 460 92 L 620 92" fill="none" stroke="#0284C7" stroke-width="7" class="pipe-flow"/>
    <text x="560" y="80" fill="#0284C7" font-size="9" font-weight="bold">BÂTIMENT</text>

    <!-- Voie Reprise -->
    <text x="80" y="155" fill="#64748B" font-size="11" font-weight="bold">VOIE REPRISE EXTRACTION</text>
    <path d="M 620 180 L 460 180" fill="none" stroke="#64748B" stroke-width="6" class="pipe-flow"/>

    <!-- Callouts SCADA Light -->
    {make_callout(670, 25, "TEMP. SOUFFLAGE", "${temp_soufflage:1} °C", "#0284C7", 220)}
    {make_callout(670, 75, "TEMP. REPRISE", "${temp_reprise:1} °C", "#059669", 220)}
    {make_callout(670, 125, "DÉBIT SOUFFLAGE", "${debit_soufflage:0} m³/h", "#D97706", 220)}
    {make_callout(670, 175, "PERTE PRESSION FILTRE", "${pression_filtre:0} Pa", "#DC2626", 220)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Aéraulique GTB : {name}", token, proto, svg)

def build_synoptic_tgbt(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """TGBT & Schéma Unifilaire Basse Tension (SLD)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <line x1="50" y1="50" x2="220" y2="50" stroke="#E2001A" stroke-width="5"/>
    <text x="50" y="35" fill="#E2001A" font-size="11" font-weight="bold">ARRIVÉE HTA / BT (400V TRIPHASÉ)</text>

    <!-- Disjoncteur Général Masterpact -->
    <g transform="translate(260, 50)">
      <rect x="-18" y="-18" width="36" height="36" fill="#FFFFFF" stroke="#059669" stroke-width="2"/>
      <line x1="-10" y1="-10" x2="10" y2="10" stroke="#059669" stroke-width="3"/>
      <line x1="-10" y1="10" x2="10" y2="-10" stroke="#059669" stroke-width="3"/>
      <text x="0" y="30" fill="#059669" font-size="9" text-anchor="middle" font-weight="bold">DISJONCTEUR DGBT</text>
    </g>

    <!-- Jeu de Barres Général Cuivre -->
    <line x1="380" y1="35" x2="380" y2="230" stroke="#D97706" stroke-width="6"/>
    <text x="395" y="35" fill="#B45309" font-size="11" font-weight="bold">JEU DE BARRES TGBT 1600A</text>

    <!-- Départs Force, CVC, Éclairage -->
    <g transform="translate(380, 75)">
      <line x1="0" y1="0" x2="120" y2="0" stroke="#0284C7" stroke-width="3"/>
      <text x="130" y="4" fill="#334155" font-size="10" font-weight="600">Départ CVC & Pompes (250A)</text>
    </g>
    <g transform="translate(380, 135)">
      <line x1="0" y1="0" x2="120" y2="0" stroke="#0284C7" stroke-width="3"/>
      <text x="130" y="4" fill="#334155" font-size="10" font-weight="600">Départ Informatique / Onduleur (160A)</text>
    </g>
    <g transform="translate(380, 195)">
      <line x1="0" y1="0" x2="120" y2="0" stroke="#0284C7" stroke-width="3"/>
      <text x="130" y="4" fill="#334155" font-size="10" font-weight="600">Départ Éclairage DALI (63A)</text>
    </g>

    <!-- Callouts Électriques Light -->
    {make_callout(670, 25, "PUISSANCE TOTALE", "${puissance_totale_kw:1} kW", "#E2001A", 220)}
    {make_callout(670, 75, "COS PHI (FACTEUR)", "${facteur_puissance:2}", "#059669", 220)}
    {make_callout(670, 125, "TENSION PH-PH", "${tension_l1_l2:0} V", "#0284C7", 220)}
    {make_callout(670, 175, "EAU GÉNÉRALE", "${debit_eau_general:1} m³/h", "#D97706", 220)}
  </svg>
    """
    return scada_wrapper(f"Schéma Unifilaire SCADA : {name}", token, proto, svg)

def build_synoptic_qai(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Station Qualité de l'Air Intérieur (QAI & Confort Bâtiment)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Boîtier Station QAI -->
    <rect x="70" y="40" width="550" height="180" rx="16" fill="#F1F5F9" stroke="#059669" stroke-width="2.5"/>
    <text x="100" y="65" fill="#065F46" font-size="11" font-weight="bold">SONDE QUALITÉ D'AIR INTÉRIEUR (QAI / NORME BÂTIMENT VERT BREEAM-WELL)</text>

    <!-- Capteur NDIR CO2 -->
    <g transform="translate(130, 95)">
      <rect width="110" height="85" rx="8" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
      <circle cx="55" cy="35" r="18" fill="#E0F2FE" stroke="#0284C7"/>
      <text x="55" y="39" fill="#0284C7" font-size="10" text-anchor="middle" font-weight="bold">CO₂</text>
      <text x="55" y="70" fill="#334155" font-size="9" text-anchor="middle">NDIR INFRAROUGE</text>
    </g>

    <!-- Capteur PM2.5 / PM10 (Laser) -->
    <g transform="translate(285, 95)">
      <rect width="110" height="85" rx="8" fill="#FFFFFF" stroke="#DC2626" stroke-width="2"/>
      <circle cx="55" cy="35" r="18" fill="#FEE2E2" stroke="#DC2626"/>
      <text x="55" y="39" fill="#DC2626" font-size="10" text-anchor="middle" font-weight="bold">PM</text>
      <text x="55" y="70" fill="#334155" font-size="9" text-anchor="middle">DIFFUSION LASER</text>
    </g>

    <!-- Capteur COV Totaux (MOx) -->
    <g transform="translate(440, 95)">
      <rect width="110" height="85" rx="8" fill="#FFFFFF" stroke="#D97706" stroke-width="2"/>
      <circle cx="55" cy="35" r="18" fill="#FEF3C7" stroke="#D97706"/>
      <text x="55" y="39" fill="#D97706" font-size="10" text-anchor="middle" font-weight="bold">VOC</text>
      <text x="55" y="70" fill="#334155" font-size="9" text-anchor="middle">SEMI-COND MOX</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "CONCENTRATION CO2", "${taux_co2:0} ppm", "#0284C7", 230)}
    {make_callout(660, 75, "PARTICULES PM2.5", "${particules_pm25:1} µg/m³", "#DC2626", 230)}
    {make_callout(660, 125, "COV TOTAUX", "${cov_totaux:0} ppb", "#D97706", 230)}
    {make_callout(660, 175, "TEMP. AMBIANTE", "${temp_ambiante:1} °C", "#059669", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique QAI Bâtiment SCADA : {name}", token, proto, svg)

def build_synoptic_heatpump(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """
    Pompe à Chaleur Réversible (PAC Air/Eau).
    Représentation thermodynamique authentique : Compresseur Scroll, Vanne 4 voies d'inversion,
    Échangeur à plaques côté hydraulique, Batterie ailetée extérieure et ventilateur axial.
    """
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Enceinte Unité Extérieure PAC -->
    <rect x="50" y="40" width="320" height="180" rx="12" fill="#F1F5F9" stroke="#0284C7" stroke-width="2.5"/>
    <text x="70" y="65" fill="#0369A1" font-size="11" font-weight="bold">GROUPE EXTÉRIEUR THERMODYNAMIQUE (R32)</text>

    <!-- Ventilateur Axial Hélicoïde -->
    <g transform="translate(130, 130)">
      <circle cx="0" cy="0" r="38" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
      <g class="scada-rotor">
        <path d="M -24 -6 C -12 -20 12 -20 24 -6 C 12 20 -12 20 -24 -6 Z" fill="#0284C7"/>
      </g>
      <circle cx="0" cy="0" r="8" fill="#0F172A"/>
      <text x="0" y="55" fill="#0284C7" font-size="8" text-anchor="middle" font-weight="bold">VENTILATEUR AXIAL</text>
    </g>

    <!-- Batterie Ailetée / Évaporateur Air -->
    <rect x="190" y="85" width="25" height="90" rx="3" fill="#BAE6FD" stroke="#0284C7" stroke-width="1.5"/>
    <line x1="190" y1="105" x2="215" y2="105" stroke="#0284C7" stroke-width="1.5"/>
    <line x1="190" y1="125" x2="215" y2="125" stroke="#0284C7" stroke-width="1.5"/>
    <line x1="190" y1="145" x2="215" y2="145" stroke="#0284C7" stroke-width="1.5"/>

    <!-- Compresseur Inverter Scroll -->
    <g transform="translate(290, 130)">
      <rect x="-30" y="-45" width="60" height="90" rx="14" fill="#FFFFFF" stroke="#DC2626" stroke-width="2"/>
      <path d="M -15 -10 C -5 -25 5 -25 15 -10 C 5 5 -5 5 -15 -10 Z" fill="#DC2626"/>
      <text x="0" y="25" fill="#DC2626" font-size="8" text-anchor="middle" font-weight="bold">SCROLL</text>
      <text x="0" y="38" fill="#475569" font-size="7" text-anchor="middle">INVERTER</text>
    </g>

    <!-- Vanne 4 Voies d'Inversion de Cycle -->
    <g transform="translate(420, 130)">
      <circle cx="0" cy="0" r="22" fill="#FEF3C7" stroke="#D97706" stroke-width="2"/>
      <path d="M -12 -12 L 12 12 M -12 12 L 12 -12" stroke="#D97706" stroke-width="3"/>
      <text x="0" y="-28" fill="#B45309" font-size="8" text-anchor="middle" font-weight="bold">VANNE 4 VOIES</text>
      <text x="0" y="36" fill="#B45309" font-size="7" text-anchor="middle">INVERSION CYCLE</text>
    </g>

    <!-- Échangeur à Plaques Condenseur / Hydro (Module Intérieur) -->
    <rect x="490" y="65" width="130" height="130" rx="10" fill="#F1F5F9" stroke="#E2001A" stroke-width="2.5"/>
    <text x="555" y="90" fill="#0F172A" font-size="10" text-anchor="middle" font-weight="bold">ÉCHANGEUR PLAQUES</text>
    <path d="M 510 110 L 600 110" stroke="#DC2626" stroke-width="5" class="pipe-flow"/>
    <text x="555" y="125" fill="#DC2626" font-size="8" text-anchor="middle">DÉPART CHAUD</text>
    <path d="M 600 160 L 510 160" stroke="#0284C7" stroke-width="5" class="pipe-flow-fast"/>
    <text x="555" y="175" fill="#0284C7" font-size="8" text-anchor="middle">RETOUR CHAUFFAGE</text>

    <!-- Callouts SCADA Light -->
    {make_callout(670, 25, "TEMP. DÉPART EAU", "${temp_depart_eau:1} °C", "#DC2626", 220)}
    {make_callout(670, 75, "PUISSANCE THERMIQUE", "${puissance_thermique_kw:1} kW", "#E2001A", 220)}
    {make_callout(670, 125, "PRESSION CIRCUIT", "${pression_circuit:1} bar", "#0284C7", 220)}
    {make_callout(670, 175, "MODE FONCTIONNEMENT", "${mode_chaud}", "#059669", 220)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Pompe à Chaleur SCADA : {name}", token, proto, svg)

def build_synoptic_fire_ssi(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Centrale de Sécurité Incendie (SSI Catégorie A / NF S 61-931)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Centrale ECS / CMSI -->
    <rect x="60" y="40" width="560" height="180" rx="12" fill="#F1F5F9" stroke="#E2001A" stroke-width="2.5"/>
    <text x="85" y="65" fill="#B91C1C" font-size="11" font-weight="bold">CENTRALE SÉCURITÉ INCENDIE (ECS / CMSI CONFORME NF S 61-931)</text>

    <!-- Boucle de Détection Optique de Fumée -->
    <g transform="translate(130, 110)">
      <circle cx="0" cy="0" r="26" fill="#FFFFFF" stroke="#DC2626" stroke-width="2"/>
      <circle cx="0" cy="0" r="10" fill="#FEE2E2" stroke="#DC2626"/>
      <text x="0" y="42" fill="#DC2626" font-size="9" text-anchor="middle" font-weight="bold">DÉTECTEUR FUMÉE</text>
    </g>

    <!-- Clapets Coupe-Feu Motorisés -->
    <g transform="translate(280, 110)">
      <rect x="-25" y="-25" width="50" height="50" fill="#FFFFFF" stroke="#D97706" stroke-width="2"/>
      <line x1="-25" y1="0" x2="25" y2="0" stroke="#D97706" stroke-width="3"/>
      <text x="0" y="42" fill="#D97706" font-size="9" text-anchor="middle" font-weight="bold">CLAPET COUPE-FEU</text>
    </g>

    <!-- Ventilateur Tourelle de Désenfumage 400°C/2h -->
    <g transform="translate(440, 110)">
      <rect x="-30" y="-30" width="60" height="60" rx="8" fill="#FFFFFF" stroke="#059669" stroke-width="2"/>
      <g class="scada-rotor-fast">
        <path d="M -15 -4 C -8 -12 8 -12 15 -4 C 8 12 -8 12 -15 -4 Z" fill="#059669"/>
      </g>
      <text x="0" y="45" fill="#059669" font-size="9" text-anchor="middle" font-weight="bold">DÉSENFUMAGE 400°/2h</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "OPACITÉ FUMÉE", "${opacite_fumee_obsm:2} Obs/m", "#DC2626", 230)}
    {make_callout(660, 75, "DÉBIT DÉSENFUMAGE", "${debit_desenfumage_m3h:0} m³/h", "#059669", 230)}
    {make_callout(660, 125, "ALIM SECOURS (AES)", "${tension_alim_secours:1} V", "#0284C7", 230)}
    {make_callout(660, 175, "STATUT CLAPETS", "${statut_clapets_coupe_feu}", "#D97706", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Sécurité Incendie SCADA : {name}", token, proto, svg)

def build_synoptic_dali_lighting(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Gestion d'Éclairage DALI-2 & Détection Présence Bâtiment."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Contrôleur DALI Passerelle IP/BACnet -->
    <rect x="60" y="45" width="560" height="170" rx="12" fill="#F1F5F9" stroke="#D97706" stroke-width="2.5"/>
    <text x="85" y="70" fill="#B45309" font-size="11" font-weight="bold">GESTION ÉCLAIRAGE ARCHITECTURAL DALI-2 / DÉTECTION PIR MULTI-CAPTEURS</text>

    <!-- Bus 2 Fils DALI -->
    <line x1="90" y1="120" x2="580" y2="120" stroke="#D97706" stroke-width="4" stroke-dasharray="8,4"/>
    <text x="90" y="110" fill="#D97706" font-size="9" font-weight="bold">BUS DALI-2 (64 ADRESSES)</text>

    <!-- Luminaires LED DALI Adressables -->
    <g transform="translate(180, 120)">
      <polygon points="-25,-25 25,-25 15,10 -15,10" fill="#FEF3C7" stroke="#D97706" stroke-width="1.5"/>
      <polygon points="-35,25 35,25 15,10 -15,10" fill="#FDE68A" opacity="0.4"/>
      <text x="0" y="-32" fill="#B45309" font-size="8" text-anchor="middle" font-weight="bold">LUM. DALI #01</text>
    </g>
    <g transform="translate(340, 120)">
      <polygon points="-25,-25 25,-25 15,10 -15,10" fill="#FEF3C7" stroke="#D97706" stroke-width="1.5"/>
      <polygon points="-35,25 35,25 15,10 -15,10" fill="#FDE68A" opacity="0.4"/>
      <text x="0" y="-32" fill="#B45309" font-size="8" text-anchor="middle" font-weight="bold">LUM. DALI #02</text>
    </g>

    <!-- Capteur PIR Présence + Luxmètre -->
    <g transform="translate(500, 120)">
      <circle cx="0" cy="0" r="22" fill="#FFFFFF" stroke="#059669" stroke-width="2"/>
      <text x="0" y="4" fill="#059669" font-size="8" text-anchor="middle" font-weight="bold">PIR + LUX</text>
      <text x="0" y="-28" fill="#059669" font-size="8" text-anchor="middle" font-weight="bold">DÉTECTEUR</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "ÉCLAIREMENT", "${eclairement_lux:0} lux", "#D97706", 230)}
    {make_callout(660, 75, "TAUX PRÉSENCE", "${taux_presence_zone_pct:0} %", "#059669", 230)}
    {make_callout(660, 125, "GRADATION DALI", "${gradation_dali_pct:0} %", "#0284C7", 230)}
    {make_callout(660, 175, "PUISSANCE ÉCLAIRAGE", "${puissance_eclairage_w:0} W", "#E2001A", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Éclairage DALI SCADA : {name}", token, proto, svg)

def build_synoptic_thermal_meter(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Compteur d'Énergie Thermique (Calories / Réseau Urbain de Chaleur)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Conduite Départ Chaud -->
    <path d="M 60 70 L 600 70" fill="none" stroke="#DC2626" stroke-width="8" class="pipe-flow"/>
    <text x="70" y="55" fill="#DC2626" font-size="10" font-weight="bold">DÉPART EAU CHAUDE (ALLER)</text>
    <!-- Sonde Température Aller PT100 -->
    <g transform="translate(180, 70)">
      <rect x="-8" y="-30" width="16" height="25" fill="#FFFFFF" stroke="#DC2626" stroke-width="2"/>
      <text x="0" y="-36" fill="#DC2626" font-size="8" text-anchor="middle" font-weight="bold">SONDE ALLER</text>
    </g>

    <!-- Débitmètre Ultrasonique sur Retour -->
    <path d="M 600 180 L 60 180" fill="none" stroke="#0284C7" stroke-width="8" class="pipe-flow-fast"/>
    <text x="70" y="205" fill="#0284C7" font-size="10" font-weight="bold">RETOUR EAU REFROIDIE</text>
    <g transform="translate(320, 180)">
      <rect x="-35" y="-20" width="70" height="40" rx="8" fill="#FFFFFF" stroke="#0284C7" stroke-width="2.5"/>
      <text x="0" y="5" fill="#0284C7" font-size="9" text-anchor="middle" font-weight="bold">DÉBITMÈTRE US</text>
    </g>
    <!-- Sonde Température Retour PT100 -->
    <g transform="translate(480, 180)">
      <rect x="-8" y="5" width="16" height="25" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
      <text x="0" y="42" fill="#0284C7" font-size="8" text-anchor="middle" font-weight="bold">SONDE RETOUR</text>
    </g>

    <!-- Intégrateur / Calculateur Calorimétrique -->
    <g transform="translate(320, 105)">
      <rect x="-65" y="-25" width="130" height="50" rx="8" fill="#F1F5F9" stroke="#E2001A" stroke-width="2"/>
      <text x="0" y="-3" fill="#0F172A" font-size="10" text-anchor="middle" font-weight="bold">INTÉGRATEUR EN 1434</text>
      <text x="0" y="14" fill="#E2001A" font-size="8" text-anchor="middle" font-weight="bold">Q = m · Cp · ΔT</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "DÉBIT VOLUMIQUE", "${debit_volumique_m3h:2} m³/h", "#0284C7", 230)}
    {make_callout(660, 75, "ÉCART DE TEMP. (ΔT)", "${delta_t_deg:1} °C", "#D97706", 230)}
    {make_callout(660, 125, "PUISSANCE THERMIQUE", "${puissance_thermique_kw:1} kW", "#DC2626", 230)}
    {make_callout(660, 175, "ÉNERGIE CUMULÉE", "${energie_cumulee_mwh:2} MWh", "#059669", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Compteur Thermique SCADA : {name}", token, proto, svg)

def build_synoptic_access_flow(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Contrôle d'Accès & Comptage des Flux de Personnes."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Hall d'Accueil & Couloir Sécurisé -->
    <rect x="60" y="40" width="560" height="180" rx="12" fill="#F1F5F9" stroke="#0284C7" stroke-width="2.5"/>
    <text x="85" y="65" fill="#0369A1" font-size="11" font-weight="bold">CONTRÔLE D'ACCÈS DU BÂTIMENT & COMPTAGE DES FLUX TEMPS RÉEL</text>

    <!-- Tourniquet / Portillon d'Accès Rapide (Speed Gates) -->
    <g transform="translate(180, 130)">
      <rect x="-20" y="-45" width="40" height="90" rx="6" fill="#FFFFFF" stroke="#059669" stroke-width="2"/>
      <line x1="20" y1="0" x2="60" y2="0" stroke="#059669" stroke-width="4"/>
      <rect x="60" y="-45" width="40" height="90" rx="6" fill="#FFFFFF" stroke="#059669" stroke-width="2"/>
      <text x="40" y="-55" fill="#059669" font-size="9" text-anchor="middle" font-weight="bold">VOIE 1 (ENTRÉE)</text>
    </g>

    <g transform="translate(360, 130)">
      <rect x="-20" y="-45" width="40" height="90" rx="6" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
      <line x1="20" y1="0" x2="60" y2="0" stroke="#0284C7" stroke-width="4"/>
      <rect x="60" y="-45" width="40" height="90" rx="6" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
      <text x="40" y="-55" fill="#0284C7" font-size="9" text-anchor="middle" font-weight="bold">VOIE 2 (SORTIE)</text>
    </g>

    <!-- Capteur Vidéo Stéréoscopique 3D de Flux -->
    <g transform="translate(530, 90)">
      <rect x="-25" y="-15" width="50" height="30" rx="4" fill="#FFFFFF" stroke="#D97706" stroke-width="1.5"/>
      <circle cx="-12" cy="0" r="5" fill="#D97706"/>
      <circle cx="12" cy="0" r="5" fill="#D97706"/>
      <text x="0" y="32" fill="#B45309" font-size="8" text-anchor="middle" font-weight="bold">CAMÉRA 3D FLUX</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "FLUX ENTRÉES", "${flux_entrees_min:0} pers/min", "#059669", 230)}
    {make_callout(660, 75, "FLUX SORTIES", "${flux_sorties_min:0} pers/min", "#0284C7", 230)}
    {make_callout(660, 125, "JAUGE OCCUPATION", "${jauge_occupation_pct:0} %", "#D97706", 230)}
    {make_callout(660, 175, "REFUS D'ACCÈS", "${tentatives_refusees_h:0} /heure", "#DC2626", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Contrôle Accès SCADA : {name}", token, proto, svg)


# =====================================================================
# 3. INFRASTRUCTURES & RÉSEAUX (03_infrastructures) - 8 CAS D'USAGE
# =====================================================================

def build_synoptic_transfo_hta(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Transformateur HTA/BT Immergé dans l'Huile (20kV / 400V)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Cuve du Transformateur à Ailettes -->
    <rect x="80" y="55" width="280" height="150" rx="14" fill="#F1F5F9" stroke="#E2001A" stroke-width="2.5"/>
    <text x="220" y="80" fill="#0F172A" font-size="11" text-anchor="middle" font-weight="bold">TRANSFORMATEUR HTA/BT 1250 kVA</text>

    <!-- Ailettes de Refroidissement -->
    <line x1="80" y1="100" x2="360" y2="100" stroke="#CBD5E1" stroke-width="2"/>
    <line x1="80" y1="120" x2="360" y2="120" stroke="#CBD5E1" stroke-width="2"/>
    <line x1="80" y1="140" x2="360" y2="140" stroke="#CBD5E1" stroke-width="2"/>
    <line x1="80" y1="160" x2="360" y2="160" stroke="#CBD5E1" stroke-width="2"/>

    <!-- Traversées HTA Porcelaine (20 kV) -->
    <g transform="translate(130, 30)">
      <rect x="-10" y="0" width="20" height="25" fill="#FFFFFF" stroke="#E2001A" stroke-width="1.5"/>
      <text x="0" y="-6" fill="#E2001A" font-size="8" text-anchor="middle" font-weight="bold">HTA 20kV</text>
    </g>

    <!-- Traversées BT (400 V) -->
    <g transform="translate(310, 30)">
      <rect x="-10" y="0" width="20" height="25" fill="#FFFFFF" stroke="#0284C7" stroke-width="1.5"/>
      <text x="0" y="-6" fill="#0284C7" font-size="8" text-anchor="middle" font-weight="bold">BT 400V</text>
    </g>

    <!-- Relais de Protection DGPT2 (Gaz, Pression, Température) -->
    <g transform="translate(420, 100)">
      <rect x="0" y="0" width="110" height="70" rx="6" fill="#FFFFFF" stroke="#D97706" stroke-width="2"/>
      <text x="55" y="25" fill="#D97706" font-size="10" text-anchor="middle" font-weight="bold">RELAIS DGPT2</text>
      <text x="55" y="45" fill="#64748B" font-size="8" text-anchor="middle">Sécurité Huile</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "TEMP. HUILE", "${temp_huile_transfo:1} °C", "#E2001A", 230)}
    {make_callout(660, 75, "TAUX DE CHARGE", "${charge_transfo_pct:0} %", "#0284C7", 230)}
    {make_callout(660, 125, "PRESSION CUVE", "${pression_cuve:2} bar", "#D97706", 230)}
    {make_callout(660, 175, "TAUX HARMONIQUES THD", "${taux_thd:1} %", "#059669", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Transformateur HTA SCADA : {name}", token, proto, svg)

def build_synoptic_solar_pv(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Centrale Solaire Photovoltaïque & Onduleur MPPT."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <g transform="translate(80, 45)">
      <circle cx="0" cy="0" r="20" fill="#FEF3C7" stroke="#D97706" stroke-width="2"/>
      <text x="0" y="38" fill="#B45309" font-size="9" text-anchor="middle" font-weight="bold">PYRANOMÈTRE</text>
    </g>

    <!-- Panneaux Photovoltaïques -->
    <g transform="translate(160, 60)">
      <polygon points="0,60 25,10 115,10 90,60" fill="#E0F2FE" stroke="#0284C7" stroke-width="2"/>
      <polygon points="105,60 130,10 220,10 195,60" fill="#E0F2FE" stroke="#0284C7" stroke-width="2"/>
      <text x="110" y="85" fill="#334155" font-size="10" text-anchor="middle" font-weight="bold">CHAMP SOLAIRE 500kWc</text>
    </g>

    <!-- Ligne DC -->
    <path d="M 370 95 L 450 95" fill="none" stroke="#D97706" stroke-width="5" stroke-dasharray="6,3"/>
    <text x="410" y="85" fill="#B45309" font-size="9" text-anchor="middle" font-weight="bold">DC 820V</text>

    <!-- Onduleur Central MPPT -->
    <g transform="translate(510, 95)">
      <rect x="-45" y="-50" width="90" height="100" rx="8" fill="#FFFFFF" stroke="#059669" stroke-width="2.5"/>
      <text x="-20" y="-12" fill="#D97706" font-size="12" font-weight="bold">DC</text>
      <text x="12" y="22" fill="#0284C7" font-size="12" font-weight="bold">AC</text>
      <text x="0" y="65" fill="#059669" font-size="9" text-anchor="middle" font-weight="bold">ONDULEUR MPPT</text>
    </g>

    <path d="M 555 95 L 640 95" fill="none" stroke="#0284C7" stroke-width="5" class="pipe-flow"/>
    <text x="600" y="115" fill="#0284C7" font-size="9" font-weight="bold">RÉSEAU HTA</text>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "ENSOLEILLEMENT", "${ensoleillement:0} W/m²", "#D97706", 230)}
    {make_callout(660, 75, "PUISSANCE INJECTÉE", "${puissance_injection_kw:1} kW", "#059669", 230)}
    {make_callout(660, 125, "RENDEMENT ONDULEUR", "${rendement_onduleur:1} %", "#0284C7", 230)}
    {make_callout(660, 175, "TENSION DC STRING", "${tension_dc_string:0} V", "#E2001A", 230)}
  </svg>
    """
    return scada_wrapper(f"Supervision Solaire SCADA : {name}", token, proto, svg)

def build_synoptic_irve_charger(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Borne de Recharge Haute Puissance IRVE (Véhicules Électriques DC)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Borne DC Ultra-Fast Charge -->
    <rect x="100" y="40" width="220" height="180" rx="14" fill="#F1F5F9" stroke="#059669" stroke-width="2.5"/>
    <text x="210" y="70" fill="#065F46" font-size="11" text-anchor="middle" font-weight="bold">BORNE IRVE ULTRA-RAPIDE 150kW</text>

    <!-- Écran Tactile & Lecteur RFID -->
    <rect x="150" y="85" width="120" height="50" rx="4" fill="#FFFFFF" stroke="#0284C7" stroke-width="1.5"/>
    <text x="210" y="115" fill="#0284C7" font-size="10" text-anchor="middle" font-weight="bold">CHARGING IN PROGRESS</text>

    <!-- Câble de Recharge Combo CCS2 Refroidi Liquide -->
    <path d="M 320 140 Q 420 190 480 130" fill="none" stroke="#059669" stroke-width="8"/>
    <g transform="translate(480, 130)">
      <rect x="0" y="-15" width="45" height="30" rx="6" fill="#1E293B" stroke="#059669" stroke-width="2"/>
      <text x="22" y="4" fill="#FFFFFF" font-size="8" text-anchor="middle" font-weight="bold">CCS2</text>
    </g>

    <!-- Véhicule Électrique (Silhouette) -->
    <path d="M 520 150 L 550 120 L 620 120 L 640 150 Z" fill="#E2E8F0" stroke="#475569" stroke-width="2"/>
    <circle cx="545" cy="155" r="12" fill="#334155"/>
    <circle cx="615" cy="155" r="12" fill="#334155"/>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "PUISSANCE DE CHARGE", "${puissance_charge_kw:1} kW", "#059669", 230)}
    {make_callout(660, 75, "ÉNERGIE SESSION", "${energie_session_kwh:1} kWh", "#0284C7", 230)}
    {make_callout(660, 125, "COURANT DE CHARGE", "${courant_charge_a:1} A", "#D97706", 230)}
    {make_callout(660, 175, "STATUT CONNECTEUR", "${statut_connecteur}", "#E2001A", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Borne IRVE SCADA : {name}", token, proto, svg)

def build_synoptic_water_pump(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """
    Poste de Relevage des Eaux Usées (Assainissement).
    Représentation dédiée : Fosse humide béton, double pompe submersible P1/P2,
    sonde ultrason de niveau de bâche, et conduite PEHD de refoulement vers la STEP.
    """
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Fosse Humide Béton -->
    <rect x="80" y="40" width="350" height="180" rx="10" fill="#F1F5F9" stroke="#475569" stroke-width="3"/>
    <text x="255" y="70" fill="#1E293B" font-size="11" text-anchor="middle" font-weight="bold">FOSSE DE RELEVAGE BÉTON (EAUX USÉES)</text>

    <!-- Effluent / Niveau liquide -->
    <rect x="85" y="110" width="340" height="105" rx="6" fill="#A7F3D0" opacity="0.6"/>
    <!-- Sonde Ultrason Niveau -->
    <g transform="translate(200, 40)">
      <rect x="-15" y="0" width="30" height="20" fill="#D97706"/>
      <path d="M 0 20 L -15 50 M 0 20 L 15 50" stroke="#D97706" stroke-width="1.5" stroke-dasharray="3,3"/>
      <text x="0" y="-8" fill="#B45309" font-size="8" text-anchor="middle" font-weight="bold">SONDE ULTRASON</text>
    </g>

    <!-- Pompes Submersibles P1 et P2 -->
    <g transform="translate(160, 165)">
      <rect x="-20" y="-30" width="40" height="40" rx="6" fill="#FFFFFF" stroke="#059669" stroke-width="2"/>
      <text x="0" y="-8" fill="#059669" font-size="9" text-anchor="middle" font-weight="bold">POMPE 1</text>
    </g>
    <g transform="translate(320, 165)">
      <rect x="-20" y="-30" width="40" height="40" rx="6" fill="#FFFFFF" stroke="#64748B" stroke-width="2"/>
      <text x="0" y="-8" fill="#475569" font-size="9" text-anchor="middle" font-weight="bold">POMPE 2 (SECOURS)</text>
    </g>

    <!-- Conduite de Refoulement PEHD vers STEP -->
    <path d="M 160 135 L 160 90 L 520 90" fill="none" stroke="#059669" stroke-width="6" class="pipe-flow-fast"/>
    <text x="560" y="95" fill="#059669" font-size="10" font-weight="bold">REFOULEMENT STEP</text>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "NIVEAU BÂCHE", "${niveau_bache_m:2} m", "#0284C7", 230)}
    {make_callout(660, 75, "DÉBIT REFOULEMENT", "${debit_refoulement:1} m³/h", "#059669", 230)}
    {make_callout(660, 125, "CONSO POMPE", "${conso_pompe_kw:1} kW", "#D97706", 230)}
    {make_callout(660, 175, "ALARME DÉBORDEMENT", "${alarme_debordement}", "#E2001A", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Poste de Relevage Assainissement SCADA : {name}", token, proto, svg)

def build_synoptic_wind_turbine(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Aérogénérateur MW / Éolienne Haute Puissance."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Mât Béton / Acier Tubulaire -->
    <path d="M 230 230 L 245 80 L 255 80 L 270 230 Z" fill="#E2E8F0" stroke="#475569" stroke-width="2"/>
    
    <!-- Nacelle Supérieure -->
    <rect x="220" y="65" width="75" height="30" rx="8" fill="#F1F5F9" stroke="#0284C7" stroke-width="2"/>
    <text x="257" y="84" fill="#0369A1" font-size="8" text-anchor="middle" font-weight="bold">NACELLE 3MW</text>

    <!-- Rotor Éolien Tri-pales -->
    <g transform="translate(220, 80)">
      <circle cx="0" cy="0" r="10" fill="#0284C7"/>
      <g class="scada-rotor">
        <path d="M 0 0 L -60 -20 Q -80 0 -60 20 Z" fill="#0284C7" opacity="0.8"/>
        <path d="M 0 0 L 40 -60 Q 60 -70 50 -40 Z" fill="#0284C7" opacity="0.8"/>
        <path d="M 0 0 L 40 60 Q 60 70 50 40 Z" fill="#0284C7" opacity="0.8"/>
      </g>
    </g>

    <!-- Anémomètre de Nacelle -->
    <g transform="translate(290, 50)">
      <line x1="0" y1="15" x2="0" y2="0" stroke="#475569" stroke-width="2"/>
      <circle cx="0" cy="0" r="6" fill="#D97706"/>
      <text x="0" y="-8" fill="#B45309" font-size="8" text-anchor="middle">ANÉMOMÈTRE</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "VITESSE VENT", "${vitesse_vent_ms:1} m/s", "#0284C7", 230)}
    {make_callout(660, 75, "VITESSE ROTOR", "${vitesse_rotor_rpm:1} RPM", "#059669", 230)}
    {make_callout(660, 125, "PUISSANCE ACTIVE", "${puissance_active_mw:2} MW", "#E2001A", 230)}
    {make_callout(660, 175, "ORIENTATION (YAW)", "${angle_nacelle_yaw_deg:0} °", "#D97706", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Éolienne SCADA : {name}", token, proto, svg)

def build_synoptic_bess_storage(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Système de Stockage d'Énergie par Batteries (BESS Container)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Conteneur Isotherme 40ft BESS -->
    <rect x="60" y="45" width="560" height="170" rx="12" fill="#F1F5F9" stroke="#059669" stroke-width="2.5"/>
    <text x="85" y="70" fill="#065F46" font-size="11" font-weight="bold">CONTENEUR STOCKAGE BATTERIES LFP (BESS 2 MWh / CLIMATISATION REDONDANTE)</text>

    <!-- Racks Batteries Li-ion -->
    <g transform="translate(100, 90)">
      <rect x="0" y="0" width="70" height="100" rx="4" fill="#FFFFFF" stroke="#0284C7" stroke-width="1.5"/>
      <text x="35" y="55" fill="#0284C7" font-size="9" text-anchor="middle" font-weight="bold">RACK #01</text>
    </g>
    <g transform="translate(190, 90)">
      <rect x="0" y="0" width="70" height="100" rx="4" fill="#FFFFFF" stroke="#0284C7" stroke-width="1.5"/>
      <text x="35" y="55" fill="#0284C7" font-size="9" text-anchor="middle" font-weight="bold">RACK #02</text>
    </g>
    <g transform="translate(280, 90)">
      <rect x="0" y="0" width="70" height="100" rx="4" fill="#FFFFFF" stroke="#0284C7" stroke-width="1.5"/>
      <text x="35" y="55" fill="#0284C7" font-size="9" text-anchor="middle" font-weight="bold">RACK #03</text>
    </g>

    <!-- Onduleur Réversible PCS 4 Quadrants -->
    <g transform="translate(420, 90)">
      <rect x="0" y="0" width="130" height="100" rx="6" fill="#FFFFFF" stroke="#E2001A" stroke-width="2"/>
      <text x="65" y="45" fill="#E2001A" font-size="10" text-anchor="middle" font-weight="bold">CONVERTISSEUR PCS</text>
      <text x="65" y="65" fill="#334155" font-size="8" text-anchor="middle">Bi-directionnel AC/DC</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "ÉTAT DE CHARGE (SOC)", "${soc_pct:1} %", "#059669", 230)}
    {make_callout(660, 75, "TENSION DU PACK", "${tension_pack_v:1} V", "#0284C7", 230)}
    {make_callout(660, 125, "COURANT CHARGE/DÉCH.", "${courant_charge_decharge_a:1} A", "#E2001A", 230)}
    {make_callout(660, 175, "SANTÉ BATTERIE (SOH)", "${soh_pct:1} %", "#D97706", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Stockage BESS SCADA : {name}", token, proto, svg)

def build_synoptic_rail_switch(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Aiguillage & Signalisation Ferroviaire Sécurisée (SIL-4)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Voie Principale & Voie Déviée -->
    <line x1="60" y1="120" x2="600" y2="120" stroke="#334155" stroke-width="6"/>
    <line x1="60" y1="150" x2="600" y2="150" stroke="#334155" stroke-width="6"/>
    <!-- Déviation -->
    <path d="M 280 120 Q 420 80 600 60" fill="none" stroke="#334155" stroke-width="6"/>
    <text x="70" y="100" fill="#334155" font-size="10" font-weight="bold">VOIE PRINCIPALE</text>
    <text x="500" y="45" fill="#334155" font-size="10" font-weight="bold">VOIE DÉVIÉE</text>

    <!-- Moteur d'Aiguille Électromécanique -->
    <g transform="translate(260, 160)">
      <rect x="0" y="0" width="100" height="55" rx="6" fill="#F1F5F9" stroke="#E2001A" stroke-width="2"/>
      <text x="50" y="25" fill="#E2001A" font-size="9" text-anchor="middle" font-weight="bold">MOTEUR AIGUILLE</text>
      <text x="50" y="40" fill="#475569" font-size="8" text-anchor="middle">Contrôle de tringle</text>
    </g>

    <!-- Résistances de Réchauffage des Rails (Anti-gel) -->
    <line x1="280" y1="113" x2="400" y2="113" stroke="#D97706" stroke-width="3" stroke-dasharray="4,2"/>
    <text x="340" y="103" fill="#D97706" font-size="8" text-anchor="middle" font-weight="bold">RÉCHAUFFAGE RAIL</text>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "COURANT MOTEUR", "${courant_moteur_aiguille_a:1} A", "#E2001A", 230)}
    {make_callout(660, 75, "TEMPS MANŒUVRE", "${temps_manoeuvre_ms:0} ms", "#0284C7", 230)}
    {make_callout(660, 125, "TEMP. DU RAIL", "${temp_rail_rechauffage:1} °C", "#D97706", 230)}
    {make_callout(660, 175, "POSITION AIGUILLE", "${position_aiguille}", "#059669", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Aiguillage Ferroviaire SCADA : {name}", token, proto, svg)

def build_synoptic_water_treatment(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Bassin d'Aération & Épuration Biologique STEP (Traitement de l'Eau)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Bassin d'Aération Biologique -->
    <rect x="60" y="45" width="560" height="170" rx="12" fill="#F1F5F9" stroke="#0284C7" stroke-width="2.5"/>
    <text x="85" y="70" fill="#0369A1" font-size="11" font-weight="bold">BASSIN D'AÉRATION BIOLOGIQUE STEP (ÉLIMINATION CARBONE & AZOTE)</text>

    <!-- Liquide Biologique & Bulles d'Aération -->
    <rect x="70" y="90" width="540" height="115" rx="6" fill="#BAE6FD" opacity="0.5"/>
    <line x1="100" y1="190" x2="580" y2="190" stroke="#0284C7" stroke-width="4"/>
    <circle cx="160" cy="160" r="6" fill="#FFFFFF" stroke="#0284C7"/>
    <circle cx="280" cy="140" r="8" fill="#FFFFFF" stroke="#0284C7"/>
    <circle cx="400" cy="150" r="7" fill="#FFFFFF" stroke="#0284C7"/>
    <circle cx="500" cy="130" r="6" fill="#FFFFFF" stroke="#0284C7"/>

    <!-- Sonde d'Oxygène Dissous Optique (LDO) -->
    <g transform="translate(240, 60)">
      <rect x="-12" y="0" width="24" height="60" rx="4" fill="#FFFFFF" stroke="#059669" stroke-width="2"/>
      <text x="0" y="-8" fill="#059669" font-size="8" text-anchor="middle" font-weight="bold">SONDE O2 (LDO)</text>
    </g>

    <!-- Sonde pH / Redox -->
    <g transform="translate(440, 60)">
      <rect x="-12" y="0" width="24" height="60" rx="4" fill="#FFFFFF" stroke="#D97706" stroke-width="2"/>
      <text x="0" y="-8" fill="#D97706" font-size="8" text-anchor="middle" font-weight="bold">REDOX / pH</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "OXYGÈNE DISSOUS", "${oxygene_dissous_mgl:2} mg/L", "#059669", 230)}
    {make_callout(660, 75, "POTENTIEL REDOX", "${potentiel_redox_mv:0} mV", "#D97706", 230)}
    {make_callout(660, 125, "ACIDITÉ / pH", "${ph_eau:2} pH", "#0284C7", 230)}
    {make_callout(660, 175, "TURBIDITÉ", "${turbidite_ntu:1} NTU", "#E2001A", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Traitement Eau STEP SCADA : {name}", token, proto, svg)


# =====================================================================
# 4. VILLES INTELLIGENTES & TÉLÉCOMS (04_villes_telecoms) - 8 CAS D'USAGE
# =====================================================================

def build_synoptic_city_lighting(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Armoire d'Éclairage Public Connecté & Télégestion."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Armoire de Commande Rue -->
    <rect x="70" y="60" width="130" height="140" rx="8" fill="#F1F5F9" stroke="#D97706" stroke-width="2"/>
    <text x="135" y="90" fill="#B45309" font-size="10" text-anchor="middle" font-weight="bold">ARMOIRE ÉCLAIRAGE</text>
    <text x="135" y="110" fill="#64748B" font-size="9" text-anchor="middle">Horloge Astro</text>

    <!-- Candélabres LED sur voirie -->
    <g transform="translate(300, 80)">
      <line x1="0" y1="120" x2="0" y2="0" stroke="#64748B" stroke-width="4"/>
      <path d="M 0 0 Q 15 -10 30 -5" fill="none" stroke="#64748B" stroke-width="3"/>
      <polygon points="25,-5 35,-5 30,5" fill="#D97706"/>
      <polygon points="20,5 40,5 60,80 0,80" fill="#FDE68A" opacity="0.35"/>
    </g>

    <g transform="translate(480, 80)">
      <line x1="0" y1="120" x2="0" y2="0" stroke="#64748B" stroke-width="4"/>
      <path d="M 0 0 Q 15 -10 30 -5" fill="none" stroke="#64748B" stroke-width="3"/>
      <polygon points="25,-5 35,-5 30,5" fill="#D97706"/>
      <polygon points="20,5 40,5 60,80 0,80" fill="#FDE68A" opacity="0.35"/>
    </g>

    <!-- Ligne d'alimentation souterraine -->
    <line x1="200" y1="180" x2="580" y2="180" stroke="#D97706" stroke-width="4" stroke-dasharray="6,3"/>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "PUISSANCE ÉCLAIRAGE", "${puissance_eclairage_kw:1} kW", "#D97706", 230)}
    {make_callout(660, 75, "NIVEAU GRADATION", "${niveau_gradation_pct:0} %", "#059669", 230)}
    {make_callout(660, 125, "COURANT DE FUITE", "${courant_fuite_ma:1} mA", "#E2001A", 230)}
    {make_callout(660, 175, "ÉTAT PORTE ARMOIRE", "${alerte_porte_ouverte}", "#0284C7", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Smart Lighting SCADA : {name}", token, proto, svg)

def build_synoptic_city_weather(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Station Météo Urbaine & Surveillance Microclimat."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Mât Météo Urbain -->
    <line x1="280" y1="230" x2="280" y2="60" stroke="#475569" stroke-width="5"/>
    
    <!-- Anémomètre Girouette Ultrasonique -->
    <g transform="translate(280, 50)">
      <circle cx="0" cy="0" r="14" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
      <line x1="-12" y1="0" x2="12" y2="0" stroke="#0284C7" stroke-width="2"/>
      <line x1="0" y1="-12" x2="0" y2="12" stroke="#0284C7" stroke-width="2"/>
      <text x="0" y="-20" fill="#0284C7" font-size="8" text-anchor="middle" font-weight="bold">ANÉMOMÈTRE ULTRASON</text>
    </g>

    <!-- Pyranomètre / Indice UV -->
    <g transform="translate(220, 100)">
      <rect x="-15" y="-10" width="30" height="20" rx="3" fill="#FEF3C7" stroke="#D97706" stroke-width="1.5"/>
      <text x="0" y="24" fill="#B45309" font-size="8" text-anchor="middle" font-weight="bold">CAPTEUR UV</text>
    </g>

    <!-- Abri Météo Ventilé (Température & Humidité) -->
    <g transform="translate(340, 110)">
      <rect x="-20" y="-25" width="40" height="50" rx="4" fill="#FFFFFF" stroke="#059669" stroke-width="1.5"/>
      <line x1="-15" y1="-10" x2="15" y2="-10" stroke="#059669" stroke-width="1.5"/>
      <line x1="-15" y1="0" x2="15" y2="0" stroke="#059669" stroke-width="1.5"/>
      <line x1="-15" y1="10" x2="15" y2="10" stroke="#059669" stroke-width="1.5"/>
      <text x="0" y="38" fill="#059669" font-size="8" text-anchor="middle" font-weight="bold">ABRI TEMP/HR</text>
    </g>

    <!-- Pluviomètre à Augets Basculants -->
    <g transform="translate(180, 160)">
      <polygon points="-15,0 15,0 10,25 -10,25" fill="#E0F2FE" stroke="#0284C7" stroke-width="1.5"/>
      <text x="0" y="38" fill="#0284C7" font-size="8" text-anchor="middle" font-weight="bold">PLUVIOMÈTRE</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "TEMP. EXTÉRIEURE", "${temp_ext:1} °C", "#0284C7", 230)}
    {make_callout(660, 75, "VITESSE DU VENT", "${vitesse_vent_kmh:1} km/h", "#059669", 230)}
    {make_callout(660, 125, "HUMIDITÉ RELATIVE", "${humidite_ext:0} %", "#D97706", 230)}
    {make_callout(660, 175, "INDICE RAYONNEMENT UV", "${indice_uv:1}", "#E2001A", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Station Météo SCADA : {name}", token, proto, svg)

def build_synoptic_telecom(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Shelter Télécoms / Nœud Fibre Optique & Climatisation N+1."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Enceinte Shelter Sécurisé -->
    <rect x="70" y="40" width="550" height="180" rx="10" fill="#F1F5F9" stroke="#0284C7" stroke-width="2.5"/>
    <text x="180" y="65" fill="#0369A1" font-size="11" font-weight="bold">SHELTER TÉLÉCOMS / POP FIBRE OPTIQUE</text>

    <!-- Baies Serveurs / Switchs 19 pouces -->
    <rect x="110" y="80" width="65" height="120" rx="4" fill="#FFFFFF" stroke="#475569" stroke-width="1.5"/>
    <line x1="115" y1="100" x2="170" y2="100" stroke="#0284C7" stroke-width="2"/>
    <line x1="115" y1="120" x2="170" y2="120" stroke="#0284C7" stroke-width="2"/>
    <text x="142" y="190" fill="#334155" font-size="8" text-anchor="middle" font-weight="bold">BAIE IP</text>

    <rect x="200" y="80" width="65" height="120" rx="4" fill="#FFFFFF" stroke="#475569" stroke-width="1.5"/>
    <line x1="205" y1="100" x2="260" y2="100" stroke="#059669" stroke-width="2"/>
    <text x="232" y="190" fill="#334155" font-size="8" text-anchor="middle" font-weight="bold">OLT FIBRE</text>

    <!-- Onduleur UPS Double Conversion -->
    <rect x="290" y="80" width="70" height="120" rx="4" fill="#FFFFFF" stroke="#D97706" stroke-width="1.5"/>
    <text x="325" y="130" fill="#B45309" font-size="9" text-anchor="middle" font-weight="bold">UPS 40kVA</text>
    <text x="325" y="145" fill="#64748B" font-size="8" text-anchor="middle">BATTERIES</text>

    <!-- Climatisation Redondante N+1 -->
    <rect x="400" y="80" width="80" height="120" rx="4" fill="#E0F2FE" stroke="#0284C7" stroke-width="1.5"/>
    <text x="440" y="130" fill="#0369A1" font-size="9" text-anchor="middle" font-weight="bold">CLIM PRECISION</text>
    <text x="440" y="145" fill="#0284C7" font-size="8" text-anchor="middle">N+1 REDONDANT</text>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "CHARGE ONDULEUR", "${charge_onduleur_pct:0} %", "#059669", 230)}
    {make_callout(660, 75, "AUTONOMIE BATTERIE", "${autonomie_batterie_min:0} min", "#0284C7", 230)}
    {make_callout(660, 125, "TEMP. BAIE SERVEUR", "${temp_baie_serveur:1} °C", "#D97706", 230)}
    {make_callout(660, 175, "DÉTECTION INONDATION", "${detection_inondation}", "#E2001A", 230)}
  </svg>
    """
    return scada_wrapper(f"Supervision Shelter Télécoms SCADA : {name}", token, proto, svg)

def build_synoptic_city_traffic(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Comptage Trafic Routier, Mobilités Douces & Radars Doppler."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Chaussée Routière Principale -->
    <rect x="50" y="70" width="580" height="150" rx="8" fill="#E2E8F0" stroke="#94A3B8" stroke-width="2"/>

    <!-- Piste Cyclable Sécurisée (Bande verte normée) -->
    <rect x="50" y="70" width="580" height="35" rx="4" fill="#D1FAE5" stroke="#059669" stroke-width="1.5"/>
    <text x="70" y="92" fill="#065F46" font-size="10" font-weight="bold">VOIE CYCLABLE & TROTTINETTES (BIKE LANE)</text>
    <line x1="50" y1="105" x2="630" y2="105" stroke="#059669" stroke-width="2"/>

    <!-- Ligne médiane blanche pour flux VL -->
    <line x1="50" y1="160" x2="630" y2="160" stroke="#FFFFFF" stroke-width="4" stroke-dasharray="14,10" class="pipe-flow"/>
    <text x="70" y="140" fill="#334155" font-size="10" font-weight="bold">VOIE VL 1 (AMONT)</text>
    <text x="70" y="195" fill="#334155" font-size="10" font-weight="bold">VOIE VL 2 (AVAL / BUS)</text>

    <!-- Boucles à Induction Magnétiques au sol -->
    <rect x="220" y="115" width="45" height="35" rx="3" fill="#FFFFFF" stroke="#0284C7" stroke-width="1.5" stroke-dasharray="3,2"/>
    <rect x="220" y="170" width="45" height="35" rx="3" fill="#FFFFFF" stroke="#0284C7" stroke-width="1.5" stroke-dasharray="3,2"/>
    <text x="242" y="136" fill="#0284C7" font-size="8" text-anchor="middle" font-weight="bold">BOUCLE 1</text>
    <text x="242" y="191" fill="#0284C7" font-size="8" text-anchor="middle" font-weight="bold">BOUCLE 2</text>

    <!-- Portique Radar Doppler & Caméra IA -->
    <line x1="380" y1="50" x2="380" y2="220" stroke="#475569" stroke-width="4"/>
    <line x1="375" y1="50" x2="480" y2="50" stroke="#475569" stroke-width="4"/>
    <rect x="420" y="40" width="45" height="20" rx="4" fill="#E2001A" stroke="#FFFFFF" stroke-width="1.5"/>
    <text x="442" y="54" fill="#FFFFFF" font-size="8" text-anchor="middle" font-weight="bold">RADAR</text>
    <polygon points="430,62 455,62 490,135 395,135" fill="#0284C7" opacity="0.15"/>

    <!-- Feu Tricolore Urbain -->
    <g transform="translate(560, 40)">
      <rect width="26" height="65" rx="6" fill="#1E293B" stroke="#475569" stroke-width="2"/>
      <circle cx="13" cy="14" r="6" fill="#DC2626" opacity="0.3"/>
      <circle cx="13" cy="32" r="6" fill="#D97706" opacity="0.3"/>
      <circle cx="13" cy="50" r="6" fill="#059669" opacity="1" class="scada-live-indicator"/>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "DÉBIT VÉHICULES", "${debit_vehicules:0} véh/h", "#0284C7", 230)}
    {make_callout(660, 75, "DÉBIT CYCLISTES", "${debit_cyclistes:0} vélos/h", "#059669", 230)}
    {make_callout(660, 125, "VITESSE MOYENNE", "${vitesse_moyenne_kmh:1} km/h", "#D97706", 230)}
    {make_callout(660, 175, "ÉTAT DE CONGESTION", "${alerte_congestion}", "#E2001A", 230)}
  </svg>
    """
    return scada_wrapper(f"Supervision Trafic & Mobilités SCADA : {name}", token, proto, svg)

def build_synoptic_city_waste_bin(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Conteneur d'Apport Volontaire Déchets (PAV Connecté)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Sol / Voirie -->
    <line x1="60" y1="100" x2="600" y2="100" stroke="#334155" stroke-width="4"/>
    <text x="80" y="90" fill="#475569" font-size="9" font-weight="bold">NIVEAU CHAUSSÉE</text>

    <!-- Borne d'Apport Supérieure -->
    <rect x="230" y="45" width="120" height="55" rx="8" fill="#F1F5F9" stroke="#059669" stroke-width="2"/>
    <text x="290" y="75" fill="#065F46" font-size="10" text-anchor="middle" font-weight="bold">TRÉMIE DÉCHETS</text>

    <!-- Cuve Enterrée 4m³ -->
    <rect x="200" y="100" width="180" height="120" rx="6" fill="#E2E8F0" stroke="#475569" stroke-width="2.5"/>
    <text x="290" y="125" fill="#475569" font-size="10" text-anchor="middle" font-weight="bold">CUVE ENTERRÉE 4m³</text>
    
    <!-- Niveau de Remplissage (Effet liquide/solide) -->
    <rect x="205" y="150" width="170" height="65" rx="4" fill="#FED7AA" stroke="#EA580C" stroke-width="1.5"/>

    <!-- Sonde Ultrason Niveau + Température -->
    <g transform="translate(290, 100)">
      <circle cx="0" cy="5" r="8" fill="#D97706"/>
      <line x1="0" y1="13" x2="0" y2="45" stroke="#D97706" stroke-width="2" stroke-dasharray="3,2"/>
      <text x="0" y="-8" fill="#D97706" font-size="8" text-anchor="middle" font-weight="bold">ULTRASON</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "TAUX REMPLISSAGE", "${taux_remplissage_pct:0} %", "#EA580C", 230)}
    {make_callout(660, 75, "TEMP. INTERNE CUVE", "${temp_interne_cuve:1} °C", "#D97706", 230)}
    {make_callout(660, 125, "BATTERIE CAPTEUR", "${batterie_autonomie_pct:0} %", "#059669", 230)}
    {make_callout(660, 175, "ALARME INCENDIE", "${alerte_incendie}", "#E2001A", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Gestion Déchets SCADA : {name}", token, proto, svg)

def build_synoptic_city_smart_irrigation(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Arrosage Intelligent des Espaces Verts & Tensiométrie du Sol."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Sol Végétalisé / Gazon urbain -->
    <rect x="60" y="80" width="560" height="140" rx="8" fill="#DCFCE7" stroke="#059669" stroke-width="2"/>
    <text x="80" y="105" fill="#065F46" font-size="11" font-weight="bold">ESPACE VERT / GESTION RAISONNÉE DE L'EAU (TENSIOMÉTRIE)</text>

    <!-- Sonde Tensiométrique dans le Sol -->
    <g transform="translate(180, 110)">
      <rect x="-8" y="0" width="16" height="70" rx="4" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
      <text x="0" y="-8" fill="#0284C7" font-size="8" text-anchor="middle" font-weight="bold">SONDE SOL -10cm</text>
    </g>

    <!-- Électrovanne d'Arrosage Motorisée 24V -->
    <g transform="translate(360, 130)">
      <polygon points="-20,-15 0,0 -20,15" fill="#059669"/>
      <polygon points="20,-15 0,0 20,15" fill="#059669"/>
      <circle cx="0" cy="0" r="6" fill="#D97706"/>
      <text x="0" y="-22" fill="#059669" font-size="9" text-anchor="middle" font-weight="bold">ÉLECTROVANNE 24V</text>
    </g>

    <!-- Tuyère d'Arrosage Déployée -->
    <g transform="translate(510, 110)">
      <line x1="0" y1="30" x2="0" y2="0" stroke="#0284C7" stroke-width="4"/>
      <path d="M 0 0 Q -25 -20 -40 -10 M 0 0 Q 25 -20 40 -10" stroke="#0284C7" stroke-width="2" stroke-dasharray="3,2"/>
      <text x="0" y="-15" fill="#0284C7" font-size="8" text-anchor="middle" font-weight="bold">TUYÈRE</text>
    </g>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "TENSION MATRICIELLE", "${tension_matricielle_sol_cbar:1} cbar", "#0284C7", 230)}
    {make_callout(660, 75, "TEMP. DU SOL", "${temp_sol_10cm:1} °C", "#D97706", 230)}
    {make_callout(660, 125, "DÉBIT D'ARROSAGE", "${debit_arrosage_lmin:1} L/min", "#059669", 230)}
    {make_callout(660, 175, "CONSO EAU SESSION", "${conso_eau_session_m3:2} m³", "#E2001A", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Smart Irrigation SCADA : {name}", token, proto, svg)

def build_synoptic_city_acoustic_sensor(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Sonde Acoustique Urbaine & Surveillance des Nuisances Sonores."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Mât de Mesure Acoustique Classe 1 -->
    <line x1="260" y1="230" x2="260" y2="60" stroke="#475569" stroke-width="5"/>
    
    <!-- Microphone de Précision avec Boule Anti-Vent -->
    <g transform="translate(260, 50)">
      <circle cx="0" cy="0" r="18" fill="#F1F5F9" stroke="#E2001A" stroke-width="2"/>
      <circle cx="0" cy="0" r="8" fill="#E2001A"/>
      <text x="0" y="-24" fill="#E2001A" font-size="9" text-anchor="middle" font-weight="bold">MICRO CLASSE 1 (IEC 61672)</text>
    </g>

    <!-- Onde Acoustique Représentée -->
    <path d="M 290 50 Q 320 20 350 50 T 410 50" fill="none" stroke="#E2001A" stroke-width="2" stroke-dasharray="4,2"/>
    <path d="M 230 50 Q 200 20 170 50 T 110 50" fill="none" stroke="#E2001A" stroke-width="2" stroke-dasharray="4,2"/>

    <!-- Panneau Solaire Autonome -->
    <g transform="translate(260, 110)">
      <polygon points="-30,-15 30,-15 20,5 -20,5" fill="#E0F2FE" stroke="#0284C7" stroke-width="1.5"/>
      <text x="0" y="20" fill="#0284C7" font-size="8" text-anchor="middle" font-weight="bold">PANNEAU SOLAIRE</text>
    </g>

    <!-- Boîtier DSP Analyse Spectrale en Temps Réel -->
    <rect x="225" y="145" width="70" height="50" rx="4" fill="#FFFFFF" stroke="#334155" stroke-width="1.5"/>
    <text x="260" y="173" fill="#0F172A" font-size="8" text-anchor="middle" font-weight="bold">DSP 1/3 OCTAVE</text>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "NIVEAU SONORE (LAeq)", "${niveau_laeq_dba:1} dBA", "#E2001A", 230)}
    {make_callout(660, 75, "NIVEAU CRÊTE (LCpeak)", "${niveau_lcpeak_dbc:1} dBC", "#D97706", 230)}
    {make_callout(660, 125, "BATTERIE SOLAIRE", "${batterie_solaire_v:2} V", "#059669", 230)}
    {make_callout(660, 175, "SEUIL NOCTURNE DÉPASSÉ", "${depassement_seuil_nocturne}", "#0284C7", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique Sonde Acoustique SCADA : {name}", token, proto, svg)

def build_synoptic_city_structure_shm(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Surveillance Santé des Structures (SHM / Ouvrages d'Art & Ponts)."""
    svg = f"""
  <svg viewBox="0 0 950 260" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Tablier de Pont en Béton Précontraint / Ouvrage d'Art -->
    <rect x="60" y="75" width="560" height="45" rx="6" fill="#E2E8F0" stroke="#334155" stroke-width="2.5"/>
    <text x="340" y="103" fill="#0F172A" font-size="11" text-anchor="middle" font-weight="bold">TABLIER OUVRAGE D'ART / PILE BÉTON PRÉCONTRAINT (SHM)</text>

    <!-- Piles de Pont -->
    <rect x="140" y="120" width="50" height="90" fill="#CBD5E1" stroke="#475569" stroke-width="2"/>
    <rect x="490" y="120" width="50" height="90" fill="#CBD5E1" stroke="#475569" stroke-width="2"/>

    <!-- Inclinomètre MEMS Biaxial Haute Précision -->
    <g transform="translate(165, 60)">
      <circle cx="0" cy="0" r="12" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
      <line x1="-8" y1="0" x2="8" y2="0" stroke="#0284C7" stroke-width="2"/>
      <text x="0" y="-16" fill="#0284C7" font-size="8" text-anchor="middle" font-weight="bold">INCLINOMÈTRE</text>
    </g>

    <!-- Fissuromètre Électronique Corde Vibrante -->
    <g transform="translate(340, 130)">
      <line x1="-25" y1="0" x2="25" y2="0" stroke="#E2001A" stroke-width="3"/>
      <circle cx="-25" cy="0" r="4" fill="#E2001A"/>
      <circle cx="25" cy="0" r="4" fill="#E2001A"/>
      <text x="0" y="18" fill="#E2001A" font-size="8" text-anchor="middle" font-weight="bold">FISSUROMÈTRE (mm)</text>
    </g>

    <!-- Jauges de Déformation (Extensométrie Fibre Optique) -->
    <line x1="240" y1="115" x2="440" y2="115" stroke="#059669" stroke-width="3" stroke-dasharray="6,3"/>
    <text x="340" y="70" fill="#059669" font-size="8" text-anchor="middle" font-weight="bold">CORDE VIBRANTE / FIBRE BRAGG</text>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, "INCLINOMÉTRIE", "${inclinometrie_mrad:2} mrad", "#0284C7", 230)}
    {make_callout(660, 75, "ÉCARTEMENT FISSURE", "${ecartement_fissure_mm:3} mm", "#E2001A", 230)}
    {make_callout(660, 125, "DÉFORMATION (STRAIN)", "${deformation_microstrain:1} µε", "#059669", 230)}
    {make_callout(660, 175, "FRÉQUENCE PROPRE", "${frequence_propre_hz:2} Hz", "#D97706", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique SHM Ouvrage d'Art SCADA : {name}", token, proto, svg)


# =====================================================================
# 5. SYNOPTIQUE PROCESS GÉNÉRIQUE DE SECOURS (FALLBACK LIGHT)
# =====================================================================
def build_generic_scada_synoptic(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Synoptique de process générique de secours avec variables dynamiques réelles."""
    clean_vars = [get_clean_var_key(v) for v in vars_list]
    val1 = f"${{{clean_vars[0]}:1}}" if len(clean_vars) > 0 else "0.0"
    val2 = f"${{{clean_vars[1]}:1}}" if len(clean_vars) > 1 else "ACTIF"
    label1 = vars_list[0].name if len(vars_list) > 0 else "PROCESS ACTIF"
    label2 = vars_list[1].name if len(vars_list) > 1 else "RÉGULATION"

    svg = f"""
  <svg viewBox="0 0 950 250" style="width:100%; height:auto; background:#F8FAFC; border-radius:8px; border:1px solid #CBD5E1;">
    <!-- Réacteur Process -->
    <rect x="80" y="40" width="180" height="160" rx="16" fill="#F1F5F9" stroke="#0284C7" stroke-width="2"/>
    <text x="170" y="70" fill="#0284C7" font-size="12" text-anchor="middle" font-weight="bold">UNITÉ DE PROCESS</text>
    <rect x="85" y="110" width="170" height="85" rx="8" fill="#BAE6FD" opacity="0.4"/>

    <!-- Alimentation -->
    <path d="M 20 100 L 80 100" fill="none" stroke="#059669" stroke-width="6" class="pipe-flow"/>
    <text x="40" y="90" fill="#059669" font-size="9" font-weight="bold">ALIM.</text>

    <!-- Pompe centrifuge -->
    <path d="M 260 150 L 380 150" fill="none" stroke="#0284C7" stroke-width="6" class="pipe-flow"/>
    <circle cx="410" cy="150" r="28" fill="#FFFFFF" stroke="#E2001A" stroke-width="2"/>
    <g transform="translate(410, 150)" class="scada-rotor-fast">
      <path d="M -18 -5 C -8 -15 8 -15 18 -5 C 8 15 -8 15 -18 -5 Z" fill="#E2001A"/>
    </g>
    <text x="410" y="195" fill="#E2001A" font-size="9" text-anchor="middle" font-weight="bold">POMPE PROCESS</text>

    <!-- Échangeur / Refroidisseur -->
    <path d="M 440 150 L 580 150" fill="none" stroke="#0284C7" stroke-width="6" class="pipe-flow-fast"/>
    <rect x="580" y="90" width="120" height="110" rx="10" fill="#F1F5F9" stroke="#D97706" stroke-width="2"/>
    <text x="640" y="125" fill="#D97706" font-size="11" text-anchor="middle" font-weight="bold">ÉCHANGEUR</text>
    <text x="640" y="145" fill="#64748B" font-size="9" text-anchor="middle">Régulation PID</text>

    <!-- Distribution Usine -->
    <path d="M 700 150 L 820 150" fill="none" stroke="#059669" stroke-width="6" class="pipe-flow"/>
    <polygon points="820,145 835,150 820,155" fill="#059669"/>
    <text x="780" y="140" fill="#059669" font-size="10" font-weight="bold">DISTRIBUTION</text>

    <!-- Callouts SCADA Light -->
    {make_callout(660, 25, label1, val1, "#0284C7", 230)}
    {make_callout(660, 85, label2, val2, "#059669", 230)}
  </svg>
    """
    return scada_wrapper(f"Synoptique SCADA Process : {name}", token, proto, svg)


# =====================================================================
# TABLE DE DISPATCH EXHAUSTIVE DES 32 SYNOPTIQUES MÉTIERS
# =====================================================================
SYNOPTIC_BUILDERS = {
    # 01_industrie
    "ind_compressor": build_synoptic_compressor,
    "ind_spindle": build_synoptic_spindle,
    "ind_chiller": build_synoptic_chiller,
    "ind_conveyor": build_synoptic_conveyor,
    "ind_cold_room": build_synoptic_cold_room,
    "ind_steam_boiler": build_synoptic_steam_boiler,
    "ind_cleanroom_cta": build_synoptic_cleanroom_cta,
    "ind_thermal_furnace": build_synoptic_thermal_furnace,

    # 02_tertiaire
    "bldg_cta": build_synoptic_cta,
    "bldg_tgbt": build_synoptic_tgbt,
    "bldg_qai": build_synoptic_qai,
    "bldg_heatpump": build_synoptic_heatpump,
    "bldg_fire_ssi": build_synoptic_fire_ssi,
    "bldg_dali_lighting": build_synoptic_dali_lighting,
    "bldg_thermal_meter": build_synoptic_thermal_meter,
    "bldg_access_flow": build_synoptic_access_flow,

    # 03_infrastructures
    "infra_transfo_hta": build_synoptic_transfo_hta,
    "infra_solar_pv": build_synoptic_solar_pv,
    "infra_irve_charger": build_synoptic_irve_charger,
    "infra_water_pump": build_synoptic_water_pump,
    "infra_wind_turbine": build_synoptic_wind_turbine,
    "infra_bess_storage": build_synoptic_bess_storage,
    "infra_rail_switch": build_synoptic_rail_switch,
    "infra_water_treatment": build_synoptic_water_treatment,

    # 04_villes_telecoms
    "city_lighting": build_synoptic_city_lighting,
    "city_weather": build_synoptic_city_weather,
    "telecom_shelter": build_synoptic_telecom,
    "city_traffic": build_synoptic_city_traffic,
    "city_waste_bin": build_synoptic_city_waste_bin,
    "city_smart_irrigation": build_synoptic_city_smart_irrigation,
    "city_acoustic_sensor": build_synoptic_city_acoustic_sensor,
    "city_structure_shm": build_synoptic_city_structure_shm,

    # Mappings par mots-clés spécifiques (sans collisions ambiguës)
    "heatpump": build_synoptic_heatpump,
    "spindle": build_synoptic_spindle,
    "conveyor": build_synoptic_conveyor,
    "cleanroom": build_synoptic_cleanroom_cta,
    "furnace": build_synoptic_thermal_furnace,
    "irve": build_synoptic_irve_charger,
    "water_pump": build_synoptic_water_pump,
    "wind_turbine": build_synoptic_wind_turbine,
    "bess": build_synoptic_bess_storage,
    "rail_switch": build_synoptic_rail_switch,
    "water_treatment": build_synoptic_water_treatment,
    "weather": build_synoptic_city_weather,
    "waste_bin": build_synoptic_city_waste_bin,
    "irrigation": build_synoptic_city_smart_irrigation,
    "acoustic": build_synoptic_city_acoustic_sensor,
    "structure_shm": build_synoptic_city_structure_shm,
    "compressor": build_synoptic_compressor,
    "boiler": build_synoptic_steam_boiler,
    "chiller": build_synoptic_chiller,
    "tgbt": build_synoptic_tgbt,
    "solar": build_synoptic_solar_pv,
    "lighting": build_synoptic_city_lighting,
    "traffic": build_synoptic_city_traffic,
    "shelter": build_synoptic_telecom,
}
