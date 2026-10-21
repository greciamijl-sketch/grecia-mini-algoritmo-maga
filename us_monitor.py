import json
import os
import re
import html
import requests
from ntscraper import Nitter

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STATE_FILE = "last_seen_us.json"

# ================= LISTA DE CUENTAS MONITOREADAS =================
HANDLES = [
    "GreciMM18",  # Cuenta para pruebas directas
    "BasedMikeLee", "TrumpWarRoom", "EricLDaugh", "MAGAVoice", "GuntherEagleman",
    "TheSCIF", "RapidResponse47", "bennyjohnson", "nicksortor", "JackPosobiec",
    "Real_RobN", "LauraLoomer", "NathanielSami", "LindseyGrahamSC", "elonmusk",
    "johnnymaga", "mcucolo57", "Interior", "libsoftiktok", "BPUnion",
    "howardlutnick", "SenRandPaul", "realDonaldTrump", "USAmbIndia", "altcap",
    "TheJusticeDept", "MrWhiplash_", "BuzzPatterson", "OneBadDude_", "WallStreetApes",
    "marklevinshow", "VigilantFox", "marcthiessen", "TaraBull", "WhiteHouse",
    "ACTBrigitte", "AbrahamHamadeh", "SteveGuest", "JayTC53", "EYakoby",
    "JDunlap1974", "its_Lexieroy", "irishpatriot91", "glennbeck", "interiorpress47",
    "FoxNews", "GreereMedeea", "FreedomCaucusF", "IngrahamAngle", "IHF_Heritage"
]

# ================= FILTRO ESTRICTO =================
KEYWORDS_REGEX = re.compile(
    r"\b("
    r"m[eé]xic\w*|mexican\w*|"
    r"claudia\s*sheinbaum|sheinbaum|"
    r"roberto\s*velasco|velasco\s*[aá]lvarez|@r_velascoa|"
    r"usmca|t-?mec|nafta\s*2\.0"
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

def send_telegram(handle, text, link):
    safe_text = html.escape(text)
    message = (
        f"🦅 <b>[GreciaMiniAlgoritmoMAGA]</b>\n"
        f"👤 <b>Cuenta:</b> @{handle}\n\n"
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
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error al enviar mensaje: {e}")

def main():
    state = load_state()
    is_initial_run = (len(state) == 0)

    scraper = Nitter(log_level=0)

    for handle in HANDLES:
        last_link = state.get(handle)

        try:
            tweets_data = scraper.get_tweets(handle, mode="user", number=5)
            tweets = tweets_data.get("tweets", [])
        except Exception as e:
            print(f"Error al consultar @{handle}: {e}")
            continue

        if not tweets:
            continue

        if is_initial_run or last_link is None:
            state[handle] = tweets[0]["link"]
            continue

        new_tweets = []
        for t in tweets:
            t_link = t["link"]
            if t_link == last_link:
                break
            new_tweets.append(t)

        for t in reversed(new_tweets):
            full_text = clean_html(t.get("text", ""))

            if KEYWORDS_REGEX.search(full_text):
                preview = full_text[:400] + ("..." if len(full_text) > 400 else "")
                send_telegram(handle, preview, t["link"])

        if new_tweets:
            state[handle] = new_tweets[0]["link"]

    save_state(state)

if __name__ == "__main__":
    main()
