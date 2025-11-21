# Smart Contract Analyzer - Serverless Implementation (Phase 7)

This directory contains the **AWS Lambda serverless implementation** of the contract analysis service, demonstrating **Phase 7: Serverless & Cloud-Native Services** from the DevOps roadmap.

---

## 📚 What You'll Learn

By implementing this serverless architecture, you'll gain hands-on experience with:

### 1. **AWS Lambda** (Function-as-a-Service)
- **Event-driven computing**: Code runs only when triggered
- **Auto-scaling**: From 0 to 1000s of concurrent executions
- **Pay-per-use**: No charges when idle
- **Managed infrastructure**: No servers to maintain

### 2. **API Gateway**
- **RESTful API management**: Route HTTP requests to Lambda
- **Security**: API keys, JWT authorization, throttling
- **CORS configuration**: Cross-origin resource sharing
- **Rate limiting**: Prevent API abuse

### 3. **Infrastructure as Code (SAM)**
- **AWS SAM**: Simplified CloudFormation for serverless
- **Declarative resources**: Define infrastructure in YAML
- **Reproducible deployments**: Same infrastructure every time
- **Version control**: Track infrastructure changes in Git

### 4. **Event-Driven Architecture**
- **S3 triggers**: Automatic processing on file upload
- **Async workflows**: Decouple services with events
- **Scalability**: Handle variable workloads efficiently

### 5. **Cost Optimization**
- **Serverless economics**: Pay only for execution time
- **Memory tuning**: Optimize Lambda memory allocation
- **Cold start mitigation**: Keep functions warm
- **Cost monitoring**: Track spending per function

### 6. **Monitoring & Observability**
- **CloudWatch Logs**: Centralized logging
- **CloudWatch Metrics**: Performance monitoring
- **CloudWatch Alarms**: Automated alerting
- **X-Ray tracing**: Distributed tracing

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User/Frontend                            │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS POST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway                                 │
│  - REST API endpoint: /analyze                                   │
│  - JWT Authentication                                            │
│  - Rate Limiting: 50 req/sec                                     │
│  - CORS enabled                                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │ Invoke
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Lambda Function: ContractAnalyzer                   │
│                                                                  │
│  1. Receives contract code from API Gateway                      │
│  2. Validates input (Solidity syntax check)                      │
│  3. Calls OpenAI GPT-4 API (primary)                            │
│  4. Falls back to Google Gemini if OpenAI fails                 │
│  5. Parses AI response (security + gas analysis)                │
│  6. Returns JSON response                                        │
│                                                                  │
│  Runtime: Python 3.11                                            │
│  Memory: 1024 MB                                                 │
│  Timeout: 300 seconds (5 min)                                    │
│  Auto-scaling: 0 → 1000 concurrent                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌──────────────────┐        ┌──────────────────┐
    │  OpenAI API      │        │  Google Gemini   │
    │  (GPT-4)         │        │  (Fallback)      │
    │  - Primary AI    │        │  - Cost effective│
    │  - Best accuracy │        │  - Redundancy    │
    └──────────────────┘        └──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Optional: S3 Trigger Flow                     │
└─────────────────────────────────────────────────────────────────┘
                             
    User uploads .sol file
              │
              ▼
    ┌─────────────────┐
    │   S3 Bucket     │
    │  - Versioning   │
    │  - Encryption   │
    └────────┬────────┘
             │ S3 Event
             ▼
    ┌─────────────────┐
    │  Lambda Trigger │
    │  - Auto analyze │
    │  - Store result │
    └─────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring & Logs                             │
└─────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────┐
    │ CloudWatch Logs │────▶│ CloudWatch      │────▶│  Alarms     │
    │ - Function logs │     │ Metrics         │     │ - Errors    │
    │ - API logs      │     │ - Invocations   │     │ - Throttles │
    │ - Error traces  │     │ - Duration      │     │ - 5xx codes │
    └─────────────────┘     │ - Error rate    │     └─────────────┘
                            └─────────────────┘
