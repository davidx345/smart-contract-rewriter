# 🔐 GitHub Secrets Configuration Guide

## What are GitHub Secrets?
GitHub Secrets are encrypted environment variables that store sensitive information like API keys, passwords, and webhook URLs securely in your repository.

## Required Secrets for Notifications

### 1. Slack Configuration
- **Secret Name:** `SLACK_WEBHOOK_URL`
- **Value:** Your Slack webhook URL (starts with https://hooks.slack.com/services/...)
- **Purpose:** Sends real-time notifications to your Slack channel

### 2. Email Configuration
- **Secret Name:** `EMAIL_USERNAME`
- **Value:** Your email address (e.g., your-email@gmail.com)
- **Purpose:** The "from" address for email notifications

- **Secret Name:** `EMAIL_PASSWORD`
- **Value:** Your app password (Gmail) or regular password (Outlook)
- **Purpose:** Authentication for sending emails

- **Secret Name:** `NOTIFICATION_EMAIL`
- **Value:** Email address where you want to receive alerts
- **Purpose:** The "to" address for critical failure notifications

## How to Add Secrets to GitHub

### Step 1: Go to Repository Settings
1. Open your GitHub repository: https://github.com/davidx345/smart-contract-rewriter
2. Click on "Settings" tab
3. Scroll down to "Security" section
4. Click "Secrets and variables" → "Actions"

### Step 2: Add New Repository Secret
1. Click "New repository secret"
2. Enter the secret name (exactly as shown above)
3. Enter the secret value
4. Click "Add secret"

### Step 3: Repeat for All Secrets
Add all 4 secrets:
- SLACK_WEBHOOK_URL
- EMAIL_USERNAME
- EMAIL_PASSWORD
- NOTIFICATION_EMAIL

## Example Values (Replace with your actual values)
```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
NOTIFICATION_EMAIL=your-email@gmail.com
```

## Testing the Setup
Once you add these secrets and push a commit, the notification system will automatically work:
- ✅ Success deployments → Slack #general channel
- ❌ Failed deployments → Slack #deployments channel + Email alert
- 🔄 All deployments → Slack #deployments channel with status

## Security Notes
- ✅ Secrets are encrypted and not visible in logs
- ✅ Only GitHub Actions can access them
- ✅ They never appear in your code
- ✅ You can update them anytime without changing code
