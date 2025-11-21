#!/bin/bash

###############################################################################
# AWS Lambda Deployment Script for Smart Contract Analyzer
# This script automates the deployment process for Phase 7
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="smart-contract-analyzer"
REGION="us-east-1"
ENVIRONMENT="dev"

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install it first."
        echo "Install: https://aws.amazon.com/cli/"
        exit 1
    fi
    print_success "AWS CLI installed"
    
    # Check SAM CLI
    if ! command -v sam &> /dev/null; then
        print_error "AWS SAM CLI not found. Please install it first."
        echo "Install: pip install aws-sam-cli"
        exit 1
    fi
    print_success "AWS SAM CLI installed"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
    print_success "Python 3 installed"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured."
        echo "Run: aws configure"
        exit 1
    fi
    print_success "AWS credentials configured"
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_info "AWS Account ID: $ACCOUNT_ID"
}

get_api_keys() {
    print_header "API Keys Configuration"
    
    # Check if parameters file exists
    if [ -f "parameters.json" ]; then
        print_info "Found existing parameters.json"
        read -p "Use existing API keys? [Y/n]: " use_existing
        if [[ $use_existing =~ ^[Nn]$ ]]; then
            rm parameters.json
        else
            return 0
        fi
    fi
    
    # Get OpenAI API Key
    print_info "OpenAI API Key (for GPT-4 analysis - primary service)"
    read -sp "Enter OpenAI API Key: " OPENAI_KEY
    echo ""
    
    # Get Gemini API Key
    print_info "Google Gemini API Key (fallback service - optional but recommended)"
    read -sp "Enter Gemini API Key (or press Enter to skip): " GEMINI_KEY
    echo ""
    
    if [ -z "$GEMINI_KEY" ]; then
        GEMINI_KEY="not-configured"
        print_warning "Gemini not configured - no fallback available"
    fi
    
    # Create parameters file
    cat > parameters.json << EOF
[
  {
    "ParameterKey": "OpenAIAPIKey",
    "ParameterValue": "$OPENAI_KEY"
  },
  {
    "ParameterKey": "GeminiAPIKey",
    "ParameterValue": "$GEMINI_KEY"
  },
  {
    "ParameterKey": "Environment",
    "ParameterValue": "$ENVIRONMENT"
  },
  {
    "ParameterKey": "EnableS3Trigger",
    "ParameterValue": "false"
  }
]
EOF
    
    print_success "API keys configured"
}

build_lambda() {
    print_header "Building Lambda Function"
    
    print_info "Installing dependencies and packaging code..."
    sam build
    
    if [ $? -eq 0 ]; then
        print_success "Build completed successfully"
    else
        print_error "Build failed"
        exit 1
    fi
}

test_locally() {
    print_header "Local Testing"
    
    read -p "Would you like to test locally before deploying? [y/N]: " test_local
    
    if [[ $test_local =~ ^[Yy]$ ]]; then
        print_info "Starting local API Gateway..."
        print_info "API will be available at: http://localhost:3000"
        print_info "Press Ctrl+C to stop and continue with deployment"
        
        # Start local API in background
        sam local start-api &
        LOCAL_PID=$!
        
        sleep 5
        
        # Test endpoint
        print_info "Testing local endpoint..."
        curl -X POST http://localhost:3000/analyze \
            -H "Content-Type: application/json" \
            -d '{
                "contract_code": "pragma solidity ^0.8.0; contract Test { }",
                "contract_name": "TestContract",
                "analysis_type": "security"
            }' || true
        
        echo ""
        read -p "Press Enter to stop local testing and continue..."
        
        # Stop local API
        kill $LOCAL_PID 2>/dev/null || true
        print_success "Local testing stopped"
    fi
}

deploy_to_aws() {
    print_header "Deploying to AWS"
    
    print_info "Stack Name: $STACK_NAME"
    print_info "Region: $REGION"
    print_info "Environment: $ENVIRONMENT"
    
    read -p "Proceed with deployment? [Y/n]: " proceed
    
    if [[ $proceed =~ ^[Nn]$ ]]; then
        print_warning "Deployment cancelled"
        exit 0
    fi
    
    print_info "Deploying stack..."
    sam deploy \
        --stack-name "$STACK_NAME-$ENVIRONMENT" \
        --parameter-overrides file://parameters.json \
        --capabilities CAPABILITY_IAM \
        --region $REGION \
        --no-fail-on-empty-changeset \
        --no-confirm-changeset
    
    if [ $? -eq 0 ]; then
        print_success "Deployment completed successfully!"
    else
        print_error "Deployment failed"
        exit 1
    fi
}

get_outputs() {
    print_header "Deployment Outputs"
    
    # Get stack outputs
    OUTPUTS=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME-$ENVIRONMENT" \
        --region $REGION \
        --query 'Stacks[0].Outputs' \
        --output table)
    
    echo "$OUTPUTS"
    
    # Get API endpoint specifically
    API_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME-$ENVIRONMENT" \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`AnalyzeEndpoint`].OutputValue' \
        --output text)
    
    if [ -n "$API_ENDPOINT" ]; then
        echo ""
        print_success "Your API Endpoint:"
        echo -e "${GREEN}$API_ENDPOINT${NC}"
        
        # Save to file
        echo "$API_ENDPOINT" > .api-endpoint.txt
        print_info "Endpoint saved to .api-endpoint.txt"
    fi
}

