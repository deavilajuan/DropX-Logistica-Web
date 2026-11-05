import re
from urllib.parse import quote

from flask import Blueprint, current_app, flash, redirect, render_template, request, session
from app.models import Paquete

public_bp = Blueprint('public', __name__)

PLANES = {
    'basico': 'Básico',
    'profesional': 'Profesional',
    'empresarial': 'Empresarial',
}

ASUNTOS = {
    'cotizacion': 'Cotización de servicio corporativo',
    'soporte': 'Soporte y atención al cliente',
    'aliados': 'Información para aliados y conductores',
    'integraciones': 'Integración API / E-commerce',
    'otro': 'Otras consultas generales',
}

@public_bp.route('/')
def index():
    session.clear()
    return render_template('public/index.html')

@public_bp.route('/rastreo', methods=['GET', 'POST'])
def rastreo():
    # Obtiene la guía desde la URL (?guia=...) o desde el input del formulario
    guia_buscada = request.args.get('guia') or request.form.get('guia_input', '')
    guia_buscada = guia_buscada.strip().upper() if guia_buscada else None

    paquete = None
    if guia_buscada:
        paquete = Paquete.query.filter_by(numero_guia=guia_buscada).first()
        if not paquete:
            flash(f"No encontramos la guía '{guia_buscada}'. Verifica el número.", "danger")

    return render_template('public/rastreo.html', paquete=paquete, guia_buscada=guia_buscada)

@public_bp.route('/servicios')
def servicios():
    return render_template('public/servicios.html')

@public_bp.route('/ser-aliado')
def ser_aliado():
    return render_template('public/ser_aliado.html')

@public_bp.route('/contacto', methods=['GET', 'POST'])
def contacto():
    plan_slug = (request.values.get('plan') or '').strip().lower()
    plan_seleccionado = PLANES.get(plan_slug)
    form_data = {}

    whatsapp_number = re.sub(
        r'\D', '', current_app.config.get('WHATSAPP_ADVISOR_NUMBER', '')
    )
    whatsapp_number = whatsapp_number if 8 <= len(whatsapp_number) <= 15 else ''

    if request.method == 'POST':
        form_data = {
            field: (request.form.get(field) or '').strip()
            for field in ('nombre', 'email', 'telefono', 'asunto', 'mensaje')
        }
        plan_slug = (request.form.get('plan') or '').strip().lower()
        plan_seleccionado = PLANES.get(plan_slug)

        if not all(form_data.values()) or form_data['asunto'] not in ASUNTOS:
            flash('Completa todos los campos para continuar.', 'danger')
        elif not whatsapp_number:
            flash(
                'El contacto por WhatsApp aún no está configurado. '
                'Por favor, inténtalo más tarde.',
                'danger',
            )
        else:
            lineas_mensaje = [
                'Hola DropX, quisiera hablar con un asesor.',
                f"Nombre: {form_data['nombre']}",
                f"Correo: {form_data['email']}",
                f"Teléfono: {form_data['telefono']}",
                f"Asunto: {ASUNTOS[form_data['asunto']]}",
            ]
            if plan_seleccionado:
                lineas_mensaje.append(f'Plan de interés: {plan_seleccionado}')
            lineas_mensaje.append(f"Mensaje: {form_data['mensaje']}")
            url_whatsapp = (
                f"https://wa.me/{whatsapp_number}"
                f"?text={quote(chr(10).join(lineas_mensaje))}"
            )
            return redirect(url_whatsapp, code=303)

    mensaje_inicial = (
        f'Me interesa recibir información sobre el plan {plan_seleccionado} '
        'y quisiera hablar con un asesor.'
        if plan_seleccionado else ''
    )
    mensaje_whatsapp = (
        f'Hola DropX, quisiera hablar con un asesor comercial sobre el plan '
        f'{plan_seleccionado}.'
        if plan_seleccionado else 'Hola DropX, quisiera hablar con un asesor.'
    )
    whatsapp_url = (
        f"https://wa.me/{whatsapp_number}?text={quote(mensaje_whatsapp)}"
        if whatsapp_number else None
    )

    return render_template(
        'public/contacto.html',
        plan_slug=plan_slug if plan_seleccionado else '',
        plan_seleccionado=plan_seleccionado,
        mensaje_inicial=mensaje_inicial,
        whatsapp_url=whatsapp_url,
        form_data=form_data,
    )

@public_bp.route('/recuperar-password')
def recuperar():
    return render_template('public/recuperar.html')

@public_bp.route('/nosotros')
def nosotros():
    return render_template('public/nosotros.html')

@public_bp.route('/privacidad')
def privacidad():
    return render_template('public/privacidad.html')

@public_bp.route('/terminos')
def terminos():
    return render_template('public/terminos.html')