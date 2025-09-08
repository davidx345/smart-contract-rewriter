# 🔔 Slack Webhook Setup Guide

## Step 1: Create a Slack Workspace (if you don't have one)
1. Go to https://slack.com/create
2. Create a new workspace or use existing one

## Step 2: Create a Slack App
1. Go to https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. Name: "Smart Contract CI/CD Bot"
5. Select your workspace

## Step 3: Enable Incoming Webhooks
1. In your app settings, go to "Features" → "Incoming Webhooks"
2. Toggle "Activate Incoming Webhooks" to ON
3. Click "Add New Webhook to Workspace"
4. Choose a channel (create #deployments channel recommended)
5. Click "Allow"

## Step 4: Copy the Webhook URL
You'll get a URL like:
https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX

## Step 5: Test the Webhook
Run this command to test:
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Hello from Smart Contract CI/CD!"}' \
  YOUR_WEBHOOK_URL_HERE
```

## What to do next:
1. Follow the steps above
2. Get your webhook URL
3. Come back and we'll configure it in GitHub secrets
