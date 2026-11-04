import os
from flask import Flask
from dotenv import load_dotenv
from app.database import db

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dropx_default_secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///dropx.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WHATSAPP_ADVISOR_NUMBER'] = (
        os.getenv('WHATSAPP_ADVISOR_NUMBER') or '573022224273'
    )

    db.init_app(app)

    # Registrar rutas
    from app.routes.public import public_bp
    from app.routes.suite import suite_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(suite_bp, url_prefix='/suite')

    # Crear tablas y datos de prueba automáticamente al iniciar
    with app.app_context():
        db.create_all()
        _crear_datos_iniciales()

    return app

def _crear_datos_iniciales():
    from app.models import Paquete, HistorialRuta, Repartidor
    # Insertar la guía de prueba de tu diseño si no existe
    if not Paquete.query.filter_by(numero_guia='DX-9827461').first():
        p = Paquete(
            numero_guia='DX-9827461',
            remitente='Tienda Virtual Moda Elite',
            destinatario='Carolina Pérez',
            direccion_entrega='Calle 127 #15-32, Apto 402, Bogotá',
            ciudad_destino='Bogotá',
            estado='En ruta de entrega',
            peso=2.5,
            fecha_estimada='Hoy, antes de las 6:00 PM'
        )
        db.session.add(p)
        db.session.flush()

        # Agregar eventos del historial que se ven en tu foto
        h1 = HistorialRuta(paquete_id=p.id, titulo='En ruta de entrega - Bogotá Norte', descripcion='El mensajero Diego R. se encuentra en camino a tu dirección.', hora='Hoy, 10:14 AM')
        h2 = HistorialRuta(paquete_id=p.id, titulo='Recibido en centro de distribución principal', descripcion='Clasificado y asignado al vehículo de reparto local.', hora='Ayer, 04:30 PM')
        h3 = HistorialRuta(paquete_id=p.id, titulo='Guía generada por remitente', descripcion='Sincronizado desde Tienda Virtual Moda Elite.', hora='14 de Octubre, 09:12 AM')
        db.session.add_all([h1, h2, h3])

        # Agregar un par de repartidores de tu Figma
        r1 = Repartidor(nombre='José Carlos Gómez', zona='Zona Norte - Bogotá', telefono='+57 312 456 7890', calificacion=4.9, entregas_mes=142, estado='En ruta')
        r2 = Repartidor(nombre='Alberto Luis Restrepo', zona='El Poblado - Medellín', telefono='+57 315 789 1234', calificacion=4.8, entregas_mes=128, estado='Activo')
        db.session.add_all([r1, r2])

        db.session.commit()
