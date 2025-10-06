<#
.SYNOPSIS
    Quick redeploy of Teams Bot code with Managed Identity fix
    
.DESCRIPTION
    Deploys ONLY the code without changing infrastructure
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$AppName = "teamsbot-mihai-mi",
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "teams-chatbots"
)

$ErrorActionPreference = "Stop"

Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          Quick Redeploy - Teams Bot with MI Fix                   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = $PSScriptRoot

Write-Host "📦 Preparing deployment package..." -ForegroundColor Yellow
Write-Host "   Script directory: $ScriptDir" -ForegroundColor Gray

# Create temp directory for deployment
$TempDir = Join-Path $env:TEMP "teams_bot_deploy_$(Get-Date -Format 'yyyyMMddHHmmss')"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
Write-Host "   Temp directory: $TempDir" -ForegroundColor Gray

# Copy required files
$FilesToCopy = @(
    "app.py",
    "bot.py",
    "backend_client.py",
    "requirements.txt"
)

Write-Host ""
Write-Host "📋 Copying files..." -ForegroundColor Yellow
foreach ($file in $FilesToCopy) {
    $source = Join-Path $ScriptDir $file
    if (Test-Path $source) {
        Copy-Item $source -Destination $TempDir
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  $file not found" -ForegroundColor Yellow
    }
}

# Create zip file
$ZipPath = Join-Path $env:TEMP "teams_bot_$(Get-Date -Format 'yyyyMMddHHmmss').zip"
Write-Host ""
Write-Host "📦 Creating deployment package..." -ForegroundColor Yellow

# Use .NET compression (more reliable than Compress-Archive for large files)
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($TempDir, $ZipPath)

Write-Host "   ✅ Package created: $ZipPath" -ForegroundColor Green
$ZipSize = (Get-Item $ZipPath).Length / 1KB
Write-Host "   Size: $([math]::Round($ZipSize, 2)) KB" -ForegroundColor Gray

# Deploy to Azure
Write-Host ""
Write-Host "🚀 Deploying to Azure..." -ForegroundColor Yellow
Write-Host "   App: $AppName" -ForegroundColor Gray
Write-Host "   Resource Group: $ResourceGroup" -ForegroundColor Gray

try {
    az webapp deployment source config-zip `
        --resource-group $ResourceGroup `
        --name $AppName `
        --src $ZipPath `
        --timeout 600
    
    Write-Host ""
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "❌ Deployment failed: $_" -ForegroundColor Red
    exit 1
}

# Cleanup
Write-Host ""
Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
Remove-Item $TempDir -Recurse -Force
Remove-Item $ZipPath -Force
Write-Host "   ✅ Cleanup done" -ForegroundColor Green

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    ✅ Deployment Complete!                         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Wait 30-60 seconds for the app to restart" -ForegroundColor White
Write-Host "2. Check logs:" -ForegroundColor White
Write-Host "   az webapp log tail --name $AppName --resource-group $ResourceGroup" -ForegroundColor Gray
Write-Host "3. Look for this line in logs:" -ForegroundColor White
Write-Host "   '🔐 Using UserAssignedMSI - password set to None'" -ForegroundColor Gray
Write-Host "4. Test in Teams - errors should be gone!" -ForegroundColor White
Write-Host ""
