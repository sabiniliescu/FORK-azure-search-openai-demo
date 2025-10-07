# Script pentru verificarea instalării pyodbc după azd deploy
Write-Host "🔍 Verificarea instalării pyodbc în Azure..." -ForegroundColor Yellow

# Extrage URL-ul backend din output-ul azd deploy
$backendUrl = "https://capps-backend-dcnxgznrq3wmc.happyground-5a8ca1ce.eastus.azurecontainerapps.io"

Write-Host "📡 Testez endpoint-ul: $backendUrl" -ForegroundColor Cyan

try {
    # Fac o cerere către /config pentru a vedea log-urile de startup
    $response = Invoke-RestMethod -Uri "$backendUrl/config" -Method GET -TimeoutSec 30
    Write-Host "✅ Aplicația răspunde!" -ForegroundColor Green
    
    # Verific log-urile din Azure Container Apps
    Write-Host "📋 Verificând log-urile Azure pentru mesajele pyodbc..." -ForegroundColor Cyan
    
    # Instrucțiuni pentru utilizator
    Write-Host ""
    Write-Host "🔍 VERIFICARE MANUALĂ NECESARĂ:" -ForegroundColor Yellow
    Write-Host "1. Deschide Azure Portal: https://portal.azure.com" -ForegroundColor White
    Write-Host "2. Navighează la Container Apps > capps-backend-xxx" -ForegroundColor White
    Write-Host "3. Mergi la 'Monitoring' > 'Log stream' sau 'Logs'" -ForegroundColor White
    Write-Host "4. Caută în log-uri unul din aceste mesaje:" -ForegroundColor White
    Write-Host ""
    Write-Host "   ✅ SUCCES - ar trebui să vezi:" -ForegroundColor Green
    Write-Host "   🎉 [DATABASE SUCCESS] pyodbc v5.2.0 INSTALAT CU SUCCES!" -ForegroundColor Green
    Write-Host "   ✅ [DATABASE] Azure SQL Database connectivity: ENABLED" -ForegroundColor Green
    Write-Host ""
    Write-Host "   ❌ EȘEC - dacă vezi:" -ForegroundColor Red
    Write-Host "   ❌ [DATABASE ERROR] pyodbc NU ESTE INSTALAT!" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 TIP: Poți testa și făcând un chat în aplicație și urmărind log-urile." -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Eroare la conectarea la aplicație: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "⏳ Aplicația poate să nu fie încă gata. Încearcă din nou în 1-2 minute." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Pentru a testa complet database logging-ul:" -ForegroundColor Cyan
Write-Host "1. Deschide aplicația în browser: $backendUrl" -ForegroundColor White
Write-Host "2. Fă un chat test" -ForegroundColor White
Write-Host "3. Verifică log-urile Azure pentru mesajele de succes" -ForegroundColor White
