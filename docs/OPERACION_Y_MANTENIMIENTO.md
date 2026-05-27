# Operacion y mantenimiento

## Respaldo recomendado
- Dump diario de MySQL.
- Respaldo de `static/uploads`.
- Resguardo periodico de bitacora.

## Checklist diario
- Estado de terminales.
- Eventos inusuales en bitacora.
- Salud de DB y espacio en disco.

## Checklist antes de votacion
- Padron cargado.
- Candidatos activos validados.
- Terminales y tokens operativos.
- Usuarios admin activos.

## Incidentes comunes
- Error de tablas inexistentes: ejecutar `sql/schema.sql`.
- Error de dependencias: reinstalar `requirements.txt`.
- IP incorrecta en bitacora: revisar proxy headers.

## Post evento
- Cerrar votacion.
- Generar acta final.
- Exportar abstencionistas.
- Congelar respaldos del evento.
