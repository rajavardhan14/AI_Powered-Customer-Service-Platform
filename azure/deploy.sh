#!/bin/bash
set -e

# Automated Microsoft Azure Deployment Script (Bash)
# AI-Powered Customer Service & Business Analytics Platform

RESOURCE_GROUP=${1:-"rg-aegis-ai-platform"}
LOCATION=${2:-"eastus"}
GEMINI_KEY=${3:-""}

echo "=========================================================="
echo "   Deploying Platform to Microsoft Azure Container Apps   "
echo "=========================================================="

RAND_SUFFIX=$((1000 + RANDOM % 9000))
ACR_NAME="acraegis${RAND_SUFFIX}"
APP_NAME="aegis-support-platform"
ENV_NAME="aegis-managed-env"

echo "[1/5] Creating Azure Resource Group: ${RESOURCE_GROUP}..."
az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}"

echo "[2/5] Creating Azure Container Registry: ${ACR_NAME}..."
az acr create --resource-group "${RESOURCE_GROUP}" --name "${ACR_NAME}" --sku Basic --admin-enabled true

echo "[3/5] Building Docker Image in ACR Cloud..."
az acr build --registry "${ACR_NAME}" --image aegis-platform:latest --file docker/Dockerfile .

echo "[4/5] Creating Azure Container Apps Environment..."
az containerapp env create --name "${ENV_NAME}" --resource-group "${RESOURCE_GROUP}" --location "${LOCATION}"

echo "[5/5] Deploying Container App..."
ACR_SERVER="${ACR_NAME}.azurecr.io"
ACR_USER=$(az acr credential show --name "${ACR_NAME}" --query username -o tsv)
ACR_PASS=$(az acr credential show --name "${ACR_NAME}" --query "passwords[0].value" -o tsv)

ENV_ARGS=()
if [ -n "$GEMINI_KEY" ]; then
  ENV_ARGS+=("--env-vars" "GEMINI_API_KEY=${GEMINI_KEY}")
fi

az containerapp create \
  --name "${APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --environment "${ENV_NAME}" \
  --image "${ACR_SERVER}/aegis-platform:latest" \
  --registry-server "${ACR_SERVER}" \
  --registry-username "${ACR_USER}" \
  --registry-password "${ACR_PASS}" \
  --target-port 8000 \
  --ingress external \
  --cpu 1.0 \
  --memory 2.0Gi \
  "${ENV_ARGS[@]}"

FQDN=$(az containerapp show --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --query properties.configuration.ingress.fqdn -o tsv)

echo "=========================================================="
echo "DEPLOYMENT SUCCESSFUL!"
echo "Public Web URL: https://${FQDN}"
echo "Power BI REST Endpoint: https://${FQDN}/api/export/powerbi-json"
echo "=========================================================="
