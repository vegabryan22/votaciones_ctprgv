param(
  [Parameter(Mandatory=$true)]
  [string]$RootPassword
)

$ErrorActionPreference = 'Stop'
$mysql = 'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe'

if (-not (Test-Path $mysql)) {
  throw "No se encontr? mysql.exe en $mysql"
}

& $mysql -u root -p$RootPassword -e "SELECT VERSION();" | Out-Null
if ($LASTEXITCODE -ne 0) {
  throw "No se pudo autenticar como root en MySQL con la clave proporcionada."
}

& $mysql -u root -p$RootPassword -e @"
CREATE DATABASE IF NOT EXISTS votaciones CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'votaciones'@'localhost' IDENTIFIED BY 'Lr3rBD4Ecmhkd8Pt';
ALTER USER 'votaciones'@'localhost' IDENTIFIED BY 'Lr3rBD4Ecmhkd8Pt';
GRANT ALL PRIVILEGES ON votaciones.* TO 'votaciones'@'localhost';
FLUSH PRIVILEGES;
"@
if ($LASTEXITCODE -ne 0) {
  throw "No se pudo crear/actualizar la base de datos o permisos de usuario."
}

Write-Host 'Base de datos y usuario listos.'
