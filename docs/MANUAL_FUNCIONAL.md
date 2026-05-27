# Manual funcional

## Modulos
- Votacion por terminal.
- Dashboard administrativo.
- Candidatos.
- Estudiantes.
- Carga masiva.
- Abstencionistas.
- Mantenimiento del sitio.
- Usuarios y roles.
- Bitacora del sistema.

## Flujo de votacion
1. Terminal autorizada inicia sesion.
2. Se valida cedula del estudiante.
3. Se confirma identidad.
4. Se emite voto.
5. Se muestra confirmacion final.

## Roles
- `admin`: mantenimiento total del sistema.
- `viewer`: consulta restringida de dashboard.
- `terminal_admin`: administracion de terminales y autoregistro.

## Acciones criticas
- Cerrar/Reabrir votacion.
- Reset anual de padron.
- Rotacion de token de terminal.
- Cambio de contrasenas de usuarios.

## Bitacora
- Registra actor, accion, detalle, IP y fecha.
- Permite filtros por actor, accion, IP, rango y texto.
