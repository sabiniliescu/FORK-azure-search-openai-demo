# Teams Bot - Azure Deployment with Managed Identity

A Microsoft Teams bot integrated with Azure OpenAI, deployed to Azure App Service using Managed Identity for secure authentication.

## 🎯 Features

- ✅ Microsoft Teams integration
- ✅ Azure OpenAI backend connectivity
- ✅ Managed Identity authentication (no secrets!)
- ✅ Async message processing
- ✅ Health check endpoint
- ✅ Comprehensive logging

## 📋 Prerequisites

- Azure subscription
- Azure CLI installed and configured
- PowerShell 7+ (for deployment script)
- Python 3.11+ (for local development)
- Microsoft Teams admin access (for bot registration)

## 🚀 Quick Start

### 1. Azure Resources Setup

First, ensure you have these Azure resources created:

```bash
# Resource Group
RESOURCE_GROUP="teams-chatbots"
APP_NAME="teamsbot-mihai-mi"
LOCATION="westeurope"

# Create Resource Group (if not exists)
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create App Service Plan
az appservice plan create \
    --name "${APP_NAME}-plan" \
    --resource-group $RESOURCE_GROUP \
    --is-linux \
    --sku B1

# Create Web App
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan "${APP_NAME}-plan" \
    --name $APP_NAME \
    --runtime "PYTHON:3.11"

# Create User-Assigned Managed Identity
az identity create \
    --resource-group $RESOURCE_GROUP \
    --name "mi-$APP_NAME"
```

### 2. Bot Registration

Create a Bot Registration in Azure Portal:

1. Go to **Azure Portal** → **Create a resource** → **Bot**
2. Create a new **Azure Bot** resource
3. Use **User-Assigned Managed Identity** for authentication
4. Note the **Application (client) ID** - this is your `MICROSOFT_APP_ID`
5. Add Microsoft Teams channel

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
# Bot Configuration
MICROSOFT_APP_ID=your-managed-identity-client-id
MICROSOFT_APP_TYPE=UserAssignedMSI
MICROSOFT_APP_TENANTID=your-azure-tenant-id

# Backend Configuration
BACKEND_URL=https://your-backend-url.azurecontainerapps.io

# Server Configuration
PORT=8000
```

### 4. Deploy to Azure

Use the consolidated deployment script:

```powershell
# Simple deployment
.\deploy_to_azure.ps1

# Deploy with custom settings
.\deploy_to_azure.ps1 -ResourceGroup "my-rg" -AppName "my-bot"

# Deploy and configure Managed Identity
.\deploy_to_azure.ps1 -ConfigureIdentity
```

### 5. Configure Managed Identity

After deployment, assign the Managed Identity to your App Service:

```bash
# Get the Managed Identity resource ID
IDENTITY_ID=$(az identity show \
    --resource-group $RESOURCE_GROUP \
    --name "mi-$APP_NAME" \
    --query id -o tsv)

# Assign it to the App Service
az webapp identity assign \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --identities $IDENTITY_ID

# Configure app settings
IDENTITY_CLIENT_ID=$(az identity show \
    --resource-group $RESOURCE_GROUP \
    --name "mi-$APP_NAME" \
    --query clientId -o tsv)

az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --settings \
        MICROSOFT_APP_ID=$IDENTITY_CLIENT_ID \
        MICROSOFT_APP_TYPE="UserAssignedMSI" \
        MICROSOFT_APP_TENANTID="your-tenant-id" \
        BACKEND_URL="your-backend-url"
```

## 🏗️ Project Structure

```
teams_bot/
├── app.py                           # Main application entry point
├── bot.py                           # Teams bot logic
├── backend_client.py                # Backend API client
├── managed_identity_credentials.py  # Managed Identity authentication
├── managed_identity_adapter.py      # Custom Bot Framework adapter
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── deploy_to_azure.ps1             # Deployment script
└── README.md                        # This file
```

## 🔧 Local Development

### Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run Locally

```bash
# Set environment variables
export MICROSOFT_APP_ID=""  # Leave empty for local dev
export BACKEND_URL="http://localhost:50505"

# Run the bot
python app.py
```

### Test with Bot Framework Emulator

1. Download [Bot Framework Emulator](https://github.com/Microsoft/BotFramework-Emulator/releases)
2. Open Emulator
3. Connect to `http://localhost:8000/api/messages`
4. Leave App ID and Password empty for local testing

## 📊 Monitoring

### View Logs

```bash
# Stream live logs
az webapp log tail --resource-group teams-chatbots --name teamsbot-mihai-mi

# Download logs
az webapp log download --resource-group teams-chatbots --name teamsbot-mihai-mi
```

### Health Check

Visit: `https://your-app-name.azurewebsites.net/health`

Expected response:
```json
{
  "status": "healthy",
  "service": "teams-bot"
}
```

## 🔐 Security

### Managed Identity Benefits

- ✅ **No secrets in code** - credentials managed by Azure
- ✅ **Automatic rotation** - Azure handles credential lifecycle
- ✅ **Least privilege** - granular permission control
- ✅ **Audit trail** - all access logged in Azure AD

### Required Permissions

The Managed Identity needs:
- **Bot Framework** access (automatically granted when using MI for bot)
- **Backend API** access (configure based on your backend)

## 🐛 Troubleshooting

### Bot not responding in Teams

1. Check logs: `az webapp log tail --resource-group <rg> --name <app>`
2. Verify Managed Identity is assigned to App Service
3. Confirm `MICROSOFT_APP_ID` matches the Managed Identity client ID
4. Ensure `MICROSOFT_APP_TYPE` is set to `UserAssignedMSI`

### Authentication errors (AADSTS7000216)

This means Managed Identity is not properly configured:

```bash
# Verify identity assignment
az webapp identity show --resource-group <rg> --name <app>

# Re-assign if needed
az webapp identity assign \
    --resource-group <rg> \
    --name <app> \
    --identities <identity-resource-id>
```

### Backend connection errors

1. Check `BACKEND_URL` is correctly set
2. Verify backend is accessible from Azure
3. Check backend logs for incoming requests

## 📝 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MICROSOFT_APP_ID` | Yes | - | Managed Identity client ID |
| `MICROSOFT_APP_TYPE` | Yes | - | Set to `UserAssignedMSI` |
| `MICROSOFT_APP_TENANTID` | Yes | - | Azure AD tenant ID |
| `BACKEND_URL` | Yes | - | Backend API endpoint |
| `PORT` | No | `8000` | Server port |

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test locally with Bot Emulator
4. Deploy to a test environment
5. Create a pull request

## 📄 License

See LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check this README and troubleshooting section
2. Review application logs
3. Check Azure Portal for resource health
4. Contact the development team

---

**Built with** ❤️ **using Azure, Python, and Microsoft Bot Framework**
