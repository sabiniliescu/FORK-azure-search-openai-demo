#!/usr/bin/env pwsh
<#!
.SYNOPSIS
    Provision or update the Azure Bot resource and Teams channel for the Teams bot web app.

.DESCRIPTION
    Creates (or updates) an Azure Bot resource that uses a User-Assigned Managed Identity and
    points it at the specified Web App endpoint. If the bot already exists, only the endpoint
    is updated. The script also ensures the Microsoft Teams channel is enabled.

.NOTES
    Requires the Azure CLI (`az`) to be installed and you must be logged in (`az login`).
#>

param(
    [Parameter()]
    [string]$ResourceGroup,

    [Parameter()]
    [string]$AppName,

    [Parameter()]
    [string]$BotName,

    [Parameter()]
    [string]$ManagedIdentityName,

    [Parameter()]
    [string]$Endpoint,

    [Parameter()]
    [string]$Location,

    [Parameter()]
    [ValidateSet("F0", "S1")]
    [string]$Sku
)

$ErrorActionPreference = "Stop"

function Resolve-FirstValue {
    param(
        [Parameter(Mandatory = $false)]
        [object[]]$Candidates
    )

    if (-not $Candidates) {
        return $null
    }

    foreach ($candidate in $Candidates) {
        if ($null -ne $candidate) {
            $value = $candidate.ToString().Trim()
            if ($value) {
                return $value
            }
        }
    }

    return $null
}

function Import-DotEnv {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return
    }

    foreach ($line in Get-Content $Path) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $trimmed = $line.Trim()
        if ($trimmed.StartsWith('#')) { continue }

        $pair = $line -split '=', 2
        if ($pair.Length -ne 2) { continue }

        $key = $pair[0].Trim()
        $value = $pair[1].Trim()

        if ($value.StartsWith('"') -and $value.EndsWith('"') -and $value.Length -ge 2) {
            $value = $value.Substring(1, $value.Length - 2)
        } elseif ($value.StartsWith("'") -and $value.EndsWith("'") -and $value.Length -ge 2) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        [Environment]::SetEnvironmentVariable($key, $value)
    }
}

function Try-LoadAzdEnv {
    if (-not (Get-Command azd -ErrorAction SilentlyContinue)) {
        return
    }

    try {
        $envList = azd env list --output json | ConvertFrom-Json
        $defaultEnv = $envList | Where-Object { $_.IsDefault } | Select-Object -First 1
        if ($defaultEnv -and $defaultEnv.DotEnvPath) {
            Import-DotEnv $defaultEnv.DotEnvPath
            Write-Host "   Loaded azd environment: $($defaultEnv.Name)" -ForegroundColor Gray
        }
    } catch {
        Write-Host "   Unable to load azd environment automatically ($_)." -ForegroundColor DarkGray
    }
}

Try-LoadAzdEnv

$ResourceGroup = Resolve-FirstValue @(
    $ResourceGroup,
    $env:AZURE_TEAMS_BOT_RESOURCE_GROUP,
    $env:AZURE_RESOURCE_GROUP
)

if (-not $ResourceGroup) {
    throw "Unable to resolve the resource group. Provide --ResourceGroup or set AZURE_RESOURCE_GROUP."
}

$AppName = Resolve-FirstValue @(
    $AppName,
    $env:AZURE_TEAMS_BOT_WEBAPP_NAME,
    $env:AZURE_APP_SERVICE,
    $env:AZURE_TEAMS_BOT_NAME
)

if (-not $AppName) {
    try {
        $webAppsRaw = az webapp list `
            --resource-group $ResourceGroup `
            --query "[].name" `
            --output tsv 2>$null
        if ($LASTEXITCODE -eq 0 -and $webAppsRaw) {
            $webAppCandidates = $webAppsRaw -split "`n" | Where-Object { $_ }
            $AppName = ($webAppCandidates | Where-Object { $_ -like "*teamsbot*" } | Select-Object -First 1)
            if (-not $AppName -and $webAppCandidates) {
                $AppName = ($webAppCandidates | Select-Object -First 1)
            }
        }
    } catch {
        Write-Host "   Unable to auto-detect web app name ($_)." -ForegroundColor DarkGray
    }
}

if (-not $AppName) {
    throw "Unable to resolve the Teams bot Web App name. Provide --AppName or set AZURE_TEAMS_BOT_WEBAPP_NAME."
}

$BotName = Resolve-FirstValue @(
    $BotName,
    $env:AZURE_TEAMS_BOT_NAME,
    "bot-$AppName"
)

$ManagedIdentityName = Resolve-FirstValue @(
    $ManagedIdentityName,
    $env:AZURE_TEAMS_BOT_MANAGED_IDENTITY_NAME,
    $env:AZURE_TEAMS_BOT_IDENTITY_NAME
)

if (-not $ManagedIdentityName) {
    try {
        $identityRaw = az identity list `
            --resource-group $ResourceGroup `
            --query "[].name" `
            --output tsv 2>$null
        if ($LASTEXITCODE -eq 0 -and $identityRaw) {
            $identityCandidates = $identityRaw -split "`n" | Where-Object { $_ }
            $ManagedIdentityName = ($identityCandidates | Where-Object { $_ -like "*$AppName*" } | Select-Object -First 1)
            if (-not $ManagedIdentityName -and $identityCandidates) {
                $ManagedIdentityName = ($identityCandidates | Select-Object -First 1)
            }
        }
    } catch {
        Write-Host "   Unable to auto-detect managed identity name ($_)." -ForegroundColor DarkGray
    }
}

if (-not $ManagedIdentityName) {
    $ManagedIdentityName = "mi-$AppName"
}

