from datetime import timedelta
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from database import academy_secure, check_subscription, secure, wipe_academy_token, wipe_token
from flutterwave import generate_payment_reference, verify_payment

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

CHOOSE, SIGNALS, MENTORSHIP = range(3)

globals = {"transaction_reference": ""}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [
        ["Join VIP Signals"],
        ["Join the Monster Academy"],
        ]
    user = update.message.from_user
    await update.message.reply_text(
        f"Hi {user.first_name} - {user.id}, I'm the Forex Monsters Assistant Bot. I will be helping you today.\n\n"
        "What would you like to do?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="", resize_keyboard=True
        ),
    )
    return CHOOSE

async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """store users selection"""
    user = update.message.from_user
    text = update.message.text
    context.user_data["action"] = text
    logger.info("Action of %s: %s", user.first_name, text)
    if(text=="Join VIP Signals"):
        keyboard = [
            [InlineKeyboardButton("1 Month Access  💲20", url="https://forexmonsters.selar.co/2886b2",)],
            [InlineKeyboardButton("3 Months Access 💲50", url="https://forexmonsters.selar.co/232834")],
            [InlineKeyboardButton("6 Months Access 💲100", url="https://forexmonsters.selar.co/98413c")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("First copy the USER ID below, we'll ask for it:",reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text(f"{user.id}",reply_markup=ReplyKeyboardRemove())

        token:str = generate_payment_reference()

        """I'm creating an 'auth token' replica a minute later
        As no way a user can complete Selar's payment flow before a minute's end
        Unless a malicious attempt is in progress
        :SECURITY 101
        """
        name = f"s{user.id}"
        due = timedelta(seconds=60)
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if(current_jobs):
            for job in current_jobs:
                job.schedule_removal()
        context.job_queue.run_once(secure,due, name=name, user_id=user.id, data=token)
        
        """I'm invalidating the 'auth token' replica 15 minutes later
        As no way a user has not yet claimed their package
        Or atleast they should have
        :SECURITY 101
        """
        name = str(user.id)
        due = timedelta(minutes=15)
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if(current_jobs):
            for job in current_jobs:
                job.schedule_removal()
        context.job_queue.run_once(wipe_token,due, name=name, data=token)
        
        await update.message.reply_text(
            "To trade with the winning team 😎, be part of the VIPs for daily signals 👌🚀 Let's go 🏹"
            "\n\n1 Month  💲̶4̶0̶ ❌ Now 💲20 ✅"
            "\n\n3 Months 💲̶7̶0̶ ❌ Now 💲50 ✅"
            "\n\n6 Months 💲̶1̶2̶0̶ ❌ Now 💲100 ✅"
            "\n\nBECOME A VIP NOW 😎 (while discount lasts 🔥🔥) and take your trading to the next level 💹"
            "\n\nDON'T MISS OUT 🚨🚨🚨"
            ,
            reply_markup=reply_markup,
        )
    else:
        url="https://forexmonsters.selar.co/4rp3zp"
        keyboard = [
            [InlineKeyboardButton("Monsters Mentorship  💲130", url=url,)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("First copy the USER ID below, we'll ask for it:",reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text(f"{user.id}",reply_markup=ReplyKeyboardRemove())

        token:str = generate_payment_reference()

        """I'm creating an 'auth token' replica a minute later
        As no way a user can complete Selar's payment flow before a minute's end
        Unless a malicious attempt is in progress
        :SECURITY 101
        """
        name = f"ms{user.id}"
        due = timedelta(seconds=60)
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if(current_jobs):
            for job in current_jobs:
                job.schedule_removal()
        context.job_queue.run_once(academy_secure,due, name=name, user_id=user.id, data=token)
        
        """I'm invalidating the 'auth token' replica 15 minutes later
        As no way a user has not yet claimed their package
        Or atleast they should have
        :SECURITY 101
        """
        name = f"m{user.id}"
        due = timedelta(minutes=15)
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if(current_jobs):
            for job in current_jobs:
                job.schedule_removal()
        context.job_queue.run_once(wipe_academy_token,due, name=name, data=token)

        await update.message.reply_text(
            "You deserve it all 💰🤑💸 and you should not be struggling all by yourself ✊"
            "\n\nWith the right guidance and lessons, you can fulfill your dreams from the forex industry. Your seat awaits you 🚀🚀🚀"
            "\n\nJoin the Monster Academy and get all the necessary skills to become a pro 😎"
            "\n\nOriginal 💲̶3̶5̶0̶ ❌🙅🏿‍♂️ Now 💲130 ✅👌"
            "\n\nProceed below for payment while discount lasts. DON'T MISS OUT 🔥",
            reply_markup=reply_markup,
        )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can make it work some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payment_reference = globals["transaction_reference"]
    await update.message.reply_text(
        f"Verifying payment for reference: \n{payment_reference}", reply_markup=ReplyKeyboardRemove()
    )
    status:str = await verify_payment(payment_reference)
    if(status=="wrong"):
         await update.message.reply_text(
        "No transaction was found for this reference. Make sure to first complete payment"
        "\n\nHaving trouble? contact /support", reply_markup=ReplyKeyboardRemove()
    )
    else:
        await update.message.reply_text(
        f"Payment {status}", reply_markup=ReplyKeyboardRemove()
    )
        if(status=="successful"):
            await context.bot.unban_chat_member(chat_id="", user_id="", only_if_banned=True)
            invite_link = await context.bot.create_chat_invite_link(chat_id="",expire_date="",member_limit=1,)
            # Academy is lifetime so amount and package is a constant, no need to fetch t
            # Just hard code t f needed
            # but also meaning no database needed(optional) for academy, coz no checks will be required
            # no group removal required for academy as user is never banned
            # meaning just an ivite completes this
            # only for signals, would this be the part where: add to database logic
            await update.message.reply_text(
            f"Here is your invite link \n{invite_link}", reply_markup=ReplyKeyboardRemove()
            )
    
async def check_subscription_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    result = await check_subscription(user.id)
    print(result)
    if(result):
        await update.message.reply_text(
            f"You are currently subscribed to {result[1]}", reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "You do not have an active subscription", reply_markup=ReplyKeyboardRemove()
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "/start to start a session"
        "\n/check to check subscription"
        "\n/support to communicate with us"
        "\n/help to display available commands", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Contact"
        "\nforexmonstersteam@gmail.com", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END
        