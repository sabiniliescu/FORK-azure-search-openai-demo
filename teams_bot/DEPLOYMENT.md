# Deployment Guide: Teams Bot pentru Azure Search OpenAI Demo

Acest ghid te va ajuta să deploiezi bot-ul Teams care se integrează cu backend-ul existent Azure OpenAI RAG.

## Prerequisite

1. **Subscription Azure activ** cu permisiuni de deployment
2. **Backend-ul deja deployed** - aplicația principală trebuie să fie deja funcțională în Azure
3. **Azure CLI** instalat și configurat
4. **PowerShell 7+** (pentru Windows)
5. **Permisiuni în Microsoft Teams** pentru a publica aplicații custom

## Pas 1: Înregistrare Azure Bot

### 1.1 Creează o Azure AD App Registration

```powershell
# Loginează-te în Azure
az login

# Setează subscription-ul activ
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Creează App Registration pentru bot
$appName = "TeamsBot-RAG-Assistant"
$app = az ad app create --display-name $appName --query "{appId:appId}" -o json | ConvertFrom-Json

# Salvează App ID
$appId = $app.appId
Write-Host "Microsoft App ID: $appId"

# Creează un client secret
$secret = az ad app credential reset --id $appId --append --query password -o tsv
Write-Host "Microsoft App Password: $secret"
Write-Host "IMPORTANT: Salvează acest password! Nu va mai fi afișat!"
```

### 1.2 Configurează permisiunile

```powershell
# Adaugă permisiunile necesare pentru bot
az ad app permission add --id $appId --api 00000003-0000-0000-c000-000000000000 --api-permissions e1fe6dd8-ba31-4d61-89e7-88639da4683d=Scope

# Grant admin consent (dacă ai permisiuni)
az ad app permission admin-consent --id $appId
```

## Pas 2: Configurare Variabile de Mediu

Creează un fișier `.env` în directorul `teams_bot/`:

```bash
# Copiază template-ul
cp teams_bot/.env.example teams_bot/.env
```

Editează `.env` și completează:

```bash
# Microsoft Bot Framework
MICROSOFT_APP_ID=<App-ID-din-pasul-1>
MICROSOFT_APP_PASSWORD=<Password-din-pasul-1>

# Backend URL (URL-ul backend-ului tău deployed)
BACKEND_URL=https://your-backend-app.azurecontainerapps.io

# Port (default pentru bots)
PORT=3978
```

**IMPORTANT:** Găsește `BACKEND_URL`:
```powershell
# Dacă ai folosit azd pentru deployment
azd env get-values | Select-String "SERVICE_BACKEND_URI"

# Sau în Azure Portal
# Navighează la Container Apps → selectează backend-ul → Overview → Application Url
```

## Pas 3: Configurare Deployment Azure

### 3.1 Setează variabilele azd

```powershell
# Setează resource group (folosește același cu backend-ul)
azd env set AZURE_RESOURCE_GROUP "rg-your-resource-group"

# Setează location
azd env set AZURE_LOCATION "eastus"

# Setează credențialele botului
azd env set MICROSOFT_APP_ID "<your-app-id>"
azd env set MICROSOFT_APP_PASSWORD "<your-app-password>" --secret

# Setează backend URL
azd env set BACKEND_URL "https://your-backend-app.azurecontainerapps.io"
```

## Pas 4: Deploy Bot în Azure

### Opțiunea A: Folosind scriptul de deployment

```powershell
# Rulează scriptul de deployment
.\scripts\deploy_teams_bot.ps1
```

### Opțiunea B: Manual cu Azure CLI

```powershell
# 1. Creează Resource Group (dacă nu există)
az group create --name "rg-teams-bot" --location "eastus"

# 2. Deploy infrastructura
az deployment group create \
  --resource-group "rg-teams-bot" \
  --template-file "./infra/teams-bot.bicep" \
  --parameters "./infra/teams-bot.parameters.json" \
  --parameters microsoftAppId=$appId microsoftAppPassword=$secret

# 3. Deploy codul
cd teams_bot
az webapp up --name "teamsbot-your-name" --resource-group "rg-teams-bot" --runtime "PYTHON:3.11"
```

## Pas 5: Configurare Teams App Manifest

### 5.1 Generează UUID-uri

```powershell
# Generează Teams App ID
$teamsAppId = [guid]::NewGuid().ToString()
Write-Host "Teams App ID: $teamsAppId"
```

