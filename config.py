import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = "data.db"
CSV_PATH = "tashkilotlar.csv"
