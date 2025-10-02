# Projet Télémédecine - Analyse de Données Biomédicales

Ce projet permet d'analyser des données biomédicales provenant de capteurs portables, en particulier pour l'analyse de l'activité respiratoire et des mouvements du pied lors d'activités de marche, de repos et de montée/descente d'escaliers, entre autres.

## 📋 Description

Le projet traite des fichiers de données brutes (format `.txt`) contenant des informations de capteurs biomédicaux avec trois axes de mesure :
- **THORAX** : Activité respiratoire
- **X** : Mouvement selon l'axe X
- **Y** : Mouvement selon l'axe Y

## 🔧 Installation

### Avec pip (recommandé pour la production)

1. Clonez le projet :
```bash
git clone https://github.com/appollo30/environnement_telemedecine.git
```


2. Installez les dépendances :
```bash
# Pour le développement (inclut jupyter, matplotlib, etc.)
pip install -r requirements-dev.txt
```

### Avec Conda

1. Créez l'environnement depuis le fichier YAML :
```bash
conda env create -f environment.yml
```

2. Activez l'environnement :
```bash
conda activate telemedecine
```

## 🚀 Utilisation

### Exécution du script principal

Le script `main.py` permet de traiter un fichier de données brutes :

```bash
python main.py <chemin_vers_fichier.txt>
```

**Exemple :**
```bash
python main.py raw_data/protocole_respiration_viviane_induct.txt
```

### Contraintes d'utilisation

- Le fichier doit être au format `.txt`
- Le fichier doit contenir des données formatées selon le protocole du capteur
- L'adresse MAC du capteur doit être `00:07:80:65:E0:11`

## 📊 Fonctions principales

### `parse_raw(file_content: List[str]) -> Tuple[Dict, pd.DataFrame]`

**Description :** Fonction principale pour analyser les données brutes du capteur.

**Paramètres :**
- `file_content` : Liste des lignes du fichier de données brutes

**Retour :**
- `header_json` : Dictionnaire contenant les métadonnées (taux d'échantillonnage, date, heure)
- `df` : DataFrame pandas avec les colonnes :
  - `timestamp` : Horodatage des mesures
  - `THORAX` : Données d'activité respiratoire
  - `X` : Mouvement axe X
  - `Y` : Mouvement axe Y

**Fonctionnement :**
1. Extrait et parse l'en-tête JSON (ligne 2 du fichier)
2. Récupère les paramètres du capteur (taux d'échantillonnage, date, heure)
3. Traite les données ligne par ligne en ignorant les colonnes d'index
4. Crée un DataFrame avec timestamps calculés depuis les métadonnées
5. Définit le timestamp comme index du DataFrame

**Exemple d'utilisation :**
```python
from src.utils import parse_raw

file_path = "raw_data/protocole_respiration_viviane_induct.txt"
header_json, df = parse_raw(df)
# On peut ensuite faire ce qu'on veut avec les données
```


### Autres fonctions utilitaires

#### `simple_line_plot(df: pd.DataFrame)`
Génère un graphique multi-axes des trois signaux (THORAX, X, Y) avec Plotly.

#### `fourier_transform_plot(df: pd.DataFrame)`
Crée un graphique de la transformée de Fourier du signal THORAX pour l'analyse fréquentielle.

#### `butterworth_filter_thorax(df: pd.DataFrame, lowcut=0.05, highcut=0.8, order=4)`
Applique un filtre passe-bande Butterworth au signal THORAX pour réduire le bruit.

## 📁 Structure du projet

```
proj/
├── main.py                    # Script principal d'exécution
├── requirements.txt           # Dépendances de production
├── requirements-dev.txt       # Dépendances de développement
├── environment.yml            # Configuration Conda
├── data_exploration.ipynb     # Notebook d'exploration
├── src/
│   ├── __init__.py
│   └── utils.py              # Fonctions utilitaires
└── raw_data/                 # Données brutes d'exemple
    ├── protocole_apnee_leo_induct.txt
    ├── protocole_respiration_viviane_induct.txt
    └── ...
```

## 🛠️ Développement

Pour contribuer au projet :

1. Installez les dépendances de développement : `pip install -r requirements-dev.txt`
2. Utilisez le notebook `data_exploration.ipynb` pour l'exploration des données
3. Les fonctions utilitaires sont dans `src/utils.py`
