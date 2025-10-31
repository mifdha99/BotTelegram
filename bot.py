import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import yt_dlp
import re
from datetime import datetime

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_DURATION = 1800  # 30 menit

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self):
        self.supported_domains = [
            'youtube.com', 'youtu.be', 'tiktok.com', 'vm.tiktok.com',
            'instagram.com', 'facebook.com', 'twitter.com', 'x.com',
            'twitch.tv', 'vimeo.com', 'dailymotion.com', 'bilibili.com',
            'reddit.com', 'likee.video', 'kwai.com'
        ]
    
    def is_supported_url(self, url):
        return any(domain in url for domain in self.supported_domains)
    
    def get_video_info(self, url):
        """Get video information without downloading"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Format duration
                duration = info.get('duration', 0)
                if duration:
                    minutes, seconds = divmod(duration, 60)
                    hours, minutes = divmod(minutes, 60)
                    if hours > 0:
                        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    else:
                        duration_str = f"{minutes:02d}:{seconds:02d}"
                else:
                    duration_str = "Unknown"
                
                # Get available formats
                formats = []
                if 'formats' in info:
                    for f in info['formats']:
                        if f.get('vcodec') != 'none':  # Video formats only
                            formats.append({
                                'format_id': f.get('format_id'),
                                'ext': f.get('ext'),
                                'resolution': f.get('resolution', 'unknown'),
                                'filesize': f.get('filesize', 0)
                            })
                
                return {
                    'title': info.get('title', 'Unknown Title'),
                    'duration': duration_str,
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'thumbnail': info.get('thumbnail'),
                    'description': info.get('description', '')[:200] + '...' if info.get('description') else 'No description',
                    'formats': formats,
                    'webpage_url': info.get('webpage_url', url),
                    'original_duration': duration
                }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
    
    def download_video(self, url, quality='best', download_audio=False):
        """Download video with selected quality"""
        try:
            if download_audio:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': '/tmp/%(title)s.%(ext)s',
                    'quiet': True,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
            else:
                if quality == 'best':
                    format_selection = 'best[height<=1080]'
                elif quality == '720p':
                    format_selection = 'best[height<=720]'
                elif quality == '480p':
                    format_selection = 'best[height<=480]'
                elif quality == '360p':
                    format_selection = 'best[height<=360]'
                else:
                    format_selection = 'best[height<=720]'
                
                ydl_opts = {
                    'format': format_selection,
                    'outtmpl': '/tmp/%(title)s.%(ext)s',
                    'quiet': True,
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # For audio downloads, change extension to mp3
                if download_audio:
                    filename = os.path.splitext(filename)[0] + '.mp3'
                
                return filename, info
        
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None, None

# Initialize downloader
downloader = VideoDownloader()

# User sessions to track download requests
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user = update.message.from_user
    welcome_text = f"""
🤖 **Video Downloader Bot SUPER LENGKAP**

Halo {user.first_name}! Saya bisa mendownload video dari:

🎬 **Platform Supported:**
• YouTube (Video & Shorts)
• TikTok 
• Instagram (Reels & Posts)
• Facebook
• Twitter/X
• Twitch
• Vimeo
• Dailymotion
• Reddit
• Likee
• Kwai
• Dan lainnya!

⚡ **Fitur:**
• Download video berbagai kualitas
• Download audio (MP3)
• Info video sebelum download
• Support thumbnail
• Auto format selection

📖 **Cara Pakai:**
1. Kirim link video
2. Pilih kualitas/format
3. Tunggu proses download
4. Video akan dikirim otomatis

⚠ **Batasan:**
• Maksimal 50MB per video
• Maksimal 30 menit durasi
• Format: MP4, MP3, WEBM

🔗 **Contoh Link:**
`https://youtube.com/shorts/abc123`
`https://vm.tiktok.com/xyz789/`
`https://instagram.com/reel/def456/`
    """
    
    keyboard = [
        [InlineKeyboardButton("📋 List Platform", callback_data="platforms")],
        [InlineKeyboardButton("ℹ️ Cara Pakai", callback_data="help")],
        [InlineKeyboardButton("⚙️ Supported Format", callback_data="formats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "platforms":
        platforms_text = """
📋 **Platform yang Didukung:**

• YouTube (youtube.com, youtu.be)
• YouTube Shorts
• TikTok (tiktok.com, vm.tiktok.com)
• Instagram (instagram.com/reel/)
• Facebook (facebook.com/watch/)
• Twitter/X (twitter.com, x.com)
• Twitch (twitch.tv)
• Vimeo (vimeo.com)
• Dailymotion (dailymotion.com)
• Bilibili (bilibili.com)
• Reddit (reddit.com)
• Likee (likee.video)
• Kwai (kwai.com)
• Dan banyak lainnya!
        """
        await query.edit_message_text(platforms_text, parse_mode='Markdown')
    
    elif query.data == "help":
        help_text = """
ℹ️ **Cara Penggunaan:**

1. **Kirim Link**: Salin dan kirim link video
2. **Pilih Format**: Bot akan menampilkan pilihan kualitas
3. **Download**: Pilih kualitas yang diinginkan
4. **Tunggu**: Bot akan mengirim video yang sudah didownload

⚡ **Tips:**
• Gunakan WiFi untuk video besar
• Video >50MB tidak bisa dikirim
• Durasi maksimal 30 menit
• Format MP3 untuk audio only
        """
        await query.edit_message_text(help_text, parse_mode='Markdown')
    
    elif query.data == "formats":
        formats_text = """
