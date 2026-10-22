$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    uv run --frozen --no-sync --group dev python -X utf8 -B scripts/validate_skill.py --evals evals/scenarios.json
    if ($LASTEXITCODE -ne 0) { throw 'Package/scenario validation failed' }
    uv run --frozen --no-sync --group dev python -X utf8 -B -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Unit and offline MCP tests failed' }
}
finally {
    Pop-Location
}
