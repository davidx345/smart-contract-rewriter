#!/usr/bin/env powershell

<#
.SYNOPSIS
    Terraform Infrastructure Deployment Script for Smart Contract Rewriter
    
.DESCRIPTION
    This script automates the deployment of infrastructure using Terraform.
    It includes validation, security scanning, cost estimation, and deployment.
    
.PARAMETER Environment
    Target environment (dev, staging, prod)
    
.PARAMETER Action
    Action to perform (plan, apply, destroy, validate, security-scan)
    
.PARAMETER AutoApprove
    Skip interactive approval for apply/destroy
    
.PARAMETER Workspace
    Terraform workspace to use
    
.EXAMPLE
    .\deploy-infrastructure.ps1 -Environment dev -Action plan
    .\deploy-infrastructure.ps1 -Environment prod -Action apply -AutoApprove
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment,
    
    [Parameter(Mandatory=$true)]
    [ValidateSet("plan", "apply", "destroy", "validate", "security-scan", "cost-estimate")]
    [string]$Action,
    
    [switch]$AutoApprove,
    
    [string]$Workspace = $null
)

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TerraformDir = Join-Path $ScriptDir ".."
$EnvironmentDir = Join-Path $TerraformDir "environments\$Environment"
$VarFile = Join-Path $EnvironmentDir "terraform.tfvars"

# Colors for output
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Blue = "Blue"

function Write-StatusMessage {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Test-Prerequisites {
    Write-StatusMessage "🔍 Checking prerequisites..." $Blue
    
    # Check if Terraform is installed
    try {
        $terraformVersion = terraform version
        Write-StatusMessage "✅ Terraform found: $($terraformVersion[0])" $Green
    }
    catch {
        Write-StatusMessage "❌ Terraform not found. Please install Terraform." $Red
        exit 1
    }
    
    # Check if AWS CLI is configured
    try {
        $awsIdentity = aws sts get-caller-identity 2>$null
        if ($awsIdentity) {
            $identity = $awsIdentity | ConvertFrom-Json
            Write-StatusMessage "✅ AWS CLI configured - Account: $($identity.Account)" $Green
        }
        else {
            Write-StatusMessage "❌ AWS CLI not configured. Please run 'aws configure'." $Red
            exit 1
        }
    }
    catch {
        Write-StatusMessage "❌ AWS CLI not found or not configured." $Red
        exit 1
    }
    
    # Check if environment configuration exists
    if (!(Test-Path $VarFile)) {
        Write-StatusMessage "❌ Environment configuration not found: $VarFile" $Red
        exit 1
    }
    
    Write-StatusMessage "✅ All prerequisites met" $Green
}

function Initialize-Terraform {
    Write-StatusMessage "🚀 Initializing Terraform..." $Blue
    
    Set-Location $TerraformDir
    
    # Initialize Terraform
    terraform init -reconfigure
    
    if ($LASTEXITCODE -ne 0) {
        Write-StatusMessage "❌ Terraform initialization failed" $Red
        exit 1
    }
    
    # Select or create workspace
    if ($Workspace) {
        terraform workspace select $Workspace 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-StatusMessage "📝 Creating new workspace: $Workspace" $Yellow
            terraform workspace new $Workspace
        }
        Write-StatusMessage "✅ Using workspace: $Workspace" $Green
    }
    else {
        $currentWorkspace = terraform workspace show
        Write-StatusMessage "✅ Using workspace: $currentWorkspace" $Green
    }
}

function Invoke-SecurityScan {
    Write-StatusMessage "🔒 Running security scan..." $Blue
    
    # Check if tfsec is available
    try {
        tfsec --version | Out-Null
        Write-StatusMessage "🔍 Running tfsec security scan..." $Blue
        tfsec . --format json --out security-report.json
        tfsec . --format table
        
        if ($LASTEXITCODE -ne 0) {
            Write-StatusMessage "⚠️  Security scan found issues. Check the report." $Yellow
        }
        else {
            Write-StatusMessage "✅ Security scan passed" $Green
        }
    }
    catch {
        Write-StatusMessage "⚠️  tfsec not found. Install with: go install github.com/aquasecurity/tfsec/cmd/tfsec@latest" $Yellow
    }
    
    # Check if checkov is available
    try {
        checkov --version | Out-Null
        Write-StatusMessage "🔍 Running Checkov security scan..." $Blue
        checkov -d . --framework terraform --output json --output-file checkov-report.json
        checkov -d . --framework terraform
        
        if ($LASTEXITCODE -ne 0) {
            Write-StatusMessage "⚠️  Checkov found issues. Check the report." $Yellow
        }
        else {
            Write-StatusMessage "✅ Checkov scan passed" $Green
        }
    }
    catch {
        Write-StatusMessage "⚠️  Checkov not found. Install with: pip install checkov" $Yellow
    }
}

