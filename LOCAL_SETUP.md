# Votaciones - Setup local (Windows)

1) Entorno Python ya creado:
   - `votaciones_backend\\.venv`
   - Dependencias instaladas de `requirements.txt`

2) Configurar MySQL local (usa tu password real de root):

```powershell
powershell -ExecutionPolicy Bypass -File .\votaciones_backend\setup_db.ps1 -RootPassword "TU_PASSWORD_ROOT"
```

3) Iniciar la app:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_local.ps1
```

4) Abrir en navegador:
   - `http://127.0.0.1:5000/votaciones`
