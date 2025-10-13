from __future__ import annotations

import time
import base64
import os
import pyautogui
import tempfile
from queue import Queue, Empty
from threading import Thread
from typing import Optional, Tuple
from . import config
from . import waiters
from . import hotkeys
import pyperclip
import subprocess

SNIPPET_DIR = config.BASE_DIR / "scripts"

# --- réglages (ajuste si nécessaire) ---
CHUNK_SIZE = 600          # caractères par bloc (baisse si la VM perd des chars)
DELAY_BETWEEN = 0.002     # délai entre chunks (0 = max speed, risque perte si trop rapide)
QUEUE_TIMEOUT = 0.2

def _load_snippet(snippet_name: str) -> str:
    path = SNIPPET_DIR / snippet_name
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"Lecture snippet JS echouee: {exc} ({path})") from exc


def open_snippet_in_notepad(snippet_name: str) -> None:
    """
    Ouvre le fichier du snippet dans Notepad, copie son contenu, puis
    ferme Notepad avec les commandes demandées.
    """
    # Résoudre le chemin du snippet (dans scripts/ par défaut)
    path = SNIPPET_DIR / snippet_name
    if not path.exists():
        raise FileNotFoundError(f"Snippet introuvable: {path}")

    # Lecture/validation
    try:
        _ = path.read_text(encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"Lecture snippet JS echouee: {exc} ({path})") from exc

    # Ouvrir Notepad, copier, fermer
    np = subprocess.Popen(["notepad.exe", str(path)])
    time.sleep(1.0)
    hotkeys.select_all()
    time.sleep(0.2)
    hotkeys.copy()
    time.sleep(0.3)
    # Fermer Notepad via les commandes fournies
    try:
        subprocess.run(["taskkill", "/F", "/IM", "notepad.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["taskkill", "/F", "/IM", "notepadapp.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass





def paste_snipet(snippet: str,
                 use_base64: bool = True,
                 auto_focus_console: bool = False,
                 focus_coords: Optional[tuple] = None) -> None:
    """
    Ouvre la console (Ctrl+Shift+K), vide-la, injecte le snippet et appuie Enter.
    - snippet: code JS brut (UTF-8) à injecter
    - use_base64: si True (recommandé) encode en base64 et tape le wrapper ASCII
    - auto_focus_console: si True, le code cliquera automatiquement pour s'assurer du focus
    - focus_coords: (x,y) si tu veux un clic précis pour le focus
    """
    # 0) délai avant démarrage (garde ton timing d'origine)
    time.sleep(0.8)

    # Méthode demandée: ouvrir directement le fichier du snippet dans Notepad,
    # copier, fermer (via taskkill fournis), puis coller dans la console
    try:
        candidate = (snippet or "").strip()
        if candidate:
            # si c'est un nom de fichier .js, on va chercher dans scripts/
            if candidate.lower().endswith('.js'):
                open_snippet_in_notepad(candidate)
                hotkeys.open_chrome_console()
                time.sleep(0.8)
                hotkeys.select_all()
                pyautogui.press("backspace")
                time.sleep(0.1)
                hotkeys.paste()
                time.sleep(0.2)
                pyautogui.press("enter")
                time.sleep(0.1)
                return
    except Exception:
        # Si Notepad échoue, on retombera sur la logique existante ci‑dessous
        pass

    # 1) ouvrir la console (Ctrl+Shift+K)
    hotkeys.open_chrome_console()
    time.sleep(0.8)

    # 2) sélectionner tout et vider (Ctrl+A puis Backspace)
    hotkeys.select_all()
    pyautogui.press("backspace")
    time.sleep(0.1)
    # Ut
    # ilise les commandes système, mais seulement pour Windows
    pyperclip.copy('')
    time.sleep(0.05)
    pyperclip.copy(snippet)
    proc = subprocess.Popen(
        ['powershell', '-command', 'Set-Clipboard'],
        stdin=subprocess.PIPE,
        close_fds=True
    )
    time.sleep(0.5)
    hotkeys.paste()
    time.sleep(0.1)
    return

    # 3) injection sûre
    if use_base64:
        print(f"Injection via base64: {snippet}")
        # wrapper ASCII safe qui contient le code encodé en base64
        wrapper = make_base64_wrapper(snippet)
        # tape la ligne wrapper rapidement ; si tu veux, active auto_focus_console
        type_one_line_fast(wrapper, focus_delay=0.0, auto_focus=auto_focus_console, focus_coords=focus_coords)
    else:
        # fallback : taper le snippet brut (risque d'illegal char)
        type_one_line_fast(snippet, focus_delay=0.0, auto_focus=auto_focus_console, focus_coords=focus_coords)

    # 4) courte pause puis Enter pour exécuter
    time.sleep(0.2)
    pyautogui.press("enter")
    # marqueur de fin : petite pause
    time.sleep(0.1)


# ---------- Utilities ----------

def make_base64_wrapper(js_text: str) -> str:
    """
    Retourne une seule ligne JS ASCII qui décode le base64 et exécute le script.
    Utilise TextDecoder et new Function pour compatibilité moderne.
    """
    b64 = base64.b64encode(js_text.encode("utf-8")).decode("ascii")
    wrapper = (
        ("(function(){"
        "try{"
        "var s=atob('" + b64 + "');"
        "var bytes=new Uint8Array(s.split('').map(function(c){return c.charCodeAt(0);}));"
        "var code=new TextDecoder('utf-8').decode(bytes);"
        "new Function(code)();"
        "console.log('SCRIPT_INJECTED_OK');"
        "}catch(e){console.error('INJECTION_ERROR',e);}"
        "})();")
    )
    return wrapper
# (Anciennes fonctions utilitaires AZERTY supprimées car non utilisées)
# ---------- Fast typing (pyautogui only) ----------
def _send_chunk(chunk: str):
    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False
    pyautogui.typewrite(chunk, interval=0)

def _producer_chunks(text: str, queue: Queue):
    n = len(text)
    pos = 0
    while pos < n:
        end = min(n, pos + CHUNK_SIZE)
        queue.put(text[pos:end])
        pos = end
    queue.put(None)  # signal fin

def _consumer_thread(queue: Queue):
    while True:
        try:
            chunk = queue.get(timeout=QUEUE_TIMEOUT)
        except Empty:
            continue
        if chunk is None:
            break
        _send_chunk(chunk)
        if DELAY_BETWEEN:
            time.sleep(DELAY_BETWEEN)
        queue.task_done()

def type_one_line_fast(text: str, focus_delay: float = 0.2, auto_focus: bool = False,
                      focus_coords: Optional[Tuple[int,int]] = None):
    """
    Tape une longue ligne ASCII rapidement dans la fenêtre active.
    - focus_delay: délai avant de commencer (laisser le temps au focus)
    - auto_focus: si True, effectue un clic avant d'écrire
    - focus_coords: (x, y) coordonnées du clic si auto_focus True; None => clic au centre
    """
    # petit délai pour permettre au caller de s'assurer que la fenêtre est prête
    time.sleep(focus_delay)

    if auto_focus:
        # clique automatiquement pour donner le focus ; si coords non fournies, clic au centre de l'écran.
        if focus_coords:
            pyautogui.click(focus_coords[0], focus_coords[1])
        else:
            # clic au centre de la fenêtre active (approx écran center)
            screen_w, screen_h = pyautogui.size()
            pyautogui.click(screen_w // 2, screen_h // 2)
        time.sleep(0.05)  # short wait after click

    q = Queue(maxsize=10)
    consumer = Thread(target=_consumer_thread, args=(q,), daemon=True)
    consumer.start()
    _producer_chunks(text, q)
    consumer.join()

 


def  _execute_snippet(snippet_name: str, *, wait_for_page_load: bool = False) -> None:
    snippet = _load_snippet(snippet_name)
    print(f"[INFO] Execution du snippet: {snippet_name}")
    if wait_for_page_load:
        print("[INFO] Attente du chargement de la page Interlocuteur...")
        detected = waiters.wait_for_image_on_screen(
            config.LIST_INTERLOCUTOR_IMAGE,
            timeout=20.0,
            interval=0.5,
        )
        if not detected:
            raise RuntimeError("Chargement Interlocuteur non detecte (image list-interlocutors.png introuvable).")
        
        print("[INFO] Page Interlocuteur detectee, execution du snippet...")
        time.sleep(0.3)
       

    try:
        paste_snipet(snippet_name)
        time.sleep(0.5)
        if snippet_name in ("dom_interlocuteurs_snippet.js", "dom_get_first_interlocuteurs_snippet.js"):
            detected = waiters.wait_for_any_image_on_screen(
                config.SEARCH_RESULT_TEMPLATES,
                timeout=60.0,
                interval=0.5,
            )
            if not detected:
                raise RuntimeError("Resultat de recherche non detecte (image result-cancel-ok.png, result-cancel.png ou result-ok.png introuvable).")
            else:
                print("[INFO] ✅ Resultat de recherche detecte, copie et execution du snippet...")
                time.sleep(0.3)
                hotkeys.select_all()
                time.sleep(0.3)
                hotkeys.copy()
                time.sleep(0.1)
                pyautogui.press("enter")
                time.sleep(0.5)
                print(f"[INFO] ✅  Resultat de recherche copie: {pyperclip.paste()}")
  
        
        #switchKeyboardLayout("fr-FR")
        print(f"[INFO] Snippet {snippet_name} colle et execute dans la console.")
    except Exception as exc:
        print(f"[WARN] Execution snippet {snippet_name} echouee: {exc}")

def open_interlocuteur_tab() -> None:
    """Ouvre l'iframe Interlocuteur dans un nouvel onglet via window.open."""
    _execute_snippet("open_interlocuteur_tab.js")


def run_dom_interlocuteurs_snippet() -> None:
    """Extrait les interlocuteurs directement depuis la page (onglet deja ouvert)."""
    _execute_snippet("dom_interlocuteurs_snippet.js", wait_for_page_load=True)

def run_dom_get_first_interlocuteurs_snippet() -> None:
    """Extrait les interlocuteurs directement depuis la page (onglet deja ouvert)."""
    _execute_snippet("dom_get_first_interlocuteurs_snippet.js")


__all__ = [
    "open_interlocuteur_tab",
    "run_dom_interlocuteurs_snippet",
    "run_dom_get_first_interlocuteurs_snippet",
]


