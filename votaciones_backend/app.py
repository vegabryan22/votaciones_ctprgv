from datetime import datetime
import io
import os
import csv
from functools import wraps
from flask import Flask, flash, jsonify, request, render_template, send_file, redirect, session, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

from werkzeug.utils import secure_filename
import pandas as pd
import util.database as db
import util.pdf_generator as pdf_gen

app = Flask(__name__, static_url_path='/votaciones_backend/static')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['APPLICATION_ROOT'] = '/votaciones'
app.secret_key = '123'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def _read_system_version():
    root_dir = os.path.dirname(BASE_DIR)
    version_file = os.path.join(root_dir, 'VERSION')
    try:
        with open(version_file, 'r', encoding='utf-8') as fh:
            version = fh.read().strip()
            return version or 'dev'
    except Exception:
        return 'dev'


@app.context_processor
def inject_system_version():
    return {'system_version': _read_system_version()}


def _safe_candidate_image_name(raw_value):
    image_name = os.path.basename((raw_value or '').strip())
    if not image_name:
        return 'default.png'
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
    return image_name if os.path.exists(image_path) else 'default.png'


def _normalize_candidate_images(candidates):
    normalized = []
    for c in candidates or []:
        item = dict(c)
        item['imagen'] = _safe_candidate_image_name(item.get('imagen'))
        normalized.append(item)
    return normalized

db.ensure_voting_settings()
db.ensure_terminales_table()
db.ensure_bitacora_table()
db.ensure_system_users_table()
db.ensure_core_tables()



@app.route('/votaciones')
def index():
    return votar()


@app.route('/votaciones/')
def index_slash():
    return votar()

login_manager = LoginManager()
login_manager.init_app(app)

TERMINAL_ADMIN_USER = os.getenv('TERMINAL_ADMIN_USER', 'terminaladmin')
TERMINAL_ADMIN_PASS = os.getenv('TERMINAL_ADMIN_PASS', 'Cambiar-12345')
VIEWER_USER = os.getenv('VIEWER_USER', 'visor')
VIEWER_PASS = os.getenv('VIEWER_PASS', 'Cambiar-12345')
db.ensure_builtin_role_user(TERMINAL_ADMIN_USER, TERMINAL_ADMIN_PASS, 'terminal_admin')
db.ensure_builtin_role_user(VIEWER_USER, VIEWER_PASS, 'viewer')

VIEWER_ALLOWED_ENDPOINTS = {
    'viewer_login',
    'viewer_logout',
    'viewer_dashboard',
    'voting_stats',
    'descargar_corte',
    'static',
}

AUTO_AUDIT_EXCLUDED_ENDPOINTS = {
    'static',
    'terminal_ping',
}

class User(UserMixin):
    def __init__(self, id, username, role='admin'):
        self.id = id
        self.username = username
        self.role = role

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    user = db.get_system_user_by_id(user_id)
    if not user:
        return None
    return User(user['id'], user['username'], user.get('role', 'admin'))


def _current_terminal():
    terminal_id = session.get('terminal_id')
    if not terminal_id:
        return None
    terminal = db.obtener_terminal_por_id(terminal_id)
    if not terminal:
        session.pop('terminal_id', None)
        session.pop('terminal_code', None)
        return None
    if not terminal.get('activa'):
        session.pop('terminal_id', None)
        session.pop('terminal_code', None)
        return None
    return terminal


def require_terminal_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        terminal = _current_terminal()
        if not terminal:
            if request.path.startswith('/votaciones/terminal/'):
                return fn(*args, **kwargs)
            flash('Terminal no autorizada. Ingrese codigo y token de terminal.', 'error')
            return redirect(url_for('terminal_login', next=request.path))
        db.marcar_terminal_en_linea(terminal['id'])
        return fn(*args, **kwargs)
    return wrapper


def terminal_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('terminal_admin_auth'):
            return redirect(url_for('terminal_admin_login'))
        return fn(*args, **kwargs)
    return wrapper


def dashboard_access_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get('viewer_auth') or session.get('_user_id'):
            return fn(*args, **kwargs)
        return redirect(url_for('viewer_login'))
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('_user_id'):
            return redirect(url_for('login'))
        if session.get('user_role') != 'admin':
            flash('Acceso solo para administradores.', 'error')
            return redirect(url_for('mantenimiento'))
        return fn(*args, **kwargs)
    return wrapper


def _actor_name():
    if session.get('terminal_admin_auth'):
        return f"{session.get('terminal_admin_user', 'unknown')} (terminal_admin)"
    return f"{session.get('user_name', 'unknown')} ({session.get('user_role', 'admin')})"


def _current_actor_for_audit():
    if session.get('terminal_admin_auth'):
        return f"{session.get('terminal_admin_user', 'unknown')} (terminal_admin)"
    if session.get('viewer_auth'):
        return f"{session.get('viewer_user', 'unknown')} (viewer)"
    if session.get('_user_id'):
        return f"{session.get('user_name', session.get('_user_id'))} ({session.get('user_role', 'admin')})"
    if session.get('terminal_id'):
        return f"{session.get('terminal_code', session.get('terminal_id'))} (terminal)"
    return "anon"


