# AWS EC2 + Vercel Hybrid Deployment Guide

## Architecture Overview

This setup uses a **hybrid deployment strategy**:
- **Backend Microservices**: AWS EC2 (cost-effective, full control)
- **Frontend**: Vercel (global CDN, excellent performance)

## Prerequisites Setup

### 1. AWS Account Setup
- Ensure you have an AWS account
- Create an IAM user with EC2 full access
- Generate Access Key ID and Secret Access Key

### 2. GitHub Secrets Configuration

Add these secrets to your GitHub repository:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1

# Application Secrets
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_jwt_secret_key_here

# Database (will be created automatically)
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/smart_contract_db
```

### 3. EC2 Instance Creation

Run the AWS deployment manager to create your EC2 instance:

```bash
# Install AWS dependencies
pip install -r scripts/aws-requirements.txt

# Create EC2 instance and setup
python scripts/aws-ec2-deployment-manager.py --create-instance --instance-type t3.micro

# Deploy microservices
python scripts/aws-ec2-deployment-manager.py --deploy --deployment-strategy unified
```

### 4. Vercel Frontend Deployment

After AWS EC2 backend is running:

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy frontend
cd frontend
vercel --prod

# Set environment variables in Vercel dashboard:
# VITE_API_URL=http://your-ec2-ip:8000
```

### 5. Configure API Proxy

Update `vercel.json` with your EC2 IP:
```json
{
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "http://your-ec2-ip:8000/api/$1"
    }
  ],
  "env": {
    "VITE_API_URL": "http://your-ec2-ip:8000"
  }
}
```

After running the deployment script, you'll get:
- EC2_HOST: The public IP of your EC2 instance
- EC2_PRIVATE_KEY: The SSH private key (save the .pem file content)

Add these to GitHub secrets:
```bash
EC2_HOST=your_ec2_public_ip
EC2_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----
your_private_key_content_here
-----END RSA PRIVATE KEY-----
```

## Deployment Architecture

### Hybrid Infrastructure:
1. **AWS EC2 Backend** (Microservices)
   - Unified Main API (Port 8000)
   - Contract Service (Port 8001) 
   - PostgreSQL Database (Port 5432)

2. **Vercel Frontend**
   - Global CDN distribution
   - Automatic HTTPS
   - API proxy to AWS EC2 backend

### Service URLs:
- Frontend: https://your-vercel-app.vercel.app
- Main API: http://your-ec2-ip:8000
- API Docs: http://your-ec2-ip:8000/docs
- Contract Service: http://your-ec2-ip:8001

## Testing Deployment

### Local Testing:
```bash
# Test unified main service
curl http://your-ec2-ip:8000/health

# Test authentication
curl -X POST http://your-ec2-ip:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password","full_name":"Test User"}'

# Test contract service
curl http://your-ec2-ip:8001/health
```

### CI/CD Pipeline:
The pipeline will automatically:
1. Test microservices locally
2. Deploy to EC2 on main branch pushes
3. Run health checks
4. Rollback on failure

## Cost Optimization

### Free Tier Usage:
- t3.micro instance (750 hours/month free)
- Up to 30GB EBS storage (free)
- 1GB data transfer (free)

### Monitoring:
- CloudWatch basic monitoring (free)
- Application logs via Docker

## Security

### Network Security:
- Security groups allowing only necessary ports
- SSH key-based authentication
- Private database access

### Application Security:
- JWT authentication
- Environment variable secrets
- HTTPS ready (add SSL certificate)

## Troubleshooting

### Common Issues:
1. **Deployment fails**: Check AWS credentials and permissions
2. **Services won't start**: Check Docker installation and permissions
3. **Health checks fail**: Verify ports are open in security groups
4. **Database connection fails**: Check PostgreSQL container status

### Debug Commands:
```bash
# SSH to EC2
ssh -i your-key.pem ec2-user@your-ec2-ip

# Check service status
cd ~/smart-contract-rewriter/microservices
docker-compose ps
docker-compose logs

# Check system resources
htop
df -h
```

## Next Steps

1. **Custom Domain**: Add Route 53 domain and SSL certificate
2. **Load Balancer**: Add Application Load Balancer for high availability
3. **Monitoring**: Set up CloudWatch dashboards and alerts
4. **Backup**: Configure RDS for production database
5. **Scaling**: Auto Scaling Groups for multiple instances

This setup provides a cost-effective, scalable foundation for your smart contract analysis platform.
