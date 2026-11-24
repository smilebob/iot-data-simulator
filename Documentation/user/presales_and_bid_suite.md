# 💼 Guide Avant-Vente & Porteurs d'Offres Numériques (v2.3.0)

Ce guide présente l'ensemble des outils intégrés à l'**IoT Data Simulator** (et à l'agent IA **`iot-preset-designer`**) pour préparer rapidement des **démonstrateurs clients percutants**, **chiffrer les architectures IoT/Data** et **générer les livrables de mémoires techniques**.

---

## 1. Calculateur de Dimensionnement & Volumétrie IoT (`Dimensionnement Offre`)

Accessible depuis la barre d'actions principale via le bouton **« Dimensionnement Offre »** (ou en ligne de commande via `scripts/sizing_estimator.py`).

### Paramètres & Calculs
- **Import automatique** : Cliquez sur *« Importer depuis mes équipements actifs »* pour récupérer le nombre d'équipements, de points de mesure et la cadence moyenne.
- **Projection sur parc client** : Ajustez librement le nombre d'équipements ($N$), le nombre de variables par équipement, la cadence d'émission (en secondes), le protocole (`MQTT TLS`, `HTTP REST`, `CoAP`) et la durée de rétention (1 à 15 ans).
- **Indicateurs calculés** :
  - **Débit de messages** (`msg/s`, `msg/jour`) et **Points de données / jour**.
  - **Trafic réseau & forfait 4G/LTE** (`kbps` et `Go/mois`, incluant l'en-tête protocole et TLS).
  - **Stockage base de données** (`Go` bruts et compressés TimescaleDB au ratio 5:1).
  - **Gabarit Serveur ThingsBoard recommandé** (*Compact Mono-nœud*, *Standard Production*, *Haute Performance* ou *Cluster Entreprise Distribué*).
- **Export Mémoire Technique** : Le bouton **« Copier Fiche Technique (Markdown) »** copie un tableau complet prêt à coller dans votre réponse à appel d'offres.

---

## 2. Modèles Métiers Réglementaires & ROI (Décret BACS / Tertiaire / ISO 50001)

Trois nouveaux cas d'usage natifs intègrent des formules physiques AST calculant en temps réel des indicateurs de performance énergétique et financière :

| ID Modèle | Nom | Secteur | KPIs & Formules Natives |
| :--- | :--- | :--- | :--- |
| `bldg_bacs_class_a` | **GTB Classe A (Décret BACS / Tertiaire)** | Tertiaire & Smart Building | `puissance_totale_kw`, **IPE Surfacique** (`kWh/m².an`), **Émissions CO2** (`kgCO2/h`), **Gain énergétique BACS** (`%`) |
| `infra_district_heating` | **Sous-Station Réseau de Chaleur (RCU)** | Infrastructures & Énergie | `delta_t_primaire`, `puissance_thermique_kw`, `energie_thermique_mwh`, **CO2 Évité vs Gaz** (`kgCO2/h`) |
| `ind_iso50001_multifluid` | **Comptage Multi-Fluides ISO 50001** | Industrie & Automatismes | Électricité, Gaz, Eau, **Coût Horaire (`€/h`)**, **IPE Production (`kWh/t`)**, compteurs intégrés |

---

## 3. Sites Clients Express & Storyboards Live (`Sites & Démo Live`)

### A. Site Blueprints (Déploiement Multi-Équipements en 1 Clic)
Instanciez instantanément une architecture client complète et téléchargez son **Dashboard Master Hypervision Site ThingsBoard 4.3** (`TB JSON`) :
1. **Immeuble Tertiaire Connecté (Décret BACS)** : GTB Classe A + CTA Double Flux + PAC + TGBT + Bornes IRVE.
2. **Usine Industrielle Décarbonée (ISO 50001)** : Comptage Multi-Fluides + Centrale Air Comprimé + Groupe Froid + Ombrière Solaire PV.
3. **Microgrid Énergie & Stockage** : Centrale Solaire PV + Stockage Batterie BESS + Poste Source HTA + Station IRVE.

### B. Storyboards de Soutenance Live (Scénarios Minutés)
Pilotez une démonstration scénarisée en 4 phases de 15s (60s au total) pendant votre soutenance client :
- **`demo_bacs_derive`** (*Soutenance Décret BACS*) : Régime Nominal $\rightarrow$ Dérive énergétique CVC $\rightarrow$ Pic critique & Alarme ThingsBoard $\rightarrow$ Retour nominal.
- **`demo_maintenance_predictive`** (*Maintenance Prédictive*) : Acquisition Nominale $\rightarrow$ Capteur Figé (*Freeze*) $\rightarrow$ Perte Liaison (*Timeout*) $\rightarrow$ Rétablissement.

> [!NOTE]
> À l'arrêt manuel ou à la fin du scénario, le simulateur restaure automatiquement toutes les variables à l'état nominal (`anomaly = none`).

---

## 4. Générateur de Livrables d'Offres (`Livrables Offre`)

Téléchargez en 1 clic deux pièces directement exploitables dans vos dossiers d'offres :
1. **Liste de Points GTB / IoT (`io_list_offre.csv`)** : Format CSV **UTF-8 avec BOM et séparateur `;`** (ouverture directe sans perte d'accents dans Microsoft Excel FR), détaillant chaque équipement, protocole, variable, unité, plage min/max, cadence et règle d'alarme recommandée.
2. **Dossier Technique d'Architecture (`dossier_technique_offre.md`)** : Document Markdown complet contenant un diagramme de flux Mermaid, l'inventaire des équipements, la synthèse des KPIs ROI et l'annexe de dimensionnement.

---

## 5. Provisioning Direct ThingsBoard 4.3 (`Push ThingsBoard`)

Éliminez toute manipulation manuelle lors de la préparation d'une démo ThingsBoard :
1. **Connexion éphémère** : Saisissez l'URL ThingsBoard et vos identifiants. Aucun identifiant ni jeton JWT n'est jamais sauvegardé sur disque ou dans le navigateur.
2. **Support Multi-Tenant & Client (Customer)** :
   - Si vous êtes connecté en **`SYS_ADMIN`** : sélectionnez le **Tenant** cible dans la liste déroulante.
   - Sélectionnez un **Client (Customer)** existant ou saisissez un nom pour le créer à la volée.
3. **Provisioning & Synchronisation automatique** :
   - Crée les *Devices* dans ThingsBoard et les assigne au *Customer*.
   - Récupère leurs **Access Tokens** réels et les injecte automatiquement dans le simulateur.
   - Crée et importe les **Dashboards ThingsBoard** déjà liés aux vrais UUIDs des devices et les assigne au *Customer*.
   - **Option « Forcer HTTP REST »** *(pré-cochée par défaut)* : bascule automatiquement chaque équipement sur HTTP REST et renseigne `custom_host`, `custom_port` et `use_tls` depuis l'URL ThingsBoard saisie (fonctionne derrière tout pare-feu d'entreprise sur port 443).
   - **Provisioning Complet (v3.0)** :
     - **Asset Site + Relations `Contains`** : crée automatiquement un Asset racine (Site Client) relié à tous les équipements provisionnés.
     - **Profils d'Alarmes ISA-101 natifs** : génère des `DeviceProfile` avec règles `WARNING` (90 % de plage) et `CRITICAL` (hors plage) pour déclencher de vraies alarmes ThingsBoard en soutenance via le *Bouton Chaos*.
     - **Import 1 clic du Bundle 70 Widgets ISA-101** : déploie directement les 70 widgets modulaires dans la bibliothèque du Tenant cible.

---

## 6. Nouveautés Avant-Vente & Ingénierie v3.0

### 📈 Backfill Historique Accéléré (7j / 30j / 90j)
Avant un rendez-vous client, cliquez sur **« 📈 Backfill »** sur n'importe quelle carte équipement pour injecter en quelques secondes **7, 30 ou 90 jours de courbes historiques réalistes** (cycles jour/nuit, ralenti week-end, variables dérivées, intégrateurs d'énergie kWh/MWh et pics d'anomalies rétrospectifs) dans ThingsBoard REST v1.

### 📦 Pack Soutenance Client Complet (.ZIP — 1 Clic)
Dans la modale **Livrables d'Offres**, téléchargez en 1 clic **`pack_soutenance_iot_thingsboard.zip`** regroupant :
1. `01_IO_List_Points.csv` *(avec colonne **Registre Modbus TCP**)*
2. `02_Dossier_Architecture_IoT.md` *(avec dimensionnement `dp/s` et **5 sources officielles ThingsBoard**)*
3. `03_ThingsBoard_IoT_Gateway_modbus.json` *(connecteur Modbus prêt à importer)*
4. `04_Widgets_ISA101_Bundle_70.json` *(les 70 widgets ANSI/ISA-101)*
5. `dashboards/*.json` *(tous les tableaux de bord ThingsBoard actifs)*
6. `Catalogue_Commercial_Cas_Usage.pdf` *(book commercial des 35 cas d'usage)*

### 🎨 Studio Visuel de Synoptiques ANSI/ISA-101 (No-Code)
Cliquez sur **« 🎨 Studio »** sur un équipement (ou depuis *Livrables d'Offres*) pour assembler visuellement jusqu'à 6 composants parmi les **70 SVG ISA-101**, les relier aux variables de l'équipement avec aperçu temps réel, et enregistrer la composition directement sur le Dashboard ThingsBoard généré.

### 🔌 Serveur Modbus TCP Intégré & 🚀 Stress-Test (`dp/s`)
- **Serveur Modbus TCP (Port 5020, 0 droit admin)** : expose vos équipements simulés en registres Holding Float32 Big-Endian et Coils R/W pour tester en direct une passerelle **ThingsBoard IoT Gateway** ou un automate, avec téléchargement de `tb_gateway_modbus.json`.
- **Générateur de Charge (`dp/s`)** : simule `10` à `2 000` équipements virtuels en mode benchmark (`dry-run`) ou live HTTP pour valider empiriquement la charge `dp/s` face aux prévisions du calculateur de dimensionnement.
