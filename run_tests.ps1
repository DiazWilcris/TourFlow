$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    python -m venv (Join-Path $PSScriptRoot ".venv")
}

& $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
Push-Location (Join-Path $PSScriptRoot "Selenium")
& $venvPython -m pytest tests/ --rootdir . --html=..\reports\reporte.html --self-contained-html -v
$testExitCode = $LASTEXITCODE
Pop-Location
exit $testExitCode
