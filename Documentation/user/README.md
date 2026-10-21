# 📖 Manuel de l'Utilisateur : IoT Data Simulator

Bienvenue dans le guide utilisateur de l'application **IoT Data Simulator**.

Cette application a été conçue pour vous permettre de générer très simplement des flux de données IoT réalistes, d'animer des démonstrations impressionnantes sur **ThingsBoard** (ou d'autres plateformes IoT comme **Home Assistant** ou **Datacake**), et de tester la réactivité de vos règles d'alarmes grâce à des injections d'anomalies en 1 clic.

---

## 🧭 Sommaire du Guide Utilisateur

1. [Prise en main Rapide (5 minutes)](quickstart.md) : Découverte de l'interface web, lancement de la simulation et compréhension des cartes de variables.
2. [Tutoriel Pas à Pas : Connexion avec ThingsBoard](thingsboard_tutorial.md) : **Le guide pas-à-pas complet**, depuis la création d'un équipement dans ThingsBoard jusqu'à la création d'un dashboard de démo et le déclenchement d'une alarme via le bouton *Chaos*.
3. [Guide des Modes de Simulation](simulation_modes.md) : Explication de chaque mode de génération (Sinus, Triangle, Rampe, Bruit gaussien, Marche aléatoire, Tableau de points horodatés et import de fichiers CSV).
4. [Exploration des flux avec MQTTX Web](mqttx_inspection.md) : Comment utiliser l'interface web intégrée pour espionner et valider les trames MQTT émises en direct.
5. [Tableaux de Bord SCADA ThingsBoard Préconfigurés](thingsboard_dashboards.md) : Guide d'utilisation, téléchargement en 1 clic avec token ThingsBoard préconfiguré, thème Light haute lisibilité (WCAG AA), procédure d'importation en 3 étapes et **référentiel exhaustif des 32 synoptiques vectoriels SCADA métiers**.

---

## 💡 Concepts Clés

* **Équipement Virtuel (Device)** : Représente une machine ou un capteur physique (ex: *Station Météo*, *Compresseur d'Atelier*, *Chaudière*). Un équipement regroupe plusieurs grandeurs physiques et possède son propre identifiant / token sur la plateforme IoT.
* **Variable** : Grandeur physique mesurée ou paramètre de contrôle.
  * **Télémétrie** : Donnée continue horodatée (température, pression, puissance, vitesse de rotation).
  * **Attribut / Contrôle** : Paramètre d'état ou consigne (ex: état On/Off de pompe, mode de régulation).
* **Bouton Chaos (Injection d'Anomalie)** : Outil de démonstration permettant d'altérer instantanément le signal généré (Pic de chaleur, dérive thermique, panne de transmission) pour déclencher les alertes de votre plateforme IoT devant vos clients ou vos équipes.
