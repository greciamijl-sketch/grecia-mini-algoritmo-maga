import json
import os
import re
import html
import time
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
X_AUTH_TOKEN = os.environ.get("X_AUTH_TOKEN", "").strip().strip('"').strip("'")
X_CT0 = os.environ.get("X_CT0", "").strip().strip('"').strip("'")

STATE_FILE = "last_seen_maga.json"

MAX_EMPTY_IN_A_ROW = 5

# ================= DIRECTORIO DE MONITOREO MAGA (50 CUENTAS) =================
X_SOURCES = [
    {"category": "CONGRESO / SENADO", "author": "Mike Lee", "handle": "BasedMikeLee"},
    {"category": "CAMPAÑA / COMUNICACIÓN", "author": "Trump War Room", "handle": "TrumpWarRoom"},
    {"category": "MEDIOS DIGITALES", "author": "Eric Daugherty", "handle": "EricLDaugh"},
    {"category": "COMUNIDAD MAGA", "author": "MAGA Voice", "handle": "MAGAVoice"},
    {"category": "REPORTERO INDEPENDIENTE", "author": "Nick Sortor", "handle": "nicksortor"},
    {"category": "RESPUESTA RÁPIDA", "author": "Rapid Response 47", "handle": "RapidResponse47"},
    {"category": "COMENTARISTA", "author": "Gunther Eagleman", "handle": "GuntherEagleman"},
    {"category": "CADENA NOTICIAS", "author": "RSBN", "handle": "RSBNetwork"},
    {"category": "CADENA NOTICIAS", "author": "Real America's Voice", "handle": "RealAmVoice"},
    {"category": "ACTIVISMO DIGITAL", "author": "Johnny MAGA", "handle": "johnnymaga"},
    {"category": "PODCAST / MEDIOS", "author": "Benny Johnson", "handle": "bennyjohnson"},
    {"category": "INTELIGENCIA / DEFENSA", "author": "The SCIF", "handle": "TheSCIF"},
    {"category": "ACTIVISMO / INVESTIGACIÓN", "author": "Laura Loomer", "handle": "LauraLoomer"},
    {"category": "ANÁLISIS POLÍTICO", "author": "Rob N.", "handle": "Real_RobN"},
    {"category": "LIDERAZGO TECH", "author": "Elon Musk", "handle": "elonmusk"},
    {"category": "CONGRESO / SENADO", "author": "Lindsey Graham", "handle": "LindseyGrahamSC"},
    {"category": "GABINETE / COMERCIO", "author": "Howard Lutnick", "handle": "howardlutnick"},
    {"category": "DIPLOMACIA", "author": "US Amb India", "handle": "USAmbIndia"},
    {"category": "FINANZAS / MERCADOS", "author": "Alternative Capital", "handle": "altcap"},
    {"category": "ANÁLISIS ESTRATÉGICO", "author": "Nathaniel Sami", "handle": "NathanielSami"},
    {"category": "FRONTERA / SINDICATO", "author": "Border Patrol Union", "handle": "BPUnion"},
    {"category": "GOBIERNO EE.UU.", "author": "Dept of the Interior", "handle": "Interior"},
    {"category": "ANÁLISIS POLÍTICO", "author": "M. Cucolo", "handle": "mcucolo57"},
    {"category": "MEDIOS / OPINIÓN", "author": "Glenn Beck", "handle": "glennbeck"},
    {"category": "ESTRATEGIA DIGITAL", "author": "Bo Loudon", "handle": "BoLoudon"},
    {"category": "NOTICIAS URGENTES", "author": "Breaking911", "handle": "Breaking911"},
    {"category": "OPINIÓN / REDES", "author": "Eyal Yakoby", "handle": "EYakoby"},
    {"category": "COMENTARISTA", "author": "Mr. Whiplash", "handle": "MrWhiplash_"},
    {"category": "MONITOREO CULTURAL", "author": "Libs of TikTok", "handle": "libsoftiktok"},
    {"category": "RADIO / CONSTITUCIÓN", "author": "Mark R. Levin", "handle": "marklevinshow"},
    {"category": "COLUMNA / ANÁLISIS", "author": "Marc Thiessen", "handle": "marcthiessen"},
    {"category": "ANÁLISIS POLÍTICO", "author": "Jack Posobiec", "handle": "JackPosobiec"},
    {"category": "CONGRESO / POLÍTICA", "author": "Abraham Hamadeh", "handle": "AbrahamHamadeh"},
    {"category": "JUSTICIA EE.UU.", "author": "Department of Justice", "handle": "TheJusticeDept"},
    {"category": "CONGRESO / SENADO", "author": "Rand Paul", "handle": "SenRandPaul"},
    {"category": "MEDIOS INDEPENDIENTES", "author": "The Vigilant Fox", "handle": "VigilantFox"},
    {"category": "COMUNICACIÓN POLÍTICA", "author": "Steve Guest", "handle": "SteveGuest"},
    {"category": "PRESIDENCIA EE.UU.", "author": "Donald J. Trump", "handle": "realDonaldTrump"},
    {"category": "CASA BLANCA", "author": "The White House", "handle": "WhiteHouse"},
    {"category": "COMENTARISTA DIGITAL", "author": "TaraBull", "handle": "TaraBull"},
    {"category": "MERCADOS / POLÍTICA", "author": "Wall Street Apes", "handle": "WallStreetApes"},
    {"category": "ACTIVISMO POLÍTICO", "author": "Brigitte Gabriel", "handle": "ACTBrigitte"},
    {"category": "CONGRESO / CÁMARA", "author": "Anna Paulina Luna", "handle": "RepLuna"},
    {"category": "PARTIDO REPUBLICANO", "author": "House Republicans", "handle": "Republicans"},
    {"category": "NOTICIAS RÁPIDAS", "author": "The Insider Paper", "handle": "TheInsiderPaper"},
    {"category": "CADENA MEDIOS", "author": "TheBlaze", "handle": "theblaze"},
    {"category": "PODCAST POLÍTICO", "author": "Steak for Breakfast", "handle": "SteakforPodcast"},
    {"category": "OPINIÓN / REDES", "author": "JayTC53", "handle": "JayTC53"},
    {"category": "INTELIGENCIA FUENTES ABIERTAS", "author": "C_3C_3", "handle": "C_3C_3"},
    {"category": "CÍRCULO TRUMP", "author": "Donald Trump Jr.", "handle": "DonaldJTrumpJr"}
]

