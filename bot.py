import os
import requests
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- Konfigurasi Token Bot dan Unsplash API Key (Baca dari Environment Variables) ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# --- Daftar ID Admin ---
# GANTI DENGAN ID PENGGUNA TELEGRAM KAMU!
# Untuk mengetahui ID pengguna Telegram-mu, kamu bisa forward pesan dari dirimu ke bot @userinfobot
ADMIN_IDS = [7086594019] # Contoh: Ganti dengan ID Telegram kamu
                                  # Jika ada lebih dari satu admin, pisahkan dengan koma

# URL API Unsplash
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"

# --- Fungsi Pengecekan Admin ---
def is_admin(user_id: int) -> bool:
    """Memeriksa apakah user_id yang diberikan adalah admin."""
    return user_id in ADMIN_IDS

# --- Perintah Umum ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengirim pesan selamat datang saat perintah /start diterima."""
    await update.message.reply_text(
        "Halo! 👋 Saya bot pencari foto Unsplash. Kirimkan kata kunci foto yang ingin kamu cari, "
        "misalnya 'kucing lucu' atau 'pemandangan gunung'."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengirim pesan bantuan saat perintah /help diterima."""
    await update.message.reply_text(
        "Untuk mencari foto, cukup ketikkan kata kunci yang kamu inginkan. "
        "Contoh: 'bunga mawar', 'sunset di pantai'.\n"
        "Saya akan mencoba mencarikan 3 foto terbaik untukmu."
    )

async def search_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mencari foto di Unsplash berdasarkan kata kunci dari pengguna."""
    query = update.message.text
    if not query:
        await update.message.reply_text("Mohon masukkan kata kunci untuk mencari foto.")
        return

    params = {
        "query": query,
        "client_id": UNSPLASH_ACCESS_KEY,
        "per_page": 3
    }

    try:
        response = requests.get(UNSPLASH_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if data and data["results"]:
            photos = data["results"]
            media = []
            for photo in photos:
                if "urls" in photo and "regular" in photo["urls"]:
                    media.append(InputMediaPhoto(media=photo["urls"]["regular"]))

            if media:
                await update.message.reply_media_group(media=media)
                await update.message.reply_text(f"Ini dia 3 foto terbaik untuk '{query}' dari Unsplash.")
            else:
                await update.message.reply_text(f"Maaf, tidak ada foto yang ditemukan untuk '{query}'. Coba kata kunci lain.")
        else:
            await update.message.reply_text(f"Maaf, tidak ada foto yang ditemukan untuk '{query}'. Coba kata kunci lain.")

    except requests.exceptions.RequestException as e:
        print(f"Error saat memanggil API Unsplash: {e}")
        await update.message.reply_text(
            "Maaf, terjadi kesalahan saat mencoba mengambil foto. Silakan coba lagi nanti."
        )
    except Exception as e:
        print(f"Error tak terduga: {e}")
        await update.message.reply_text(
            "Terjadi kesalahan yang tidak terduga. Mohon laporkan jika ini sering terjadi."
        )

# --- Perintah Admin (Menu Khusus Admin) ---
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menampilkan menu admin jika pengguna adalah admin."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Maaf, kamu tidak memiliki akses ke menu ini.")
        return

    keyboard = [
        [InlineKeyboardButton("Info Pengguna", callback_data="admin_info_pengguna")],
        [InlineKeyboardButton("Log Bot", callback_data="admin_log_bot")],
        [InlineKeyboardButton("Broadcast Pesan", callback_data="admin_broadcast")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Selamat datang di menu Admin:", reply_markup=reply_markup)

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani callback dari tombol menu admin."""
    query = update.callback_query
    await query.answer() # Penting untuk menghilangkan loading state pada tombol

    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.edit_message_text("Maaf, kamu tidak memiliki akses ke fungsi ini.")
        return

    data = query.data

    if data == "admin_info_pengguna":
        # Contoh: Mengambil info bot dan penggunanya
        bot_info = await context.bot.get_me()
        response_text = (
            f"**Info Bot:**\n"
            f"ID: `{bot_info.id}`\n"
            f"Nama: `{bot_info.first_name}`\n"
            f"Username: `@{bot_info.username}`\n\n"
            f"**Info Admin (Anda):**\n"
            f"ID Anda: `{user_id}`\n"
            f"Username Anda: `@{query.from_user.username}`"
        )
        await query.edit_message_text(response_text, parse_mode='Markdown')
    elif data == "admin_log_bot":
        # Di lingkungan Railway, kamu perlu cara untuk mengakses log.
        # Ini hanya placeholder. Mungkin perlu integrasi dengan layanan logging.
        await query.edit_message_text("Fungsi melihat log belum diimplementasikan sepenuhnya. Cek log di dashboard Railway Anda.")
    elif data == "admin_broadcast":
        await query.edit_message_text("Fitur broadcast belum diimplementasikan. Anda bisa menambahkan logikanya di sini.")

# --- Main Fungsi ---
def main() -> None:
    """Menjalankan bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    if not TELEGRAM_BOT_TOKEN or not UNSPLASH_ACCESS_KEY:
        print("Error: TELEGRAM_BOT_TOKEN atau UNSPLASH_ACCESS_KEY tidak ditemukan di environment variables.")
        print("Pastikan Anda sudah mengaturnya di Railway.")
        exit(1)

    # Handler Perintah Umum
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Handler Perintah Admin
    application.add_handler(CommandHandler("admin", admin_menu))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))

    # Handler Pesan Teks untuk Pencarian Foto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_photos))

    # Jalankan bot
    print("Bot sedang berjalan...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
