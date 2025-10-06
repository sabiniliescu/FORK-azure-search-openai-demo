#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy DOAR codul pentru Teams bot (presupune că resursele există deja)
.DESCRIPTION
    Script RAPID pentru re-deploy al codului când resursele Azure sunt deja create.
    Folosește az webapp deploy (mai rapid decât config-zip).
.PARAMETER ResourceGroupName
    Numele resource group-ului Azure
.PARAMETER AppName
    Numele Web App-ului
.EXAMPLE
    .\deploy_code_only.ps1 -ResourceGroupName "teams-chatbots" -AppName "teamsbot-mihai-mi"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$AppName
)

# Error handling
$ErrorActionPreference = "Continue"

Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "🚀 Teams Bot Code Deployment (Fast)" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   Resource Group: $ResourceGroupName" -ForegroundColor Gray
Write-Host "   App Name: $AppName" -ForegroundColor Gray
Write-Host ""

# Step 1: Create deployment package
Write-Host "📋 Step 1: Creating deployment package..." -ForegroundColor Yellow

$tempDir = Join-Path $env:TEMP "teams-bot-deploy-$(Get-Random)"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Copy necessary files
$filesToCopy = @(
    "app.py",
    "bot.py",
    "backend_client.py",
    "requirements.txt",
    "manifest"
)

Write-Host "   Copying files..." -ForegroundColor Gray
foreach ($file in $filesToCopy) {
    $sourcePath = Join-Path $PSScriptRoot $file
    if (Test-Path $sourcePath) {
        if (Test-Path $sourcePath -PathType Container) {
            Copy-Item -Path $sourcePath -Destination $tempDir -Recurse -Force
            Write-Host "     ✓ $file (folder)" -ForegroundColor DarkGray
        } else {
            Copy-Item -Path $sourcePath -Destination $tempDir -Force
            Write-Host "     ✓ $file" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "     ⚠ $file (not found, skipping)" -ForegroundColor DarkYellow
    }
}

# Create ZIP
$zipPath = Join-Path $env:TEMP "teams-bot-$(Get-Random).zip"
Write-Host "   Creating ZIP archive..." -ForegroundColor Gray
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force

$zipSize = (Get-Item $zipPath).Length / 1MB
Write-Host "   ZIP size: $($zipSize.ToString('F2')) MB" -ForegroundColor Gray
Write-Host "✅ Package created!" -ForegroundColor Green
Write-Host ""

# Step 2: Deploy to Azure
Write-Host "📋 Step 2: Deploying to Azure..." -ForegroundColor Yellow
Write-Host "   Method: az webapp deploy (fast & reliable)" -ForegroundColor Gray
Write-Host "   This may take 1-2 minutes..." -ForegroundColor Gray
Write-Host ""

# Use az webapp deploy instead of config-zip (faster, better timeout handling)
$deployOutput = az webapp deploy `
    --resource-group $ResourceGroupName `
    --name $AppName `
    --src-path $zipPath `
    --type zip `
    --async true `
    2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    Write-Host "Error: $deployOutput" -ForegroundColor Red
    
    Write-Host ""
    Write-Host "💡 Trying alternative method (config-zip with longer timeout)..." -ForegroundColor Yellow
    
    # Fallback to config-zip
    az webapp deployment source config-zip `
        --resource-group $ResourceGroupName `
        --name $AppName `
        --src $zipPath `
        --timeout 600 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Both deployment methods failed!" -ForegroundColor Red
        Write-Host ""
        Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
        Write-Host "   1. Check Web App is running: az webapp show --name $AppName --resource-group $ResourceGroupName" -ForegroundColor Gray
        Write-Host "   2. Check deployment logs: az webapp log tail --name $AppName --resource-group $ResourceGroupName" -ForegroundColor Gray
        Write-Host "   3. Try manual deploy via Azure Portal" -ForegroundColor Gray
        
        # Cleanup
        Remove-Item $tempDir -Recurse -Force
        Remove-Item $zipPath -Force
        exit 1
    }
}

Write-Host "✅ Code deployed successfully!" -ForegroundColor Green
Write-Host ""

# Cleanup temp files
Remove-Item $tempDir -Recurse -Force
Remove-Item $zipPath -Force

# Step 3: Wait for app to start
Write-Host "📋 Step 3: Waiting for app to start..." -ForegroundColor Yellow
Write-Host "   Waiting 20 seconds for app to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 20

# Get Web App URL
$webAppUrl = az webapp show `
    --name $AppName `
    --resource-group $ResourceGroupName `
    --query defaultHostName `
    -o tsv

if ([string]::IsNullOrWhiteSpace($webAppUrl)) {
    Write-Host "⚠ Could not get Web App URL" -ForegroundColor Yellow
} else {
    Write-Host "✅ Web App is running!" -ForegroundColor Green
    Write-Host "   URL: https://$webAppUrl" -ForegroundColor Gray
    Write-Host "   Health: https://$webAppUrl/health" -ForegroundColor Gray
    Write-Host "   Bot endpoint: https://$webAppUrl/api/messages" -ForegroundColor Gray
}

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Green
Write-Host "✅ Code Deployment Complete!" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test health endpoint: curl https://$webAppUrl/health" -ForegroundColor Gray
Write-Host "2. Check logs: az webapp log tail --name $AppName --resource-group $ResourceGroupName" -ForegroundColor Gray
Write-Host "3. If OK, continue with Bot Service creation (Step 8 din main script)" -ForegroundColor Gray
Write-Host ""