def _client_ip():
    # Soporta proxys inversos (X-Forwarded-For / X-Real-IP) y fallback local.
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        first = xff.split(',')[0].strip()
        if first:
            return first
    xri = request.headers.get('X-Real-IP', '').strip()
    if xri:
        return xri
    return (request.remote_addr or '').strip()


def _voting_is_closed():
    return bool(db.get_voting_status().get("voting_closed"))


def _require_voting_closed_for_change(action_name):
    if not _voting_is_closed():
        flash('No se permite modificar esta información mientras la votación está ABIERTA.', 'error')
        db.registrar_evento_critico(
            _actor_name(),
            'bloqueo_operacion_por_votacion_abierta',
            f'operacion={action_name}',
            _client_ip()
        )
        return False
    return True


@app.before_request
def restrict_viewer_scope():
    # Si la sesion es de visor, bloquear cualquier ruta fuera de su alcance.
    if session.get('viewer_auth'):
        endpoint = request.endpoint or ''
        if endpoint not in VIEWER_ALLOWED_ENDPOINTS:
            flash('Acceso no permitido para usuario visor.', 'error')
            return redirect(url_for('viewer_dashboard'))


@app.after_request
def registrar_evento_sistema(response):
    try:
        # Auditoria automatica de endpoints de negocio.
        path = request.path or ''
        endpoint = request.endpoint or ''
        if not path.startswith('/votaciones'):
            return response
        if endpoint in AUTO_AUDIT_EXCLUDED_ENDPOINTS:
            return response
        if request.method == 'GET' and response.status_code < 400:
            return response

        actor = _current_actor_for_audit()
        accion = f"http_{request.method.lower()}_{endpoint or 'unknown'}"
        detalle = f"path={path}; status={response.status_code}"
        db.registrar_evento_critico(actor, accion, detalle, _client_ip())
    except Exception:
        # Nunca romper el request por auditoria.
        pass
    return response


@app.route('/votaciones/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.authenticate_system_user(username, password, role='admin')
        if user:
            login_user(User(user['id'], user['username'], user.get('role', 'admin')))
            session['user_role'] = user.get('role', 'admin')
            session['user_name'] = user.get('username')
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('mantenimiento'))
        else:
            flash('Credenciales incorrectas', 'error')
    return render_template('login.html')


@app.route('/votaciones/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_role', None)
    session.pop('user_name', None)
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('login'))

@app.route('/votaciones/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect('/votaciones/register')

        success, message = db.register_user(username, password)

        if success:
            flash(message, 'success')
            return redirect('/votaciones/login')
        else:
            flash(message, 'error')
            return redirect('/votaciones/register')

    return render_template('register.html')


@app.route('/votaciones/api/voting-stats')
@dashboard_access_required
def voting_stats():
    status = db.get_voting_status()
    # El visor nunca ve resultados por candidato.
    if session.get('viewer_auth'):
        candidate_stats = []
    else:
        candidate_stats = db.get_voting_stats_by_candidate() if status["voting_closed"] else []
    candidate_stats = _normalize_candidate_images(candidate_stats)
    participation_stats = db.get_participation_stats()
    level_stats = db.get_participation_by_level()
    return jsonify({
        'voting_closed': status["voting_closed"],
        'is_viewer': bool(session.get('viewer_auth')),
        'candidates': candidate_stats,
        'participation': participation_stats,
        'levels': level_stats
    })


@app.route('/votaciones/votar', methods=['GET', 'POST'])
@require_terminal_auth
def votar():
    if _voting_is_closed():
        flash('La votación está cerrada. No se pueden recibir nuevos votos.', 'error')
        return redirect(url_for('mantenimiento'))
    if request.method == 'POST':
        cedula = (request.form.get('cedula') or '').strip()
        cedula_normalizada = ''.join(ch for ch in cedula if ch.isalnum())
        estudiante = db.obtener_estudiante_por_cedula(cedula_normalizada)
        if estudiante:
            if db.ya_voto(estudiante['id']):
                flash('Ya has votado. No puedes votar más de una vez.', 'error')
                return redirect(url_for('votar'))
            session['estudiante_id'] = estudiante['id']
            return render_template('confirmar_estudiante.html', estudiante=estudiante)
        else:
            flash('Estudiante no encontrado', 'error')
            return redirect(url_for('votar'))
    return render_template('solicitar_cedula.html')


@app.route('/votaciones/descargar_acta')
@dashboard_access_required
def descargar_acta():
    if session.get('viewer_auth'):
        flash('El usuario visor no puede generar acta final.', 'error')
        return redirect(url_for('viewer_dashboard'))
    status = db.get_voting_status()
    if not status["voting_closed"]:
        flash('El acta final solo se puede generar cuando la votacion este cerrada.', 'error')
        return redirect(url_for('mantenimiento'))
    datos = db.obtener_datos_dashboard()
    pdf_bytes = pdf_gen.generar_pdf_acta(datos)
    # Obtener la fecha actual
    fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Concatenar la fecha actual al nombre del archivo
    download_name = f'ActaFinalCierre_{fecha_actual}.pdf'
    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=download_name,
        mimetype='application/pdf'
    )

