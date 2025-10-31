import os
import logging
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(level=logging.INFO)

def start(update, context):
    update.message.reply_text("✅ Bot is working!")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    logging.info("🤖 Bot started!")
    updater.idle()

if __name__ == '__main__':
    main()
