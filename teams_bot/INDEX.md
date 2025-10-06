# 📚 INDEX - Documentație Teams Bot Deployment

Ghid rapid pentru navigare prin documentația de deployment.

## 🚀 Start Here

**Nou în deployment Azure?** Începe aici:

### 🌟 OPȚIUNE 1: Managed Identity (RECOMANDAT - Mai Sigur!) ⭐

**Dacă ai permisiuni pentru Managed Identity:**

1. **[test_managed_identity_permissions.ps1](./test_managed_identity_permissions.ps1)** 🧪 - **Test Permissions (2 min)**
   - Verifică dacă ai permisiuni pentru Managed Identity
   - Rulează: `.\test_managed_identity_permissions.ps1`
   - Dacă testul trece → folosește opțiunea cu MI!

2. **[deploy_with_managed_identity.ps1](./deploy_with_managed_identity.ps1)** 🚀 - **Deploy cu MI (10-15 min)**
   - Zero secrets/passwords - mai sigur!
   - Deployment automat complet
   - Best practice pentru production

3. **[MANAGED_IDENTITY_COMPARISON.md](./MANAGED_IDENTITY_COMPARISON.md)** 📊 - **Comparație MI vs App Registration**
   - De ce MI e mai bun
   - Diferențe de securitate
   - Cost comparison

### 🔧 OPȚIUNE 2: App Registration Manual (Funcționează Mereu)

**Dacă nu ai permisiuni pentru Managed Identity sau vrei control manual:**

1. **[QUICK_START_DEPLOY.md](./QUICK_START_DEPLOY.md)** ⚡ - **TL;DR Deployment (5 minute)**
   - Quick reference cu toate comenzile
   - Perfect pentru cei care știu ce fac
   - Copy-paste ready

2. **[DEPLOY_MANUAL.md](./DEPLOY_MANUAL.md)** 📖 - **Deployment Manual Pas cu Pas**
   - Pentru deployment fără permisiuni de Global Admin
   - Pași detalați cu screenshots
   - Abordare tradițională

3. **[README_DEPLOYMENT.md](./README_DEPLOYMENT.md)** � - **Overview Deployment Opțiuni**
   - Comparație manual vs azd
   - Explicații tehnice
   - Decision guide

4. **[DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)** � - **Technical Summary**
   - Explicație completă a soluției
   - De ce funcționează approach-ul ales
   - Infrastructure as Code details

**Legacy (mai vechi, pot fi depășite):**
- [QUICKSTART.md](./QUICKSTART.md) - Deployment rapid (vechi)
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Ghid complet (vechi)

## 📁 Structură Documentație

### Deployment

| Fișier | Descriere | Când să folosești |
|--------|-----------|-------------------|
| [QUICK_START_DEPLOY.md](./QUICK_START_DEPLOY.md) | ⚡ TL;DR comenzi deployment | Quick reference, știi ce faci |
| [DEPLOY_MANUAL.md](./DEPLOY_MANUAL.md) | ⭐ Ghid manual pas cu pas | **RECOMANDAT** - fără Global Admin rights |
| [README_DEPLOYMENT.md](./README_DEPLOYMENT.md) | 📖 Overview opțiuni deployment | Decision making, comparație approaches |
| [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md) | 📋 Technical deep-dive | Înțelegere tehnică completă |
| [QUICKSTART.md](./QUICKSTART.md) | Legacy quick guide | Doar dacă ai Global Admin (vechi) |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Legacy full guide | Reference pentru concepte generale |
| [deploy.ps1](./deploy.ps1) | Script automat (nu funcționează) | ❌ Nu folosi - necesită Global Admin |

### Funcționalități

| Fișier | Descriere | Când să folosești |
|--------|-----------|-------------------|
| [LINK_MAPPING.md](./LINK_MAPPING.md) | Explicație link mapping pentru economie tokeni | Pentru a înțelege optimizarea linkurilor |
| [README.md](./README.md) | Documentație generală proiect | Overview și dezvoltare locală |

### Configurare

