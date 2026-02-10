"""Helpers para búsquedas contra la API de Chosic.

Provee funciones para:
- get_track(api: ChosicAPI, track_id: str): Obtiene información de una pista
- get_artists(api: ChosicAPI, ids: str|list[str]): Obtiene información de artistas
- fetch_audio_features(api: ChosicAPI, track_id: str, timeout: float|None = None): Obtiene características de audio
- get_genre_releases(api: ChosicAPI, genre: str, limit: int|None = None, extra_params: dict|None = None): Obtiene lanzamientos por género
- recommendations(api: ChosicAPI, seed_tracks=None, seed_artists=None, limit: int = 100, extra_params: dict|None = None, fetch_all: bool = False, page_size: int = 100): Obtiene recomendaciones
- search(api: ChosicAPI, q: str, type: str = 'track', limit: int = 10, extra_params: dict|None = None, fetch_all: bool = False, page_size: int = 10): Realiza búsquedas
- get_top_playlists(api: ChosicAPI, artist_id: str|None = None, genre_name: str|None = None, limit: int|None = None, extra_params: dict|None = None): Obtiene top playlists

Cada función tiene su contraparte `_auto` que crea la API internamente.

Incluye también ThreadRunner para ejecución en hilos con callbacks.

SISTEMA DE LOGGING CENTRALIZADO:

Este módulo configura un LOGGER RAÍZ que es compartido por todos los módulos importados
(Cliente, Service, Downloader). Esto permite un control unificado del nivel de logging
desde la CLI o desde código.

La función _configure_logging(verbose, debug, quiet) configura el logger raíz (root logger)
con uno de estos niveles:
- quiet=True: logging.ERROR (solo errores)
- debug=True: logging.DEBUG (máximo detalle)
- verbose=True: logging.INFO (información útil)
- default: logging.WARNING (advertencias y errores)

Todos los módulos (Cliente, Service, Downloader) heredan esta configuración automáticamente
porque usan logging.getLogger(__name__), que por defecto propaga hacia el root logger.

IMPORTANTE: El logger raíz SOLO se configura si no tiene handlers existentes (evita duplicados).
Si necesitas cambiar el nivel después, solo usa: logging.getLogger().setLevel(nuevo_nivel)

CAMBIAR LOGGER EN OTRO CONTEXTO (sin CLI):

Si eliminas la CLI o ejecutas el código desde otra aplicación (GUI, web app, etc),
necesitas configurar el logger raíz ANTES de importar los módulos:

    import logging
    
    # Configurar logging raíz ANTES de importar ChosicAlpha
    logging.basicConfig(
        level=logging.DEBUG,  # o INFO, WARNING, ERROR, CRITICAL
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # DESPUÉS de configurar, importar los módulos
    from ChosicAlpha.Busqueda import search
    from ChosicAlpha.Cliente import create_ready_api_from_args
    
    # Ahora todas las operaciones estarán logeadas

Alternativa: Si quieres controlar logging desde tu aplicación:

    import logging
    
    def setup_custom_logging(debug=False):
        '''Configura logging personalizado para tu aplicación.'''
        level = logging.DEBUG if debug else logging.INFO
        root = logging.getLogger()
        
        # Limpiar handlers existentes
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        
        # Crear nuevo handler personalizado
        handler = logging.FileHandler('mi_app.log')  # o StreamHandler, etc
        formatter = logging.Formatter(
            '[%(asctime)s] %(name)s | %(levelname)-8s | %(message)s',
            '%H:%M:%S'
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)
        root.setLevel(level)
    
    # Llamar ANTES de usar ChosicAlpha
    setup_custom_logging(debug=True)

    from ChosicAlpha.Busqueda import search
    # Ahora logging usa tu formato personalizado

"""

from __future__ import annotations

import argparse
import configparser
import json
import logging
import os
import re
import sys
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import requests


# Asegurar import local
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Soportar ejecución tanto como módulo como script directo
try:
    # Importación relativa (cuando se ejecuta como módulo)
    from . import __version__
    from .models import ChosicResponse, ArtistDetail, Features, TrackItem, TracksCollection
    from .Cliente import create_chosic_api, create_ready_api_from_args, ChosicAPIError, ChosicAPI
    from .Service import ChosicService
    from .json_utils import dump_json, dumps_json
except ImportError:
    # Importación absoluta (cuando se ejecuta como script directo)
    from ChosicAlpha import __version__
    from ChosicAlpha.models import ChosicResponse, ArtistDetail, Features, TrackItem, TracksCollection
    from ChosicAlpha.Cliente import create_chosic_api, create_ready_api_from_args, ChosicAPIError, ChosicAPI
    from ChosicAlpha.Service import ChosicService
    from ChosicAlpha.json_utils import dump_json, dumps_json

logger = logging.getLogger(__name__)


