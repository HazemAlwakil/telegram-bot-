import os, uuid, logging, smtplib, shutil
from dotenv import load_dotenv
from email.message import EmailMessage
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
AUTHORIZED_USER_ID = int(os.getenv("AUTHORIZED_USER_ID"))

photo_paths = []
os.makedirs("photos", exist_ok=True)

def is_authorized(update: Update) -> bool:
    return update.effective_user.id == AUTHORIZED_USER_ID

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("🚫 Access denied.")
        return

    photo_file = await update.message.photo[-1].get_file()
    file_name = f"{uuid.uuid4()}.jpg"
    file_path = os.path.join("photos", file_name)
    await photo_file.download_to_drive(file_path)
    photo_paths.append(file_path)
    await update.message.reply_text("📸 Photo saved.")

async def send_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("🚫 Access denied.")
        return

    if not photo_paths:
        await update.message.reply_text("No photos to send.")
        return

    msg = EmailMessage()
    msg["Subject"] = "Your Telegram Photos"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECEIVER_EMAIL
    msg.set_content("Attached are your photos.")

    for path in photo_paths:
        with open(path, "rb") as f:
            msg.add_attachment(f.read(), maintype="image", subtype="jpeg", filename=os.path.basename(path))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

    photo_paths.clear()
    shutil.rmtree("photos")
    os.makedirs("photos", exist_ok=True)

    await update.message.reply_text("✅ Photos sent successfully.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(CommandHandler("send", send_photos))
app.run_polling()
