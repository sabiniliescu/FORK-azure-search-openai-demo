# 🚀 Quick Start: Deploy Teams Bot în Azure

Acest ghid te ajută să deploiezi bot-ul Teams în Azure în mai puțin de 10 minute.

## Prerequisites

✅ **TREBUIE să ai:**
1. Azure subscription activ
2. Backend-ul deja deployed în Azure
3. Azure CLI instalat ([Download](https://aka.ms/installazurecliwindows))
4. PowerShell 7+ ([Download](https://github.com/PowerShell/PowerShell/releases))

## Deployment în 3 pași

### 📋 Pas 1: Găsește URL-ul backend-ului

```powershell
# Opțiunea A: Dacă ai folosit azd
cd ..  # Din teams_bot înapoi la root
azd env get-values | Select-String "SERVICE_BACKEND_URI"

# Opțiunea B: Din Azure Portal
# 1. Navighează la Azure Portal
# 2. Container Apps → selectează backend-ul
# 3. Overview → copiază "Application Url"
```

**Salvează URL-ul** (ex: `https://backend-app-xyz.azurecontainerapps.io`)

### 🔐 Pas 2: Login în Azure

```powershell
# Login în Azure
az login

# (Opțional) Setează subscription-ul activ
az account set --subscription "YOUR_SUBSCRIPTION_NAME"

# Verifică că ești autentificat
az account show
```

### 🚀 Pas 3: Rulează scriptul de deployment

```powershell
cd teams_bot

# Rulează deployment (înlocuiește valorile!)
.\deploy.ps1 `
    -ResourceGroupName "rg-teams-bot" `
    -AppName "teamsbot-mihai" `
    -BackendUrl "https://backend-app-xyz.azurecontainerapps.io"
```

**Parametri:**
- `ResourceGroupName`: Numele resource group-ului (se creează automat dacă nu există)
- `AppName`: Nume unic pentru bot (ex: teamsbot-prenume-nume)
- `BackendUrl`: URL-ul backend-ului din Pas 1

**Timpul de deployment:** ~5-7 minute ⏱️

### 📱 Pas 4: Instalează bot-ul în Teams

După ce deployment-ul s-a finalizat cu succes:

1. **Deschide Microsoft Teams**
2. Click pe **Apps** (sidebar stâng)
3. Click pe **Manage your apps** (jos)
4. Click pe **Upload a custom app** → **Upload for me or my teams**
5. Selectează fișierul: `teams_bot/teams-app.zip`
6. Click **Add** pentru a adăuga bot-ul
7. **Testează:** "Care sunt beneficiile companiei?"

## 🎉 Asta e tot!

Bot-ul tău este acum live în Teams și se conectează la backend-ul existent!

---

## ⚙️ Opțiuni avansate

### Folosirea unui resource group existent

```powershell
# Verifică resource groups existente
az group list --output table

# Deploy în același RG ca backend-ul
.\deploy.ps1 `
    -ResourceGroupName "rg-mihai-existing" `
    -AppName "teamsbot-mihai" `
    -BackendUrl "https://backend-app.azurecontainerapps.io"
```

### Skip Bot Registration (dacă ai deja App ID)

```powershell
# Dacă ai făcut deja înregistrarea și ai .env cu credențiale
.\deploy.ps1 `
    -ResourceGroupName "rg-teams-bot" `
    -AppName "teamsbot-mihai" `
    -BackendUrl "https://backend-app.azurecontainerapps.io" `
    -SkipBotRegistration
```

### Altă regiune Azure

```powershell
.\deploy.ps1 `
    -ResourceGroupName "rg-teams-bot" `
    -AppName "teamsbot-mihai" `
    -BackendUrl "https://backend-app.azurecontainerapps.io" `
    -Location "westeurope"
```

---

## 🔍 Verificare și Debugging

### Verifică că bot-ul funcționează

```powershell
# Test health endpoint
curl https://teamsbot-mihai.azurewebsites.net/health

# Vezi logs live
az webapp log tail --name teamsbot-mihai --resource-group rg-teams-bot

# Vezi configurația
az webapp config appsettings list --name teamsbot-mihai --resource-group rg-teams-bot
```

### Restart bot-ul

```powershell
az webapp restart --name teamsbot-mihai --resource-group rg-teams-bot
```

### Update backend URL

```powershell
az webapp config appsettings set `
    --name teamsbot-mihai `
    --resource-group rg-teams-bot `
    --settings BACKEND_URL="https://new-backend-url.azurecontainerapps.io"
```

---

## ❌ Probleme comune

### "Bot nu răspunde în Teams"

**Cauză:** Backend URL incorect sau backend-ul nu este accesibil

**Soluție:**
```powershell
# Verifică backend URL
az webapp config appsettings list --name teamsbot-mihai --resource-group rg-teams-bot | Select-String "BACKEND_URL"

# Testează backend-ul direct
curl https://backend-url/health
```

### "The name is already in use"

**Cauză:** Numele `AppName` este deja folosit de altcineva în Azure

**Soluție:**
```powershell
# Folosește un nume mai specific
.\deploy.ps1 `
    -ResourceGroupName "rg-teams-bot" `
    -AppName "teamsbot-prenume-nume-$(Get-Random -Maximum 9999)" `
    -BackendUrl "https://backend-app.azurecontainerapps.io"
```

### "Insufficient permissions"

**Cauză:** Nu ai permisiuni să creezi resurse în subscription

**Soluție:**
- Contactează Azure Admin pentru permisiuni
- SAU folosește un alt subscription: `az account set --subscription "AltSubscription"`

### "Teams App Package invalid"

**Cauză:** Iconițele lipsesc din `manifest/`

**Soluție:**
```powershell
# Creează iconițe simple sau downloadează template-uri
# color.png: 192x192 px
# outline.png: 32x32 px

# Plasează în: teams_bot/manifest/

# Re-creează package-ul
cd manifest
Compress-Archive -Path manifest.json,color.png,outline.png -DestinationPath ../teams-app.zip -Force
```

---

## 📚 Resurse

- **Deployment complet:** Vezi [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Link mapping:** Vezi [LINK_MAPPING.md](./LINK_MAPPING.md)
- **Backend:** [Azure Search OpenAI Demo](https://github.com/Azure-Samples/azure-search-openai-demo)

---

## 💡 Tips

1. **Numele AppName** trebuie să fie unic în toată Azure (nu doar în subscription-ul tău)
2. **Salvează credențialele** (App ID și Password) într-un password manager
3. **Testează local** înainte de deployment cu `python app.py`
4. **Monitoring:** Activează Application Insights pentru logs avansate

---

## 🆘 Suport

Dacă întâmpini probleme:

1. Verifică logs: `az webapp log tail --name <app-name> --resource-group <rg-name>`
2. Verifică [troubleshooting section](#-probleme-comune)
3. Consultă [DEPLOYMENT.md](./DEPLOYMENT.md) pentru detalii complete

---

**Succes! 🎉**