def _configure_logging(verbose: bool = False, debug: bool = False, quiet: bool = False) -> None:
    """Configura el logging global para Busqueda y todos los módulos importados.
    
    Esta función configura el ROOT LOGGER (logger raíz), no solo Busqueda.
    Esto significa que módulos como Downloader, Service y Cliente automáticamente
    respetan la configuración global porque heredan del root logger.
    
    Niveles de logging (en orden de verbosidad):
    - quiet=True: logging.ERROR
      Solo muestra errores críticos. Ideal para scripts de producción.
    - verbose=True: logging.INFO
      Muestra eventos de interés general. Recomendado con --fetch-all.
    - debug=True: logging.DEBUG
      Máximo detalle: parámetros, páginas cargadas, merges, etc.
    - por defecto: logging.WARNING
      Muestra advertencias y errores. Balance por defecto.
    
    COMPORTAMIENTO:
    - Solo configura basicConfig si el root logger no tiene handlers aún.
    - Si ya hay handlers (ej. otra aplicación los configuró), solo actualiza el nivel.
    - Usa formato: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    EJEMPLO DE USO (si necesitas cambiar logging después):
    
        import logging
        from ChosicAlpha.Busqueda import _configure_logging
        
        _configure_logging(verbose=True)  # Cambiar a INFO
        
        # Ahora todas las operaciones mostrarán nivel INFO
    
    NOTAS IMPORTANTES:
    - Esta función DEBE ser llamada ANTES de usar search(), recommendations(), etc.
    - En la CLI, se llama automáticamente en main() basado en --quiet/--verbose/--debug.
    - Si eliminas la CLI, llama a esta función o usa logging.basicConfig() directamente.
    """
    if quiet:
        level = logging.ERROR
    elif debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    
    # Configurar el ROOT logger para que todos los módulos respeten la configuración
    root_logger = logging.getLogger()
    
    # Solo configurar basicConfig si aún no hay handlers (evitar duplicados)
    if not root_logger.handlers:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Si ya hay handlers, solo actualizar el nivel del root logger
        root_logger.setLevel(level)
    
    # Actualizar nivel de nuestro logger específico
    logger.setLevel(level)


def _load_config_file() -> dict[str, Any]:
    """Carga la configuración desde archivo .chosicrc (local o ~/).
    
    Busca en este orden:
    1. .chosicrc en el directorio actual
    2. ~/.chosicrc en el home del usuario
    
    Retorna un dict con las opciones encontradas.
    """
    config_paths = [
        Path('.chosicrc'),
        Path.home() / '.chosicrc'
    ]
    
    config = {}
    
    for config_path in config_paths:
        if config_path.exists():
            logger.debug(f'Leyendo archivo de configuración: {config_path}')
            parser = configparser.ConfigParser()
            try:
                parser.read(config_path)
                
                # Parsear secciones y convertir a dict
                for section in parser.sections():
                    for key, value in parser.items(section):
                        # Convertir valores comunes a tipos Python
                        if value.lower() in ('true', 'yes', 'on', '1'):
                            config[key] = True
                        elif value.lower() in ('false', 'no', 'off', '0'):
                            config[key] = False
                        elif value.isdigit():
                            config[key] = int(value)
                        else:
                            try:
                                config[key] = float(value)
                            except ValueError:
                                config[key] = value
                
                logger.info(f'Configuración cargada desde: {config_path}')
                logger.debug(f'Parámetros encontrados: {list(config.keys())}')
                return config
            except Exception as e:
                logger.warning(f'Error leyendo {config_path}: {e}')
                continue
    
    logger.debug('No se encontró archivo de configuración (.chosicrc)')
    return config


class ThreadRunner:
    """Utilidad para ejecutar funciones en hilos (ThreadPoolExecutor) con callbacks.

    - submit(func, *args, callback=None, err_callback=None, tk_root=None)
      ejecuta `func(*args)` en un worker; cuando termina llama a `callback(result)`
      o `err_callback(exception)`. Si se pasa `tk_root` (un objeto Tk), los
      callbacks se invocan usando `tk_root.after(0, ...)` para correr en hilo UI.
    - shutdown() cierra el pool.
    """

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()

    def submit(
        self,
        func: Callable,
        *args: Any,
        callback: Callable[[Any], None] | None = None,
        err_callback: Callable[[Exception], None] | None = None,
        tk_root: object | None = None) -> Future:
        """Ejecuta `func(*args)` en un hilo, con callbacks opcionales para resultado o error."""
        fut = self._executor.submit(func, *args)

        if callback or err_callback:
            def _done(f: Future):
                try:
                    res = f.result()
                    if callback:
                        if tk_root is not None:
                            after_method = getattr(tk_root, 'after', None)
                            if callable(after_method):
                                after_method(0, lambda: callback(res)) # type: ignore
                            else:
                                callback(res)
                        else:
                            callback(res)
                except Exception as e:
                    if err_callback:
                        if tk_root is not None:
                            after_method = getattr(tk_root, 'after', None)
                            if callable(after_method):
                                after_method(0, lambda: err_callback(e)) # type: ignore
                            else:
                                err_callback(e)
                        else:
                            err_callback(e)

            fut.add_done_callback(_done)

        return fut

    def shutdown(self, wait: bool = True):
        """Cierra el ThreadPoolExecutor."""
        with self._lock:
            self._executor.shutdown(wait=wait)



