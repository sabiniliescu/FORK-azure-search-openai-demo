# ⚡ Quick Start - Teams Bot Deployment

## TL;DR

```powershell
# 1. Creează App Registration în Azure Portal
# Azure Portal → Azure AD → App registrations → New registration
# Copiază: App ID și Secret

# 2. Deploy (alege una)

### Opțiunea A: Manual (cel mai simplu)
cd teams_bot
# Editează .env cu App ID și Secret
az webapp up --name teamsbot-mihai --runtime "PYTHON:3.11" --sku B1

### Opțiunea B: Cu azd (recomandat long-term)
azd env set DEPLOY_TEAMS_BOT true
azd env set TEAMS_BOT_APP_ID "<app-id>"
azd env set TEAMS_BOT_APP_PASSWORD "<secret>"
azd provision
azd deploy teamsbot

# 3. Configurează Bot în Portal
# Azure Portal → Bot Services → Create → Use existing app registration
# Set Messaging Endpoint: https://<your-app>.azurewebsites.net/api/messages

# 4. Activează Teams Channel
# Bot Service → Channels → Microsoft Teams → Save

# 5. Test în Teams
# Bot Service → Channels → Teams → Open in Teams
```

## Fișiere Importante

| Fișier | Scop |
|--------|------|
| `DEPLOY_MANUAL.md` | 📖 Ghid complet pas cu pas |
| `DEPLOYMENT_SUMMARY.md` | 📋 Explicație tehnică detaliată |
| `README_DEPLOYMENT.md` | 🚀 Overview deployment opțiuni |
| `infra/teams-bot.bicep` | 🏗️ Infrastructure as Code |

## Comenzi Utile

```powershell
# Health check
curl https://<your-app>.azurewebsites.net/health

# Logs
az webapp log tail --name <app-name> --resource-group <rg-name>

# Update code
azd deploy teamsbot

# Get backend URL
azd env get-value BACKEND_URI

# Environment variables
az webapp config appsettings list --name <app-name> --resource-group <rg-name>
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Bot nu răspunde | Verifică Messaging Endpoint în Bot Service |
| 401 Error | Verifică App ID și Password în Web App settings |
| 500 Error | Check logs: `az webapp log tail` |
| Build failed | Verifică `requirements.txt` |

## Prerequisites

- ✅ Azure Subscription
- ✅ Backend deployment activ (via `azd up`)
- ✅ Azure CLI instalat: `az --version`
- ✅ Azure Developer CLI (optional): `azd version`
- ✅ Access la Azure Portal pentru App Registration

## Ce se creează

- 🌐 **Web App** (App Service) - Python 3.11, Basic B1
- 🤖 **Bot Service** - Azure Bot, Free F0
- 📱 **Teams Channel** - Microsoft Teams integration
- 🔐 **App Registration** (manual) - Authentication

## Costs (Estimare)

- App Service (B1): ~$13/lună
- Bot Service (F0): Free
- **Total**: ~$13/lună

## Next Steps După Deployment

1. Test botul în Teams
2. Configurează permissions pentru utilizatori
3. Setup monitoring (Application Insights)
4. Documentează URL-uri pentru echipă

---

**📞 Need Help?** Vezi `DEPLOY_MANUAL.md` pentru detalii complete.
