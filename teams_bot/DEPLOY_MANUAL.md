# Deployment Manual pentru Teams Bot

## ⚠️ IMPORTANT: Deployment Simplificat fără Managed Identity

Deoarece nu ai permisiuni pentru a crea Azure AD App Registration prin script, vei urma acești pași:

## Pas 1: Creează Azure App Registration Manual

1. **Deschide Azure Portal**: https://portal.azure.com
2. **Navighează la**: Azure Active Directory → App registrations → New registration
3. **Completează**:
   - Name: `mihai-teams-bot`
   - Supported account types: `Accounts in this organizational directory only`
   - Redirect URI: Leave empty
4. **Click**: Register

## Pas 2: Creează Client Secret

1. **În App Registration** pe care tocmai ai creat-o:
   - Du-te la: Certificates & secrets → New client secret
   - Description: `teams-bot-secret`
   - Expires: 24 months (sau la alegere)
2. **IMPORTANT**: **COPIAZĂ IMEDIAT** valoarea secretului (Value) - o vei folosi la pasul următor!
   - ⚠️ Nu vei mai putea vedea această valoare după ce părăsești pagina!
3. **Copiază și Application (client) ID** de pe pagina Overview

## Pas 3: Configurează .env

Editează fișierul `teams_bot/.env`:

```bash
# Înlocuiește cu valorile tale
MICROSOFT_APP_ID=<Application-client-ID-de-la-pas-2>
MICROSOFT_APP_PASSWORD=<Secret-value-de-la-pas-2>

# Backend URL - obține-l cu: azd env get-value BACKEND_URI
BACKEND_URL=https://capps-backend-dcnxgznrq3wmc.happyground-5a8ca1ce.eastus.azurecontainerapps.io
```

## Pas 4: Deploy cu azd

```powershell
# Setează flag pentru deployment de Teams bot
azd env set DEPLOY_TEAMS_BOT true

# Setează App ID și Password
azd env set TEAMS_BOT_APP_ID "<Application-client-ID-de-la-pas-2>"
azd env set TEAMS_BOT_APP_PASSWORD "<Secret-value-de-la-pas-2>"

# Deploy infrastructure (va crea Web App și Bot Service)
azd provision

# Deploy doar serviciul teamsbot
azd deploy teamsbot
```

**SAU** dacă vrei să deploy-ezi doar infrastructura fără să modifici backend-ul:

```powershell
# Deploy doar Teams bot infrastructure
az deployment group create \
  --resource-group rg-azure-search-openai-demo \
  --template-file infra/teams-bot.bicep \
  --parameters botName=mihai-teams-bot \
               appServicePlanName=plan-teams-bot \
               webAppName=app-teams-bot \
               microsoftAppId="<Application-client-ID>" \
               microsoftAppPassword="<Secret-value>" \
               backendUrl="$(azd env get-value BACKEND_URI)"
```

## Pas 5: Creează Bot Channel Registration

După ce deployment-ul este gata, obține URL-ul Web App:

```powershell
$webAppUrl = az webapp show --name teamsbot-mihai --resource-group rg-azure-search-openai-demo --query defaultHostName -o tsv
echo "https://$webAppUrl/api/messages"
```

### În Azure Portal:

1. **Creează Bot Channel Registration**:
   - Go to: Create a resource → AI + Machine Learning → Azure Bot
   - Bot handle: `mihai-teams-bot`
   - Subscription: Alege subscription-ul tău
   - Resource Group: `rg-azure-search-openai-demo` (sau la ce folosești)
   - Pricing tier: F0 (Free)
   - Microsoft App ID: Alege "Use existing app registration"
   - App ID: `<Application-client-ID-de-la-pas-2>`
   - Click: Create

2. **Configurează Messaging endpoint**:
   - În Bot Channel Registration → Configuration
   - Messaging endpoint: `https://<webAppUrl-de-mai-sus>/api/messages`
   - Click: Apply

3. **Activează Teams Channel**:
   - În Bot Channel Registration → Channels
   - Click pe Microsoft Teams icon
   - Click: Save

## Pas 6: Testează în Teams

1. **În Bot Channel Registration → Channels → Microsoft Teams**
2. Click pe "Open in Teams"
3. Începe conversația cu botul!

## Troubleshooting

### Bot nu răspunde
```powershell
# Verifică logs
az webapp log tail --name teamsbot-mihai --resource-group rg-azure-search-openai-demo
```

### 401 Unauthorized
- Verifică că App ID și Password sunt corecte în .env
- Verifică că messaging endpoint este corect configurat
- Verifică că botul are același App ID ca în App Registration

### Backend connection failed
```powershell
# Testează backend
curl https://capps-backend-dcnxgznrq3wmc.happyground-5a8ca1ce.eastus.azurecontainerapps.io/health
```

## Alternative: Deploy manual complet

Dacă azd deploy nu funcționează, poți face deploy manual:

```powershell
cd teams_bot

# Creează ZIP
Compress-Archive -Path .\* -DestinationPath teams-bot.zip -Force

# Deploy
az webapp deployment source config-zip --name teamsbot-mihai --resource-group rg-azure-search-openai-demo --src teams-bot.zip

# Configurează environment variables
az webapp config appsettings set --name teamsbot-mihai --resource-group rg-azure-search-openai-demo --settings MICROSOFT_APP_ID="<app-id>" MICROSOFT_APP_PASSWORD="<password>" BACKEND_URL="<backend-url>"
```

## Notă Importantă

Acest approach folosește **App Registration** traditional în loc de Managed Identity pentru că:
- Bot Framework SDK pentru Python nu suportă direct Managed Identity
- Ai nevoie de permisiuni de Global Administrator pentru Managed Identity cu Bot Service
- Approach-ul traditional funcționează și este mai simplu de configurat

Dacă în viitor vrei să folosești Managed Identity, va trebui:
1. Upgrade la Bot Framework SDK care suportă Managed Identity
2. Configurare certificate authentication
3. Permission de Global Admin în Azure AD
