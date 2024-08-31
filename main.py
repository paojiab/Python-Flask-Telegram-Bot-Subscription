import asyncio
from datetime import datetime, time, timedelta
import sqlite3
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
import uvicorn
from asgiref.wsgi import WsgiToAsgi

from commands import CHOOSE, cancel, check_subscription_command, choose, help_command, start, support_command, verify_command
from database import add_academy_subscription, add_subscription, check_academy_subscription, check_academy_token, check_raw_academy_token, check_raw_token, check_subscription, check_token, create_academy_database, create_academy_tokens_database, create_database, create_tokens_database, remove_subscription
from keys import CHANNEL_CHAT_ID, GROUP_CHAT_ID, MAIL_PASSWORD, MAIL_USERNAME, TELEGRAM_BOT_KEY
from flask_mail import Mail, Message

create_database()
create_academy_database()
create_tokens_database()
create_academy_tokens_database()

async def main() -> None:
    """Run the bot."""
    # Create the Application and pass in your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_KEY).build()

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE: [MessageHandler(filters.Regex("Join VIP Signals|Join the Monster Academy"), choose)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(CommandHandler("check", check_subscription_command))

    application.add_handler(CommandHandler("support", support_command))

    flask_app = Flask(__name__)

    # Configure mail settings
    flask_app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
    flask_app.config['MAIL_PORT'] = 587
    flask_app.config['MAIL_USE_TLS'] = True
    flask_app.config['MAIL_USERNAME'] = MAIL_USERNAME
    flask_app.config['MAIL_PASSWORD'] = MAIL_PASSWORD

    mail = Mail(flask_app)

    @flask_app.get("/")
    async def index():
        return "<p>Forex Monsters Automation Center</p>"
    
    @flask_app.route("/initiate-signals")
    async def initiate():
        user_email = request.args.get('email')
        full_name = request.args.get('fullname')
        return render_template("initiate_signals.html", full_name=full_name,user_email=user_email)
    
    @flask_app.route("/initiate-mentorship")
    async def initiate_mentorship():
        user_email = request.args.get('email')
        full_name = request.args.get('fullname')
        return render_template("initiate_mentorship.html", full_name=full_name,user_email=user_email)
    
    @flask_app.post("/generate-signals-link")
    async def generate_signals_link():
        user_id = request.form['user_id']
        """Checking if current user actually came from Telgram Bot
        False if no 'auth token' replica is available for their user id
        They could have just stored the redirect_url and are getting back
        :SECURITY 101
        """
        proceed = await check_token(user_id)
        if (proceed):
            token=proceed[1]
            return redirect(url_for("signals",user_id=user_id,token=token))
        else:
            abort(401)

    @flask_app.post("/generate-mentorship-link")
    async def generate_mentorship_link():
        user_id = request.form['user_id']
        """Checking if current user actually came from Telgram Bot
        False if no 'auth token' replica is available for their user id
        They could have just stored the redirect_url and are getting back
        :SECURITY 101
        """
        proceed = await check_academy_token(user_id)
        if (proceed):
            token=proceed[1]
            return redirect(url_for("mentorship",user_id=user_id,token=token))
        else:
            abort(401)
    
    @flask_app.route("/signals/<user_id>/<token>")
    async def signals(user_id,token):
        chat_id=CHANNEL_CHAT_ID
        proceed = await check_raw_token(token)
        """Checking provided 'auth token' replica is valid
        False if no such 'auth token' exists in system
        They could have just stored the auth generating url with an old 'auth token' replica
        :SECURITY 101
        """
        if(proceed):
            subscribed = await check_subscription(user_id)
            """Checking if user is already subscribed given ther 'auth token' replica is valid
           True if they have an existing subscription in the database
            They are probably just coming back to generate links for other Telegram user accounts
            while the access token is still valid
            :SECURITY 101
            """
            if(subscribed):
                abort(409)
            else:
                await add_subscription(user_id,"month")
                # schedule user removal
                due = timedelta(days=30)
                application.job_queue.run_once(remove_subscription,due,user_id=user_id)
                # link expires because if valid user might use it even after an ended subscription
                expire_date = datetime.now() + timedelta(days=1)
                await application.bot.unban_chat_member(chat_id=chat_id,user_id=user_id,only_if_banned=True)
                invite_object = await application.bot.create_chat_invite_link(chat_id=chat_id,member_limit=1,expire_date=expire_date)
                invite_link = invite_object.invite_link
                return render_template("signals_invite.html", invite_link=invite_link)
        else:
            abort(401)

    @flask_app.route("/mentorship/<user_id>/<token>")
    async def mentorship(user_id,token):
        chat_id=CHANNEL_CHAT_ID
        proceed = await check_raw_academy_token(token)
        """Checking provided 'auth token' replica is valid
        False if no such 'auth token' exists in system
        They could have just stored the auth generating url with an old 'auth token' replica
        :SECURITY 101
        """
        if(proceed):
            subscribed = await check_academy_subscription(user_id)
            """Checking if user is already subscribed given ther 'auth token' replica is valid
           True if they have an existing subscription in the database
            They are probably just coming back to generate links for other Telegram user accounts
            while the access token is still valid
            :SECURITY 101
            """
            if(subscribed):
                abort(409)
            else:
                await add_academy_subscription(user_id)
                expire_date = ""
                await application.bot.unban_chat_member(chat_id=chat_id,user_id=user_id,only_if_banned=True)
                invite_object = await application.bot.create_chat_invite_link(chat_id=chat_id,member_limit=1,expire_date=expire_date)
                invite_link = invite_object.invite_link
                return render_template("mentorship_invite.html", invite_link=invite_link)
        else:
            abort(401)
    
    @flask_app.route("/academy-invite")
    async def invite():
        user_email = request.args.get('email')
        full_name = request.args.get('fullname')
        chat_id= GROUP_CHAT_ID
        invite_object = await application.bot.create_chat_invite_link(chat_id=chat_id,member_limit=1)
        invite_link = invite_object.invite_link
        sender = "Forex_Monsters_Academy"
        subject = "Forex Monsters Academy Enrolment"
        html = f"""
        <!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Forex Monsters Academy Enrolment</title>
                </head>
                <body >
                    <p>Dear { full_name }</p>
                    <h2>Thank you for your successful payment.</h2>
                    <p>We'd therefore like to invite you to join our exclusive mentorship Telegram group. Here's your invite link:</p>
                    <a href="{ invite_link }">Join Now</a>
                    <p>A copy of this information has been sent to: <u><i>{ user_email }</i></u> </p>
                </body>
            </html>
        """

        msg = Message(subject=subject,
                      sender=sender,
                      recipients=[user_email],
                      html=html
                      )

        mail.send(msg)
        return render_template("academy_invite.html", invite_link=invite_link, full_name=full_name,user_email=user_email)

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=WsgiToAsgi(flask_app),
            port=5000,
            use_colors=False,
            host="127.0.0.1",
        )
    )
    
    # Run application and webserver together
    async with application:
        # pip install "python-telegram-bot[job-queue]"
        await application.bot.set_my_commands([('start','Starts the bot'),('check','Checks subscription status'),('support','Offers quick contact'),('help','Shows available commands')])
        await application.bot.set_chat_menu_button()
        await application.start()
        await application.updater.start_polling()
        await webserver.serve()
        await application.stop()
        await application.updater.stop()

if __name__ == "__main__":
    asyncio.run(main())