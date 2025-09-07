import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from supabase import create_client, Client
from flask import Flask
import threading

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем Flask app для Render
app = Flask(__name__)
@app.route('/')
def home():
    return "Telegram Bot is running!"

# Конфигурация из переменных окружения
BOT_TOKEN = os.environ['BOT_TOKEN']
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']

# Инициализация Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Команда /start
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username or f"user_{user.id}"

    user_data = supabase.table('users').select('*').eq('tg_id', user_id).execute()
    
    if not user_data
