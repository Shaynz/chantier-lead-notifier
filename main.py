import os
import time
import requests
import json
from datetime import datetime, timezone

# Config depuis les variables d'environnement
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
BASE44_API_KEY = os.environ["BASE44_API_KEY"]
APP_ID = "6a5e86447b1f838a3df9339a"
ENTITY = "Lead"
CHECK_INTERVAL = 120  # secondes

LAST_SEEN_FILE = "last_seen_id.txt"

def get_last_seen_id():
    if os.path.exists(LAST_SEEN_FILE):
        with open(LAST_SEEN_FILE, "r") as f:
            return f.read().strip()
    return None

def save_last_seen_id(lead_id):
    with open(LAST_SEEN_FILE, "w") as f:
        f.write(lead_id)

def get_leads():
    url = f"https://api.base44.com/api/apps/{APP_ID}/entities/{ENTITY}"
    headers = {"api_key": BASE44_API_KEY}
    params = {"sort": "-created_date", "limit": 10}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def send_telegram(lead):
    budget = lead.get("monthly_ad_budget", "N/A")
    message = (
        f"🔔 *Nouveau Lead — Chantier Numérique*\n\n"
        f"🏢 *Nom:* {lead.get('company_name', 'N/A')}\n"
        f"📧 *Email:* {lead.get('email', 'N/A')}\n"
        f"🌐 *URL:* {lead.get('company_url', 'N/A')}\n"
        f"📞 *Téléphone:* {lead.get('phone', 'N/A')}\n"
        f"💰 *Budget mensuel:* {budget}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def main():
    print("✅ Démarrage du notifier Chantier Numérique...")
    
    # Initialiser avec le dernier lead connu
    leads = get_leads()
    if leads and not get_last_seen_id():
        save_last_seen_id(leads[0]["id"])
        print(f"Dernier lead existant: {leads[0]['id']}")

    while True:
        try:
            leads = get_leads()
            last_seen = get_last_seen_id()
            new_leads = []

            for lead in leads:
                if lead["id"] == last_seen:
                    break
                new_leads.append(lead)

            if new_leads:
                # Envoyer du plus ancien au plus récent
                for lead in reversed(new_leads):
                    send_telegram(lead)
                    print(f"Notif envoyée pour: {lead.get('company_name')} ({lead['id']})")
                save_last_seen_id(new_leads[0]["id"])

        except Exception as e:
            print(f"Erreur: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
