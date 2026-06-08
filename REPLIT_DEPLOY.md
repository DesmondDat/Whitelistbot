# Replit Deployment Guide

Deploy your Telegram bot to Replit for **24/7 uptime**.

## Step 1: Create Replit Account

1. Go to [replit.com](https://replit.com)
2. Sign up (free account)
3. Connect your GitHub or upload files directly

## Step 2: Create a New Replit Project

### Option A: From GitHub (Easiest)
1. Push your code to GitHub
2. On Replit, click "Create" → "Import from GitHub"
3. Select your repository
4. Wait for import to complete

### Option B: Upload Files Directly
1. Click "Create" → "New Replit"
2. Choose "Python" as language
3. Upload your files:
   - `telegram_bot.py`
   - `requirements.txt`
   - `.env`
   - `Procfile`
   - `runtime.txt`

## Step 3: Install Dependencies

In Replit shell, run:
```bash
pip install -r requirements.txt
```

## Step 4: Add Environment Variable

1. Click "Secrets" (lock icon) on the left sidebar
2. Add new secret:
   - Key: `TELEGRAM_TOKEN`
   - Value: Your token from @BotFather
3. Save

## Step 5: Create `.env.local` File

In Replit, create `.env.local`:
```
TELEGRAM_TOKEN=your_token_here
```

(Replit will automatically load `.env.local`)

## Step 6: Run the Bot

In Replit shell:
```bash
python telegram_bot.py
```

You should see:
```
🤖 Starting Telegram Whitelist Bot...
✅ Bot is running. Press Ctrl+C to stop.
```

## Step 7: Set as Background Worker (24/7)

### Keep bot running 24/7:

1. Click the play button (Run button) - this will run once
2. To make it persistent, use Replit's "Always On" feature:
   - Upgrade to Replit Pro ($7/month)
   - OR use external uptime monitoring

### Free Alternative: Use UptimeRobot
1. Go to [UptimeRobot.com](https://uptimerobot.com)
2. Create free account
3. Add a new monitor:
   - Type: HTTP(s)
   - URL: Your Replit project URL (usually `https://project-name.username.repl.co`)
   - Interval: 5 minutes
4. This will keep pinging your bot and keep it alive

## Step 8: Test Your Bot

On Telegram:
1. Search for your bot (@your_bot_name)
2. Send `/start`
3. Submit form link and wallet address
4. Check `submissions.json` file on Replit

## Project Structure on Replit

```
your-project/
├── telegram_bot.py       (Main bot)
├── requirements.txt      (Dependencies)
├── .env.local            (Environment variables)
├── Procfile             (Process file)
├── runtime.txt          (Python version)
└── submissions.json     (Database - auto-created)
```

## Accessing Your Database

In Replit:
1. Click "Files" on the left
2. Look for `submissions.json`
3. Click to view all submissions
4. Download for backup

## Database Format

```json
[
  {
    "user_id": 123456789,
    "username": "user_handle",
    "form_link": "https://docs.google.com/forms/d/abc123/viewform",
    "wallet": "0x1234567890abcdef...",
    "timestamp": "2026-06-08T12:34:56.789012",
    "status": "pending"
  }
]
```

## Troubleshooting

### Bot not responding
- Check TELEGRAM_TOKEN in Secrets
- Ensure bot is still running (check console)
- Restart the project

### Database not saving
- Check write permissions in `/home/runner` directory
- Verify `submissions.json` file exists
- Check Replit console for errors

### Bot keeps stopping
- Upgrade to Replit Pro for Always On
- Use UptimeRobot for free monitoring
- Check error logs in console

## Monitoring Your Bot

### View Logs
All messages, errors, and submissions are logged to console.

### Export Submissions
Regularly download `submissions.json` to backup:
1. Right-click file → Download
2. Store safely on your computer

## Auto-Restart on Error

For reliability, use this wrapper script `run.py`:

```python
import subprocess
import time

while True:
    try:
        subprocess.run(['python', 'telegram_bot.py'])
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
        continue
```

Then run `python run.py` instead.

## Next Steps

1. ✅ Deploy bot to Replit
2. ✅ Test with /start command
3. ✅ Share bot link with users
4. ✅ Monitor submissions in `submissions.json`
5. ✅ Regularly backup database

## Bot Commands

Users can use:
- `/start` - Submit form link and wallet
- `/help` - Show help
- `/mystatus` - View their submissions
- `/stats` - See total submissions
- `/cancel` - Cancel submission

## Cost

- **Replit Free**: Runs when you visit, goes to sleep after inactivity
- **Replit Pro**: $7/month for Always On (24/7 uptime)
- **UptimeRobot Free**: Keeps bot alive (unlimited)

**Recommended**: Use Replit Free + UptimeRobot Free for $0 cost with decent uptime.

---

**Ready to deploy?** Start by creating your Replit project now!