function Invoke-CostEstimate {
    Write-StatusMessage "💰 Estimating costs..." $Blue
    
    # Try to use Infracost if available
    try {
        infracost --version | Out-Null
        Write-StatusMessage "💵 Running Infracost analysis..." $Blue
        
        # Generate cost estimate
        infracost breakdown --path . --format json --out cost-estimate.json
        infracost breakdown --path . --format table
        
        Write-StatusMessage "✅ Cost estimate generated" $Green
    }
    catch {
        Write-StatusMessage "⚠️  Infracost not found. Install from: https://www.infracost.io/docs/" $Yellow
        Write-StatusMessage "💡 Manual cost estimation: Review instance types and quantities in tfvars" $Blue
    }
}

function Invoke-TerraformValidate {
    Write-StatusMessage "✅ Validating Terraform configuration..." $Blue
    
    terraform validate
    
    if ($LASTEXITCODE -ne 0) {
        Write-StatusMessage "❌ Terraform validation failed" $Red
        exit 1
    }
    
    terraform fmt -check -recursive
    
    if ($LASTEXITCODE -ne 0) {
        Write-StatusMessage "⚠️  Terraform formatting issues found. Run 'terraform fmt -recursive' to fix." $Yellow
    }
    
    Write-StatusMessage "✅ Terraform configuration is valid" $Green
}

function Invoke-TerraformPlan {
    Write-StatusMessage "📋 Creating Terraform plan..." $Blue
    
    $planFile = "terraform-$Environment.tfplan"
    
    terraform plan -var-file="$VarFile" -out="$planFile" -detailed-exitcode
    
    $exitCode = $LASTEXITCODE
    
    switch ($exitCode) {
        0 { 
            Write-StatusMessage "✅ No changes needed" $Green 
            return $false
        }
        1 { 
            Write-StatusMessage "❌ Terraform plan failed" $Red
            exit 1
        }
        2 { 
            Write-StatusMessage "📝 Changes planned successfully" $Green
            return $true
        }
    }
}

function Invoke-TerraformApply {
    Write-StatusMessage "🚀 Applying Terraform configuration..." $Blue
    
    $planFile = "terraform-$Environment.tfplan"
    
    if (!(Test-Path $planFile)) {
        Write-StatusMessage "❌ Plan file not found. Run plan first." $Red
        exit 1
    }
    
    if (!$AutoApprove) {
        $confirmation = Read-Host "Are you sure you want to apply these changes to $Environment? (yes/no)"
        if ($confirmation -ne "yes") {
            Write-StatusMessage "❌ Deployment cancelled by user" $Yellow
            exit 0
        }
    }
    
    terraform apply "$planFile"
    
    if ($LASTEXITCODE -ne 0) {
        Write-StatusMessage "❌ Terraform apply failed" $Red
        exit 1
    }
    
    Write-StatusMessage "✅ Infrastructure deployed successfully" $Green
    
    # Show outputs
    Write-StatusMessage "📊 Deployment outputs:" $Blue
    terraform output
}

function Invoke-TerraformDestroy {
    Write-StatusMessage "💥 Planning infrastructure destruction..." $Red
    
    if (!$AutoApprove) {
        $confirmation = Read-Host "⚠️  WARNING: This will DESTROY all infrastructure in $Environment. Type 'DELETE' to confirm"
        if ($confirmation -ne "DELETE") {
            Write-StatusMessage "❌ Destruction cancelled by user" $Yellow
            exit 0
        }
    }
    
    terraform destroy -var-file="$VarFile" -auto-approve
    
    if ($LASTEXITCODE -ne 0) {
        Write-StatusMessage "❌ Terraform destroy failed" $Red
        exit 1
    }
    
    Write-StatusMessage "✅ Infrastructure destroyed successfully" $Green
}

# Main execution
try {
    Write-StatusMessage "🏗️  Smart Contract Rewriter - Infrastructure Deployment" $Blue
    Write-StatusMessage "Environment: $Environment | Action: $Action" $Blue
    
    Test-Prerequisites
    Initialize-Terraform
    
    switch ($Action) {
        "validate" {
            Invoke-TerraformValidate
        }
        "security-scan" {
            Invoke-SecurityScan
        }
        "cost-estimate" {
            Invoke-CostEstimate
        }
        "plan" {
            Invoke-TerraformValidate
            Invoke-SecurityScan
            $hasChanges = Invoke-TerraformPlan
            if ($hasChanges) {
                Invoke-CostEstimate
            }
        }
        "apply" {
            Invoke-TerraformValidate
            Invoke-SecurityScan
            $hasChanges = Invoke-TerraformPlan
            if ($hasChanges) {
                Invoke-CostEstimate
                Invoke-TerraformApply
            }
            else {
                Write-StatusMessage "ℹ️  No changes to apply" $Blue
            }
        }
        "destroy" {
            Invoke-TerraformDestroy
        }
    }
    
    Write-StatusMessage "🎉 Operation completed successfully!" $Green
}
catch {
    Write-StatusMessage "❌ Error occurred: $($_.Exception.Message)" $Red
    exit 1
}
finally {
    Set-Location $ScriptDir
}