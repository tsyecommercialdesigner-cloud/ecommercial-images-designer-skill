$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    $gitVersion = & git --version
    if ($LASTEXITCODE -ne 0 -or $gitVersion -notmatch '^git version ') { throw 'Git is required for isolated tracking and workspace checks' }
    Write-Output "Git runtime: $gitVersion"
    uv run --frozen --no-sync --group dev python -X utf8 -B scripts/validate_skill.py --evals evals/scenarios.json
    if ($LASTEXITCODE -ne 0) { throw 'Package/scenario validation failed' }
    uv run --frozen --no-sync --group dev python -X utf8 -B -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Unit and offline MCP tests failed' }
    $nodeVersion = & node --version
    if ($LASTEXITCODE -ne 0 -or $nodeVersion -notmatch '^v(\d+)\.' -or [int]$Matches[1] -lt 22) {
        throw 'Node.js 22+ is required for the offline Desktop orchestration tests'
    }
    Write-Output "Node runtime: $nodeVersion"
    $testPython = uv run --frozen --no-sync --group dev python -c 'import sys; print(sys.executable)'
    if ($LASTEXITCODE -ne 0) { throw 'Could not resolve the existing test interpreter' }
    $previousTestPython = $env:DSH_TEST_PYTHON
    try {
        $env:DSH_TEST_PYTHON = $testPython.Trim()
        $nodeTests = @(Get-ChildItem -LiteralPath tests -Filter 'test_*.mjs' | Sort-Object Name | ForEach-Object FullName)
        if ($nodeTests.Count -eq 0) { throw 'No offline Node tests discovered' }
        & node --test @nodeTests
        if ($LASTEXITCODE -ne 0) { throw 'Offline Desktop orchestration tests failed' }
    }
    finally { $env:DSH_TEST_PYTHON = $previousTestPython }
}
finally {
    Pop-Location
}
