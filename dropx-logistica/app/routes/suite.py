from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from datetime import datetime, timedelta
import math
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
            session.permanent = request.form.get('remember') == '1'
            flash(f"Bienvenido a la Suite, {credenciales[email]['nombre']}", "success")
            return redirect(url_for('suite.dashboard'))
        else:
            flash("Credenciales incorrectas. Verifica tu correo y contraseña.", "danger")

    return render_template('suite/login.html')

@suite_bp.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    if request.method == 'POST':
        flash("La recuperación por correo todavía no está configurada.", "warning")
    return render_template('suite/recuperar.html')

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
        numero_guia = request.form.get('numero_guia', '').strip().upper()
        remitente = request.form.get('remitente', '').strip()
        destinatario = request.form.get('destinatario', '').strip()
        ciudad = request.form.get('ciudad', '').strip()
        direccion = request.form.get('direccion', '').strip()
        try:
            peso = float(request.form.get('peso', '1'))
        except ValueError:
            flash("Ingresa un peso válido para el paquete.", "danger")
            return redirect(url_for('suite.paquetes'))

        if not all([numero_guia, remitente, destinatario, ciudad, direccion]) or not math.isfinite(peso) or peso <= 0:
            flash("Completa todos los campos e ingresa un peso mayor que cero.", "danger")
            return redirect(url_for('suite.paquetes'))
        if Paquete.query.filter_by(numero_guia=numero_guia).first():
            flash(f"La guía {numero_guia} ya está registrada.", "danger")
            return redirect(url_for('suite.paquetes'))

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

    estado = request.args.get('estado', '').strip()
    guia = request.args.get('guia', '').strip()
    rango = request.args.get('rango', 'todo')
    if guia:
        rango = 'todo'
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 8

    consulta = Paquete.query
    if guia:
        consulta = consulta.filter(Paquete.numero_guia.ilike(f'%{guia}%'))
    estados = {
        'bodega': ['Recibido'],
        'ruta': ['En tránsito', 'En transito', 'En ruta de entrega'],
        'entregado': ['Entregado'],
        'pendiente': ['Pendiente'],
    }
    if estado in estados:
        consulta = consulta.filter(Paquete.estado.in_(estados[estado]))

    ahora = datetime.utcnow()
    if rango in ('7', '30'):
        consulta = consulta.filter(Paquete.fecha_creacion >= ahora - timedelta(days=int(rango)))
    elif rango == 'mes':
        consulta = consulta.filter(
            Paquete.fecha_creacion >= ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        )
    elif rango != 'todo':
        rango = '30'
        consulta = consulta.filter(Paquete.fecha_creacion >= ahora - timedelta(days=30))

    total_filtrado = consulta.count()
    total_paginas = max(1, (total_filtrado + por_pagina - 1) // por_pagina)
    pagina = min(max(pagina, 1), total_paginas)
    lista_paquetes = (
        consulta.order_by(Paquete.fecha_creacion.desc())
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )

    metricas = {
        'total': Paquete.query.count(),
        'bodega': Paquete.query.filter_by(estado='Recibido').count(),
        'ruta': Paquete.query.filter(
            Paquete.estado.in_(['En tránsito', 'En transito', 'En ruta de entrega'])
        ).count(),
        'entregados': Paquete.query.filter_by(estado='Entregado').count(),
    }
    usuario_actual = session.get('user', {})
    return render_template(
        'suite/paquetes.html',
        paquetes=lista_paquetes,
        usuario=usuario_actual,
        metricas=metricas,
        guia=guia,
        estado=estado,
        rango=rango,
        pagina=pagina,
        total_paginas=total_paginas,
        total_filtrado=total_filtrado,
        por_pagina=por_pagina,
    )

@suite_bp.route('/paquetes/<int:paquete_id>/editar', methods=['POST'])
@login_required
def editar_paquete(paquete_id):
    paquete = Paquete.query.get_or_404(paquete_id)
    remitente = request.form.get('remitente', '').strip()
    destinatario = request.form.get('destinatario', '').strip()
    ciudad = request.form.get('ciudad', '').strip()
    direccion = request.form.get('direccion', '').strip()
    estado = request.form.get('estado', '').strip()
    try:
        peso = float(request.form.get('peso', ''))
    except ValueError:
        flash("Ingresa un peso válido para el paquete.", "danger")
        return redirect(url_for('suite.paquetes'))

    estados_validos = {'Recibido', 'En tránsito', 'En ruta de entrega', 'Entregado', 'Pendiente'}
    if not all([remitente, destinatario, ciudad, direccion]) or not math.isfinite(peso) or peso <= 0 or estado not in estados_validos:
        flash("Revisa los datos del paquete e intenta nuevamente.", "danger")
        return redirect(url_for('suite.paquetes'))

    paquete.remitente = remitente
    paquete.destinatario = destinatario
    paquete.ciudad_destino = ciudad
    paquete.direccion_entrega = direccion
    paquete.estado = estado
    paquete.peso = peso
    db.session.commit()
    flash(f"Paquete {paquete.numero_guia} actualizado.", "success")
    return redirect(url_for('suite.paquetes'))

@suite_bp.route('/paquetes/<int:paquete_id>/eliminar', methods=['POST'])
@login_required
def eliminar_paquete(paquete_id):
    paquete = Paquete.query.get_or_404(paquete_id)
    numero_guia = paquete.numero_guia
    db.session.delete(paquete)
    db.session.commit()
    flash(f"Paquete {numero_guia} eliminado.", "success")
    return redirect(url_for('suite.paquetes'))

@suite_bp.route('/repartidores', methods=['GET', 'POST'])
@login_required
def repartidores():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        zona = request.form.get('zona', '').strip()
        telefono = request.form.get('telefono', '').strip()
        estado = request.form.get('estado', 'Activo').strip()
        try:
            calificacion = float(request.form.get('calificacion', '5'))
            entregas_mes = int(request.form.get('entregas_mes', '0'))
        except ValueError:
            flash("Ingresa una calificación y un número de entregas válidos.", "danger")
            return redirect(url_for('suite.repartidores'))

        estados_validos = {'Activo', 'En ruta', 'Desconectado'}
        if (
            not all([nombre, zona, telefono])
            or not math.isfinite(calificacion)
            or not 0 <= calificacion <= 5
            or entregas_mes < 0
            or estado not in estados_validos
        ):
            flash("Revisa los datos del repartidor e intenta nuevamente.", "danger")
            return redirect(url_for('suite.repartidores'))

        nuevo_repartidor = Repartidor(
            nombre=nombre,
            zona=zona,
            telefono=telefono,
            estado=estado,
            calificacion=calificacion,
            entregas_mes=entregas_mes,
        )
        db.session.add(nuevo_repartidor)
        db.session.commit()
        flash(f"Repartidor {nombre} agregado correctamente.", "success")
        return redirect(url_for('suite.repartidores'))

    lista_repartidores = Repartidor.query.order_by(Repartidor.nombre.asc()).all()
    ranking_repartidores = Repartidor.query.order_by(
        Repartidor.entregas_mes.desc(),
        Repartidor.nombre.asc()
    ).limit(5).all()
    max_entregas = max((repartidor.entregas_mes or 0 for repartidor in ranking_repartidores), default=0)
    metricas = {
        'total': Repartidor.query.count(),
        'activos': Repartidor.query.filter(Repartidor.estado.in_(['Activo', 'En ruta'])).count(),
        'en_ruta': Repartidor.query.filter_by(estado='En ruta').count(),
        'disponibles': Repartidor.query.filter_by(estado='Activo').count(),
    }
    usuario_actual = session.get('user', {})
    return render_template(
        'suite/repartidores.html',
        repartidores=lista_repartidores,
        ranking_repartidores=ranking_repartidores,
        max_entregas=max_entregas,
        metricas=metricas,
        usuario=usuario_actual,
    )

@suite_bp.route('/repartidores/<int:repartidor_id>/eliminar', methods=['POST'])
@login_required
def eliminar_repartidor(repartidor_id):
    repartidor = Repartidor.query.get_or_404(repartidor_id)
    nombre = repartidor.nombre
    db.session.delete(repartidor)
    db.session.commit()
    flash(f"Repartidor {nombre} eliminado correctamente.", "success")
    return redirect(url_for('suite.repartidores'))

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
