param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot "..\dist"),
    [string]$SourceDirectory = (Join-Path $PSScriptRoot "..")
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $SourceDirectory).Path
$output = [System.IO.Path]::GetFullPath($OutputDirectory)
$stage = Join-Path ([System.IO.Path]::GetTempPath()) ("bento-forge-package-" + [guid]::NewGuid())

try {
    New-Item -ItemType Directory -Path $output -Force | Out-Null
    New-Item -ItemType Directory -Path $stage -Force | Out-Null
    foreach ($item in @("Language", "audio", "hooks", "mode", "ui", "workers")) {
        Copy-Item -LiteralPath (Join-Path $root $item) -Destination $stage -Recurse -Force
    }
    $utilsStage = Join-Path $stage "utils"
    New-Item -ItemType Directory -Path $utilsStage -Force | Out-Null
    Copy-Item -Path (Join-Path $root "utils\*") -Destination $utilsStage -Recurse -Force `
        -Exclude "ai_config.json", "ai_prompts.json", "i18n_config.json", "factory_state.json"
    foreach ($item in @("__init__.py", "manifest.json")) {
        Copy-Item -LiteralPath (Join-Path $root $item) -Destination $stage -Force
    }

    $cacheDirectories = @(
        Get-ChildItem -LiteralPath $stage -Recurse -Force -Directory |
            Where-Object { $_.Name -eq "__pycache__" } |
            Sort-Object { $_.FullName.Length } -Descending
    )
    foreach ($cacheDirectory in $cacheDirectories) {
        Remove-Item -LiteralPath $cacheDirectory.FullName -Recurse -Force
    }
    $bytecodeFiles = @(
        Get-ChildItem -LiteralPath $stage -Recurse -Force -File |
            Where-Object { $_.Extension -in @(".pyc", ".pyo") }
    )
    foreach ($bytecodeFile in $bytecodeFiles) {
        Remove-Item -LiteralPath $bytecodeFile.FullName -Force
    }

    $artifact = Join-Path $output "bento-forge.ankiaddon"
    if (Test-Path -LiteralPath $artifact) { Remove-Item -LiteralPath $artifact -Force }
    $zipArtifact = Join-Path $output "bento-forge.zip"
    if (Test-Path -LiteralPath $zipArtifact) { Remove-Item -LiteralPath $zipArtifact -Force }
    Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zipArtifact -CompressionLevel Optimal
    Move-Item -LiteralPath $zipArtifact -Destination $artifact -Force
    $hash = (Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath ($artifact + ".sha256") -Value "$hash  bento-forge.ankiaddon" -NoNewline

    $manifest = Get-Content -Raw -Encoding utf8 (Join-Path $root "manifest.json") | ConvertFrom-Json
    $sbom = [ordered]@{
        bomFormat = "CycloneDX"; specVersion = "1.5"; version = 1
        metadata = @{ component = @{ type = "application"; name = $manifest.name; version = $manifest.version } }
        components = @($manifest.dependencies.packages | ForEach-Object { @{ type = "library"; name = $_ } })
    }
    $sbom | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $output "bento-forge.sbom.json") -Encoding utf8
    Write-Output "Built $artifact with SHA-256 $hash"
}
finally {
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue }
}
