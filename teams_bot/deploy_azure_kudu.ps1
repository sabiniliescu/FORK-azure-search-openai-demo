#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick Azure Deployment via Kudu (Fast & Reliable)
    
.DESCRIPTION
    Uploads bot code to Azure Web App using Kudu ZipDeploy
    Much faster and more reliable than az webapp deploy
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$AppName = "teamsbot-mihai-mi",
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "teams-chatbots"
)

$ErrorActionPreference = "Stop"

# Ensure script runs from the teams_bot directory regardless of invocation location
$scriptDir = Split-Path -Parent $PSCommandPath
Set-Location $scriptDir

Write-Host "`n$("=" * 80)" -ForegroundColor Cyan
Write-Host "🚀 Azure Deployment via Kudu" -ForegroundColor Cyan
Write-Host "$("=" * 80)`n" -ForegroundColor Cyan

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   App Name: $AppName" -ForegroundColor White
Write-Host "   Resource Group: $ResourceGroup`n" -ForegroundColor White

# Step 1: Create deployment package
Write-Host "📦 Step 1: Creating deployment package..." -ForegroundColor Yellow

$tempDir = Join-Path $env:TEMP "teams_bot_deploy_$(Get-Date -Format 'yyyyMMddHHmmss')"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Copy essential files
$filesToCopy = @(
    "app.py",
    "bot.py",
    "backend_client.py",
    "requirements.txt",
    "data_models.py"
)

foreach ($file in $filesToCopy) {
    if (Test-Path $file) {
        Copy-Item $file -Destination $tempDir -Force
        Write-Host "   ✓ $file" -ForegroundColor Green
    }
}

# Create .env for Azure (with production settings)
$azureEnv = @"
# Microsoft Bot Framework (will be set via App Settings)
MICROSOFT_APP_ID=
MICROSOFT_APP_PASSWORD=

# Backend URL
BACKEND_URL=https://capps-backend-dcnxgznrq3wmc.happyground-5a8ca1ce.eastus.azurecontainerapps.io

# Port (Azure sets this automatically, but default to 8000)
PORT=8000
"@
Set-Content -Path (Join-Path $tempDir ".env") -Value $azureEnv

Write-Host "   ✓ .env (Azure config)" -ForegroundColor Green

# Create ZIP
Write-Host "`n📦 Step 2: Creating ZIP archive..." -ForegroundColor Yellow

$zipPath = Join-Path $env:TEMP "teams_bot_azure.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($tempDir, $zipPath)

$zipSize = (Get-Item $zipPath).Length / 1KB
Write-Host "✅ ZIP created: $([math]::Round($zipSize, 2)) KB`n" -ForegroundColor Green

# Step 3: Get publish credentials
Write-Host "🔐 Step 3: Getting publish credentials..." -ForegroundColor Yellow

$creds = az webapp deployment list-publishing-credentials `
    --name $AppName `
    --resource-group $ResourceGroup `
    --query "{username:publishingUserName, password:publishingPassword}" `
    --output json | ConvertFrom-Json

if (-not $creds) {
    Write-Host "❌ Failed to get credentials!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Credentials retrieved" -ForegroundColor Green

# Step 4: Upload via Kudu
Write-Host "`n🚀 Step 4: Uploading to Azure (this may take 1-2 minutes)..." -ForegroundColor Yellow

$kuduUrl = "https://$AppName.scm.azurewebsites.net/api/zipdeploy"
$base64Auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$($creds.username):$($creds.password)"))

try {
    $null = Invoke-WebRequest `
        -Uri $kuduUrl `
        -Method POST `
        -Headers @{
            Authorization = "Basic $base64Auth"
        } `
        -InFile $zipPath `
        -ContentType "application/zip" `
        -UseBasicParsing `
        -TimeoutSec 300

    Write-Host "✅ Code deployed successfully!" -ForegroundColor Green

} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    
    # Try alternative method with curl
    Write-Host "`n💡 Trying alternative method (curl)..." -ForegroundColor Yellow
    
    curl.exe -X POST $kuduUrl `
        -H "Authorization: Basic $base64Auth" `
        -H "Content-Type: application/zip" `
        --data-binary "@$zipPath" `
        --max-time 300
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Code deployed successfully (via curl)!" -ForegroundColor Green
    } else {
        Write-Host "❌ Both deployment methods failed!" -ForegroundColor Red
        Write-Host "`n💡 Manual deployment option:" -ForegroundColor Yellow
        Write-Host "   1. Open: https://$AppName.scm.azurewebsites.net/ZipDeploy" -ForegroundColor White
        Write-Host "   2. Drag & drop: $zipPath" -ForegroundColor White
        exit 1
    }
}

