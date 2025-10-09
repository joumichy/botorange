#!/usr/bin/env python3
"""
Script simple pour scraper Kompass sans bloquer le navigateur
"""
import asyncio
import pandas as pd
from playwright.async_api import async_playwright
from datetime import datetime

import signal
import sys
import os
import glob
from config import SCRAPING_CONFIG, SELECTORS, OUTPUT_CONFIG

# Variable globale pour stocker les résultats partiels
_partial_results = []


def _get_output_dir():
    """Return a directory next to the executable/app when frozen.

    - macOS (.app): dist/<Name>/ (parent of the .app bundle)
    - Windows: dist/<Name>/ (folder of the .exe)
    - Dev: folder of this source file
    """
    try:
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
            # Detect macOS .app bundle and go three levels up to the dist folder
            if sys.platform == "darwin" and "/Contents/MacOS" in exe_dir.replace("\\", "/"):
                return os.path.abspath(os.path.join(exe_dir, "..", "..", ".."))
            return exe_dir
    except Exception:
        pass
    # Not frozen: write next to source
    return os.path.dirname(os.path.abspath(__file__))

def _save_partial_results():
    """Sauvegarde les résultats partiels en cas d'interruption"""
    global _partial_results
    if _partial_results:
        try:
            df = pd.DataFrame(_partial_results)
            date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            out_dir = _get_output_dir()
            partial_file = os.path.join(out_dir, f"kompass_data_partial_{date_str}.xlsx")
            
            # Sauvegarder avec la même structure que le fichier final
            with pd.ExcelWriter(partial_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=OUTPUT_CONFIG['excel_sheets']['companies'], index=False)
            
            print(f"\n[SAUVEGARDE PARTIELLE] Résultats sauvegardés dans: {partial_file}")
            print(f"[SAUVEGARDE PARTIELLE] {len(_partial_results)} entreprises sauvegardées")
        except Exception as e:
            print(f"[ERREUR SAUVEGARDE PARTIELLE] {e}")

def _signal_handler(signum, frame):
    """Gestionnaire de signal pour les interruptions"""
    print(f"\n[INTERRUPTION DÉTECTÉE] Signal {signum} reçu")
    _save_partial_results()
    sys.exit(0)

async def fetch_siret_for_company(context, company_info, index, total):
    """Récupère le SIRET d'une entreprise dans un nouvel onglet"""
    if not company_info.get('detailUrl'):
        return company_info, ""
    
    page = None
    try:
        # Créer un nouvel onglet dans le même contexte de navigateur
        page = await context.new_page()
        
        # Aller sur la page principale puis naviguer vers le détail
        full_url = f"https://fr.kompass.com/easybusiness{company_info['detailUrl']}"
        await page.goto(full_url, timeout=15000)
        
        # Attendre que le SIRET soit visible
        await page.wait_for_selector('#detail-registration-numbers', timeout=10000)
        
        # Extraire le SIRET
        siret = await page.evaluate("""
        () => {
            const siretElement = document.querySelector('#detail-registration-numbers');
            if (siretElement) {
                return siretElement.textContent.trim().replace(/\\s+/g, '');
            }
            return '';
        }
        """)
        
        print(f"  [{index+1}/{total}] ✅ {company_info['company'][:40]:<40} SIRET: {siret}")
        return company_info, siret
        
    except Exception as e:
        print(f"  [{index+1}/{total}] ❌ {company_info['company'][:40]:<40} Erreur: {str(e)[:30]}")
        return company_info, ""
    finally:
        if page:
            try:
                await page.close()
            except:
                pass


