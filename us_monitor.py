import json
import os
import re
import html
import feedparser
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STATE_FILE = "last_seen_us.json"

# ================= 50 CUENTAS POLÍTICAS Y MEDIÁTICAS =================
HANDLES = [
    "GreciMM18", "BasedMikeLee", "TrumpWarRoom", "EricLDaugh", "MAGAVoice", "GuntherEagleman",
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

SOURCES = [
    {
        "handle": f"@{h}",
        "url": f"https://nitter.privacydev.net/{h}/rss"
    }
    for h in HANDLES
]

# ================= FILTRO ESPECÍFICO =================
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
    message = f"""🦅 <b>[GreciaMiniAlgoritmoMAGA]</b>
👤 <b>Cuenta:</b> {handle}

{safe_text}

🔗 <a href="{link}">Ver publicación original</a>"""

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
        print(f"Error al enviar a Telegram: {e}")

def main():
    state = load_state()
    is_initial_run = (len(state) == 0)

    for source in SOURCES:
        handle = source["handle"]
        url = source["url"]
        last_id = state.get(handle)

        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        except Exception:
            continue

        if not feed.entries:
            continue

        if is_initial_run or last_id is None:
            state[handle] = feed.entries[0].get("id", feed.entries[0].link)
            continue

        new_entries = []
        for entry in feed.entries:
            entry_id = entry.get("id", entry.link)
            if entry_id == last_id:
                break
            new_entries.append(entry)

        for entry in reversed(new_entries):
            raw_title = entry.get("title", "")
            raw_summary = entry.get("summary", "")
            full_text = clean_html(f"{raw_title} {raw_summary}")

            if KEYWORDS_REGEX.search(full_text):
                preview = full_text[:400] + ("..." if len(full_text) > 400 else "")
                send_telegram(handle, preview, entry.link)

        if new_entries:
            state[handle] = new_entries[0].get("id", new_entries[0].link)

    save_state(state)

if __name__ == "__main__":
    main()