test_deployed_api() {
    print_header "Testing Deployed API"
    
    read -p "Would you like to test the deployed API? [Y/n]: " test_api
    
    if [[ ! $test_api =~ ^[Nn]$ ]]; then
        if [ -z "$API_ENDPOINT" ]; then
            API_ENDPOINT=$(cat .api-endpoint.txt 2>/dev/null)
        fi
        
        if [ -z "$API_ENDPOINT" ]; then
            print_error "Could not find API endpoint"
            return 1
        fi
        
        print_info "Testing API endpoint: $API_ENDPOINT"
        
        # Test with a simple contract
        RESPONSE=$(curl -s -X POST "$API_ENDPOINT" \
            -H "Content-Type: application/json" \
            -d '{
                "contract_code": "pragma solidity ^0.8.0;\n\ncontract SimpleStorage {\n    uint256 public value;\n    \n    function setValue(uint256 _value) public {\n        value = _value;\n    }\n}",
                "contract_name": "SimpleStorage",
                "analysis_type": "security"
            }')
        
        echo ""
        echo "Response:"
        echo "$RESPONSE" | python3 -m json.tool || echo "$RESPONSE"
        
        if echo "$RESPONSE" | grep -q "analysis_report"; then
            print_success "API test successful!"
        else
            print_warning "API test returned unexpected response"
        fi
    fi
}

show_next_steps() {
    print_header "Next Steps"
    
    cat << EOF
${GREEN}✅ Deployment Complete!${NC}

📝 What you've accomplished:
   ✅ Deployed serverless Lambda function
   ✅ Created API Gateway endpoint
   ✅ Set up CloudWatch monitoring
   ✅ Configured auto-scaling (0 → 1000 concurrent)
   ✅ Implemented cost optimization with AI fallback

📊 Monitoring:
   • CloudWatch Logs: aws logs tail /aws/lambda/$ENVIRONMENT-contract-analyzer --follow
   • CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/
   • Lambda Metrics: aws lambda get-function --function-name $ENVIRONMENT-contract-analyzer

🧪 Testing:
   • API Endpoint: $API_ENDPOINT
   • Test command: curl -X POST $API_ENDPOINT -H "Content-Type: application/json" -d @events/analyze-event.json

💰 Cost Monitoring:
   • AWS Cost Explorer: https://console.aws.amazon.com/cost-management/
   • Lambda Pricing: Free tier includes 1M requests + 400K GB-seconds per month
   • Estimated cost: ~\$1-2 for 10,000 analyses/month

🔧 Useful Commands:
   • View logs: sam logs --name ContractAnalyzerFunction --tail
   • Redeploy: ./deploy.sh (this script)
   • Delete stack: sam delete
   • Local testing: sam local start-api

📚 Documentation:
   • README.md - Complete guide
   • template.yaml - Infrastructure definition
   • handler.py - Lambda function code

🎯 Phase 7 Tasks Remaining:
   [ ] Add Contract Rewrite Lambda
   [ ] Add Contract Generation Lambda
   [ ] Implement SQS for async processing
   [ ] Add DynamoDB caching
   [ ] Set up CI/CD pipeline
   [ ] Add API Gateway authorizer
   [ ] Implement rate limiting per user

${YELLOW}⚠️  Remember to:${NC}
   • Keep API keys secure (parameters.json is in .gitignore)
   • Monitor costs in AWS Cost Explorer
   • Set up billing alarms
   • Review CloudWatch logs for errors

${GREEN}Congratulations on completing your first serverless deployment!${NC}
EOF
}

cleanup() {
    print_header "Cleanup"
    
    read -p "Would you like to delete the deployed stack? [y/N]: " delete_stack
    
    if [[ $delete_stack =~ ^[Yy]$ ]]; then
        print_warning "This will delete ALL resources created by this deployment"
        read -p "Are you sure? Type 'yes' to confirm: " confirm
        
        if [ "$confirm" = "yes" ]; then
            print_info "Deleting stack..."
            sam delete --stack-name "$STACK_NAME-$ENVIRONMENT" --region $REGION --no-prompts
            
            print_success "Stack deleted successfully"
            
            # Clean up local files
            rm -f .api-endpoint.txt
            print_info "Cleaned up local files"
        else
            print_info "Deletion cancelled"
        fi
    fi
}

###############################################################################
# Main Script
###############################################################################

main() {
    clear
    
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        Smart Contract Analyzer - Serverless Deployment       ║
║                      Phase 7: Serverless                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    
    # Parse command line arguments
    case "${1:-deploy}" in
        deploy)
            check_prerequisites
            get_api_keys
            build_lambda
            test_locally
            deploy_to_aws
            get_outputs
            test_deployed_api
            show_next_steps
            ;;
        test)
            test_deployed_api
            ;;
        logs)
            print_info "Tailing Lambda logs..."
            sam logs --name ContractAnalyzerFunction --tail
            ;;
        cleanup)
            cleanup
            ;;
        *)
            echo "Usage: $0 {deploy|test|logs|cleanup}"
            echo ""
            echo "Commands:"
            echo "  deploy  - Full deployment process"
            echo "  test    - Test deployed API"
            echo "  logs    - View Lambda logs"
            echo "  cleanup - Delete deployed resources"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