```

---

## 📁 Project Structure

```
serverless/
├── template.yaml                 # SAM template (IaC for serverless)
├── samconfig.toml               # SAM deployment configuration
├── README.md                    # This file
│
├── contract-analyzer/           # Lambda function code
│   ├── handler.py              # Main Lambda handler
│   │   ├── lambda_handler()    # API Gateway trigger
│   │   └── handler_for_s3_trigger()  # S3 upload trigger
│   │
│   └── requirements.txt        # Python dependencies
│       ├── openai             # OpenAI GPT-4 API
│       ├── google-generativeai # Google Gemini API
│       └── boto3              # AWS SDK
│
└── events/                     # Test events for local testing
    ├── analyze-event.json     # Sample API Gateway event
    └── s3-upload-event.json   # Sample S3 trigger event
```

---

## 🚀 Deployment Guide

### Prerequisites

1. **AWS Account**: Free tier eligible
2. **AWS CLI**: Installed and configured
3. **AWS SAM CLI**: Installed (for serverless deployment)
4. **Python 3.11**: For local testing
5. **Docker**: For building Lambda layers (optional)

### Installation

```bash
# 1. Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# 2. Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output (json)

# 3. Install AWS SAM CLI
pip install aws-sam-cli
# or on Mac: brew install aws-sam-cli
# or on Windows: choco install aws-sam-cli

# 4. Verify installations
aws --version
sam --version
python --version
```

### Step-by-Step Deployment

#### **Step 1: Navigate to serverless directory**

```bash
cd serverless/
```

#### **Step 2: Set up API keys (IMPORTANT)**

Create a file to store your API keys securely:

```bash
# Create parameter file (never commit this to Git!)
cat > parameters.json << EOF
[
  {
    "ParameterKey": "OpenAIAPIKey",
    "ParameterValue": "sk-your-openai-api-key-here"
  },
  {
    "ParameterKey": "GeminiAPIKey",
    "ParameterValue": "your-gemini-api-key-here"
  },
  {
    "ParameterKey": "Environment",
    "ParameterValue": "dev"
  },
  {
    "ParameterKey": "EnableS3Trigger",
    "ParameterValue": "false"
  }
]
EOF

# Add to .gitignore to prevent accidental commit
echo "parameters.json" >> ../.gitignore
```

#### **Step 3: Build the Lambda function**

```bash
# This downloads dependencies and packages your code
sam build

# Output:
# Building codeuri: contract-analyzer/ runtime: python3.11
# Running PythonPipBuilder:ResolveDependencies
# Running PythonPipBuilder:CopySource
# Build Succeeded
```

**What happens during build:**
- Downloads `openai`, `google-generativeai`, `boto3` packages
- Creates deployment package with all dependencies
- Stores in `.aws-sam/build/` directory

#### **Step 4: Test locally (optional but recommended)**

```bash
# Start local API Gateway
sam local start-api

# In another terminal, test the endpoint
curl -X POST http://localhost:3000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract Test { }",
    "contract_name": "TestContract",
    "analysis_type": "security"
  }'
```

**Benefits of local testing:**
- No AWS charges during development
- Fast iteration cycle
- Debug with breakpoints
- Test without deploying

#### **Step 5: Deploy to AWS**

```bash
# Guided deployment (first time)
sam deploy --guided --parameter-overrides file://parameters.json

# You'll be prompted:
# Stack Name [smart-contract-analyzer]: <press enter>
# AWS Region [us-east-1]: <press enter>
# Parameter OpenAIAPIKey: ********** (hidden)
# Parameter GeminiAPIKey: ********** (hidden)
# Confirm changes before deploy [Y/n]: Y
# Allow SAM CLI IAM role creation [Y/n]: Y
# Save arguments to configuration file [Y/n]: Y

# Deployment starts...
# Creating CloudFormation stack...
# Uploading Lambda code to S3...
# Creating Lambda function...
# Creating API Gateway...
# Stack creation complete!
```

**What gets created:**
1. Lambda function: `dev-contract-analyzer`
2. API Gateway: `dev-contract-analyzer-api`
3. CloudWatch Log Groups: `/aws/lambda/dev-contract-analyzer`
4. IAM Role: For Lambda execution permissions
5. CloudWatch Alarms: Error and throttle monitoring

#### **Step 6: Get your API endpoint**

```bash
# SAM outputs the API URL
sam list endpoints --output json

# Example output:
# https://abc123def.execute-api.us-east-1.amazonaws.com/dev/analyze
```

#### **Step 7: Test the deployed API**

```bash
# Store the endpoint URL
API_URL="https://your-api-id.execute-api.us-east-1.amazonaws.com/dev"

