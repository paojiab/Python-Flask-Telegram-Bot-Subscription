from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from commands import CHOOSE, cancel, choose, start, verify_command
from keys import TELEGRAM_BOT_KEY


def main() -> None:
    """Run the bot."""
    # Create the Application and pass in your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_KEY).build()

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE: [MessageHandler(filters.Regex("Become a VIP|Join the Monster Academy"), choose)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.add_handler(CommandHandler("verify", verify_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()