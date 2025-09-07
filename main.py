import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

BOT_TOKEN = os.environ.get('BOT_TOKEN', 'ваш_токен_бота')

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(f"Привет, {user.first_name}! Бот запущен и работает! 🎉")

def echo(update: Update, context: CallbackContext):
    update.message.reply_text("Я получил твое сообщение! Все работает!")

def run_bot():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    import threading
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
