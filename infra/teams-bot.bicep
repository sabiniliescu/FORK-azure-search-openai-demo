// Bicep file for deploying Teams Bot resources to Azure
// This deployment requires manual App Registration creation

@description('Location for all resources')
param location string = resourceGroup().location

@description('Name of the Teams Bot')
param botName string

@description('Name of the App Service Plan')
param appServicePlanName string

@description('Name of the Web App')
param webAppName string

@description('Microsoft App ID (from manual App Registration)')
param microsoftAppId string

@description('Microsoft App Password (client secret from App Registration)')
@secure()
param microsoftAppPassword string

@description('Backend API URL')
param backendUrl string

@description('SKU for the App Service Plan')
param appServicePlanSku string = 'B1'

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: appServicePlanSku
    tier: 'Basic'
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// Web App for Teams Bot
resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: webAppName
  location: location
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'MICROSOFT_APP_ID'
          value: microsoftAppId
        }
        {
          name: 'MICROSOFT_APP_PASSWORD'
          value: microsoftAppPassword
        }
        {
          name: 'BACKEND_URL'
          value: backendUrl
        }
        {
          name: 'PORT'
          value: '8000'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
      ]
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
    }
    httpsOnly: true
  }
}

// Azure Bot Service
resource botService 'Microsoft.BotService/botServices@2022-09-15' = {
  name: botName
  location: 'global'
  kind: 'azurebot'
  sku: {
    name: 'F0' // Free tier
  }
  properties: {
    displayName: botName
    endpoint: 'https://${webApp.properties.defaultHostName}/api/messages'
    msaAppId: microsoftAppId
  }
}

// Teams Channel
resource teamsChannel 'Microsoft.BotService/botServices/channels@2022-09-15' = {
  parent: botService
  name: 'MsTeamsChannel'
  location: 'global'
  properties: {
    channelName: 'MsTeamsChannel'
    properties: {
      enableCalling: false
      isEnabled: true
    }
  }
}

// Outputs
output botEndpoint string = 'https://${webApp.properties.defaultHostName}/api/messages'
output webAppName string = webApp.name
output botName string = botService.name
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
