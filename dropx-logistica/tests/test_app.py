"""Pruebas automatizadas de DropX Logística (ejecutar con `pytest` dentro de dropx-logistica/)."""
import re
from pathlib import Path

import pytest

from app.database import db
from app.models import Paquete, Repartidor

PUBLICAS = ['/', '/servicios', '/ser-aliado', '/contacto', '/nosotros',
            '/privacidad', '/terminos', '/rastreo']
MODULOS = ['/suite/dashboard', '/suite/paquetes', '/suite/repartidores',
           '/suite/logisticos', '/suite/reportes']


# ---------------------------------------------------------------- sitio público
@pytest.mark.parametrize('ruta', PUBLICAS)
def test_pagina_publica_responde_200(client, ruta):
    assert client.get(ruta).status_code == 200


def test_rastreo_guia_existente_normaliza_la_guia(client):
    html = client.get('/rastreo?guia=%20dx-9827461%20').get_data(as_text=True)
    assert 'DX-9827461' in html
    assert 'Carolina' in html


def test_rastreo_guia_inexistente_avisa(client):
    html = client.get('/rastreo?guia=DX-0000000').get_data(as_text=True)
    assert 'No encontramos la guía' in html


def test_contacto_vacio_muestra_el_error_al_usuario(client):
    r = client.post('/contacto', data={})
    assert r.status_code == 200
    assert 'Completa todos los campos' in r.get_data(as_text=True)


def test_contacto_valido_redirige_a_whatsapp(client):
    datos = {'nombre': 'Ana', 'email': 'ana@correo.com', 'telefono': '3001234567',
             'asunto': 'cotizacion', 'mensaje': 'Hola', 'plan': 'basico'}
    r = client.post('/contacto', data=datos)
    assert r.status_code == 303
    assert r.headers['Location'].startswith('https://wa.me/573001112233?text=')


def test_recuperar_publico_redirige_a_la_suite(client):
    r = client.get('/recuperar-password')
    assert r.status_code == 302
    assert r.headers['Location'].endswith('/suite/recuperar')


def test_todos_los_url_for_de_las_plantillas_existen(app):
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    faltantes = []
    for plantilla in Path(app.root_path, 'templates').rglob('*.html'):
        texto = plantilla.read_text(encoding='utf-8')
        for endpoint in re.findall(r"url_for\('([\w.]+)'", texto):
            if endpoint not in endpoints:
                faltantes.append((plantilla.name, endpoint))
    assert not faltantes, faltantes


# ------------------------------------------------------------ acceso y roles
@pytest.mark.parametrize('ruta', MODULOS)
def test_modulos_sin_sesion_redirigen_al_login(client, ruta):
    r = client.get(ruta)
    assert r.status_code == 302
    assert '/suite/login' in r.headers['Location']


def test_login_con_credenciales_invalidas(client):
    r = client.post('/suite/login', data={'email': 'x@x.com', 'password': 'mal'})
    assert r.status_code == 200
    assert 'Credenciales incorrectas' in r.get_data(as_text=True)


@pytest.mark.parametrize('ruta', MODULOS)
def test_superadmin_accede_a_todos_los_modulos(admin, ruta):
    assert admin.get(ruta).status_code == 200


def test_logistico_no_accede_a_reportes_pero_si_a_logisticos(logistico):
    r = logistico.get('/suite/reportes')
    assert r.status_code == 302
    assert r.headers['Location'].endswith('/suite/dashboard')
    assert logistico.get('/suite/logisticos').status_code == 200


def test_logout_cierra_la_sesion(admin):
    admin.get('/suite/logout')
    assert admin.get('/suite/dashboard').status_code == 302


def test_modulo_logistico_incluye_mapa_kpis_y_hubs(admin):
    html = admin.get('/suite/logisticos').get_data(as_text=True)
    for fragmento in ('id="mapaLogistico"', 'Rutas activas', 'Vehículos en operación',
                      'Tiempo promedio entrega', 'Eficiencia de ruta',
                      'badge-en-curso', 'hub-optimo', 'hub-critico'):
        assert fragmento in html, fragmento


# ------------------------------------------------------------------- paquetes
def _paquete(**cambios):
    datos = {'numero_guia': 'dx-1001', 'remitente': 'Tienda', 'destinatario': 'Luis',
             'ciudad': 'Cartagena', 'direccion': 'Calle 1 # 2-3', 'peso': '3.5'}
    datos.update(cambios)
    return datos


def _id_paquete(app, guia='DX-1001'):
    with app.app_context():
        return Paquete.query.filter_by(numero_guia=guia).one().id


def test_crear_paquete(app, admin):
    assert admin.post('/suite/paquetes', data=_paquete()).status_code == 302
    with app.app_context():
        p = Paquete.query.filter_by(numero_guia='DX-1001').one()
        assert p.estado == 'Recibido'
        assert p.peso == 3.5


