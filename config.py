import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8237207326:AAHMSHbknlQb31MfdsUSY0MVAriRAB69kJU")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "765318133").split(',')))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "--1003730654738"))
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://https://t.me/mvpni7")

DNS_LIST = [
    {"name": "Google", "primary": "8.8.8.8", "secondary": "8.8.4.4", "for_gaming": False},
    {"name": "Cloudflare", "primary": "1.1.1.1", "secondary": "1.0.0.1", "for_gaming": True},
    {"name": "OpenDNS", "primary": "208.67.222.222", "secondary": "208.67.220.220", "for_gaming": False},
    {"name": "Quad9", "primary": "9.9.9.9", "secondary": "149.112.112.112", "for_gaming": False},
]
