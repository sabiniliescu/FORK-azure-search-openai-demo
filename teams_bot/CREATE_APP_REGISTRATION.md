# Instrucțiuni pentru Azure Admin - Creare App Registration

## Context
User-ul nu are permisiuni să creeze Azure AD App Registrations. Admin-ul trebuie să creeze manual App Registration și să furnizeze credențialele.

## Pași pentru Admin

### 1. Creează App Registration

```powershell
# Login ca admin
az login

# Creează App Registration
az ad app create --display-name "teamsbot-mihai" --query "{appId:appId,displayName:displayName}" -o json
```

**Salvează App ID** din output (ex: `12345678-1234-1234-1234-123456789012`)

### 2. Creează Client Secret

```powershell
# Înlocuiește <APP_ID> cu valoarea de mai sus
az ad app credential reset --id <APP_ID> --append --query password -o tsv
```

**Salvează Password** din output (va fi afișat o singură dată!)

### 3. Configurează permisiuni (Opțional, dar recomandat)

```powershell
# Adaugă permisiuni Teams
az ad app permission add --id <APP_ID> --api 00000003-0000-0000-c000-000000000000 --api-permissions e1fe6dd8-ba31-4d61-89e7-88639da4683d=Scope

# Grant admin consent
az ad app permission admin-consent --id <APP_ID>
```

### 4. Furnizează credențialele către user

Trimite user-ului (prin canal securizat):
```
Microsoft App ID: <APP_ID>
Microsoft App Password: <PASSWORD>
```

## User-ul va continua deployment-ul

După ce primește credențialele, user-ul va:

1. Edita fișierul `.env` cu credențialele:
```bash
MICROSOFT_APP_ID=<APP_ID>
MICROSOFT_APP_PASSWORD=<PASSWORD>
BACKEND_URL=https://capps-backend-dcnxgznrq3wmc.happyground-5a8ca1ce.eastus.azurecontainerapps.io
PORT=3978
```

2. Rula deployment cu skip bot registration:
```powershell
.\deploy.ps1 `
    -ResourceGroupName "teams-chatbots" `
    -AppName "teamsbot-mihai" `
    -BackendUrl "https://capps-backend-dcnxgznrq3wmc.happyground-5a8ca1ce.eastus.azurecontainerapps.io" `
    -SkipBotRegistration
```

## Alternativ: Portal Azure

Admin-ul poate crea App Registration și din Portal:

1. Mergi la [Azure Portal](https://portal.azure.com)
2. Azure Active Directory → App registrations → New registration
3. Name: `teamsbot-mihai`
4. Supported account types: "Accounts in this organizational directory only"
5. Click **Register**
6. **Copiază Application (client) ID**
7. Certificates & secrets → New client secret
8. Description: "Teams Bot Secret"
9. Expires: 24 months (sau custom)
10. Click **Add**
11. **Copiază Value** (secret-ul, va fi afișat o singură dată!)
12. Trimite ambele valori către user

---

**Important:** Password-ul nu va mai fi afișat după ce închizi pagina!
