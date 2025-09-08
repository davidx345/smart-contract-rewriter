# 📧 Email Notification Setup Guide

## Gmail Setup (Recommended)
If you want to use Gmail for sending notifications:

### Step 1: Enable 2-Factor Authentication
1. Go to https://myaccount.google.com/security
2. Enable 2-Factor Authentication if not already enabled

### Step 2: Create App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer" (or "Other")
3. Generate password
4. Save this 16-character password (example: abcd efgh ijkl mnop)

### Step 3: Note Your Settings
- **SMTP Server:** smtp.gmail.com
- **Port:** 587
- **Username:** your-email@gmail.com
- **Password:** the 16-character app password (not your regular password)

## Alternative: Outlook/Hotmail
- **SMTP Server:** smtp-mail.outlook.com
- **Port:** 587
- **Username:** your-email@outlook.com or @hotmail.com
- **Password:** your regular password (or app password if 2FA enabled)

## What information I need from you:
1. **Email address** you want to send FROM (notifications will come from this)
2. **Email address** you want to send TO (where you want to receive alerts)
3. **App password** (for Gmail) or regular password (for Outlook)

## Security Note:
We'll store these securely in GitHub Secrets - they won't be visible in code!
