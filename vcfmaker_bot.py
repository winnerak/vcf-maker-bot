from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os

# 🔐 Replace these with actual Telegram user IDs
ALLOWED_USERS = [7296364795]  # Example: [123456789, 987654321]

TOKEN = '8169067910:AAFKGcKiqZ5Q4VBg4e3YnMz7gzDxS7bFa_k'  # Replace with your actual token

# ✅ Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return

    await update.message.reply_text(
        "✅ Welcome to VCF Maker Bot!\n\n"
        "You can send:\n"
        "📄 A `.txt` file with a caption like `Ansh 30`\n"
        "✍️ Or a text message starting with `Ansh 30` followed by numbers\n\n"
        "**VCF files will be generated with names like:** `Ansh 0001`, `Ansh 0002`, etc.",
        parse_mode='Markdown'
    )

# ✅ Generate VCF in batches
def generate_vcf_batches(numbers, name_prefix, batch_size):
    total = len(numbers)
    batch_files = []

    for i in range(0, total, batch_size):
        batch = numbers[i:i + batch_size]
        file_index = (i // batch_size) + 1
        filename = f"{name_prefix}_{file_index}.vcf"
        with open(filename, 'w') as vcf:
            for j, number in enumerate(batch, start=i + 1):
                number = '+' + number.lstrip('+0')
                contact_name = f"{name_prefix} {j:04d}"  # zero-padded name
                vcf.write(f"""BEGIN:VCARD
VERSION:3.0
FN:{contact_name}
TEL;TYPE=CELL:{number}
END:VCARD
""")
        batch_files.append(filename)
    return batch_files

# ✅ Handle file uploads (.txt)
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return

    file = update.message.document
    caption = update.message.caption

    if not caption:
        await update.message.reply_text("⚠️ Please add a caption like: `Ansh 30`")
        return

    parts = caption.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await update.message.reply_text("⚠️ Invalid caption format. Use: `Ansh 30`")
        return

    name_prefix = parts[0]
    batch_size = int(parts[1])

    if not file.file_name.endswith('.txt'):
        await update.message.reply_text("⚠️ Only `.txt` files are supported.")
        return

    new_file = await file.get_file()
    input_path = f"{file.file_id}.txt"
    await new_file.download_to_drive(input_path)

    with open(input_path, 'r') as f:
        numbers = [line.strip() for line in f if line.strip()]

    batch_files = generate_vcf_batches(numbers, name_prefix, batch_size)

    for vcf_file in batch_files:
        await update.message.reply_document(document=open(vcf_file, 'rb'))

    os.remove(input_path)
    for f in batch_files:
        os.remove(f)

# ✅ Handle plain text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return

    lines = update.message.text.strip().splitlines()
    if len(lines) < 2:
        await update.message.reply_text("⚠️ First line should be: `Ansh 30`\nFollowed by phone numbers.")
        return

    header = lines[0].strip().split()
    if len(header) != 2 or not header[1].isdigit():
        await update.message.reply_text("⚠️ Invalid format. First line must be: `Ansh 30`")
        return

    name_prefix = header[0]
    batch_size = int(header[1])
    numbers = [line.strip() for line in lines[1:] if line.strip().isdigit() or line.strip().startswith('+')]

    if not numbers:
        await update.message.reply_text("⚠️ No valid phone numbers found.")
        return

    batch_files = generate_vcf_batches(numbers, name_prefix, batch_size)

    for vcf_file in batch_files:
        await update.message.reply_document(document=open(vcf_file, 'rb'))
        os.remove(vcf_file)

# ✅ Run the bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("✅ Bot is running...")
    app.run_polling()