# Test the analysis endpoint
curl -X POST ${API_URL}/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0;\n\ncontract VulnerableBank {\n    mapping(address => uint256) public balances;\n    \n    function deposit() public payable {\n        balances[msg.sender] += msg.value;\n    }\n    \n    function withdraw(uint256 amount) public {\n        require(balances[msg.sender] >= amount);\n        (bool success, ) = msg.sender.call{value: amount}(\"\");\n        require(success);\n        balances[msg.sender] -= amount;\n    }\n}",
    "contract_name": "VulnerableBank",
    "analysis_type": "security"
  }'
```

**Expected response:**
```json
{
  "request_id": "abc-123-def-456",
  "contract_name": "VulnerableBank",
  "analysis_type": "security",
  "analysis_report": {
    "vulnerabilities": [
      {
        "type": "reentrancy",
        "severity": "critical",
        "line_number": 10,
        "description": "Reentrancy vulnerability in withdraw function",
        "recommendation": "Use ReentrancyGuard or checks-effects-interactions pattern"
      }
    ],
    "overall_security_score": 35,
    "service_used": "OpenAI",
    "model_used": "gpt-4"
  },
  "timestamp": "2025-11-06T10:30:00Z"
}
```

---

## 🎯 Understanding Lambda Costs

### Cost Breakdown

**Lambda Pricing (us-east-1):**
- **Requests**: $0.20 per 1 million requests
- **Duration**: $0.0000166667 per GB-second
- **Free Tier**: 1 million requests + 400,000 GB-seconds per month

**Example Calculation:**

Assuming:
- Memory: 1024 MB (1 GB)
- Average duration: 10 seconds per analysis
- Usage: 10,000 analyses per month

```
Requests cost:
10,000 requests × $0.20 / 1,000,000 = $0.002

Duration cost:
10,000 × 10 seconds × 1 GB × $0.0000166667 = $1.67

Total: $1.67/month for 10,000 analyses
```

**Compare to EC2 t2.micro (always running):**
- Cost: ~$8.50/month
- Savings: 81% with serverless!

**Additional costs:**
- API Gateway: $3.50 per million requests
- CloudWatch Logs: $0.50 per GB ingested
- S3 (if enabled): $0.023 per GB

---

## 🔧 Configuration Options

### Adjust Lambda Memory

Memory affects both cost and performance:

```yaml
# In template.yaml
ContractAnalyzerFunction:
  Type: AWS::Serverless::Function
  Properties:
    MemorySize: 512    # Options: 128, 256, 512, 1024, 1536, 2048, 3008
    Timeout: 60        # Seconds (max: 900)
```

**Memory tuning tips:**
- More memory = faster CPU = lower duration
- Find sweet spot: Run CloudWatch Insights query
- Monitor: `Max(MemoryUsed) / MemoryAllocated`

### Enable S3 Automatic Analysis

```bash
# Redeploy with S3 trigger enabled
sam deploy --parameter-overrides \
  Environment=dev \
  EnableS3Trigger=true \
  OpenAIAPIKey=sk-xxx \
  GeminiAPIKey=yyy
```

This creates an S3 bucket where users can upload `.sol` files for automatic analysis.

### Switch to Gemini-only (Cost Optimization)

Edit `handler.py`:

```python
# Comment out OpenAI initialization
# openai_client = None

# Force Gemini
if GEMINI_API_KEY and genai:
    gemini_model = genai.GenerativeModel(GEMINI_MODEL)
```

**Gemini advantages:**
- 10x cheaper than GPT-4
- Faster response times
- Generous free tier

---

## 📊 Monitoring & Debugging

### View Lambda Logs

```bash
# Real-time logs
sam logs --name ContractAnalyzerFunction --tail

# Specific time range
sam logs --name ContractAnalyzerFunction \
  --start-time '10min ago' \
  --end-time 'now'

# Filter errors only
sam logs --name ContractAnalyzerFunction --filter "ERROR"
```

### CloudWatch Insights Queries

```sql
-- Average execution duration
fields @timestamp, @duration
| stats avg(@duration), max(@duration), min(@duration)

-- Error rate
filter @message like /ERROR/
| stats count() as error_count by bin(5m)

-- Memory usage
fields @memorySize, @maxMemoryUsed
| stats avg(@maxMemoryUsed) as avg_memory_mb

-- Most expensive invocations
fields @timestamp, @duration, @billedDuration
| sort @billedDuration desc
| limit 20
```

### CloudWatch Metrics Dashboard

Key metrics to monitor:
- **Invocations**: How many times Lambda was called
- **Duration**: How long each invocation took
- **Errors**: Failed invocations
- **Throttles**: Rejected due to concurrency limits
- **ConcurrentExecutions**: Simultaneous invocations

### X-Ray Tracing

Enable detailed tracing:

```yaml
# In template.yaml
ContractAnalyzerFunction:
  Properties:
    Tracing: Active
```

View traces:
```bash
aws xray get-trace-summaries --start-time $(date -u -d '1 hour ago' +%s) --end-time $(date +%s)
```

---

## 🧪 Testing

### Unit Tests

Create `tests/test_handler.py`:

```python
import json
import pytest
from contract-analyzer.handler import lambda_handler

def test_lambda_handler_success():
    """Test successful contract analysis"""
    
    event = {
        'body': json.dumps({
            'contract_code': 'pragma solidity ^0.8.0; contract Test {}',
            'contract_name': 'Test',
            'analysis_type': 'security'
        })
    }
    
    context = MockContext()
    
    response = lambda_handler(event, context)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'analysis_report' in body

def test_lambda_handler_missing_code():
    """Test error handling for missing contract code"""
    
    event = {'body': json.dumps({})}
    context = MockContext()
    
    response = lambda_handler(event, context)
    
    assert response['statusCode'] == 400

class MockContext:
    request_id = 'test-request-123'
    memory_limit_in_mb = 1024
```

Run tests:
```bash
pytest tests/ -v
```

### Integration Tests

```bash
# Test against deployed API
API_URL="https://your-api.execute-api.us-east-1.amazonaws.com/dev"

# Test 1: Valid contract
curl -X POST ${API_URL}/analyze \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/valid_contract.json

# Test 2: Invalid contract
curl -X POST ${API_URL}/analyze \
  -H "Content-Type: application/json" \
  -d '{"contract_code": "invalid solidity"}'

# Test 3: Large contract (performance)
time curl -X POST ${API_URL}/analyze \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/large_contract.json
```

---

## 🚀 Advanced Features

### Enable Provisioned Concurrency

Keep Lambda warm to avoid cold starts:

```bash
aws lambda put-provisioned-concurrency-config \
  --function-name dev-contract-analyzer \
  --provisioned-concurrent-executions 2 \
  --qualifier $LATEST
```

**Cost**: ~$0.015 per hour per provisioned instance

### Lambda Layers for Shared Dependencies

Create a layer for OpenAI/Gemini libraries:

```bash
# Create layer directory
mkdir -p layers/ai-libs/python

# Install dependencies into layer
pip install openai google-generativeai -t layers/ai-libs/python/

# Create layer
cd layers/ai-libs
zip -r ai-libs-layer.zip python/

# Upload layer
aws lambda publish-layer-version \
  --layer-name ai-libs \
  --zip-file fileb://ai-libs-layer.zip \
  --compatible-runtimes python3.11
```

**Benefits:**
- Reduce deployment package size
- Share libraries across multiple functions
- Faster deployments

### API Gateway Custom Domain

Map API to your domain:

```bash
# 1. Create certificate in ACM
aws acm request-certificate \
  --domain-name api.yourdomain.com \
  --validation-method DNS

# 2. Create custom domain
aws apigateway create-domain-name \
  --domain-name api.yourdomain.com \
  --certificate-arn arn:aws:acm:us-east-1:123:certificate/abc

# 3. Create base path mapping
aws apigateway create-base-path-mapping \
  --domain-name api.yourdomain.com \
  --rest-api-id abc123 \
  --stage dev
```

---

## 🛠️ Troubleshooting

### Issue: Cold Start Latency

**Problem**: First request takes 5-10 seconds

**Solutions:**
1. Enable provisioned concurrency (costs $)
2. Increase memory (more CPU = faster init)
3. Minimize dependencies in `requirements.txt`
4. Use Lambda SnapStart (for Java/Python 3.9+)

### Issue: Lambda Timeout

**Problem**: Function times out after 300 seconds

**Solutions:**
1. Optimize AI prompt (shorter = faster response)
2. Switch to faster model (gpt-3.5-turbo vs gpt-4)
3. Implement async processing with SQS
4. Increase timeout (max 900 seconds)

### Issue: High Costs

**Problem**: Bill is higher than expected

**Debug:**
```bash
# Check invocation count
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=dev-contract-analyzer \
  --start-time $(date -u -d '7 days ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 86400 \
  --statistics Sum

# Check duration
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=dev-contract-analyzer \
  --start-time $(date -u -d '7 days ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 86400 \
  --statistics Average
```

**Solutions:**
1. Implement caching (DynamoDB/Redis)
2. Use cheaper AI model
3. Add rate limiting
4. Optimize memory allocation

### Issue: API Gateway 502/504 Errors

**Problem**: Gateway returns 5xx errors

**Debug:**
```bash
# Check Lambda errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/dev-contract-analyzer \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000

# Check Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=dev-contract-analyzer \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Sum
```

**Common causes:**
1. Lambda timeout (check CloudWatch logs)
2. Out of memory (increase MemorySize)
3. Unhandled exceptions (add try-catch)
4. OpenAI API key invalid

---

## 🧹 Cleanup

### Delete the stack

```bash
# This deletes ALL resources created by SAM
sam delete

# Confirm deletion
# Are you sure you want to delete the stack? [y/N]: y
# Are you sure you want to delete the folder in S3? [y/N]: y

# Verify deletion
aws cloudformation list-stacks \
  --stack-status-filter DELETE_COMPLETE
```

**What gets deleted:**
- Lambda function
- API Gateway
- CloudWatch Log Groups
- IAM roles
- S3 bucket (if created)
- CloudWatch Alarms

**Manual cleanup (if needed):**
```bash
# Delete CloudWatch Logs (if not auto-deleted)
aws logs delete-log-group --log-group-name /aws/lambda/dev-contract-analyzer

# Delete S3 bucket (if not empty)
aws s3 rm s3://dev-smart-contracts-123456 --recursive
aws s3 rb s3://dev-smart-contracts-123456
```

---

## 📚 Next Steps (Phase 7 Completion)

✅ **Completed:**
- ✅ Converted Contract Analysis to Lambda
- ✅ Created API Gateway endpoint
- ✅ Implemented event-driven architecture
- ✅ Set up monitoring and alarms
- ✅ Cost optimization with Gemini fallback

🎯 **Additional Phase 7 Tasks:**

1. **Add More Serverless Functions:**
   - Contract Rewrite Lambda
   - Contract Generation Lambda
   - Notification Lambda (email/Slack)

2. **Event-Driven Enhancements:**
   - SQS queue for async processing
   - SNS topics for fan-out notifications
   - EventBridge rules for scheduled analysis

3. **API Gateway Features:**
   - JWT authorizer for user authentication
   - Usage plans and API keys
   - Request/response transformation
   - Caching for frequently analyzed contracts

4. **Performance Optimization:**
   - Implement DynamoDB for caching results
   - Lambda@Edge for global distribution
   - CloudFront distribution for API

5. **Testing & CI/CD:**
   - Add to GitHub Actions pipeline
   - Canary deployments
   - Blue/green deployments
   - Load testing with Artillery

---

## 📖 Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/)
- [API Gateway Best Practices](https://docs.aws.amazon.com/apigateway/latest/developerguide/best-practices.html)
- [Lambda Performance Optimization](https://aws.amazon.com/blogs/compute/operating-lambda-performance-optimization-part-1/)
- [Serverless Patterns](https://serverlessland.com/patterns)

---

## 💡 Key Takeaways

**Serverless Benefits:**
- ✅ Zero server management
- ✅ Automatic scaling
- ✅ Pay-per-use pricing
- ✅ Built-in high availability
- ✅ Faster time to market

**When to Use Serverless:**
- Variable/unpredictable workloads
- Event-driven applications
- Microservices architectures
- Rapid prototyping
- Cost-sensitive projects

**When NOT to Use Serverless:**
- Long-running processes (>15 minutes)
- Consistent high-volume traffic (EC2 might be cheaper)
- Complex state management
- Large dependencies (>250MB unzipped)
- Specialized hardware requirements

---

**Congratulations! You've completed Phase 7: Serverless & Cloud-Native Services** 🎉

You now have a production-ready, cost-optimized, auto-scaling serverless application with monitoring, security, and best practices baked in.

---

*Need help? Check the troubleshooting section or open an issue on GitHub.*
