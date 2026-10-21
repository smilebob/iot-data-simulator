# 🛡️ Contrôle d'Accès (RBAC) & Protection des Secrets (Conformité CIS)

Ce document décrit le modèle de sécurité, la gestion des identités, le contrôle d'accès basé sur les rôles (RBAC) et les mécanismes de protection des données sensibles au sein de la stack **IoT Data Simulator**.

---

## 1. Modèle RBAC (Role-Based Access Control)

L'application implémente trois niveaux de privilèges stricts :

| Rôle | Description & Responsabilités | Périmètre d'Actions Autorisées |
| :--- | :--- | :--- |
| **`ADMIN`** *(Administrateur Système)* | Gestion intégrale du cycle de vie des utilisateurs, configuration réseau globale du broker MQTT et des secrets système. | • Gestion des utilisateurs (création, suppression, réinitialisation de mot de passe)<br>• Configuration globale du broker MQTT et certificats<br>• Purge des journaux applicatifs<br>• Toutes les actions des opérateurs |
| **`OPERATOR`** *(Ingénieur Test / Opérateur)* | Exploitation opérationnelle du simulateur, modélisation des signaux, injection de pannes et validation des liaisons IoT. | • Démarrage / Arrêt de la simulation<br>• Injection de pannes (*Chaos Button*) et forçage manuel<br>• Gestion des équipements et variables (CRUD)<br>• Upload CSV et rejeu temporel<br>• Tests de connectivité (MQTT, HTTP, CoAP)<br>• Import / Export de scénarios |
| **`VIEWER`** *(Observateur / Auditeur)* | Surveillance en temps réel, monitoring de télémétrie et consultation des dashboards. | • Consultation en direct du tableau de bord et graphiques<br>• Écoute du flux WebSocket temps réel (`/ws/live`)<br>• Consultation des logs applicatifs (lecture seule)<br>• Modification de son propre mot de passe |

---

## 2. Protection des Secrets & Directives CIS Benchmark

### A. Hachage des Mots de Passe (Scrypt RFC 7914)
- **Algorithme à Haute Résistance Mémoire** : utilisation de `scrypt` ($N=16384, r=8, p=1$).
- **Sel Aléatoire** : chaque mot de passe est haché avec un sel cryptographique unique de 16 octets généré par `secrets.token_bytes(16)`.
- **Protection Anti-Timing Attack** : la validation utilise `secrets.compare_digest` en temps constant.
- **Stockage** : format normalisé `$scrypt$16384$8$1${salt_b64}${key_b64}`. Aucun mot de passe en clair n'est stocké ou consigné dans les logs.

### B. Ségrégation et Permissions des Fichiers (`data/users.json`)
- **Isolation physique** : la base utilisateurs est stockée dans `data/users.json`, strictement séparée de `data/simulator_state.json`. Cela garantit que l'exportation d'un scénario de simulation ne fuite aucun hash d'utilisateur.
- **Permissions restreintes `0600`** : le fichier est créé avec les droits `stat.S_IRUSR | stat.S_IWUSR` (accessible uniquement par l'utilisateur du conteneur `UID 10001`).
- **Écritures Atomiques** : utilisation du pattern fichier temporaire + `os.replace` pour prévenir toute corruption lors d'un arrêt abrupt.

### C. Sessions JWT & Cookies Sécurisés
- **Clé Secrète de Signature** : générée aléatoirement (256 bits) et conservée dans `data/.jwt_secret` (`chmod 0600`) ou injectée par la variable d'environnement `JWT_SECRET_KEY`.
- **Attributs Cookie** :
  - `HttpOnly = True` : inaccessible depuis le JavaScript client (immunité contre le vol par faille XSS).
  - `SameSite = "lax"` : protection contre les attaques Cross-Site Request Forgery (CSRF).
  - `Secure = True` en production HTTPS.
- **Validité** : jetons horodatés limités à 8 heures avec validation stricte de l'expiration (`exp`).

---

## 3. Compte Administrateur Initial

Au premier démarrage du conteneur, si aucun utilisateur n'existe :
- **Identifiant par défaut** : `admin` (ou variable `DEFAULT_ADMIN_USERNAME`).
- **Mot de passe initial** : `Admin_123456!` (ou variable `DEFAULT_ADMIN_PASSWORD`).
- **Indicateur de changement** : `must_change_password: True` invite l'administrateur à modifier immédiatement son mot de passe lors de sa première session.
- **Protection contre le verrouillage** : le système refuse toute suppression du dernier compte administrateur actif.
