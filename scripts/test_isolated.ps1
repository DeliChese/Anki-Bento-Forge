param(
    [string]$Python = "python"
)

$before = @(git status --porcelain)
$dataDir = Join-Path ([System.IO.Path]::GetTempPath()) ("bento-forge-tests-" + [guid]::NewGuid())
$null = New-Item -ItemType Directory -Path $dataDir -Force
$hadDataDir = Test-Path Env:BENTO_FORGE_DATA_DIR
$previousDataDir = $env:BENTO_FORGE_DATA_DIR
$hadTestTmp = Test-Path Env:BENTO_FORGE_TEST_TMP
$previousTestTmp = $env:BENTO_FORGE_TEST_TMP

try {
    foreach ($round in 1..2) {
        $runRoot = Join-Path $dataDir ("run-" + $round)
        $profileDir = Join-Path $runRoot "profile"
        $testTemp = Join-Path $runRoot "pytest"
        $null = New-Item -ItemType Directory -Path $profileDir, $testTemp -Force
        $env:BENTO_FORGE_DATA_DIR = $profileDir
        $env:BENTO_FORGE_TEST_TMP = $testTemp

        Write-Output "Isolated pytest round $round/2"
        & $Python -m pytest --rootdir=tests -p no:cacheprovider -q tests
        $roundExit = $LASTEXITCODE
        if ($roundExit -ne 0) {
            throw "pytest failed in round $round (exit: $roundExit)."
        }

        Remove-Item -LiteralPath $runRoot -Recurse -Force -ErrorAction Stop
        if (Test-Path -LiteralPath $runRoot) {
            throw "Test run directory was not removed: $runRoot"
        }
    }

    $after = @(git status --porcelain)
    if (Compare-Object -ReferenceObject $before -DifferenceObject $after) {
        throw "The test suite changed the worktree."
    }
}
finally {
    if ($hadDataDir) {
        $env:BENTO_FORGE_DATA_DIR = $previousDataDir
    } elseif (Test-Path Env:BENTO_FORGE_DATA_DIR) {
        Remove-Item Env:BENTO_FORGE_DATA_DIR
    }
    if ($hadTestTmp) {
        $env:BENTO_FORGE_TEST_TMP = $previousTestTmp
    } elseif (Test-Path Env:BENTO_FORGE_TEST_TMP) {
        Remove-Item Env:BENTO_FORGE_TEST_TMP
    }
    if (Test-Path -LiteralPath $dataDir) {
        Remove-Item -LiteralPath $dataDir -Recurse -Force -ErrorAction Stop
    }
}
