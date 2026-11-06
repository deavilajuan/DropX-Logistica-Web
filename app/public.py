import re
from urllib.parse import quote

from flask import Blueprint, current_app, flash, redirect, render_template, request

from app.models import Package

# Sitio público (no necesita sesión)
bp = Blueprint('public', __name__)

# Asuntos del formulario de contacto
SUBJECTS = {
    'quote': 'Cotización de servicio corporativo',
    'support': 'Soporte y atención al cliente',
    'allies': 'Información para aliados y conductores',
    'integrations': 'Integración API / E-commerce',
    'other': 'Otras consultas generales',
}

# Vehículos aceptados para ser aliado
VEHICLES = ('Moto', 'Carro', 'Van', 'Camioneta')


def whatsapp_url(lines):
    """Arma el enlace de WhatsApp con el mensaje. Devuelve None si no hay número configurado."""
    # Solo dígitos, entre 8 y 15 (formato internacional sin "+")
    number = re.sub(r'\D', '', current_app.config['WHATSAPP_ADVISOR_NUMBER'])
    if not 8 <= len(number) <= 15:
        return None
    return f"https://wa.me/{number}?text={quote(chr(10).join(lines))}"


def read_fields(names):
    """Lee los campos del formulario y les quita los espacios sobrantes."""
    return {name: (request.form.get(name) or '').strip() for name in names}


# ---------- Páginas ----------
@bp.route('/', methods=['GET', 'POST'])
def index():
    """Landing: todas las secciones están en esta página. El formulario de contacto
    (sección #contacto) llega por POST y redirige a WhatsApp con el mensaje armado."""
    form = {}
    if request.method == 'POST':
        form = read_fields(('name', 'email', 'phone', 'subject', 'message'))
        if not all(form.values()) or form['subject'] not in SUBJECTS:
            flash('Complete todos los campos para continuar.', 'danger')
        else:
            url = whatsapp_url([
                'Hola DropX, quisiera hablar con un asesor.',
                f"Nombre: {form['name']}",
                f"Correo: {form['email']}",
                f"Teléfono: {form['phone']}",
                f"Asunto: {SUBJECTS[form['subject']]}",
                f"Mensaje: {form['message']}",
            ])
            if url:
                return redirect(url, code=303)
            flash('El contacto por WhatsApp aún no está configurado. Inténtelo más tarde.', 'danger')

    # Enlace directo al chat (botón "Escribir por WhatsApp")
    chat_url = whatsapp_url(['Hola DropX, quisiera hablar con un asesor.'])
    return render_template('public/index.html', form=form, subjects=SUBJECTS, chat_url=chat_url)


@bp.route('/rastreo')
def rastreo():
    # El número de guía llega por la URL (?guia=DX-000001)
    tracking = request.args.get('guia', '').strip().upper()
    package = None
    if tracking:
        # Si no existe, la plantilla muestra el aviso de "guía no encontrada"
        package = Package.query.filter_by(tracking_number=tracking).first()
    return render_template('public/rastreo.html', package=package, tracking=tracking)


@bp.route('/privacidad')
def privacidad():
    return render_template('public/privacidad.html')


@bp.route('/terminos')
def terminos():
    return render_template('public/terminos.html')


@bp.route('/ser-aliado', methods=['GET', 'POST'])
def ser_aliado():
    form = {}
    if request.method == 'POST':
        form = read_fields(('first_name', 'last_name', 'email', 'phone', 'vehicle'))
        if not all(form.values()) or form['vehicle'] not in VEHICLES:
            flash('Complete todos los campos para continuar.', 'danger')
        else:
            url = whatsapp_url([
                'Hola DropX, quiero ser aliado en Cartagena.',
                f"Nombre: {form['first_name']} {form['last_name']}",
                f"Correo: {form['email']}",
                f"Celular: {form['phone']}",
                f"Vehículo: {form['vehicle']}",
            ])
            if url:
                return redirect(url, code=303)
            flash('El contacto por WhatsApp aún no está configurado. Inténtelo más tarde.', 'danger')
    return render_template('public/ser_aliado.html', form=form, vehicles=VEHICLES)
