# Arquitectura tecnica

## Stack
- Backend: Flask
- Persistencia: MySQL
- Frontend: Jinja2 + Bootstrap + JS
- Graficos: Chart.js

## Componentes
- `app.py`: controladores HTTP y middleware de acceso/auditoria.
- `util/database.py`: operaciones CRUD, inicializacion de tablas, bitacora.
- `util/pdf_generator.py`: generacion de reportes oficiales.

## Modelo de datos principal
- `candidatos`
- `estudiantes`
- `votos`
- `system_users`
- `terminales_votacion`
- `voting_settings`
- `bitacora_critica`

## Auditoria
- Eventos manuales de negocio + eventos HTTP automaticos.
- Resolucion de IP real por headers de proxy.

## Rutas clave
- `/votaciones/*` flujo de voto.
- `/votaciones/mantenimiento*` administracion.
- `/votaciones/bitacora` auditoria.
