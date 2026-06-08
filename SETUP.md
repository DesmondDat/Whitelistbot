# Whitelist Bot Setup Guide

This Google Forms bot has been configured for whitelist submissions with **speed optimization** and **email rotation** support. It can fill in wallet addresses, X (Twitter) usernames, and links automatically while bypassing the "one response per email" restriction.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Download Firefox driver (geckodriver):
   - Download from: https://github.com/mozilla/geckodriver/releases
   - Extract and save to your preferred location

## Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:
```
FORM_LINK=https://docs.google.com/forms/d/YOUR_FORM_ID/viewform
WALLET_ADDRESS=0x1234567890abcdef1234567890abcdef12345678,0xabcdef1234567890abcdef1234567890abcdef12
X_USERNAME=your_twitter_handle,another_handle
X_LINK=https://twitter.com/your_profile,https://twitter.com/another_profile
GOOGLE_EMAIL=your_email@gmail.com
GOOGLE_PASSWORD=your_app_password
GMAIL_ALIAS_PREFIX=whitelist
NUM_RESPONSES=
ELEMENT_WAIT_TIMEOUT=5
FORM_LOAD_WAIT=1
SUBMIT_WAIT=1
BETWEEN_SUBMISSIONS=0.5
DRIVER_PATH=/path/to/geckodriver
```

## Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `FORM_LINK` | The Google Form URL | `https://docs.google.com/forms/d/abc123/viewform` |
| `WALLET_ADDRESS` | Blockchain wallet addresses (comma-separated) | `0x1234...,0xabcd...` |
| `X_USERNAME` | Twitter/X usernames (comma-separated) | `@handle1,@handle2` |
| `X_LINK` | Links to X profiles (comma-separated) | `https://twitter.com/profile1,https://twitter.com/profile2` |
| `GOOGLE_EMAIL` | Google account email (optional - for sign-in required forms) | `your_email@gmail.com` |
| `GOOGLE_PASSWORD` | Google account password or App Password (optional) | Leave empty if form doesn't require login |
| `GMAIL_ALIAS_PREFIX` | Prefix for Gmail aliases to bypass "one email per response" restriction | `whitelist` or leave empty |
| `NUM_RESPONSES` | Number of times to submit per entry (auto-uses entry count if empty) | `1` or leave blank |
| `ELEMENT_WAIT_TIMEOUT` | Timeout for waiting for page elements (seconds) | `5` (shorter = faster but less stable) |
| `FORM_LOAD_WAIT` | Wait time after form loads (seconds) | `1` |
| `SUBMIT_WAIT` | Wait time after clicking submit (seconds) | `1` |
| `BETWEEN_SUBMISSIONS` | Delay between each submission (seconds) | `0.5` (very fast) |
| `DRIVER_PATH` | Path to geckodriver (optional) | `/home/user/geckodriver` |

## Speed Optimization

The bot has been optimized for **2-minute closing forms**:

1. **Configurable wait times** - Adjust these to balance speed vs stability:
   - `ELEMENT_WAIT_TIMEOUT=5` - How long to wait for elements to appear
   - `FORM_LOAD_WAIT=1` - Wait after form loads
   - `SUBMIT_WAIT=1` - Wait after submit
   - `BETWEEN_SUBMISSIONS=0.5` - Delay between submissions

2. **Smart waits** - Uses explicit element detection instead of fixed sleep times
3. **Parallel threads** - Can submit multiple forms simultaneously

**Estimated submission time**: 5-15 seconds per form (depending on your internet speed and form complexity)

## Bypassing "One Email Per Response"

The bot supports **two methods** to bypass email restrictions:

### Method 1: Gmail Alias (Recommended - Requires Gmail)

Use Gmail's `+` feature to create unlimited unique addresses for the same account:

```env
GOOGLE_EMAIL=yourname@gmail.com
GMAIL_ALIAS_PREFIX=whitelist
```

This generates:
- `yourname+whitelist1@gmail.com`
- `yourname+whitelist2@gmail.com`
- `yourname+whitelist3@gmail.com`
- etc.

**Advantages**: 
- Unlimited submissions
- All emails go to same Gmail inbox
- No setup required
- Google recognizes all as same account for Google Forms logins

### Method 2: Multiple Gmail Accounts

Use separate Google accounts:

```env
GOOGLE_EMAIL=account1@gmail.com,account2@gmail.com,account3@gmail.com
GOOGLE_PASSWORD=password_for_all_accounts
```

**Note**: All accounts must have the same password (or set up an app password)

### Method 3: No Email Restriction

If form doesn't have email restrictions, leave credentials empty:

```env
GOOGLE_EMAIL=
GOOGLE_PASSWORD=
```

## Google Sign-In Setup

If the form requires users to sign in:

1. **Enable 2FA on your Google account** (if not already enabled)
2. **Create an App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Generate a 16-character app password
   - Copy this to `GOOGLE_PASSWORD` in `.env`
3. **Add your credentials to `.env`**

### Note on App Passwords
- Use **App Passwords** instead of your actual password (safer)
- App Passwords work only with 2FA enabled
- If you don't have 2FA, you can use your account password, but it's not recommended

## Running the Bot

```bash
python main.py
```

The bot will:
1. Load all entries from `.env`
2. Calculate optimal timing
3. For each entry:
   - Authenticate with Google (using unique email if aliases configured)
   - Load the form
   - Fill all whitelist data
   - Submit the form
   - Move to next entry
4. Show progress and completion status

## Performance Tuning

### For very fast forms (close in <2 min):
```env
ELEMENT_WAIT_TIMEOUT=3
FORM_LOAD_WAIT=0.5
SUBMIT_WAIT=0.5
BETWEEN_SUBMISSIONS=0.2
```

### For slow/complex forms:
```env
ELEMENT_WAIT_TIMEOUT=10
FORM_LOAD_WAIT=2
SUBMIT_WAIT=2
BETWEEN_SUBMISSIONS=1
```

### Maximum speed (parallel submissions):
The bot automatically handles this - if you set `NUM_RESPONSES` to a high number, it will spawn multiple threads to submit in parallel (max 4 at a time).

## Troubleshooting

### "Form closed" errors
- Forms are closing before bot finishes. Try reducing wait times or pre-fetching data
- Ensure wallet addresses and usernames are in `.env` before running

### Login Issues
- **"Invalid credentials"**: Check your email and App Password are correct
- **CAPTCHA appears**: Google is detecting automated access. Wait a few hours and try again
- **"Account not recognized"**: Use the email associated with your Google account

### Email Aliases Not Working
- Gmail only - not supported on other email providers
- Emails must be in format: `yourname@gmail.com`
- The `+` symbol is key to the alias feature

### Form Not Submitting
- Check if form fields have different labels/placeholders
- Some fields may use IDs instead of placeholders
- Review Firefox console for JavaScript errors
- Try increasing `ELEMENT_WAIT_TIMEOUT`

## Important Notes

- The bot uses Selenium + Firefox for full automation
- Each email (or alias) is treated as unique by Google Forms
- Wait times directly impact success rate vs speed - balance is key
- **Terms of Service**: Ensure your usage complies with Google Forms ToS
- **Security**: Use App Passwords instead of storing your actual password
