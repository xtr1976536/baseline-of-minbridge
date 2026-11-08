param([int]$Limit = 0, [switch]$RetryErrors, [string]$Config = 'configs/local.aiwanwu-gpt56sol.json')
$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $PSScriptRoot
$secretPath = Join-Path $env:LOCALAPPDATA 'Codex\secrets\aiwanwu-financereasoning.dpapi'
$encryptedKey = (Get-Content -LiteralPath $secretPath -Raw).Trim()
$credential = New-Object System.Management.Automation.PSCredential('api', (ConvertTo-SecureString $encryptedKey))
$previousKey = $env:FR_GPT56SOL_API_KEY
$exitCode = 1
Push-Location -LiteralPath $projectDir
try {
    $env:FR_GPT56SOL_API_KEY = $credential.GetNetworkCredential().Password
    $runnerArguments = @('-X', 'utf8', '-m', 'fr_repro', 'run', '--config', $Config)
    if ($Limit -gt 0) { $runnerArguments += @('--limit', $Limit) }
    if ($RetryErrors) { $runnerArguments += '--retry-errors' }
    & python @runnerArguments
    $exitCode = $LASTEXITCODE
}
finally {
    $env:FR_GPT56SOL_API_KEY = $previousKey
    Pop-Location
}
exit $exitCode
