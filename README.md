# DropX Logística (prototipo web)

Prototipo desarrollado para la asignatura de Ingeniería de Software de la Universidad Tecnológica de Bolívar (Colombia).
Simula una empresa de envíos y distribución (tipo Servientrega o Interrapidísimo): es solo un prototipo académico.

## Qué incluye

- **Sitio público:** inicio, servicios, nosotros, ser aliado, contacto (redirige a WhatsApp), rastreo de guías, privacidad y términos.
- **Suite logística (`/suite`):** login con roles, dashboard, paquetes (crear, filtrar, editar, eliminar), repartidores (crear, editar, eliminar), módulo logístico con mapa (Leaflet) y reportes (solo Superadmin, interfaz sin generación real de archivos).

## Requisitos

- Python 3.10 o superior

## Instalación y ejecución (Windows, PowerShell)

```powershell
cd dropx-logistica
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r ..\requirements.txt
copy ..\.env.example .env        # y edita los valores
python run.py
```

Abre http://127.0.0.1:5000. La base de datos SQLite y los datos de ejemplo (guía `DX-9827461`) se crean solos al iniciar.

En Linux/macOS: `source .venv/bin/activate` y `cp ../.env.example .env`.

## Variables de entorno (`.env`)

| Variable | Descripción |
|---|---|
| `SECRET_KEY` | Clave de sesión de Flask. Cámbiala siempre fuera de desarrollo. |
| `DATABASE_URL` | Conexión a la base de datos (por defecto `sqlite:///dropx.db`). |
| `WHATSAPP_ADVISOR_NUMBER` | Número del asesor para el formulario de contacto. |

## Cuentas de demostración (Suite)

| Rol | Correo | Contraseña |
|---|---|---|
| Superadmin | admin@dropx.com | admin123 |
| Logístico | logistica@dropx.com | logistica123 |

> Son credenciales de demostración escritas en el código. No usar en producción.

## Pruebas automatizadas

```powershell
cd dropx-logistica
pip install -r ..\requirements-dev.txt
python -m pytest
```

Las pruebas usan una base de datos temporal y no tocan `instance/dropx.db`.

## Estructura

```
dropx-logistica/
├── run.py
├── app/
│   ├── __init__.py        # fábrica de la app y datos de ejemplo
│   ├── models.py          # Paquete, HistorialRuta, Repartidor
│   ├── routes/            # public.py (sitio) y suite.py (panel interno)
│   ├── templates/         # layouts/, public/, suite/
│   └── static/            # css, js e imágenes
└── tests/                 # pruebas con pytest
```

## Pendientes conocidos

- Recuperación de contraseña por correo (la pantalla existe, el envío no).
- Generación real de reportes PDF/Excel.
- Autenticación con usuarios en base de datos y contraseñas con hash; protección CSRF.
- Integración API / e-commerce (solo contenido informativo).
