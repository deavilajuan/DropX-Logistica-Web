import re
from urllib.parse import quote

from flask import Blueprint, current_app, flash, redirect, render_template, request

from app.models import Package

# Sitio público (no necesita sesión)
bp = Blueprint('public', __name__)

PLANS = {
    'basico': 'Básico',
    'profesional': 'Profesional',
    'empresarial': 'Empresarial',
}

SUBJECTS = {
    'cotizacion': 'Cotización de servicio corporativo',
    'soporte': 'Soporte y atención al cliente',
    'aliados': 'Información para aliados y conductores',
    'integraciones': 'Integración API / E-commerce',
    'otro': 'Otras consultas generales',
}


@bp.route('/')
def index():
    return render_template('public/index.html')


@bp.route('/rastreo')
def rastreo():
    # Número de guía desde la URL (?guia=...)
    tracking = request.args.get('guia', '').strip().upper()
    package = None
    if tracking:
        package = Package.query.filter_by(tracking_number=tracking).first()
        if not package:
            flash(f"No encontramos la guía '{tracking}'. Verifica el número.", 'danger')
    return render_template('public/rastreo.html', package=package, tracking=tracking)


@bp.route('/servicios')
def servicios():
    return render_template('public/servicios.html')


@bp.route('/ser-aliado')
def ser_aliado():
    return render_template('public/ser_aliado.html')


@bp.route('/nosotros')
def nosotros():
    return render_template('public/nosotros.html')


@bp.route('/privacidad')
def privacidad():
    return render_template('public/privacidad.html')


@bp.route('/terminos')
def terminos():
    return render_template('public/terminos.html')


@bp.route('/contacto', methods=['GET', 'POST'])
def contacto():
    # Número del asesor: solo dígitos, entre 8 y 15
    number = re.sub(r'\D', '', current_app.config['WHATSAPP_ADVISOR_NUMBER'])
    if not 8 <= len(number) <= 15:
        number = ''

    plan_key = (request.values.get('plan') or '').strip().lower()
    form = {}

    if request.method == 'POST':
        fields = ('nombre', 'email', 'telefono', 'asunto', 'mensaje')
        form = {field: (request.form.get(field) or '').strip() for field in fields}

        if not all(form.values()) or form['asunto'] not in SUBJECTS:
            flash('Completa todos los campos para continuar.', 'danger')
        elif not number:
            flash('El contacto por WhatsApp aún no está configurado. Inténtalo más tarde.', 'danger')
        else:
            lines = [
                'Hola DropX, quisiera hablar con un asesor.',
                f"Nombre: {form['nombre']}",
                f"Correo: {form['email']}",
                f"Teléfono: {form['telefono']}",
                f"Asunto: {SUBJECTS[form['asunto']]}",
            ]
            if plan_key in PLANS:
                lines.append(f'Plan de interés: {PLANS[plan_key]}')
            lines.append(f"Mensaje: {form['mensaje']}")
            url = f"https://wa.me/{number}?text={quote(chr(10).join(lines))}"
            return redirect(url, code=303)

    plan = PLANS.get(plan_key)
    initial_message = (
        f'Me interesa recibir información sobre el plan {plan} y quisiera hablar con un asesor.'
        if plan else ''
    )
    whatsapp_text = (
        f'Hola DropX, quisiera hablar con un asesor comercial sobre el plan {plan}.'
        if plan else 'Hola DropX, quisiera hablar con un asesor.'
    )
    whatsapp_url = f'https://wa.me/{number}?text={quote(whatsapp_text)}' if number else None

    return render_template(
        'public/contacto.html',
        plan_key=plan_key if plan else '',
        plan=plan,
        initial_message=initial_message,
        whatsapp_url=whatsapp_url,
        form=form,
    )
