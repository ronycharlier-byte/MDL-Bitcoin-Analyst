param(
  [string]$OutputSchema = "gpt_action_openapi.cloudflare.deployed.yaml"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "Checking Cloudflare Wrangler authentication..."
$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$whoami = & npx wrangler whoami 2>&1
$whoamiExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
if ($whoamiExitCode -ne 0 -or ($whoami -join "`n") -match "not authenticated") {
  Write-Host "Wrangler is not authenticated. Starting Cloudflare login..."
  $ErrorActionPreference = "Continue"
  & npx wrangler login
  $loginExitCode = $LASTEXITCODE
  $ErrorActionPreference = $previousErrorActionPreference
  if ($loginExitCode -ne 0) {
    throw "Cloudflare login failed or was not completed."
  }
}

Write-Host "Deploying Cloudflare Worker..."
$ErrorActionPreference = "Continue"
$deployOutput = & npx wrangler deploy 2>&1
$deployExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
$deployText = $deployOutput -join "`n"
Write-Host $deployText

if ($deployExitCode -ne 0) {
  throw "Wrangler deploy failed."
}

$match = [regex]::Match($deployText, "https://[A-Za-z0-9.-]+\.workers\.dev")
if (-not $match.Success) {
  throw "Could not find workers.dev URL in wrangler deploy output."
}

$workerUrl = $match.Value.TrimEnd("/")
Write-Host "Detected Worker URL: $workerUrl"

$templatePath = Join-Path $root "gpt_action_openapi.cloudflare.yaml"
$outputPath = Join-Path $root $OutputSchema

$schema = Get-Content -LiteralPath $templatePath -Raw
$schema = $schema -replace "https://quant-btc-model-lite\.your-workers-subdomain\.workers\.dev", $workerUrl
$schema | Set-Content -LiteralPath $outputPath -Encoding utf8

Write-Host "Wrote GPT Action schema: $outputPath"
Write-Host "Upload this generated schema to GPT Actions."
