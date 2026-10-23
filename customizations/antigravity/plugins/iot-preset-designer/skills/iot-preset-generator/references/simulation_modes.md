# 📈 Répertoire des 12 Modes de Simulation du Simulateur IoT

Ce document détaille les paramètres, formules et cas d'usage de chaque mode de génération disponible dans `VariableConfig.sim_mode`.

---

## 1. Signaux Déterministes & Périodiques (`MathConfig`)

### 1.1 `sine` & `cosine` (Ondes Sinusoïdales)
- **Comportement** : Oscillation fluide et continue entre `min_val` et `max_val` sur une période temporelle `period` (en secondes).
- **Formule interne** : $\text{val}(t) = \text{mid} + \text{amp} \cdot \sin(2\pi \cdot t / \text{period}) + \text{bruit}$
- **Cas d'usage** : Variations thermiques jour/nuit, cycles de respiration ou de ventilation, oscillation de vitesse moteur.
- **Paramètres clés** :
  - `min_val` (float) : Valeur basse de l'oscillation.
  - `max_val` (float) : Valeur haute de l'oscillation.
  - `period` (float, sec) : Durée d'un cycle complet (ex: `60.0` pour 1 min, `300.0` pour 5 min).
  - `noise_percent` (float, %) : Pourcentage de perturbation aléatoire gaussienne ajoutée au signal (ex: `1.0` pour 1 %).

### 1.2 `triangle` (Onde Triangulaire)
- **Comportement** : Montée linéaire constante jusqu'à `max_val` puis descente symétrique jusqu'à `min_val`.
- **Cas d'usage** : Balayage d'axe linéaire aller-retour, rampe de test cyclique d'actionneur.

### 1.3 `square` (Onde Carrée / Signal Créneau)
- **Comportement** : Bascule abrupte entre `min_val` (état bas) et `max_val` (état haut) à mi-période.
- **Cas d'usage** : Clignotement de balise, cadence pas-à-pas de transfert, cycle 50/50 d'injection.

### 1.4 `sawtooth` (Dent de Scie)
- **Comportement** : Montée linéaire progressive de `min_val` jusqu'à `max_val`, puis retombée instantanée à `min_val`.
- **Cas d'usage** : Cycle de montée en pression d'un compresseur avec purge rapide, niveau de trémie d'ensachage se vidant périodiquement.

### 1.5 `ramp` (Rampe Continue)
- **Comportement** : Évolution monotone pas à pas par incrément `step`.
- **Cas d'usage** : Montée en régime de préchauffage ou rampe de démarrage d'une turbine.

---

## 2. Signaux Stochastiques & Aléatoires (`MathConfig`)

### 2.1 `random_walk` (Marche Aléatoire / Dérive avec Inertie)
- **Comportement** : La valeur courante effectue un déplacement stochastique à chaque pas ($v_{t} = v_{t-1} + \Delta$), bornée strictement entre `min_val` et `max_val`.
- **Paramètres clés** :
  - `step` (float) : Amplitude maximale de variation par tick (ex: `0.05` pour des variations douces, `1.5` pour des à-coups).
  - `min_val`, `max_val` : Butées d'arrêt physique du système.
- **Cas d'usage** : Pression cuve d'air comprimé, température d'huile de palier, concentration de $CO_2$ ambiante, débit d'eau sanitaire.

### 2.2 `gaussian` (Bruit Blanc Gaussien)
- **Comportement** : Tirage aléatoire suivant une loi normale centrée sur `mean` avec un écart-type `std_dev`.
- **Paramètres clés** : `mean` (moyenne), `std_dev` (dispersion), `min_val`, `max_val`.
- **Cas d'usage** : Bruit de fond de capteur acoustique (dBA), micro-vibrations d'une broche en rotation, turbulences aérauliques.

---

## 3. Grandeurs Statiques & Attributs (`constant`)

### 3.1 `constant`
- **Comportement** : Émet une valeur fixe définie par `math_config.constant_val`.
- **Types supportés** : Nombre (`230.0`), Booléen (`true`/`false`), Texte (`"MODE_AUTO"`, `"RUNNING"`).
- **Cas d'usage** : Attributs ThingsBoard pilotables (`var_type: "attribute"`), consignes de température de régulation, mode de marche (Manuel / Auto / Arrêt).

---

## 4. Rejeu Temporel Échantillonné (`points_table`)

### 4.1 `points_table`
- **Comportement** : Rejoue une séquence de points horodatés `(timestamp, value)` avec interpolation linéaire continue.
- **Cas d'usage** : Rejeu d'un profil de charge électrique réel de 24h issu d'un compteur Enedis, courbe d'ensolleillement météo réelle, profil de vol ou de trajet GPS.

---

## 5. Moteur de Dépendance Causal & Intégrateurs (`physics.py`)

### 5.1 `derived` (Formules Mathématiques Dérivées)
- **Comportement** : Évalué à chaque tick après les grandeurs primaires. La valeur est calculée via une formule mathématique basée sur d'autres variables de l'équipement.
- **Sécurité CIS / OWASP** : Évaluation via analyseur AST (Abstract Syntax Tree) Python sécurisé. Aucun `eval()`, `exec()` ni appel de fonction système n'est autorisé.
- **Opérateurs & Fonctions Autorisés** :
  - Arithmétique : `+`, `-`, `*`, `/`, `**` (puissance), `%` (modulo), parenthèses `()`.
  - Fonctions : `abs()`, `min()`, `max()`, `round()`, `sqrt()`, `sin()`, `cos()`.
- **Exemples Industriels Réels** :
  - Puissance triphasée : `(u_tension * i_courant * 1.732 * cos_phi) / 1000`
  - Rendement compresseur : `(debit_effectif / debit_nominal) * 100`
  - Perte de charge : `pression_amont - pression_aval`
  - Débit calorifique : `debit_massique * 4.18 * (temp_depart - temp_retour)`

### 5.2 `integrator` (Intégrateur Continu dans le Temps)
- **Comportement** : Effectue une intégration d'Euler continue dans le temps de la grandeur source :
  $$\text{Index}(t) = \text{Index}(t-\Delta t) + \text{valeur\_source} \cdot \frac{\Delta t}{\text{facteur\_temps}}$$
- **Paramètres (`integrator_config`)** :
  - `source_variable` (string) : ID technique de la variable de flux instantané à intégrer (ex: `"puissance_active"`, `"debit_eau"`).
  - `time_unit` (string) : Unité de temps de la source :
    - `"hours"` : Si la source est en puissance (kW) pour produire de l'énergie en (kWh), ou débit en m³/h pour produire des m³.
    - `"seconds"` : Si la source est un débit par seconde (kg/s ➔ kg).
    - `"minutes"` : Si la source est un débit par minute (L/min ➔ L).
  - `initial_val` (float) : Index initial de départ du compteur (ex: `15420.5`).
- **Cas d'usage** : Compteurs d'énergie active kWh, compteurs volumétriques d'eau m³, masse cumulée d'hydrogène kg.
