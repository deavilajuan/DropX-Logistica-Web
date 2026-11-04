from datetime import datetime
from app.database import db

class Paquete(db.Model):
    __tablename__ = 'paquetes'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_guia = db.Column(db.String(50), unique=True, nullable=False) # Ej: DX-9827461
    remitente = db.Column(db.String(120), nullable=False)
    destinatario = db.Column(db.String(120), nullable=False)
    direccion_entrega = db.Column(db.String(255), nullable=False)
    ciudad_destino = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(50), default='Recibido') # Recibido, En tránsito, En ruta de entrega, Entregado
    peso = db.Column(db.Float, default=1.0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_estimada = db.Column(db.String(100), default='Hoy, antes de las 6:00 PM')
    
    historial = db.relationship('HistorialRuta', backref='paquete', lazy=True, cascade="all, delete-orphan")

class HistorialRuta(db.Model):
    __tablename__ = 'historial_rutas'
    
    id = db.Column(db.Integer, primary_key=True)
    paquete_id = db.Column(db.Integer, db.ForeignKey('paquetes.id'), nullable=False)
    titulo = db.Column(db.String(150), nullable=False) # Ej: En ruta de entrega - Bogotá Norte
    descripcion = db.Column(db.String(255))
    hora = db.Column(db.String(100), nullable=False) # Ej: Hoy, 10:14 AM
    completado = db.Column(db.Boolean, default=True)

class Repartidor(db.Model):
    __tablename__ = 'repartidores'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    zona = db.Column(db.String(100), nullable=False) # Ej: Zona Norte - Bogotá
    telefono = db.Column(db.String(50), nullable=False)
    calificacion = db.Column(db.Float, default=5.0)
    entregas_mes = db.Column(db.Integer, default=0)
    estado = db.Column(db.String(50), default='Activo') # Activo, En ruta, Desconectado
