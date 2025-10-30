import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Token dari environment variable
BOT_TOKEN = os.getenv('8053922983:AAEzmY_wfNO9A49pya5xZriHkkn0iUaOXnY')

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🤖 **Video Downloader Bot**

Kirim link video dari YouTube, TikTok, Instagram, dll.
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Format URL tidak valid.")
        return
    
    msg = await update.message.reply_text("⏳ Memproses video...")
    
    try:
        ydl_opts = {
            'format': 'best[height<=480]',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            with open(filename, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption=f"📹 {info.get('title', 'Video')}"
                )
            
            await msg.delete()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await msg.edit_text("❌ Gagal mendownload video.")

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable not set!")
        return
        
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    logger.info("🤖 Bot started...")
    application.run_polling()

if __name__ == '__main__':
    main()
