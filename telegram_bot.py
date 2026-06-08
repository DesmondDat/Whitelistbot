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
FORM_LINK, WALLET, SAVE_ADDRESS = range(3)

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


class SubmissionDatabase:
    """Simple JSON-based database for storing submissions and saved addresses"""
    
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.load()
    
    def load(self):
        """Load submissions from file"""
        if Path(self.db_file).exists():
            with open(self.db_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.data = data.get('submissions', [])
                    self.saved_addresses = data.get('saved_addresses', {})
                else:
                    self.data = data
                    self.saved_addresses = {}
        else:
            self.data = []
            self.saved_addresses = {}
    
    def save(self):
        """Save submissions and saved addresses to file"""
        with open(self.db_file, 'w') as f:
            json.dump({
                'submissions': self.data,
                'saved_addresses': self.saved_addresses
            }, f, indent=2)
    
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
    
    def add_saved_address(self, user_id, nickname, wallet_address):
        """Save a wallet address with nickname (max 5)"""
        user_id_str = str(user_id)
        if user_id_str not in self.saved_addresses:
            self.saved_addresses[user_id_str] = []
        
        # Check if max 5 addresses reached
        if len(self.saved_addresses[user_id_str]) >= 5:
            return False
        
        # Add address
        self.saved_addresses[user_id_str].append({
            'nickname': nickname,
            'wallet': wallet_address,
            'saved_at': datetime.now().isoformat()
        })
        self.save()
        return True
    
    def get_saved_addresses(self, user_id):
        """Get all saved addresses for user"""
        return self.saved_addresses.get(str(user_id), [])
    
    def delete_saved_address(self, user_id, index):
        """Delete a saved address by index"""
        user_id_str = str(user_id)
        if user_id_str in self.saved_addresses and 0 <= index < len(self.saved_addresses[user_id_str]):
            del self.saved_addresses[user_id_str][index]
            self.save()
            return True
        return False
    
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
    user_id = update.effective_user.id
    saved = db.get_saved_addresses(user_id)
    
    if saved:
        # Show saved addresses as quick buttons
        keyboard = []
        for i, addr in enumerate(saved):
            keyboard.append([f"💾 {addr['nickname']} - {addr['wallet'][:15]}..."])
        keyboard.append(["📝 Type new address"])
        
        await update.message.reply_text(
            f"✅ Form link saved!\n\n"
            f"Select a saved wallet or type a new one:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        )
    else:
        await update.message.reply_text(
            f"✅ Form link saved!\n\n"
            f"Now, please send your wallet address:\n"
            f"(e.g., 0x1234567890abcdef1234567890abcdef12345678)\n\n"
            f"💡 Tip: Use /save to save this address for next time!",
        )
    
    return WALLET


async def wallet_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store wallet and save to database"""
    wallet_input = update.message.text.strip()
    user_id = update.effective_user.id
    saved = db.get_saved_addresses(user_id)
    
    wallet = None
    
    # Check if user selected a saved address
    if saved:
        for i, addr in enumerate(saved):
            if addr['nickname'] in wallet_input or wallet_input.startswith('💾'):
                wallet = addr['wallet']
                break
    
    # If not a saved address, validate as new wallet
    if not wallet:
        wallet = wallet_input
        if not wallet or len(wallet) < 20:
            await update.message.reply_text(
                "❌ Invalid wallet address. Please try again:"
            )
            return WALLET
    
    form_link = context.user_data['form_link']
    username = update.effective_user.username or "unknown"
    
    # Save to database
    submission = db.add(user_id, username, form_link, wallet)
    
    await update.message.reply_text(
        f"✅ Submission saved!\n\n"
        f"💾 Data stored in database\n"
        f"🔗 Form: {form_link[:50]}...\n"
        f"💰 Wallet: {wallet[:20]}...\n\n"
        f"Status: ⏳ Pending\n\n"
        f"Options:\n"
        f"/start - Submit another entry\n"
        f"/save - Save this wallet address for later\n"
        f"/mysaved - View saved addresses",
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
/save - Save a wallet address (max 5)
/mysaved - View your saved addresses
/deletesaved - Delete a saved address
/cancel - Cancel current action

**How it works:**
1. Send /start
2. Provide your form link
3. Select a saved wallet or type new one
4. Done! Your data is saved

**Save Wallets:**
Use /save to store up to 5 wallet addresses with nicknames like "Main", "Trading", "Backup".
Next time you submit, just click the saved address!

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


async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start saving a new wallet address"""
    user_id = update.effective_user.id
    saved = db.get_saved_addresses(user_id)
    
    if len(saved) >= 5:
        await update.message.reply_text(
            "❌ You already have 5 saved addresses (maximum limit).\n\n"
            "Use /deletesaved to remove one first.\n"
            "Or use /mysaved to view them."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📝 What nickname for this wallet?\n"
        "(e.g., Main, Trading, Backup)\n\n"
        "Type /cancel to exit."
    )
    context.user_data['saving_address'] = True
    return SAVE_ADDRESS


async def save_nickname_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get nickname and ask for wallet, or save wallet if nickname already set"""
    user_id = update.effective_user.id
    
    # Check if we already have a nickname stored
    if 'save_nickname' not in context.user_data:
        # First message - this is the nickname
        nickname = update.message.text.strip()
        
        if len(nickname) > 20:
            await update.message.reply_text("❌ Nickname too long. Max 20 characters.")
            return SAVE_ADDRESS
        
        context.user_data['save_nickname'] = nickname
        await update.message.reply_text(
            f"💰 Now send the wallet address for '{nickname}':\n"
            f"(e.g., 0x1234567890abcdef1234567890abcdef12345678)"
        )
        return SAVE_ADDRESS
    else:
        # Second message - this is the wallet
        wallet = update.message.text.strip()
        
        if not wallet or len(wallet) < 20:
            await update.message.reply_text(
                "❌ Invalid wallet. Please send a valid address:"
            )
            return SAVE_ADDRESS
        
        nickname = context.user_data.get('save_nickname', 'Unknown')
        
        # Add to saved addresses
        success = db.add_saved_address(user_id, nickname, wallet)
        
        if success:
            saved = db.get_saved_addresses(user_id)
            await update.message.reply_text(
                f"✅ Saved!\n\n"
                f"📝 {nickname}\n"
                f"💰 {wallet[:20]}...\n\n"
                f"You have {len(saved)}/5 saved addresses.\n\n"
                f"Type /start to use it!"
            )
            # Clean up context
            context.user_data.pop('save_nickname', None)
        else:
            await update.message.reply_text(
                "❌ Error saving. Use /mysaved to check your addresses."
            )
        
        return ConversationHandler.END


async def mysaved_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's saved addresses"""
    user_id = update.effective_user.id
    saved = db.get_saved_addresses(user_id)
    
    if not saved:
        await update.message.reply_text(
            "📭 No saved addresses yet.\n\n"
            "Use /save to add one!"
        )
        return
    
    text = f"💾 **Your Saved Addresses** ({len(saved)}/5)\n\n"
    for i, addr in enumerate(saved, 1):
        text += f"{i}. **{addr['nickname']}**\n"
        text += f"   `{addr['wallet']}`\n"
        text += f"   Saved: {addr['saved_at'][:10]}\n\n"
    
    text += "Use /deletesaved to remove one\n"
    text += "Use /start to submit with a saved address"
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def deletesaved_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a saved address"""
    user_id = update.effective_user.id
    saved = db.get_saved_addresses(user_id)
    
    if not saved:
        await update.message.reply_text(
            "📭 No saved addresses to delete."
        )
        return
    
    text = "🗑️ **Select address to delete:**\n\n"
    for i, addr in enumerate(saved):
        text += f"`/del{i+1}` - {addr['nickname']}\n"
    
    text += "\n(Click a command to delete)"
    
    # Store for next command
    context.user_data['saved_addresses'] = saved
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def delete_index_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete saved address by index"""
    command = update.message.text
    user_id = update.effective_user.id
    
    try:
        # Extract index from command like /del1, /del2, etc
        index = int(command.replace('/del', '')) - 1
        saved = db.get_saved_addresses(user_id)
        
        if 0 <= index < len(saved):
            addr = saved[index]
            db.delete_saved_address(user_id, index)
            await update.message.reply_text(
                f"🗑️ Deleted: **{addr['nickname']}**\n\n"
                f"You now have {len(saved)-1}/5 saved addresses.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Invalid selection.")
    except:
        await update.message.reply_text("❌ Error. Use /deletesaved")



def main() -> None:
    """Start the bot with Flask health check server"""
    print("🤖 Starting Telegram Whitelist Bot...")
    print(f"📁 Database: {DB_FILE}")
    print(f"📊 Submissions in DB: {len(db.get_all())}")
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add submission conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FORM_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, form_link_received)],
            WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Add save address conversation handler
    save_handler = ConversationHandler(
        entry_points=[CommandHandler("save", save_command)],
        states={
            SAVE_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_nickname_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(save_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mystatus", mystatus_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("mysaved", mysaved_command))
    application.add_handler(CommandHandler("deletesaved", deletesaved_command))
    
    # Add handlers for /del1 through /del5
    for i in range(1, 6):
        application.add_handler(CommandHandler(f"del{i}", delete_index_command))
    
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

