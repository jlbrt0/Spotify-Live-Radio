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
import os
import re
from db_request import *

load_dotenv()
token = os.getenv('TOKEN')
bot = Bot(token=token)
FRIEND_USERNAME = range(1)
USERNAME, NAME = range(2)

#Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    user_id = update.message.from_user['id']
    if id_check(user_id):
        await update.message.reply_text("""Spotify Live Radio vous permet de partager vos Spotify Jam avec vos amis !""")
        await update.message.reply_text("Pour commencer, quel nom d'utilisateur souhaites-tu ?")
        return USERNAME
    else:
        old_username = get_username(user_id)
        context.user_data["old_username"] = old_username
        await update.message.reply_text("""Tu souhaites reconfigurer ton profil, c'est ça ?""")
        await update.message.reply_text("Quel est ton nouveau nom d'utilisateur ?")
        return USERNAME

async def username_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    username = update.message.text.lower()

    if not (re.fullmatch(r"[a-zA-Z0-9_]+", username)):
        await update.message.reply_text("""Désolé, le nom d'utilisateur ne peut contenir que des lettres, chiffres et tirets du bas.""")
        await update.message.reply_text("""Tu peux réessayer avec la commande /start""")
        return ConversationHandler.END
    elif not username_check(username):
        await update.message.reply_text("""Désolé, le nom d'utilisateur que tu as choisi est déjà pris.""")
        await update.message.reply_text("""Tu peux réessayer avec la commande /start""")
        return ConversationHandler.END
    else:
        context.user_data["username"] = username.lower()
        await update.message.reply_text(f"C'est noté !")
        await update.message.reply_text("""Maintenant comment veux-tu que l'on t'appelle ?""")
        return NAME

async def name_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    username = context.user_data["username"]
    user_id = update.message.from_user['id']
    name = update.message.text
    if id_check(user_id):
        create_profil(username, user_id, name)
    else:
        old_username = context.user_data["old_username"]
        update_profil(old_username,username,user_id,name)


    await update.message.reply_text(f"C'est noté {name}")
    await update.message.reply_text("""
Voici les commandes disponibles :
                                    
/start - Reconfigurer ton profil
                                    
/username - Obtenir ton nom d'utilisateur
                                    
/share - Partager ta Live Radio a un ami
                                    
/help - Afficher cette liste

Pour lancer ta Live Radio partage simplement le Jam depuis Spotify !""")
    return ConversationHandler.END

############################################################################
    
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
"""Voici les commandes disponibles :

/start - Reconfigurer ton profil
                                    
/username - Obtenir ton nom d'utilisateur
                                    
/share - Partager ta Live Radio a un ami
                                    
/help - Afficher cette liste

Pour lancer ta Live Radio partage simplement le Jam depuis Spotify !""")
    
async def username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user['id']
    username = get_username(user_id)
    await update.message.reply_text("Voici ton nom d'utilisateur. Envoie le à une personne de confiance !")
    await update.message.reply_text(f'*`{username}`*', parse_mode='MarkdownV2')

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user['id']
    username = get_username(user_id)
    await update.message.reply_text(f"Votre nom est {username}")

############################################################################

async def share(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Quel est le nom d'utilisateur de ton ami ?")
    return FRIEND_USERNAME

async def friend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    friend_username = update.message.text.lower()
    user_id = update.message.from_user['id']

    try:
        friend_user_id = get_user_id(friend_username)    
        username = get_username(user_id)
        name = get_name(username)
        add_friend(username, user_id, friend_username,friend_user_id)
        
        await bot.send_message(chat_id=friend_user_id, text=f"{name} vient de t'ajouter ! Tu sera notifié lorsqu'il lancera sa Live Radio.")
        await update.message.reply_text(f"C'est noté ! Ton ami sera notifié lorsque tu lancera ta Live Radio.")
    except BadRequest:
        await update.message.reply_text(f"Désolé, le nom d'utilisateur que tu as fourni n'existe pas.")


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
        username = get_username(user_id)
        name = get_name(username)
        friends_list = get_id_friends_list(user_id)

        for friend_id in friends_list:
            await bot.send_photo(
                photo="https://upload.wikimedia.org/wikipedia/commons/3/33/Spotify_logo13.png",
                caption=f"{name} vient de lancer sa Live Radio !",
                reply_markup=reply_markup,
                chat_id=friend_id
            )

        await update.message.reply_text("La Live Radio a été partagée à tout tes amis !")

def main() -> None:
    application = Application.builder().token(token=token).build()

    start_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username_selection)],
            NAME : [MessageHandler(filters.TEXT & ~filters.COMMAND, name_selection)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    add_friend_conv = ConversationHandler(
        entry_points=[CommandHandler("share", share)],
        states={
            FRIEND_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, friend)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(start_conv)
    application.add_handler(add_friend_conv)
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("username", username))
    application.add_handler(CommandHandler("test", test))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
