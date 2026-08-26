param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot "..\dist"),
    [string]$SourceDirectory = (Join-Path $PSScriptRoot "..")
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $SourceDirectory).Path
$output = [System.IO.Path]::GetFullPath($OutputDirectory)
$stage = Join-Path ([System.IO.Path]::GetTempPath()) ("bento-forge-package-" + [guid]::NewGuid())
$runtimeDirectories = @("Language", "audio", "hooks", "mode", "ui", "utils", "workers")
$runtimeJsonFiles = @(
    "utils/ai_config.example.json",
    "utils/ui_theme.json"
)
$requiredRuntimeFiles = @(
    "__init__.py",
    "manifest.json",
    "workers/__init__.py",
    "workers/import_worker.py"
)

function Copy-RuntimeFile {
    param([string]$SourcePath, [string]$RelativePath)

    $destination = Join-Path $stage $RelativePath
    $destinationDirectory = Split-Path -Parent $destination
    New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
    Copy-Item -LiteralPath $SourcePath -Destination $destination -Force
}

try {
    New-Item -ItemType Directory -Path $output -Force | Out-Null
    New-Item -ItemType Directory -Path $stage -Force | Out-Null
    foreach ($directory in $runtimeDirectories) {
        $sourceRoot = Join-Path $root $directory
        if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
            throw "Required runtime directory is missing: $directory"
        }
        foreach ($file in Get-ChildItem -LiteralPath $sourceRoot -Recurse -Force -File) {
            $relativePath = $file.FullName.Substring($root.Length).TrimStart('\', '/')
            $normalizedPath = $relativePath.Replace('\', '/')
            $include = $file.Extension.Equals(".py", [System.StringComparison]::OrdinalIgnoreCase) `
                -or $runtimeJsonFiles.Contains($normalizedPath)
            if ($include) {
                Copy-RuntimeFile -SourcePath $file.FullName -RelativePath $relativePath
            }
        }
    }
    foreach ($item in @("__init__.py", "manifest.json")) {
        $sourcePath = Join-Path $root $item
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
            throw "Required package file is missing: $item"
        }
        Copy-RuntimeFile -SourcePath $sourcePath -RelativePath $item
    }

    foreach ($required in $requiredRuntimeFiles) {
        if (-not (Test-Path -LiteralPath (Join-Path $stage $required) -PathType Leaf)) {
            throw "Required runtime file was not staged: $required"
        }
    }
    $forbiddenFiles = @(
        Get-ChildItem -LiteralPath $stage -Recurse -Force -File |
            Where-Object {
                $_.Extension -in @(".pyc", ".pyo") -or
                $_.FullName -match "[\\/]__pycache__[\\/]" -or
                $_.Name -in @(
                    "ai_config.json", "ai_prompts.json", "factory_state.json",
                    "i18n_config.json", "import_history.json"
                )
            }
    )
    if ($forbiddenFiles.Count -gt 0) {
        $forbiddenList = ($forbiddenFiles.FullName -join ", ")
        throw "Forbidden local/runtime state entered the package stage: $forbiddenList"
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
