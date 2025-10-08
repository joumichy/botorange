# Scraper Kompass

Script simple pour scraper les numéros de téléphone depuis le site Kompass.

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

### Méthode 1 : Script interactif
```bash
python run_scraper.py
```

### Méthode 2 : Script direct
1. Exécutez : `python main.py`
2. Le navigateur s'ouvrira, naviguez vers votre page Kompass
3. Appuyez sur Entrée pour commencer le scraping

### Méthode 3 : Fichier batch (Windows)
Double-cliquez sur `run_scraper.bat`

## Configuration

Modifiez `config.py` pour ajuster :
- Nombre de pages à scraper
- Délais de navigation
- Mode headless du navigateur

## Résultats

Le script génère un fichier Excel `kompass_data_YYYYMMDD_HHMMSS.xlsx` avec :
- **Feuille "Entreprises"** : Informations complètes (nom, téléphone, ville, adresse)

## Notes

- Le script ouvre un navigateur, naviguez manuellement vers votre page Kompass
- Assurez-vous d'être connecté à votre compte Kompass
- Le script utilise un navigateur visible pour éviter la détection
- Les données sont automatiquement dédupliquées