@pytest.mark.parametrize('cambios', [{'peso': 'abc'}, {'peso': '0'}, {'peso': '-2'},
                                     {'peso': 'nan'}, {'peso': 'inf'}, {'remitente': ''}])
def test_crear_paquete_invalido_no_se_guarda(app, admin, cambios):
    admin.post('/suite/paquetes', data=_paquete(**cambios))
    with app.app_context():
        assert Paquete.query.filter_by(numero_guia='DX-1001').first() is None


def test_guia_duplicada_no_se_crea_dos_veces(app, admin):
    admin.post('/suite/paquetes', data=_paquete())
    admin.post('/suite/paquetes', data=_paquete())
    with app.app_context():
        assert Paquete.query.filter_by(numero_guia='DX-1001').count() == 1


def test_editar_paquete(app, admin):
    admin.post('/suite/paquetes', data=_paquete())
    pid = _id_paquete(app)
    r = admin.post(f'/suite/paquetes/{pid}/editar',
                   data={'remitente': 'Nueva', 'destinatario': 'Luis', 'ciudad': 'Bogotá',
                         'direccion': 'Cra 5', 'estado': 'Entregado', 'peso': '4'})
    assert r.status_code == 302
    with app.app_context():
        p = db.session.get(Paquete, pid)
        assert (p.remitente, p.estado, p.peso) == ('Nueva', 'Entregado', 4.0)


def test_editar_paquete_con_estado_invalido_no_cambia(app, admin):
    admin.post('/suite/paquetes', data=_paquete())
    pid = _id_paquete(app)
    admin.post(f'/suite/paquetes/{pid}/editar',
               data={'remitente': 'Nueva', 'destinatario': 'Luis', 'ciudad': 'Bogotá',
                     'direccion': 'Cra 5', 'estado': 'Volando', 'peso': '4'})
    with app.app_context():
        assert db.session.get(Paquete, pid).remitente == 'Tienda'


def test_eliminar_paquete(app, admin):
    admin.post('/suite/paquetes', data=_paquete())
    pid = _id_paquete(app)
    assert admin.post(f'/suite/paquetes/{pid}/eliminar').status_code == 302
    with app.app_context():
        assert db.session.get(Paquete, pid) is None


# ---------------------------------------------------------------- repartidores
def _repartidor(**cambios):
    datos = {'nombre': 'Pedro Pérez', 'zona': 'Zona Sur - Cali', 'telefono': '+57 300 111 2222',
             'estado': 'Activo', 'calificacion': '4.7', 'entregas_mes': '10'}
    datos.update(cambios)
    return datos


def _id_repartidor(app, nombre='Pedro Pérez'):
    with app.app_context():
        return Repartidor.query.filter_by(nombre=nombre).one().id


def test_crear_repartidor(app, admin):
    assert admin.post('/suite/repartidores', data=_repartidor()).status_code == 302
    assert _id_repartidor(app)


@pytest.mark.parametrize('cambios', [{'calificacion': '6'}, {'calificacion': '-1'},
                                     {'calificacion': 'abc'}, {'entregas_mes': '-3'},
                                     {'estado': 'Volando'}, {'nombre': ''}])
def test_crear_repartidor_invalido_no_se_guarda(app, admin, cambios):
    admin.post('/suite/repartidores', data=_repartidor(**cambios))
    with app.app_context():
        assert Repartidor.query.filter_by(zona='Zona Sur - Cali').first() is None


def test_editar_repartidor(app, admin):
    admin.post('/suite/repartidores', data=_repartidor())
    rid = _id_repartidor(app)
    r = admin.post(f'/suite/repartidores/{rid}/editar',
                   data=_repartidor(nombre='Pedro P. Gómez', estado='En ruta',
                                    calificacion='4.9', entregas_mes='25'))
    assert r.status_code == 302
    with app.app_context():
        rep = db.session.get(Repartidor, rid)
        assert (rep.nombre, rep.estado, rep.calificacion, rep.entregas_mes) == \
            ('Pedro P. Gómez', 'En ruta', 4.9, 25)


def test_editar_repartidor_invalido_no_cambia(app, admin):
    admin.post('/suite/repartidores', data=_repartidor())
    rid = _id_repartidor(app)
    admin.post(f'/suite/repartidores/{rid}/editar', data=_repartidor(calificacion='9'))
    with app.app_context():
        assert db.session.get(Repartidor, rid).calificacion == 4.7


def test_editar_repartidor_requiere_sesion(client):
    r = client.post('/suite/repartidores/1/editar', data=_repartidor())
    assert r.status_code == 302
    assert '/suite/login' in r.headers['Location']


def test_eliminar_repartidor(app, admin):
    admin.post('/suite/repartidores', data=_repartidor())
    rid = _id_repartidor(app)
    assert admin.post(f'/suite/repartidores/{rid}/eliminar').status_code == 302
    with app.app_context():
        assert db.session.get(Repartidor, rid) is None
