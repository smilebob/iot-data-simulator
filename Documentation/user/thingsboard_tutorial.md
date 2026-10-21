# 🎓 Tutoriel Pas à Pas : Connecter le Simulateur à ThingsBoard

Ce tutoriel illustre pas à pas comment connecter l'application à **ThingsBoard** (qu'il s'agisse de *ThingsBoard Cloud* ou d'une instance *Community / Professional Edition* installée localement ou sur vos serveurs), créer un tableau de bord visuel et déclencher une alarme en direct avec le bouton *Chaos*.

---

## 🎯 Objectif du Tutoriel
* Créer un équipement virtuel dans ThingsBoard.
* Connecter le simulateur à ThingsBoard à l'aide de l'Access Token.
* Visualiser les courbes de télémétrie en temps réel dans un dashboard ThingsBoard.
* Configurer une règle d'alarme de surchauffe (> 40°C) dans ThingsBoard.
* Déclencher l'alarme en direct en injectant un **Pic d'Anomalie** depuis le simulateur.

---

## 📝 Étape 1 : Créer le Device dans ThingsBoard

1. Connectez-vous à votre interface ThingsBoard (ex: [https://thingsboard.cloud](https://thingsboard.cloud)).
2. Dans le menu de navigation à gauche, cliquez sur **`Device groups`** (ou **`Entities` > `Devices`**).
3. Cliquez sur l'icône **`+`** (en haut à droite) puis sélectionnez **`Add new device`**.
4. Remplissez le formulaire :
   * **Name** : `Compresseur_Industriel_01`
   * **Device profile** : Laissez `default` (ou sélectionnez un profil dédié).
5. Cliquez sur **`Next: Credentials`** :
   * Le type d'identification par défaut est **Access Token**.
   * ThingsBoard génère un token aléatoire ou vous permet d'en choisir un personnalisé (ex: `TOKEN_COMPRESSEUR_DEMO`).
6. Cliquez sur **`Add`**.
7. Dans la liste des devices, cliquez sur votre nouveau device et cliquez sur **`Copy access token`**. Conservez-le précieusement.

---

## 📝 Étape 2 : Configurer le Simulateur IoT & Choisir le Protocole

L'application permet d'émettre vers ThingsBoard selon **3 protocoles au choix** pour chaque équipement virtuel :

1. Ouvrez l'interface du simulateur sur **[http://localhost:8000](http://localhost:8000)**.
2. Dans la barre supérieure ou les paramètres de l'équipement :
   * Renseignez le nom d'hôte de votre ThingsBoard (ex: `easythings.app...` ou `thingsboard.cloud`).
3. Cliquez sur **`Nouvel Équipement`** (ou éditez un équipement existant) :
   * **Identifiant Unique** : `compresseur_01`
   * **Nom d'affichage** : `Compresseur Atelier 01`
   * **Plateforme Cible** : `ThingsBoard`
   * **Protocole ThingsBoard** :
     * 🟢 **HTTP REST (Recommandé pour Cloudflare / Port 443 HTTPS)** : Envoie les données en requêtes `POST https://{host}/api/v1/{token}/telemetry`. Idéal lorsque le serveur est protégé par un CDN ou reverse proxy qui bloque les flux TCP bruts sur le port 1883.
     * 🔵 **MQTT (Broker TCP standard)** : Utilise une session TCP persistante sur le port 1883 ou 8883 (MQTTS).
     * 🟣 **CoAP (RFC 7252 / UDP Port 5683)** : Transmission par datagrammes légers sans overhead de session.
   * **Access Token** : Collez le token copié à l'étape 1 (`TOKEN_COMPRESSEUR_DEMO`).
   * Cliquez sur **`Tester la communication`** : le simulateur valide immédiatement si ThingsBoard répond et si le Token est accepté !
   * Cliquez sur **`Enregistrer`**.
4. Cliquez sur **`Ajouter une Variable`** pour créer une mesure de température :
   * **Identifiant Unique** : `temperature`
   * **Nom Lisible** : `Température Moteur`
   * **Équipement Associé** : Sélectionnez `Compresseur Atelier 01`
   * **Type IoT** : `Télémétrie`
   * **Type de Donnée** : `Nombre Flottant`
   * **Unité** : `°C`
   * **Intervalle d'Envoi** : `2.0` (secondes)
   * **Mode de Simulation** : `Fonction Sinusoïdale` (Min: `22.0`, Max: `34.0`, Période: `30.0`, Bruit: `2.0`)
   * Cliquez sur **`Enregistrer la variable`**.

---

## 📝 Étape 3 : Vérifier la Réception dans ThingsBoard

1. Retournez sur ThingsBoard dans la fiche de votre équipement `Compresseur_Industriel_01`.
2. Cliquez sur l'onglet **`Latest telemetry`** (Dernière télémétrie) :
   * Vous devez voir apparaître la clé `temperature` avec sa valeur qui évolue en temps réel toutes les 2 secondes avec un horodatage précis !

---

## 📝 Étape 4 : Créer un Dashboard Visuel dans ThingsBoard

1. Dans ThingsBoard, allez dans **`Dashboards`** > cliquez sur **`+ Add new dashboard`** > nommez-le `Supervision Usine`.
2. Ouvrez le dashboard et passez en mode édition (icône crayon en bas à droite).
3. Cliquez sur **`Add new widget`** :
   * Choisissez le paquet de widgets **`Charts`** > sélectionnez **`Timeseries Line Chart`**.
   * Dans la source de données (**Datasource**) :
     * Type : `Entity`
     * Entité : `Compresseur_Industriel_01`
     * Clé de télémétrie : `temperature`
   * Cliquez sur **`Add`**.
4. Vous disposez maintenant d'un magnifique graphique oscillant en direct entre 22°C et 34°C.

---

## 📝 Étape 5 : Démonstration d'Alarme avec le Bouton Chaos 💥

Pour bluffer votre audience lors d'une démonstration :

1. Dans ThingsBoard, allez dans le profil de l'équipement (**`Device profiles`** > `default`) > onglet **`Alarm rules`**.
2. Ajoutez une règle d'alarme :
   * **Alarm type** : `Surchauffe Moteur Critique`
   * **Create condition** : `temperature > 40`
   * **Clear condition** : `temperature <= 35`
   * Sauvegardez le profil.
3. Placez votre écran avec le dashboard ThingsBoard d'un côté et l'interface du Simulateur IoT de l'autre.
4. Sur la carte `Température Moteur` du simulateur, cliquez sur le bouton **`💥 Pic`** :
   * **Ce qui se passe** :
     1. La valeur saute immédiatement à ~80°C.
     2. ThingsBoard reçoit le pic télémétrique sur `v1/devices/me/telemetry`.
     3. La règle d'alarme se déclenche instantanément : une alerte rouge clignotante apparaît sur votre dashboard ThingsBoard !
     4. Au bout de quelques secondes, la simulation reprend son onde normale (retour sous 35°C), et l'alarme repasse automatiquement à l'état résolu !