# Parámetros extra soportados por las endpoints `recommendations`/`search`
# clave: (tipo esperado, descripción, rango/ejemplo)
SUPPORTED_EXTRA_PARAMS = {
    'seed_tracks': ('str|list', 'IDs o URIs de pistas semilla, coma-separados', 'ej: 6r7FXNO57mlZCBY6PXcZZT'),
    'seed_artists': ('str|list', 'IDs o URIs de artistas semilla, coma-separados', 'ej: 1KpCi9BOfviCVhmpI4G2sY'),
    'seed_genres': ('str|list', 'Géneros semilla, coma-separados', 'ej: rock,pop'),
    'limit': ('int', 'Límite de resultados por página (máx. 100)', 'ej: 100'),
    # Targets típicos (0-100) expresados como enteros percentuales en la API
    'target_acousticness': ('int 0-100', 'Objetivo de acousticness (porcentual)', '0-100'),
    'target_danceability': ('int 0-100', 'Objetivo de danceability (porcentual)', '0-100'),
    'target_energy': ('int 0-100', 'Objetivo de energy (porcentual)', '0-100'),
    'target_instrumentalness': ('int 0-100', 'Objetivo de instrumentalness (porcentual)', '0-100'),
    'target_liveness': ('int 0-100', 'Objetivo de liveness (porcentual)', '0-100'),
    'target_popularity': ('int 0-100', 'Objetivo de popularidad (porcentual)', '0-100'),
    'target_valence': ('int 0-100', 'Objetivo de valence (porcentual)', '0-100'),
    'min_tempo': ('int', 'Tempo mínimo (BPM)', 'ej: 80'),
    'max_tempo': ('int', 'Tempo máximo (BPM)', 'ej: 180'),
    # Otros rangos numéricos que la API puede aceptar
    'min_duration_ms': ('int', 'Duración mínima en ms', 'ej: 60000'),
    'max_duration_ms': ('int', 'Duración máxima en ms', 'ej: 300000'),
}

# Máximo permitido por la API en un solo request
MAX_PER_REQUEST = 100



def get_track(api: ChosicAPI,
              track_id: str):
    """Obtiene un `TrackItem` por `track_id` el track_id es una URI o ID Spotify.

    - Intenta mapear la respuesta a `TrackItem` usando `ChosicResponse.from_dict`.
    - Si el mapeo falla, devuelve el dict crudo.
    """
    service = ChosicService(api)
    return service.get_track(track_id)

def get_track_auto(track_id: str, *,
                   base_url: str = 'https://www.chosic.com/api/tools',
                   timeout: float | None = None,
                   read_env: bool = True,
                   exit_on_fail: bool = False):
    """Convenience wrapper: crea la API internamente y devuelve el TrackItem o JSON crudo.

    Parámetros opcionales permiten ajustar `base_url`, `timeout` y `read_env`.
    """
    args = SimpleNamespace(base_url=base_url,timeout=timeout, read_env=read_env)
    api = create_ready_api_from_args(args, exit_on_fail=exit_on_fail)
    return get_track(api, track_id)


def get_artists(api: ChosicAPI,
                ids: str | list[str]):
    """Obtiene una lista de artistas a partir de `ids` los ids son URIs o IDs Spotify.

    - `ids` puede ser una lista/tupla de ids o una cadena separada por comas.
    - Devuelve la lista de objetos (ArtistItem/ArtistDetail) si el mapeo tuvo éxito, o el dict crudo.
    """
    service = ChosicService(api)
    return service.get_artists(ids)


def get_artists_auto(ids, *,
                     base_url: str = 'https://www.chosic.com/api/tools',
                     timeout: float | None = None,
                     read_env: bool = True,
                     exit_on_fail: bool = False):
    """Convenience wrapper: crea la API internamente y llama a `get_artists`."""
    args = SimpleNamespace(base_url=base_url, timeout=timeout, read_env=read_env)
    api = create_ready_api_from_args(args, exit_on_fail=exit_on_fail)
    return get_artists(api, ids)


def recommendations(api: ChosicAPI,
                    seed_tracks=None, seed_artists=None,
                    limit: int = 100,
                    extra_params: dict[str, Any] | None = None,
                    fetch_all: bool = False,
                    page_size: int = 100) -> ChosicResponse:
    """Solicita recomendaciones basadas en seeds (tracks/artists)."""
    service = ChosicService(api)
    return service.recommendations(seed_tracks=seed_tracks, seed_artists=seed_artists, limit=limit, extra_params=extra_params, fetch_all=fetch_all, page_size=page_size)


def recommendations_auto(*, seed_tracks=None,
                         seed_artists=None,
                         limit: int = 100,
                         extra_params: dict[str, Any] | None = None,
                         fetch_all: bool = False,
                         page_size: int = 100,
                         base_url: str = 'https://www.chosic.com/api/tools',
                         timeout: float | None = None, read_env: bool = True,
                         exit_on_fail: bool = False) -> ChosicResponse:
    """Convenience wrapper: crea la API internamente y llama a `recommendations`."""
    args = SimpleNamespace(base_url=base_url, timeout=timeout, read_env=read_env)
    api = create_ready_api_from_args(args, exit_on_fail=exit_on_fail)
    return recommendations(api, seed_tracks=seed_tracks, seed_artists=seed_artists, limit=limit, extra_params=extra_params, fetch_all=fetch_all, page_size=page_size)

def search(api: ChosicAPI,
           q: str,
           type: str = 'track',
           limit: int = 10,
           extra_params: dict[str, Any] | None = None,
           fetch_all: bool = False,
           page_size: int = 10) -> ChosicResponse:
    """Realiza una petición `search` y devuelve el resultado mapeado.

    - `api` debe ser una instancia de `ChosicAPI` (o cualquier objeto con `client.request`).
    - `extra_params` puede incluir los parámetros listados en `SUPPORTED_EXTRA_PARAMS`.
    - Devuelve `ChosicResponse` si el JSON es compatible, si no devuelve el dict crudo.
    """
    service = ChosicService(api)
    return service.search(q=q, type_=type, limit=limit, extra_params=extra_params, fetch_all=fetch_all, page_size=page_size)

