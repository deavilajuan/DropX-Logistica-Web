from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func

from app import db
from app.models import STATUSES, Package, PackageEvent, User

# Panel web (Suite logística): todas las rutas empiezan con /suite
bp = Blueprint('suite', __name__, url_prefix='/suite')

# Roles que pueden entrar al panel (el courier solo usa la app)
WEB_ROLES = ('admin', 'manager')
MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']


# Solo para el administrador (como un middleware de Laravel)
def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Acceso denegado: esta sección es exclusiva del administrador.', 'danger')
            return redirect(url_for('suite.dashboard'))
        return view(*args, **kwargs)

    return login_required(wrapper)


def month_start(date):
    return date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


# ---------- Sesión ----------
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('suite.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Credenciales incorrectas. Verifica tu correo y contraseña.', 'danger')
        elif user.role not in WEB_ROLES:
            flash('Esta cuenta solo puede ingresar desde la app.', 'danger')
        else:
            login_user(user, remember=request.form.get('remember') == '1')
            flash(f'Bienvenido a la Suite, {user.name}', 'success')
            return redirect(url_for('suite.dashboard'))

    return render_template('suite/login.html')


@bp.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    # TO DO: Enviar el correo de recuperación de contraseña.
    if request.method == 'POST':
        flash('La recuperación por correo todavía no está configurada.', 'warning')
    return render_template('suite/recuperar.html')


@bp.route('/logout')
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('suite.login'))


