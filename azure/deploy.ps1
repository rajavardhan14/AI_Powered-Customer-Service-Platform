# Automated Microsoft Azure Deployment Script (PowerShell)
# AI-Powered Customer Service & Business Analytics Platform

param (
    [string]$ResourceGroup = "rg-aegis-ai-platform",
    [string]$Location = "eastus",
    [string]$GeminiApiKey = ""
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Deploying Platform to Microsoft Azure Container Apps   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Check Azure CLI login
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Logging into Azure CLI..." -ForegroundColor Yellow
    az login | Out-Null
}

$randSuffix = Get-Random -Minimum 1000 -Maximum 9999
$AcrName = "acraegis$randSuffix"
$AppName = "aegis-support-platform"
$EnvName = "aegis-managed-env"

Write-Host "[1/5] Creating Azure Resource Group: $ResourceGroup in $Location..." -ForegroundColor Green
az group create --name $ResourceGroup --location $Location | Out-Null

Write-Host "[2/5] Creating Azure Container Registry: $AcrName..." -ForegroundColor Green
az acr create --resource-group $ResourceGroup --name $AcrName --sku Basic --admin-enabled true | Out-Null

Write-Host "[3/5] Building Docker Image in ACR Cloud..." -ForegroundColor Green
az acr build --registry $AcrName --image aegis-platform:latest --file docker/Dockerfile .

Write-Host "[4/5] Creating Azure Container Apps Environment..." -ForegroundColor Green
az containerapp env create --name $EnvName --resource-group $ResourceGroup --location $Location | Out-Null

Write-Host "[5/5] Deploying Container App..." -ForegroundColor Green
$acrServer = "$AcrName.azurecr.io"
$acrUser = az acr credential show --name $AcrName --query username -o tsv
$acrPass = az acr credential show --name $AcrName --query "passwords[0].value" -o tsv

$envVars = @()
if ($GeminiApiKey) {
    $envVars += "GEMINI_API_KEY=$GeminiApiKey"
}

az containerapp create `
  --name $AppName `
  --resource-group $ResourceGroup `
  --environment $EnvName `
  --image "$acrServer/aegis-platform:latest" `
  --registry-server $acrServer `
  --registry-username $acrUser `
  --registry-password $acrPass `
  --target-port 8000 `
  --ingress external `
  --cpu 1.0 `
  --memory 2.0Gi `
  --env-vars $envVars

$fqdn = az containerapp show --name $AppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn -o tsv

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "Public Web URL: https://$fqdn" -ForegroundColor Yellow
Write-Host "Power BI REST Endpoint: https://$fqdn/api/export/powerbi-json" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
