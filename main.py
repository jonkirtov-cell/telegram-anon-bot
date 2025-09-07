import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from supabase import create_client, Client
from flask import Flask
import threading
from concurrent.futures import ThreadPoolExecutor
import asyncio
import uuid

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is running!"

BOT_TOKEN = os.environ['BOT_TOKEN']
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or f"user_{user.id}"
    
    loop = asyncio.get_event_loop()
    
    def sync_supabase_query():
        return supabase.table('users').select('*').eq('tg_id', user_id).execute()
    
    try:
        user_data = await loop.run_in_executor(ThreadPoolExecutor(), sync_supabase_query)
        
        if not user_data.data:
            unique_link = str(uuid.uuid4())[:8]
            await loop.run_in_executor(ThreadPoolExecutor(), 
                lambda: supabase.table('users').insert({
                    'tg_id': user_id, 'username': username, 'unique_link': unique_link, 'is_active': True
                }).execute())
        else:
            unique_link = user_data.data[0]['unique_link']

        referral_link = f"https://t.me/{context.bot.username}?start={unique_link}"
        welcome_text = f"""Привет, {user.first_name}! 👋
        **Твой Тайный Советник готов к работе.**
        Твоя ссылка: {referral_link}
        Поделись ею в соцсетях! 😉"""
        await update.message.reply_text(welcome_text)
        
    except Exception as e:
        logger.error(f"Ошибка при работе с Supabase: {e}")
        await update.message.reply_text("😔 Произошла техническая ошибка. Попробуйте позже.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user = update.effective_user
        message_text = update.message.text

        if context.args and len(context.args) > 0:
            unique_link = context.args[0]
            loop = asyncio.get_event_loop()
            
            def sync_target_query():
                return supabase.table('users').select('*').eq('unique_link', unique_link).eq('is_active', True).execute()
            
            try:
                target_user_data = await loop.run_in_executor(ThreadPoolExecutor(), sync_target_query)
                
                if target_user_data.data:
                    target_user = target_user_data.data[0]
                    target_tg_id = target_user['tg_id']
                    
                    await loop.run_in_executor(ThreadPoolExecutor(),
                        lambda: supabase.table('messages').insert({
                            'from_user_tg_id': user.id, 'to_user_tg_id': target_tg_id, 'message_text': message_text,
                        }).execute())

                    await context.bot.send_message(chat_id=target_tg_id, text=f"📨 *Анонимное сообщение:*\n\n_{message_text}_", parse_mode='Markdown')
                    await update.message.reply_text("✅ Сообщение доставлено!")
                    return
                    
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения: {e}")
                await update.message.reply_text("😔 Ошибка при отправке сообщения.")

    await update.message.reply_text("Привет! Чтобы отправить сообщение, перейди по ссылке друга.")

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
