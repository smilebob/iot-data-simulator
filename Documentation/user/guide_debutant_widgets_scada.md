# 🎓 Guide Débutant : Utiliser les 70 Widgets SCADA ISA-101 dans ThingsBoard 4.3

Ce guide pas-à-pas s'adresse à **tout utilisateur (aucun prérequis technique)** souhaitant créer ses propres tableaux de bord industriels dans **ThingsBoard 4.3** en glissant-déposant nos **70 composants SVG normalisés ANSI/ISA-101.01**.

---

## 🧠 Pourquoi la norme ISA-101 ? (À comprendre en 30 secondes)

Un bon tableau de bord industriel ne doit pas ressembler à un sapin de Noël ! Selon la norme **ISA-101 (High-Performance HMI)** :
- **En fonctionnement normal** : tout est sobre — fond **gris mat anti-éblouissement (`#E5E7EB`)**, équipements en **gris acier (`#475569`)**, chiffres lisibles en **noir/ardoise (`#0F172A`)**.
- **En cas d'anomalie uniquement (Couleur par Exception)** : l'œil repère instantanément le problème grâce à un **double codage Forme + Couleur** (accessible aux opérateurs daltoniens) :
  - **▲ Ambre (`#D97706`)** : Avertissement (seuil haut / dérive).
  - **■ ! Rouge (`#DC2626`) + bordure pulsante** : Alarme Critique nécessitant une action immédiate.

---

## Étape 1 : Télécharger le Bundle de Widgets depuis le Simulateur

1. Ouvrez l'interface web de l'**IoT Data Simulator**.
2. Cliquez sur le bouton **« Livrables Offre »** dans la barre d'actions supérieure.
3. Dans la section **« Bundles Widgets SCADA ISA-101 ThingsBoard 4.3 »**, choisissez :
   - **« Tout (70) »** pour télécharger la bibliothèque complète (`tb43_scada_widgets_bundle.json`), **OU**
   - Un **Bundle Thématique** adapté à votre métier client (*Primitives ISA*, *Élec & Data Center*, *CVC & GTB*, *Process & H2*, *Eau/STEP/RCU*, *Infra/Tunnels/City*).

---

## Étape 2 : Importer le Bundle dans ThingsBoard 4.3 (une seule fois)

1. Connectez-vous à votre instance **ThingsBoard 4.3** (avec un compte *Tenant Admin*).
2. Dans le menu de gauche, cliquez sur **Widgets Library** (icône puzzle) $\rightarrow$ onglet **Widget Bundles**.
3. Cliquez sur le bouton **`+`** en haut à droite $\rightarrow$ sélectionnez **Import widget bundle**.
4. Glissez-déposez le fichier `.json` téléchargé à l'étape 1, puis cliquez sur **Import**.
5. Votre nouvelle collection (ex : **`SCADA ISA-101 Industriel & Énergie`**) apparaît immédiatement dans votre bibliothèque ThingsBoard !

> [!TIP]
> **Importer un seul widget individuel ?** Si vous ne voulez qu'un seul symbole (ex : uniquement la *Batterie BESS*), ouvrez l'onglet **Widget Types** $\rightarrow$ **`+`** $\rightarrow$ **Import widget type** et sélectionnez un fichier dans `dashboards/thingsboard/widgets/individual/`.

---

## Étape 3 : Poser un Widget sur Votre Tableau de Bord

1. Dans ThingsBoard, ouvrez un tableau de bord existant (ou créez-en un nouveau via **Dashboards** $\rightarrow$ **`+`**).
2. Passez en mode édition en cliquant sur le crayon **Edit mode** (en bas à droite).
3. Cliquez sur **+ Add widget** (en haut ou au centre de l'écran).
4. Dans la liste des bundles, choisissez **`SCADA ISA-101 Industriel & Énergie`** (ou votre bundle thématique).
5. Cliquez sur le composant souhaité (ex : *Pompe Centrifuge*, *Baie Serveur IT*, *Barre Analogique HH/H/L/LL*, *Batterie Stockage BESS*).

---

## Étape 4 : Connecter Votre Équipement et Votre Variable (Mappage)

La fenêtre de configuration du widget s'ouvre sur l'onglet **Data** :
1. Dans **Entity alias** (Source de données), sélectionnez votre équipement (*Device*) cible (ex : `PAC Site Alpha` ou `TGBT Principal`).
   - *(Si aucun alias n'existe encore, cliquez sur **Create new** $\rightarrow$ Type **Single entity** $\rightarrow$ **Device** $\rightarrow$ sélectionnez votre équipement).*
2. Dans **Data keys** (Clés de données), cliquez dans le champ, choisissez **Time series** (télémétrie) ou **Attributes** (attribut) et sélectionnez la variable à afficher (ex : `puissance_totale_kw`, `soc_pct`, `temp_ambiante`).
3. Cliquez sur **Add** pour poser le widget sur la grille, puis redimensionnez-le à votre convenance.

---

## Étape 5 : Personnaliser le Libellé, l'Unité et les Seuils d'Alarmes

Pour activer le changement de couleur et les badges **▲ / ■ !** en cas de dépassement :
1. Passez la souris sur votre widget (en mode édition) et cliquez sur l'icône **crayon (Edit widget)**.
2. Ouvrez l'onglet **Settings** (Paramètres) :
   - **Libellé affiché** : Titre court affiché au-dessus du symbole (ex : `Temp. Départ Eau`).
   - **Unité** : Laissez vide pour reprendre automatiquement l'unité ThingsBoard, ou saisissez-la (`°C`, `bar`, `kW`, `%`).
   - **Décimales** : Nombre de chiffres après la virgule (`0`, `1` ou `2`).
   - **Seuil Avertissement ▲ Ambre (>=)** : Valeur à partir de laquelle le composant passe en Ambre avec le triangle `▲` (ex : `75`).
   - **Seuil Critique ■ ! Rouge (>=)** : Valeur à partir de laquelle le composant passe en Rouge pulsant avec le carré `■ !` (ex : `90`).
3. Cliquez sur **Apply** puis sur **Save** (en haut à droite du dashboard).

---

## 🛠️ Dépannage Rapide (Questions Fréquentes)

| Symptôme | Cause probable | Solution en 10 secondes |
| :--- | :--- | :--- |
| Le widget affiche `--` | Aucune donnée reçue ou clé mal orthographiée | Vérifiez dans *Devices $\rightarrow$ Latest telemetry* que la clé sélectionnée reçoit bien des valeurs du simulateur. |
| La barre / cuve reste pleine ou vide | La valeur dépasse `100` | Les widgets à niveau (`proc_tank`, `elec_bess_battery`, `isa_analog_bar`) attendent idéalement un pourcentage `0..100`. |
| Le widget ne passe pas en Rouge lors d'un pic | Seuils non renseignés | Ouvrez *Edit widget $\rightarrow$ Settings* et renseignez **Seuil Avertissement** et **Seuil Critique**. |
| Je veux tester mes alarmes en direct | Besoin d'une panne simulée | Dans l'IoT Data Simulator, cliquez sur l'icône **Éclair (Chaos / Spike)** sur la variable ou lancez un **Storyboard Live** ! |
