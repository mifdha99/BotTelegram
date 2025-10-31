import os
import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Token dari environment variable - PASTI BENAR
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Validasi token - PASTI BENAR
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable not set!")
    print("💡 Please set BOT_TOKEN in Railway environment variables")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🤖 **Video Downloader Bot**

Halo! Saya bot downloader video yang berjalan di cloud!

**Platform yang didukung:**
• YouTube
• TikTok  
• Instagram
• Facebook
• Twitter

**Cara pakai:**
1. Kirim link video ke saya
2. Tunggu proses download
3. Video akan dikirim ke Anda

⚡ **Bot berjalan 24/7 di Railway!**
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user = update.message.from_user
    
    logger.info(f"User {user.first_name} requested download: {url}")
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Format URL tidak valid.")
        return
    
    msg = await update.message.reply_text("⏳ Memproses video...")
    
    try:
        ydl_opts = {
            'format': 'best[height<=480][filesize<50M]',
            'outtmpl': '/tmp/%(title).80s.%(ext)s',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                await msg.edit_text("❌ Tidak bisa mendapatkan info video.")
                return
                
            title = info.get('title', 'Video')
            await msg.edit_text(f"📹 **{title}**\n⏳ Sedang mendownload...")
            
            ydl.download([url])
            filename = ydl.prepare_filename(info)
            
            if os.path.exists(filename):
                with open(filename, 'rb') as video_file:
                    await update.message.reply_video(
                        video=video_file,
                        caption=f"📹 {title}",
                        supports_streaming=True
                    )
                await msg.delete()
                os.remove(filename)
            else:
                await msg.edit_text("❌ File tidak ditemukan setelah download.")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        await msg.edit_text("❌ Gagal mendownload video.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    logger.info("🤖 Bot started successfully on Railway!")
    logger.info("⚡ Bot is running 24/7!")
    application.run_polling()

if __name__ == '__main__':
    main()