| Fișier | Descriere | Când să folosești |
|--------|-----------|-------------------|
| [.env.example](./.env.example) | Template variabile de mediu | Setup local sau Azure |
| [manifest/README.md](./manifest/README.md) | Configurare manifest Teams | Customizare aplicație Teams |
| [manifest/ICONS.md](./manifest/ICONS.md) | Ghid creare iconițe | Creare iconițe pentru Teams |

## 🎯 Scenarii Comune

### "Vreau deployment CEL MAI SIGUR pentru production" 🌟
```
1. Test permissions: .\test_managed_identity_permissions.ps1
2. Dacă testul trece ✅:
   - Deploy: .\deploy_with_managed_identity.ps1
   - Zero secrets, zero maintenance!
   - Best practice Microsoft
```

### "Vreau să deploiez ACUM - cel mai simplu mod"
```
1. Citește: DEPLOY_MANUAL.md (Pas 1-6)
2. Creează App Registration manual în Azure Portal
3. Deploy cu az webapp sau azd
4. Configurează Bot Service în Portal
5. Upload în Teams
```

### "Vreau quick reference cu toate comenzile"
```
1. Citește: QUICK_START_DEPLOY.md
2. Copy-paste comenzile
3. Adaptează cu valorile tale
```

### "Am deja bot cu App Registration - vreau să migrez la Managed Identity"
```
1. Verifică permissions: .\test_managed_identity_permissions.ps1
2. Citește: MANAGED_IDENTITY_COMPARISON.md → "Migration Path"
3. Deploy nou cu MI (nume diferit)
4. Test și șterge vechiul bot
```

### "Am probleme la deployment - eroare permisiuni"
```
✅ SOLUȚIE 1: Folosește Managed Identity
   - Test: .\test_managed_identity_permissions.ps1
   - Deploy: .\deploy_with_managed_identity.ps1

✅ SOLUȚIE 2: Folosește DEPLOY_MANUAL.md
   - Creezi App Registration manual în Portal (ai access)
   - Nu necesită Global Admin
```

### "Vreau să înțeleg diferența între MI și App Registration"
```
1. Citește: MANAGED_IDENTITY_COMPARISON.md
2. TL;DR: MI = mai sigur, fără secrets, zero maintenance
3. App Reg = mai simplu setup, mai mult control manual
```

### "Am probleme la deployment"
```
1. Verifică: DEPLOYMENT.md → Pas 7 (Troubleshooting)
2. Verifică logs: az webapp log tail
3. Testează: curl https://your-bot.azurewebsites.net/health
```

### "Vreau să înțeleg cum funcționează link mapping"
```
1. Citește: LINK_MAPPING.md
2. Testează: python test_link_mapping.py
3. Testează cu backend: python test_link_mapping_integration.py
```

### "Trebuie să creez iconițe pentru Teams"
```
1. Citește: manifest/ICONS.md
2. Alege o opțiune (Canva, Python generator, etc.)
3. Creează color.png (192x192) și outline.png (32x32)
```

### "Vreau să testez local înainte de Azure"
```
1. Citește: README.md → Quick Start - Dezvoltare Locală
2. Setup: cp .env.example .env
3. Rulează: python app.py
4. Testează: Bot Framework Emulator
```

### "Am deja App ID și vreau doar să deploy codul"
```
1. Setează .env cu credențiale existente
2. Rulează: deploy.ps1 -SkipBotRegistration
```

## 📊 Flow Complet Deployment

```
┌─────────────────────────────────────────────────────────┐
│ 1. PREGĂTIRE                                            │
│    └─ Verifică backend URL                              │
│    └─ Azure CLI login                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 2. BOT REGISTRATION                                     │
│    └─ Creează Azure AD App                              │
│    └─ Generează App ID & Password                       │
│    └─ Salvează în .env                                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 3. DEPLOYMENT AZURE                                     │
│    └─ Creează Resource Group                            │
│    └─ Deploy Web App                                    │
│    └─ Configurează App Settings                         │
│    └─ Deploy cod                                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 4. BOT SERVICE                                          │
│    └─ Creează Azure Bot Service                         │
│    └─ Configurează endpoint                             │
│    └─ Activează Teams channel                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 5. TEAMS APP PACKAGE                                    │
│    └─ Generează Teams App ID                            │
│    └─ Actualizează manifest.json                        │
│    └─ Creează teams-app.zip                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 6. PUBLISH ÎN TEAMS                                     │
│    └─ Upload teams-app.zip                              │
│    └─ Testează bot                                      │
│    └─ (Opțional) Publish pentru organizație             │
└─────────────────────────────────────────────────────────┘
```