def search_auto(q: str, *,
                type: str = 'track',
                limit: int = 10,
                extra_params: dict[str, Any] | None = None,
                fetch_all: bool = False,
                page_size: int = 10,
                base_url: str = 'https://www.chosic.com/api/tools',
                timeout: float | None = None, read_env: bool = True,
                exit_on_fail: bool = False) -> ChosicResponse:
    """Convenience wrapper: crea la API internamente y llama a `search`.

    Parámetros principales: `q`, `type`, `limit`, y `extra_params`.
    Opcionales: `fetch_all`, `page_size`, `base_url`, `timeout`, `read_env`, `exit_on_fail`.
    """
    args = SimpleNamespace(base_url=base_url, timeout=timeout, read_env=read_env)
    api = create_ready_api_from_args(args, exit_on_fail=exit_on_fail)
    return search(api, q=q, type=type, limit=limit, extra_params=extra_params, fetch_all=fetch_all, page_size=page_size)


def fetch_all_genres_auto(*,
                          save_path: str = 'all_genres.json',
                          timeout: float = 15.0):
    """Descarga `https://www.chosic.com/data/all_genres.json` y lo guarda en `save_path`.

    Devuelve el objeto JSON parseado.
    """
    url = 'https://www.chosic.com/data/all_genres.json'
    session = requests.Session()
    # Headers similar to ChosicHttpClient default to avoid 403
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Origin': 'https://www.chosic.com',
        'Referer': 'https://www.chosic.com/music-genre-finder/',
        'X-Requested-With': 'XMLHttpRequest',
    })

    # If CHOSIC_COOKIE env is present, add cookies to the session
    cookie_env = os.environ.get('CHOSIC_COOKIE')
    if cookie_env:
        try:
            parts = [p.strip() for p in cookie_env.split(';') if p.strip()]
            cookie_dict = {}
            for part in parts:
                if '=' in part:
                    k, v = part.split('=', 1)
                    cookie_dict[k.strip()] = v.strip()
            if cookie_dict:
                session.cookies.update(cookie_dict)
        except Exception:
            pass

    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    dump_json(data, save_path)
    return data


def fetch_audio_features(api: ChosicAPI,
                         track_id: str,
                         timeout: float | None = None):
    """Obtiene audio features para `track_id` usando `api.client` track_id es el ID o URI de Spotify, solo soporta track.

    Devuelve el dict JSON crudo.
    """
    service = ChosicService(api)
    return service.fetch_audio_features(track_id, timeout=timeout)


def fetch_audio_features_auto(track_id: str, *,
                              save_path: str | None = None,
                              base_url: str = 'https://www.chosic.com/api/tools',
                              timeout: float | None = 15.0,
                              read_env: bool = True,
                              exit_on_fail: bool = False) -> Features | dict[str, Any]:
    """Convenience wrapper: crea la API internamente y llama a `fetch_audio_features`."""
    args = SimpleNamespace(base_url=base_url, timeout=timeout, read_env=read_env)
    api = create_ready_api_from_args(args, exit_on_fail=exit_on_fail)
    feat = fetch_audio_features(api, track_id, timeout=timeout)
    if save_path:
        dump_json(feat, save_path)
    return feat


def get_genre_releases(api: ChosicAPI,
                       genre: str, limit: int | None = None,
                       extra_params: dict[str, Any] | None = None) -> ChosicResponse:
    """Obtiene lanzamientos por género y devuelve `ChosicResponse` mapeado o dict crudo."""
    service = ChosicService(api)
    return service.get_genre_releases(genre=genre, limit=limit, extra_params=extra_params)


def get_genre_releases_auto(genre: str, *,
                            limit: int | None = None,
                            extra_params: dict[str, Any] | None = None,
                            base_url: str = 'https://www.chosic.com/api/tools',
                            timeout: float | None = None, read_env: bool = True,
                            exit_on_fail: bool = False) -> ChosicResponse:
    """Convenience wrapper que crea la API y llama a `get_genre_releases`."""
    args = SimpleNamespace(base_url=base_url, timeout=timeout, read_env=read_env)
    api = create_ready_api_from_args(args, exit_on_fail=exit_on_fail)
    return get_genre_releases(api, genre=genre, limit=limit, extra_params=extra_params)


def get_top_playlists(api: ChosicAPI,
                      artist_id: str | None = None,
                      genre_name: str | None = None,
                      limit: int | None = None,
                      extra_params: dict[str, Any] | None = None) -> ChosicResponse:
    """Obtiene top playlists filtrando por `artist_id` y/o `genre_name`.

    Devuelve un `ChosicResponse` mapeado o dict crudo según la respuesta.
    """
    service = ChosicService(api)
    return service.get_top_playlists(artist_id=artist_id, genre_name=genre_name, limit=limit, extra_params=extra_params)


def get_top_playlists_auto(artist_id: str | None = None,
                           genre_name: str | None = None,
                           *,
                           limit: int | None = None,
                           extra_params: dict[str, Any] | None = None,
                           base_url: str = 'https://www.chosic.com/api/tools',
                           timeout: float | None = None, read_env: bool = True,
                           exit_on_fail: bool = False) -> ChosicResponse:
    """Convenience wrapper que crea la API y llama a `get_top_playlists`."""
    args = SimpleNamespace(base_url=base_url, timeout=timeout, read_env=read_env)
    api = create_ready_api_from_args(args, exit_on_fail=exit_on_fail)
    return get_top_playlists(api, artist_id=artist_id, genre_name=genre_name, limit=limit, extra_params=extra_params)


def _extract_track_id(track: Any) -> str | None:
    """Intenta extraer un ID de pista de un objeto que puede ser un dict o un TrackItem."""
    if track is None:
        return None
    if isinstance(track, dict):
        return track.get('id') or track.get('uri')
    return getattr(track, 'id', None) or getattr(track, 'uri', None)