# ================= FILTRO TEMÁTICO RIGUROSO =================
KEYWORDS_REGEX = re.compile(
    r"\b("
    r"m[eé]xic\w*|mexique|messico|mexiko|"
    r"claudia\s*sheinbaum|sheinbaum|@claudiashein|"
    r"c[aá]rtel\w*|"
    r"tariff\w*|arancel\w*|tarifa\w*|"
    r"usmca|t-?mec|tmec|nafta"
    r")\b",
    re.IGNORECASE
)


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def clean_html(raw_html):
    clean = re.sub(r"<[^>]+>", " ", raw_html)
    return " ".join(clean.split())


def send_telegram(category, author, text, link):
    safe_text = html.escape(text)
    message = (
        f"🚨 <b>[GreciaMini-MAGA - {category}]</b>\n"
        f"👤 <b>Fuente:</b> {author}\n\n"
        f"{safe_text}\n\n"
        f"🔗 <a href='{link}'>Ver publicación</a>"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if not r.ok:
            print(f"❌ Telegram error {r.status_code}: {r.text}", flush=True)
    except Exception as e:
        print(f"Error al enviar mensaje a Telegram: {e}", flush=True)


def wait_challenge(page, max_wait=25):
    for _ in range(max_wait):
        try:
            title = (page.title() or "").lower()
        except Exception:
            title = ""
        if "un momento" not in title and "just a moment" not in title:
            return True
        time.sleep(1)
    return False


def check_login(page):
    page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=25000)
    if not wait_challenge(page, 25):
        print("🛡️ Cloudflare bloqueó al runner. Se reintentará en el próximo ciclo.", flush=True)
        return False
    time.sleep(3)
    return "login" not in page.url and "/i/flow" not in page.url


