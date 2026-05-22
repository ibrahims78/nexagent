$configPath = "$env:APPDATA\PCCommander\config.json"
if (Test-Path $configPath) {
    $content = Get-Content $configPath -Raw -Encoding UTF8
    $json = $content | ConvertFrom-Json
    
    # Fix model_gemini
    if ($json.ai) {
        $json.ai.model_gemini = "gemini-2.5-flash-preview-05-20"
        if (-not $json.ai.provider) { $json.ai.provider = "gemini" }
    }
    
    $json | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
    Write-Host "SUCCESS: config.json updated - model set to gemini-2.5-flash-preview-05-20"
} else {
    Write-Host "WARNING: config.json not found at $configPath"
}
