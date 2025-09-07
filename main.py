import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client

# Конфигурация из переменных окружения Railway
BOT_TOKEN = os.environ['BOT_TOKEN']
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']

# Инициализация Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or f"user_{user.id}"

    # Проверяем, есть ли пользователь в БД
    user_data = supabase.table('users').select('*').eq('tg_id', user_id).execute()
    
    if not user_data.data:
        # Создаем уникальную ссылку для пользователя
        import uuid
        unique_link = str(uuid.uuid4())[:8]
        supabase.table('users').insert({
            'tg_id': user_id,
            'username': username,
            'unique_link': unique_link,
            'is_active': True
        }).execute()
    else:
        unique_link = user_data.data[0]['unique_link']

    referral_link = f"https://t.me/{context.bot.username}?start={unique_link}"
    
    welcome_text = f"""
    Привет, {user.first_name}! 👋

    **Твой Тайный Советник готов к работе.**
    Твоя персональная ссылка для анонимных сообщений:
    {referral_link}

    Поделись ею в соцсетях и узнай, что о тебе думают друзья! 😉
    """
    await update.message.reply_text(welcome_text)

# Обработка входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user = update.effective_user
        message_text = update.message.text

        if context.args and len(context.args) > 0:
            unique_link = context.args[0]
            target_user_data = supabase.table('users').select('*').eq('unique_link', unique_link).eq('is_active', True).execute()
            
            if target_user_data.data:
                target_user = target_user_data.data[0]
                target_tg_id = target_user['tg_id']
                
                supabase.table('messages').insert({
                    'from_user_tg_id': user.id,
                    'to_user_tg_id': target_tg_id,
                    'message_text': message_text,
                }).execute()

                await context.bot.send_message(
                    chat_id=target_tg_id,
                    text=f"📨 *Анонимное сообщение:*\n\n_{message_text}_",
                    parse_mode='Markdown'
                )
                await update.message.reply_text("✅ Сообщение доставлено!")
                return

    await update.message.reply_text("Привет! Чтобы отправить сообщение, перейди по ссылке друга.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