# Step 5: Configure App Settings
Write-Host "`n⚙️  Step 5: Configuring App Settings..." -ForegroundColor Yellow

# Get Managed Identity details
$miClientId = az identity show `
    --name "mi-$AppName" `
    --resource-group $ResourceGroup `
    --query clientId `
    --output tsv

Write-Host "   MI Client ID: $miClientId" -ForegroundColor Gray

# Configure app settings
az webapp config appsettings set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --settings `
        BACKEND_URL="https://capps-backend-dcnxgznrq3wmc.happyground-5a8ca1ce.eastus.azurecontainerapps.io" `
        MICROSOFT_APP_TYPE="UserAssignedMSI" `
        MICROSOFT_APP_ID="$miClientId" `
        MICROSOFT_APP_TENANTID="52d32ffe-bfad-4f92-b437-e29121332333" `
        PORT="8000" `
        SCM_DO_BUILD_DURING_DEPLOYMENT="true" `
    --output none

Write-Host "✅ App Settings configured" -ForegroundColor Green

# Ensure the app uses the aiohttp-compatible Gunicorn worker
Write-Host "   ↳ Setting startup command for aiohttp" -ForegroundColor Gray
az webapp config set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --startup-file 'gunicorn app:app --worker-class aiohttp.worker.GunicornWebWorker --bind=0.0.0.0:$PORT --timeout 600' `
    --output none

Write-Host "✅ Startup command configured" -ForegroundColor Green

# Step 6: Restart Web App
Write-Host "`n🔄 Step 6: Restarting Web App..." -ForegroundColor Yellow

az webapp restart --name $AppName --resource-group $ResourceGroup --output none

Write-Host "✅ Web App restarted" -ForegroundColor Green

# Step 7: Wait and test
Write-Host "`n⏳ Step 7: Waiting for app to start (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "🏥 Testing health endpoint..." -ForegroundColor Yellow
$healthUrl = "https://$AppName.azurewebsites.net/health"

try {
    $health = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ Health check passed! Status: $($health.StatusCode)" -ForegroundColor Green
    Write-Host "   Response: $($health.Content)" -ForegroundColor Gray
} catch {
    Write-Host "⚠ Health endpoint not responding yet" -ForegroundColor Yellow
    Write-Host "   This is normal - app may still be starting" -ForegroundColor Gray
}

# Cleanup
Write-Host "`n🧹 Cleaning up..." -ForegroundColor Yellow
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

# Summary
Write-Host "`n$("=" * 80)" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "$("=" * 80)" -ForegroundColor Green

Write-Host "`n📋 Web App Details:" -ForegroundColor Cyan
Write-Host "   URL: https://$AppName.azurewebsites.net" -ForegroundColor White
Write-Host "   Health: https://$AppName.azurewebsites.net/health" -ForegroundColor White
Write-Host "   Bot Endpoint: https://$AppName.azurewebsites.net/api/messages" -ForegroundColor White

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Create Bot Service:" -ForegroundColor Yellow
Write-Host "      - Go to Azure Portal → Create Resource → Azure Bot" -ForegroundColor White
Write-Host "      - Bot Name: bot-$AppName" -ForegroundColor White
Write-Host "      - App Type: User-Assigned Managed Identity" -ForegroundColor White
Write-Host "      - App ID: $miClientId" -ForegroundColor White
Write-Host "      - Endpoint: https://$AppName.azurewebsites.net/api/messages" -ForegroundColor White
Write-Host "`n   2. Enable Teams Channel in Bot Service" -ForegroundColor Yellow
Write-Host "`n   3. Test in Microsoft Teams`n" -ForegroundColor Yellow

Write-Host "💡 To check logs:" -ForegroundColor Yellow
Write-Host "   az webapp log tail --name $AppName --resource-group $ResourceGroup`n" -ForegroundColor White
