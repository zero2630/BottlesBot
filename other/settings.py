import os

import dotenv

dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", default="None")
ADMINS = os.getenv("ADMINS", default="None").split(",")

DB_HOST = os.getenv("DB_HOST", default="None")
DB_NAME = os.getenv("DB_NAME", default="None")
DB_PASS = os.getenv("DB_PASS", default="None")
DB_PORT = os.getenv("DB_PORT", default="None")
DB_USER = os.getenv("DB_USER", default="None")