def scrape_tweets(page, handle):
    page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=20000)

    if not wait_challenge(page, 15):
        print(f"🛡️ @{handle}: Cloudflare bloqueando.", flush=True)
        return []

    try:
        page.wait_for_selector("article[data-testid='tweet']", timeout=12000)
    except Exception:
        print(f"⚠️ @{handle}: sin tuits visibles en el DOM.", flush=True)
        return []

    for _ in range(2):
        page.mouse.wheel(0, 800)
        time.sleep(0.8)

    tweet_elements = page.locator("article[data-testid='tweet']").all()[:6]

    tweets = []
    for art in tweet_elements:
        try:
            link_elem = art.locator("a[href*='/status/']").first
            href = link_elem.get_attribute("href") if link_elem.count() > 0 else None
            if not href or "/status/" not in href:
                continue

            match_id = re.search(r"/status/(\d+)", href)
            if not match_id:
                continue
            tweet_id = match_id.group(1)

            text_elem = art.locator("[data-testid='tweetText']").first
            text = text_elem.inner_text() if text_elem.count() > 0 else art.inner_text()

            tweets.append({
                "id": tweet_id,
                "text": text,
                "link": f"https://x.com{href}" if href.startswith("/") else href
            })
        except Exception:
            continue

    return tweets


def main():
    state = load_state()
    is_initial_run = (len(state) == 0)

    print(f"=== INICIANDO MONITOREO MAGA: {len(X_SOURCES)} FUENTES ===", flush=True)

    if not X_AUTH_TOKEN or not X_CT0:
        print("❌ Faltan los secrets de sesión X_AUTH_TOKEN o X_CT0.", flush=True)
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="es-ES",
            viewport={"width": 1280, "height": 900}
        )

        context.add_cookies([
            {"name": "auth_token", "value": X_AUTH_TOKEN, "domain": ".x.com", "path": "/"},
            {"name": "ct0", "value": X_CT0, "domain": ".x.com", "path": "/"},
            {"name": "auth_token", "value": X_AUTH_TOKEN, "domain": "x.com", "path": "/"},
            {"name": "ct0", "value": X_CT0, "domain": "x.com", "path": "/"}
        ])

        page = context.new_page()

        if not check_login(page):
            print("❌ Sesión de X no válida. Verifica las cookies en Secrets.", flush=True)
            browser.close()
            return

        empty_in_a_row = 0

        for source in X_SOURCES:
            category = source["category"]
            author = source["author"]
            handle = source["handle"]
            last_id = state.get(handle)

            try:
                tweets = scrape_tweets(page, handle)
            except Exception as e:
                print(f"❌ Error al consultar @{handle}: {e}", flush=True)
                empty_in_a_row += 1
                if empty_in_a_row >= MAX_EMPTY_IN_A_ROW:
                    print("⛔ Demasiados fallos seguidos. Pausa de seguridad para proteger sesión.", flush=True)
                    break
                continue

            print(f"✅ @{handle}: {len(tweets)} tuits obtenidos.", flush=True)

            if not tweets:
                empty_in_a_row += 1
                if empty_in_a_row >= MAX_EMPTY_IN_A_ROW:
                    print("⛔ Múltiples cuentas vacías seguidas. Fin preventivo de corrida.", flush=True)
                    break
                continue

            empty_in_a_row = 0

            newest_id = max(tweets, key=lambda t: int(t["id"]))["id"]

            if is_initial_run or last_id is None:
                state[handle] = newest_id
                continue

            try:
                last_int = int(last_id)
            except ValueError:
                state[handle] = newest_id
                continue

            new_tweets = [t for t in tweets if int(t["id"]) > last_int]
            new_tweets.sort(key=lambda t: int(t["id"]))

            for t in new_tweets:
                full_text = clean_html(t["text"])
                if KEYWORDS_REGEX.search(full_text):
                    print(f"🚨 Coincidencia en @{handle}: {full_text[:60]}", flush=True)
                    preview = full_text[:400] + ("..." if len(full_text) > 400 else "")
                    send_telegram(category, f"{author} (@{handle})", preview, t["link"])

            if new_tweets:
                state[handle] = newest_id

        browser.close()

    save_state(state)
    print("\n=== FIN DEL MONITOREO GRECIA-MINI-ALGORITMO-MAGA ===", flush=True)


if __name__ == "__main__":
    main()
