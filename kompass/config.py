#!/usr/bin/env python3
"""
Configuration pour le scraper Kompass
"""
KOMPASS_LICENSE_HASH="16d74232d666243e3dd9711daaef2b7538f849efaa62cf19f91a97e82c420e34"

# Configuration du scraping
SCRAPING_CONFIG = {
    'max_pages': 3,                    # Nombre max de pages
    'page_delay': 3000,               # Délai entre pages (ms)
    'page_timeout': 30000,            # Timeout de chargement (ms)
    'headless': False,                # Mode visible/invisible
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Sélecteurs CSS pour Kompass
SELECTORS = {
    'company_name': 'td.col-company_name .ng-binding, td.col-company_name a',
    'phone_number': 'td.col-phone .ng-binding, td.col-phone a',
    'city': 'td.col-city .ng-binding, td.col-city',
    'address': 'td.col-address .ng-binding, td.col-address',
    'next_button': [
        'button.paginationBtn[title="Page suivante"]',
        'button.paginationBtn[data-ng-click="getPage(1)"]',
        'button:has-text(">")',
        'a:has-text(">")'
    ],
    'main_table': 'table'
}

# Configuration des fichiers de sortie
OUTPUT_CONFIG = {
    'filename_prefix': 'kompass_data',
    'date_format': '%Y%m%d_%H%M%S',
    'excel_sheets': {
        'phones': 'Téléphones',
        'companies': 'Entreprises'
    }
}