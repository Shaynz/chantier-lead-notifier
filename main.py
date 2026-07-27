import os
import time
import requests
from datetime import datetime, timezone

# Config depuis les variables d'environnement
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
BASE44_API_KEY = os.environ["BASE44_API_KEY"]
APP_ID = "6a5e86447b1f838a3df9339a"
CHECK_INTERVAL = 120  # secondes

def get_leads():
    url = f"https://api.base44.com/api/apps/{APP_ID}/entities/Lead/records"
    headers = {
        "api_key": BASE44_API_KEY,
        "Content-Type": "application/json"
    }
    params = {"sort": "-created_date", "limit": 10}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get("records", data.get("data", data.get("items", [])))
    return []

def send_telegram(lead):
    if "data" in lead:
        d = lead["data"]
    else:
        d = lead

    message = (
        f"🔔 *Nouveau Lead — Chantier Numérique*\n\n"
        f"🏢 *Nom:* {d.get('company_name', 'N/A')}\n"
        f"📧 *Email:* {d.get('email', 'N/A')}\n"
        f"🌐 *URL:* {d.get('company_url', 'N/A')}\n"
        f"📞 *Téléphone:* {d.get('phone', 'N/A')}\n"
        f"💰 *Budget mensuel:* {d.get('monthly_ad_budget', 'N/A')}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload)
    print(f"Telegram: {r.status_code}")

def parse_date(date_str):
    """Parse ISO date string to datetime."""
    if not date_str:
        return None
    try:
        # Enlever le Z et ajouter timezone UTC
        date_str = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(date_str)
    except:
        return None

def main():
    print("✅ Démarrage du notifier Chantier Numérique...")

    # On utilise l'heure de démarrage comme référence
    # On ne notifie que les leads créés APRÈS ce moment
    start_time = datetime.now(timezone.utc)
    print(f"Heure de démarrage: {start_time.isoformat()}")

    # Récupérer les IDs existants au démarrage pour ne pas re-notifier
    seen_ids = set()
    try:
        leads = get_leads()
        for lead in leads:
            seen_ids.add(lead["id"])
        print(f"{len(seen_ids)} leads existants ignorés.")
    except Exception as e:
        print(f"Erreur init: {e}")

    while True:
        try:
            leads = get_leads()
            new_leads = []

            for lead in leads:
                if lead["id"] not in seen_ids:
                    new_leads.append(lead)

            if new_leads:
                for lead in reversed(new_leads):
                    send_telegram(lead)
                    seen_ids.add(lead["id"])
                    print(f"✅ Notif envoyée: {lead.get('company_name', lead['id'])}")
            else:
                print(f"Aucun nouveau lead. ({datetime.now(timezone.utc).strftime('%H:%M:%S')})")

        except Exception as e:
            print(f"Erreur: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
