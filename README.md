# Tableau de bord TVA — Meridian Distribution

Application web développée avec Streamlit pour permettre à la direction financière et à la comptabilité de Meridian Distribution de suivre la qualité du référentiel clients (10 000 numéros de TVA intracommunautaires vérifiés auprès du service VIES de la Commission européenne).



## Fonctionnalités

- **Indicateurs clés** : suivi global du nombre de numéros valides, invalides et non tranchés avec leur part en pourcentage.
- **Entonnoir de vérification** : visualisation des pertes avant l'envoi à VIES (absents, doublons, erreurs de structure).
- **Filtres cumulatifs** : filtrage dynamique par pays déclaré, canal de saisie et période de saisie.
- **Analyse des erreurs** : graphiques en barres horizontales de la part de numéros invalides par canal de saisie et par pays déclaré, avec valeurs affichées directement sur chaque barre.
- **Liste des numéros à traiter** : tableau des numéros invalides et non tranchés avec l'action comptable associée et bouton d'export CSV compatible Excel (séparateur `;`, encodage `utf-8-sig`).

## Technologies utilisées

- **Python** (3.11 à 3.14)
- **Streamlit** (1.66.1)
- **pandas** (3.1.0)
- **Plotly Express** (7.1.0)

## Installation et lancement

1. Cloner le dépôt et se placer dans le dossier du projet :

```bash
git clone https://github.com/Hamouz88/dashboard-tva.git
cd dashboard-tva
```

2. Créer et activer l'environnement virtuel :

```bash
# Sous Windows (Git Bash)
python -m venv .venv
source .venv/Scripts/activate

# Sous Mac / Linux
python3 -m venv .venv
source .venv/bin/activate
```

3. Installer les dépendances et lancer l'application :

```bash
pip install -r requirements.txt
streamlit run app.py
```

