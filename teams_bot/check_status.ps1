#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick check: Ce rulează și ce trebuie pornit?
    
.DESCRIPTION
    Verifică rapid dacă backend și bot rulează local
#>

$ErrorActionPreference = "Stop"

Write-Host "`n" -NoNewline
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "🔍 MihAI Local Development - Status Check" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

# Check 1: Backend
Write-Host "`n📡 Backend (localhost:50505)..." -ForegroundColor Yellow -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:50505/" -UseBasicParsing -TimeoutSec 2
    Write-Host " ✅ RUNNING" -ForegroundColor Green
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Gray
    Write-Host "   Response: $(if($response.Content.Length -gt 50) { $response.Content.Substring(0,50) + '...' } else { $response.Content })" -ForegroundColor Gray
} catch {
    Write-Host " ❌ NOT RUNNING" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host "`n   💡 To start backend:" -ForegroundColor Yellow
    Write-Host "      cd app" -ForegroundColor White
    Write-Host "      .\start.ps1" -ForegroundColor White
}

# Check 2: Teams Bot
Write-Host "`n🤖 Teams Bot (localhost:3978)..." -ForegroundColor Yellow -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3978/health" -UseBasicParsing -TimeoutSec 2
    $content = $response.Content | ConvertFrom-Json
    Write-Host " ✅ RUNNING" -ForegroundColor Green
    Write-Host "   Status: $($content.status)" -ForegroundColor Gray
    Write-Host "   Service: $($content.service)" -ForegroundColor Gray
} catch {
    Write-Host " ❌ NOT RUNNING" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host "`n   💡 To start bot:" -ForegroundColor Yellow
    Write-Host "      cd teams_bot" -ForegroundColor White
    Write-Host "      python app.py" -ForegroundColor White
}

# Summary
Write-Host "`n" -NoNewline
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "📋 Quick Commands:" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

Write-Host "`n1️⃣  Start Backend (Terminal 1):" -ForegroundColor Yellow
Write-Host "   cd app" -ForegroundColor White
Write-Host "   .\start.ps1" -ForegroundColor White

Write-Host "`n2️⃣  Start Bot (Terminal 2):" -ForegroundColor Yellow
Write-Host "   cd teams_bot" -ForegroundColor White
Write-Host "   python app.py" -ForegroundColor White

Write-Host "`n3️⃣  Connect Bot Emulator:" -ForegroundColor Yellow
Write-Host "   Bot URL: http://localhost:3978/api/messages" -ForegroundColor White
Write-Host "   App ID: (leave empty)" -ForegroundColor Gray
Write-Host "   App Password: (leave empty)" -ForegroundColor Gray

Write-Host "`n" -NoNewline
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
