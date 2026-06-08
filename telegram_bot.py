"""
Telegram Bot for Google Forms Whitelist Submissions
Collects form link and wallet address, stores in database, submits to form
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from threading import Thread
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
FORM_LINK, WALLET = range(2)

# Database file
DB_FILE = 'submissions.json'

# Get Telegram token from .env
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    print("ERROR: TELEGRAM_TOKEN not set in .env file!")
    print("Get your token from @BotFather on Telegram")
    exit(1)

# Create Flask app for HTTP health checks
app = Flask(__name__)

@app.route('/')
def health():
    """Health check endpoint for UptimeRobot"""
    return {
        'status': 'ok',
        'bot': 'running',
        'submissions': len(db.get_all())
    }, 200

@app.route('/status')
def status():
    """Bot status endpoint"""
    return {
        'bot_name': 'Whitelist Bot',
        'status': 'running',
        'total_submissions': len(db.get_all()),
        'database': DB_FILE
    }, 200

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
FORM_LINK, WALLET = range(2)

# Database file
DB_FILE = 'submissions.json'

# Get Telegram token from .env
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    print("ERROR: TELEGRAM_TOKEN not set in .env file!")
    print("Get your token from @BotFather on Telegram")
    exit(1)


class SubmissionDatabase:
    """Simple JSON-based database for storing submissions"""
    
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.load()
    
    def load(self):
        """Load submissions from file"""
        if Path(self.db_file).exists():
            with open(self.db_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = []
    
    def save(self):
        """Save submissions to file"""
        with open(self.db_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add(self, user_id, username, form_link, wallet):
        """Add a new submission"""
        submission = {
            'user_id': user_id,
            'username': username,
            'form_link': form_link,
            'wallet': wallet,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        self.data.append(submission)
        self.save()
        return submission
    
    def get_all(self):
        """Get all submissions"""
        return self.data
    
    def get_by_user(self, user_id):
        """Get submissions by user"""
        return [s for s in self.data if s['user_id'] == user_id]


# Initialize database
db = SubmissionDatabase()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask for form link"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n"
        "I'll collect your form link and wallet address.\n\n"
        "Please send your Google Form link:\n"
        "(e.g., https://docs.google.com/forms/d/abc123/viewform)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return FORM_LINK


async def form_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store form link and ask for wallet"""
    form_link = update.message.text.strip()
    
    if not form_link.startswith('http'):
        await update.message.reply_text(
            "❌ Invalid link. Please send a valid Google Form URL:"
        )
        return FORM_LINK
    
    context.user_data['form_link'] = form_link
    await update.message.reply_text(
        f"✅ Form link saved!\n\n"
        f"Now, please send your wallet address:\n"
        f"(e.g., 0x1234567890abcdef1234567890abcdef12345678)",
    )
    return WALLET


async def wallet_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store wallet and save to database"""
    wallet = update.message.text.strip()
    
    if not wallet or len(wallet) < 20:
        await update.message.reply_text(
            "❌ Invalid wallet address. Please try again:"
        )
        return WALLET
    
    form_link = context.user_data['form_link']
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    
    # Save to database
    submission = db.add(user_id, username, form_link, wallet)
    
    await update.message.reply_text(
        f"✅ Submission saved!\n\n"
        f"💾 Data stored in database\n"
        f"🔗 Form: {form_link[:50]}...\n"
        f"💰 Wallet: {wallet[:20]}...\n\n"
        f"Status: ⏳ Pending\n\n"
        f"Type /start to submit another entry.",
        reply_markup=ReplyKeyboardRemove(),
    )
    
    logger.info(f"New submission from @{username} (ID: {user_id})")
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation"""
    await update.message.reply_text(
        "❌ Cancelled.\n\nType /start to try again.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message"""
    help_text = """
🤖 **Whitelist Bot**

**Commands:**
/start - Submit form link and wallet
/help - Show this message
/mystatus - View your submissions
/cancel - Cancel current submission

**How it works:**
1. Send /start
2. Provide your form link
3. Provide your wallet address
4. Data is stored in database

Questions? Contact admin.
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def mystatus_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's submissions"""
    user_id = update.effective_user.id
    submissions = db.get_by_user(user_id)
    
    if not submissions:
        await update.message.reply_text(
            "📊 No submissions yet.\n\nType /start to submit."
        )
        return
    
    text = f"📊 **Your Submissions** ({len(submissions)})\n\n"
    for i, sub in enumerate(submissions, 1):
        text += f"{i}. Wallet: `{sub['wallet'][:20]}...`\n"
        text += f"   Status: {sub['status']}\n"
        text += f"   Date: {sub['timestamp'][:10]}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show database stats (admin only)"""
    all_submissions = db.get_all()
    
    text = f"""
📊 **Database Stats**

Total Submissions: {len(all_submissions)}
Pending: {len([s for s in all_submissions if s['status'] == 'pending'])}
Submitted: {len([s for s in all_submissions if s['status'] == 'submitted'])}

Use /mystatus to see your submissions.
"""
    await update.message.reply_text(text)


def main() -> None:
    """Start the bot with Flask health check server"""
    print("🤖 Starting Telegram Whitelist Bot...")
    print(f"📁 Database: {DB_FILE}")
    print(f"📊 Submissions in DB: {len(db.get_all())}")
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FORM_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, form_link_received)],
            WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mystatus", mystatus_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("cancel", cancel))

    # Run Flask in a separate thread
    def run_flask():
        port = int(os.getenv('PORT', 5000))
        print(f"🌐 Flask server running on http://0.0.0.0:{port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Run the Telegram bot
    print("✅ Telegram bot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

