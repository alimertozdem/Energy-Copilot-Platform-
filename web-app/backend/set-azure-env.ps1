# set-azure-env.ps1
# Pushes the values from web-app/backend/.env to the Azure Container App as env vars.
# Run from the web-app/backend folder (where .env lives).
# Secrets stay local — only az reads them; nothing is printed except variable NAMES.

$ErrorActionPreference = "Stop"
try { $PSNativeCommandArgumentPassing = "Standard" } catch {}

$rg       = "rg-energylens"
$app      = "energylens-api"
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
    # strip one layer of surrounding quotes if present
    if ($val.Length -ge 2 -and (
            ($val.StartsWith('"') -and $val.EndsWith('"')) -or
            ($val.StartsWith("'") -and $val.EndsWith("'")))) {
        $val = $val.Substring(1, $val.Length - 2)
    }
    # PORT is injected by the platform; LLM_PROVIDER is forced to mock below
    if ($key -eq "PORT" -or $key -eq "LLM_PROVIDER") { continue }
    $pairs += "$key=$val"
}

# values not present in .env (or forced)
$pairs += "LLM_PROVIDER=mock"
$pairs += "CORS_ORIGINS=$frontend"
$pairs += "FRONTEND_URL=$frontend"

Write-Host ("Setting {0} env vars on {1}:" -f $pairs.Count, $app) -ForegroundColor Cyan
(($pairs | ForEach-Object { ($_ -split '=', 2)[0] }) -join ", ")

az containerapp update -g $rg -n $app --set-env-vars $pairs

Write-Host "`nEnv var names now on the app (verify all are present):" -ForegroundColor Green
az containerapp show -g $rg -n $app --query "properties.template.containers[0].env[].name" -o tsv
