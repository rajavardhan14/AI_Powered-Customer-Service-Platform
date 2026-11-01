# Microsoft Azure Deployment Guide
## AI-Powered Customer Service & Business Analytics Platform

This guide outlines deployment to **Microsoft Azure** using **Azure Container Apps (ACA)** or **Azure App Service (Linux Containers)**.

---

## 1. Prerequisites
- An active [Microsoft Azure Subscription](https://azure.microsoft.com/).
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed (`az version`).
- Docker installed locally (if building locally), or Azure Container Registry (ACR) cloud build.

---

## 2. Option A: Deployment to Azure Container Apps (Recommended)

Azure Container Apps provides serverless container execution with built-in HTTPS, custom domains, and automatic scaling.

### Step 1: Login and Set Resource Group
```bash
az login
az account set --subscription "<YOUR_SUBSCRIPTION_ID_OR_NAME>"

# Define variables
RESOURCE_GROUP="rg-aegis-ai-platform"
LOCATION="eastus"
ACR_NAME="acraegis$(Get-Random -Minimum 1000 -Maximum 9999)" # Windows PowerShell
# On Linux: ACR_NAME="acraegis$RANDOM"
CONTAINER_APP_NAME="aegis-support-platform"
ENVIRONMENT_NAME="aegis-env"

# Create Resource Group
az group create --name $RESOURCE_GROUP --location $LOCATION
```

### Step 2: Create Azure Container Registry (ACR) and Build Image
```bash
# Create ACR
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Build image in the cloud using ACR Tasks (no local Docker required!)
az acr build --registry $ACR_NAME --image aegis-platform:latest --file docker/Dockerfile .
```

### Step 3: Create Container Apps Environment & Deploy
```bash
# Create Container Apps Managed Environment
az containerapp env create \
  --name $ENVIRONMENT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Retrieve ACR credentials
ACR_SERVER="${ACR_NAME}.azurecr.io"
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Deploy Container App
az containerapp create \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT_NAME \
  --image "${ACR_SERVER}/aegis-platform:latest" \
  --registry-server $ACR_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8000 \
  --ingress external \
  --cpu 1.0 \
  --memory 2.0Gi \
  --env-vars GEMINI_API_KEY="<YOUR_GEMINI_KEY>"
```

### Step 4: Verify Deployment
Once completed, retrieve your public application URL:
```bash
az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv
```
Open `https://<fqdn>` in your browser to access the live platform.

---

## 3. Option B: Deployment to Azure App Service

If your organization prefers traditional Azure App Service plans:

```bash
APP_PLAN="plan-aegis-linux"
APP_NAME="aegis-support-app-$RANDOM"

# 1. Create Linux App Service Plan (B1 basic or P1V3)
az appservice plan create \
  --name $APP_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1

# 2. Deploy Web App from ACR container
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_PLAN \
  --name $APP_NAME \
  --deployment-container-image-name "${ACR_SERVER}/aegis-platform:latest"

# 3. Configure Container Port and Environment Settings
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings WEBSITES_PORT=8000 GEMINI_API_KEY="<YOUR_GEMINI_KEY>"
```

---

## 4. Connecting Power BI to the Live Azure Deployment

Once deployed to Azure:
1. In Power BI Desktop, navigate to **Get Data ➔ Web**.
2. Enter your live Azure URL:
   ```text
   https://<YOUR_AZURE_FQDN>/api/export/powerbi-json
   ```
3. Set your Power BI dashboard to refresh periodically.