@app.route('/votaciones/descargar_corte')
@dashboard_access_required
def descargar_corte():
    # Corte sin informacion de candidatos (solo participacion/abstencion y nivel).
    datos_completos = db.obtener_datos_dashboard()
    datos = {
        "votos_por_candidato": [],
        "participacion": datos_completos.get("participacion"),
        "votos_por_nivel": datos_completos.get("votos_por_nivel", [])
    }
    pdf_bytes = pdf_gen.generar_pdf_corte(datos)
    # Obtener la fecha actual
    fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M")
    
    # Concatenar la fecha actual al nombre del archivo
    download_name = f'Corte_{fecha_actual}.pdf'
    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=download_name,
        mimetype='application/pdf'
    )

@app.route('/votaciones/candidatos', methods=['GET', 'POST'])
@admin_required
def candidatos():
    if request.method == 'POST':
        if not _require_voting_closed_for_change('candidatos'):
            return redirect(url_for('candidatos'))
        candidato_id = request.form.get('candidato_id')
        nombre = request.form['nombre']
        imagen = request.files.get('imagen')
        filename = None

        if imagen and imagen.filename:
            filename = secure_filename(imagen.filename)
            imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen.save(imagen_path)

        if candidato_id:
            db.actualizar_candidato(candidato_id, nombre, filename)
        else:
            db.registrar_candidato(nombre, filename)

        flash('Operación completada correctamente', 'success')
        return redirect(url_for('candidatos'))
    else:
        candidatos = _normalize_candidate_images(db.obtener_candidatos())
        return render_template('mantenimiento_candidatos.html', candidatos=candidatos)


