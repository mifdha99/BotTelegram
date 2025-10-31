import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Token
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handler start
def start(update, context):
    update.message.reply_text("✅ Bot jalan! Kirim link video.")

# Handler message
def echo(update, context):
    update.message.reply_text(f"📹 Akan download: {update.message.text}")

# Main
def main():
    # Buat updater
    updater = Updater(BOT_TOKEN, use_context=True)
    
    # Get dispatcher
    dp = updater.dispatcher
    
    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, echo))
    
    # Start bot
    updater.start_polling()
    logger.info("🤖 BOT JALAN!")
    
    # Run sampai stop
    updater.idle()

if __name__ == '__main__':
    main()
