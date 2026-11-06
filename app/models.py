from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager

# Roles del sistema
ROLES = ('admin', 'manager', 'courier')

# Estados de una guía (clave guardada en la base de datos -> texto en pantalla)
STATUSES = {
    'pending': 'Pendiente',
    'picked_up': 'Recogido',
    'delivered': 'Entregado',
    'issue': 'Con novedad',
}


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, manager o courier
    phone = db.Column(db.String(30))  # solo couriers
    zone = db.Column(db.String(100))  # solo couriers
    created_at = db.Column(db.DateTime, server_default=db.text('CURRENT_TIMESTAMP'))

    # La contraseña nunca se guarda en texto plano
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Datos que devuelve la API (sin la contraseña)
    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email, 'role': self.role}


class Package(db.Model):
    __tablename__ = 'packages'

    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(20), unique=True, nullable=False)  # ej: DX-152216
    sender = db.Column(db.String(120), nullable=False)
    recipient = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    weight = db.Column(db.Float, nullable=False, default=1.0)
    status = db.Column(db.String(20), nullable=False, default='pending')
    courier_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, server_default=db.text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(
        db.DateTime, server_default=db.text('CURRENT_TIMESTAMP'), onupdate=datetime.now
    )
    delivered_at = db.Column(db.DateTime)

    courier = db.relationship('User')
    events = db.relationship(
        'PackageEvent',
        order_by='PackageEvent.id.desc()',  # el más reciente primero
        cascade='all, delete-orphan',
    )

    @property
    def status_label(self):
        return STATUSES[self.status]


# Historial de movimientos de una guía (lo que ve el cliente en el rastreo)
class PackageEvent(db.Model):
    __tablename__ = 'package_events'

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(
        db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False
    )
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.text('CURRENT_TIMESTAMP'))


# Flask-Login usa esta función para saber quién tiene la sesión abierta
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
