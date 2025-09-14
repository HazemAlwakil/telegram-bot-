import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from PIL import Image
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv, find_dotenv


load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo_file = await update.message.photo[-1].get_file()
        file_path = "original.jpg"
        await photo_file.download_to_drive(file_path)

        # Compress image
        compressed_path = "compressed.jpg"
        img = Image.open(file_path)
        img.save(compressed_path, "JPEG", optimize=True, quality=40)

        # Send email
        msg = EmailMessage()
        msg["Subject"] = "Compressed Image"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = RECEIVER_EMAIL
        msg.set_content("Here is your compressed image.")
        with open(compressed_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="image", subtype="jpeg", filename="compressed.jpg")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        await update.message.reply_text("✅ Image compressed and emailed successfully!")

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ Failed to process and send the image.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

if __name__ == "__main__":
    app.run_polling()
