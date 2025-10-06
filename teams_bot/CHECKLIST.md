# ✅ Deployment Checklist - Teams Bot

Folosește această checklist pentru a te asigura că deployment-ul se face corect.

## 📋 Pre-Deployment Checklist

### 1. Prerequisites

- [ ] Azure subscription activ
- [ ] Azure CLI instalat (`az --version`)
- [ ] PowerShell 7+ instalat (`$PSVersionTable.PSVersion`)
- [ ] Python 3.9+ instalat (`python --version`)
- [ ] Git instalat (pentru version control)

### 2. Backend Verification

- [ ] Backend-ul este deployed și funcțional
- [ ] Știi URL-ul backend-ului (ex: `https://backend-app.azurecontainerapps.io`)
- [ ] Backend health endpoint răspunde: `curl https://backend-url/health`
- [ ] Backend `/chat` endpoint funcționează

### 3. Azure Login

- [ ] Autentificat în Azure: `az login`
- [ ] Subscription corect setat: `az account show`
- [ ] Ai permisiuni să creezi resurse în subscription

### 4. Configurare Locală

- [ ] Ai clonat repository-ul local
- [ ] Ești în directorul `teams_bot/`
- [ ] Ai făcut `pip install -r requirements.txt` (opțional, pentru testare locală)

---

## 🚀 Deployment Checklist

### 5. Rulare Script Deployment

- [ ] Ai decis numele pentru bot (ex: `teamsbot-prenume-nume`)
- [ ] Ai decis numele resource group (ex: `rg-teams-bot`)
- [ ] Ai pregătit comanda de deployment:

```powershell
.\deploy.ps1 `
    -ResourceGroupName "rg-teams-bot" `
    -AppName "teamsbot-NUMELE_TAU" `
    -BackendUrl "https://BACKEND_URL"
```

- [ ] Ai rulat scriptul de deployment
- [ ] Scriptul s-a finalizat cu succes (vezi mesaj "DEPLOYMENT FINALIZAT CU SUCCES")

### 6. Salvare Credențiale

- [ ] **IMPORTANT:** Ai salvat Microsoft App ID
- [ ] **IMPORTANT:** Ai salvat Microsoft App Password (din output sau `.env`)
- [ ] Ai salvat credențialele într-un password manager securizat
- [ ] Ai backup pentru `.env` file

**⚠️ CRITICAL:** Password-ul nu va mai fi afișat niciodată!

### 7. Verificare Deployment

- [ ] Health endpoint răspunde: `curl https://APP_NAME.azurewebsites.net/health`
- [ ] Web App rulează în Azure Portal
- [ ] Bot Service există în Azure Portal
- [ ] Teams Channel este activat în Bot Service

---

## 📱 Teams Integration Checklist

### 8. Iconițe Teams App

**Opțiunea A - Creează iconițe custom:**
- [ ] Ai creat `color.png` (192x192 px)
- [ ] Ai creat `outline.png` (32x32 px, fundal transparent)
- [ ] Iconițele sunt în `manifest/` folder

**Opțiunea B - Folosește iconițe default:**
- [ ] Ai downloadat iconițe template
- [ ] Iconițele sunt în `manifest/` folder

**Verificare dimensiuni:**
```powershell
Add-Type -AssemblyName System.Drawing
[System.Drawing.Image]::FromFile("manifest/color.png").Size   # Trebuie: 192x192
[System.Drawing.Image]::FromFile("manifest/outline.png").Size # Trebuie: 32x32
```

### 9. Manifest Verification

- [ ] Fișierul `manifest/manifest.json` există
- [ ] UUID-urile au fost generate/actualizate automat de script
- [ ] `botId` este corect (Microsoft App ID)
- [ ] `validDomains` conține domeniul corect
- [ ] JSON-ul este valid: `Get-Content manifest/manifest.json | ConvertFrom-Json`

### 10. Teams Package Creation

- [ ] Ai rulat comanda de creare package (sau scriptul a făcut-o automat):
```powershell
cd manifest
Compress-Archive -Path manifest.json,color.png,outline.png -DestinationPath ../teams-app.zip -Force
```

- [ ] Fișierul `teams-app.zip` există în `teams_bot/`
- [ ] ZIP-ul conține exact 3 fișiere: manifest.json, color.png, outline.png

### 11. Upload în Teams

- [ ] Ai deschis Microsoft Teams desktop/web
- [ ] Ai navigat la Apps → Manage your apps
- [ ] Ai făcut click pe "Upload a custom app"
- [ ] Ai selectat "Upload for me or my teams"
- [ ] Ai selectat fișierul `teams-app.zip`
- [ ] Nu au apărut erori la upload
- [ ] Aplicația apare în lista de apps

---

## 🧪 Testing Checklist

### 12. Testare Funcțională

