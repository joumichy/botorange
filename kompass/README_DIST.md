# Distribution – KompassScraper (Windows & macOS)

Ce guide explique comment construire et livrer un exécutable « client » sans avoir à installer Python chez le client.

## Principe

- Emballage avec PyInstaller (format dossier « onedir »).
- Chromium Playwright téléchargé à l’avance dans `playwright-browsers/` et embarqué.
- Hook d’exécution PyInstaller qui pointe Playwright vers ce dossier.

## Prérequis build

- Windows 10/11 (pour build Windows) ou macOS (pour build macOS) – build natif par OS.
- Python 3.9+ installé sur la machine de build.
- Accès Internet sur la machine de build pour télécharger les dépendances et Chromium.

## Windows – étapes

1) Ouvrir un terminal PowerShell et se placer dans `kompass/`.
2) Lancer: `build_win.bat`
3) Résultat: `dist\KompassScraper\` avec `KompassScraper.exe` et `playwright-browsers\`.
4) Zipper le dossier `dist\KompassScraper\` et livrer au client.

## macOS – étapes

1) Ouvrir Terminal et se placer dans `kompass/`.
2) Rendre exécutable: `chmod +x build_mac.sh`
3) Lancer: `./build_mac.sh`
4) Résultat: `dist/KompassScraper/KompassScraper.app` et `playwright-browsers/`.
5) Zipper le dossier ou créer un DMG et livrer.

## Lancement côté client

- Windows: double‑cliquer `KompassScraper.exe`.
- macOS: double‑cliquer `KompassScraper.app` (peut nécessiter clic droit → Ouvrir si non signé).

Le navigateur s’ouvre, puis suivez les instructions en console.

## Conseils

- Si vous avez une icône, ajoutez l’option `--icon` dans les scripts de build.
- Pour signature/notarisation macOS, réaliser l’opération après génération de l’app.

