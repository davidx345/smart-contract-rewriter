  # 🚀 Quick Start Guide - Phase 7 Serverless

Get your serverless Lambda function deployed in **5 minutes**!

## Prerequisites Checklist

- [ ] AWS account (free tier eligible)
- [ ] OpenAI API key (get from: https://platform.openai.com/api-keys)
- [ ] Optional: Google Gemini API key (get from: https://makersuite.google.com/app/apikey)

## Installation (One-time setup)

```bash
# 1. Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# 2. Configure AWS credentials
aws configure
# Enter your Access Key ID and Secret Access Key

# 3. Install AWS SAM CLI
pip install aws-sam-cli

# 4. Verify installations
aws --version    # Should show: aws-cli/2.x
sam --version    # Should show: SAM CLI, version 1.x
```

## Deployment (Automated)

```bash
cd serverless/

# Make deployment script executable
chmod +x deploy.sh

# Run automated deployment
./deploy.sh

# Follow the prompts:
# 1. Enter OpenAI API key
# 2. Enter Gemini API key (optional)
# 3. Confirm deployment
# 4. Wait ~2-3 minutes for deployment
# 5. Test the deployed API
```

## What You'll Get

After deployment, you'll have:

✅ **Lambda Function**: Auto-scaling serverless compute  
✅ **API Gateway**: Public HTTPS endpoint  
✅ **CloudWatch Logs**: Automatic logging  
✅ **CloudWatch Alarms**: Error and throttle alerts  
✅ **IAM Roles**: Least-privilege security  
✅ **Cost Optimization**: Pay only for what you use  

## Testing Your Deployment

```bash
# Your API endpoint will be shown after deployment
# Example: https://abc123.execute-api.us-east-1.amazonaws.com/dev/analyze

# Test with curl
curl -X POST https://YOUR-API-ENDPOINT/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract Test { uint256 value; }",
    "contract_name": "TestContract",
    "analysis_type": "security"
  }'
```

## Costs Estimate

For the **AWS Free Tier**:
- **Lambda**: 1M requests + 400K GB-seconds per month (FREE)
- **API Gateway**: 1M requests per month (FREE for 12 months)
- **CloudWatch**: 5GB logs + 10 custom metrics (FREE)

**After free tier:**
- 10,000 analyses/month = ~$1.70/month
- 100,000 analyses/month = ~$17/month

Compare to EC2 t2.micro always running = $8.50/month

## Monitoring

```bash
# View logs in real-time
sam logs --name ContractAnalyzerFunction --tail

# Check Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=dev-contract-analyzer \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Sum
```

## Cleanup

```bash
# Delete all resources
./deploy.sh cleanup

# Or manually
sam delete
```

## Troubleshooting

### Issue: "AWS credentials not configured"
**Solution:**
```bash
aws configure
# Enter Access Key ID, Secret Access Key, Region (us-east-1)
```

### Issue: "SAM CLI not found"
**Solution:**
```bash
pip install aws-sam-cli
```

### Issue: "Lambda timeout"
**Solution:** Check CloudWatch logs:
```bash
sam logs --name ContractAnalyzerFunction --tail
```

### Issue: "API returns 502/504"
**Solution:** Check Lambda errors:
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/dev-contract-analyzer \
  --filter-pattern "ERROR"
```

## Next Steps

1. ✅ **Deploy successfully** (you're here!)
2. 📊 **Monitor performance** in CloudWatch
3. 💰 **Set up billing alerts** (recommended)
4. 🔒 **Add JWT authentication** to API Gateway
5. 🚀 **Deploy more Lambda functions** (rewrite, generate)
6. 📦 **Integrate with frontend** (update API endpoint)
7. 🔄 **Add to CI/CD pipeline** (automate deployment)

## Resources

- [Complete README](README.md) - Full documentation
- [AWS Lambda Docs](https://docs.aws.amazon.com/lambda/)
- [AWS SAM Guide](https://docs.aws.amazon.com/serverless-application-model/)
- [handler.py](contract-analyzer/handler.py) - Lambda function code
- [template.yaml](template.yaml) - Infrastructure definition

---

**Time to deploy:** 5 minutes  
**Time to delete:** 30 seconds  
**Cost (free tier):** $0/month  
**Learning value:** Priceless! 🎓
