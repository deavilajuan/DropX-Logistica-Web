from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from app.database import db
from app.models import Paquete, Repartidor

suite_bp = Blueprint('suite', __name__)

# Decorador que protege las pantallas del dashboard
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Debes iniciar sesión para acceder a la Suite Logística.", "danger")
            return redirect(url_for('suite.login'))
        return f(*args, **kwargs)
    return decorated_function
#Funciones de decoracion para el admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario = session.get('user', {})
        if usuario.get('rol') != 'Superadmin':
            flash("Acceso denegado: Esta sección es exclusiva para el Superadmin.", "danger")
            return redirect(url_for('suite.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# RUTA DE LOGIN
@suite_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('suite.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        # Cuentas autorizadas
        credenciales = {
            'admin@dropx.com': {'pass': 'admin123', 'rol': 'Superadmin', 'nombre': 'Carlos Mendoza'},
            'logistica@dropx.com': {'pass': 'logistica123', 'rol': 'Logístico', 'nombre': 'Diana Gómez'}
        }

        if email in credenciales and credenciales[email]['pass'] == password:
            session['user'] = {
                'email': email,
                'rol': credenciales[email]['rol'],
                'nombre': credenciales[email]['nombre']
            }
            flash(f"Bienvenido a la Suite, {credenciales[email]['nombre']}", "success")
            return redirect(url_for('suite.dashboard'))
        else:
            flash("Credenciales incorrectas. Verifica tu correo y contraseña.", "danger")

    return render_template('suite/login.html')

# RUTA DE LOGOUT (Cerrar sesión)
@suite_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for('suite.login'))

# PANTALLAS DEL DASHBOARD PROTEGIDAS
@suite_bp.route('/')
@suite_bp.route('/dashboard')
@login_required
def dashboard():
    usuario_actual = session.get('user', {})

    # 1. Conteo de paquetes por estado
    total_recibidos = Paquete.query.filter_by(estado='Recibido').count()
    total_entregados = Paquete.query.filter_by(estado='Entregado').count()
    total_transito = Paquete.query.filter(Paquete.estado.in_(['En tránsito', 'En transito', 'En ruta de entrega'])).count()
    total_pendientes = Paquete.query.filter_by(estado='Pendiente').count()

    # 2. Conteo por rangos de peso
    peso_0_5 = Paquete.query.filter(Paquete.peso <= 5).count()
    peso_5_8 = Paquete.query.filter(Paquete.peso > 5, Paquete.peso <= 8).count()
    peso_8_10 = Paquete.query.filter(Paquete.peso > 8, Paquete.peso <= 10).count()
    peso_10_mas = Paquete.query.filter(Paquete.peso > 10).count()

    # 3. Datos de Repartidores para la Dona (Top 3 + Otros)
    repartidores_top = Repartidor.query.order_by(Repartidor.entregas_mes.desc()).limit(3).all()
    nombres_repartidores = [r.nombre.split()[0] + ' ' + r.nombre.split()[1] if len(r.nombre.split()) > 1 else r.nombre for r in repartidores_top]
    entregas_repartidores = [r.entregas_mes for r in repartidores_top]

    # Si faltan repartidores o está vacía, aseguramos al menos valores para que la dona pinte
    if not entregas_repartidores or sum(entregas_repartidores) == 0:
        nombres_repartidores = ['José Carlos', 'Alberto Luis', 'César Gaviria', 'Otros']
        entregas_repartidores = [52.1, 22.8, 13.9, 11.2]
    else:
        nombres_repartidores.append('Otros')
        entregas_repartidores.append(max(5, int(sum(entregas_repartidores) * 0.1)))

    metricas = {
        'recibidos': total_recibidos,
        'transito': total_transito,
        'entregados': total_entregados,
        'pendientes': total_pendientes,
        'pesos': [peso_0_5, peso_5_8, peso_8_10, peso_10_mas],
        'repartidores_labels': nombres_repartidores,
        'repartidores_data': entregas_repartidores
    }

    ultimos_paquetes = Paquete.query.order_by(Paquete.fecha_creacion.desc()).limit(5).all()

    return render_template('suite/dashboard.html', 
                        usuario=usuario_actual, 
                        metricas=metricas, 
                        paquetes_recientes=ultimos_paquetes)

@suite_bp.route('/paquetes', methods=['GET', 'POST'])
@login_required
def paquetes():
    if request.method == 'POST':
        numero_guia = request.form.get('numero_guia')
        remitente = request.form.get('remitente')
        destinatario = request.form.get('destinatario')
        ciudad = request.form.get('ciudad')
        peso = float(request.form.get('peso', 1.0))
        direccion = request.form.get('direccion', 'Centro de distribución')

        nuevo = Paquete(
            numero_guia=numero_guia,
            remitente=remitente,
            destinatario=destinatario,
            ciudad_destino=ciudad,
            peso=peso,
            direccion_entrega=direccion,
            estado='Recibido'
        )
        db.session.add(nuevo)
        db.session.commit()
        flash(f"Paquete {numero_guia} creado con éxito", "success")
        return redirect(url_for('suite.paquetes'))

    lista_paquetes = Paquete.query.all()
    usuario_actual = session.get('user', {})
    return render_template('suite/paquetes.html', paquetes=lista_paquetes, usuario=usuario_actual)

@suite_bp.route('/repartidores')
@login_required
def repartidores():
    lista_repartidores = Repartidor.query.all()
    usuario_actual = session.get('user', {})
    return render_template('suite/repartidores.html', repartidores=lista_repartidores, usuario=usuario_actual)

@suite_bp.route('/logisticos')
@login_required
def logisticos():
    usuario_actual = session.get('user', {})
    return render_template('suite/logisticos.html', usuario=usuario_actual)

@suite_bp.route('/reportes')
@login_required
@admin_required
def reportes():
    usuario_actual = session.get('user', {})
    return render_template('suite/reportes.html', usuario=usuario_actual)