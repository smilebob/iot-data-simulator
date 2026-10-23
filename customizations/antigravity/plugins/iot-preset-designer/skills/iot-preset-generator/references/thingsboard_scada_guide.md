# 🎨 Guide SCADA & Tableaux de Bord ThingsBoard 4.3

Ce guide détaille les conventions techniques pour concevoir des tableaux de bord ThingsBoard 4.3 professionnels pour les cas d'usage du simulateur IoT.

---

## 🏗️ 1. Architecture du Dashboard ThingsBoard 4.3

Un tableau de bord complet ThingsBoard 4.3 généré par le simulateur contient 5 zones fonctionnelles organisées sur une grille de 24 colonnes :

| Zone | Lignes (Row) | Largeur (Cols) | Widget FQN ThingsBoard | Rôle |
| :--- | :---: | :---: | :--- | :--- |
| **En-tête & Statut** | 0 | 24 | `system.cards.html_card` | Titre, statut de communication, protocole et identifiants techniques |
| **Synoptique SCADA Vectoriel** | 1 - 9 | 16 | `system.cards.html_value_card` | Représentation P&ID/SLD vectorielle SVG avec canalisations animées et tags dynamiques |
| **Commandes Interactives** | 1 - 9 | 8 | `system.single_switch` / `update_multiple_attributes` | Interrupteurs rotatifs et formulaires pour piloter consignes et modes de marche |
| **Jauges Numériques** | 10 - 15 | 24 | `system.digital_gauges.simple_gauge_justgage` | Jauges radiales ou linéaires pour grandeurs analogiques critiques |
| **Courbes Temps Réel** | 16 - 22 | 24 | `system.charts.basic_timeseries` | Graphique multi-courbes synchronisé affichant l'historique de télémétrie |

---

## ⚡ 2. Règle Critique de Data Binding ThingsBoard 4.3 (`html_value_card`)

Dans ThingsBoard 4.3, le widget de synoptique SCADA vectoriel (`system.cards.html_value_card`) injecte les données temps réel dans le code HTML/SVG via le motif `${cle}` :

> [!IMPORTANT]
> **Règle absolue ThingsBoard 4.3** :
> Pour qu'une balise `${pression_cuve}` ou `${temperature:2}` soit remplacée par sa valeur en direct dans ThingsBoard 4.3, le champ `label` du `dataKey` dans la datasource doit être **strictement égal au nom de la variable sans espaces** :
> ```json
> {
>   "name": "pression_cuve",
>   "label": "pression_cuve",
>   "type": "timeseries"
> }
> ```
> Si `label` est différent de `name` (par exemple `label: "Pression Cuve (bar)"`), ThingsBoard 4.3 échoue à résoudre `${pression_cuve}` et affiche le tag brut sans substitution !

---

## 🖌️ 3. Structure d'un Synoptique SCADA P&ID Vectoriel (SVG)

Le synoptique vectoriel doit être inséré dans `config.settings.cardHtml` :
```html
<div class="scada-container" style="background:#0F172A; border-radius:12px; padding:16px; color:#F8FAFC; position:relative; overflow:hidden;">
  <svg viewBox="0 0 800 450" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <!-- Animation de flux de fluide dans les tuyauteries -->
      <style>
        @keyframes pipeFlow {
          0% { stroke-dashoffset: 40; }
          100% { stroke-dashoffset: 0; }
        }
        .pipe-flow {
          stroke-dasharray: 8, 4;
          animation: pipeFlow 1.2s linear infinite;
        }
      </style>
      <linearGradient id="pipeGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#334155"/>
        <stop offset="50%" stop-color="#64748B"/>
        <stop offset="100%" stop-color="#1E293B"/>
      </linearGradient>
    </defs>

    <!-- Tuyauteries de process -->
    <path d="M 100 200 L 400 200 L 400 320 L 700 320" fill="none" stroke="#475569" stroke-width="8" stroke-linecap="round"/>
    <path d="M 100 200 L 400 200 L 400 320 L 700 320" fill="none" stroke="#38BDF8" stroke-width="3" class="pipe-flow"/>

    <!-- Équipement principal (ex: Cuve / Réacteur) -->
    <rect x="340" y="140" width="120" height="180" rx="16" fill="#1E293B" stroke="#0284C7" stroke-width="2"/>
    <text x="400" y="165" fill="#38BDF8" font-size="12" font-weight="bold" text-anchor="middle">CUVE H2</text>

    <!-- Étiquette de mesure dynamique -->
    <g transform="translate(355, 230)">
      <rect width="90" height="34" rx="6" fill="#0F172A" stroke="#38BDF8" stroke-width="1.2"/>
      <text x="45" y="14" fill="#94A3B8" font-size="9" text-anchor="middle">Pression</text>
      <text x="45" y="27" fill="#38BDF8" font-size="12" font-weight="bold" font-family="monospace" text-anchor="middle">${pression_h2:1} bar</text>
    </g>
  </svg>
</div>
```

---

## 🎛️ 4. Widgets de Contrôle Interactifs (ThingsBoard 4.3)

Pour permettre le pilotage bidirectionnel d'attributs (marche/arrêt, mode chaud/froid, consigne) :

1. **Interrupteur Booléen (`system.single_switch`)** :
   - FQN : `system.single_switch`
   - `bundleAlias` : `"control_widgets"`
   - `typeAlias` : `"single_switch"`
   - `type` : `"rpc"`
   - Configuration cible :
     ```json
     "settings": {
       "initialState": {
         "action": "GET_ATTRIBUTE",
         "getAttribute": { "scope": "SHARED_SCOPE", "key": "etat_marche" }
       },
       "onUpdateState": {
         "action": "SET_ATTRIBUTE",
         "setAttribute": { "scope": "SHARED_SCOPE", "key": "etat_marche" }
       }
     }
     ```

2. **Formulaire de Consigne Analogique (`system.input_widgets.update_multiple_attributes`)** :
   - FQN : `system.input_widgets.update_multiple_attributes`
   - `bundleAlias` : `"input_widgets"`
   - Permet à l'opérateur de modifier une valeur numérique (ex: `consigne_temperature`) stockée dans `SHARED_SCOPE` et lue par le simulateur en direct.
