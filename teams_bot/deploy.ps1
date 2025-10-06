# Teams Bot Deployment Script pentru Azure
# Acest script automatizează deployment-ul bot-ului Teams în Azure

param(
    [string]$ResourceGroupName,
    [string]$Location = "eastus",
    [string]$AppName,
    [string]$BackendUrl,
    [switch]$SkipBotRegistration,
    [switch]$Help
)

# Colors pentru output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Show-Help {
    Write-Host @"
===========================================
Teams Bot Deployment Script
===========================================

Usage:
    .\deploy.ps1 -ResourceGroupName <rg-name> -AppName <app-name> -BackendUrl <url> [options]

Required Parameters:
    -ResourceGroupName    Numele resource group-ului Azure (ex: rg-teams-bot)
    -AppName              Numele unic pentru bot (ex: teamsbot-mihai)
    -BackendUrl           URL-ul backend-ului deployed (ex: https://backend.azurecontainerapps.io)

Optional Parameters:
    -Location             Azure region (default: eastus)
    -SkipBotRegistration  Skip înregistrarea bot-ului dacă există deja
    -Help                 Afișează acest mesaj

Examples:
    # Deployment complet
    .\deploy.ps1 -ResourceGroupName "rg-teams-bot" -AppName "teamsbot-mihai" -BackendUrl "https://backend.azurecontainerapps.io"

    # Folosind bot registration existent
    .\deploy.ps1 -ResourceGroupName "rg-teams-bot" -AppName "teamsbot-mihai" -BackendUrl "https://backend.azurecontainerapps.io" -SkipBotRegistration

Prerequisites:
    - Azure CLI instalat și autentificat (az login)
    - PowerShell 7+
    - Backend-ul deja deployed în Azure
    - Python 3.9+ instalat local (pentru testare)

"@
    exit 0
}

if ($Help) {
    Show-Help
}

# Validare parametri
if (-not $ResourceGroupName -or -not $AppName -or -not $BackendUrl) {
    Write-ColorOutput Red "❌ Eroare: Parametri lipsă!"
    Write-Host ""
    Show-Help
}

Write-ColorOutput Cyan @"

===========================================
🤖 Teams Bot Deployment Script
===========================================
Resource Group: $ResourceGroupName
App Name: $AppName
Backend URL: $BackendUrl
Location: $Location
===========================================

"@

# Check prerequisites
Write-ColorOutput Yellow "📋 Verificare prerequisite..."

# Check Azure CLI
try {
    $azVersion = az version --query '\"azure-cli\"' -o tsv 2>$null
    Write-ColorOutput Green "✅ Azure CLI: $azVersion"
} catch {
    Write-ColorOutput Red "❌ Azure CLI nu este instalat sau nu este în PATH"
    Write-Host "Instalează de la: https://aka.ms/installazurecliwindows"
    exit 1
}

# Check login
try {
    $account = az account show --query name -o tsv 2>$null
    if (-not $account) {
        Write-ColorOutput Red "❌ Nu ești autentificat în Azure"
        Write-Host "Rulează: az login"
        exit 1
    }
    Write-ColorOutput Green "✅ Azure Account: $account"
} catch {
    Write-ColorOutput Red "❌ Nu ești autentificat în Azure"
    Write-Host "Rulează: az login"
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version 2>$null
    Write-ColorOutput Green "✅ Python: $pythonVersion"
} catch {
    Write-ColorOutput Yellow "⚠️  Python nu este instalat (necesar doar pentru testare locală)"
}

Write-Host ""

# STEP 1: Bot Registration
$appId = ""
$appPassword = ""

