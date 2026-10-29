#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor del sitio Pimbert · Deslizora.

Usa solamente la librería estándar de Python 3.8 o superior: no hay que instalar nada.

    python servidor.py          ->  http://localhost:8000
    python servidor.py 8080     ->  otro puerto

Qué hace:
  * Crea la base de datos SQLite (datos/pimbert.db) la primera vez, desde base_de_datos.sql.
  * Entrega las páginas de la carpeta sitio/. Los bloques marcados con <!--DB:nombre--> ... <!--/DB:nombre-->
    se rellenan con lo que hay en la base (menú, pie, tarjetas del index, FAQ, materiales, etc.).
  * Recibe las consultas del formulario (POST /api/consultas) y las guarda en la tabla "consultas".
  * Ofrece un panel protegido con clave para ver esas consultas: /admin
"""
import hmac
import json
import os
import re
import secrets
import sqlite3
import sys
import threading
import time
import webbrowser
from contextlib import closing
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

BASE = Path(__file__).resolve().parent
SITIO = (BASE / 'sitio').resolve()
DATOS = BASE / 'datos'
DB_RUTA = Path(os.environ.get('PIMBERT_DB', DATOS / 'pimbert.db'))
SQL_RUTA = BASE / 'base_de_datos.sql'
CLAVE_RUTA = DATOS / 'clave_admin.txt'
CLAVE = ''  # se carga al iniciar
MAX_CONSULTAS = int(os.environ.get('PIMBERT_MAX_CONSULTAS', 8))  # envíos por IP cada 10 minutos

TIPOS = {
    '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8', '.mp4': 'video/mp4', '.svg': 'image/svg+xml',
    '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.webp': 'image/webp', '.ico': 'image/x-icon',
}


# ───────────────────────────── Base de datos ─────────────────────────────

def conectar():
    db = sqlite3.connect(DB_RUTA, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    return db


def inicializar_bd():
    if DB_RUTA.exists():
        return
    DB_RUTA.parent.mkdir(parents=True, exist_ok=True)
    try:
        with closing(sqlite3.connect(DB_RUTA)) as db:
            db.executescript(SQL_RUTA.read_text(encoding='utf-8'))
            db.commit()
    except Exception:
        DB_RUTA.unlink(missing_ok=True)
        raise


def cargar_clave():
    """Clave del panel: variable PIMBERT_ADMIN_CLAVE, o la de datos/clave_admin.txt (se genera sola)."""
    if os.environ.get('PIMBERT_ADMIN_CLAVE'):
        return os.environ['PIMBERT_ADMIN_CLAVE']
    if CLAVE_RUTA.exists():
        return CLAVE_RUTA.read_text(encoding='utf-8').strip()
    clave = secrets.token_urlsafe(9)
    CLAVE_RUTA.write_text(clave, encoding='utf-8')
    return clave


# ───────────── Armado de las páginas (misma estructura HTML que el sitio original) ─────────────

def e(valor):
    return escape(str(valor), quote=True)


FLECHA = ('<svg fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" '
          'stroke-width="2" viewbox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"></path></svg>')
ICONO = ('<svg fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" '
         'viewbox="0 0 24 24">{}</svg>')


def r_menu(db, actual):
    filas = db.execute('SELECT * FROM paginas WHERE en_menu = 1 ORDER BY es_boton, orden')
    out = []
    for p in filas:
        cur = ' aria-current="page"' if p['archivo'] == actual else ''
        if p['es_boton']:
            out.append(f'<a{cur} class="button button-primary" href="{e(p["archivo"])}">{e(p["titulo_menu"])} {FLECHA}</a>')
        else:
            out.append(f'<a{cur} href="{e(p["archivo"])}">{e(p["titulo_menu"])}</a>')
    return '\n'.join(out)


def r_pie(db, actual):
    out = []
    for p in db.execute('SELECT * FROM paginas ORDER BY orden'):
        cur = ' aria-current="page"' if p['archivo'] == actual else ''
        out.append(f'<a{cur} href="{e(p["archivo"])}">{e(p["titulo_pie"])}</a>')
    return ''.join(out)


def r_tarjetas(db, actual):
    return '\n'.join(
        f'<article class="explore-card"><span class="explore-num">{p["orden"]:02d}</span><h3>{e(p["tarjeta_titulo"])}</h3>'
        f'<p>{e(p["tarjeta_descripcion"])}</p><a class="explore-link" href="{e(p["archivo"])}">{e(p["tarjeta_enlace"])} '
        f'<span aria-hidden="true">→</span></a></article>'
        for p in db.execute('SELECT * FROM paginas WHERE tarjeta_titulo IS NOT NULL ORDER BY orden'))


def r_caracteristicas(db, actual):
    return '\n'.join(
        f'<article class="feature-card">\n<div class="feature-icon">{ICONO.format(c["icono_svg"])}</div>\n'
        f'<h3>{e(c["titulo"])}</h3>\n<p>{e(c["descripcion"])}</p>\n</article>'
        for c in db.execute('SELECT * FROM caracteristicas ORDER BY orden'))


def r_puntos(db, actual):
    return '\n'.join(f'<div class="summary-point"><span>{p["orden"]:02d}</span>{e(p["titulo"])}</div>'
                     for p in db.execute('SELECT * FROM puntos_resumen ORDER BY orden'))


def r_pasos(db, actual):
    return '\n'.join(
        f'<article class="step"><div class="step-number">{p["orden"]}</div><h3>{e(p["titulo"])}</h3><p>{e(p["descripcion"])}</p></article>'
        for p in db.execute('SELECT * FROM pasos ORDER BY orden'))


def _materiales(grupo):
    def render(db, actual):
        return '\n'.join(
            f'<div class="material"><div class="material-symbol">{e(m["simbolo"])}</div>'
            f'<div><h3>{e(m["nombre"])}</h3><p>{e(m["descripcion"])}</p></div></div>'
            for m in db.execute('SELECT * FROM materiales WHERE grupo = ? ORDER BY orden', (grupo,)))
    return render


def r_ambitos(db, actual):
    return '\n'.join(
        f'<article class="use-card">\n<div class="use-icon">{ICONO.format(a["icono_svg"])}</div>\n'
        f'<h3>{e(a["titulo"])}</h3>\n<p>{e(a["descripcion"])}</p>\n<span class="use-tag">{e(a["etiqueta"])}</span>\n</article>'
        for a in db.execute('SELECT * FROM ambitos_uso ORDER BY orden'))


def r_preguntas(db, actual):
    return '\n'.join(
        f'<details>\n<summary>{e(q["pregunta"])}</summary>\n<p>{e(q["respuesta"])}</p>\n</details>'
        for q in db.execute('SELECT * FROM preguntas_frecuentes ORDER BY orden'))


def r_espacios(db, actual):
    return ''.join(f'<option value="{t["id"]}">{e(t["nombre"])}</option>'
                   for t in db.execute('SELECT * FROM tipos_espacio ORDER BY orden'))


REGIONES = {
    'menu': r_menu, 'pie': r_pie, 'tarjetas': r_tarjetas,
    'caracteristicas': r_caracteristicas, 'puntos': r_puntos, 'pasos': r_pasos,
    'materiales_prototipo': _materiales('prototipo'), 'materiales_fabricacion': _materiales('fabricacion'),
    'ambitos': r_ambitos, 'preguntas': r_preguntas, 'espacios': r_espacios,
}


def render_pagina(html, db, actual):
    """Reemplaza el contenido de cada bloque <!--DB:x-->...<!--/DB:x--> con lo que hay en la base."""
    def reemplazo(m):
        fn = REGIONES.get(m.group(1))
        return m.group(0) if fn is None else f'<!--DB:{m.group(1)}-->\n{fn(db, actual)}\n<!--/DB:{m.group(1)}-->'
    return re.sub(r'<!--DB:(\w+)-->.*?<!--/DB:\1-->', reemplazo, html, flags=re.S)


# ───────────────────────────── Límites de uso ─────────────────────────────

_intentos, _cerrojo = {}, threading.Lock()


def _recientes(clave, ventana):
    ahora = time.time()
    return [t for t in _intentos.get(clave, []) if ahora - t < ventana]


def limitado(clave, maximo, ventana):
    with _cerrojo:
        return len(_recientes(clave, ventana)) >= maximo


def anotar(clave, ventana=600):
    with _cerrojo:
        _intentos[clave] = _recientes(clave, ventana) + [time.time()]


# ───────────────────────────── Validación de consultas ─────────────────────────────

CAMPOS = [  # (clave, nombre visible, máximo, obligatorio)
    ('nombre', 'Nombre', 120, True), ('contacto', 'Contacto', 160, True),
    ('institucion', 'Institución o empresa', 160, False), ('ancho', 'Ancho', 40, False),
    ('alto', 'Alto', 40, False), ('detalles', 'Detalles', 2000, False),
]


def validar_consulta(datos, db):
    """Devuelve (valores, error). Si hay error, valores es None."""
    valores = {}
    for clave, visible, maximo, obligatorio in CAMPOS:
        v = datos.get(clave) or ''
        if not isinstance(v, str):
            return None, 'Los datos enviados no son válidos.'
        v = v.strip()
        if obligatorio and not v:
            return None, f'Completá el campo «{visible}».'
        if len(v) > maximo:
            return None, f'El campo «{visible}» admite hasta {maximo} caracteres.'
        valores[clave] = v or None
    c = valores['contacto']
    if not (re.search(r'\S+@\S+\.\S+', c) or len(re.sub(r'\D', '', c)) >= 6):
        return None, 'Ingresá un email o un teléfono de contacto válido.'
    try:
        espacio = int(datos.get('tipo_espacio_id'))
    except (TypeError, ValueError):
        espacio = None
    if espacio is None or not db.execute('SELECT 1 FROM tipos_espacio WHERE id = ?', (espacio,)).fetchone():
        return None, 'Elegí dónde usarías Deslizora.'
    valores['tipo_espacio_id'] = espacio
    return valores, None


# ───────────────────────────── Servidor HTTP ─────────────────────────────

class Manejador(BaseHTTPRequestHandler):
    server_version = 'PimbertServidor/1.0'

    # --- respuestas ---
    def _cabeceras(self, codigo, tipo, largo, extra=None):
        self.send_response(codigo)
        self.send_header('Content-Type', tipo)
        self.send_header('Content-Length', str(largo))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        extra = dict(extra or {})
        extra.setdefault('Cache-Control', 'no-cache')
        for k, v in extra.items():
            self.send_header(k, v)
        self.end_headers()

    def _enviar(self, codigo, cuerpo=b'', tipo='text/plain; charset=utf-8', extra=None):
        self._cabeceras(codigo, tipo, len(cuerpo), extra)
        if self.command != 'HEAD':
            self.wfile.write(cuerpo)

    def _json(self, codigo, obj):
        self._enviar(codigo, json.dumps(obj, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')

    def _leer_json(self):
        try:
            largo = int(self.headers.get('Content-Length') or 0)
            if not 0 < largo <= 20000:
                return None
            datos = json.loads(self.rfile.read(largo).decode('utf-8'))
            return datos if isinstance(datos, dict) else None
        except (ValueError, UnicodeDecodeError):
            return None

    # --- archivos estáticos ---
    def _archivo(self, destino, tipo):
        tam = destino.stat().st_size
        ini, fin, codigo, extra = 0, tam - 1, 200, {'Accept-Ranges': 'bytes', 'Cache-Control': 'public, max-age=3600'}
        m = re.fullmatch(r'bytes=(\d*)-(\d*)', (self.headers.get('Range') or '').strip())
        if m and (m.group(1) or m.group(2)):  # los navegadores piden los videos por tramos
            if m.group(1):
                ini = int(m.group(1))
                fin = int(m.group(2)) if m.group(2) else tam - 1
            else:
                ini = max(tam - int(m.group(2)), 0)
            fin = min(fin, tam - 1)
            if ini > fin:
                return self._enviar(416, b'', extra={'Content-Range': f'bytes */{tam}'})
            codigo = 206
            extra['Content-Range'] = f'bytes {ini}-{fin}/{tam}'
        self._cabeceras(codigo, tipo, fin - ini + 1, extra)
        if self.command == 'HEAD':
            return
        try:
            with open(destino, 'rb') as f:
                f.seek(ini)
                restante = fin - ini + 1
                while restante > 0:
                    bloque = f.read(min(65536, restante))
                    if not bloque:
                        break
                    self.wfile.write(bloque)
                    restante -= len(bloque)
        except (BrokenPipeError, ConnectionResetError):
            pass  # el navegador cortó la descarga (normal con videos)

    def _estatico(self, ruta):
        ruta = {'/': '/index.html', '/admin': '/admin.html'}.get(ruta, ruta)
        try:
            destino = (SITIO / ruta.lstrip('/')).resolve()
            destino.relative_to(SITIO)
            tipo = TIPOS.get(destino.suffix.lower())
            if tipo is None or not destino.is_file():
                raise ValueError
        except (ValueError, OSError):
            return self._enviar(404, 'Página no encontrada'.encode('utf-8'))
        if destino.suffix.lower() != '.html':
            return self._archivo(destino, tipo)
        texto = destino.read_text(encoding='utf-8')
        if destino.name != 'admin.html':
            try:
                with closing(conectar()) as db:
                    texto = render_pagina(texto, db, destino.name)
            except Exception as error:  # si la base falla, se muestra el contenido estático de respaldo
                sys.stderr.write(f'[aviso] No se pudo leer la base de datos: {error}\n')
        self._enviar(200, texto.encode('utf-8'), tipo)

    # --- panel de administración ---
    def _autorizado(self):
        clave_ip = 'admin:' + self.client_address[0]
        if limitado(clave_ip, 10, 600):
            self._json(429, {'ok': False, 'error': 'Demasiados intentos. Esperá unos minutos.'})
            return False
        auth = self.headers.get('Authorization', '')
        token = auth[7:] if auth.startswith('Bearer ') else ''
        if token and hmac.compare_digest(token.encode('utf-8'), CLAVE.encode('utf-8')):
            return True
        anotar(clave_ip)
        self._json(401, {'ok': False, 'error': 'Clave incorrecta.'})
        return False

    def _admin(self, ruta):
        m = re.fullmatch(r'/api/admin/consultas(?:/(\d+))?', ruta)
        if not m:
            return self._json(404, {'ok': False, 'error': 'No encontrado'})
        if not self._autorizado():
            return
        cid = int(m.group(1)) if m.group(1) else None
        with closing(conectar()) as db:
            if self.command == 'GET' and cid is None:
                filas = db.execute(
                    'SELECT c.id, c.creada_en, c.nombre, c.contacto, c.institucion, c.ancho, c.alto, '
                    't.nombre AS espacio, c.detalles, c.estado FROM consultas c '
                    'JOIN tipos_espacio t ON t.id = c.tipo_espacio_id ORDER BY c.id DESC').fetchall()
                return self._json(200, {'ok': True, 'consultas': [dict(f) for f in filas]})
            if cid is None:
                return self._json(405, {'ok': False, 'error': 'Método no permitido'})
            if self.command == 'PATCH':
                datos = self._leer_json() or {}
                if datos.get('estado') not in ('nueva', 'atendida'):
                    return self._json(400, {'ok': False, 'error': 'Estado inválido.'})
                n = db.execute('UPDATE consultas SET estado = ? WHERE id = ?', (datos['estado'], cid)).rowcount
            elif self.command == 'DELETE':
                n = db.execute('DELETE FROM consultas WHERE id = ?', (cid,)).rowcount
            else:
                return self._json(405, {'ok': False, 'error': 'Método no permitido'})
            db.commit()
        self._json(200 if n else 404, {'ok': bool(n)})

    # --- métodos HTTP ---
    def do_GET(self):
        ruta = unquote(urlsplit(self.path).path)
        if ruta.startswith('/api/admin/'):
            return self._admin(ruta)
        if ruta.startswith('/api/'):
            return self._json(404, {'ok': False, 'error': 'No encontrado'})
        self._estatico(ruta)

    do_HEAD = do_GET

    def do_PATCH(self):
        self._admin(urlsplit(self.path).path)

    do_DELETE = do_PATCH

    def do_POST(self):
        if urlsplit(self.path).path != '/api/consultas':
            return self._json(404, {'ok': False, 'error': 'No encontrado'})
        clave_ip = 'consulta:' + self.client_address[0]
        if limitado(clave_ip, MAX_CONSULTAS, 600):
            return self._json(429, {'ok': False, 'error': 'Enviaste muchas consultas seguidas. Probá de nuevo en unos minutos.'})
        anotar(clave_ip)
        datos = self._leer_json()
        if datos is None:
            return self._json(400, {'ok': False, 'error': 'Los datos enviados no son válidos.'})
        with closing(conectar()) as db:
            v, error = validar_consulta(datos, db)
            if error:
                return self._json(400, {'ok': False, 'error': error})
            cur = db.execute(
                'INSERT INTO consultas (nombre, contacto, institucion, ancho, alto, tipo_espacio_id, detalles) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                (v['nombre'], v['contacto'], v['institucion'], v['ancho'], v['alto'], v['tipo_espacio_id'], v['detalles']))
            db.commit()
        self._json(201, {'ok': True, 'id': cur.lastrowid})

    def log_message(self, formato, *args):
        sys.stderr.write('%s  %s\n' % (time.strftime('%H:%M:%S'), formato % args))


def main():
    global CLAVE
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
        sys.stderr.reconfigure(errors='replace')
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '127.0.0.1')
    inicializar_bd()
    CLAVE = cargar_clave()
    servidor = ThreadingHTTPServer((host, puerto), Manejador)
    url = f'http://localhost:{puerto}'
    print('=' * 60)
    print(' Pimbert · Deslizora funcionando')
    print(f' Sitio:            {url}')
    print(f' Panel de consultas: {url}/admin')
    print(f' Clave del panel:  {CLAVE}')
    print(' Para detener el servidor: Ctrl + C')
    print('=' * 60)
    if os.environ.get('NO_ABRIR') != '1':
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print('\nServidor detenido.')


if __name__ == '__main__':
    main()
