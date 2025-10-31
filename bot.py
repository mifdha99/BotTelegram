import os
import logging
import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import yt_dlp

# Token dari environment variable
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Validasi token
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable not set!")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update, context):
    welcome_text = """
🤖 **Video Downloader Bot**

Halo! Kirim link video dari YouTube, TikTok, Instagram, dll.
    """
    update.message.reply_text(welcome_text)

def download_video(update, context):
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        update.message.reply_text("❌ Format URL tidak valid.")
        return
    
    msg = update.message.reply_text("⏳ Memproses video...")
    
    try:
        ydl_opts = {
            'format': 'best[height<=480]',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            with open(filename, 'rb') as video_file:
                update.message.reply_video(
                    video=video_file,
                    caption=f"📹 {info.get('title', 'Video')}"
                )
            
            msg.delete()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        msg.edit_text("❌ Gagal mendownload video.")

def error_handler(update, context):
    logger.error(f"Error: {context.error}")

def main():
    # ✅ PAKAI UPDATER, BUKAN APPLICATION
    updater = Updater(BOT_TOKEN, use_context=True)
    
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_video))
    
    # Error handler
    dp.add_error_handler(error_handler)
    
    updater.start_polling()
    logger.info("🤖 Bot started successfully!")
    updater.idle()

if __name__ == '__main__':
    main()
