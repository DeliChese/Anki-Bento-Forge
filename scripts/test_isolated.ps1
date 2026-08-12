param(
    [string]$Python = "python"
)

$before = @(git status --porcelain)
$dataDir = Join-Path ([System.IO.Path]::GetTempPath()) ("bento-forge-tests-" + [guid]::NewGuid())
$pytestTemp = Join-Path $dataDir "pytest"
$null = New-Item -ItemType Directory -Path $dataDir -Force
$env:BENTO_FORGE_DATA_DIR = $dataDir

try {
    & $Python -m pytest --rootdir=tests --basetemp $pytestTemp -p no:cacheprovider -q tests
    $firstExit = $LASTEXITCODE
    & $Python -m pytest --rootdir=tests --basetemp $pytestTemp -p no:cacheprovider -q tests
    $secondExit = $LASTEXITCODE
    $after = @(git status --porcelain)

    if (Compare-Object -ReferenceObject $before -DifferenceObject $after) {
        throw "The test suite changed the worktree."
    }
    if ($firstExit -ne 0 -or $secondExit -ne 0) {
        throw "pytest failed (first run: $firstExit; second run: $secondExit)."
    }
}
finally {
    Remove-Item -LiteralPath $dataDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item Env:BENTO_FORGE_DATA_DIR -ErrorAction SilentlyContinue
}
