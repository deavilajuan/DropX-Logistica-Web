# DropX Web

Panel web, sitio público y API del proyecto DropX (gestión de entregas), desarrollados con Flask y MySQL.
La API es la que utiliza la app móvil [`dropx_app`](https://github.com/yammadev/dropx_app).

## Ejecutar en modo de prueba

Requisitos: Python 3.10 o superior y MySQL encendido (en XAMPP, el módulo MySQL) con la base de datos `dropx` creada.

**1. Instalar las dependencias** (terminal de VS Code, un comando por línea):

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**2. Crear el archivo `.env`** y cambiar `SECRET_KEY` y las contraseñas:

```bash
cp .env.example .env
```

**3. Crear las tablas, los usuarios iniciales y encender el servidor:**

```bash
flask --app app db upgrade
flask --app app seed
flask --app app run --debug
```

El sitio queda en <http://127.0.0.1:5000> y la Suite en <http://127.0.0.1:5000/suite/login>.

### Usuarios iniciales

Las contraseñas son las definidas en el `.env`.

| Nombre | Correo | Rol | Variable del `.env` |
|---|---|---|---|
| Administrador | `admin@dropx.com` | `admin` | `SEED_ADMIN_PASSWORD` |
| Manager | `manager@dropx.com` | `manager` | `SEED_MANAGER_PASSWORD` |
| Jhon Doe | `courier@dropx.com` | `courier` | `SEED_COURIER_PASSWORD` |

El comando `seed` puede repetirse sin problema: los usuarios que ya existen se omiten.

## Descripción

- **Sitio público:** inicio, servicios, ser aliado, contacto (redirige a WhatsApp), rastreo de guías, nosotros, privacidad y términos.
- **Suite (`/suite`):** panel para `admin` y `manager`: dashboard, paquetes (crear, filtrar, editar, eliminar), repartidores (crear, eliminar), logísticos (mapa de ejemplo) y reportes (solo `admin`, solo interfaz).
- **API (`/api`):** autenticación con JWT para la app móvil.

| Rol | Qué hace | Desde dónde ingresa |
|---|---|---|
| `admin` | Administra el sistema (reportes) | Suite |
| `manager` | Gestiona paquetes y repartidores | Suite |
| `courier` | Reparte los paquetes | App móvil |

Estados de una guía: **Pendiente**, **Recogido**, **Entregado** y **Con novedad**.
Todo número de guía lleva el formato `DX-123456`.

## API

Autenticación con JWT para la app móvil. Las rutas están documentadas en [docs/api.md](docs/api.md).

## Variables de entorno (`.env`)

| Variable | Descripción |
|---|---|
| `SECRET_KEY` | Firma la sesión del panel y los tokens JWT. Obligatoria. |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Conexión a MySQL (por defecto, XAMPP local: `localhost`, `3306`, `root`, sin contraseña y `dropx`). |
| `DB_SSL_CA` | Opcional. Ruta del certificado `.pem` para servicios en la nube que exigen SSL (ej: Aiven). |
| `JWT_EXPIRES_HOURS` | Duración del token de la API (por defecto, 8). |
| `WHATSAPP_ADVISOR_NUMBER` | Número del asesor para el formulario de contacto. |
| `SEED_*_PASSWORD` | Contraseñas de los usuarios que crea `seed`. |

## Arquitectura

- **`app/models.py`:** tablas `users`, `packages` y `package_events` (SQLAlchemy, como Eloquent).
- **`app/suite.py`, `app/public.py`, `app/api.py`:** rutas del panel, del sitio y de la API (un `Blueprint` por archivo, como un grupo de rutas de Laravel).
- **Librerías:** Flask-SQLAlchemy y Flask-Migrate (base de datos y migraciones), Flask-Login (sesión del panel), Flask-JWT-Extended (API) y Flask-WTF (protección CSRF de los formularios).

## Estructura de carpetas

```
dropx_web/
├── app/
│   ├── __init__.py       # Crea la app y conecta las extensiones
│   ├── models.py         # Tablas: users, packages y package_events
│   ├── public.py         # Rutas del sitio público
│   ├── suite.py          # Rutas del panel web (login, paquetes, repartidores)
│   ├── api.py            # Rutas de la API (login y me)
│   ├── seed.py           # Comando "seed": crea los usuarios iniciales
│   ├── templates/
│   │   ├── public/       # Páginas del sitio (base.html es el diseño común)
│   │   └── suite/        # Páginas del panel (base.html es el diseño común)
│   └── static/           # css, js e imágenes
├── docs/
│   └── api.md            # Rutas de la API
├── migrations/           # Migraciones de la base de datos (Flask-Migrate)
├── config.py             # Configuración (lee el .env)
├── requirements.txt      # Dependencias de Python
├── .env.example          # Modelo del .env (el .env real no se sube a GitHub)
├── .gitignore
└── README.md             # Documentación
```

Al cambiar los modelos, generar una nueva migración y aplicarla:

```bash
flask --app app db migrate -m "descripcion del cambio"
flask --app app db upgrade
```
