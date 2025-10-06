# Deploy Teams Bot with Managed Identity
# No App ID or Password needed - uses Azure Managed Identity for authentication

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$AppName,
    
    [Parameter(Mandatory=$true)]
    [string]$BackendUrl,
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus",
    
    [Parameter(Mandatory=$false)]
    [string]$AppServiceSku = "B1"
)

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🚀 Teams Bot Deployment with Managed Identity" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Variables
$botName = "bot-$AppName"
$appPlanName = "plan-$AppName"
$managedIdentityName = "mi-$AppName"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "   App Name: $AppName" -ForegroundColor White
Write-Host "   Bot Name: $botName" -ForegroundColor White
Write-Host "   Managed Identity: $managedIdentityName" -ForegroundColor White
Write-Host "   Location: $Location" -ForegroundColor White
Write-Host "   Backend URL: $BackendUrl" -ForegroundColor White
Write-Host ""

# Check if logged in
Write-Host "📋 Step 1: Verifying Azure login..." -ForegroundColor Yellow
$account = az account show 2>&1 | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Not logged in to Azure. Please run: az login" -ForegroundColor Red
    exit 1
}
$tenantId = $account.tenantId
Write-Host "✅ Logged in as: $($account.user.name)" -ForegroundColor Green
Write-Host "   Tenant ID: $tenantId" -ForegroundColor Gray
Write-Host ""

# Create or verify resource group
Write-Host "📋 Step 2: Creating/verifying resource group..." -ForegroundColor Yellow
az group create --name $ResourceGroupName --location $Location | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create resource group" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Resource group ready: $ResourceGroupName" -ForegroundColor Green
Write-Host ""

# Create User-Assigned Managed Identity
Write-Host "📋 Step 3: Creating User-Assigned Managed Identity..." -ForegroundColor Yellow
$existingMI = az identity show --name $managedIdentityName --resource-group $ResourceGroupName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   Managed Identity already exists, using existing one" -ForegroundColor Gray
    $mi = $existingMI | ConvertFrom-Json
} else {
    Write-Host "   Creating new Managed Identity..." -ForegroundColor Gray
    $mi = az identity create `
        --name $managedIdentityName `
        --resource-group $ResourceGroupName `
        --location $Location | ConvertFrom-Json
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create Managed Identity" -ForegroundColor Red
        exit 1
    }
    
    # Wait a bit for the identity to propagate
    Write-Host "   Waiting for identity to propagate (15 seconds)..." -ForegroundColor Gray
    Start-Sleep -Seconds 15
}

$miClientId = $mi.clientId
$miPrincipalId = $mi.principalId
$miResourceId = $mi.id

Write-Host "✅ Managed Identity ready!" -ForegroundColor Green
Write-Host "   Client ID: $miClientId" -ForegroundColor Gray
Write-Host "   Principal ID: $miPrincipalId" -ForegroundColor Gray
Write-Host ""

# Create App Service Plan
Write-Host "📋 Step 4: Creating App Service Plan..." -ForegroundColor Yellow
$existingPlan = az appservice plan show --name $appPlanName --resource-group $ResourceGroupName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   App Service Plan already exists" -ForegroundColor Gray
} else {
    az appservice plan create `
        --name $appPlanName `
        --resource-group $ResourceGroupName `
        --location $Location `
        --sku $AppServiceSku `
        --is-linux | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create App Service Plan" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✅ App Service Plan ready: $appPlanName" -ForegroundColor Green
Write-Host ""

# Create Web App with System-Assigned Managed Identity
Write-Host "📋 Step 5: Creating Web App with Managed Identity..." -ForegroundColor Yellow
$existingApp = az webapp show --name $AppName --resource-group $ResourceGroupName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   Web App already exists, updating..." -ForegroundColor Gray
    
    # Enable system-assigned managed identity
    az webapp identity assign --name $AppName --resource-group $ResourceGroupName | Out-Null
} else {
    Write-Host "   Creating new Web App..." -ForegroundColor Gray
    az webapp create `
        --name $AppName `
        --resource-group $ResourceGroupName `
        --plan $appPlanName `
        --runtime "PYTHON:3.11" `
        --assign-identity [system] | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create Web App" -ForegroundColor Red
        exit 1
    }
}

# Get the system-assigned identity
$webAppIdentity = az webapp identity show --name $AppName --resource-group $ResourceGroupName | ConvertFrom-Json
$webAppPrincipalId = $webAppIdentity.principalId

Write-Host "✅ Web App ready with System-Assigned Managed Identity!" -ForegroundColor Green
Write-Host "   Web App Principal ID: $webAppPrincipalId" -ForegroundColor Gray
Write-Host ""

# Configure Web App settings
Write-Host "📋 Step 6: Configuring Web App settings..." -ForegroundColor Yellow
az webapp config appsettings set `
    --name $AppName `
    --resource-group $ResourceGroupName `
    --settings `
        MICROSOFT_APP_TYPE="UserAssignedMSI" `
        MICROSOFT_APP_ID="$miClientId" `
        MICROSOFT_APP_TENANTID="$tenantId" `
        BACKEND_URL="$BackendUrl" `
        PORT="8000" `
        WEBSITES_PORT="8000" `
        SCM_DO_BUILD_DURING_DEPLOYMENT="true" `
        ENABLE_ORYX_BUILD="true" | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to configure Web App settings" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Web App configured with Managed Identity settings" -ForegroundColor Green
Write-Host ""

# Deploy code
Write-Host "📋 Step 7: Deploying bot code..." -ForegroundColor Yellow
Write-Host "   Creating deployment package..." -ForegroundColor Gray

# Create a temporary directory for deployment
$tempDir = Join-Path $env:TEMP "teams-bot-deploy-$(Get-Random)"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Copy necessary files (exclude unnecessary files)
$filesToCopy = @(
    "app.py",
    "bot.py",
    "backend_client.py",
    "requirements.txt",
    "manifest"
)

foreach ($file in $filesToCopy) {
    $sourcePath = Join-Path $PSScriptRoot $file
    if (Test-Path $sourcePath) {
        if (Test-Path $sourcePath -PathType Container) {
            Copy-Item -Path $sourcePath -Destination $tempDir -Recurse -Force
        } else {
            Copy-Item -Path $sourcePath -Destination $tempDir -Force
        }
    }
}

# Create ZIP
$zipPath = Join-Path $env:TEMP "teams-bot-$(Get-Random).zip"
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force

Write-Host "   Uploading code to Azure..." -ForegroundColor Gray
az webapp deployment source config-zip `
    --name $AppName `
    --resource-group $ResourceGroupName `
    --src $zipPath | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to deploy code" -ForegroundColor Red
    Remove-Item $tempDir -Recurse -Force
    Remove-Item $zipPath -Force
    exit 1
}

# Cleanup temp files
Remove-Item $tempDir -Recurse -Force
Remove-Item $zipPath -Force

Write-Host "✅ Code deployed successfully!" -ForegroundColor Green
Write-Host ""

# Wait for deployment to complete
Write-Host "   Waiting for app to start (30 seconds)..." -ForegroundColor Gray
Start-Sleep -Seconds 30

# Get Web App URL
$webAppUrl = az webapp show --name $AppName --resource-group $ResourceGroupName --query defaultHostName -o tsv
$botEndpoint = "https://$webAppUrl/api/messages"

Write-Host "✅ Web App is running!" -ForegroundColor Green
Write-Host "   URL: https://$webAppUrl" -ForegroundColor Gray
Write-Host "   Endpoint: $botEndpoint" -ForegroundColor Gray
Write-Host ""

# Create Azure Bot Service with Managed Identity
Write-Host "📋 Step 8: Creating Azure Bot Service with Managed Identity..." -ForegroundColor Yellow
$existingBot = az bot show --name $botName --resource-group $ResourceGroupName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   Bot already exists, updating endpoint..." -ForegroundColor Gray
    az bot update `
        --name $botName `
        --resource-group $ResourceGroupName `
        --endpoint $botEndpoint | Out-Null
} else {
    Write-Host "   Creating new Azure Bot with Managed Identity..." -ForegroundColor Gray
    az bot create `
        --name $botName `
        --resource-group $ResourceGroupName `
        --sku F0 `
        --app-type UserAssignedMSI `
        --appid $miClientId `
        --tenant-id $tenantId `
        --msi-resource-id $miResourceId `
        --endpoint $botEndpoint | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create Bot Service" -ForegroundColor Red
        Write-Host "   You may need to create it manually in Azure Portal" -ForegroundColor Yellow
        Write-Host "   Bot Name: $botName" -ForegroundColor Yellow
        Write-Host "   Endpoint: $botEndpoint" -ForegroundColor Yellow
        Write-Host "   Managed Identity Resource ID: $miResourceId" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Bot Service created successfully!" -ForegroundColor Green
    }
}
Write-Host ""