- [ ] Ai adăugat bot-ul (click "Add")
- [ ] Conversația s-a deschis
- [ ] Ai primit mesajul de welcome

**Test conversații:**
- [ ] Test 1: "Care sunt beneficiile companiei?"
  - [ ] Bot-ul răspunde
  - [ ] Răspunsul conține informații relevante
  - [ ] Citations/linkuri sunt afișate corect

- [ ] Test 2: "Spune-mi mai multe despre..."
  - [ ] Bot-ul menține contextul conversației
  - [ ] Multi-turn conversation funcționează

- [ ] Test 3: "Ce posturi sunt disponibile?"
  - [ ] Bot-ul returnează informații despre joburi
  - [ ] Link mapping funcționează (linkuri scurte → lungi)

### 13. Verificare Features

- [ ] **Citations:** Linkurile către documente funcționează
- [ ] **Superscript:** Numerele de citare sunt formatate corect
- [ ] **HTML Cleaning:** Formatarea HTML → Teams markdown funcționează
- [ ] **Link Mapping:** ID-uri scurte (link1, link2) → linkuri reale
- [ ] **Conversation History:** Bot-ul își amintește conversațiile anterioare

---

## 🔍 Post-Deployment Checklist

### 14. Monitoring Setup

- [ ] Ai activat Application Insights (opțional)
- [ ] Ai configurat alerts pentru erori
- [ ] Știi cum să accesezi logs: `az webapp log tail --name APP_NAME --resource-group RG_NAME`

### 15. Documentation

- [ ] Ai documentat credențialele într-un loc securizat
- [ ] Ai documentat URL-urile importante:
  - [ ] Web App URL: `https://APP_NAME.azurewebsites.net`
  - [ ] Backend URL
  - [ ] Resource Group name
  - [ ] Microsoft App ID

- [ ] Ai creat documentație pentru echipă (dacă e cazul)

### 16. Backup

- [ ] Ai backup pentru `.env` file
- [ ] Ai backup pentru `manifest/manifest.json` actualizat
- [ ] Ai backup pentru `teams-app.zip` final

---

## 📊 Success Criteria

Deployment-ul este considerat reușit când:

- ✅ Web App rulează și răspunde la `/health`
- ✅ Bot Service este configurat și activ
- ✅ Teams App este uploaded și funcțional
- ✅ Bot-ul răspunde la întrebări în Teams
- ✅ Conversațiile multi-turn funcționează
- ✅ Citations și linkuri sunt corecte
- ✅ Nu apar erori în logs

---

## ❌ Common Issues Checklist

Dacă ceva nu funcționează, verifică:

### Bot nu răspunde în Teams

- [ ] Backend URL este corect setat: `az webapp config appsettings list`
- [ ] Backend este accesibil: `curl https://backend-url/health`
- [ ] Endpoint-ul botului este configurat corect în Bot Service
- [ ] Teams Channel este activat

### Erori la upload Teams package

- [ ] Iconițele au dimensiunile corecte (192x192, 32x32)
- [ ] outline.png are fundal transparent
- [ ] manifest.json este valid JSON
- [ ] Toate UUID-urile sunt valide
- [ ] ZIP-ul conține exact 3 fișiere

### Web App nu pornește

- [ ] Verifică logs: `az webapp log tail`
- [ ] Verifică că toate dependencies sunt în `requirements.txt`
- [ ] Verifică că `PORT=3978` în App Settings
- [ ] Verifică că Python runtime este 3.11

---

## 📞 Support Resources

Dacă ai probleme:

1. **Verifică documentația:**
   - [ ] [QUICKSTART.md](./QUICKSTART.md) pentru pași rapidi
   - [ ] [DEPLOYMENT.md](./DEPLOYMENT.md) pentru troubleshooting detaliat
   - [ ] [INDEX.md](./INDEX.md) pentru navigare completă

2. **Check logs:**
   ```powershell
   az webapp log tail --name "APP_NAME" --resource-group "RG_NAME"
   ```

3. **Test endpoints:**
   ```powershell
   curl https://APP_NAME.azurewebsites.net/health
   curl https://backend-url/health
   ```

4. **Azure Portal:**
   - [ ] Verifică Web App status
   - [ ] Verifică Bot Service configuration
   - [ ] Verifică Application Insights (dacă activat)

---

## ✅ Final Sign-off

- [ ] Toate check-urile de mai sus sunt completate
- [ ] Bot-ul funcționează corect în Teams
- [ ] Documentația este completă
- [ ] Echipa știe cum să folosească bot-ul
- [ ] Credențialele sunt salvate securizat

**Deployment Status:** 🎉 COMPLET ✅

**Date:** _______________

**Deployed by:** _______________

**Notes:** 
_____________________________________
_____________________________________
_____________________________________

---

**Felicitări! Bot-ul tău Teams este live! 🚀**
