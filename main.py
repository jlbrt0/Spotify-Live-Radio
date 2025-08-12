from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.error import BadRequest
from dotenv import load_dotenv
from functions_framework import http
import os
import re
import asyncio
from backend import *

load_dotenv()
token = os.getenv('TOKEN')
bot = Bot(token=token)
FRIEND_ID = range(1)
USER_NAME = range(1)

database_information = connect_to_database()

@http
def telegram_bot(request):
    return asyncio.run(main(request))

#Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("""Spotify Live Radio vous permet de partager vos Spotify Jam avec vos amis !""")
    await update.message.reply_text("Pour commencer, comment veux-tu que l'on t'appelle ?")

    return USER_NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_name = update.message.text
    user_id = update.message.from_user['id']

    create_profile(database_information, user_id, user_name)

    await update.message.reply_text(f"C'est noté {user_name}")
    await update.message.reply_text("""
Voici les commandes disponibles :
                                    
/start - Reconfigurer ton profil
                                    
/code - Obtenir ton code secret
                                    
/share - Partager ta Live Radio a un ami
                                    
/help - Afficher cette liste

Pour lancer ta Live Radio partage simplement le Jam depuis Spotify !""")
    return ConversationHandler.END

############################################################################
    
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
"""Voici les commandes disponibles :

/start - Reconfigurer ton profil
                                    
/code - Obtenir ton code secret
                                    
/share - Partager ta Live Radio a un ami
                                    
/help - Afficher cette liste

Pour lancer ta Live Radio partage simplement le Jam depuis Spotify !""")
    
async def code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user['id']
    await update.message.reply_text("Voici ton code secret. Envoie le à une personne de confiance !")
    await update.message.reply_text(f'*`{user_id}`*', parse_mode='MarkdownV2')

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user['id']
    username = get_username(database_information, user_id)
    await update.message.reply_text(f"Votre nom est {username}")

############################################################################

async def share(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Quel est le code secret de ton ami ?")
    return FRIEND_ID

async def friend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    friend_id = update.message.text
    user_id = update.message.from_user['id']

    try:
        username = get_username(database_information, user_id)        
        await bot.send_message(chat_id=friend_id, text=f"{username} vient de t'ajouter ! Tu sera notifié lorsqu'il lancera sa Live Radio.")
        add_friend(database_information, user_id,friend_id)
        
        await update.message.reply_text(f"C'est noté {username} ! Ton ami sera notifié lorsque tu lancera ta Live Radio.")
    except BadRequest:
        await update.message.reply_text(f"Désolé, le code secret que tu as fourni n'est pas valide.")


    return ConversationHandler.END

##########################################################################

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END

############################################################################

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text

    if "https://spotify.link/" in message:
        match = re.search(r'https?://\S+', message)
        link = match.group(0)

        keyboard = [
            [InlineKeyboardButton("▶️ Écouter sur Spotify", url=link)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        user_id = update.message.from_user['id']
        friends_dict = get_friends(database_information, user_id)
        username = get_username(database_information, user_id)

        for friend_id in friends_dict:
            await bot.send_photo(
                photo="https://upload.wikimedia.org/wikipedia/commons/3/33/Spotify_logo13.png",
                caption=f"{username} vient de lancer sa Live Radio !",
                reply_markup=reply_markup,
                chat_id=friend_id
            )

        await update.message.reply_text("La Live Radio a été partagée à tout tes amis !")

async def main(request) -> None:
    application = Application.builder().token(token=token).build()

    start_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            USER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    share_conv = ConversationHandler(
        entry_points=[CommandHandler("share", share)],
        states={
            FRIEND_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, friend)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(start_conv)
    application.add_handler(share_conv)
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("code", code))
    application.add_handler(CommandHandler("test", test))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

    if request.method == 'GET':
        await bot.set_webhook(f'https://{request.host}/telegram_bot')
        return "webhook set"

    async with application:
        update = Update.de_json(request.json, bot)
        await application.process_update(update)

    return "ok"
