import os

import click
from flask.cli import with_appcontext

from app import db
from app.models import User

# (nombre, correo, rol, variable del .env con la contraseña)
USERS = [
    ('Administrador', 'admin@dropx.com', 'admin', 'SEED_ADMIN_PASSWORD'),
    ('Manager', 'manager@dropx.com', 'manager', 'SEED_MANAGER_PASSWORD'),
    ('Jhon Doe', 'courier@dropx.com', 'courier', 'SEED_COURIER_PASSWORD'),
]


# Se ejecuta con: flask --app app seed (como php artisan db:seed)
@click.command('seed')
@with_appcontext
def seed_command():
    """Crea los usuarios iniciales (los que ya existen se saltan)."""
    for name, email, role, password_var in USERS:
        if User.query.filter_by(email=email).first():
            click.echo(f'Ya existe: {email}')
            continue

        password = os.getenv(password_var)
        if not password:
            raise click.ClickException(f'Falta {password_var} en el archivo .env')

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        click.echo(f'Creado: {email} ({role})')

    db.session.commit()