async def wait_for_next_button_enabled(page, max_wait_time=3000, poll_interval=200):
    """
    Attend que le bouton next soit activé avec polling
    Args:
        page: Page Playwright
        max_wait_time: Temps maximum d'attente en millisecondes (défaut: 3000ms)
        poll_interval: Intervalle de polling en millisecondes (défaut: 200ms)
    Returns:
        tuple: (button_element, is_enabled) ou (None, False) si timeout
    """
    start_time = asyncio.get_event_loop().time()
    max_wait_seconds = max_wait_time / 1000
    poll_seconds = poll_interval / 1000
    
    print(f"⏳ Attente de l'activation du bouton next (max {max_wait_time}ms)...")
    
    while (asyncio.get_event_loop().time() - start_time) < max_wait_seconds:
        # Chercher le bouton next avec tous les sélecteurs
        next_button = None
        for selector in SELECTORS['next_button']:
            try:
                next_button = await page.query_selector(selector)
                if next_button:
                    break
            except:
                continue
        
        if next_button:
            try:
                # Vérifier si le bouton est activé
                is_enabled = await next_button.is_enabled()
                is_disabled = await next_button.get_attribute('data-ng-disabled')
                
                # Le bouton est considéré comme activé si:
                # - is_enabled est True ET
                # - data-ng-disabled n'est pas "true" (ou est None)
                if is_enabled and is_disabled != "true":
                    elapsed = int((asyncio.get_event_loop().time() - start_time) * 1000)
                    print(f"✅ Bouton next activé après {elapsed}ms")
                    return next_button, True
                else:
                    # Afficher le statut pour debug
                    print(f"🔄 Bouton trouvé mais désactivé (enabled: {is_enabled}, disabled: {is_disabled})")
            except Exception as e:
                print(f"⚠️ Erreur lors de la vérification du bouton: {e}")
        else:
            print("🔄 Bouton next non trouvé, nouvelle tentative...")
        
        # Attendre avant la prochaine vérification
        await asyncio.sleep(poll_seconds)
    
    # Timeout atteint
    elapsed = int((asyncio.get_event_loop().time() - start_time) * 1000)
    print(f"⏰ Timeout atteint après {elapsed}ms - bouton next non activé")
    return None, False