### 5.2 Actualizează manifest-ul

Editează `teams_bot/manifest/manifest.json`:

1. Înlocuiește `{{TEAMS_APP_ID}}` cu UUID-ul generat
2. Înlocuiește `{{MICROSOFT_APP_ID}}` cu App ID-ul din Pas 1
3. Înlocuiește `{{BOT_DOMAIN}}` cu domeniul web app-ului (ex: `teamsbot-yourname.azurewebsites.net`)

Exemplu:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "bots": [
    {
      "botId": "12345678-1234-1234-1234-123456789012",
      ...
    }
  ],
  "validDomains": [
    "teamsbot-yourname.azurewebsites.net"
  ],
  "webApplicationInfo": {
    "id": "12345678-1234-1234-1234-123456789012",
    "resource": "api://teamsbot-yourname.azurewebsites.net/12345678-1234-1234-1234-123456789012"
  }
}
```

### 5.3 Adaugă iconițe

Plasează două imagini în `teams_bot/manifest/`:
- `color.png` - 192x192 px (icon color pentru Teams)
- `outline.png` - 32x32 px (icon outline pentru Teams)

Poți crea iconițe simple sau folosi un generator online.

### 5.4 Creează pachetul Teams

```powershell
# Din directorul teams_bot/manifest
cd teams_bot/manifest
Compress-Archive -Path manifest.json,color.png,outline.png -DestinationPath ../teams-app.zip -Force
cd ../..
```

## Pas 6: Publish în Microsoft Teams

### 6.1 Upload aplicația

1. Deschide **Microsoft Teams**
2. Click pe **Apps** în sidebar-ul stâng
3. Click pe **Manage your apps** (jos)
4. Click pe **Upload an app** → **Upload a custom app**
5. Selectează `teams_bot/teams-app.zip`

### 6.2 Testează bot-ul

1. După upload, click pe aplicație
2. Click **Add** pentru a adăuga bot-ul
3. Începe o conversație:
   - "Care sunt beneficiile companiei?"
   - "Spune-mi despre politica de concediu"
   - "Ce posturi sunt disponibile?"

## Pas 7: Verificare și Debugging

### Verifică că bot-ul funcționează

```powershell
# Check health endpoint
curl https://teamsbot-yourname.azurewebsites.net/health

# Vezi logs
az webapp log tail --name "teamsbot-yourname" --resource-group "rg-teams-bot"
```

### Probleme comune

**Bot nu răspunde:**
- Verifică că `BACKEND_URL` este corect în configurare
- Verifică că backend-ul este accesibil
- Verifică logs: `az webapp log tail`

**Erori de autentificare:**
- Verifică că `MICROSOFT_APP_ID` și `MICROSOFT_APP_PASSWORD` sunt corecte
- Verifică că endpoint-ul botului este configurat corect în Azure Bot Service

**Teams nu găsește bot-ul:**
- Verifică că manifestul are UUID-uri valide
- Verifică că domeniul este adăugat în `validDomains`

## Pas 8: (Opțional) Publish pentru Organizație

Pentru a face bot-ul disponibil pentru toată organizația:

1. **Obține aprobare de la IT Admin**
2. **Upload în Teams Admin Center:**
   - Navighează la [Teams Admin Center](https://admin.teams.microsoft.com)
   - **Teams apps** → **Manage apps** → **Upload**
   - Selectează `teams-app.zip`
3. **Setează politici:**
   - Configurează cine poate vedea și folosi aplicația
   - Setează permisiuni și constrângeri

## Arhitectură Finală

```
┌─────────────────┐
│ Microsoft Teams │
│   (Frontend)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Teams Bot     │
│  (Azure App)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Backend API    │
│ (Existing RAG)  │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│ Azure  │ │  Azure   │
│OpenAI  │ │AI Search │
└────────┘ └──────────┘
```

## Resurse Adiționale

- [Bot Framework Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Teams App Manifest Schema](https://docs.microsoft.com/en-us/microsoftteams/platform/resources/schema/manifest-schema)
- [Azure Bot Service](https://azure.microsoft.com/en-us/services/bot-services/)

## Suport

Pentru probleme sau întrebări:
- Verifică [troubleshooting section](#pas-7-verificare-și-debugging)
- Consultă logs-urile Azure
- Verifică documentația Microsoft Teams Platform
