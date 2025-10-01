#!/bin/bash

# 🔔 Notification System Test Script
# This script is used to test the CI/CD notification system

echo "🧪 Testing notification system..."
echo "⏰ Test timestamp: $(date)"
echo "📧 This should trigger Slack and email notifications"
echo "✅ Notification test script executed successfully"

# Test environment variables (for CI/CD)
if [ "$CI" = "true" ]; then
    echo "🤖 Running in CI/CD environment"
    echo "📊 Workflow: $GITHUB_WORKFLOW"
    echo "🏷️ Run ID: $GITHUB_RUN_ID"
fi

exit 0