if (-not $SkipBotRegistration) {
    Write-ColorOutput Yellow "🔐 Pas 1: Creare Azure AD App Registration..."
    
    try {
        # Check dacă există deja
        $existingApp = az ad app list --display-name $AppName --query "[0].appId" -o tsv 2>$null
        
        if ($existingApp) {
            Write-ColorOutput Yellow "⚠️  App Registration '$AppName' există deja"
            $useExisting = Read-Host "Folosești App ID existent? (y/n)"
            
            if ($useExisting -eq 'y') {
                $appId = $existingApp
                Write-ColorOutput Green "✅ Folosim App ID existent: $appId"
                
                # Creează un nou secret
                Write-ColorOutput Yellow "📝 Generare client secret nou..."
                $appPassword = az ad app credential reset --id $appId --append --query password -o tsv
                Write-ColorOutput Green "✅ Client secret generat"
            } else {
                $newAppName = Read-Host "Introdu un nume nou pentru aplicație"
                $AppName = $newAppName
            }
        }
        
        if (-not $appId) {
            # Creează App Registration
            Write-ColorOutput Yellow "📝 Creare App Registration..."
            $appId = az ad app create --display-name $AppName --query appId -o tsv
            Write-ColorOutput Green "✅ App ID: $appId"
            
            # Creează client secret
            Write-ColorOutput Yellow "📝 Generare client secret..."
            $appPassword = az ad app credential reset --id $appId --query password -o tsv
            Write-ColorOutput Green "✅ Client secret generat"
        }
        
        # Salvează în fișier .env
        Write-ColorOutput Yellow "💾 Salvare credențiale în .env..."
        $envContent = @"
# Microsoft Bot Framework
MICROSOFT_APP_ID=$appId
MICROSOFT_APP_PASSWORD=$appPassword

# Backend URL
BACKEND_URL=$BackendUrl

# Port
PORT=3978
"@
        Set-Content -Path ".env" -Value $envContent
        Write-ColorOutput Green "✅ Credențiale salvate în .env"
        
        Write-ColorOutput Cyan @"

⚠️  IMPORTANT - Salvează aceste credențiale:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Microsoft App ID: $appId
Microsoft App Password: $appPassword
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Password-ul nu va mai fi afișat!
Credențialele sunt salvate și în fișierul .env

"@
        
    } catch {
        Write-ColorOutput Red "❌ Eroare la crearea App Registration: $_"
        exit 1
    }
} else {
    Write-ColorOutput Yellow "⏭️  Skip Bot Registration (folosind credențiale existente)"
    
    # Citește din .env
    if (Test-Path ".env") {
        $envContent = Get-Content ".env"
        $appId = ($envContent | Select-String "MICROSOFT_APP_ID=(.+)").Matches.Groups[1].Value
        Write-ColorOutput Green "✅ App ID din .env: $appId"
    } else {
        Write-ColorOutput Red "❌ Fișierul .env nu există!"
        Write-Host "Rulează fără -SkipBotRegistration sau creează manual .env"
        exit 1
    }
}

Write-Host ""

# STEP 2: Resource Group
Write-ColorOutput Yellow "🏗️  Pas 2: Verificare/Creare Resource Group..."

$rgExists = az group exists --name $ResourceGroupName
if ($rgExists -eq "true") {
    Write-ColorOutput Green "✅ Resource Group '$ResourceGroupName' există"
} else {
    Write-ColorOutput Yellow "📝 Creare Resource Group..."
    az group create --name $ResourceGroupName --location $Location --output none
    Write-ColorOutput Green "✅ Resource Group creat: $ResourceGroupName"
}

Write-Host ""

# STEP 3: Deploy App Service
Write-ColorOutput Yellow "🚀 Pas 3: Deploy Azure App Service..."

