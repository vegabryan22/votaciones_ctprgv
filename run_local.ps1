$ErrorActionPreference = 'Stop'

$py = '.\\votaciones_backend\\.venv\\Scripts\\python.exe'
if (-not (Test-Path $py)) {
  throw 'No existe el entorno virtual en votaciones_backend\\.venv'
}

Set-Location .\votaciones_backend
& $py app.py
