# 🚀 Teams Bot - Deployment Guide

## Rezumat

Teams bot-ul MihAI comunică cu backend-ul Azure pentru a răspunde la întrebările utilizatorilor din Microsoft Teams.

**2 Opțiuni de Deployment:**

1. **[RECOMANDAT] Deployment Manual Simplificat** - Vezi `DEPLOY_MANUAL.md`
2. **Deployment cu azd** - Integrare completă (vezi mai jos)

---

## Opțiunea 1: Deployment Manual (RECOMANDAT)

✅ **Avantaje:**
- Mai simplu și mai rapid
- Nu necesită modificări la infrastructure
- Controlezi exact ce se întâmplă

📖 **Ghid Complet:** [`DEPLOY_MANUAL.md`](./DEPLOY_MANUAL.md)

**Pe scurt:**
1. Creezi App Registration în Azure Portal
2. Copiezi App ID și Secret
3. Deploy manual cu `az webapp` sau prin Azure Portal
4. Configurezi Bot Channel Registration
5. Activezi Teams Channel

---

## Opțiunea 2: Deployment cu azd

✅ **Avantaje:**
- Integrare completă cu restul proiectului
- Infrastructure as Code (Bicep)
- Deployment automatizat

⚠️ **Dezavantaje:**
- Tot trebuie să creezi App Registration manual
- Mai complex de configurat
- Poate modifica infrastructure existentă

### Pași:

#### 1. Creează App Registration (manual)
Vezi pasii 1-2 din `DEPLOY_MANUAL.md`

#### 2. Configurează azd environment

```powershell
# Activează deployment de Teams bot
azd env set DEPLOY_TEAMS_BOT true

# Setează credentials
azd env set TEAMS_BOT_APP_ID "<your-app-id>"
azd env set TEAMS_BOT_APP_PASSWORD "<your-secret>"
```

#### 3. Deploy infrastructure și cod

```powershell
# Varianta 1: Deploy complet (backend + teamsbot)
azd up

# Varianta 2: Deploy doar Teams bot
azd provision  # Creează infrastructure
azd deploy teamsbot  # Deploy doar cod Teams bot
```

#### 4. Obține Bot Endpoint

```powershell
# Obține URL-ul botului
azd env get-value TEAMS_BOT_ENDPOINT
```

#### 5. Configurează Bot Channel Registration

Vezi pasul 5 din `DEPLOY_MANUAL.md`

---

## Verificare Deployment

```powershell
# Check health endpoint
$botUrl = azd env get-value TEAMS_BOT_URL
curl "$botUrl/health"

# Expected response:
# {"status": "healthy", "service": "teams-bot"}
```

## Logs și Troubleshooting

```powershell
# Get Web App name
$webAppName = azd env get-value TEAMS_BOT_WEBAPP_NAME

# Stream logs
az webapp log tail --name $webAppName --resource-group $(azd env get-value AZURE_RESOURCE_GROUP)

# Download logs
az webapp log download --name $webAppName --resource-group $(azd env get-value AZURE_RESOURCE_GROUP)
```

## Common Issues

### Bot nu răspunde în Teams
1. **Verifică App ID și Password**
   ```powershell
   az webapp config appsettings list --name $webAppName --resource-group $(azd env get-value AZURE_RESOURCE_GROUP) | Select-String "MICROSOFT_APP"
   ```

2. **Verifică Messaging Endpoint** în Bot Channel Registration
   - Trebuie să fie: `https://<your-webapp>.azurewebsites.net/api/messages`
   - Verifică că endpoint-ul este "Enabled"

3. **Verifică Backend URL**
   ```powershell
   # Botul trebuie să poată accesa backend-ul
   az webapp config appsettings list --name $webAppName --resource-group $(azd env get-value AZURE_RESOURCE_GROUP) | Select-String "BACKEND_URL"
   ```

### 500 Internal Server Error

```powershell
# Check logs pentru detalii
az webapp log tail --name $webAppName --resource-group $(azd env get-value AZURE_RESOURCE_GROUP)
```

Cauze comune:
- Backend URL gresit sau inaccesibil
- App ID/Password gresit
- Lipsesc dependencies în requirements.txt

### Build Failed

```powershell
# Verifică build logs
az webapp log deployment show --name $webAppName --resource-group $(azd env get-value AZURE_RESOURCE_GROUP)
```

**Soluție:** Verifică că toate package-urile din `requirements.txt` sunt disponibile și compatibile.

---

## Next Steps

După deployment reușit:

1. **Testează botul** în Teams
2. **Configurează permissions** pentru utilizatori
3. **Monitorizează usage** prin Application Insights (dacă este activat)
4. **Actualizează documentația** cu URL-ul și detaliile specifice

---

## Resurse

- [Bot Framework Documentation](https://docs.microsoft.com/azure/bot-service/)
- [Teams Bot Development](https://docs.microsoft.com/microsoftteams/platform/bots/what-are-bots)
- [Azure Web App Deployment](https://docs.microsoft.com/azure/app-service/)
- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/)

---

## Support

Pentru probleme specifice proiectului, verifică:
- `DEPLOY_MANUAL.md` - Deployment manual pas cu pas
- `QUICKSTART.md` - Development local
- `../docs/` - Documentație backend
