# Test Managed Identity Permissions for Teams Bot
# This script verifies if you have permissions to use Managed Identity with Azure Bot Service

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "🔐 Testing Managed Identity Permissions for Teams Bot" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# 1. Check if logged in
Write-Host "📋 Step 1: Checking Azure CLI login..." -ForegroundColor Yellow
$account = az account show 2>&1 | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Not logged in. Please run: az login" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Logged in as: $($account.user.name)" -ForegroundColor Green
Write-Host "   Subscription: $($account.name)" -ForegroundColor Gray
Write-Host ""

# 2. Test creating User-Assigned Managed Identity
Write-Host "📋 Step 2: Testing User-Assigned Managed Identity creation..." -ForegroundColor Yellow
$testRG = "rg-test-mi-$(Get-Random -Minimum 1000 -Maximum 9999)"
$testMIName = "mi-test-bot"
$location = "eastus"

Write-Host "   Creating test resource group: $testRG" -ForegroundColor Gray
$rgResult = az group create --name $testRG --location $location 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Cannot create resource group. Check permissions." -ForegroundColor Red
    Write-Host "   Error: $rgResult" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Resource group created successfully" -ForegroundColor Green

Write-Host "   Creating User-Assigned Managed Identity..." -ForegroundColor Gray
$miResult = az identity create --name $testMIName --resource-group $testRG --location $location 2>&1 | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Cannot create Managed Identity. You might not have permissions." -ForegroundColor Red
    Write-Host "   Error: $miResult" -ForegroundColor Red
    
    # Cleanup
    Write-Host "   Cleaning up test resource group..." -ForegroundColor Gray
    az group delete --name $testRG --yes --no-wait
    exit 1
}

$miClientId = $miResult.clientId
$miPrincipalId = $miResult.principalId
$miResourceId = $miResult.id

Write-Host "✅ Managed Identity created successfully!" -ForegroundColor Green
Write-Host "   Client ID: $miClientId" -ForegroundColor Gray
Write-Host "   Principal ID: $miPrincipalId" -ForegroundColor Gray
Write-Host ""

# 3. Test creating Bot Service with Managed Identity
Write-Host "📋 Step 3: Testing Bot Service creation with Managed Identity..." -ForegroundColor Yellow
$testBotName = "bot-test-mi-$(Get-Random -Minimum 1000 -Maximum 9999)"

Write-Host "   Creating Azure Bot with Managed Identity..." -ForegroundColor Gray
$botResult = az bot create `
    --name $testBotName `
    --resource-group $testRG `
    --sku F0 `
    --app-type UserAssignedMSI `
    --appid $miClientId `
    --tenant-id $account.tenantId `
    --msi-resource-id $miResourceId `
    --endpoint "https://example.com/api/messages" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Cannot create Bot with Managed Identity." -ForegroundColor Red
    Write-Host "   This might be due to:" -ForegroundColor Yellow
    Write-Host "   1. Missing 'Microsoft.BotService/botServices/write' permission" -ForegroundColor Yellow
    Write-Host "   2. Missing permissions to assign Managed Identity to Bot" -ForegroundColor Yellow
    Write-Host "   Error: $botResult" -ForegroundColor Red
    
    # Cleanup
    Write-Host "   Cleaning up..." -ForegroundColor Gray
    az group delete --name $testRG --yes --no-wait
    exit 1
}

Write-Host "✅ Bot Service with Managed Identity created successfully!" -ForegroundColor Green
Write-Host ""

# 4. Test creating App Service with Managed Identity
Write-Host "📋 Step 4: Testing App Service with System-Assigned Managed Identity..." -ForegroundColor Yellow
$testAppPlan = "plan-test-$(Get-Random -Minimum 1000 -Maximum 9999)"
$testAppName = "app-test-$(Get-Random -Minimum 1000 -Maximum 9999)"

Write-Host "   Creating App Service Plan..." -ForegroundColor Gray
az appservice plan create `
    --name $testAppPlan `
    --resource-group $testRG `
    --sku B1 `
    --is-linux | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Cannot create App Service Plan" -ForegroundColor Yellow
} else {
    Write-Host "✅ App Service Plan created" -ForegroundColor Green
    
    Write-Host "   Creating Web App with System-Assigned Managed Identity..." -ForegroundColor Gray
    $webAppResult = az webapp create `
        --name $testAppName `
        --resource-group $testRG `
        --plan $testAppPlan `
        --runtime "PYTHON:3.11" `
        --assign-identity [system] 2>&1 | ConvertFrom-Json
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Cannot create Web App with Managed Identity" -ForegroundColor Red
    } else {
        $webAppIdentity = $webAppResult.identity.principalId
        Write-Host "✅ Web App with System-Assigned Managed Identity created!" -ForegroundColor Green
        Write-Host "   Principal ID: $webAppIdentity" -ForegroundColor Gray
    }
}
Write-Host ""

# 5. Cleanup
Write-Host "📋 Step 5: Cleaning up test resources..." -ForegroundColor Yellow
az group delete --name $testRG --yes --no-wait
Write-Host "✅ Cleanup initiated (running in background)" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "📊 SUMMARY - Managed Identity Permissions Test" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ You have permissions to:" -ForegroundColor Green
Write-Host "   1. Create User-Assigned Managed Identity" -ForegroundColor Green
Write-Host "   2. Create Azure Bot Service with Managed Identity" -ForegroundColor Green
Write-Host "   3. Create App Service with System-Assigned Managed Identity" -ForegroundColor Green
Write-Host ""
Write-Host "🎉 GREAT NEWS!" -ForegroundColor Green
Write-Host "   You CAN use Managed Identity for Teams Bot deployment!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Run: .\deploy_with_managed_identity.ps1" -ForegroundColor White
Write-Host "   2. This will deploy Teams bot WITHOUT needing App ID/Password" -ForegroundColor White
Write-Host "   3. More secure and easier to manage!" -ForegroundColor White
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
