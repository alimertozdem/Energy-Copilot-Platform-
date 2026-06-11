# set-appservice-env.ps1
# Pushes the values from .env to an Azure App Service web app as app settings.
# Run from web-app/backend (where .env lives).
#   .\set-appservice-env.ps1 -app <your-webapp-name>
param([string]$app = "energylens-api-web")

$ErrorActionPreference = "Stop"
try { $PSNativeCommandArgumentPassing = "Standard" } catch {}

$rg       = "rg-energylens"
$frontend = "https://energy-copilot-platform.vercel.app"
$envFile  = ".env"

if (-not (Test-Path $envFile)) {
    throw ".env not found here. Open PowerShell in web-app/backend, then run this again."
}

$pairs = @()
foreach ($line in Get-Content $envFile) {
    $t = $line.Trim()
    if ($t -eq "" -or $t.StartsWith("#")) { continue }
    if ($t.StartsWith("export ")) { $t = $t.Substring(7).Trim() }
    $i = $t.IndexOf("=")
    if ($i -lt 1) { continue }
    $key = $t.Substring(0, $i).Trim()
    $val = $t.Substring($i + 1).Trim()
    if ($val.Length -ge 2 -and (
            ($val.StartsWith('"') -and $val.EndsWith('"')) -or
            ($val.StartsWith("'") -and $val.EndsWith("'")))) {
        $val = $val.Substring(1, $val.Length - 2)
    }
    if ($key -eq "PORT" -or $key -eq "LLM_PROVIDER") { continue }
    $pairs += "$key=$val"
}

# values not present in .env (or forced) + App Service container port
$pairs += "LLM_PROVIDER=mock"
$pairs += "CORS_ORIGINS=$frontend"
$pairs += "FRONTEND_URL=$frontend"
$pairs += "WEBSITES_PORT=8000"

Write-Host ("Setting {0} app settings on {1}:" -f $pairs.Count, $app) -ForegroundColor Cyan
(($pairs | ForEach-Object { ($_ -split '=', 2)[0] }) -join ", ")

az webapp config appsettings set -g $rg -n $app --settings $pairs | Out-Null

Write-Host "`nApp setting names now on the web app:" -ForegroundColor Green
az webapp config appsettings list -g $rg -n $app --query "[].name" -o tsv
