# Teams Bot Architecture - Managed Identity Implementation

## Problem
The Microsoft Bot Framework SDK (v4.17.0) doesn't natively support Azure Managed Identity authentication. When deploying to Azure App Service with Managed Identity, the bot would fail with error:
```
AADSTS7000216: 'client_assertion', 'client_secret' or 'request' is required for the client_credentials grant type.
```

## Solution Architecture

### Custom Components

#### 1. ManagedIdentityAppCredentials
**File**: `managed_identity_credentials.py`

Custom implementation of `AppCredentials` that uses Azure Managed Identity instead of client secrets.

```python
class ManagedIdentityAppCredentials(AppCredentials):
    def __init__(self, app_id: str, tenant_id: Optional[str] = None):
        # Set required attributes directly (don't call super().__init__)
        self.microsoft_app_id = app_id
        self.microsoft_app_password = ""
        self.tenant_id = tenant_id
        self.oauth_scope = None  # Required by SDK
        
        # Initialize Managed Identity credential
        self.credential = ManagedIdentityCredential(client_id=app_id)
        self.scope = "https://api.botframework.com/.default"
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        token = self.credential.get_token(self.scope)
        return token.token
```

**Key Points**:
- Uses synchronous `ManagedIdentityCredential` (not async version)
- Sets attributes directly instead of calling parent `__init__` (which expects a password)
- Includes `oauth_scope = None` for SDK compatibility
- Token scope is `https://api.botframework.com/.default`

#### 2. ManagedIdentityBotAdapter
**File**: `managed_identity_adapter.py`

Custom `BotFrameworkAdapter` that overrides credential handling to force use of Managed Identity.

```python
class ManagedIdentityBotAdapter(BotFrameworkAdapter):
    def __init__(self, app_id: str, tenant_id: Optional[str] = None):
        # Initialize adapter with empty password
        settings = BotFrameworkAdapterSettings(
            app_id=app_id, 
            app_password=""
        )
        super().__init__(settings)
        
        # Create and set Managed Identity credentials
        self.credentials = ManagedIdentityAppCredentials(
            app_id=app_id, 
            tenant_id=tenant_id
        )
        self._credentials = self.credentials
    
    def get_app_credentials(self, app_id: str, oauth_scope: str = None):
        # Always return Managed Identity credentials
        return self.credentials
```

**Key Points**:
- Inherits from `BotFrameworkAdapter`
- Overrides `get_app_credentials()` to always return Managed Identity credentials
- Sets both `self.credentials` and `self._credentials`

### Application Flow

```
Teams Message
    ↓
Azure App Service (with Managed Identity)
    ↓
app.py: messages() endpoint
    ↓
ManagedIdentityBotAdapter
    ↓
TeamsBot.on_message_activity()
    ↓
backend_client.py: query_backend()
    ↓
Backend API (Container Apps)
    ↓
Response back through chain
    ↓
ManagedIdentityBotAdapter.get_app_credentials()
    ↓
ManagedIdentityAppCredentials.get_access_token()
    ↓
Azure Managed Identity gets token
    ↓
Bot Framework Connector sends message
    ↓
Teams receives response
```

## Azure Configuration

### Required App Settings
```bash
MICROSOFT_APP_ID=<managed-identity-client-id>
MICROSOFT_APP_TYPE=UserAssignedMSI
MICROSOFT_APP_TENANTID=<azure-tenant-id>
```

### Managed Identity Assignment
```bash
# Assign Managed Identity to App Service
az webapp identity assign \
    --resource-group <rg> \
    --name <app-name> \
    --identities <identity-resource-id>
```

## Why This Works

1. **Managed Identity Credential**: Azure automatically provides credentials to the App Service
2. **Token Acquisition**: `ManagedIdentityCredential.get_token()` gets Azure AD tokens without secrets
3. **SDK Compatibility**: Custom classes satisfy Bot Framework SDK's attribute requirements
4. **Override Pattern**: By overriding `get_app_credentials()`, we force the SDK to use our Managed Identity credentials instead of default password-based auth

## Deployment

Use the consolidated script:
```powershell
.\deploy_to_azure.ps1 -ConfigureIdentity
```

This script:
1. Creates deployment package (excludes dev files)
2. Deploys to Azure App Service
3. Assigns Managed Identity
4. Configures app settings
5. Validates deployment

## Security Benefits

- ✅ No client secrets in code or configuration
- ✅ Automatic credential rotation by Azure
- ✅ Centralized identity management
- ✅ Audit trail in Azure AD
- ✅ Supports role-based access control

## Dependencies

```txt
# Core bot framework
botbuilder-core==4.17.0
botbuilder-schema==4.17.0
botframework-connector==4.17.0

# Azure authentication
azure-identity==1.19.0

# Web framework
aiohttp==3.12.15
```

## Lessons Learned

1. Bot Framework SDK v4.17.0 doesn't support Managed Identity out of the box
2. Must use synchronous `ManagedIdentityCredential`, not async version
3. `AppCredentials` expects specific attributes - must set them directly
4. Must override `get_app_credentials()` to ensure custom credentials are used
5. SDK requires `oauth_scope` attribute even if set to `None`

---

**Status**: ✅ Production-ready, fully tested and deployed
