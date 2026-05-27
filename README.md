# Votaciones CTPRGV

Sistema web de elecciones estudiantiles del CTP Roberto Gamboa Valverde.

## Caracteristicas
- Flujo de votacion por terminal autorizada.
- Panel de mantenimiento administrativo.
- Gestion de candidatos y padron estudiantil.
- Carga masiva de estudiantes (CSV/XLSX).
- Dashboard en tiempo real con metricas de participacion.
- Bitacora de auditoria con filtros (actor, accion, IP, fechas y texto).
- Control de cierre/reapertura de votacion.
- Generacion de corte y acta final en PDF.

## Estructura del proyecto
- `votaciones_backend/app.py`: rutas Flask y reglas de negocio.
- `votaciones_backend/util/database.py`: acceso a datos y mantenimiento de tablas.
- `votaciones_backend/util/pdf_generator.py`: generacion de reportes PDF.
- `votaciones_backend/templates/`: vistas Jinja2.
- `votaciones_backend/static/`: CSS, JS e imagenes.
- `sql/schema.sql`: script oficial de creacion de base de datos.
- `docs/`: documentacion funcional y tecnica.

## Requisitos
- Python 3.13+
- MySQL 8+
- Windows/Linux

## Instalacion rapida (local)
1. Crear entorno virtual:
   - `python -m venv votaciones_backend/.venv`
2. Instalar dependencias:
   - `votaciones_backend/.venv/Scripts/python -m pip install -r votaciones_backend/requirements.txt`
3. Crear BD y usuario:
   - ejecutar `sql/schema.sql` con usuario root de MySQL.
4. Configurar credenciales en `votaciones_backend/config.py`.
5. Iniciar sistema:
   - `powershell -ExecutionPolicy Bypass -File .\run_local.ps1`
6. Abrir:
   - `http://127.0.0.1:5000/votaciones`

## Usuarios de referencia
- Admin del sistema: configurable en tabla `system_users`.
- Rol visor (`viewer`): solo dashboard/corte sin resultados por candidato.
- Rol terminal_admin (`terminal_admin`): autorizacion y gestion de terminales.

## Seguridad y auditoria
- Registro de eventos criticos en `bitacora_critica`.
- Captura de IP real por `X-Forwarded-For`, `X-Real-IP` y fallback a `remote_addr`.
- Auditoria automatica HTTP para endpoints del sistema.

## Versionado
- SemVer operativo en archivo `VERSION`.
- Historial de cambios en `CHANGELOG.md`.

## Documentacion
- [Guia de implementacion](docs/IMPLEMENTACION.md)
- [Manual funcional](docs/MANUAL_FUNCIONAL.md)
- [Arquitectura tecnica](docs/ARQUITECTURA_TECNICA.md)
- [Operacion y mantenimiento](docs/OPERACION_Y_MANTENIMIENTO.md)
