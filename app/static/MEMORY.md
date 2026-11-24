# 📦 Mémoire du Module : Frontend Web SPA (`app/static/`)

> **Dossier** : `/home/pierre/Projets/iot-data-simulator/app/static/` | **Dernière MAJ** : 2026-11-24 | **Version** : 3.0.0

## 🎯 Rôle & Responsabilité
Interface utilisateur Single Page Application (HTML5, Tailwind CSS, Lucide Icons, JavaScript vanilla avec JSDoc) permettant le pilotage temps réel de la simulation, l'administration RBAC, l'import/export de modèles métiers, le Studio Visuel de Synoptiques ISA-101 et l'accès à la Suite Avant-Vente (Dimensionnement sourcé ThingsBoard, Sites Express, Storyboards Live, Livrables & Pack ZIP, Serveur Modbus TCP, Stress-Test `dp/s`, Backfill Historique et Push ThingsBoard 1 clic avec option HTTP REST).

## 🗂️ Fichiers & Composants Clés
| Fichier | Rôle | Composants / Fonctions Clés |
| :--- | :--- | :--- |
| [`index.html`](file:///home/pierre/Projets/iot-data-simulator/app/static/index.html) | Structure DOM & Modales | Header, Accordéon Équipements, `#modal-sizing`, `#modal-sites-demo`, `#modal-deliverables`, `#modal-tb-push`, `#modal-catalog`, `#modal-synoptic-studio` |
| [`app.js`](file:///home/pierre/Projets/iot-data-simulator/app/static/app.js) | Logique SPA, WebSocket `/ws/live`, appels REST | `refreshAll()`, `openSizingModal()`, `openSitesDemoModal()`, `openDeliverablesModal()`, `openTbPushModal()`, `triggerDeviceBackfill()`, `toggleModbusServer()`, `toggleStressTest()`, `openSynopticStudioModal()` |
| [`styles.css`](file:///home/pierre/Projets/iot-data-simulator/app/static/styles.css) | Design tokens & Thèmes Clair/Sombre | Variables CSS haute lisibilité, surcharges `html.light #modal-* > div` obligatoires (testées par `test_ui_accessibility_and_themes.py`) |

## ⚠️ Pièges & Consignes du Module (Gotchas)
- **Règle 1 (Performance CSS Modales & Listbox)** : Ne JAMAIS utiliser `backdrop-blur` sur les overlays de modales plein écran (cause de lag GPU/compositor sévère lors de l'ouverture de menus déroulants `<select>`). Utiliser un fond uni `bg-black/75`.
- **Règle 2 (Tokens Éphémères ThingsBoard)** : `tbEphemeralToken` et `tbSysAdminToken` dans `app.js` doivent rester strictement en mémoire vive et être remis à `null` dans `closeTbPushModal()` (jamais stockés dans `localStorage` ou `sessionStorage`).
- **Règle 3 (Persistance UI non-sensible)** : Seuls le thème (`theme`) et l'état de pliage de l'accordéon (`collapsedDevices`) sont stockés dans `localStorage`.
