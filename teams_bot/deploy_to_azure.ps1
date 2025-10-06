#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy Teams Bot to Azure App Service with Managed Identity

.DESCRIPTION
    This script deploys the Teams Bot application to Azure App Service.
    It handles:
    - Creating zip package
    - Deploying to Azure App Service
    - Configuring Managed Identity settings
    - Restarting the application

.PARAMETER ResourceGroup
    Azure Resource Group name (default: teams-chatbots)

.PARAMETER AppName
    Azure App Service name (default: teamsbot-mihai-mi)

.PARAMETER ConfigureIdentity
    Configure Managed Identity settings (default: false)

.EXAMPLE
    .\deploy_to_azure.ps1
    Deploy with default settings

.EXAMPLE
    .\deploy_to_azure.ps1 -ResourceGroup "my-rg" -AppName "my-bot"
    Deploy to custom resource group and app

.EXAMPLE
    .\deploy_to_azure.ps1 -ConfigureIdentity
    Deploy and configure Managed Identity
#>

param(
    [string]$ResourceGroup = "teams-chatbots",
    [string]$AppName = "teamsbot-mihai-mi",
    [switch]$ConfigureIdentity = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Teams Bot - Azure Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clean up old deployment artifacts
Write-Host "🧹 Cleaning up old artifacts..." -ForegroundColor Yellow
if (Test-Path "deploy.zip") {
    Remove-Item "deploy.zip" -Force
    Write-Host "   ✓ Removed old deploy.zip" -ForegroundColor Green
}

# Step 2: Create deployment package
Write-Host ""
Write-Host "📦 Creating deployment package..." -ForegroundColor Yellow

# Directories to completely skip (never recurse into these)
$skipDirs = @("venv", "__pycache__", ".git", "app_logs", "app_logs_latest", "app_logs_new", "temp_deploy")

# File patterns to exclude
$excludeFiles = @("*.ps1", "*.md", "*.zip", "*.log", "*.pyc", "test_*.py", ".gitignore", ".env")

# Files to explicitly include (whitelist approach - safer!)
$includeFiles = @(
    "app.py",
    "bot.py", 
    "backend_client.py",
    "managed_identity_credentials.py",
    "managed_identity_adapter.py",
    "requirements.txt",
    ".env",
    "Dockerfile"
)

# Create temporary directory for deployment
$tempDir = ".\temp_deploy"
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

Write-Host "   Copying core files..." -ForegroundColor Gray

# Copy specific files only (whitelist approach)
foreach ($file in $includeFiles) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $tempDir -Force
        Write-Host "   ✓ $file" -ForegroundColor DarkGray
    }
}

# Copy manifest directory if it exists
if (Test-Path "manifest") {
    Copy-Item -Path "manifest" -Destination "$tempDir\manifest" -Recurse -Force
    Write-Host "   ✓ manifest/" -ForegroundColor DarkGray
}

# Create zip from temp directory (much smaller, safer)
Write-Host "   Creating archive..." -ForegroundColor Gray
Compress-Archive -Path "$tempDir\*" -DestinationPath "deploy.zip" -Force

# Clean up temp directory immediately
Remove-Item -Path $tempDir -Recurse -Force

# Force garbage collection to free memory
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()

$zipSize = (Get-Item "deploy.zip").Length / 1KB
Write-Host "   ✓ Created deploy.zip ($([math]::Round($zipSize, 2)) KB)" -ForegroundColor Green

# Step 3: Deploy to Azure
Write-Host ""
Write-Host "🚀 Deploying to Azure App Service..." -ForegroundColor Yellow
Write-Host "   Resource Group: $ResourceGroup" -ForegroundColor Gray
Write-Host "   App Name: $AppName" -ForegroundColor Gray
Write-Host ""

try {
    $deployResult = az webapp deploy `
        --resource-group $ResourceGroup `
        --name $AppName `
        --src-path "deploy.zip" `
        --type zip `
        --async true 2>&1 | Out-String

    if ($LASTEXITCODE -ne 0) {
        throw "Deployment failed: $deployResult"
    }

    Write-Host "   ✓ Deployment initiated successfully" -ForegroundColor Green
    
    # Wait for deployment to complete
    Write-Host ""
    Write-Host "⏳ Waiting for deployment to complete..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    # Check deployment status
    Write-Host "   Checking deployment status..." -ForegroundColor Gray
    $status = az webapp show --resource-group $ResourceGroup --name $AppName --query "state" -o tsv
    
    if ($status -eq "Running") {
        Write-Host "   ✓ Application is running" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ Application status: $status" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   ✗ Deployment failed: $_" -ForegroundColor Red
    exit 1
}

# Step 4: Configure Managed Identity (optional)
if ($ConfigureIdentity) {
    Write-Host ""
    Write-Host "🔐 Configuring Managed Identity..." -ForegroundColor Yellow
    
    try {
        # Get Managed Identity
        $identityName = "mi-$AppName"
        Write-Host "   Looking for Managed Identity: $identityName" -ForegroundColor Gray
        
        $identity = az identity show `
            --resource-group $ResourceGroup `
            --name $identityName `
            --query "{clientId: clientId, id: id}" `
            -o json 2>&1 | ConvertFrom-Json
        
        if ($identity.clientId) {
            Write-Host "   ✓ Found Managed Identity" -ForegroundColor Green
            Write-Host "     Client ID: $($identity.clientId)" -ForegroundColor Gray
            
            # Assign identity to App Service
            Write-Host "   Assigning identity to App Service..." -ForegroundColor Gray
            az webapp identity assign `
                --resource-group $ResourceGroup `
                --name $AppName `
                --identities $identity.id | Out-Null
            
            Write-Host "   ✓ Identity assigned" -ForegroundColor Green
            
            # Configure app settings
            Write-Host "   Configuring app settings..." -ForegroundColor Gray
            az webapp config appsettings set `
                --resource-group $ResourceGroup `
                --name $AppName `
                --settings `
                    MICROSOFT_APP_ID=$($identity.clientId) `
                    MICROSOFT_APP_TYPE="UserAssignedMSI" `
                | Out-Null
            
            Write-Host "   ✓ App settings configured" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠ Managed Identity not found: $identityName" -ForegroundColor Yellow
            Write-Host "   Please create it manually or check the name" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "   ⚠ Could not configure Managed Identity: $_" -ForegroundColor Yellow
    }
}

# Step 5: Show deployment info
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 App URL: https://$AppName.azurewebsites.net" -ForegroundColor Cyan
Write-Host "💚 Health: https://$AppName.azurewebsites.net/health" -ForegroundColor Cyan
Write-Host "📊 Portal: https://portal.azure.com/#resource/subscriptions/.../resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$AppName" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 To view logs:" -ForegroundColor Yellow
Write-Host "   az webapp log tail --resource-group $ResourceGroup --name $AppName" -ForegroundColor Gray
Write-Host ""
Write-Host "🔄 To restart:" -ForegroundColor Yellow
Write-Host "   az webapp restart --resource-group $ResourceGroup --name $AppName" -ForegroundColor Gray
Write-Host ""

# Clean up deployment package
Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
if (Test-Path "deploy.zip") {
    Remove-Item "deploy.zip" -Force -ErrorAction SilentlyContinue
    Write-Host "   ✓ Removed deploy.zip" -ForegroundColor Green
}
if (Test-Path "temp_deploy") {
    Remove-Item "temp_deploy" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   ✓ Removed temp directory" -ForegroundColor Green
}

# Final garbage collection
[System.GC]::Collect()

Write-Host ""
Write-Host "✨ Done!" -ForegroundColor Green
