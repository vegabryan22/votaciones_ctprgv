# Changelog

Todos los cambios relevantes del sistema de votaciones se documentan aqui.

## [1.0.21] - 2026-05-28
### Changed
- Mejora completa de vista móvil en mantenimiento: menú lateral colapsable con botón `Menú`.
- Ajuste de tipografías, espaciados y tamaños de controles para pantallas pequeñas.
- Cierre automático del menú móvil al seleccionar una opción.

## [1.0.20] - 2026-05-28
### Fixed
- El botón `Salir` en sesión de visor ahora usa su endpoint correcto (`/votaciones/visor/logout`).
- Se mantiene `Salir` de admin en su endpoint actual (`/votaciones/logout`).

## [1.0.19] - 2026-05-28
### Changed
- Login de `Visor` unificado al mismo `layout_front` que `Admin` y flujo de votación.
- Rediseño visual de formularios de acceso `Admin` y `Visor` con estilo consistente.
- Header azul ajustado: logos más grandes y más cercanos a los bordes para mejor presencia visual.

## [1.0.18] - 2026-05-28
### Changed
- Se agregó menú rápido en `layout_front` con accesos directos a `Votar`, `Visor` y `Admin`.
- Se excluye explícitamente `Terminal admin` del menú público de la vista de votación.

## [1.0.17] - 2026-05-28
### Changed
- Manual HTML actualizado y alineado al flujo actual del sistema.
- Documentación de autoregistro directo de terminal (sin confirmación manual intermedia).
- Sección de terminales actualizada con eliminación masiva por botón y confirmación.
- Corrección de textos y acentos en contenido del manual.

## [1.0.16] - 2026-05-28
### Changed
- Autoregistro de terminal ahora completa la autorización en el mismo flujo y redirige directo a votar.
- Se elimina el paso intermedio de confirmación manual en login para terminal recién autoregistrada.

## [1.0.15] - 2026-05-28
### Changed
- Módulo de terminales: eliminación masiva simplificada a botón superior con confirmación visual.
- Se eliminó el requisito de escribir `ELIMINAR` para borrar todas las terminales.
- Se retiró la tarjeta inferior de limpieza masiva para una interfaz más limpia.

## [1.0.14] - 2026-05-28
### Added
- Nuevo módulo dedicado de terminales en `/votaciones/terminales` para gestión centralizada.
- Acción masiva para eliminar todas las terminales con confirmación explícita `ELIMINAR`.

### Changed
- Gestión de terminales separada de mantenimiento de sitio para mejorar operación.
- Redirección de crear/editar/rotar/eliminar terminal hacia el nuevo módulo de terminales.
- Menú lateral actualizado con opción `Terminales`.
- Etiquetas de UI renombradas de `Abstencionistas` a `Abstencionismo`.

## [1.0.12] - 2026-05-28
### Fixed
- Corrección de condición de carrera en registro de voto entre terminales concurrentes.
- Confirmación "Gracias por votar" solo cuando el voto se guarda realmente en base de datos.
- Manejo explícito de duplicado por estudiante (error 1062) para mostrar mensaje de "ya votó".

## [1.0.11] - 2026-05-28
### Changed
- Demo de vista de votación de estudiante movida a modal en mantenimiento de candidatos.
- Limpieza de la pantalla principal de candidatos para reducir saturación visual.

## [1.0.10] - 2026-05-28
### Changed
- Reemplazo de vista previa repetida por candidato en mantenimiento por una demo unificada de la vista del estudiante para votar.
- Ajuste de presentación de demo de partidos para validar visualmente cómo se muestran en terminal.

## [1.0.9] - 2026-05-28
### Added
- Manual de uso completo en formato HTML accesible desde la aplicación (`/votaciones/manual`).
- Enlace directo a manual en el menú de mantenimiento.
- Vista previa de candidato "como se verá en terminal" en mantenimiento de candidatos.

### Changed
- Ajuste de visualización de imágenes de partidos para verse completas (sin recorte agresivo) en mantenimiento y vista de votación.
- Tarjetas de imagen de candidato en votación con proporción estable para consistencia visual.

## [1.0.8] - 2026-05-28
### Changed
- Reorganizacion del dashboard para reducir huecos y mejorar simetria entre contenedores.
- Reubicacion y compactacion de controles de accion para mejor balance visual.
- Mejora del formateo en cuadros de estadisticas y tarjetas de resumen rapido.
- Manejo robusto de valores nulos en estadisticas (mostrar 0.00% en lugar de null%).
- Estado visual de graficas sin datos con mensajes compactos y centrados.
- Movimiento de configuracion de minimo de terminales a mantenimiento de sitio.

## [1.0.7] - 2026-05-28
### Changed
- Compactación adicional del panel "Control de Elección" (menos padding y separación interna).
- Ajuste de alturas de input/botón de umbral para vista más densa.
- Mejora de ubicación visual en cabecera y menor espacio superior del contenido.

## [1.0.6] - 2026-05-28
### Changed
- Reubicación de botones de reportes en una barra de acciones más ordenada.
- Mejora visual de botones (ancho consistente, iconos y espaciado).
- Ajuste responsive para mejor presentación en móvil.

## [1.0.5] - 2026-05-28
### Fixed
- Corrección de caracteres UTF-8 dañados en la plantilla base de mantenimiento (`layout.html`).
- Restauración de textos con acentos correctos en menú y comentarios de plantilla.

## [1.0.4] - 2026-05-28
### Changed
- Rediseño compacto del panel "Control de Elección" para mejorar legibilidad y reducir altura visual.
- Semáforo de estado en formato píldora (verde/amarillo/rojo) con jerarquía visual más clara.
- Reglas de preparación mostradas en chips compactos en lugar de bloques extensos.

## [1.0.3] - 2026-05-28
### Added
- Visualizacion de version del sistema en el pie de pagina (layouts de mantenimiento y votacion), leida desde archivo `VERSION`.

### Changed
- Mejora visual del dashboard: tarjetas mas limpias, mejor espaciado y composicion mas consistente.
- Reduccion del tamano visual de graficos para una lectura mas comoda.
- Ajustes de colores/leyendas en Chart.js para mayor claridad.

## [1.0.2] - 2026-05-28
### Added
- Semaforo operativo (verde/amarillo/rojo) para evaluar preparacion antes de abrir votacion.
- Validaciones de apertura: minimo de candidatos activos, presencia obligatoria de "Voto en Blanco", minimo de terminales activas y padron con estudiantes.
- Parametro configurable de minimo de terminales activas desde mantenimiento.

### Changed
- Estado por defecto de una eleccion nueva a votacion cerrada (modo seguro).
- Bitacora de apertura/bloqueo de apertura con detalle de metricas y reglas evaluadas.

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
