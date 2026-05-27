# Implementacion del sistema

## 1. Preparacion de servidor
- Instalar Python 3.13 y MySQL 8.
- Crear usuario de sistema para ejecutar la app.
- Habilitar firewall para el puerto de publicacion (ej. 5000 o proxy 80/443).

## 2. Base de datos
- Ejecutar `sql/schema.sql` con root.
- Verificar que exista la BD `votaciones` y tablas base.

## 3. Aplicacion
- Clonar repositorio.
- Crear entorno virtual.
- Instalar dependencias desde `requirements.txt`.
- Ajustar `votaciones_backend/config.py` con credenciales correctas.

## 4. Primer arranque
- Iniciar app con `run_local.ps1` (entorno local) o con servicio `gunicorn` en Linux.
- Validar acceso en `/votaciones`.

## 5. Configuracion inicial operativa
- Crear/validar usuarios administrativos en `system_users`.
- Registrar terminales autorizadas.
- Cargar padron de estudiantes.
- Cargar imagenes de partidos/candidatos.

## 6. Buenas practicas de despliegue
- Usar proxy inverso (Nginx/Apache) con HTTPS.
- Reenviar IP real (`X-Forwarded-For`, `X-Real-IP`).
- Respaldar DB diariamente.
- Monitorear bitacora y logs de servicio.

## 7. Cierre de proceso electoral
- Cerrar votacion desde mantenimiento.
- Generar corte y acta final.
- Exportar bitacora para resguardo.
- Ejecutar limpieza anual del padron cuando corresponda.
