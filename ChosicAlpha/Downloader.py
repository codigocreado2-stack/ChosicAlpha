"""Downloader: Descarga preview e imágenes (cover art) de pistas usando helpers.

Crea una carpeta por pista con nombre: "{track_name} - {artist_name} ({id})".
Dentro guarda:
- audio: "{track_name} - {artist_name}.{ext}" (desde preview_url)
- imágenes: "image_default.{ext}" y "image_large.{ext}" si están disponibles

Uso desde CLI:
  python3 Downloader.py <track_id_or_url> [<track_id_or_url> ...] --out mis_descargas --overwrite
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import requests

# Asegurar import local
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    # Importación relativa (cuando se ejecuta como módulo)
    from .Busqueda import get_track_auto
except ImportError:
    # Importación absoluta (cuando se ejecuta directamente)
    from Busqueda import get_track_auto

logger = logging.getLogger(__name__)
# Nota: No añadimos handler aquí para respetar la configuración global de logging
# cuando se importa como módulo desde Busqueda. El handler se añade solo en CLI.

INVALID_FILENAME_RE = re.compile(r'[\\/:"*?<>|\n\r]')


def _sanitize(s: str) -> str:
    """Sanitiza un string para usarlo como nombre de archivo."""
    s = s or ''
    original = s
    s = s.strip()
    s = INVALID_FILENAME_RE.sub('_', s)
    # limit length
    if len(s) > 200:
        s = s[:200].rstrip()
    if s != original:
        logger.debug(f'Sanitizado: "{original}" -> "{s}"')
    return s


def _download_url(url: str, dest: Path, timeout: float = 30.0) -> None:
    """Descarga una URL a un archivo local con inferencia de extensión."""
    if not url:
        raise ValueError('Empty URL')
    logger.debug(f'Iniciando descarga: {url}')
    logger.info('  -> descargando %s', url)
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Referer': 'https://www.chosic.com',
    }
    try:
        r = session.get(url, headers=headers, timeout=timeout, stream=True)
        r.raise_for_status()
        logger.debug(f'Respuesta HTTP: {r.status_code}, Content-Type: {r.headers.get("Content-Type")}')
    except Exception as e:
        logger.error(f'Error en solicitud HTTP para {url}: {e}')
        raise RuntimeError(f'Error descargando {url}: {e}')

    # Try to infer extension
    content_type = r.headers.get('Content-Type', '')
    ext = None
    if 'image/' in content_type:
        ext = content_type.split('/', 1)[1].split(';', 1)[0]
        logger.debug(f'Tipo de imagen detectado: {ext}')
    elif 'audio/' in content_type:
        ext = content_type.split('/', 1)[1].split(';', 1)[0]
        logger.debug(f'Tipo de audio detectado: {ext}')
    else:
        logger.debug(f'Content-Type no reconocido: {content_type}')

    if dest.suffix and len(dest.suffix) > 1:
        out_path = dest
        logger.debug(f'Extensión ya presente en destino: {dest.suffix}')
    else:
        if ext:
            # normalize common suffixes
            if ext == 'jpeg':
                ext = 'jpg'
            out_path = dest.with_suffix('.' + ext)
            logger.debug(f'Extensión inferida y añadida: .{ext}')
        else:
            out_path = dest
            logger.debug('No se pudo inferir extensión, usando destino tal cual')

    try:
        total_size = 0
        with out_path.open('wb') as fh:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)
                    total_size += len(chunk)
        logger.debug(f'Descargados {total_size} bytes ({total_size / 1024:.1f} KB)')
    except Exception as e:
        logger.error(f'Error escribiendo archivo {out_path}: {e}')
        raise RuntimeError(f'Error escribiendo {out_path}: {e}')

    logger.info('  -> guardado en %s', out_path)


def download_track_assets(track_id_or_url: str, out_root: Path = Path('downloads'), overwrite: bool = False) -> Path:
    """Descarga preview e imágenes para una pista.

    Args:
        track_id_or_url: ID, URI o URL de Spotify aceptado por `get_track_auto`.
        out_root: Carpeta base donde crear la carpeta por pista.
        overwrite: Si es True, sobrescribe archivos existentes.

    Returns:
        La ruta de la carpeta creada.
    """
    logger.debug(f'Iniciando descarga de assets para: {track_id_or_url} (overwrite={overwrite})')
    
    try:
        track = get_track_auto(track_id_or_url)
        logger.debug(f'Track obtenido: {type(track).__name__}')
    except Exception as e:
        logger.error(f'Error obteniendo información de la pista: {e}')
        raise
    
    # `track` puede ser un objeto TrackItem o un dict
    if hasattr(track, '__dict__') or hasattr(track, 'id'):
        logger.debug('Track identificado como objeto (dataclass/TrackItem)')
        tid = getattr(track, 'id', '')
        name = getattr(track, 'name', '')
        artist_list = getattr(track, 'artists', None)
        if isinstance(artist_list, (list, tuple)) and len(artist_list) > 0:
            artist_name = getattr(artist_list[0], 'name', '')
        else:
            artist_name = ''
        # album images may be in album object
        album = getattr(track, 'album', None)
        image_default = getattr(album, 'image_default', None) if album is not None else getattr(track, 'image', None)
        image_large = getattr(album, 'image_large', None) if album is not None else None
        preview_url = getattr(track, 'preview_url', None)
    elif isinstance(track, dict):
        logger.debug('Track identificado como diccionario')
        tid = track.get('id', '')
        name = track.get('name', '')
        artist_name = ''
        a = track.get('artists') or []
        if isinstance(a, (list, tuple)) and a:
            artist_name = a[0].get('name', '') if isinstance(a[0], dict) else str(a[0])
        album = track.get('album') or {}
        image_default = album.get('image_default') or track.get('image') or None
        image_large = album.get('image_large') or None
        preview_url = track.get('preview_url')
    else:
        logger.error(f'Respuesta de get_track_auto no reconocida: {type(track).__name__}')
        raise RuntimeError('Respuesta de get_track_auto no reconocida')

    logger.debug(f'Información extraída: ID={tid}, nombre="{name}", artista="{artist_name}"')
    logger.debug(f'URLs: preview={bool(preview_url)}, image_default={bool(image_default)}, image_large={bool(image_large)}')

    name_s = _sanitize(name or 'unknown')
    artist_s = _sanitize(artist_name or 'unknown')
    id_s = _sanitize(tid or '')

    folder_name = f"{name_s} - {artist_s} ({id_s})" if id_s else f"{name_s} - {artist_s}"
    out_dir = Path(out_root) / folder_name
    
    logger.debug(f'Nombre de carpeta: {folder_name}')
    logger.debug(f'Ruta de salida: {out_dir}')
    
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f'Carpeta creada/verificada: {out_dir}')
    except Exception as e:
        logger.error(f'Error creando carpeta {out_dir}: {e}')
        raise RuntimeError(f'Error creando carpeta: {e}')

    # Download preview
    if preview_url:
        # choose filename base and extension
        audio_base = out_dir / f"{name_s} - {artist_s}"
        logger.debug(f'Descargando preview a: {audio_base}')
        if audio_base.exists() and not overwrite:
            logger.info('Audio ya existe, omitiendo: %s', audio_base)
            logger.debug('Para sobrescribir, usa --overwrite')
        else:
            try:
                _download_url(preview_url, audio_base)
                logger.info('Preview descargado exitosamente')
            except Exception as e:
                logger.error('No se pudo descargar preview: %s', e)
    else:
        logger.info('No hay preview_url para %s', track_id_or_url)
        logger.debug('La pista podría no tener preview disponible')

    # Download images
    if image_default:
        logger.debug(f'Descargando image_default')
        try:
            _download_url(image_default, out_dir / 'image_default')
            logger.info('Image default descargada exitosamente')
        except Exception as e:
            logger.error('No se pudo descargar image_default: %s', e)
            logger.debug(f'URL: {image_default}')
    else:
        logger.info('No hay image_default para %s', track_id_or_url)

    if image_large:
        logger.debug(f'Descargando image_large')
        try:
            _download_url(image_large, out_dir / 'image_large')
            logger.info('Image large descargada exitosamente')
        except Exception as e:
            logger.error('No se pudo descargar image_large: %s', e)
            logger.debug(f'URL: {image_large}')

    logger.info(f'Descarga completada para: {folder_name}')
    logger.debug(f'Ubicación final: {out_dir}')
    return out_dir


def _build_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos para la CLI."""
    p = argparse.ArgumentParser(
        description='Descargar preview e imágenes para tracks usando Chosic helpers',
        epilog="""
EJEMPLOS:

  # Descargar assets de un track
  %(prog)s 3n3Ppam7vgaVa1iaRUc9Lp --out downloads

  # Descargar múltiples tracks
  %(prog)s 3n3Ppam7vgaVa1iaRUc9Lp 70wYA8oYHoMzhRRkARoMhU --out mi_musica

  # Descargar con URL de Spotify
  %(prog)s https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp --out downloads

  # Sobrescribir archivos existentes
  %(prog)s "Mr Brightside" --overwrite

  # Modo verbose con detalles de descarga
  %(prog)s 3n3Ppam7vgaVa1iaRUc9Lp --verbose

  # Modo debug completo para troubleshooting
  %(prog)s "My Song" --debug

NOTA: Para cada track se crea una carpeta: "track name - artist name (id)"
      dentro se guardan: audio.mp3, image_default.jpg, image_large.jpg
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument('tracks', nargs='+', help='ID/URI/URL Spotify de la pista (puede pasar varios)')
    p.add_argument('--out', default='downloads', help='Carpeta base de salida (default: downloads)')
    p.add_argument('--overwrite', action='store_true', help='Sobrescribir archivos existentes')
    p.add_argument('--quiet', action='store_true', help='Modo silencioso: solo errores')
    p.add_argument('--verbose', action='store_true', help='Modo verbose: muestra información detallada (level INFO)')
    p.add_argument('--debug', action='store_true', help='Modo debug: máximo detalle para troubleshooting (level DEBUG)')
    return p


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada para la CLI de descarga."""
    argv = argv or sys.argv[1:]
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Configurar logging solo si se ejecuta como CLI (no como módulo importado)
    # Evitar duplicar handlers si ya existen
    if not logger.handlers:
        log_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(log_formatter)
        logger.addHandler(log_handler)

    # Configurar el nivel de logging según flags
    if args.quiet:
        logger.setLevel(logging.ERROR)
    elif args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    logger.info(f'=== Iniciando descarga de {len(args.tracks)} track(s) ===')
    logger.debug(f'Parámetros: out={args.out}, overwrite={args.overwrite}')
    logger.debug(f'Niveles: quiet={args.quiet}, verbose={args.verbose}, debug={args.debug}')
    
    out_root = Path(args.out)
    logger.debug(f'Carpeta base de salida: {out_root.resolve()}')
    
    success_count = 0
    error_count = 0
    
    for idx, t in enumerate(args.tracks, 1):
        logger.info(f'[{idx}/{len(args.tracks)}] Procesando: {t}')
        try:
            d = download_track_assets(t, out_root=out_root, overwrite=args.overwrite)
            logger.info(f'[{idx}/{len(args.tracks)}] ✓ Hecho: {d}')
            success_count += 1
        except Exception as e:
            logger.error(f'[{idx}/{len(args.tracks)}] ✗ Error procesando {t}: {e}', exc_info=True)
            error_count += 1
    
    logger.info(f'=== Descarga finalizada: {success_count} exitosas, {error_count} errores ===')
    
    if error_count > 0:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
