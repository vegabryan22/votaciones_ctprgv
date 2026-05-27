# Changelog

Todos los cambios relevantes del sistema de votaciones se documentan aqui.

## [1.0.0] - 2026-05-27
### Added
- Estructura de repositorio local/GitHub con versionado inicial.
- Documentacion tecnica, funcional y de implementacion.
- Script oficial `sql/schema.sql` para despliegue de base de datos.
- Auditoria expandida de bitacora con filtros avanzados.
- Captura de IP real via `X-Forwarded-For` y `X-Real-IP`.
- Registro automatico de eventos HTTP de negocio.
- Ruta de mantenimiento anual `reset-padron`.

### Changed
- Unificacion visual del panel de mantenimiento.
- Formato de actor de bitacora a `usuario (rol)`.
- Ajuste de visualizacion de logos de partidos (sin recorte).
- Inicializacion automatica de tablas core en arranque.

### Fixed
- Error 404 en `/votaciones/mantenimiento/reset-padron`.
- Errores de tablas faltantes (`candidatos`, `estudiantes`).
- Error por dependencia faltante `openpyxl`.
- Duplicidad de mensajes flash en login de terminal.

## [0.9.x] - 2026-05 (reconstruido)
### Added
- Modulo de mantenimiento de sitio y gestion de terminales.
- Roles `viewer` y `terminal_admin`.
- Dashboard con ocultamiento de resultados mientras la votacion esta abierta.
- Generacion de reportes PDF (corte y acta final).

## [0.8.x] - 2025 (reconstruido)
### Added
- Carga masiva de estudiantes desde archivos.
- Mantenimiento de candidatos y estudiantes.
- Flujo completo de votacion por cedula.

## [0.7.x] - 2024 (reconstruido)
### Added
- Base funcional inicial de votaciones (Flask + MySQL).
- Plantillas HTML iniciales y recursos estaticos.

> Nota: las versiones anteriores a 1.0.0 son reconstruccion historica basada en artefactos de codigo/fechas de archivos y pueden no coincidir 1:1 con el historial original del servidor.
## [1.0.1] - 2026-05-27
### Fixed
- Corrección de textos con caracteres dañados (acentos) en mensajes y formularios.
- Eliminación de mensaje flash duplicado en login administrativo (`/votaciones/login`).
- Homologación de etiquetas de "Contraseña" y "Sesión" en vistas administrativas.