$Location = Resolve-FirstValue @(
    $Location,
    $env:AZURE_TEAMS_BOT_LOCATION,
    $env:AZURE_LOCATION
)

if (-not $Location) {
    try {
        $rgInfo = az group show `
            --name $ResourceGroup `
            --output json 2>$null
        if ($LASTEXITCODE -eq 0 -and $rgInfo) {
            $Location = ((ConvertFrom-Json $rgInfo).location)
        }
    } catch {
        Write-Host "   Unable to determine resource group location ($_)." -ForegroundColor DarkGray
    }
}

if (-not $Location) {
    $Location = "eastus"
}

$Sku = Resolve-FirstValue @(
    $Sku,
    $env:AZURE_TEAMS_BOT_SKU
)

if (-not $Sku) {
    $Sku = "F0"
}
$Sku = $Sku.ToUpperInvariant()

Write-Host "`n$('=' * 80)" -ForegroundColor Cyan
Write-Host "🤖 Azure Bot Resource Deployment" -ForegroundColor Cyan
Write-Host "$('=' * 80)`n" -ForegroundColor Cyan

# Derive defaults when omitted
if (-not $Endpoint) {
    $defaultHost = az webapp show `
        --name $AppName `
        --resource-group $ResourceGroup `
        --query defaultHostName `
        --output tsv

    if (-not $defaultHost) {
        throw "Unable to determine default host name for Web App '$AppName'. Provide --Endpoint explicitly."
    }

    $Endpoint = "https://$defaultHost/api/messages"
}

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   Resource Group : $ResourceGroup" -ForegroundColor White
Write-Host "   Web App        : $AppName" -ForegroundColor White
Write-Host "   Bot Name       : $BotName" -ForegroundColor White
Write-Host "   Managed Identity: $ManagedIdentityName" -ForegroundColor White
Write-Host "   Endpoint       : $Endpoint" -ForegroundColor White
Write-Host "   Location       : $Location" -ForegroundColor White
Write-Host "   SKU            : $Sku`n" -ForegroundColor White

Write-Host "🔐 Step 1: Verifying Azure login..." -ForegroundColor Yellow
try {
    $account = az account show --output json | ConvertFrom-Json
} catch {
    throw "Not logged in to Azure. Please run 'az login' and retry."
}
$tenantId = $account.tenantId
Write-Host "✅ Logged in as: $($account.user.name)" -ForegroundColor Green
Write-Host "   Tenant ID: $tenantId`n" -ForegroundColor Gray

Write-Host "🏗️  Step 2: Ensuring resource group exists..." -ForegroundColor Yellow
az group create `
    --name $ResourceGroup `
    --location $Location `
    --output none
Write-Host "✅ Resource group ready" -ForegroundColor Green

Write-Host "🆔 Step 3: Resolving managed identity..." -ForegroundColor Yellow
$identity = az identity show `
    --name $ManagedIdentityName `
    --resource-group $ResourceGroup `
    --output json 2>$null

if (-not $identity) {
    throw "User-assigned managed identity '$ManagedIdentityName' was not found in resource group '$ResourceGroup'."
}

$identityObj = $identity | ConvertFrom-Json
$miClientId = $identityObj.clientId
$miResourceId = $identityObj.id
Write-Host "✅ Managed identity located" -ForegroundColor Green
Write-Host "   Client ID: $miClientId" -ForegroundColor Gray
Write-Host "   Resource ID: $miResourceId`n" -ForegroundColor Gray

Write-Host "🤖 Step 4: Creating or updating Azure Bot..." -ForegroundColor Yellow
$botExists = az bot show `
    --name $BotName `
    --resource-group $ResourceGroup `
    --output json 2>$null

if ($botExists) {
    Write-Host "   Bot already exists. Updating endpoint..." -ForegroundColor Gray
    az bot update `
        --name $BotName `
        --resource-group $ResourceGroup `
        --endpoint $Endpoint `
        --output none
    Write-Host "✅ Bot endpoint updated" -ForegroundColor Green
} else {
    Write-Host "   Creating new Azure Bot resource..." -ForegroundColor Gray
    az bot create `
        --name $BotName `
        --resource-group $ResourceGroup `
        --sku $Sku `
        --location $Location `
        --app-type UserAssignedMSI `
        --appid $miClientId `
        --tenant-id $tenantId `
        --msi-resource-id $miResourceId `
        --endpoint $Endpoint `
        --output none
    Write-Host "✅ Azure Bot created" -ForegroundColor Green
}

Write-Host "💬 Step 5: Enabling Microsoft Teams channel..." -ForegroundColor Yellow
$teamsEnable = az bot msteams create `
    --name $BotName `
    --resource-group $ResourceGroup `
    --is-enabled true `
    --enable-calling false 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Teams channel enabled" -ForegroundColor Green
} else {
    Write-Host "⚠️  Unable to enable Teams channel automatically (may already be enabled)." -ForegroundColor Yellow
    Write-Host "   Azure CLI output:`n$teamsEnable" -ForegroundColor DarkGray
}

Write-Host "📦 Step 6: Summary" -ForegroundColor Yellow
Write-Host "   Bot Name   : $BotName" -ForegroundColor White
Write-Host "   Endpoint   : $Endpoint" -ForegroundColor White
Write-Host "   App ID     : $miClientId" -ForegroundColor White
Write-Host "   Tenant ID  : $tenantId" -ForegroundColor White
Write-Host "   Resource ID: $miResourceId" -ForegroundColor White

Write-Host "`n$('=' * 80)" -ForegroundColor Cyan
Write-Host "✅ Azure Bot deployment script completed" -ForegroundColor Green
Write-Host "$('=' * 80)" -ForegroundColor Cyan
