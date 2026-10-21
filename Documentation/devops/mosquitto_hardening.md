# 🔐 Durcissement du Broker Eclipse Mosquitto

Par défaut, pour faciliter les démonstrations locales immédiates, le broker Mosquitto écoute en mode anonyme sur le port standard 1883. Ce guide explique comment durcir Mosquitto pour un environnement d'entreprise ou exposé sur Internet.

---

## 1. Activation de l'Authentification par Utilisateur / Mot de passe

### A. Génération du fichier de mots de passe Mosquitto
Exécutez dans un conteneur Mosquitto ou en local avec l'utilitaire `mosquitto_passwd` :
```bash
# Création d'un nouvel utilisateur 'iot_operator'
docker compose exec mosquitto mosquitto_passwd -c /mosquitto/config/passwords.txt iot_operator
# (Entrez un mot de passe robuste lorsque demandé)
```

### B. Mise à jour de la configuration Mosquitto
Dans [mosquitto/config/mosquitto.conf](file:///home/pierre/Projets/iot-data-simulator/mosquitto/config/mosquitto.conf) :
```conf
# Désactiver les connexions sans authentification
allow_anonymous false
password_file /mosquitto/config/passwords.txt
```

---

## 2. Configuration du Chiffrement TLS 1.2 / 1.3 (MQTTS - Port 8883)

### A. Génération des certificats X.509
Placez vos certificats dans le dossier `mosquitto/config/certs/` :
* `ca.crt` : Certificat de l'autorité de certification racine.
* `server.crt` : Certificat serveur signé par l'autorité.
* `server.key` : Clé privée du serveur (permissions `chmod 600`).

### B. Déclaration du listener chiffré dans `mosquitto.conf`
```conf
# Listener MQTTS sécurisé
listener 8883
cafile /mosquitto/config/certs/ca.crt
certfile /mosquitto/config/certs/server.crt
keyfile /mosquitto/config/certs/server.key

# Exigence TLS 1.2 minimum (Recommandation CIS)
tls_version tlsv1.2
```

### C. Ouverture du port dans `docker-compose.yml`
Ajoutez le port dans le service `mosquitto` :
```yaml
ports:
  - "1883:1883"
  - "8883:8883"
  - "9001:9001"
```

---

## 3. Contrôle d'Accès par Listes d'Autorisations (ACLs)

Pour limiter les droits d'un client à ses propres topics :
Créez `mosquitto/config/acl.txt` :
```
# Règles pour l'utilisateur ThingsBoard
user thingsboard_gw
topic write v1/devices/me/telemetry
topic write v1/devices/me/attributes
topic read v1/devices/me/rpc/request/+

# Règles de lecture pour le visualiseur MQTTX
user observer
topic read #
```

Ajoutez dans `mosquitto.conf` :
```conf
acl_file /mosquitto/config/acl.txt
```