async def main():
    """Script principal de scraping"""
    print("=== Scraper Kompass EasyBusiness ===")
    print("Ce script va ouvrir un navigateur et vous guider pour le scraping")
    print("💡 Astuce: Appuyez sur Ctrl+C à tout moment pour sauvegarder les résultats partiels")
    print()
    
    # Configurer le gestionnaire de signal pour les interruptions
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    
    # Réinitialiser les résultats partiels
    global _partial_results
    _partial_results.clear()
    
    # Demander le nombre de pages
    try:
        max_pages = int(input("Nombre de pages à scraper (défaut: 3): ") or "3")
    except ValueError:
        max_pages = 3
    
    # Demander si on veut extraire les SIRET
    extract_siret = input("\nExtraire les numéros SIRET ? (y/n, défaut: n): ").lower().strip()
    extract_siret = extract_siret in ['y', 'yes', 'o', 'oui']
    
    # Si extraction SIRET activée, demander le niveau de parallélisme
    parallel_limit = 5
    if extract_siret:
        try:
            parallel_limit = int(input("Nombre de pages de détail SIRET en parallèle (défaut: 5, max: 10): ") or "5")
            parallel_limit = min(parallel_limit, 10)  # Limiter à 10 pour ne pas surcharger
        except ValueError:
            parallel_limit = 5
    
    print(f"\nConfiguration:")
    print(f"  Pages de résultats: {max_pages}")
    if extract_siret:
        print(f"  Extraction SIRET: OUI ({parallel_limit} pages de détail simultanées)")
    else:
        print(f"  Extraction SIRET: NON (scraping rapide)")
    
    # Confirmation
    confirm = input("\nVoulez-vous continuer ? (y/n): ").lower()
    if confirm != 'y':
        print("Annulé")
        return
    
    all_companies = []
    
    async with async_playwright() as p:
        # Lancer le navigateur
        browser = await p.chromium.launch(
            headless=SCRAPING_CONFIG['headless'],
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent=SCRAPING_CONFIG['user_agent']
        )
        page = await context.new_page()
        
        try:
            print("\n✅ Navigateur lancé")
            print("🌐 Navigation automatique vers Kompass EasyBusiness...")
            
            # Navigation automatique vers l'URL
            await page.goto("https://fr.kompass.com/easybusiness#/")
            print("✅ Page Kompass EasyBusiness chargée")
            
            print("\n📋 Instructions:")
            print("1. Connectez-vous à votre compte Kompass si nécessaire")
            print("2. Effectuez votre recherche et allez sur la page avec les résultats")
            print("3. Revenez dans ce terminal et appuyez sur Entrée")
            print()
            print("⏳ En attente...")
            
            # Attendre que l'utilisateur soit prêt avec les résultats
            input("Appuyez sur Entrée quand vous êtes sur la page avec les résultats de recherche...")
            
            # Attendre un peu pour que la page se charge
            await page.wait_for_timeout(2000)
            
            # Vérifier que la page contient des résultats
            try:
                await page.wait_for_selector('table tbody tr', timeout=10000)
                print("✅ Page avec résultats détectée")
            except:
                print("⚠️ Aucun résultat trouvé sur cette page")
                return
            
            for page_num in range(1, max_pages + 1):
                print(f"\n{'='*60}")
                print(f"📄 Scraping de la page {page_num}/{max_pages}")
                print(f"{'='*60}")
                
                # Attendre que le tableau soit chargé
                try:
                    await page.wait_for_selector(SELECTORS['main_table'], timeout=15000)
                except:
                    print("Tableau non trouvé, tentative de recherche alternative...")
                
                # Extraire les informations de base + les liens de détail
                company_links = await page.evaluate(f"""
                () => {{
                    const results = [];
                    const rows = document.querySelectorAll('table tbody tr');
                    
                    const selectors = {{
                        company: `{SELECTORS['company_name']}`,
                        phone: `{SELECTORS['phone_number']}`,
                        city: `{SELECTORS['city']}`,
                        address: `{SELECTORS['address']}`
                    }};
                    
                    rows.forEach((row, index) => {{
                        // Extraire les données de base
                        const companyElement = row.querySelector(selectors.company);
                        const phoneElement = row.querySelector(selectors.phone);
                        const cityElement = row.querySelector(selectors.city);
                        const addressElement = row.querySelector(selectors.address);
                        
                        // Trouver le lien de détail (avec l'attribut data-ng-href)
                        const detailLink = row.querySelector('a[role="button"][data-ng-href^="#/detail/"]');
                        
                        const rowData = {{
                            company: companyElement?.textContent.trim() || '',
                            phone: phoneElement?.textContent.trim() || '',
                            city: cityElement?.textContent.trim() || '',
                            address: addressElement?.textContent.trim() || '',
                            detailUrl: detailLink?.getAttribute('data-ng-href') || detailLink?.getAttribute('href') || null
                        }};
                        
                        // Fallback pour le téléphone
                        if (!rowData.phone) {{
                            const phoneRegex = /(\\+33\\s?[0-9\\s\\.\\-]{{8,}})|(0[1-9][0-9\\s\\.\\-]{{8,}})/;
                            const match = row.textContent.match(phoneRegex);
                            if (match) rowData.phone = match[0].trim();
                        }}
                        
                        if (rowData.company || rowData.phone) {{
                            results.push(rowData);
                        }}
                    }});
                    
                    return results;
                }}
                """)
                
                print(f"✅ Trouvé {len(company_links)} entreprises sur cette page")
                
                # Si extraction SIRET activée
                if extract_siret:
                    print(f"⏳ Récupération des SIRET en parallèle ({parallel_limit} simultanées)...\n")
                    
                    # Récupérer les SIRET en parallèle avec limite de concurrence
                    semaphore = asyncio.Semaphore(parallel_limit)
                    
                    async def fetch_with_semaphore(company_info, idx):
                        async with semaphore:
                            return await fetch_siret_for_company(context, company_info, idx, len(company_links))
                    
                    tasks = [fetch_with_semaphore(info, idx) 
                            for idx, info in enumerate(company_links)]
                    results_with_siret = await asyncio.gather(*tasks)
                    
                    # Ajouter les données complètes avec SIRET
                    for company_info, siret in results_with_siret:
                        company_data = {
                            'company': company_info['company'],
                            'phone': company_info['phone'],
                            'city': company_info['city'],
                            'address': company_info['address'],
                            'siret': siret
                        }
                        all_companies.append(company_data)
                        _partial_results.append(company_data)
                    
                    print(f"\n📊 Total collecté jusqu'à présent: {len(_partial_results)} entreprises")
                    print(f"   Dont {sum(1 for c in _partial_results if c.get('siret'))} avec SIRET")
                else:
                    # Mode rapide sans SIRET
                    for company_info in company_links:
                        company_data = {
                            'company': company_info['company'],
                            'phone': company_info['phone'],
                            'city': company_info['city'],
                            'address': company_info['address']
                        }
                        all_companies.append(company_data)
                        _partial_results.append(company_data)
                    
                    print(f"📊 Total collecté jusqu'à présent: {len(_partial_results)} entreprises")
                
                # Aller à la page suivante si ce n'est pas la dernière page
                if page_num < max_pages:
                    try:
                        print(f"\n⏭️  Navigation vers la page {page_num + 1}...")
                        
                        # Utiliser la fonction d'attente avec polling pour le bouton next
                        next_button, is_enabled = await wait_for_next_button_enabled(page)
                        
                        if next_button and is_enabled:
                            await next_button.click()
                            await page.wait_for_timeout(SCRAPING_CONFIG['page_delay'])
                            print(f"✅ Navigation réussie vers la page {page_num + 1}\n")
                        else:
                            print("❌ Bouton suivant non trouvé ou non activé, arrêt du scraping")
                            break
                            
                    except Exception as e:
                        print(f"❌ Erreur lors de la navigation vers la page suivante: {e}")
                        break
            
        except KeyboardInterrupt:
            print("\n[INTERRUPTION] Sauvegarde des résultats partiels...")
            _save_partial_results()
            return
        except Exception as e:
            print(f"Erreur lors du scraping: {e}")
            _save_partial_results()
        
        finally:
            try:
                await context.close()
            except Exception:
                pass
            try:
                await browser.close()
            except Exception:
                pass
    
    # Afficher les résultats
    print(f"\n{'='*60}")
    print(f"=== Résultats Finaux ===")
    print(f"{'='*60}")
    print(f"Entreprises trouvées: {len(all_companies)}")
    if extract_siret:
        print(f"Avec SIRET: {sum(1 for c in all_companies if c.get('siret'))}")
        print(f"Sans SIRET: {sum(1 for c in all_companies if not c.get('siret'))}")
    
    # Sauvegarder les résultats finaux
    if all_companies:
        print("\nSauvegarde des résultats finaux...")
        
        # Créer le DataFrame des entreprises
        max_rows_env = os.getenv("KOMPASS_MAX_ROWS")
        if max_rows_env:
            try:
                limit = int(max_rows_env)
                if limit >= 0:
                    all_companies = all_companies[:limit]
                    print(f"Limitation active: enregistrement des {len(all_companies)} premières entrées")
            except Exception:
                pass
        df_companies = pd.DataFrame(all_companies)
        
        # Sauvegarder en Excel (seulement les entreprises)
        out_dir = _get_output_dir()
        filename = os.path.join(
            out_dir,
            f"{OUTPUT_CONFIG['filename_prefix']}_{datetime.now().strftime(OUTPUT_CONFIG['date_format'])}.xlsx",
        )
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            if not df_companies.empty:
                df_companies.to_excel(writer, sheet_name=OUTPUT_CONFIG['excel_sheets']['companies'], index=False)
        
        print(f"✅ Résultats finaux sauvegardés dans: {filename}")
    else:
        print("❌ Aucun résultat à sauvegarder")

if __name__ == "__main__":
    asyncio.run(main())