⚙️ **Format & Kualitas:**

🎥 **Video Formats:**
• 1080p (Best Quality)
• 720p (HD)
• 480p (Medium)
• 360p (Low)

🎵 **Audio Formats:**
• MP3 (192kbps)

📁 **Output Formats:**
• MP4 (Video)
• MP3 (Audio)
• WEBM (Video)

⚠ **Note:** Format tersedia tergantung sumber video
        """
        await query.edit_message_text(formats_text, parse_mode='Markdown')

async def handle_video_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video URL messages"""
    url = update.message.text.strip()
    user_id = update.message.from_user.id
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ **Format URL tidak valid!**\nPastikan link dimulai dengan http:// atau https://")
        return
    
    # Check if URL is supported
    if not downloader.is_supported_url(url):
        await update.message.reply_text("❌ **Platform tidak didukung!**\nKirim /start untuk melihat list platform yang didukung.")
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text("🔍 **Memproses video...**\nMohon tunggu sebentar...")
    
    try:
        # Get video info
        video_info = downloader.get_video_info(url)
        
        if not video_info:
            await processing_msg.edit_text("❌ **Gagal mendapatkan info video!**\nPastikan link valid dan video dapat diakses.")
            return
        
        # Check duration
        if video_info['original_duration'] > MAX_DURATION:
            await processing_msg.edit_text(f"❌ **Video terlalu panjang!**\nDurasi: {video_info['duration']}\nMaksimal: 30 menit")
            return
        
        # Store user session
        user_sessions[user_id] = {
            'url': url,
            'info': video_info,
            'processing_msg_id': processing_msg.message_id
        }
        
        # Create quality selection keyboard
        keyboard = [
            [
                InlineKeyboardButton("🎥 1080p (Best)", callback_data=f"quality_best_{user_id}"),
                InlineKeyboardButton("🎥 720p (HD)", callback_data=f"quality_720p_{user_id}")
            ],
            [
                InlineKeyboardButton("🎥 480p (Medium)", callback_data=f"quality_480p_{user_id}"),
                InlineKeyboardButton("🎥 360p (Low)", callback_data=f"quality_360p_{user_id}")
            ],
            [
                InlineKeyboardButton("🎵 MP3 Audio", callback_data=f"quality_audio_{user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send video info with quality options
        info_text = f"""
📹 **Video Information:**

🏷️ **Judul:** {video_info['title']}
⏱️ **Durasi:** {video_info['duration']}
👤 **Uploader:** {video_info['uploader']}
👁️ **Views:** {video_info['view_count']:,}
📝 **Deskripsi:** {video_info['description']}

🎯 **Pilih kualitas download:**
        """
        
        await processing_msg.edit_text(info_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        await processing_msg.edit_text("❌ **Terjadi error!**\nCoba lagi atau gunakan link yang berbeda.")

async def handle_quality_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quality selection from buttons"""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    # Parse callback data
    parts = query.data.split('_')
    quality_type = parts[1]  # best, 720p, 480p, 360p, audio
    target_user_id = int(parts[2])
    
    # Verify user
    if user_id != target_user_id:
        await query.message.reply_text("❌ Ini bukan permintaan download Anda!")
        return
    
    # Get user session
    session = user_sessions.get(user_id)
    if not session:
        await query.message.reply_text("❌ Session expired! Kirim link lagi.")
        return
    
    url = session['url']
    video_info = session['info']
    
    # Update message to show downloading
    download_msg = await query.message.edit_text(f"⏬ **Downloading {quality_type.upper()}...**\nMohon tunggu, proses mungkin butuh beberapa menit...")
    
    try:
        # Download based on selection
        download_audio = (quality_type == 'audio')
        filename, info = downloader.download_video(url, quality_type, download_audio)
        
        if not filename or not os.path.exists(filename):
            await download_msg.edit_text("❌ **Gagal mendownload video!**\nCoba pilih kualitas lain atau gunakan link berbeda.")
            return
        
        # Check file size
        file_size = os.path.getsize(filename)
        if file_size > MAX_FILE_SIZE:
            await download_msg.edit_text(f"❌ **File terlalu besar!**\nUkuran: {file_size/(1024*1024):.1f}MB\nMaksimal: 50MB")
            os.remove(filename)
            return
        
        # Send file to user
        if download_audio:
            await query.message.reply_audio(
                audio=open(filename, 'rb'),
                title=video_info['title'],
                performer=video_info['uploader'],
                caption=f"🎵 {video_info['title']}"
            )
        else:
            await query.message.reply_video(
                video=open(filename, 'rb'),
                caption=f"📹 {video_info['title']}",
                supports_streaming=True,
                width=1280,
                height=720
            )
        
        # Clean up
        await download_msg.delete()
        os.remove(filename)
        
        # Clear user session
        user_sessions.pop(user_id, None)
        
        logger.info(f"Successfully sent video to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in download process: {e}")
        await download_msg.edit_text("❌ **Error saat mengirim video!**\nCoba lagi nanti.")
        
        # Clean up file if exists
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler"""
    logger.error(f"Error: {context.error}")
    
    if update and update.message:
        await update.message.reply_text("❌ **Terjadi error!**\nCoba lagi atau gunakan command /start")

def main():
    """Main function"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable not set!")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(platforms|help|formats)$"))
    application.add_handler(CallbackQueryHandler(handle_quality_selection, pattern="^quality_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_url))
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("🤖 Bot SUPER LENGKAP started successfully!")
    application.run_polling()

if __name__ == '__main__':
    main()
