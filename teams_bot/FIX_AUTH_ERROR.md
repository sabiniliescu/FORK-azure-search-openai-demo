# 🔧 Fix: AADSTS7000216 Authentication Error

## Problema

Primești eroarea:
```
AADSTS7000216: 'client_assertion', 'client_secret' or 'request' is required 
for the 'client_credentials' grant type.
```

## Cauza

Când folosești **User-Assigned Managed Identity** pentru autentificare, bot-ul **NU** trebuie să aibă setat `MICROSOFT_APP_PASSWORD`. Azure AD încearcă să găsească un secret/certificat pentru autentificare, dar când folosești Managed Identity, autentificarea se face automat prin identitatea managed a App Service-ului.

## Soluție

### Opțiunea 1: Rulează script-ul automat (RECOMANDAT)

```powershell
cd teams_bot
.\fix_azure_auth.ps1
```

Script-ul va:
1. ✅ Verifica dacă Managed Identity este configurată
2. ✅ Șterge `MICROSOFT_APP_PASSWORD` dacă există
3. ✅ Setează corect `MICROSOFT_APP_TYPE`, `MICROSOFT_APP_ID`, `MICROSOFT_APP_TENANTID`
4. ✅ Restartează aplicația

### Opțiunea 2: Manual în Azure Portal

1. **Navighează la App Service**
   - Mergi la [Azure Portal](https://portal.azure.com)
   - Găsește App Service-ul tău (ex: `mihai-teams-bot`)

2. **Configurare → Application Settings**
   - Șterge `MICROSOFT_APP_PASSWORD` dacă există
   - Verifică că ai:
     - `MICROSOFT_APP_TYPE` = `UserAssignedMSI`
     - `MICROSOFT_APP_ID` = `<client-id-of-managed-identity>`
     - `MICROSOFT_APP_TENANTID` = `52d32ffe-bfad-4f92-b437-e29121332333`

3. **Restart** aplicația

### Opțiunea 3: Azure CLI

```powershell
# Șterge MICROSOFT_APP_PASSWORD
az webapp config appsettings delete \
    --name mihai-teams-bot \
    --resource-group rg-mihai-app \
    --setting-names MICROSOFT_APP_PASSWORD

# Setează corect settings
az webapp config appsettings set \
    --name mihai-teams-bot \
    --resource-group rg-mihai-app \
    --settings \
        MICROSOFT_APP_TYPE="UserAssignedMSI" \
        MICROSOFT_APP_ID="<your-managed-identity-client-id>" \
        MICROSOFT_APP_TENANTID="52d32ffe-bfad-4f92-b437-e29121332333"

# Restart
az webapp restart \
    --name mihai-teams-bot \
    --resource-group rg-mihai-app
```

## Verificare

După aplicarea soluției:

1. **Verifică logs**:
   ```powershell
   az webapp log tail --name mihai-teams-bot --resource-group rg-mihai-app
   ```

2. **Caută în logs**:
   ```
   🔐 Configuring bot with app type: UserAssignedMSI
   🔐 Using UserAssignedMSI - password set to None
   ```

3. **Testează bot-ul** în Teams - ar trebui să funcționeze fără erori de autentificare

## Ce s-a schimbat în cod

### Înainte (GREȘIT pentru Managed Identity):
```python
settings = BotFrameworkAdapterSettings(
    app_id=APP_ID,
    app_password=APP_PASSWORD  # ❌ Această linie cauzează eroarea
)
```

### Acum (CORECT pentru Managed Identity):
```python
settings_kwargs = {
    'app_id': APP_ID,
    'app_password': APP_PASSWORD
}

if APP_TYPE == "UserAssignedMSI":
    settings_kwargs['app_type'] = APP_TYPE
    settings_kwargs['app_tenant_id'] = APP_TENANTID
    settings_kwargs['app_password'] = None  # ✅ Set to None for MI
    
settings = BotFrameworkAdapterSettings(**settings_kwargs)
```

## Diferențe: Client Secret vs Managed Identity

| Aspect | Client Secret | Managed Identity |
|--------|--------------|------------------|
| `MICROSOFT_APP_PASSWORD` | ✅ Obligatoriu | ❌ NU trebuie setat |
| `MICROSOFT_APP_TYPE` | - | ✅ `UserAssignedMSI` |
| `MICROSOFT_APP_TENANTID` | - | ✅ Tenant ID |
| Securitate | Secret stocat | ✅ Mai securizat |
| Rotație credentials | Manuală | Automată |

## Troubleshooting

### Eroarea persistă după fix?

1. **Verifică că Managed Identity este asignată**:
   ```powershell
   az webapp identity show --name mihai-teams-bot --resource-group rg-mihai-app
   ```

2. **Verifică settings după restart**:
   ```powershell
   az webapp config appsettings list \
       --name mihai-teams-bot \
       --resource-group rg-mihai-app \
       --query "[?name=='MICROSOFT_APP_PASSWORD' || name=='MICROSOFT_APP_TYPE' || name=='MICROSOFT_APP_ID']"
   ```

3. **Verifică că Managed Identity are permisiuni în Bot Registration**:
   - Mergi la Azure Portal → App Registrations
   - Găsește bot registration-ul tău
   - Verifică că Managed Identity client ID este același cu cel din settings

## Link-uri utile

- [Bot Framework Managed Identity](https://learn.microsoft.com/en-us/azure/bot-service/bot-builder-authentication-managed-identity)
- [Azure Managed Identities](https://learn.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/)