def search_and_download(
    api,
    q: str,
    type: str = 'track',
    limit: int = 1,
    extra_params: dict[str, Any] | None = None,
    fetch_all: bool = False,
    page_size: int = 1,
    download: bool = False,
    out_root: str = 'downloads',
    overwrite: bool = False,
    concurrency: int = 1) -> tuple[ChosicResponse | dict[str, Any], dict[str, Any]]:
    """Realiza una búsqueda y opcionalmente descarga previews/imágenes.

    - Retorna una tupla `(result, downloads)` donde `result` es el resultado
      de la búsqueda (puede ser `ChosicResponse` o `dict`) y `downloads` es
      un dict `{track_id: path_or_exception}` con los resultados de descarga.
    - La descarga usa lazy-import de `.Downloader.download_track_assets`.
    - `concurrency` controla el número de hilos para descargar en paralelo.
    """
    logger.debug(f'search_and_download iniciado: q={q}, type={type}, download={download}')
    
    # Si la query es una URL/URI/ID de Spotify track, obtener la pista directa
    result = None
    if isinstance(q, str):
        q_str = q.strip()
        track_id = None
        if 'open.spotify.com' in q_str and '/track/' in q_str:
            # extraer id tras /track/
            m = re.search(r'/track/([A-Za-z0-9]+)', q_str)
            if m:
                track_id = m.group(1).split('?')[0]
                logger.debug(f'Track ID extraído de Spotify URL: {track_id}')
        elif q_str.startswith('spotify:track:'):
            track_id = q_str.split(':')[-1]
            logger.debug(f'Track ID extraído de URI Spotify: {track_id}')
        else:
            # posible ID de 22 caracteres
            if re.fullmatch(r'[A-Za-z0-9]{22}', q_str):
                track_id = q_str
                logger.debug(f'input es un Track ID directo: {track_id}')

        if track_id:
            try:
                logger.debug(f'Obteniendo track directo: {track_id}')
                tr = get_track(api, track_id)
                if isinstance(tr, dict):
                    result = ChosicResponse.from_dict({'tracks': [tr]})
                elif isinstance(tr, TrackItem):
                    result = ChosicResponse(tracks=TracksCollection(items=[tr]))
                else:
                    # si viene otro tipo, intentar envolverlo en dict
                    try:
                        result = ChosicResponse.from_dict({'tracks': [tr]})
                    except Exception as e:
                        logger.debug(f'No se pudo mapear track directo: {e}')
                        result = None
                if result:
                    logger.debug('Track directo obtenido exitosamente')
            except Exception as e:
                logger.debug(f'Error obteniendo track directo: {e}')
                result = None

    if result is None:
        logger.debug(f'Ejecutando búsqueda: q={q}, type={type}')
        result = search(api, q=q, type=type, limit=limit, extra_params=extra_params, fetch_all=fetch_all, page_size=page_size)
    
    downloads: dict[str, Any] = {}

    if not download:
        return result, downloads

    # Lazy import para evitar acoplamientos y dependencias circulares
    from .Downloader import download_track_assets

    # Extraer lista de pistas desde `result`
    tracks = []
    if isinstance(result, ChosicResponse):
        if getattr(result, 'tracks', None):
            tracks = getattr(result.tracks, 'items', []) if hasattr(result.tracks, 'items') else []
    elif isinstance(result, dict):
        # soporte para respuesta cruda
        tracks = result.get('tracks', {}).get('items') or result.get('tracks') or []

    logger.info(f'Iniciando descarga de {len(tracks)} tracks con concurrency={concurrency}')

    if not tracks:
        logger.info('No hay tracks para descargar')
        return result, downloads

    runner = ThreadRunner(max_workers=max(1, int(concurrency)))
    futures = []
    for t in tracks:
        tid = _extract_track_id(t)
        if not tid:
            downloads[str(t)] = RuntimeError('no track id')
            logger.warning(f'Track sin ID: {t}')
            continue
        # pass positional args to ThreadRunner.submit to avoid unexpected keyword args
        logger.debug(f'Descargando: {tid}')
        fut = runner.submit(download_track_assets, tid, Path(out_root), overwrite)
        futures.append((tid, fut))

    logger.debug(f'{len(futures)} descargas en cola')

    for idx, (tid, fut) in enumerate(futures, 1):
        try:
            path = fut.result()
            downloads[tid] = str(path)
            logger.debug(f'Descarga {idx}/{len(futures)} exitosa: {tid} -> {path}')
        except Exception as e:
            downloads[tid] = e
            logger.warning(f'Descarga {idx}/{len(futures)} fallida: {tid} - {e}')

    runner.shutdown()
    logger.info(f'Descargas completadas: {sum(1 for v in downloads.values() if not isinstance(v, Exception))}/{len(downloads)}')
    return result, downloads


def search_and_download_auto(q: str, *, type: str = 'track', limit: int = 1,
                             extra_params: dict[str, Any] | None = None,
                             fetch_all: bool = False, page_size: int = 1,
                             download: bool = False, out_root: str = 'downloads',
                             overwrite: bool = False, concurrency: int = 1,
                             base_url: str = 'https://www.chosic.com/api/tools',
                             timeout: float | None = None, read_env: bool = True,
                             exit_on_fail: bool = False) -> tuple[ChosicResponse | dict[str, Any], dict[str, Any]]:
    """Convenience wrapper: crea la API internamente y llama a `search_and_download`."""
    args = SimpleNamespace(base_url=base_url, timeout=timeout, read_env=read_env)
    api = create_ready_api_from_args(args, exit_on_fail=exit_on_fail)
    return search_and_download(api, q=q, type=type, limit=limit, extra_params=extra_params, fetch_all=fetch_all, page_size=page_size, download=download, out_root=out_root, overwrite=overwrite, concurrency=concurrency)

