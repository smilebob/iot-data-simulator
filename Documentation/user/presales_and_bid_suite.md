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
