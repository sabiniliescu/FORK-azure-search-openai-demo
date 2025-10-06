#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Alternative: Test bot cu Postman-style HTTP client
#>

Write-Host "🔧 Alternativă la Bot Emulator: Test direct cu HTTP`n" -ForegroundColor Cyan

$botUrl = "http://localhost:3978/api/messages"

# Create proper Bot Framework activity
$activity = @{
    type = "message"
    id = (New-Guid).ToString()
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
    channelId = "test"
    serviceUrl = "http://localhost:3978"
    from = @{
        id = "user1"
        name = "Test User"
    }
    conversation = @{
        id = "conversation1"
    }
    recipient = @{
        id = "bot"
    }
    text = "Salut! Spune-mi despre beneficiile companiei."
}

$json = $activity | ConvertTo-Json -Depth 10

Write-Host "📤 Sending to bot..." -ForegroundColor Yellow
Write-Host $json -ForegroundColor Gray

try {
    $response = Invoke-WebRequest `
        -Uri $botUrl `
        -Method POST `
        -Body $json `
        -ContentType "application/json; charset=utf-8" `
        -TimeoutSec 60

    Write-Host "`n✅ Status: $($response.StatusCode)" -ForegroundColor Green
    
    # Bot Framework returns activities as JSON array
    if ($response.Content) {
        Write-Host "`n📥 Response:" -ForegroundColor Cyan
        $activities = $response.Content | ConvertFrom-Json
        
        if ($activities -is [array]) {
            foreach ($act in $activities) {
                Write-Host "`nActivity Type: $($act.type)" -ForegroundColor Yellow
                if ($act.text) {
                    Write-Host "Text: $($act.text)" -ForegroundColor White
                }
            }
        } else {
            Write-Host $response.Content -ForegroundColor White
        }
    }

    Write-Host "`n✅ BOT FUNCȚIONEAZĂ CORECT!" -ForegroundColor Green
    Write-Host "Problema este DOAR cu Bot Emulator (Direct Line mode)`n" -ForegroundColor Yellow

} catch {
    Write-Host "`n❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        $errorBody = $reader.ReadToEnd()
        Write-Host "Response: $errorBody" -ForegroundColor Gray
    }
}

Write-Host "`n💡 Soluții pentru Bot Emulator:" -ForegroundColor Cyan
Write-Host "1. Folosește fișierul .bot: File → Open Bot Configuration → mihai-bot-local.bot" -ForegroundColor White
Write-Host "2. SAU update Bot Emulator la versiunea latest (4.14.1+)" -ForegroundColor White
Write-Host "3. SAU folosește ngrok pentru Direct Line testing`n" -ForegroundColor White
