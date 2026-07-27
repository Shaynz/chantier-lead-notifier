import os
import time
import requests

# Config depuis les variables d'environnement
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
BASE44_API_KEY = os.environ["BASE44_API_KEY"]
APP_ID = "6a5e86447b1f838a3df9339a"
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
    url = f"https://api.base44.com/api/apps/{APP_ID}/entities/Lead/records"
    headers = {
        "api_key": BASE44_API_KEY,
        "Content-Type": "application/json"
    }
    params = {"sort": "-created_date", "limit": 10}
    response = requests.get(url, headers=headers, params=params)
    
    print(f"Status: {response.status_code} | URL: {response.url}")
    
    if response.status_code == 404:
        # Essayer un autre format d'URL
        url2 = f"https://api.base44.com/api/apps/{APP_ID}/entities/leads"
        response = requests.get(url2, headers=headers, params=params)
        print(f"Retry Status: {response.status_code} | URL: {response.url}")
    
    response.raise_for_status()
    data = response.json()
    
    # Gérer différents formats de réponse
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get("records", data.get("data", data.get("items", [])))
    return []

def send_telegram(lead):
    # Extraire les données — gérer si elles sont dans un sous-objet "data"
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
    print(f"Telegram: {r.status_code} | {r.text[:100]}")

def main():
    print("✅ Démarrage du notifier Chantier Numérique...")
    
    # Initialiser avec le dernier lead connu au démarrage
    try:
        leads = get_leads()
        if leads and not get_last_seen_id():
            save_last_seen_id(leads[0]["id"])
            print(f"Dernier lead existant: {leads[0]['id']}")
    except Exception as e:
        print(f"Erreur init: {e}")

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
                for lead in reversed(new_leads):
                    send_telegram(lead)
                    print(f"Notif envoyée pour lead: {lead['id']}")
                save_last_seen_id(new_leads[0]["id"])
            else:
                print("Aucun nouveau lead.")

        except Exception as e:
            print(f"Erreur boucle: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