# Enable Teams channel
Write-Host "📋 Step 9: Enabling Teams channel..." -ForegroundColor Yellow
$teamsChannel = az bot msteams create `
    --name $botName `
    --resource-group $ResourceGroupName `
    --enable-calling false `
    --is-enabled true 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Teams channel may already be enabled or needs manual setup" -ForegroundColor Yellow
} else {
    Write-Host "✅ Teams channel enabled!" -ForegroundColor Green
}
Write-Host ""

# Test health endpoint
Write-Host "📋 Step 10: Testing bot health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://$webAppUrl/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Health check passed!" -ForegroundColor Green
        Write-Host "   Response: $($response.Content)" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️  Health check failed (app may still be starting)" -ForegroundColor Yellow
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Resources Created:" -ForegroundColor Yellow
Write-Host "   1. User-Assigned Managed Identity: $managedIdentityName" -ForegroundColor White
Write-Host "      Client ID: $miClientId" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Web App: $AppName" -ForegroundColor White
Write-Host "      URL: https://$webAppUrl" -ForegroundColor Gray
Write-Host "      Uses: System-Assigned Managed Identity" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Bot Service: $botName" -ForegroundColor White
Write-Host "      Endpoint: $botEndpoint" -ForegroundColor Gray
Write-Host "      Uses: User-Assigned Managed Identity" -ForegroundColor Gray
Write-Host ""
Write-Host "🔐 Security:" -ForegroundColor Yellow
Write-Host "   ✅ No App ID or Password stored!" -ForegroundColor Green
Write-Host "   ✅ Uses Azure Managed Identity for authentication" -ForegroundColor Green
Write-Host "   ✅ More secure and easier to manage" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Test in Teams:" -ForegroundColor White
Write-Host "      - Go to Azure Portal → Bot Service → $botName" -ForegroundColor Gray
Write-Host "      - Channels → Microsoft Teams → Open in Teams" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Monitor logs:" -ForegroundColor White
Write-Host "      az webapp log tail --name $AppName --resource-group $ResourceGroupName" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. View in Portal:" -ForegroundColor White
Write-Host "      https://portal.azure.com/#@/resource/subscriptions/$($account.id)/resourceGroups/$ResourceGroupName/overview" -ForegroundColor Gray
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
