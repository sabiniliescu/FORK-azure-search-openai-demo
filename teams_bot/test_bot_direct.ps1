#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test Teams Bot locally with direct HTTP POST
#>

$botUrl = "http://localhost:3978/api/messages"

Write-Host "🤖 Testing Teams Bot at $botUrl`n" -ForegroundColor Cyan

# Create a Bot Framework Activity (same structure Bot Emulator uses)
$activity = @{
    type = "message"
    id = "test-message-$(Get-Date -Format 'yyyyMMddHHmmss')"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    channelId = "emulator"
    serviceUrl = "http://localhost:3978"  # Required for sending responses
    from = @{
        id = "test-user-123"
        name = "Test User"
    }
    conversation = @{
        id = "test-conversation-456"
        name = "Test Conversation"
    }
    recipient = @{
        id = "bot-789"
        name = "MihAI Bot"
    }
    text = "Salut! Ce poti sa-mi spui despre companie?"
    locale = "ro-RO"
} | ConvertTo-Json -Depth 10

Write-Host "📤 Sending message to bot..." -ForegroundColor Yellow
Write-Host $activity -ForegroundColor Gray

try {
    $response = Invoke-WebRequest `
        -Uri $botUrl `
        -Method POST `
        -Body $activity `
        -ContentType "application/json; charset=utf-8" `
        -UseBasicParsing `
        -TimeoutSec 30

    Write-Host "`n✅ Bot responded with status: $($response.StatusCode)" -ForegroundColor Green
    
    if ($response.Content) {
        Write-Host "`n📥 Response body:" -ForegroundColor Cyan
        $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
    }

} catch {
    Write-Host "`n❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "`nResponse body:" -ForegroundColor Yellow
        Write-Host $responseBody -ForegroundColor Gray
    }
}

Write-Host "`n💡 If this works, the bot is functioning correctly!" -ForegroundColor Yellow
Write-Host "   Problem is with Bot Emulator configuration (Direct Line vs direct connection)" -ForegroundColor Yellow
