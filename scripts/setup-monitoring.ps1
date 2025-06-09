# Smart Contract Rewriter - Complete Monitoring Setup Script

param(
    [switch]$Local,
    [switch]$Production,
    [string]$SlackWebhook,
    [string]$EmailConfig
)

Write-Host "📊 Setting up comprehensive monitoring for Smart Contract Rewriter..." -ForegroundColor Green

function Test-DockerCompose {
    if (!(Get-Command "docker-compose" -ErrorAction SilentlyContinue)) {
        Write-Host "❌ Docker Compose not found. Please install Docker Desktop." -ForegroundColor Red
        return $false
    }
    return $true
}

function Start-LocalMonitoring {
    Write-Host "🐳 Starting local monitoring stack..." -ForegroundColor Yellow
    
    if (!(Test-DockerCompose)) {
        exit 1
    }

    # Start monitoring services
    docker-compose up -d prometheus grafana alertmanager node-exporter

    Write-Host "✅ Local monitoring stack started!" -ForegroundColor Green
    Write-Host "🔗 Access URLs:" -ForegroundColor Cyan
    Write-Host "   Grafana:      http://localhost:3001 (admin/admin123)" -ForegroundColor White
    Write-Host "   Prometheus:   http://localhost:9090" -ForegroundColor White
    Write-Host "   Alertmanager: http://localhost:9093" -ForegroundColor White

    # Wait for services to be ready
    Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30

    # Import Grafana dashboard
    Write-Host "📈 Setting up Grafana dashboard..." -ForegroundColor Yellow
    try {
        $dashboardJson = Get-Content "monitoring/grafana/dashboards/smart-contract-dashboard.json" -Raw
        $headers = @{
            'Content-Type' = 'application/json'
            'Authorization' = 'Basic ' + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes('admin:admin123'))
        }
        Invoke-RestMethod -Uri "http://localhost:3001/api/dashboards/db" -Method Post -Headers $headers -Body $dashboardJson
        Write-Host "✅ Dashboard imported successfully!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Dashboard import failed. You can manually import it from the Grafana UI." -ForegroundColor Yellow
    }
}

function Setup-ProductionMonitoring {
    Write-Host "☁️  Setting up production monitoring..." -ForegroundColor Yellow
    
    # Check if kubectl is available
    if (!(Get-Command "kubectl" -ErrorAction SilentlyContinue)) {
        Write-Host "❌ kubectl not found. Please install kubectl for Kubernetes deployment." -ForegroundColor Red
        return
    }

    # Apply Kubernetes monitoring manifests
    Write-Host "📦 Deploying monitoring to Kubernetes..." -ForegroundColor Yellow
    
    # Create monitoring namespace
    kubectl apply -f k8s/namespace.yaml
    
    # Deploy Prometheus
    kubectl apply -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: smart-contract-rewriter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config-volume
          mountPath: /etc/prometheus
      volumes:
      - name: config-volume
        configMap:
          name: prometheus-config
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-service
  namespace: smart-contract-rewriter
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
  type: LoadBalancer
EOF

    Write-Host "✅ Production monitoring deployed!" -ForegroundColor Green
}

function Configure-Alerts {
    param([string]$SlackWebhook, [string]$EmailConfig)
    
    Write-Host "🚨 Configuring alerting..." -ForegroundColor Yellow
    
    if ($SlackWebhook) {
        Write-Host "📱 Configuring Slack notifications..." -ForegroundColor Yellow
        # Update alertmanager config with Slack webhook
        $alertConfig = Get-Content "monitoring/alertmanager/alertmanager.yml" -Raw
        $alertConfig = $alertConfig -replace "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK", $SlackWebhook
        Set-Content "monitoring/alertmanager/alertmanager.yml" -Value $alertConfig
        Write-Host "✅ Slack webhook configured!" -ForegroundColor Green
    }
    
    if ($EmailConfig) {
        Write-Host "📧 Configuring email notifications..." -ForegroundColor Yellow
        # Parse email config (format: smtp.server:port:username:password:to_email)
        $emailParts = $EmailConfig -split ":"
        if ($emailParts.Length -eq 5) {
            $alertConfig = Get-Content "monitoring/alertmanager/alertmanager.yml" -Raw
            $alertConfig = $alertConfig -replace "smtp.gmail.com:587", "$($emailParts[0]):$($emailParts[1])"
            $alertConfig = $alertConfig -replace "your-email@gmail.com", $emailParts[4]
            Set-Content "monitoring/alertmanager/alertmanager.yml" -Value $alertConfig
            Write-Host "✅ Email notifications configured!" -ForegroundColor Green
        } else {
            Write-Host "❌ Invalid email config format. Use: smtp.server:port:username:password:to_email" -ForegroundColor Red
        }
    }
}

function Show-MonitoringStatus {
    Write-Host "📊 Monitoring Status:" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    
    if ($Local) {
        # Check Docker containers
        $containers = docker ps --filter "name=prometheus|grafana|alertmanager" --format "table {{.Names}}\t{{.Status}}"
        Write-Host $containers
    }
    
    Write-Host ""
    Write-Host "📈 Key Metrics Being Monitored:" -ForegroundColor Yellow
    Write-Host "• HTTP Request Rate & Response Times" -ForegroundColor White
    Write-Host "• CPU & Memory Usage" -ForegroundColor White
    Write-Host "• Database Performance" -ForegroundColor White
    Write-Host "• Error Rates & Status Codes" -ForegroundColor White
    Write-Host "• Smart Contract Processing Metrics" -ForegroundColor White
    Write-Host "• System Health & Uptime" -ForegroundColor White
}

# Main execution
if ($Local) {
    Start-LocalMonitoring
} elseif ($Production) {
    Setup-ProductionMonitoring
} else {
    Write-Host "❓ Please specify -Local or -Production flag" -ForegroundColor Yellow
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\setup-monitoring.ps1 -Local" -ForegroundColor White
    Write-Host "  .\setup-monitoring.ps1 -Production" -ForegroundColor White
    Write-Host "  .\setup-monitoring.ps1 -Local -SlackWebhook 'https://hooks.slack.com/...'" -ForegroundColor White
    exit 1
}

if ($SlackWebhook -or $EmailConfig) {
    Configure-Alerts -SlackWebhook $SlackWebhook -EmailConfig $EmailConfig
}

Show-MonitoringStatus

Write-Host ""
Write-Host "🎉 Monitoring setup complete!" -ForegroundColor Green
Write-Host "💡 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Access Grafana dashboard to view metrics" -ForegroundColor White
Write-Host "   2. Configure additional alert rules if needed" -ForegroundColor White
Write-Host "   3. Set up notification channels (Slack/Email)" -ForegroundColor White
Write-Host "   4. Monitor your application performance!" -ForegroundColor White
