<# 
.SYNOPSIS
    Fix authentication settings for Teams Bot in Azure App Service
    
.DESCRIPTION
    This script removes MICROSOFT_APP_PASSWORD and ensures Managed Identity is properly configured
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$AppName,
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup
)

$ErrorActionPreference = "Stop"

Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       Fix Teams Bot Authentication in Azure                       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if logged in to Azure
Write-Host "🔍 Checking Azure login..." -ForegroundColor Yellow
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "❌ Not logged in to Azure. Please run 'az login' first." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Logged in as: $($account.user.name)" -ForegroundColor Green
Write-Host ""

# If AppName not provided, list available web apps
if (-not $AppName) {
    Write-Host "📋 Available App Services:" -ForegroundColor Cyan
    $webapps = az webapp list --query "[].{name:name, resourceGroup:resourceGroup, state:state, kind:kind}" | ConvertFrom-Json
    
    if ($webapps.Count -eq 0) {
        Write-Host "❌ No App Services found in your subscription" -ForegroundColor Red
        exit 1
    }
    
    $index = 1
    foreach ($app in $webapps) {
        $kind = if ($app.kind -match "linux") { "🐧 Linux" } else { "🪟 Windows" }
        Write-Host "   $index. $($app.name) [$kind] - RG: $($app.resourceGroup) - State: $($app.state)" -ForegroundColor White
        $index++
    }
    Write-Host ""
    
    $selection = Read-Host "Select App Service number (or press Enter to cancel)"
    if ([string]::IsNullOrWhiteSpace($selection)) {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
    
    $selectedIndex = [int]$selection - 1
    if ($selectedIndex -lt 0 -or $selectedIndex -ge $webapps.Count) {
        Write-Host "❌ Invalid selection" -ForegroundColor Red
        exit 1
    }
    
    $selectedApp = $webapps[$selectedIndex]
    $AppName = $selectedApp.name
    $ResourceGroup = $selectedApp.resourceGroup
    
    Write-Host "✅ Selected: $AppName in $ResourceGroup" -ForegroundColor Green
    Write-Host ""
}

# Check if app exists
Write-Host "🔍 Checking if App Service exists..." -ForegroundColor Yellow
$appExists = az webapp show --name $AppName --resource-group $ResourceGroup 2>$null
if (-not $appExists) {
    Write-Host "❌ App Service '$AppName' not found in resource group '$ResourceGroup'" -ForegroundColor Red
    exit 1
}
Write-Host "✅ App Service found: $AppName" -ForegroundColor Green
Write-Host ""

# Get current Managed Identity
Write-Host "🔍 Checking Managed Identity configuration..." -ForegroundColor Yellow
$identity = az webapp identity show --name $AppName --resource-group $ResourceGroup 2>$null | ConvertFrom-Json

$miClientId = $null

if ($identity -and $identity.type -eq "UserAssigned" -and $identity.userAssignedIdentities) {
    # Get the first user-assigned identity
    $identityKeys = $identity.userAssignedIdentities | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name
    if ($identityKeys) {
        $firstIdentityKey = $identityKeys[0]
        $miClientId = $identity.userAssignedIdentities.$firstIdentityKey.clientId
        Write-Host "✅ Managed Identity found: $miClientId" -ForegroundColor Green
    }
}

if (-not $miClientId) {
    Write-Host "⚠️  User-assigned Managed Identity not found or not properly configured." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Available options:" -ForegroundColor Cyan
    Write-Host "   1. Use existing Managed Identity (recommended)" -ForegroundColor White
    Write-Host "   2. Use Client Secret (MICROSOFT_APP_PASSWORD)" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Select option (1 or 2)"
    
    if ($choice -eq "1") {
        # List available managed identities
        Write-Host "📋 Searching for Managed Identities in resource group..." -ForegroundColor Yellow
        $identities = az identity list --resource-group $ResourceGroup 2>$null | ConvertFrom-Json
        
        if ($identities.Count -eq 0) {
            Write-Host "❌ No Managed Identities found in resource group '$ResourceGroup'" -ForegroundColor Red
            Write-Host "   Please create one first or use Client Secret authentication." -ForegroundColor Yellow
            exit 1
        }
        
        Write-Host "Available Managed Identities:" -ForegroundColor Cyan
        $index = 1
        foreach ($id in $identities) {
            Write-Host "   $index. $($id.name) - Client ID: $($id.clientId)" -ForegroundColor White
            $index++
        }
        Write-Host ""
        
        $selection = Read-Host "Select Managed Identity number"
        $selectedIndex = [int]$selection - 1
        
        if ($selectedIndex -lt 0 -or $selectedIndex -ge $identities.Count) {
            Write-Host "❌ Invalid selection" -ForegroundColor Red
            exit 1
        }
        
        $selectedIdentity = $identities[$selectedIndex]
        $identityResourceId = $selectedIdentity.id
        $miClientId = $selectedIdentity.clientId
        
        Write-Host "✅ Selected: $($selectedIdentity.name)" -ForegroundColor Green
        Write-Host ""
        
        # Assign the identity to the web app
        Write-Host "� Assigning Managed Identity to App Service..." -ForegroundColor Yellow
        az webapp identity assign `
            --name $AppName `
            --resource-group $ResourceGroup `
            --identities $identityResourceId `
            --output none
        
        Write-Host "✅ Managed Identity assigned" -ForegroundColor Green
    }
    elseif ($choice -eq "2") {
        Write-Host "⚠️  Using Client Secret authentication requires MICROSOFT_APP_PASSWORD to be set." -ForegroundColor Yellow
        Write-Host "   This script is designed for Managed Identity setup." -ForegroundColor Yellow
        Write-Host "   Please set MICROSOFT_APP_PASSWORD manually in Azure Portal." -ForegroundColor Yellow
        exit 0
    }
    else {
        Write-Host "❌ Invalid choice" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Get current app settings
Write-Host "🔍 Checking current app settings..." -ForegroundColor Yellow
$currentSettings = az webapp config appsettings list `
    --name $AppName `
    --resource-group $ResourceGroup | ConvertFrom-Json

# Check for problematic settings
$hasPassword = $currentSettings | Where-Object { $_.name -eq "MICROSOFT_APP_PASSWORD" }
$appId = ($currentSettings | Where-Object { $_.name -eq "MICROSOFT_APP_ID" }).value
$appType = ($currentSettings | Where-Object { $_.name -eq "MICROSOFT_APP_TYPE" }).value
$tenantId = ($currentSettings | Where-Object { $_.name -eq "MICROSOFT_APP_TENANTID" }).value

Write-Host "   Current settings:" -ForegroundColor Gray
Write-Host "   - MICROSOFT_APP_ID: $appId" -ForegroundColor Gray
Write-Host "   - MICROSOFT_APP_TYPE: $appType" -ForegroundColor Gray
Write-Host "   - MICROSOFT_APP_TENANTID: $tenantId" -ForegroundColor Gray
Write-Host "   - MICROSOFT_APP_PASSWORD: $(if ($hasPassword) { '❌ SET (should be removed)' } else { '✅ Not set' })" -ForegroundColor Gray
Write-Host ""

# Remove MICROSOFT_APP_PASSWORD if it exists
if ($hasPassword) {
    Write-Host "🔧 Removing MICROSOFT_APP_PASSWORD..." -ForegroundColor Yellow
    az webapp config appsettings delete `
        --name $AppName `
        --resource-group $ResourceGroup `
        --setting-names MICROSOFT_APP_PASSWORD `
        --output none
    Write-Host "✅ MICROSOFT_APP_PASSWORD removed" -ForegroundColor Green
    Write-Host ""
}

# Update app settings with correct values
Write-Host "🔧 Updating app settings for Managed Identity..." -ForegroundColor Yellow
az webapp config appsettings set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --settings `
        MICROSOFT_APP_TYPE="UserAssignedMSI" `
        MICROSOFT_APP_ID="$miClientId" `
        MICROSOFT_APP_TENANTID="52d32ffe-bfad-4f92-b437-e29121332333" `
    --output none

Write-Host "✅ App settings updated" -ForegroundColor Green
Write-Host ""

# Restart the app
Write-Host "🔄 Restarting App Service..." -ForegroundColor Yellow
az webapp restart `
    --name $AppName `
    --resource-group $ResourceGroup `
    --output none

Write-Host "✅ App Service restarted" -ForegroundColor Green
Write-Host ""

Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    ✅ Configuration Fixed!                         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Wait 1-2 minutes for the app to restart" -ForegroundColor White
Write-Host "2. Check logs: az webapp log tail --name $AppName --resource-group $ResourceGroup" -ForegroundColor White
Write-Host "3. Test the bot in Teams" -ForegroundColor White
Write-Host ""
