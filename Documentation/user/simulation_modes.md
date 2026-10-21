# 📐 Guide des Modes de Simulation & Import CSV

Le simulateur IoT vous permet de modéliser avec précision le comportement physique de vos capteurs à l'aide de deux grandes méthodes :
1. Les **fonctions mathématiques paramétrables**
2. Le **rejeu d'une série temporelle / tableau de points horodatés (ou fichier CSV)**

---

## 1. Les Fonctions Mathématiques

### Sinus & Cosinus
* **Idéal pour** : Températures ambiantes (cycle jour/nuit), variations d'ensoleillement, consommation électrique saisonnière.
* **Paramètres** :
  * `Min` & `Max` : bornes d'oscillation.
  * `Période` : durée en secondes d'un cycle complet (ex: 60s pour un cycle rapide de démo).
  * `Bruit aléatoire (%)` : ajoute des micro-fluctuations (ex: 2%) pour casser la perfection mathématique et rendre le capteur hyper réaliste.

### Créneau (Square) & Dent de scie (Sawtooth)
* **Créneau** : Alterne entre valeur min et valeur max avec un rapport cyclique de 50%. Idéal pour un compresseur qui se met en marche / arrêt, un voyant d'état ou une vanne tout-ou-rien.
* **Dent de scie** : Montée linéaire continue suivie d'une retombée brutale à zéro. Idéal pour un niveau de cuve qui se remplit doucement puis se vide d'un coup, ou un compteur horaire réinitialisé.

### Rampe Linéaire & Triangle
* **Rampe** : Progression constante avec pas paramétrable (idéal pour un totalisateur d'énergie kWh ou un odomètre).
* **Triangle** : Montée et descente symétriques (idéal pour un vérin hydraulique qui avance et recule régulièrement).

### Marche Aléatoire (Random Walk) & Bruit Gaussien
* **Marche Aléatoire** : Chaque nouvelle valeur est la précédente plus ou moins un petit pas aléatoire (bounded). Idéal pour modéliser le cours d'une matière première, le niveau de bruit ambiant en dB ou la pression atmosphérique.
* **Gaussien** : Tirage statistique centré autour de la moyenne.

---

## 2. Tableau de Points Horodatés & Rejeu CSV

Lorsque vous souhaitez rejouer un scénario métier précis (ex: courbe d'accélération d'un moteur, cycle de charge/décharge d'une batterie de véhicule électrique) :

### Saisie manuelle de points
1. Sélectionnez le mode **`Tableau de Points Horodatés`**.
2. Cliquez sur **`+ Ajouter un point`** :
   * `Offset` : seconde à laquelle le point doit être atteint (ex: 0s, 10s, 25s, 60s).
   * `Valeur` : valeur numérique ou texte à cet instant.
3. Options :
   * **Répéter en boucle** : dès que le dernier point est atteint, le cycle recommence à zéro.
   * **Interpolation linéaire** : relie les points entre eux par une droite continue au lieu d'avancer par paliers brusques.

### Import d'un fichier CSV
Vous pouvez charger directement un fichier `.csv` ou `.txt` contenant vos relevés :
* **Format attendu** (avec ou sans ligne d'en-tête) :
  ```csv
  offset_seconds,valeur
  0,15.2
  10,18.5
  20,24.0
  35,32.8
  50,22.1
  60,15.0
  ```
* Cliquez sur **`Importer fichier CSV`** dans la fenêtre d'édition : les points sont instantanément chargés dans la table !
