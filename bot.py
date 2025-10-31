import os
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = os.getenv('BOT_TOKEN')

def start(update, context):
    update.message.reply_text("🎉 BOT JALAN!")

updater = Updater(BOT_TOKEN, use_context=True)
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.start_polling()
print("🤖 Bot jalan...")
updater.idle()
