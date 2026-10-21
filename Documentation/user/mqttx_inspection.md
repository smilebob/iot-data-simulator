# 🔍 Exploration & Débogage des flux avec MQTTX Web

Pour vous permettre d'espionner et de vérifier les paquets MQTT émis par le simulateur sans installer de logiciel lourd sur votre poste, la stack Docker intègre l'outil **MQTTX Web**.

---

## 1. Accéder à l'outil

Ouvrez votre navigateur à l'adresse : **[http://localhost:8080](http://localhost:8080)**.

---

## 2. Établir la Connexion au Broker Local

1. Cliquez sur le bouton **`+ New Connection`** (ou l'icône `+`).
2. Renseignez les paramètres suivants :
   * **Name** : `Mosquitto Local`
   * **Protocol** : `ws://` (WebSocket)
   * **Host** : `localhost`
   * **Port** : `9001`
   * **Path** : `/`
   * **SSL/TLS** : Désactivé (pour le broker local en clair)
3. Cliquez sur le bouton vert **`Connect`** en haut à droite.
4. L'indicateur passe au vert : vous êtes connecté au broker !

---

## 3. Souscrire aux Topics pour Observer les Messages

1. Cliquez sur le bouton **`+ New Subscription`**.
2. Dans le champ **Topic**, vous pouvez entrer :
   * `#` : pour voir absolument tous les messages circulant sur le broker.
   * `v1/#` : pour filtrer uniquement le trafic ThingsBoard.
   * `usines/#` : pour filtrer les variables industrielles personnalisées.
3. Cliquez sur **`Confirm`**.
4. Vous voyez instantanément les messages s'afficher avec leur topic et leur payload JSON complet :
   ```json
   {
     "ts": 1729506402000,
     "values": {
       "temperature": 24.85
     }
   }
   ```

---

## 4. Tester l'envoi d'une Commande vers le Simulateur

Vous pouvez également utiliser MQTTX Web pour simuler une requête RPC ThingsBoard :
* **Topic** : `v1/devices/me/rpc/request/1`
* **Payload** : `{"method": "setTargetSpeed", "params": 1500}`
* Cliquez sur l'icône avion d'envoi.