@app.route('/votaciones/actualizar_candidato/<int:id>', methods=['GET', 'POST'])
@admin_required
def actualizar_candidato(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        imagen = request.files['imagen']
        filename = secure_filename(imagen.filename) if imagen else None

        if filename:
            imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen.save(imagen_path)
        db.actualizar_candidato(id, nombre, filename if filename else None)
        flash('Candidato actualizado correctamente', 'success')
        return redirect(url_for('candidatos'))
    else:
        candidato = db.obtener_candidato_por_id(id)
        return render_template('actualizar_candidato.html', candidato=candidato)


@app.route('/votaciones/eliminar_candidato/<int:id>', methods=['POST'])
@admin_required
def eliminar_candidato(id):
    if not _require_voting_closed_for_change('eliminar_candidato'):
        return redirect(url_for('candidatos'))
    success, message = db.eliminar_candidato(id)
    if not success:
        flash(message, 'error')
    else:
        flash('Candidato eliminado correctamente', 'success')
    return redirect(url_for('candidatos'))


@app.route('/votaciones/mostrar_candidatos', methods=['GET'])
@require_terminal_auth
def mostrar_candidatos():
    if _voting_is_closed():
        flash('La votación está cerrada. No se pueden recibir nuevos votos.', 'error')
        return redirect(url_for('votar'))
    if 'estudiante_id' not in session:
        return redirect(url_for('votar'))
    
    candidatos = _normalize_candidate_images(db.obtener_candidatos_activos())
    return render_template('lista_candidatos.html', candidatos=candidatos)


@app.route('/votaciones/procesar_voto', methods=['POST'])
@require_terminal_auth
def procesar_voto():
    if _voting_is_closed():
        flash('La votación está cerrada. No se registró el voto.', 'error')
        return redirect(url_for('votar'))
    candidato_id = request.form.get('candidato_id')
    estudiante_id = session.pop('estudiante_id', None)
    if not estudiante_id:
        flash("No se encontró una sesión de voto válida.", 'error')
        return redirect(url_for('votar'))

    ok, msg = db.registrar_voto(estudiante_id, candidato_id)
    if ok:
        return redirect(url_for('gracias'))

    flash(msg or "Error en la votación.", 'error')
    return redirect(url_for('votar'))


@app.route('/votaciones/estudiantes', methods=['GET', 'POST'])
@admin_required
def estudiantes():
    if request.method == 'POST':
        if not _require_voting_closed_for_change('estudiantes'):
            return redirect(url_for('estudiantes'))
        id_estudiante = request.form.get('id_estudiante')
        nombre = request.form['nombre']
        apellido1 = request.form['apellido1']
        apellido2 = request.form['apellido2']
        nivel = request.form['nivel']
        cedula = request.form['cedula']

        if id_estudiante:
            db.actualizar_estudiante(id_estudiante, nombre, apellido1, apellido2, nivel, cedula)
        else:
            db.agregar_estudiante(nombre, apellido1, apellido2, nivel, cedula)

        flash('Operación completada correctamente', 'success')
        return redirect(url_for('estudiantes'))
    
    estudiantes = db.obtener_todos_los_estudiantes()
    return render_template('mantenimiento_estudiantes.html', estudiantes=estudiantes)


@app.route('/votaciones/upload', methods=['GET', 'POST'])
@admin_required
def upload_file():
    if request.method == 'POST':
        if not _require_voting_closed_for_change('carga_padron'):
            return redirect(url_for('upload_file'))
        if 'file' not in request.files:
            flash('No se selecciono ningun archivo', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No se selecciono ningun archivo', 'error')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in ('xlsx', 'xls', 'csv'):
            flash('Formato no permitido. Usa .xlsx, .xls o .csv', 'error')
            return redirect(request.url)

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            result = db.importar_estudiantes_desde_excel(file_path)
            flash(
                f"Carga completada: {result['upserted']} registros procesados, "
                f"{result['empty_rows']} filas omitidas de {result['total_rows']}.",
                'success'
            )
        except Exception as e:
            flash(f'Error al importar archivo: {e}', 'error')

        return redirect(url_for('upload_file'))

    return render_template('upload.html')


@app.route('/votaciones/upload/plantilla-csv')
@admin_required
def plantilla_estudiantes_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nombre', 'Apellido1', 'Apellido2', 'Cedula', 'Nivel'])
    writer.writerow(['AARON', 'SOTO', 'NAVARRO', '120420584', '10-5'])
    writer.writerow(['MARIA', 'ROJAS', 'MORA', '116780923', '11-2'])
    mem = io.BytesIO(output.getvalue().encode('utf-8-sig'))
    mem.seek(0)
    return send_file(
        mem,
        as_attachment=True,
        download_name='plantilla_padron_estudiantes.csv',
        mimetype='text/csv'
    )


@app.route('/votaciones/upload/plantilla-xlsx')
@admin_required
def plantilla_estudiantes_xlsx():
    df = pd.DataFrame([
        {'Nombre': 'AARON', 'Apellido1': 'SOTO', 'Apellido2': 'NAVARRO', 'Cedula': '120420584', 'Nivel': '10-5'},
        {'Nombre': 'MARIA', 'Apellido1': 'ROJAS', 'Apellido2': 'MORA', 'Cedula': '116780923', 'Nivel': '11-2'}
    ])
    mem = io.BytesIO()
    with pd.ExcelWriter(mem, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Padron')
    mem.seek(0)
    return send_file(
        mem,
        as_attachment=True,
        download_name='plantilla_padron_estudiantes.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/votaciones/gracias')
def gracias():
    return render_template('gracias.html')


@app.route('/votaciones/mantenimiento')
@admin_required
def mantenimiento():
    voting_status = db.get_voting_status()
    readiness = db.get_opening_readiness()
    return render_template(
        'mantenimiento.html',
        voting_closed=voting_status["voting_closed"],
        is_viewer=False,
        readiness=readiness
    )


@app.route('/votaciones/manual')
@admin_required
def manual_uso():
    return render_template('manual.html')


def _incidencias_hoy():
    fecha = "2026-05-29"
    cambios_cedula = [
        {"id": 754, "nombre": "KENNETH JOSE MOLINA MEJIA", "cedula_anterior": "YR202318692", "cedula_nueva": "155812925121"},
        {"id": 672, "nombre": "RASHEL REGINA FLORES ROJAS", "cedula_anterior": "YR202222970", "cedula_nueva": "155830545317"},
        {"id": 801, "nombre": "STEFANY MASSIEL RODRIGUEZ HERRERA", "cedula_anterior": "YR202318672", "cedula_nueva": "C03802521"},
        {"id": 476, "nombre": "CLAUDIA GARCIA SIERRA", "cedula_anterior": "YR202434360", "cedula_nueva": "119201213515"},
        {"id": 553, "nombre": "KEVIN DAVID GONZALEZ GONZALEZ", "cedula_anterior": "YR202318722", "cedula_nueva": "186202007307"},
        {"id": 157, "nombre": "HARLYNG JOHEL CRUZ GUTIERREZ", "cedula_anterior": "YR202235905", "cedula_nueva": "155827736901"},
    ]
    inserciones = [
        {"id": 1167, "nombre": "ISAAC GAEL", "apellido1": "HIDALGO", "apellido2": "UGARTE", "cedula": "121140699", "nivel": "8-4B"},
        {"id": 1168, "nombre": "SAMUEL JOSUE", "apellido1": "VARGAS", "apellido2": "ALPIZAR", "cedula": "121930290", "nivel": "7-2B"},
    ]
    return fecha, cambios_cedula, inserciones


@app.route('/votaciones/incidencias')
@admin_required
def incidencias_hoy():
    fecha, cambios_cedula, inserciones = _incidencias_hoy()
    return render_template(
        'incidencias.html',
        fecha=fecha,
        cambios_cedula=cambios_cedula,
        inserciones=inserciones
    )


@app.route('/votaciones/incidencias/pdf')
@admin_required
def incidencias_hoy_pdf():
    fecha, cambios_cedula, inserciones = _incidencias_hoy()
    pdf_bytes = pdf_gen.generar_pdf_incidencias(fecha, cambios_cedula, inserciones)
    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=f'informe_incidencias_{fecha}.pdf',
        mimetype='application/pdf'
    )


@app.route('/votaciones/visor/login', methods=['GET', 'POST'])
def viewer_login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        user = db.authenticate_system_user(username, password, role='viewer')
        if user:
            session['viewer_auth'] = True
            session['viewer_user'] = user['username']
            db.registrar_evento_critico(f"{user['username']} (viewer)", 'login_viewer', 'Inicio sesión visor dashboard', _client_ip())
            return redirect(url_for('viewer_dashboard'))
        flash('Credenciales invalidas', 'error')
    return render_template('viewer_login.html')


@app.route('/votaciones/visor/logout', methods=['POST'])
def viewer_logout():
    if session.get('viewer_auth'):
        db.registrar_evento_critico(
            f"{session.get('viewer_user', 'unknown')} (viewer)",
            'logout_viewer',
            'Cierre sesión visor dashboard',
            _client_ip()
        )
    session.pop('viewer_auth', None)
    session.pop('viewer_user', None)
    flash('Sesión cerrada.', 'success')
    return redirect(url_for('viewer_login'))


@app.route('/votaciones/visor/dashboard')
@dashboard_access_required
def viewer_dashboard():
    voting_status = db.get_voting_status()
    readiness = db.get_opening_readiness()
    return render_template(
        'mantenimiento.html',
        voting_closed=voting_status["voting_closed"],
        is_viewer=True,
        readiness=readiness
    )


@app.route('/votaciones/mantenimiento/cerrar-votacion', methods=['POST'])
@admin_required
def cerrar_votacion():
    if _voting_is_closed():
        flash('La votación ya está cerrada.', 'warning')
        return redirect(url_for('mantenimiento'))
    db.set_voting_closed(True)
    db.registrar_evento_critico(
        _actor_name(),
        'cerrar_votacion',
        f'Se cerró la votación; votos_totales={db.count_votes_total()}',
        _client_ip()
    )
    flash('Votacion cerrada. Ahora se pueden ver resultados finales.', 'success')
    return redirect(url_for('mantenimiento'))


@app.route('/votaciones/mantenimiento/min-terminales', methods=['POST'])
@admin_required
def actualizar_min_terminales():
    if not _voting_is_closed():
        flash('Solo puedes cambiar el minimo de terminales con la votacion cerrada.', 'error')
        return redirect(url_for('mantenimiento'))
    raw = (request.form.get('min_active_terminals') or '').strip()
    try:
        value = int(raw)
    except ValueError:
        flash('El minimo de terminales debe ser un numero entero.', 'error')
        return redirect(url_for('mantenimiento'))
    if value < 1:
        flash('El minimo de terminales debe ser mayor o igual a 1.', 'error')
        return redirect(url_for('mantenimiento'))
    db.set_min_active_terminals(value)
    db.registrar_evento_critico(
        _actor_name(),
        'config_min_terminales',
        f'min_active_terminals={value}',
        _client_ip()
    )
    flash(f'Minimo de terminales activas actualizado a {value}.', 'success')
    return redirect(url_for('mantenimiento'))


@app.route('/votaciones/mantenimiento/abrir-votacion', methods=['POST'])
@admin_required
def abrir_votacion():
    if not _voting_is_closed():
        flash('La votación ya está abierta.', 'warning')
        return redirect(url_for('mantenimiento'))

    readiness = db.get_opening_readiness()
    metrics = readiness["metrics"]
    if not readiness["ready"]:
        flash(
            'No se puede abrir: verifica candidatos activos, padrón y terminales activas.',
            'error'
        )
        db.registrar_evento_critico(
            _actor_name(),
            'abrir_votacion_bloqueada',
            (
                f"checks={readiness['checks']}; "
                f"candidatos={metrics['active_candidates']}, "
                f"voto_blanco={metrics['has_blank_candidate']}, "
                f"estudiantes={metrics['students_total']}, "
                f"terminales_activas={metrics['active_terminals']}, "
                f"min_terminales={metrics['min_active_terminals']}"
            ),
            _client_ip()
        )
        return redirect(url_for('mantenimiento'))

    db.set_voting_closed(False)
    db.registrar_evento_critico(
        _actor_name(),
        'abrir_votacion',
        (
            f"Se abrió la votación; "
            f"candidatos={metrics['active_candidates']}, "
            f"voto_blanco={metrics['has_blank_candidate']}, "
            f"estudiantes={metrics['students_total']}, "
            f"terminales_activas={metrics['active_terminals']}, "
            f"min_terminales={metrics['min_active_terminals']}"
        ),
        _client_ip()
    )
    flash('Votacion reabierta. Los resultados vuelven a ocultarse.', 'success')
    return redirect(url_for('mantenimiento'))


@app.route('/votaciones/mantenimiento-sitio')
@admin_required
def mantenimiento_sitio():
    return render_template('mantenimiento_sitio.html')


@app.route('/votaciones/terminales')
@admin_required
def terminales_admin():
    terminales = db.listar_terminales()
    voting_status = db.get_voting_status()
    return render_template(
        'terminales_admin.html',
        terminales=terminales,
        voting_closed=voting_status.get("voting_closed", True),
        min_active_terminals=voting_status.get("min_active_terminals", 10)
    )


@app.route('/votaciones/terminal/login', methods=['GET', 'POST'])
def terminal_login():
    if request.method == 'POST':
        codigo = (request.form.get('codigo') or '').strip()
        token = (request.form.get('token') or '').strip()
        terminal = db.obtener_terminal_por_codigo(codigo)
        if not terminal or not terminal.get('activa') or terminal.get('token') != token:
            flash('Credenciales de terminal invalidas.', 'error')
            return redirect(url_for('terminal_login'))
        session['terminal_id'] = terminal['id']
        session['terminal_code'] = terminal['codigo']
        db.marcar_terminal_en_linea(terminal['id'])
        flash(f"Terminal autorizada: {terminal['nombre']}", 'success')
        next_url = request.args.get('next') or url_for('votar')
        return redirect(next_url)
    prefill = session.pop('terminal_prefill', None)
    return render_template('terminal_login.html', prefill=prefill or {})


@app.route('/votaciones/terminal/autoregistro', methods=['GET', 'POST'])
def terminal_autoregistro():
    if request.method == 'POST':
        admin_user = (request.form.get('admin_user') or '').strip()
        admin_pass = request.form.get('admin_pass') or ''
        codigo = (request.form.get('codigo') or '').strip()
        nombre = (request.form.get('nombre') or '').strip()
        ubicacion = (request.form.get('ubicacion') or '').strip()

        auth_user = db.authenticate_system_user(admin_user, admin_pass, role='terminal_admin')
        if not auth_user:
            flash('Credenciales de autorizacion invalidas.', 'error')
            return redirect(url_for('terminal_autoregistro'))
        if not codigo:
            flash('Debe ingresar el codigo de la terminal.', 'error')
            return redirect(url_for('terminal_autoregistro'))

        result = db.autoregistrar_terminal(codigo, nombre, ubicacion)
        terminal = db.obtener_terminal_por_codigo(codigo)
        session['terminal_id'] = terminal['id']
        session['terminal_code'] = terminal['codigo']
        db.marcar_terminal_en_linea(terminal['id'])
        db.registrar_evento_critico(
            f"{auth_user['username']} (terminal_admin)",
            'autoregistro_terminal',
            f"codigo={codigo}, action={result['action']}",
            _client_ip()
        )
        flash('Terminal autoregistrada y autorizada correctamente.', 'success')
        return redirect(url_for('votar'))
    return render_template('terminal_autoregistro.html')


@app.route('/votaciones/terminal/logout', methods=['POST'])
def terminal_logout():
    session.pop('terminal_id', None)
    session.pop('terminal_code', None)
    flash('Terminal desvinculada.', 'success')
    return redirect(url_for('terminal_login'))


@app.route('/votaciones/terminal/ping', methods=['POST'])
@require_terminal_auth
def terminal_ping():
    return jsonify({"ok": True, "terminal": session.get("terminal_code")})


@app.route('/votaciones/mantenimiento/terminales/crear', methods=['POST'])
@admin_required
def crear_terminal():
    if not _require_voting_closed_for_change('crear_terminal'):
        return redirect(url_for('terminales_admin'))
    codigo = (request.form.get('codigo') or '').strip()
    nombre = (request.form.get('nombre') or '').strip()
    ubicacion = (request.form.get('ubicacion') or '').strip()
    if not codigo or not nombre:
        flash('Codigo y nombre son obligatorios.', 'error')
        return redirect(url_for('terminales_admin'))
    try:
        token = db.crear_terminal(codigo, nombre, ubicacion)
    except Exception as e:
        flash(f'No se pudo crear terminal: {e}', 'error')
        return redirect(url_for('terminales_admin'))
    db.registrar_evento_critico(_actor_name(), 'crear_terminal', f'codigo={codigo}, nombre={nombre}, ubicacion={ubicacion}', _client_ip())
    flash(f'Terminal creada. Token: {token}', 'success')
    return redirect(url_for('terminales_admin'))


@app.route('/votaciones/mantenimiento/terminales/actualizar/<int:terminal_id>', methods=['POST'])
@admin_required
def actualizar_terminal(terminal_id):
    if not _require_voting_closed_for_change('actualizar_terminal'):
        return redirect(url_for('terminales_admin'))
    nombre = (request.form.get('nombre') or '').strip()
    ubicacion = (request.form.get('ubicacion') or '').strip()
    activa = request.form.get('activa') == '1'
    if not nombre:
        flash('El nombre es obligatorio.', 'error')
        return redirect(url_for('terminales_admin'))
    db.actualizar_terminal(terminal_id, nombre, ubicacion, activa)
    db.registrar_evento_critico(_actor_name(), 'actualizar_terminal', f'id={terminal_id}, activa={activa}, nombre={nombre}', _client_ip())
    flash('Terminal actualizada.', 'success')
    return redirect(url_for('terminales_admin'))


@app.route('/votaciones/mantenimiento/terminales/rotar-token/<int:terminal_id>', methods=['POST'])
@admin_required
def rotar_token_terminal(terminal_id):
    if not _require_voting_closed_for_change('rotar_token_terminal'):
        return redirect(url_for('terminales_admin'))
    token = db.rotar_token_terminal(terminal_id)
    db.registrar_evento_critico(_actor_name(), 'rotar_token_terminal', f'id={terminal_id}', _client_ip())
    flash(f'Nuevo token generado: {token}', 'success')
    return redirect(url_for('terminales_admin'))


@app.route('/votaciones/mantenimiento/terminales/eliminar/<int:terminal_id>', methods=['POST'])
@admin_required
def eliminar_terminal(terminal_id):
    if not _require_voting_closed_for_change('eliminar_terminal'):
        return redirect(url_for('terminales_admin'))
    db.eliminar_terminal(terminal_id)
    db.registrar_evento_critico(_actor_name(), 'eliminar_terminal', f'id={terminal_id}', _client_ip())
    flash('Terminal eliminada.', 'success')
    return redirect(url_for('terminales_admin'))


@app.route('/votaciones/mantenimiento/terminales/eliminar-todas', methods=['POST'])
@admin_required
def eliminar_todas_terminales():
    if not _require_voting_closed_for_change('eliminar_todas_terminales'):
        return redirect(url_for('terminales_admin'))
    db.eliminar_todas_terminales()
    db.registrar_evento_critico(_actor_name(), 'eliminar_todas_terminales', 'Limpieza masiva de terminales', _client_ip())
    flash('Todas las terminales fueron eliminadas.', 'success')
    return redirect(url_for('terminales_admin'))


@app.route('/votaciones/mantenimiento/reset-padron', methods=['POST'])
@admin_required
def reset_padron():
    if not _require_voting_closed_for_change('reset_padron'):
        return redirect(url_for('mantenimiento_sitio'))
    confirmation = (request.form.get('confirmation') or '').strip().upper()
    if confirmation != 'LIMPIAR':
        flash('Confirmacion invalida. Escribe LIMPIAR para continuar.', 'error')
        return redirect(url_for('mantenimiento_sitio'))

    db.reset_padron_anual()
    db.set_voting_closed(False)
    db.registrar_evento_critico(
        _actor_name(),
        'reset_padron',
        'Limpieza anual de padron (estudiantes) y votos',
        _client_ip()
    )
    flash('Padron y votos limpiados correctamente.', 'success')
    return redirect(url_for('mantenimiento_sitio'))


@app.route('/votaciones/terminal-admin/login', methods=['GET', 'POST'])
def terminal_admin_login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        user = db.authenticate_system_user(username, password, role='terminal_admin')
        if user:
            session['terminal_admin_auth'] = True
            session['terminal_admin_user'] = user['username']
            db.registrar_evento_critico(f"{user['username']} (terminal_admin)", 'login_terminal_admin', 'Inicio de sesión de terminal admin', _client_ip())
            return redirect(url_for('terminal_admin_panel'))
        flash('Credenciales invalidas', 'error')
    return render_template('terminal_admin_login.html')


@app.route('/votaciones/terminal-admin/logout', methods=['POST'])
@terminal_admin_required
def terminal_admin_logout():
    actor = f"{session.get('terminal_admin_user', 'unknown')} (terminal_admin)"
    session.pop('terminal_admin_auth', None)
    session.pop('terminal_admin_user', None)
    db.registrar_evento_critico(actor, 'logout_terminal_admin', 'Cierre de sesión de terminal admin', _client_ip())
    flash('Sesión cerrada.', 'success')
    return redirect(url_for('terminal_admin_login'))


@app.route('/votaciones/terminal-admin')
@terminal_admin_required
def terminal_admin_panel():
    terminales = db.listar_terminales()
    bitacora = db.obtener_bitacora_critica(200)
    return render_template('terminal_admin.html', terminales=terminales, bitacora=bitacora)


@app.route('/votaciones/terminal-admin/terminales/crear', methods=['POST'])
@terminal_admin_required
def terminal_admin_crear_terminal():
    codigo = (request.form.get('codigo') or '').strip()
    nombre = (request.form.get('nombre') or '').strip()
    ubicacion = (request.form.get('ubicacion') or '').strip()
    if not codigo or not nombre:
        flash('Codigo y nombre son obligatorios.', 'error')
        return redirect(url_for('terminal_admin_panel'))
    try:
        token = db.crear_terminal(codigo, nombre, ubicacion)
    except Exception as e:
        flash(f'No se pudo crear terminal: {e}', 'error')
        return redirect(url_for('terminal_admin_panel'))
    db.registrar_evento_critico(_actor_name(), 'crear_terminal', f'codigo={codigo}, nombre={nombre}, ubicacion={ubicacion}', _client_ip())
    flash(f'Terminal creada. Token: {token}', 'success')
    return redirect(url_for('terminal_admin_panel'))


@app.route('/votaciones/terminal-admin/terminales/actualizar/<int:terminal_id>', methods=['POST'])
@terminal_admin_required
def terminal_admin_actualizar_terminal(terminal_id):
    nombre = (request.form.get('nombre') or '').strip()
    ubicacion = (request.form.get('ubicacion') or '').strip()
    activa = request.form.get('activa') == '1'
    if not nombre:
        flash('El nombre es obligatorio.', 'error')
        return redirect(url_for('terminal_admin_panel'))
    db.actualizar_terminal(terminal_id, nombre, ubicacion, activa)
    db.registrar_evento_critico(_actor_name(), 'actualizar_terminal', f'id={terminal_id}, activa={activa}, nombre={nombre}', _client_ip())
    flash('Terminal actualizada.', 'success')
    return redirect(url_for('terminal_admin_panel'))


@app.route('/votaciones/terminal-admin/terminales/rotar-token/<int:terminal_id>', methods=['POST'])
@terminal_admin_required
def terminal_admin_rotar_token_terminal(terminal_id):
    token = db.rotar_token_terminal(terminal_id)
    db.registrar_evento_critico(_actor_name(), 'rotar_token_terminal', f'id={terminal_id}', _client_ip())
    flash(f'Nuevo token generado: {token}', 'success')
    return redirect(url_for('terminal_admin_panel'))


@app.route('/votaciones/terminal-admin/terminales/eliminar/<int:terminal_id>', methods=['POST'])
@terminal_admin_required
def terminal_admin_eliminar_terminal(terminal_id):
    db.eliminar_terminal(terminal_id)
    db.registrar_evento_critico(_actor_name(), 'eliminar_terminal', f'id={terminal_id}', _client_ip())
    flash('Terminal eliminada.', 'success')
    return redirect(url_for('terminal_admin_panel'))


@app.route('/votaciones/abstencionistas')
@admin_required
def abstencionistas():
    data = db.obtener_abstencionistas()
    return render_template('abstencionistas.html', abstencionistas=data, total=len(data))


@app.route('/votaciones/abstencionistas/exportar')
@admin_required
def exportar_abstencionistas():
    data = db.obtener_abstencionistas()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nombre', 'Apellido1', 'Apellido2', 'Cedula', 'Nivel'])
    for r in data:
        writer.writerow([r['id'], r['nombre'], r['apellido1'], r['apellido2'], r['cedula'], r['nivel']])

    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8-sig'))
    mem.seek(0)
    filename = f"abstencionistas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return send_file(mem, as_attachment=True, download_name=filename, mimetype='text/csv')


@app.route('/votaciones/usuarios', methods=['GET', 'POST'])
@admin_required
def usuarios():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        role = (request.form.get('role') or 'admin').strip()
        active = request.form.get('active') == '1'
        if not username or not password:
            flash('Usuario y contrasena son obligatorios.', 'error')
            return redirect(url_for('usuarios'))
        try:
            db.create_system_user(username, password, role, active=active)
            db.registrar_evento_critico(_actor_name(), 'crear_usuario', f'username={username}, role={role}, active={active}', _client_ip())
            flash('Usuario creado.', 'success')
        except Exception as e:
            flash(f'No se pudo crear usuario: {e}', 'error')
        return redirect(url_for('usuarios'))
    users = db.list_system_users()
    return render_template('usuarios.html', users=users)


@app.route('/votaciones/usuarios/actualizar/<int:user_id>', methods=['POST'])
@admin_required
def actualizar_usuario(user_id):
    role = (request.form.get('role') or 'admin').strip()
    active = request.form.get('active') == '1'
    db.update_system_user(user_id, role, active)
    db.registrar_evento_critico(_actor_name(), 'actualizar_usuario', f'user_id={user_id}, role={role}, active={active}', _client_ip())
    flash('Usuario actualizado.', 'success')
    return redirect(url_for('usuarios'))


@app.route('/votaciones/usuarios/password/<int:user_id>', methods=['POST'])
@admin_required
def cambiar_password_usuario(user_id):
    new_password = request.form.get('new_password') or ''
    if len(new_password) < 8:
        flash('La contrasena debe tener al menos 8 caracteres.', 'error')
        return redirect(url_for('usuarios'))
    db.set_system_user_password(user_id, new_password)
    db.registrar_evento_critico(_actor_name(), 'cambiar_password_usuario', f'user_id={user_id}', _client_ip())
    flash('Contrasena actualizada.', 'success')
    return redirect(url_for('usuarios'))


@app.route('/votaciones/bitacora')
@admin_required
def bitacora_sistema():
    actor = (request.args.get('actor') or '').strip()
    accion = (request.args.get('accion') or '').strip()
    ip_origen = (request.args.get('ip') or '').strip()
    texto = (request.args.get('q') or '').strip()
    fecha_desde = (request.args.get('desde') or '').strip()
    fecha_hasta = (request.args.get('hasta') or '').strip()
    try:
        limit = int(request.args.get('limit', 500))
    except ValueError:
        limit = 500
    limit = max(50, min(limit, 2000))

    eventos = db.obtener_bitacora_filtrada(
        actor=actor or None,
        accion=accion or None,
        ip_origen=ip_origen or None,
        texto=texto or None,
        fecha_desde=fecha_desde or None,
        fecha_hasta=fecha_hasta or None,
        limit=limit
    )
    acciones = db.obtener_acciones_bitacora()
    return render_template(
        'bitacora.html',
        eventos=eventos,
        acciones=acciones,
        filtros={
            'actor': actor,
            'accion': accion,
            'ip': ip_origen,
            'q': texto,
            'desde': fecha_desde,
            'hasta': fecha_hasta,
            'limit': limit,
        }
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


