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

## 2. Découverte de l'Interface Graphique

```
┌────────────────────────────────────────────────────────────────────────┐
│ [⚡ IoT Data Simulator]  [● Broker: Connecté] [Publiés: 142] [Simulation Active] │
├────────────────────────────────────────────────────────────────────────┤
│ Équipements : [Tous] [Station Météo (3)] [Compresseur Atelier (2)]  [+ Nouveau] │
├────────────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────┐    ┌───────────────────────────┐         │
│ │ Température Ambiante      │    │ Vitesse de Rotation       │         │
│ │ 24.3 °C                   │    │ 2800 rpm                  │         │
│ │ ~~~~~/\~~~~~ (Sparkline)  │    │ ~~~~~/\~~~~~ (Sparkline)  │         │
│ │ [💥 Pic] [📈 Dérive] [❄️]  │    │ [💥 Pic] [📈 Dérive] [❄️]  │         │
│ └───────────────────────────┘    └───────────────────────────┘         │
└────────────────────────────────────────────────────────────────────────┘
```

1. **La barre supérieure** :
   * **Badge Broker** : vous informe en temps réel de l'état de la liaison MQTT (vert = connecté, rouge = erreur). Cliquez dessus pour changer d'adresse de broker à tout moment.
   * **Compteur Publiés** : s'incrémente en direct à chaque trame MQTT transmise avec succès.
   * **Bouton Simulation Active** : permet de mettre en pause ou de relancer l'ensemble de la simulation en 1 clic.
2. **La barre de filtrage** :
   * Permet d'isoler un équipement virtuel spécifique ou de voir toutes les variables.
   * Boutons **`Nouvel Équipement`** et **`Ajouter une Variable`**.
3. **Les cartes de variables** :
   * Chaque carte affiche le nom lisible, l'ID technique, la valeur courante qui clignote à chaque mise à jour, l'unité, le mini-graphique animé (sparkline) et les boutons d'action rapide.

---

## 3. Tester le Forçage Manuel et l'Injection d'Anomalie

1. Repérez la carte **`Température Ambiante`**.
2. Cliquez sur le bouton **`💥 Pic`** :
   * Vous verrez la valeur bondir instantanément de +50°C pendant quelques secondes avant de reprendre sa course sinusoïdale normale.
3. Cochez la case **`Forcer :`** et tapez `45.0` :
   * Le signal mathématique est immédiatement court-circuité et la valeur reste figée sur votre consigne manuelle tant que la case reste cochée.
