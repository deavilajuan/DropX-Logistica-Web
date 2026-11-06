# API de DropX

Todas las rutas empiezan con `/api` y responden JSON. La autenticación usa tokens JWT.

URL base en pruebas: `http://127.0.0.1:5000`
(en el emulador de Android: `http://10.0.2.2:5000`).

## Autenticación

### `POST /api/auth/login`

Inicia sesión. Sirve para los tres roles (`admin`, `manager` y `courier`).

Recibe:

```json
{ "email": "courier@dropx.com", "password": "su-clave" }
```

Responde `200`:

```json
{
  "token": "eyJhbGciOi...",
  "user": { "id": 3, "name": "Jhon Doe", "email": "courier@dropx.com", "role": "courier" }
}
```

| Código | Cuándo | Respuesta |
|---|---|---|
| `400` | Falta el correo o la contraseña | `{"message": "El correo y la contraseña son obligatorios"}` |
| `401` | Correo o contraseña incorrectos | `{"message": "Correo o contraseña incorrectos"}` |

### `GET /api/auth/me`

Devuelve el usuario dueño del token. Requiere el header `Authorization: Bearer <token>`.

Responde `200`:

```json
{ "user": { "id": 3, "name": "Jhon Doe", "email": "courier@dropx.com", "role": "courier" } }
```

| Código | Cuándo | Respuesta |
|---|---|---|
| `401` | Falta el token | `{"message": "Falta el token de acceso"}` |
| `401` | El token no es válido | `{"message": "El token no es válido"}` |
| `401` | El token expiró | `{"message": "El token expiró, inicia sesión de nuevo"}` |

El token dura las horas indicadas en `JWT_EXPIRES_HOURS` (por defecto, 8) y guarda el id y el rol del usuario.

## Probar desde la terminal

```powershell
$body = @{ email = 'courier@dropx.com'; password = 'su-clave' } | ConvertTo-Json
$res = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/auth/login -ContentType 'application/json' -Body $body
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/auth/me -Headers @{ Authorization = "Bearer $($res.token)" }
```

## Pendientes

- `GET /api/packages`: listado de guías del courier (filtro por estado) y detalle.
- Cambio de estado de una guía desde la app.
- CORS, si la app Flutter se prueba en Chrome.
