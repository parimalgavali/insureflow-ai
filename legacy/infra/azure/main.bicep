targetScope = 'resourceGroup'

@description('Base name used for Azure resources.')
param appName string = 'insureflow-ai'

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Container image for the Spring Boot API.')
param apiImage string

@description('Container image for the Vue/Nginx frontend.')
param frontendImage string

@description('Container image for the triage FastAPI service.')
param triageImage string

@description('Container image for the document intelligence FastAPI service.')
param documentIntelligenceImage string

@description('Container image for the RAG FastAPI service.')
param ragImage string

@description('PostgreSQL administrator login.')
param postgresAdminLogin string = 'insureflowadmin'

@secure()
@description('PostgreSQL administrator password.')
param postgresAdminPassword string

@description('JWT issuer for the backend API.')
param jwtIssuer string = 'insureflow-ai'

@secure()
@description('JWT signing secret for the backend API.')
param jwtSecret string

var logAnalyticsName = '${appName}-logs'
var environmentName = '${appName}-env'
var postgresName = replace('${appName}-postgres', '-', '')
var postgresDatabaseName = 'insureflow'
var postgresHost = '${postgres.name}.postgres.database.azure.com'
var apiBaseUrl = 'http://${appName}-api'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: postgresName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    version: '16'
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
  }
}

resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: postgres
  name: postgresDatabaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

resource triageApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${appName}-triage'
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: false
        targetPort: 8001
      }
    }
    template: {
      containers: [
        {
          name: 'triage'
          image: triageImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
}

resource documentIntelligenceApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${appName}-document-intelligence'
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: false
        targetPort: 8002
      }
    }
    template: {
      containers: [
        {
          name: 'document-intelligence'
          image: documentIntelligenceImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
}

resource ragApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${appName}-rag'
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: false
        targetPort: 8003
      }
    }
    template: {
      containers: [
        {
          name: 'rag'
          image: ragImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
}

resource apiApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${appName}-api'
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8080
        transport: 'auto'
      }
      secrets: [
        {
          name: 'postgres-password'
          value: postgresAdminPassword
        }
        {
          name: 'jwt-secret'
          value: jwtSecret
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          env: [
            {
              name: 'SPRING_DATASOURCE_URL'
              value: 'jdbc:postgresql://${postgresHost}:5432/${postgresDatabaseName}?sslmode=require'
            }
            {
              name: 'SPRING_DATASOURCE_USERNAME'
              value: postgresAdminLogin
            }
            {
              name: 'SPRING_DATASOURCE_PASSWORD'
              secretRef: 'postgres-password'
            }
            {
              name: 'INSUREFLOW_JWT_ISSUER'
              value: jwtIssuer
            }
            {
              name: 'INSUREFLOW_JWT_SECRET'
              secretRef: 'jwt-secret'
            }
            {
              name: 'INSUREFLOW_AI_TRIAGE_BASE_URL'
              value: 'https://${triageApp.properties.configuration.ingress.fqdn}'
            }
          ]
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

resource frontendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${appName}-frontend'
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: frontendImage
          env: [
            {
              name: 'VITE_API_BASE_URL'
              value: apiBaseUrl
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
}

output apiUrl string = 'https://${apiApp.properties.configuration.ingress.fqdn}'
output frontendUrl string = 'https://${frontendApp.properties.configuration.ingress.fqdn}'
output postgresServerName string = postgres.name