# ---------- Dashboard ----------
@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    # Paquetes por estado
    counts = dict(db.session.query(Package.status, func.count()).group_by(Package.status))

    # Paquetes creados en los últimos 6 meses
    today = datetime.now()
    months, created = [], []
    for back in range(5, -1, -1):
        year, month = today.year, today.month - back
        if month < 1:
            year, month = year - 1, month + 12
        start = datetime(year, month, 1)
        end = datetime(year + month // 12, month % 12 + 1, 1)
        months.append(MONTHS[month - 1])
        created.append(Package.query.filter(Package.created_at >= start, Package.created_at < end).count())

    # Paquetes por rango de peso (kg)
    weight_ranges = [(0, 5), (5, 8), (8, 10), (10, 100000)]
    weights = [
        Package.query.filter(Package.weight > low, Package.weight <= high).count()
        for low, high in weight_ranges
    ]

    # Entregas del mes: los 3 mejores couriers y el resto juntos
    top = courier_deliveries()
    names = [name for name, _ in top[:3]]
    values = [total for _, total in top[:3]]
    if len(top) > 3:
        names.append('Otros')
        values.append(sum(total for _, total in top[3:]))

    chart_data = {
        'months': months,
        'created': created,
        'weights': weights,
        'couriers': names,
        'deliveries': values,
    }
    recent = Package.query.order_by(Package.id.desc()).limit(5).all()
    return render_template('suite/dashboard.html', counts=counts, chart_data=chart_data, recent=recent)


def courier_deliveries():
    """Entregas del mes de cada courier, de mayor a menor: [(nombre, total), ...]"""
    rows = (
        db.session.query(User.name, func.count(Package.id))
        .join(Package, Package.courier_id == User.id)
        .filter(Package.status == 'delivered', Package.delivered_at >= month_start(datetime.now()))
        .group_by(User.id, User.name)
        .order_by(func.count(Package.id).desc())
        .all()
    )
    return [(name, total) for name, total in rows]


# ---------- Paquetes ----------
def read_package_form():
    """Lee y valida el formulario de paquetes. Devuelve (datos, mensaje_de_error)."""
    data = {field: request.form.get(field, '').strip() for field in ('sender', 'recipient', 'city', 'address')}
    try:
        data['weight'] = float(request.form.get('weight', ''))
    except ValueError:
        data['weight'] = 0

    # El courier es opcional, pero si viene tiene que existir
    courier_id = request.form.get('courier_id', type=int)
    if courier_id and not User.query.filter_by(id=courier_id, role='courier').first():
        return data, 'El repartidor seleccionado no existe.'
    data['courier_id'] = courier_id

    if not all(data[f] for f in ('sender', 'recipient', 'city', 'address')) or not 0 < data['weight'] < 1000:
        return data, 'Completa todos los campos e ingresa un peso válido (mayor que cero).'
    return data, None


def add_event(package, title, description=None):
    package.events.append(PackageEvent(title=title, description=description))


@bp.route('/paquetes', methods=['GET', 'POST'])
@login_required
def paquetes():
    if request.method == 'POST':
        tracking = request.form.get('tracking_number', '').strip().upper()
        data, error = read_package_form()
        if not tracking.startswith('DX-') or len(tracking) <= 3:
            error = 'El número de guía debe tener el formato DX-123456.'
        elif Package.query.filter_by(tracking_number=tracking).first():
            error = f'La guía {tracking} ya está registrada.'

        if error:
            flash(error, 'danger')
        else:
            package = Package(tracking_number=tracking, **data)
            add_event(package, 'Guía generada', f'Registrada en la Suite por {current_user.name}.')
            db.session.add(package)
            db.session.commit()
            flash(f'Paquete {tracking} creado con éxito', 'success')
        return redirect(url_for('suite.paquetes'))

    # Filtros del listado
    tracking = request.args.get('guia', '').strip()
    status = request.args.get('estado', '')
    period = 'todo' if tracking else request.args.get('rango', '30')

    query = Package.query
    if tracking:
        query = query.filter(Package.tracking_number.ilike(f'%{tracking}%'))
    if status in STATUSES:
        query = query.filter_by(status=status)
    if period in ('7', '30'):
        query = query.filter(Package.created_at >= datetime.now() - timedelta(days=int(period)))
    elif period == 'mes':
        query = query.filter(Package.created_at >= month_start(datetime.now()))

    # Paginación (8 por página)
    page = request.args.get('pagina', 1, type=int)
    pagination = query.order_by(Package.id.desc()).paginate(page=page, per_page=8, error_out=False)

    counts = dict(db.session.query(Package.status, func.count()).group_by(Package.status))
    couriers = User.query.filter_by(role='courier').order_by(User.name).all()
    return render_template(
        'suite/paquetes.html',
        pagination=pagination,
        counts=counts,
        total=sum(counts.values()),
        couriers=couriers,
        tracking=tracking,
        status=status,
        period=period,
    )


@bp.route('/paquetes/<int:package_id>/editar', methods=['POST'])
@login_required
def editar_paquete(package_id):
    package = db.get_or_404(Package, package_id)
    data, error = read_package_form()
    new_status = request.form.get('status', '')
    if not error and new_status not in STATUSES:
        error = 'Selecciona un estado válido.'

    if error:
        flash(error, 'danger')
        return redirect(url_for('suite.paquetes'))

    for field, value in data.items():
        setattr(package, field, value)

    # Si cambia el estado, queda registrado en el historial
    if new_status != package.status:
        package.status = new_status
        package.delivered_at = datetime.now() if new_status == 'delivered' else None
        add_event(package, STATUSES[new_status], f'Actualizado por {current_user.name}.')
    db.session.commit()
    flash(f'Paquete {package.tracking_number} actualizado.', 'success')
    return redirect(url_for('suite.paquetes'))


@bp.route('/paquetes/<int:package_id>/eliminar', methods=['POST'])
@login_required
def eliminar_paquete(package_id):
    package = db.get_or_404(Package, package_id)
    tracking = package.tracking_number
    db.session.delete(package)
    db.session.commit()
    flash(f'Paquete {tracking} eliminado.', 'success')
    return redirect(url_for('suite.paquetes'))


# ---------- Repartidores (usuarios con rol courier) ----------
@bp.route('/repartidores', methods=['GET', 'POST'])
@login_required
def repartidores():
    if request.method == 'POST':
        form = {f: request.form.get(f, '').strip() for f in ('name', 'email', 'phone', 'zone')}
        form['email'] = form['email'].lower()
        password = request.form.get('password', '')

        if not all(form.values()) or len(password) < 8:
            flash('Completa todos los campos. La contraseña debe tener mínimo 8 caracteres.', 'danger')
        elif User.query.filter_by(email=form['email']).first():
            flash('Ya existe un usuario con ese correo.', 'danger')
        else:
            courier = User(role='courier', **form)
            courier.set_password(password)
            db.session.add(courier)
            db.session.commit()
            flash(f"Repartidor {form['name']} agregado correctamente.", 'success')
        return redirect(url_for('suite.repartidores'))

    couriers = User.query.filter_by(role='courier').order_by(User.name).all()
    deliveries = dict(
        db.session.query(User.id, func.count(Package.id))
        .join(Package, Package.courier_id == User.id)
        .filter(Package.status == 'delivered', Package.delivered_at >= month_start(datetime.now()))
        .group_by(User.id)
    )
    # Un courier está "en ruta" si tiene paquetes recogidos sin entregar
    on_route = {
        row[0] for row in db.session.query(Package.courier_id).filter_by(status='picked_up').distinct()
    }
    ranking = sorted(couriers, key=lambda c: deliveries.get(c.id, 0), reverse=True)[:5]
    return render_template(
        'suite/repartidores.html',
        couriers=couriers,
        deliveries=deliveries,
        on_route=on_route,
        ranking=ranking,
        max_deliveries=max(deliveries.values(), default=0),
        month_total=sum(deliveries.values()),
    )


@bp.route('/repartidores/<int:courier_id>/eliminar', methods=['POST'])
@login_required
def eliminar_repartidor(courier_id):
    courier = User.query.filter_by(id=courier_id, role='courier').first_or_404()
    # Sus paquetes quedan sin repartidor asignado
    name = courier.name
    Package.query.filter_by(courier_id=courier.id).update({'courier_id': None})
    db.session.delete(courier)
    db.session.commit()
    flash(f'Repartidor {name} eliminado correctamente.', 'success')
    return redirect(url_for('suite.repartidores'))


# ---------- Otras pantallas ----------
@bp.route('/logisticos')
@login_required
def logisticos():
    # TO DO: Mostrar datos reales en el mapa (hoy son centros de ejemplo).
    return render_template('suite/logisticos.html')


@bp.route('/reportes')
@admin_required
def reportes():
    # TO DO: Generar los reportes (hoy es solo la interfaz).
    return render_template('suite/reportes.html')
