# 🤖 Bot Framework Emulator - Setup & Troubleshooting

## Quick Fix: Testare Bot Local

### Problema: "Nu mai merge aplicația în Bot Emulator"

Bot-ul tău rulează corect local pe `http://localhost:3978`, dar trebuie configurat corect în Emulator.

---

## ✅ Pas cu Pas: Configurare Bot Emulator

### 1. Descarcă Bot Framework Emulator (dacă nu-l ai)

**Link direct:** https://github.com/Microsoft/BotFramework-Emulator/releases/latest

**Versiune recomandată:** `Bot-Framework-Emulator-4.14.1-windows-setup.exe` (sau mai nou)

**Instalare:**
```powershell
# Download și instalează din browser
# SAU cu winget:
winget install Microsoft.BotFrameworkEmulator
```

### 2. Asigură-te că bot-ul rulează local

```powershell
cd C:\Users\sabin.iliescu\Desktop\MIS_Local\AI\1REPOS\1azure-search-openai-demo\MihAI-Web\teams_bot

# Pornește bot-ul
python app.py
```

Verifică output-ul - ar trebui să vezi:
```
======================================================================
🤖 Starting Teams Bot on port 3978
======================================================================
📍 Backend URL: http://localhost:50505
📍 Bot endpoint: http://localhost:3978/api/messages
💚 Health: http://localhost:3978/health
🔐 App ID: Empty (dev mode)
======================================================================
```

### 3. Verifică Health Endpoint

Într-un browser, deschide:
```
http://localhost:3978/health
```

Ar trebui să vezi:
```json
{"status": "healthy", "service": "teams-bot"}
```

✅ Dacă vezi asta → Bot-ul rulează corect!

### 4. Configurare în Bot Emulator

#### Opțiunea A: Quick Connect (pentru development local)

1. **Deschide Bot Framework Emulator**
2. Click pe **"Open Bot"** (buton mare albastru)
3. În câmpul **"Bot URL"**, introdu:
   ```
   http://localhost:3978/api/messages
   ```
4. **Lasă goale** câmpurile:
   - Microsoft App ID
   - Microsoft App Password
   
   (pentru testare locală, nu sunt necesare!)

5. Click **"Connect"**

#### Opțiunea B: Salvează Bot Configuration (recomandat)

1. **File** → **New Bot Configuration**
2. Completează:
   - **Bot name:** `MihAI Teams Bot (Local)`
   - **Endpoint URL:** `http://localhost:3978/api/messages`
   - **Microsoft App ID:** *lasă gol*
   - **Microsoft App Password:** *lasă gol*
3. **Save as:** `mihai-teams-bot-local.bot`
4. Click **"Connect"**

---

## 🐛 Troubleshooting: Erori Comune

### Eroare: "Failed to connect to bot"

**Cauze posibile:**

1. **Bot-ul nu rulează**
   ```powershell
   # Verifică dacă bot-ul rulează
   curl http://localhost:3978/health
   ```
   
   Dacă primești eroare → pornește bot-ul cu `python app.py`

2. **Port-ul este diferit**
   
   Verifică în `.env`:
   ```properties
   PORT=3978  # Trebuie să fie același în Emulator!
   ```

3. **Backend-ul nu rulează**
   
   Verifică dacă backend-ul (localhost:50505) este pornit:
   ```powershell
   curl http://localhost:50505/health
   # SAU
   curl http://localhost:50505
   ```
   
   Dacă primești eroare → pornește backend-ul mai întâi!

### Eroare: "401 Unauthorized"

**Fix:** Asigură-te că în Emulator ai lăsat **goale** câmpurile:
- Microsoft App ID
- Microsoft App Password

Pentru testare locală, **NU** trebuie să completezi aceste câmpuri!

### Eroare: "500 Internal Server Error"

**Verifică logs bot-ului:**

În terminalul unde rulează `python app.py`, caută erori ca:
```
ERROR - Error: ...
```

**Cazuri comune:**

1. **Backend nu răspunde**
   ```
   Error: Cannot connect to backend at http://localhost:50505
   ```
   
   **Fix:** Pornește backend-ul mai întâi!

2. **Eroare în bot.py**
   ```python
   # Verifică backend_client.py
   # Verifică că backend URL este corect
   ```

### Eroare: "Emulator crashes sau nu se conectează"

**Fix 1: Restart Emulator**
```powershell
# Închide Emulator complet (Task Manager dacă e nevoie)
# Repornește-l
```

**Fix 2: Șterge cache**
```powershell
# Șterge folder-ul de cache Emulator
Remove-Item "$env:APPDATA\botframework-emulator" -Recurse -Force
# Repornește Emulator-ul
```

**Fix 3: Reinstalează Emulator**
```powershell
winget uninstall Microsoft.BotFrameworkEmulator
winget install Microsoft.BotFrameworkEmulator
```

---

## 🔍 Verificare Completă: Checklist

Urmează pașii în ordine:

