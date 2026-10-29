from flask import Blueprint, render_template, request, flash, session
from app.models import Paquete

public_bp = Blueprint('public', __name__)

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

@public_bp.route('/contacto')
def contacto():
    return render_template('public/contacto.html')

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