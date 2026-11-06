from flask import Flask
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from config import Config

# Extensiones (se conectan a la app dentro de create_app)
db = SQLAlchemy()  # base de datos (como Eloquent)
migrate = Migrate()  # migraciones (como php artisan migrate)
login_manager = LoginManager()  # sesión del panel web
jwt = JWTManager()  # tokens de la API
csrf = CSRFProtect()  # protección de los formularios del panel

login_manager.login_view = 'suite.login'
login_manager.login_message = 'Debes iniciar sesión para acceder a la Suite Logística.'
login_manager.login_message_category = 'danger'


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if not app.config['SECRET_KEY']:
        raise RuntimeError('Falta SECRET_KEY en el archivo .env')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)

    # Importar los modelos para que las migraciones los detecten
    from app import models

    # Rutas: sitio público, panel web (/suite) y API (/api)
    from app import api, public, suite
    app.register_blueprint(public.bp)
    app.register_blueprint(suite.bp)
    app.register_blueprint(api.bp)
    csrf.exempt(api.bp)  # la API usa JWT, no cookies

    # Comando: flask --app app seed
    from app.seed import seed_command
    app.cli.add_command(seed_command)

    # Estados de las guías disponibles en todas las plantillas
    @app.context_processor
    def inject_statuses():
        return {'STATUSES': models.STATUSES}

    return app
