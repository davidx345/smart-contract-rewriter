# 🚀 Hybrid Deployment Guide: AWS EC2 + Vercel

## Architecture Benefits

### Why This Hybrid Approach?
- **Vercel Frontend**: Global CDN, automatic HTTPS, excellent performance
- **AWS EC2 Backend**: Cost-effective microservices, full control, database access
- **Best of Both Worlds**: Frontend speed + Backend flexibility

## Deployment Steps

### 1. Deploy Backend to AWS EC2

```bash
# Quick setup
python scripts/aws-quick-setup.py

# Or manual
python scripts/aws-ec2-deployment-manager.py --create-instance --instance-type t3.micro
python scripts/aws-ec2-deployment-manager.py --deploy --deployment-strategy unified
```

### 2. Configure Frontend for Hybrid

Update your frontend API configuration:

**frontend/.env.production**:
```bash
VITE_API_URL=http://your-ec2-ip:8000
```

**frontend/src/services/api.ts**:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  baseURL: API_BASE_URL,
  // ... rest of your API configuration
};
```

### 3. Deploy Frontend to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy from project root
vercel --prod

# Follow prompts:
# ? Set up and deploy "smart-contract-rewriter"? [Y/n] y
# ? Which scope? [Your account]
# ? Link to existing project? [N/y] n
# ? What's your project's name? smart-contract-rewriter
# ? In which directory is your code located? ./frontend
```

### 4. Configure Vercel Environment Variables

In Vercel Dashboard (vercel.com):
1. Go to your project
2. Settings > Environment Variables
3. Add:
   ```
   VITE_API_URL = http://your-ec2-ip:8000
   ```

### 5. Update API Proxy (Optional)

For cleaner API calls, update `vercel.json`:

```json
{
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "http://your-ec2-ip:8000/api/$1",
      "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
      }
    },
    {
      "src": "/(.*)",
      "dest": "frontend/dist/$1"
    }
  ]
}
```

## Testing Your Hybrid Setup

### Backend Health Check:
```bash
curl http://your-ec2-ip:8000/health
```

### Frontend Access:
```bash
curl https://your-app.vercel.app
```

### API Integration Test:
```bash
# Test authentication through Vercel proxy
curl -X POST https://your-app.vercel.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password","full_name":"Test User"}'
```

## Production Considerations

### Security:
1. **HTTPS for Backend**: Consider adding SSL certificate to EC2
2. **CORS Configuration**: Properly configure CORS in FastAPI
3. **API Keys**: Use environment variables for sensitive data

### Performance:
1. **CDN**: Vercel provides global CDN for frontend
2. **Caching**: Implement API response caching
3. **Database**: Consider RDS for production database

### Monitoring:
1. **Vercel Analytics**: Built-in performance monitoring
2. **AWS CloudWatch**: EC2 and application monitoring
3. **Uptime Monitoring**: Third-party service for both endpoints

## Cost Optimization

### Vercel:
- **Hobby Plan**: Free for personal projects
- **Pro Plan**: $20/month for commercial use
- **Global CDN**: Included in all plans

### AWS EC2:
- **t3.micro**: 750 hours/month free (first year)
- **Storage**: 30GB EBS free tier
- **Data Transfer**: 1GB/month free

### Total Monthly Cost (After Free Tier):
- Vercel Hobby: $0
- AWS t3.micro: ~$8-10/month
- **Total**: ~$8-10/month vs $50+ for equivalent Heroku setup

## Troubleshooting

### Common Issues:

1. **CORS Errors**:
   ```python
   # In your FastAPI app
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-app.vercel.app"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **API Connection Fails**:
   - Check EC2 security groups allow port 8000
   - Verify VITE_API_URL in Vercel environment variables
   - Test direct EC2 API access

3. **Build Failures**:
   - Check Node.js version compatibility
   - Verify package.json scripts
   - Check Vercel build logs

### Debug Commands:

```bash
# Check Vercel deployment logs
vercel logs

# Test EC2 backend
ssh -i your-key.pem ec2-user@your-ec2-ip
docker-compose logs

# Check network connectivity
curl -I http://your-ec2-ip:8000/health
```

## CI/CD Integration

### GitHub Actions for Hybrid Deployment:

```yaml
# .github/workflows/hybrid-deploy.yml
name: Hybrid Deployment

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      # ... AWS EC2 deployment steps

  deploy-frontend:
    runs-on: ubuntu-latest
    needs: deploy-backend
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          working-directory: ./frontend
```

This hybrid approach gives you the **performance of Vercel's global CDN** for your frontend while maintaining **cost-effective, flexible backend infrastructure** on AWS EC2!
