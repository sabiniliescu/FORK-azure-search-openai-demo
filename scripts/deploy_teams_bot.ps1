#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Script for deploying the Teams Bot to Azure
.DESCRIPTION
    This script deploys the Teams Bot infrastructure and application to Azure
#>

Write-Host "Starting Teams Bot deployment..." -ForegroundColor Green

# Load environment variables
. (Join-Path $PSScriptRoot "load_azd_env.ps1")

# Check if required environment variables are set
$requiredVars = @(
    'AZURE_SUBSCRIPTION_ID',
    'AZURE_RESOURCE_GROUP',
    'MICROSOFT_APP_ID',
    'MICROSOFT_APP_PASSWORD'
)

foreach ($var in $requiredVars) {
    if (-not (Test-Path "env:$var")) {
        Write-Host "Error: Environment variable $var is not set" -ForegroundColor Red
        exit 1
    }
}

# Set default values if not provided
if (-not $env:AZURE_TEAMS_BOT_NAME) {
    $env:AZURE_TEAMS_BOT_NAME = "teams-bot-$env:AZURE_ENV_NAME"
}

if (-not $env:AZURE_TEAMS_BOT_WEBAPP_NAME) {
    $env:AZURE_TEAMS_BOT_WEBAPP_NAME = "teamsbot-$env:AZURE_ENV_NAME"
}

if (-not $env:AZURE_TEAMS_BOT_PLAN_NAME) {
    $env:AZURE_TEAMS_BOT_PLAN_NAME = "plan-teamsbot-$env:AZURE_ENV_NAME"
}

# Get backend URL (assuming it's the existing backend service)
if (-not $env:BACKEND_URL) {
    Write-Host "Warning: BACKEND_URL not set. Using default localhost" -ForegroundColor Yellow
    $env:BACKEND_URL = "http://localhost:50505"
}

Write-Host "Deploying infrastructure..." -ForegroundColor Cyan

# Deploy Bicep template
az deployment group create `
    --resource-group $env:AZURE_RESOURCE_GROUP `
    --template-file (Join-Path $PSScriptRoot "..\infra\teams-bot.bicep") `
    --parameters (Join-Path $PSScriptRoot "..\infra\teams-bot.parameters.json") `
    --parameters location=$env:AZURE_LOCATION

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Infrastructure deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "Infrastructure deployed successfully!" -ForegroundColor Green

# Get the web app name
$webAppName = $env:AZURE_TEAMS_BOT_WEBAPP_NAME

Write-Host "Deploying application code to $webAppName..." -ForegroundColor Cyan

# Navigate to teams_bot directory
$teamsBoitDir = Join-Path $PSScriptRoot "..\teams_bot"
Push-Location $teamsBotDir

# Create a zip file for deployment
$zipPath = Join-Path $env:TEMP "teams-bot-deploy.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

# Compress the teams_bot directory
Compress-Archive -Path * -DestinationPath $zipPath -Force

# Deploy to Azure Web App
Write-Host "Uploading code to Azure..." -ForegroundColor Cyan
az webapp deploy `
    --resource-group $env:AZURE_RESOURCE_GROUP `
    --name $webAppName `
    --src-path $zipPath `
    --type zip

Pop-Location

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Application deployment failed" -ForegroundColor Red
    exit 1
}

# Clean up
Remove-Item $zipPath -Force

Write-Host "`nDeployment completed successfully!" -ForegroundColor Green
Write-Host "`nBot endpoint: https://$webAppName.azurewebsites.net/api/messages" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Update the Teams app manifest with the bot endpoint"
Write-Host "2. Create the Teams app package (zip the manifest folder)"
Write-Host "3. Upload the app package to Teams"
Write-Host "`nFor more information, see teams_bot/DEPLOYMENT.md"
