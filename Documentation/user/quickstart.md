# ⚡ Prise en Main Rapide (5 Minutes)

Ce guide vous permet de démarrer l'application et de voir vos premières données télémétriques s'animer.

---

## 1. Démarrer la Solution

Dans votre terminal :
```bash
cd /home/pierre/Projets/iot-data-simulator
docker compose up -d
```

Ouvrez ensuite votre navigateur préféré à l'adresse : **[http://localhost:8000](http://localhost:8000)**.

---

## 2. Découverte de l'Interface Graphique (Charte Graphique EIFFAGE)

L'interface adopte la **charte graphique du Groupe Eiffage** (Rouge Eiffage `#E2001A`, fonds anthracites épurés, typographie industrielle soignée).

```
┌────────────────────────────────────────────────────────────────────────┐
│ [EIFFAGE]  IoT Data Simulator      [● Broker: Connecté] [Simulation]   │
├────────────────────────────────────────────────────────────────────────┤
│ Vue : [Tous les équipements] [Station Météo] ...   [+ Nouvel Équipement]│
├────────────────────────────────────────────────────────────────────────┤
│ ┌─ [Station Météo Solaire] (ThingsBoard) ──── [+ Var] [Éditer] [Suppr]┐│
│ │                                                                     ││
│ │  ┌───────────────────────────┐    ┌───────────────────────────┐     ││
│ │  │ Température Ambiante      │    │ Humidité Relative         │     ││
│ │  │ 24.3 °C                   │    │ 55.2 %                    │     ││
│ │  │ ~~~~~/\~~~~~ (Sparkline)  │    │ ~~~~~/\~~~~~ (Sparkline)  │     ││
│ │  │ [💥 Pic] [📈 Dérive] [❄️]  │    │ [💥 Pic] [📈 Dérive] [❄️]  │     ││
│ │  └───────────────────────────┘    └───────────────────────────┘     ││
│ └─────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────┘
```

1. **La barre supérieure EIFFAGE** :
   * **Logo & Marque EIFFAGE** : avec indicateur de connexion broker MQTT et compteur de publications en direct.
   * **Bouton Simulation Active** : permet de mettre en pause ou de relancer l'ensemble de la simulation en 1 clic.
2. **Sections d'Équipements (Regroupement clair)** :
   * Chaque équipement possède sa propre **carte conteneur dédiée** délimitée par un filet rouge Eiffage.
   * Dans l'en-tête de chaque équipement :
     * **`+ Ajouter une Variable`** : crée une variable pré-associée à cet équipement.
     * **`Éditer`** : modifie le nom, le token ThingsBoard ou la plateforme.
     * **`Supprimer`** : supprime l'équipement et nettoie ses variables associées.
3. **Les cartes de variables (internes à chaque équipement)** :
   * Chaque variable affiche sa valeur en direct, son sparkline animé rouge Eiffage, son topic MQTT actif et les boutons d'anomalies (Chaos Button).

---

## 3. Tester le Forçage Manuel et l'Injection d'Anomalie

1. Repérez la carte **`Température Ambiante`** dans la section de votre équipement.
2. Cliquez sur le bouton **`💥 Pic`** :
   * Vous verrez la valeur bondir instantanément de +50°C pendant quelques secondes avant de reprendre sa course sinusoïdale normale.
3. Cochez la case **`Forcer :`** et tapez `45.0` :
   * Le signal mathématique est immédiatement court-circuité et la valeur reste figée sur votre consigne manuelle tant que la case reste cochée.
