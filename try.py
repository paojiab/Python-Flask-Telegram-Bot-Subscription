import os
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError
from dotenv import load_dotenv
import sqlite3

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
MONTHLY_GROUP_ID = os.getenv('MONTHLY_GROUP_ID')
ANNUAL_GROUP_ID = os.getenv('ANNUAL_GROUP_ID')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
def setup_database():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                 (user_id INTEGER PRIMARY KEY, plan TEXT, start_date TEXT, expiry_date TEXT)''')
    conn.commit()
    conn.close()

# Subscription plans
subscriptions = {
    'monthly': {'name': 'VIP Monthly', 'price': 20.00, 'duration': 30, 'group_id': MONTHLY_GROUP_ID},
    'annually': {'name': 'VIP Annually', 'price': 300.00, 'duration': 365, 'group_id': ANNUAL_GROUP_ID}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome! This bot helps you manage your subscription. Use /subscribe to see options.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("For support, contact: support@example.com")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton(f"{sub['name']} ${sub['price']:.2f}", callback_data=f"sub_{key}")]
        for key, sub in subscriptions.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Choose a subscription plan:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data.startswith('sub_'):
        plan = query.data[4:]
        # Here you would typically initiate the payment process
        # For this example, we'll assume payment is successful
        await process_successful_payment(query.from_user.id, plan)
        await query.edit_message_text(text=f"Thanks for subscribing to {subscriptions[plan]['name']}!")

async def process_successful_payment(user_id: int, plan: str):
    start_date = datetime.now()
    expiry_date = start_date + timedelta(days=subscriptions[plan]['duration'])
    
    # Update database
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO subscriptions (user_id, plan, start_date, expiry_date)
                 VALUES (?, ?, ?, ?)''', (user_id, plan, start_date.isoformat(), expiry_date.isoformat()))
    conn.commit()
    conn.close()

    # Add user to appropriate group
    group_id = subscriptions[plan]['group_id']
    await add_user_to_group(user_id, group_id)

    # Schedule removal when subscription expires
    asyncio.create_task(schedule_user_removal(user_id, group_id, expiry_date))

async def add_user_to_group(user_id: int, group_id: str):
    try:
        await context.bot.unban_chat_member(chat_id=group_id, user_id=user_id)
        invite_link = await context.bot.create_chat_invite_link(chat_id=group_id, member_limit=1)
        await context.bot.send_message(
            chat_id=user_id,
            text=f"You've been added to the group. Join here: {invite_link.invite_link}"
        )
    except TelegramError as e:
        logger.error(f"Failed to add user {user_id} to group {group_id}: {e}")

async def schedule_user_removal(user_id: int, group_id: str, expiry_date: datetime):
    now = datetime.now()
    time_until_expiry = (expiry_date - now).total_seconds()
    if time_until_expiry > 0:
        await asyncio.sleep(time_until_expiry)
        await remove_user_from_group(user_id, group_id)

async def remove_user_from_group(user_id: int, group_id: str):
    try:
        await context.bot.ban_chat_member(chat_id=group_id, user_id=user_id)
        await context.bot.unban_chat_member(chat_id=group_id, user_id=user_id)  # Unban so they can rejoin later
        await context.bot.send_message(
            chat_id=user_id,
            text="Your subscription has expired. You've been removed from the group."
        )
    except TelegramError as e:
        logger.error(f"Failed to remove user {user_id} from group {group_id}: {e}")

async def check_subscriptions(context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute("SELECT user_id, plan, expiry_date FROM subscriptions WHERE expiry_date < ?", (datetime.now().isoformat(),))
    expired_subscriptions = c.fetchall()
    conn.close()

    for user_id, plan, expiry_date in expired_subscriptions:
        group_id = subscriptions[plan]['group_id']
        await remove_user_from_group(user_id, group_id)

def main() -> None:
    setup_database()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CallbackQueryHandler(button))

    # Check for expired subscriptions every day
    application.job_queue.run_daily(check_subscriptions, time=time(hour=0, minute=0, second=0))

    application.run_polling()

if __name__ == '__main__':
    main()