### ✅ Step 1: Backend rulează?

```powershell
# Terminal 1: Pornește backend
cd C:\Users\sabin.iliescu\Desktop\MIS_Local\AI\1REPOS\1azure-search-openai-demo\MihAI-Web\app\backend
python main.py
# SAU dacă folosești Docker/azd:
azd up
```

Verifică:
```powershell
curl http://localhost:50505/health
# Ar trebui să vezi răspuns JSON
```

### ✅ Step 2: Bot rulează?

```powershell
# Terminal 2: Pornește bot-ul
cd C:\Users\sabin.iliescu\Desktop\MIS_Local\AI\1REPOS\1azure-search-openai-demo\MihAI-Web\teams_bot
python app.py
```

Verifică:
```powershell
curl http://localhost:3978/health
# Ar trebui să vezi: {"status": "healthy", "service": "teams-bot"}
```

### ✅ Step 3: .env configurat corect?

```properties
# teams_bot/.env
MICROSOFT_APP_ID=          # GOL pentru local testing
MICROSOFT_APP_PASSWORD=    # GOL pentru local testing
BACKEND_URL=http://localhost:50505/
PORT=3978
```

### ✅ Step 4: Emulator configurat corect?

1. **Bot URL:** `http://localhost:3978/api/messages`
2. **App ID:** *gol*
3. **App Password:** *gol*
4. **Locale:** `ro-RO` (opțional)

### ✅ Step 5: Testează conexiunea

În Emulator, trimite un mesaj:
```
Salut!
```

Ar trebui să primești răspuns de la MihAI backend.

---

## 📊 Flow Complet de Testare

```
┌─────────────────┐
│  Bot Emulator   │
│  (localhost)    │
└────────┬────────┘
         │ HTTP POST
         ▼
┌─────────────────────────┐
│  Teams Bot (app.py)     │
│  localhost:3978         │
│  /api/messages          │
└────────┬────────────────┘
         │ HTTP GET/POST
         ▼
┌─────────────────────────┐
│  MihAI Backend          │
│  localhost:50505        │
│  /chat, /documents      │
└─────────────────────────┘
```

**Ambele trebuie să ruleze simultan!**

---

## 🚀 Script Quick Start

Salvează ca `start_local_testing.ps1`:

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start both backend and bot for local testing
#>

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting MihAI Local Testing Environment`n" -ForegroundColor Cyan

# Check if backend is running
Write-Host "📡 Checking backend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:50505/health" -TimeoutSec 2 -UseBasicParsing
    Write-Host "✅ Backend is already running!" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend not running!" -ForegroundColor Red
    Write-Host "   Please start backend first:" -ForegroundColor Yellow
    Write-Host "   cd app\backend" -ForegroundColor White
    Write-Host "   python main.py" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Start bot
Write-Host "`n🤖 Starting Teams Bot..." -ForegroundColor Yellow
cd teams_bot
python app.py

# If we get here, bot stopped
Write-Host "`n⚠️ Bot stopped" -ForegroundColor Yellow
```

**Folosire:**
```powershell
# Terminal 1: Start backend
cd app\backend
python main.py

# Terminal 2: Run script
.\start_local_testing.ps1
```

---

## 🎯 Quick Reference

| Endpoint | URL | Descriere |
|----------|-----|-----------|
| Backend Health | http://localhost:50505/health | Verifică backend |
| Backend Chat | http://localhost:50505/chat | API chat |
| Bot Health | http://localhost:3978/health | Verifică bot |
| Bot Messages | http://localhost:3978/api/messages | Bot endpoint |

---

## 📞 Next Steps

După ce bot-ul funcționează local:

1. **Testează în Emulator** → Verifică că răspunsurile sunt corecte
2. **Deploy pe Azure** → Folosește `deploy_with_managed_identity.ps1`
3. **Configurează Bot Service** → Conectează-l la Web App
4. **Adaugă în Teams** → Upload manifest

**Pentru deployment pe Azure:**
- Vezi: `DEPLOY_MANUAL.md`
- SAU: `deploy_with_managed_identity.ps1`

---

## 💡 Tips

- **Folosește 2 terminale:** unul pentru backend, unul pentru bot
- **Verifică logs:** ambele aplicații loghează în console
- **Health checks:** verifică mereu `/health` endpoints
- **Emulator settings:** Lasă App ID și Password goale pentru local!
- **BACKEND_URL:** Asigură-te că are `/` la final: `http://localhost:50505/`

---

## 📚 Resources

- **Bot Emulator Releases:** https://github.com/Microsoft/BotFramework-Emulator/releases
- **Bot Framework Docs:** https://docs.microsoft.com/en-us/azure/bot-service/
- **Debugging Guide:** https://docs.microsoft.com/en-us/azure/bot-service/bot-service-debug-emulator

---

**Ultima actualizare:** 2025-10-06
**Autor:** MihAI Teams Bot Setup Guide