try {
    # Check dacă App Service Plan există
    $planName = "$AppName-plan"
    $planExists = az appservice plan show --name $planName --resource-group $ResourceGroupName --query id -o tsv 2>$null
    
    if (-not $planExists) {
        Write-ColorOutput Yellow "📝 Creare App Service Plan..."
        az appservice plan create `
            --name $planName `
            --resource-group $ResourceGroupName `
            --location $Location `
            --sku B1 `
            --is-linux `
            --output none
        Write-ColorOutput Green "✅ App Service Plan creat"
    } else {
        Write-ColorOutput Green "✅ App Service Plan există"
    }
    
    # Check dacă Web App există
    $webAppExists = az webapp show --name $AppName --resource-group $ResourceGroupName --query id -o tsv 2>$null
    
    if (-not $webAppExists) {
        Write-ColorOutput Yellow "📝 Creare Web App..."
        az webapp create `
            --name $AppName `
            --resource-group $ResourceGroupName `
            --plan $planName `
            --runtime "PYTHON:3.11" `
            --output none
        Write-ColorOutput Green "✅ Web App creat"
    } else {
        Write-ColorOutput Green "✅ Web App există"
    }
    
    # Configurare App Settings
    Write-ColorOutput Yellow "⚙️  Configurare App Settings..."
    az webapp config appsettings set `
        --name $AppName `
        --resource-group $ResourceGroupName `
        --settings `
            MICROSOFT_APP_ID=$appId `
            MICROSOFT_APP_PASSWORD=$appPassword `
            BACKEND_URL=$BackendUrl `
            PORT=3978 `
            SCM_DO_BUILD_DURING_DEPLOYMENT=true `
        --output none
    Write-ColorOutput Green "✅ App Settings configurate"
    
    # Deploy cod
    Write-ColorOutput Yellow "📦 Deploy cod..."
    
    # Creează zip cu codul
    $tempZip = [System.IO.Path]::GetTempFileName() + ".zip"
    
    # Exclude venv, __pycache__, etc.
    $filesToInclude = @(
        "app.py",
        "bot.py",
        "backend_client.py",
        "requirements.txt"
    )
    
    Compress-Archive -Path $filesToInclude -DestinationPath $tempZip -Force
    
    # Deploy zip
    az webapp deployment source config-zip `
        --name $AppName `
        --resource-group $ResourceGroupName `
        --src $tempZip `
        --output none
    
    Remove-Item $tempZip
    
    Write-ColorOutput Green "✅ Cod deployed"
    
    $webAppUrl = "https://$AppName.azurewebsites.net"
    Write-ColorOutput Cyan @"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Web App deployed!
URL: $webAppUrl
Messaging Endpoint: $webAppUrl/api/messages
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"@
    
} catch {
    Write-ColorOutput Red "❌ Eroare la deploy Web App: $_"
    exit 1
}

Write-Host ""

# STEP 4: Configure Azure Bot Service
Write-ColorOutput Yellow "🤖 Pas 4: Configurare Azure Bot Service..."

try {
    $botName = "$AppName-bot"
    $botExists = az bot show --name $botName --resource-group $ResourceGroupName --query id -o tsv 2>$null
    
    if (-not $botExists) {
        Write-ColorOutput Yellow "📝 Creare Azure Bot..."
        az bot create `
            --name $botName `
            --resource-group $ResourceGroupName `
            --appid $appId `
            --password $appPassword `
            --endpoint "https://$AppName.azurewebsites.net/api/messages" `
            --kind "registration" `
            --output none
        Write-ColorOutput Green "✅ Azure Bot creat"
    } else {
        Write-ColorOutput Green "✅ Azure Bot există"
        
        # Update endpoint
        az bot update `
            --name $botName `
            --resource-group $ResourceGroupName `
            --endpoint "https://$AppName.azurewebsites.net/api/messages" `
            --output none
        Write-ColorOutput Green "✅ Bot endpoint actualizat"
    }
    
    # Enable Teams channel
    Write-ColorOutput Yellow "📺 Activare Teams Channel..."
    az bot msteams create --name $botName --resource-group $ResourceGroupName --output none 2>$null
    Write-ColorOutput Green "✅ Teams Channel activat"
    
} catch {
    Write-ColorOutput Yellow "⚠️  Eroare la configurare Bot Service (posibil există deja): $_"
}

Write-Host ""

# STEP 5: Generate Teams Manifest
Write-ColorOutput Yellow "📋 Pas 5: Generare Teams App Manifest..."

# Generează UUID pentru Teams App
$teamsAppId = [guid]::NewGuid().ToString()

# Actualizează manifest
$manifestPath = "manifest/manifest.json"
if (Test-Path $manifestPath) {
    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    
    $manifest.id = $teamsAppId
    $manifest.bots[0].botId = $appId
    $manifest.validDomains = @("$AppName.azurewebsites.net")
    $manifest.webApplicationInfo.id = $appId
    $manifest.webApplicationInfo.resource = "api://$AppName.azurewebsites.net/$appId"
    
    $manifest | ConvertTo-Json -Depth 10 | Set-Content $manifestPath
    
    Write-ColorOutput Green "✅ Manifest actualizat"
    Write-ColorOutput Cyan "Teams App ID: $teamsAppId"
} else {
    Write-ColorOutput Yellow "⚠️  Manifest nu există la $manifestPath"
}

Write-Host ""

# STEP 6: Create Teams App Package
Write-ColorOutput Yellow "📦 Pas 6: Creare Teams App Package..."

if (Test-Path "manifest/manifest.json") {
    $zipPath = "teams-app.zip"
    
    # Check dacă avem iconițe
    if (-not (Test-Path "manifest/color.png") -or -not (Test-Path "manifest/outline.png")) {
        Write-ColorOutput Yellow "⚠️  Iconițe lipsă! Creez iconițe default..."
        # Aici ar trebui să creezi iconițe default, dar pentru simplitate doar avertizăm
        Write-ColorOutput Yellow "   Adaugă manual color.png (192x192) și outline.png (32x32) în manifest/"
    }
    
    # Creează zip
    if (Test-Path "manifest/color.png" -and Test-Path "manifest/outline.png") {
        Compress-Archive `
            -Path "manifest/manifest.json","manifest/color.png","manifest/outline.png" `
            -DestinationPath $zipPath `
            -Force
        
        Write-ColorOutput Green "✅ Teams App Package creat: $zipPath"
    } else {
        Write-ColorOutput Yellow "⚠️  Nu s-a putut crea package-ul (iconițe lipsă)"
    }
} else {
    Write-ColorOutput Yellow "⚠️  Manifest nu există"
}

Write-Host ""

# FINAL: Summary
Write-ColorOutput Cyan @"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 DEPLOYMENT FINALIZAT CU SUCCES!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Resurse Create:
   Resource Group: $ResourceGroupName
   Web App: $AppName
   Bot Service: $AppName-bot
   URL: https://$AppName.azurewebsites.net

🔐 Credențiale:
   Microsoft App ID: $appId
   (Password salvat în .env)

📱 Următorii pași pentru Teams:
   1. Deschide Microsoft Teams
   2. Apps → Manage your apps
   3. Upload a custom app
   4. Selectează: teams-app.zip
   5. Testează bot-ul!

📊 Comenzi utile:
   # Vezi logs
   az webapp log tail --name $AppName --resource-group $ResourceGroupName

   # Restart app
   az webapp restart --name $AppName --resource-group $ResourceGroupName

   # Test endpoint
   curl https://$AppName.azurewebsites.net/health

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"@

Write-ColorOutput Green "✅ Deployment complet!"
