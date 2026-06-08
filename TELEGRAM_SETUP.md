# Telegram Bot Setup Guide

This guide will help you set up a Telegram bot for your whitelist form submissions.

## Step 1: Create a Telegram Bot

### 1.1 Open Telegram
- Download Telegram from [telegram.org](https://telegram.org) or use the web version at [web.telegram.org](https://web.telegram.org)

### 1.2 Create Bot with @BotFather
1. Search for `@BotFather` in Telegram
2. Send `/newbot`
3. Follow the prompts:
   - **Name**: Choose a name (e.g., "My Whitelist Bot")
   - **Username**: Must end with `_bot` (e.g., `my_whitelist_bot`) - must be unique
4. **Copy the API Token** - looks like: `123456789:ABCDefGhIjKlMnOpQrStUvWxYz`

### 1.3 Configure the Bot (Optional)
Back in @BotFather chat, send:
- `/setdescription` - Add a description
- `/setcommands` - Set default commands:
  ```
  start - Begin whitelist submission
  help - Show help message
  status - Check form status
  cancel - Cancel submission
  ```

## Step 2: Update Your Configuration

1. Edit `.env` file:
```bash
TELEGRAM_TOKEN=YOUR_TOKEN_HERE
FORM_LINK=https://docs.google.com/forms/d/YOUR_FORM_ID/viewform
```

2. Install Telegram dependencies:
```bash
pip install -r requirements.txt
```

## Step 3: Run the Telegram Bot

```bash
python telegram_bot.py
```

You should see:
```
🤖 Starting Telegram Whitelist Bot...
✅ Bot is running. Press Ctrl+C to stop.
```

## Step 4: Find Your Bot on Telegram

1. Search for your bot by username: `@my_whitelist_bot`
2. Send `/start` to test
3. Follow the prompts to submit

## User Workflow

When a user sends `/start`:

1. **Wallet Address**
   - User provides their wallet address (e.g., `0x1234567890abcdef1234567890abcdef12345678`)

2. **Twitter Username**
   - User provides their Twitter handle (e.g., `@myhandle` or just `myhandle`)

3. **Twitter Link**
   - User provides their profile link (e.g., `https://twitter.com/myhandle`)

4. **Confirmation**
   - Bot shows all info
   - User confirms with ✅ or cancels with ❌

5. **Submission**
   - Bot submits to Google Form
   - User receives confirmation

## Commands Available

| Command | Description |
|---------|-------------|
| `/start` | Start whitelist submission |
| `/help` | Show help message |
| `/status` | Check if form is open |
| `/cancel` | Cancel current submission |

## Hosting Options

### Option 1: Local Computer (Simple)
- Run `python telegram_bot.py` on your computer
- Bot works only while script is running
- Best for testing

### Option 2: Cloud Server (Production)
Deploy to a cloud service for 24/7 availability:

**Popular options:**
- **Heroku** (free tier limited)
- **AWS** (free tier available)
- **Google Cloud**
- **DigitalOcean** (cheapest - $5/month)
- **Railway.app**
- **Replit**

### Option 3: Telegram Webhooks (Advanced)
Instead of polling, use webhooks for better performance.

## Troubleshooting

### Bot not responding
- Check `TELEGRAM_TOKEN` is correct in `.env`
- Ensure `python telegram_bot.py` is running
- Check internet connection

### Form not submitting
- Verify `FORM_LINK` is correct
- Check `DRIVER_PATH` points to geckodriver
- If form requires auth, ensure `GOOGLE_EMAIL` and `GOOGLE_PASSWORD` are set

### Users get "error submitting form"
- Check form is still open
- Verify wallet/username formats are correct
- Check Firefox browser logs

## Advanced: Deploy to Cloud

### Using Railway (Easiest)

1. **Create Railway account** at [railway.app](https://railway.app)

2. **Connect GitHub**
   - Push your code to GitHub
   - Connect Railway to your GitHub repo

3. **Add `Procfile`** (in your project root):
   ```
   worker: python telegram_bot.py
   ```

4. **Deploy**
   - Railway auto-deploys on git push
   - Add `TELEGRAM_TOKEN` env var in Railway dashboard
   - Bot runs 24/7

### Using Replit

1. Go to [replit.com](https://replit.com)
2. Upload your project (or connect GitHub)
3. Add secret: `TELEGRAM_TOKEN`
4. Run `python telegram_bot.py`
5. Keep running (upgrade for 24/7 uptime)

## Security Notes

- ✅ **Never** commit `.env` to GitHub (use `.gitignore`)
- ✅ Use app-specific passwords, not your actual Google password
- ✅ Keep your bot token secret
- ✅ Validate user inputs
- ✅ Log all submissions for audit trail

## Customization

### Change the questions
Edit `telegram_bot.py` and modify the `await update.message.reply_text()` messages in:
- `wallet_received()`
- `twitter_received()`
- `link_received()`

### Add more fields
Add more states to the `ConversationHandler`:
```python
# Define new state
FIELD_NAME = 4

# Add to conversation
FIELD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, field_handler)],

# Create handler function
async def field_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Your code here
```

## Support

If you have issues:
1. Check Telegram bot logs
2. Verify form is open (visit link directly)
3. Ensure geckodriver is installed
4. Check `.env` configuration

---

**Ready to go live?** Start by running the local bot first, test thoroughly, then deploy to cloud for 24/7 availability.