## 🛠️ Comenzi Rapide

### Deployment
```powershell
# Deployment complet automat
.\deploy.ps1 -ResourceGroupName "rg-teams-bot" -AppName "teamsbot-mihai" -BackendUrl "https://backend.azurecontainerapps.io"

# Deploy cu credențiale existente
.\deploy.ps1 -ResourceGroupName "rg-teams-bot" -AppName "teamsbot-mihai" -BackendUrl "https://backend.azurecontainerapps.io" -SkipBotRegistration
```

### Testing Local
```powershell
# Setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env

# Rulează
python app.py
```

### Azure Management
```powershell
# Vezi logs
az webapp log tail --name "teamsbot-mihai" --resource-group "rg-teams-bot"

# Restart
az webapp restart --name "teamsbot-mihai" --resource-group "rg-teams-bot"

# Update backend URL
az webapp config appsettings set --name "teamsbot-mihai" --resource-group "rg-teams-bot" --settings BACKEND_URL="https://new-url"

# Health check
curl https://teamsbot-mihai.azurewebsites.net/health
```

### Teams Package
```powershell
# Creează package
cd manifest
Compress-Archive -Path manifest.json,color.png,outline.png -DestinationPath ../teams-app.zip -Force
```

## ❓ FAQ Quick Links

| Întrebare | Unde găsești răspuns |
|-----------|---------------------|
| Cum deploiez rapid? | [QUICKSTART.md](./QUICKSTART.md) |
| Bot nu răspunde în Teams | [DEPLOYMENT.md](./DEPLOYMENT.md#pas-7-verificare-și-debugging) |
| Cum funcționează link mapping? | [LINK_MAPPING.md](./LINK_MAPPING.md) |
| Cum creez iconițe? | [manifest/ICONS.md](./manifest/ICONS.md) |
| Cum testez local? | [README.md](./README.md#quick-start---dezvoltare-locală) |
| Erori la deployment | [DEPLOYMENT.md](./DEPLOYMENT.md#pas-7-verificare-și-debugging) |
| Customizare prompt-uri | [README.md](./README.md#customizare) |

## 🔗 Link-uri Externe Utile

### Microsoft Documentation
- [Bot Framework SDK](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Teams Platform](https://docs.microsoft.com/en-us/microsoftteams/platform/)
- [Azure Bot Service](https://azure.microsoft.com/en-us/services/bot-services/)

### Tools
- [Bot Framework Emulator](https://github.com/Microsoft/BotFramework-Emulator/releases)
- [Teams Developer Portal](https://dev.teams.microsoft.com)
- [Azure CLI Download](https://aka.ms/installazurecliwindows)

### Resources
- [Teams App Validation](https://dev.teams.microsoft.com/appvalidation.html)
- [Manifest Schema](https://docs.microsoft.com/en-us/microsoftteams/platform/resources/schema/manifest-schema)
- [Icon Resources](https://www.flaticon.com)

## 📞 Suport

Dacă întâmpini probleme:

1. ✅ **Verifică documentația relevantă** din tabelul de mai sus
2. ✅ **Verifică logs-urile** Azure cu `az webapp log tail`
3. ✅ **Testează health endpoint** cu `curl https://your-bot.azurewebsites.net/health`
4. ✅ **Consultă FAQ** și troubleshooting sections
5. ❓ **Deschide issue** în repository dacă problema persistă

---

**Pregătit pentru deployment?** 

👉 Start aici: **[QUICKSTART.md](./QUICKSTART.md)**

---

_Ultima actualizare: {date}_
