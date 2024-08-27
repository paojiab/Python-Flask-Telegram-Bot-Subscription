import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from flutterwave import generate_payment_link, generate_payment_reference, verify_payment

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
        ["Become a VIP"],
        ["Join the Monster Academy"],
        ]
    user = update.message.from_user
    await update.message.reply_text(
        f"Hi {user.first_name}, I'm the Forex Monsters Assistant Bot. I will be helping you today.\n\n"
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
    if(text=="Become a VIP"):
        keyboard = [
            [InlineKeyboardButton("1 Month Access  💲20", url="https://forexmonsters.selar.co/2886b2",)],
            [InlineKeyboardButton("3 Months Access 💲50", url="https://forexmonsters.selar.co/232834")],
            [InlineKeyboardButton("6 Months Access 💲100", url="https://forexmonsters.selar.co/98413c")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
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
        # return ConversationHandler.END
    else:
        # url="https://forexmonsters.selar.co/4rp3zp"
        payment_reference = generate_payment_reference()
        url:str = await generate_payment_link(payment_reference, str(1000))
        globals["transaction_reference"] = payment_reference
        logger.info(f"Transaction Reference: {globals["transaction_reference"]}")
        keyboard = [
            [InlineKeyboardButton("Monsters Mentorship  💲130", url=url,)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "You deserve it all 💰🤑💸 and you should not be struggling all by yourself ✊"
            "\n\nWith the right guidance and lessons, you can fulfill your dreams from the forex industry. Your seat awaits you 🚀🚀🚀"
            "\n\nJoin the Monster Academy and get all the necessary skills to become a pro 😎"
            "\n\nOriginal 💲̶3̶5̶0̶ ❌🙅🏿‍♂️ Now 💲130 ✅👌"
            "\n\nProceed below for payment while discount lasts. DON'T MISS OUT 🔥"
            "\n\nClick /verify once done to be enrolled in"
            ,
            reply_markup=reply_markup,
        )
        # return ConversationHandler.END
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
        if(status=="successful"):
            action = "start"
        await update.message.reply_text(
        f"Payment {status}", reply_markup=ReplyKeyboardRemove()
    )