def _build_args_parser(defaults: dict[str, Any] | None = None) -> argparse.ArgumentParser:
    """Construye el parser de argumentos para la CLI.
    
    Args:
        defaults: Dict con valores por defecto (ej. desde archivo de configuración)
    """
    if defaults is None:
        defaults = {}
    
    examples = """
EJEMPLOS DE USO:

  # Búsqueda simple (rápida, 1 página)
  %(prog)s "The Killers"

  # Búsqueda con límite personalizado
  %(prog)s "David Bowie" --limit 50

  # Búsqueda de múltiples páginas (RECOMENDADO para grandes volúmenes)
  %(prog)s "deorro" --fetch-all --page-size 30 --limit 100

  # Búsqueda exhaustiva con muchos resultados
  %(prog)s "rock" --fetch-all --page-size 50 --limit 200 --verbose

  # ⚠ LENTO: No hagas esto (50+ segundos)
  # %(prog)s "query" --fetch-all --page-size 1 --limit 100

  # Búsqueda con archivo de salida JSON
  %(prog)s "Arctic Monkeys" --raw --limit 20

  # Búsqueda por artista
  %(prog)s "Adele" --type artist --limit 10

  # Descargar previews e imágenes del primer resultado
  %(prog)s "Mr Brightside" --download-first --out mi_musica

  # Descargar múltiples tracks with concurrency
  %(prog)s "rock" --download --fetch-all --page-size 20 --limit 10 --concurrency 4

  # Modo silencioso para scripting (perfecto para automatización)
  %(prog)s "electronic" --quiet --raw --fetch-all --page-size 50 --limit 100

  # Audio features de una pista específica
  %(prog)s "70wYA8oYHoMzhRRkARoMhU" --fetch-features --features-id 70wYA8oYHoMzhRRkARoMhU

  # Descargar lista completa de géneros
  %(prog)s --fetch-genres --quiet

  # Ver parámetros extra soportados (targets de audio)
  %(prog)s --params-info

  # Con parámetros extra (audio targets)
  %(prog)s "dance" --fetch-all --page-size 30 --limit 50 --param target_energy=80 --param target_danceability=75

  # Debugging detallado
  %(prog)s "synthwave" --fetch-all --page-size 20 --limit 30 --debug --verbose

BÚSQUEDA DE MÚLTIPLES PÁGINAS (--fetch-all):

  La opción --fetch-all obtiene resultados de múltiples páginas con paginación automática.
  
  Parámetros clave:
  - --fetch-all: Habilita paginación múltiple
  - --page-size: Resultados por página (10-100, recomendado: 20-50)
  - --limit: Total de resultados deseados
  
  Delays automáticos entre páginas (0.5s) previenen bloqueos de Cloudflare.
  
  Ejemplos:
  - Búsqueda rápida (1-2s): --page-size 50 --limit 50
  - Búsqueda normal (2-5s): --page-size 30 --limit 100
  - Búsqueda exhaustiva (5-15s): --page-size 20 --limit 300
  - EVITAR: --page-size 1 --limit 100 (muy lento: 50+ segundos)

CONFIGURACIÓN (.chosicrc):

  Crea ~/.chosicrc para establecer valores por defecto que se usarán en todos los comandos.
  Los argumentos CLI siempre overridden la configuración del archivo.

  Ejemplo ~/.chosicrc:
  [search]
  limit = 20
  page_size = 30
  fetch_all = false
  out = ./downloads
  concurrency = 3

  [logging]
  verbose = false
  quiet = false

  [api]
  timeout = 30

  Uso: %(prog)s "query" --page-size 50 --limit 100 (ignora page_size del archivo)

NIVELES DE LOGGING:

  --quiet      Solo errores (ideal para scripts y automatización)
  (default)    Advertencias y errores
  --verbose    Información útil (level INFO, recomendado para debugging)
  --debug      Todos los detalles (level DEBUG, máximo detalle)
"""
    
    p = argparse.ArgumentParser(
        description='Buscar en Chosic API - Cliente para búsquedas, descarga de features y assets',
        epilog=examples,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    p.add_argument('q', help='Término de búsqueda (q)')
    p.add_argument('--type', default=defaults.get('type', 'track'), help='Tipo (track, artist, album)')
    p.add_argument('--limit', type=int, default=defaults.get('limit', 10), help='Número máximo de resultados (máx. 100 por página sin --fetch-all)')
    p.add_argument('--base-url', default=defaults.get('base_url', 'https://www.chosic.com/api/tools'), help='Base URL de la API')
    p.add_argument('--timeout', type=float, default=defaults.get('timeout', None), help='Timeout en segundos (opcional)')
    p.add_argument('--skip-handshake', action='store_true', help='No ejecutar handshake (puede causar errores de Cloudflare)')
    p.add_argument('--no-exit-on-fail', action='store_true', dest='no_exit', help="No llamar sys.exit() si falla el handshake")
    p.add_argument('--read-env', action='store_true', default=defaults.get('read_env', True), help='Leer variables de entorno CHOSIC_*')
    p.add_argument('--no-read-env', action='store_false', dest='read_env', help='No leer variables de entorno')
    p.add_argument('--raw', action='store_true', default=defaults.get('raw', False), help='Imprimir JSON crudo en la salida')
    p.add_argument('--fetch-all', action='store_true', default=defaults.get('fetch_all', False), help='Obtener múltiples páginas con paginación automática (usa X-WP-TotalPages)')
    p.add_argument('--page-size', type=int, default=defaults.get('page_size', 10), help='Resultados por página (máx. 100). Recomendado: 20-50 con --fetch-all (mayor = más rápido, pero más solicitudes)')
    p.add_argument('--param', action='append', help='Parámetro extra en formato key=value (puede repetirse, ej: --param target_energy=80)')
    p.add_argument('--params-info', action='store_true', help='Mostrar parámetros extra soportados (targets de audio) y salir')
    p.add_argument('--fetch-genres', action='store_true', default=defaults.get('fetch_genres', False), help='Descargar y guardar all_genres.json desde https://www.chosic.com/data/all_genres.json')
    p.add_argument('--fetch-genres-file', default=defaults.get('fetch_genres_file', 'all_genres.json'), help='Ruta de salida para all_genres.json')
    p.add_argument('--fetch-features', action='store_true', default=defaults.get('fetch_features', False), help='Descargar audio features para una pista y guardar JSON')
    p.add_argument('--features-id', default=defaults.get('features_id', None), help='ID o URI Spotify de la pista para --fetch-features')
    p.add_argument('--features-file', default=defaults.get('features_file', 'features.json'), help='Ruta de salida para audio features JSON')
    p.add_argument('--download', action='store_true', default=defaults.get('download', False), help='Descargar previews e imágenes de los tracks devueltos')
    p.add_argument('--out', default=defaults.get('out', 'downloads'), help='Carpeta base de salida para descargas')
    p.add_argument('--overwrite', action='store_true', default=defaults.get('overwrite', False), help='Sobrescribir archivos existentes al descargar')
    p.add_argument('--concurrency', type=int, default=defaults.get('concurrency', 1), help='Número de descargas concurrentes (recomendado: 2-4)')
    p.add_argument('--download-first', action='store_true', default=defaults.get('download_first', False), help='Descargar solo el primer resultado de la búsqueda (activa automáticamente --download)')
    p.add_argument('--quiet', action='store_true', default=defaults.get('quiet', False), help='Modo silencioso: solo errores (ideal para scripting y automatización)')
    p.add_argument('--verbose', action='store_true', default=defaults.get('verbose', False), help='Modo verbose: muestra mensajes informativos (nivel INFO, recomendado con --fetch-all)')
    p.add_argument('--debug', action='store_true', default=defaults.get('debug', False), help='Modo debug: máximo detalle para troubleshooting')
    return p


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada para la CLI de búsqueda."""
    argv = argv or sys.argv[1:]
    
    # Cargar configuración desde archivo ANTES de parsear argumentos
    # para que pueda ser usada como defaults
    file_config = _load_config_file()
    
    # Configurar logging temprano si está en el archivo
    _configure_logging(
        verbose=file_config.get('verbose', False),
        debug=file_config.get('debug', False),
        quiet=file_config.get('quiet', False)
    )
    
    logger.debug(f'Configuración desde archivo: {list(file_config.keys())}')
    
    parser = _build_args_parser(defaults=file_config)
    args = parser.parse_args(argv)
    
    # Reconfigurar logging con los argumentos CLI (pueden overridden el archivo)
    _configure_logging(
        verbose=getattr(args, 'verbose', False),
        debug=getattr(args, 'debug', False),
        quiet=getattr(args, 'quiet', False)
    )
    
    logger.debug(f'Argumentos parseados: {args}')
    logger.debug(f'ChosicAlpha versión {__version__}')

    if getattr(args, 'params_info', False):
        # Mostrar parámetros soportados y salir
        logger.info('Mostrando parámetros extra soportados')
        print('Parámetros extra soportados:')
        for k, v in SUPPORTED_EXTRA_PARAMS.items():
            t, desc, example = v
            print(f'- {k}: {t} — {desc} (ej: {example})')
        return 0

    if getattr(args, 'fetch_genres', False):
        # Descargar all_genres.json desde chosic y guardar
        logger.info(f'Descargando genres desde Chosic, guardará en: {args.fetch_genres_file}')
        try:
            data = fetch_all_genres_auto(save_path=args.fetch_genres_file)
            cnt = len(data) if isinstance(data, list) else len(data.keys()) if isinstance(data, dict) else 0
            logger.info(f'Descargado all_genres.json con {cnt} elementos')
            if not getattr(args, 'quiet', False):
                print(f'Descargado all_genres.json, elementos: {cnt}, guardado en {args.fetch_genres_file}')
            return 0
        except Exception as e:
            logger.error(f'Error descargando all_genres: {e}', exc_info=True)
            print('Error descargando all_genres:', e, file=sys.stderr)
            return 2

    if getattr(args, 'fetch_features', False):
        track_id = getattr(args, 'features_id', None)
        if not track_id:
            logger.error('--fetch-features requiere --features-id')
            print('Debe indicar --features-id ID_DE_LA_PISTA', file=sys.stderr)
            return 2
        logger.info(f'Descargando audio features para track: {track_id}')
        try:
            args2 = SimpleNamespace(base_url=args.base_url, timeout=args.timeout, read_env=args.read_env)
            api = create_ready_api_from_args(args2, exit_on_fail=not args.no_exit)
            logger.debug('API creada exitosamente')
            feat = fetch_audio_features(api, track_id, timeout=args.timeout)
            logger.debug(f'Features obtenidas: {len(feat) if isinstance(feat, dict) else len(vars(feat))} campos') # intenta mostrar número de campos si es dict o dataclass
            dump_json(feat, args.features_file)
            logger.info(f'Audio features guardadas en: {args.features_file}')
            if not getattr(args, 'quiet', False):
                print(f'Descargado audio features para {track_id}, guardado en {args.features_file}')
            return 0
        except Exception as e:
            logger.error(f'Error descargando audio features: {e}', exc_info=True)
            print('Error descargando audio features:', e, file=sys.stderr)
            return 2

    # Preparar la API
    if args.skip_handshake:
        logger.info('Creando API sin handshake')
        api = create_chosic_api(base_url=args.base_url, read_env=args.read_env)
        if args.timeout is not None:
            api.client.timeout = args.timeout
        logger.debug(f'API creada, base_url={args.base_url}, timeout={args.timeout}')
    else:
        logger.info('Creando API con handshake')
        api = create_ready_api_from_args(args, exit_on_fail=not args.no_exit)
        logger.debug('API lista después de handshake')

    # Parsear parámetros extra
    extra = {}
    if args.param:
        logger.debug(f'Parseando {len(args.param)} parámetros extra')
        for p in args.param:
            if '=' in p:
                k, v = p.split('=', 1)
                # detectar listas separadas por comas
                if ',' in v:
                    extra[k] = v.split(',')
                    logger.debug(f'Parámetro {k}: lista con {len(extra[k])} elementos')
                else:
                    extra[k] = v
                    logger.debug(f'Parámetro {k}: {v}')

    # Si el usuario pidió un límite mayor al máximo por petición, avisar y recortar
    if getattr(args, 'limit', None) is not None and int(args.limit) > MAX_PER_REQUEST:
        logger.warning('Limit request > %s, recortando a %s', MAX_PER_REQUEST, MAX_PER_REQUEST)
        args.limit = MAX_PER_REQUEST
    if getattr(args, 'page_size', None) is not None and int(args.page_size) > MAX_PER_REQUEST:
        logger.warning('Page size > %s, recortando a %s', MAX_PER_REQUEST, MAX_PER_REQUEST)
        args.page_size = MAX_PER_REQUEST

    # Ejecutar búsqueda (y opcionalmente descargar)
    downloads = None
    try:
        # Si se pide download-first, activar descarga y limitar a 1 resultado
        download_first = getattr(args, 'download_first', False)
        download_flag = getattr(args, 'download', False) or download_first
        call_limit = 1 if download_first else args.limit
        
        logger.info(f'Iniciando búsqueda: q="{args.q}", type={args.type}, limit={call_limit}, download={download_flag}')
        logger.debug(f'extra_params={extra}, fetch_all={args.fetch_all}')

        if download_flag:
            logger.info(f'Descargando a: {args.out}, overwrite={args.overwrite}, concurrency={args.concurrency}')
            result, downloads = search_and_download(api, q=args.q, type=args.type, limit=call_limit, extra_params=extra, fetch_all=args.fetch_all, page_size=args.page_size, download=True, out_root=args.out, overwrite=args.overwrite, concurrency=args.concurrency)
        else:
            result = search(api, q=args.q, type=args.type, limit=args.limit, extra_params=extra, fetch_all=args.fetch_all, page_size=args.page_size)
        
        logger.info('Búsqueda completada exitosamente')
    except ChosicAPIError as e:
        logger.error(f'Error en la API: {e}', exc_info=True)
        print(f'Error en la API: {e}', file=sys.stderr)
        return 2

    # Mostrar resumen y JSON (si --raw)
    if not isinstance(result, ChosicResponse):
        logger.error('La búsqueda no devolvió un ChosicResponse mapeado')
        raise ChosicAPIError('La búsqueda no devolvió un ChosicResponse mapeado')

    quiet = getattr(args, 'quiet', False)
    
    track_count = len(result.tracks.items) if result.tracks else 0
    artist_count = len(result.artists.items) if result.artists else 0
    logger.info(f'Resultados: {track_count} tracks, {artist_count} artists')

    if getattr(args, 'raw', False):
        logger.debug('Imprimiendo JSON crudo')
        print(dumps_json(result))

    if not quiet:
        if result.tracks:
            print(f'Tracks: {len(result.tracks.items)}')
            for t in result.tracks.items:
                print('-', t.name, 'by', t.artist_display)
        if result.artists:
            print(f'Artists: {len(result.artists.items)}')
            for a in result.artists.items:
                if isinstance(a, ArtistDetail):
                    print('-', a.name, f'(popularity={a.popularity}, followers={a.followers})')
                    if getattr(a, 'image', None):
                        print('  image:', a.image)
                else:
                    print('-', a.name)

    # Mostrar resumen de descargas si se pidieron
    if downloads is not None and not quiet:
        print('\nDescargas:')
        success = 0
        fail = 0
        for k, v in downloads.items():
            if isinstance(v, Exception):
                print('-', k, 'ERROR:', v)
                logger.warning(f'Descarga fallida para {k}: {v}')
                fail += 1
            else:
                print('-', k, '->', v)
                logger.debug(f'Descargado {k} -> {v}')
                success += 1
        print(f'Descargas completadas: {success}, fallidas: {fail}')
        logger.info(f'Resumen descargas: {success} exitosas, {fail} fallidas')

    logger.info('Ejecución completada')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
